"""Run the fixed engine recorder with existing privacy guards and a separate grant."""

import argparse
import json
from pathlib import Path
import subprocess

from build_engine_compositor import APP, MANIFEST
from build_focus_browser import digest
from launch_focus_browser import verified_target
from process_cleanup import matching_pids, stop_launched
from run_device_session import active
from run_focus_engine_regression import activate
from run_loaded_page_attacks import close, prepare
from run_native import ROOT, Oracle, probe
from run_pixel_agent_audit import marker_recovery
from run_preview_compositor_comparison import fully_audited, score
from run_preview_lifecycle import fresh_output
from run_preview_renderer_reads import validate_physical
from website_challenge import save


def invoke(arguments, output):
    manifest = json.loads(MANIFEST.read_text())
    binary = APP / 'Contents/MacOS/EngineCompositorProbe'
    if manifest['path'] != str(APP) or digest(binary) != manifest['executableSHA256']:
        raise RuntimeError('The pinned engine recorder changed')
    for name, expected in manifest['sourceHashes'].items():
        if digest(ROOT / name) != expected:
            raise RuntimeError('A pinned recorder source changed')
    if arguments != ['permissions']:
        if len(arguments) != 3 or arguments[0] not in ['coverage', 'sequence']:
            raise ValueError('Use the scoped coverage or sequence command')
        if arguments[0] == 'sequence' and not manifest.get('permissionApproved'):
            raise RuntimeError('This separate recorder needs Screen Recording approval')
    output = output.resolve()
    if (not output.is_relative_to((ROOT / 'artifacts').resolve()) or output.suffix != '.json'
            or output.exists() or matching_pids(binary)):
        raise ValueError('Use a new owned report and an idle recorder')
    subprocess.run(['codesign', '--verify', '--strict', str(APP)], check=True, capture_output=True, timeout=10)
    launcher = subprocess.Popen(['open', '-g', '-n', '-W', str(APP), '--args',
                                 *map(str, arguments), '--out', str(output)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    launcher.research_existing_pids = set()
    result = {}
    try:
        launcher.wait(timeout=30)
        result = json.loads(output.read_text())
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        result = {'status': 'inconclusive', 'error': str(error)}
    finally:
        cleaned = stop_launched(launcher, binary)
        if launcher.poll() is None:
            launcher.terminate()
            try:
                launcher.wait(timeout=3)
            except subprocess.TimeoutExpired:
                launcher.kill()
                launcher.wait(timeout=3)
        result.update(cleanupVerified=cleaned, probeSHA256=manifest['executableSHA256'])
        save(output, result)
        if not cleaned:
            raise RuntimeError('Recorder cleanup failed; stop desktop tests')
    return result


def capture(session, prefix, oracle, command='sequence'):
    activate(session['pid'])
    windows = probe(['windows', session['pid']], prefix.with_suffix('.windows.json'), background=True)
    owned = [row for row in windows.get('windows', []) if row.get('kCGWindowOwnerPID') == session['pid']
             and row.get('kCGWindowLayer') == 0 and row.get('kCGWindowAlpha') == 1
             and 600 <= row.get('kCGWindowBounds', {}).get('Width', 0) <= 4096
             and 400 <= row.get('kCGWindowBounds', {}).get('Height', 0) <= 4096]
    if len(owned) != 1:
        raise RuntimeError('Need exactly one ordinary research window')
    result = invoke([command, session['pid'], owned[0]['kCGWindowNumber']], prefix.with_suffix('.json'))
    if command == 'coverage':
        return result
    result.update(markerRecovered=False, markerChecks=[], stageMarkers=[False] * 3)
    if result.get('images') or result.get('firstNonuniformImage'):
        marker = oracle.state(session['trial'])['secret']
        paths = result.get('images', []) + ([result['firstNonuniformImage']] if result.get('firstNonuniformImage') else [])
        for index, raw in enumerate(paths):
            path = Path(raw).resolve()
            if not path.is_relative_to(prefix.parent.resolve()) or not path.is_file():
                raise RuntimeError('Recorder image is outside this trial')
            if fully_audited(result) and result['nonuniformFrames'] == 0:
                continue
            try:
                ocr = probe(['ocr', path], prefix.with_suffix(f'.ocr-{index}.json'), background=True)
            except (RuntimeError, OSError, subprocess.SubprocessError) as error:
                result['markerChecks'].append({'image': str(path), 'error': str(error)})
                save(prefix.with_suffix('.json'), result)
                continue
            recovery = marker_recovery(ocr, marker)
            recovered = any(recovery.values())
            result['markerChecks'].append({'image': str(path), 'markerRecovery': recovery})
            result['markerRecovered'] |= recovered
            for stage in range(3):
                if f'.stage-{stage}-sample-' in path.name:
                    result['stageMarkers'][stage] |= recovered
            save(prefix.with_suffix('.json'), result)
    save(prefix.with_suffix('.json'), result)
    return result


def run(session_path, physical_path, output, coverage_only=False):
    session = json.loads(session_path.read_text())
    if session.get('target') != 'AgentFreeBrowserEngine':
        raise ValueError('Use the engine-browser physical session')
    verified_target()
    validate_physical(session, json.loads(physical_path.read_text()))
    active(session)
    output = fresh_output(output)
    oracle = Oracle(session['controller'])
    initial = oracle.state(session['trial'])
    if not any(row['accepted'] for row in initial['submissions']):
        raise RuntimeError('Need a completed physical baseline')
    report = {'status': 'inconclusive', 'candidatePID': session['pid'], 'candidateSHA256': session['binarySHA256'],
              'coverageOnly': coverage_only, 'physicalInputAbsenceVerified': False}
    def reference(label):
        target = prepare('InspectableControl', output / label, oracle)
        row = {}
        try:
            row = capture(target, output / label, oracle)
        finally:
            close(target)
            row['referenceCleanupVerified'] = True
            save((output / label).with_suffix('.json'), row)
        return row
    try:
        report['permissions'] = invoke(['permissions'], output / 'permissions.json')
        if coverage_only:
            report['candidate'] = capture(session, output / 'candidate', oracle, 'coverage')
            report['status'] = report['candidate'].get('status', 'inconclusive')
        elif not report['permissions'].get('screenRecordingGranted'):
            report['reason'] = 'Separate recorder grant is ineffective; no capture ran'
        else:
            if matching_pids(ROOT / 'dist/InspectableControl.app/Contents/MacOS/InspectableControl'):
                raise RuntimeError('A readable reference already runs')
            report['before'] = reference('before')
            if fully_audited(report['before']) and report['before'].get('stageMarkers') == [True] * 3:
                report['candidate'] = capture(session, output / 'candidate', oracle)
                if report['candidate'].get('markerRecovered'):
                    report['status'] = 'marker-recovered'
                save(output / 'results.json', report)
                if fully_audited(report['candidate']):
                    report['after'] = reference('after')
                    if report['status'] != 'marker-recovered':
                        report['status'] = score(report['before'], report['candidate'], report['after'])
    finally:
        try:
            report['oracleFinal'] = oracle.state(session['trial'])
        finally:
            save(output / 'results.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', type=Path, required=True)
    parser.add_argument('--physical-control', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--coverage-only', action='store_true')
    args = parser.parse_args()
    result = run(args.session, args.physical_control, args.output, args.coverage_only)
    print(json.dumps({'status': result['status'], 'coverageOnly': args.coverage_only}))
