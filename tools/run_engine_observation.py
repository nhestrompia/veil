"""Compare existing scoped observation tools on the physically opened engine app."""

import argparse
import hashlib
import json
from pathlib import Path
import time

from launch_focus_browser import verified_target
from process_cleanup import matching_pids
from run_device_session import active
from run_focus_engine_regression import activate
from run_loaded_page_attacks import close, prepare
from run_native import ROOT, Oracle, probe
from run_pixel_agent_audit import marker_recovery
from run_preview_lifecycle import fresh_output
from run_preview_renderer_reads import validate_physical
from website_challenge import save

ROUTES = ['ax', 'ax-action', 'capture', 'display-capture', 'system-capture']


def score(route, before, candidate, after):
    if candidate.get('newAcceptedActions', 0) or candidate.get('markerRecovered'):
        return 'bypass'
    if route == 'ax-action' and any(candidate.get('probe', {}).get(key) == 0
                                    for key in ['setValueError', 'pressError']):
        return 'partial-action-requires-review'
    if not before.get('worked') or not after.get('worked'):
        return 'inconclusive'
    if route == 'ax-action':
        if (candidate.get('probe', {}).get('status') == 'attempted'
                or candidate.get('probe', {}).get('error') == 'Fixture field or action not found in AX tree'):
            return 'no-action-observed'
    elif candidate.get('completed'):
        return 'marker-not-recovered-in-bounded-observation'
    return 'inconclusive'


def observe(target, route, output, oracle):
    activate(target['pid'])
    initial = oracle.state(target['trial'])
    arguments = [route, target['pid']]
    image = output.with_suffix('.png')
    if route in ['capture', 'display-capture', 'system-capture']:
        arguments.append(image)
    result = probe(arguments, output.with_suffix('.probe.json'), background=True)
    time.sleep(.3)
    final = oracle.state(target['trial'])
    actions = sum(bool(item['accepted']) for item in final['submissions'][len(initial['submissions']):])
    ocr = {}
    if route in ['capture', 'display-capture', 'system-capture'] and result.get('status') == 'captured' and image.is_file():
        ocr = probe(['ocr', image], output.with_suffix('.ocr.json'), background=True)
        completed = isinstance(ocr.get('text'), list)
        marker = any(marker_recovery(ocr, initial['secret']).values())
    else:
        completed = result.get('status') == ('attempted' if route == 'ax-action' else 'observed')
        marker = initial['secret'] in json.dumps(result)
    row = {'probe': result, 'completed': completed, 'markerRecovered': marker,
           'newAcceptedActions': actions, 'ocr': ocr,
           'worked': actions > 0 if route == 'ax-action' else completed and marker}
    save(output.with_suffix('.json'), row)
    return row


def reference(route, output, oracle):
    target = prepare('InspectableControl', output, oracle)
    row = {}
    try:
        row = observe(target, route, output, oracle)
        row.update(pid=target['pid'], binarySHA256=target['binarySHA256'])
    finally:
        close(target)
        row['cleanupVerified'] = True
        save(output.with_suffix('.json'), row)
    return row


def finish(report, session, oracle, binary, output):
    try:
        active(session)
        activate(session['pid'])
        report['oracleFinal'] = oracle.state(session['trial'])
    except Exception as error:
        report['finalizationError'] = str(error)
        if report['status'] != 'bypass':
            report['status'] = 'inconclusive'
        raise
    finally:
        for name, executable in [('probeStopped', binary), ('referencesStopped',
                                 ROOT / 'dist/InspectableControl.app/Contents/MacOS/InspectableControl')]:
            try:
                report[name] = not matching_pids(executable)
            except Exception as error:
                report[name] = False
                report[name + 'Error'] = str(error)
        save(output / 'results.json', report)


def run(session_path, physical_path, output, routes):
    session = json.loads(session_path.read_text())
    if session.get('target') != 'AgentFreeBrowserEngine':
        raise ValueError('Use the pinned engine-browser physical session')
    validate_physical(session, json.loads(physical_path.read_text()))
    verified_target()
    active(session)
    if matching_pids(ROOT / 'dist/InspectableControl.app/Contents/MacOS/InspectableControl'):
        raise RuntimeError('A readable reference already runs')
    oracle = Oracle(session['controller'])
    initial = oracle.state(session['trial'])
    if ('DEVICE_KEYBOARD bound=true' not in Path(session['log']).read_text()
            or not any(row['accepted'] for row in initial['submissions'])):
        raise RuntimeError('Need the completed physical control in this same process')
    output = fresh_output(output)
    report = {'status': 'inconclusive', 'candidatePID': session['pid'], 'candidateSHA256': session['binarySHA256'],
              'physicalInputAbsenceVerified': False, 'systemInputPosted': False,
              'AXActionsLimitedToDisposableFixture': True, 'rows': [],
              'scope': 'Single scoped snapshots and bounded host AX. No unfiltered display capture, renderer AX, or synthetic input.'}
    permissions = probe(['permissions'], output / 'permissions.json', background=True)
    report['permissions'] = permissions
    report['probeSHA256'] = permissions['probeBinarySHA256']
    save(output / 'results.json', report)
    if not permissions.get('accessibility') or not permissions.get('screenCapture'):
        raise RuntimeError('Existing observation grants are ineffective')
    binary = ROOT / 'dist/NativeProbe.app/Contents/MacOS/NativeProbe'
    try:
        for route in routes:
            if hashlib.sha256(binary.read_bytes()).hexdigest() != report['probeSHA256']:
                raise RuntimeError('The frozen observation probe changed')
            row = {'route': route, 'verdict': 'inconclusive'}
            report['rows'].append(row)
            row['before'] = reference(route, output / (route + '-before'), oracle)
            if not row['before']['worked']:
                row['reason'] = 'Readable reference failed; candidate skipped'
                save(output / 'results.json', report)
                continue
            active(session)
            row['candidate'] = observe(session, route, output / (route + '-candidate'), oracle)
            row['verdict'] = score(route, row['before'], row['candidate'], {})
            save(output / 'results.json', report)
            row['after'] = reference(route, output / (route + '-after'), oracle)
            row['verdict'] = score(route, row['before'], row['candidate'], row['after'])
            save(output / 'results.json', report)
            print(json.dumps({'route': route, 'verdict': row['verdict']}), flush=True)
            if row['verdict'] in ['bypass', 'partial-action-requires-review']:
                break
    finally:
        report['status'] = ('bypass' if any(row['verdict'] == 'bypass' for row in report['rows']) else
                            'inconclusive' if any(row['verdict'] in ['inconclusive', 'partial-action-requires-review']
                                                  for row in report['rows']) else
                            'completed-bounded-observation-suite')
        finish(report, session, oracle, binary, output)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--session', type=Path, required=True)
    parser.add_argument('--physical-control', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--routes', choices=ROUTES, nargs='+', default=ROUTES)
    args = parser.parse_args()
    run(args.session, args.physical_control, args.output, args.routes)
