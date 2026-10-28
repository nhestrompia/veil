"""Test focus-driven actions on the pinned browser without posting input."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import threading
import time

from fixture import FixtureServer
from process_cleanup import matching_pids
from run_device_session import active
from run_loaded_page_attacks import close, prepare
from run_native import ROOT, Oracle, probe
from run_preview_renderer_reads import validate_physical
from website_challenge import save


def accepted(state):
    return sum(bool(row.get('accepted')) for row in state['submissions'])


def focus(pid):
    result = subprocess.run([str(ROOT / '.build/PreviewLifecycleProbe'), 'activate', str(pid)],
                            check=True, capture_output=True, text=True, timeout=7)
    row = json.loads(result.stdout)
    if row.get('status') != 'observed' or row.get('inputPosted') is not False or row.get('hooksInstalled') is not False:
        raise RuntimeError('The scoped lifecycle helper did not report a valid operation')
    return row


def verdict(row, reference_worked):
    if (not reference_worked or row.get('stationaryNewActions') != 0 or row.get('acceptedInputEvents') != 0
            or not row.get('away', {}).get('targetActive') or not row.get('back', {}).get('targetActive')):
        return 'inconclusive'
    if any(s.get('accepted') for s in row.get('newSubmissions', [])):
        return 'agent-triggered-website-action'
    return 'no-action-observed'


def cycle(target, sink, oracle, reference_worked, actor=None):
    actor = actor or focus
    before = oracle.state(target['trial'])
    offset = len(target['log'].read_text())
    time.sleep(1)
    stationary = oracle.state(target['trial'])
    row = {'stationaryNewActions': accepted(stationary) - accepted(before), 'systemInputPosted': False,
           'AXActionSent': False, 'physicalInputAbsenceVerified': False}
    if row['stationaryNewActions']:
        row['verdict'] = 'inconclusive'
        return row
    row['away'] = actor(sink['pid'])
    time.sleep(.2)
    row['back'] = actor(target['pid'])
    time.sleep(.7)
    after = oracle.state(target['trial'])
    tail = target['log'].read_text()[offset:]
    row.update(newSubmissions=after['submissions'][len(stationary['submissions']):],
               acceptedInputEvents=tail.count('INPUT_GATE_ACCEPTED'),
               refusedInputEvents=tail.count('INPUT_GATE_REFUSED'))
    row['verdict'] = verdict(row, reference_worked)
    return row


def fresh_output(output):
    output = output.resolve()
    if not output.is_relative_to((ROOT / 'artifacts').resolve()):
        raise ValueError('Use a fresh project artifact directory')
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    return output


def calibrate(output):
    output = fresh_output(output)
    if matching_pids(ROOT / 'dist/InspectableControl.app/Contents/MacOS/InspectableControl'):
        raise RuntimeError('A readable research app already runs')
    server = FixtureServer(('127.0.0.1', 0), ROOT / 'tools/feature-fixture.html')
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    controller = output / 'controller.json'
    save(controller, {'port': server.server_port, 'key': server.controller_key})
    controller.chmod(0o600)
    oracle = Oracle(controller)
    reference = sink = None
    report = {'status': 'inconclusive', 'cycles': [], 'fixtureSurface': 'focus-action',
              'helperSHA256': hashlib.sha256((ROOT / '.build/PreviewLifecycleProbe').read_bytes()).hexdigest(),
              'fixtureSHA256': hashlib.sha256((ROOT / 'tools/feature-fixture.html').read_bytes()).hexdigest()}
    try:
        sink = prepare('InspectableControl', output / 'sink', oracle)
        reference = prepare('InspectableControl', output / 'reference', oracle,
                            '?surface=focus-action&observe-activity=1')
        report['arming'] = probe(['ax-action', reference['pid']], output / 'arming.json', background=True)
        time.sleep(.5)
        report['initialAcceptedActions'] = accepted(oracle.state(reference['trial']))
        if report['initialAcceptedActions'] != 1:
            raise RuntimeError('Need exactly one reference arming action')
        for _ in range(3):
            report['cycles'].append(cycle(reference, sink, oracle, True))
        if all(row['verdict'] == 'agent-triggered-website-action' for row in report['cycles']):
            report['status'] = 'calibrated'
    finally:
        cleanup_errors = []
        try:
            for host in [reference, sink]:
                if host is not None:
                    try:
                        close(host)
                    except Exception as error:
                        cleanup_errors.append(str(error))
            report['ownedHostsStopped'] = not cleanup_errors
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=3)
            report['fixtureStopped'] = not worker.is_alive()
            if cleanup_errors or worker.is_alive():
                report.update(status='inconclusive', cleanupErrors=cleanup_errors)
            save(output / 'results.json', report)
        if cleanup_errors or worker.is_alive():
            raise RuntimeError('The reference cleanup did not complete')
    return report


def run(session_path, physical_path, control_path, output):
    session = json.loads(session_path.read_text())
    validate_physical(session, json.loads(physical_path.read_text()))
    active(session)
    control = json.loads(control_path.read_text())
    if (control.get('status') != 'calibrated' or control.get('fixtureSurface') != 'focus-action'
            or control.get('ownedHostsStopped') is not True or control.get('fixtureStopped') is not True):
        raise RuntimeError('Need a calibrated focus-action reference')
    if session.get('fixtureSurface') != 'focus-action':
        raise RuntimeError('Need the matching focus-action preview session')
    output = fresh_output(output)
    oracle = Oracle(session['controller'])
    if accepted(oracle.state(session['trial'])) != 1:
        raise RuntimeError('Need exactly one physical arming action before the experiment')
    sink = None
    report = {'status': 'inconclusive', 'pid': session['pid'], 'binarySHA256': session['binarySHA256'],
              'fixtureSurface': 'focus-action', 'cycles': [], 'systemInputPosted': False,
              'helperSHA256': hashlib.sha256((ROOT / '.build/PreviewLifecycleProbe').read_bytes()).hexdigest()}
    try:
        sink = prepare('InspectableControl', output / 'sink', oracle)
        target = {**session, 'log': Path(session['log'])}
        for _ in range(3):
            active(session)
            row = cycle(target, sink, oracle, True)
            report['cycles'].append(row)
            save(output / 'results.json', report)
            if row.get('acceptedInputEvents', 0) or row.get('stationaryNewActions'):
                break
        if any(row.get('verdict') == 'agent-triggered-website-action' for row in report['cycles']):
            report['status'] = 'agent-triggered-website-action'
        elif len(report['cycles']) == 3 and all(row['verdict'] == 'no-action-observed' for row in report['cycles']):
            report['status'] = 'no-action-observed'
    finally:
        try:
            if sink is not None:
                close(sink)
            report['sinkStopped'] = True
            active(session)
        except Exception as error:
            report.update(status='inconclusive', cleanupError=str(error))
            raise
        finally:
            save(output / 'results.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--calibrate', action='store_true')
    parser.add_argument('--session', type=Path)
    parser.add_argument('--physical-control', type=Path)
    parser.add_argument('--control', type=Path)
    args = parser.parse_args()
    if args.calibrate:
        result = calibrate(args.output)
    else:
        if not all([args.session, args.physical_control, args.control]):
            parser.error('Use --calibrate or all three session/control paths')
        result = run(args.session, args.physical_control, args.control, args.output)
    print(json.dumps({'status': result['status'], 'cycles': result['cycles']}), flush=True)
