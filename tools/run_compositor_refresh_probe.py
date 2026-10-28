"""Run unfiltered stream exclusion updates over verified owned research coverage."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from process_cleanup import matching_pids, stop_launched
from run_native import ROOT, probe
from run_pixel_agent_audit import marker_recovery


def invoke(arguments, output):
    manifest = json.loads((ROOT / 'docs/evidence/compositor-refresh-permission-manifest.json').read_text())
    app = Path(manifest['path'])
    binary = app / 'Contents/MacOS/CompositorRefreshProbe'
    if hashlib.sha256(binary.read_bytes()).hexdigest() != manifest['executableSHA256']:
        raise RuntimeError('The consent-pinned capture helper changed')
    subprocess.run(['codesign', '--verify', '--strict', str(app)], check=True, timeout=10)
    existing = matching_pids(binary)
    if existing:
        raise RuntimeError('A capture-refresh helper already runs')
    coordinate = bool(arguments and str(arguments[0]) == 'sequence')
    focus_binary = ROOT / '.build/ResearchCaptureFocus'
    focus_output = output.with_suffix('.focus.json')
    if coordinate and (not focus_binary.is_file() or focus_output.exists()):
        raise RuntimeError('Build the bounded focus coordinator and use a fresh output')
    focus = None
    launcher = subprocess.Popen(['open', '-g', '-n', '-W', str(app), '--args', *map(str, arguments),
                                 '--out', str(output)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    launcher.research_existing_pids = existing
    try:
        if coordinate:
            focus = subprocess.Popen([str(focus_binary), str(arguments[1]), str(arguments[4]),
                                      manifest['executableSHA256'], str(focus_output)],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        launcher.wait(timeout=40)
        return json.loads(output.read_text())
    finally:
        clean = stop_launched(launcher, binary)
        if launcher.poll() is None:
            launcher.terminate()
            launcher.wait(timeout=3)
        if focus is not None:
            try:
                focus.wait(timeout=17)
            except subprocess.TimeoutExpired:
                focus.terminate()
                focus.wait(timeout=3)
                raise RuntimeError('The bounded focus coordinator failed to stop')
        if not clean:
            raise RuntimeError('The scoped capture helper did not stop')


def run(output, session_path=None):
    output = output.resolve()
    if not output.is_relative_to((ROOT / 'artifacts').resolve()):
        raise ValueError('Use an output directory inside project artifacts')
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    permission = invoke(['--permissions'], output / 'permissions.json')
    if not session_path:
        return permission
    if not permission.get('screenRecordingGranted'):
        return {'status': 'permission-required', 'captureAttempted': False}
    session = json.loads(session_path.read_text())
    binary = ROOT / 'dist/InternalKeyboardControl.app/Contents/MacOS/InternalKeyboardControl'
    if (session.get('windowOnly') or not session.get('targetWindowID') or not session.get('backdropWindowID')
            or session['pid'] not in matching_pids(binary)
            or hashlib.sha256(binary.read_bytes()).hexdigest() != session['binarySHA256']):
        raise RuntimeError('The recorded ordinary research session is no longer live')
    windows = probe(['windows', session['pid']], output / 'windows.json', background=True)
    candidates = [w for w in windows.get('windows', [])
                  if w.get('kCGWindowOwnerPID') == session['pid'] and w.get('kCGWindowNumber') == session['targetWindowID']]
    if len(candidates) != 1:
        raise RuntimeError('Require the exact owned target window')
    result = invoke(['sequence', session['pid'], candidates[0]['kCGWindowNumber'], session['backdropWindowID'], session['binarySHA256']],
                    output / 'sequence.json')
    recoveries = []
    for stage in result.get('stages', []):
        for name in stage['images']:
            image = Path(name).resolve()
            if not image.is_relative_to(output) or not image.is_file():
                raise RuntimeError('Helper image is outside this run')
            ocr = probe(['ocr', image], image.with_suffix('.ocr.json'), background=True)
            recoveries.append({'stage': stage['stage'], 'image': str(image),
                               'ocrAvailable': isinstance(ocr.get('text'), list),
                               'markerRecovery': marker_recovery(ocr, session['secret']),
                               'backdropLabelRecovered': 'controlled research backdrop' in json.dumps(ocr).lower()})
    focus_path = (output / 'sequence.json').with_suffix('.focus.json')
    focus_report = json.loads(focus_path.read_text()) if focus_path.exists() else {}
    summary = {'launchFocus': focus_report, 'status': result['status'], 'streamStopped': result.get('streamStopped'),
               'targetPID': session['pid'], 'targetBinarySHA256': session['binarySHA256'],
               'windowSharingEnabled': session['windowSharingEnabled'], 'recoveries': recoveries,
               'stageReports': [{k: stage[k] for k in ['stage', 'status', 'completeFramesSinceBaseline', 'statuses']}
                                for stage in result.get('stages', [])],
               'scope': 'Sampled unfiltered crop inside verified owned coverage. Missing markers need clear references and physical visibility.'}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--session', type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.output, args.session)), flush=True)
