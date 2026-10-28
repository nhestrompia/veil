"""Compare native and stable engine policies in the combined browser code."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import threading
import time

from build_focus_browser import MANIFEST, digest
from engine_runtime import BASE, verify_content
from fixture import FixtureServer
from launch_focus_browser import launch
from process_cleanup import matching_pids, stop_launched
from run_loaded_page_attacks import close, prepare
from run_native import ROOT, Oracle
from website_challenge import save

CASES = {
    'focus': ('focus-action', False, None),
    'password-focus': ('focus-action', True, None),
    'blur': ('blur-action', False, None),
    'visibility': ('visibility-action', False, None),
    'iframe-focus': ('focus-action', False, 'iframe'),
    'cross-frame-focus': ('focus-action', False, 'cross-frame'),
}


def accepted(state):
    return sum(bool(row['accepted']) for row in state['submissions'])


def wait_for(check, seconds=20):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if check():
            return
        time.sleep(.1)
    raise RuntimeError('The bounded fixture control did not become ready')


def activate(pid, operation='activate'):
    helper = ROOT / '.build/FocusEngineActivation'
    manifest = json.loads(MANIFEST.read_text())
    if digest(helper) != manifest['activationHelperSHA256']:
        raise RuntimeError('The activation helper changed')
    result = subprocess.run([str(helper), operation, str(pid)],
                            capture_output=True, text=True, timeout=7)
    row = json.loads(result.stdout)
    reached = row.get('hidden') is True if operation == 'hide' else (
        row.get('hidden') is False if operation == 'unhide' else row.get('active') is True)
    if (result.returncode != 0 or row.get('status') != 'observed' or not reached
            or row.get('inputPosted') is not False or row.get('hooksInstalled') is not False):
        raise RuntimeError('The scoped native operation did not complete: ' + json.dumps(row))
    row['measuredEndStateReached'] = reached
    return row


def native_state(log):
    rows = [json.loads(line.removeprefix('FOCUS_CONTROL_STATE ')) for line in log.read_text().splitlines()
            if line.startswith('FOCUS_CONTROL_STATE ')]
    if not rows:
        raise RuntimeError('No native state sample exists')
    return rows[-1]


def cycle(target, sink, oracle, hide=False):
    started = time.monotonic()
    before = oracle.state(target['trial'])
    offset = len(target['log'].read_text())
    time.sleep(1)
    stationary = oracle.state(target['trial'])
    row = {'stationaryNewActions': accepted(stationary) - accepted(before),
           'nativeBefore': native_state(target['log']), 'externalInputPosted': False}
    if row['stationaryNewActions']:
        raise RuntimeError('The stationary fixture changed before activation')
    if hide:
        row['hide'] = activate(target['pid'], 'hide')
    row['away'] = activate(sink['pid'])
    time.sleep(.3)
    row['nativeWhileAway'] = native_state(target['log'])
    if hide:
        row['unhide'] = activate(target['pid'], 'unhide')
    row['back'] = activate(target['pid'])
    time.sleep(.7)
    row['nativeAfterReturn'] = native_state(target['log'])
    after = oracle.state(target['trial'])
    tail = target['log'].read_text()[offset:]
    row.update(newSubmissions=after['submissions'][len(stationary['submissions']):],
               newEvents=after['events'][len(stationary['events']):],
               admittedInput=tail.count('INPUT_GATE_ACCEPTED'), elapsedSeconds=time.monotonic() - started)
    if row['admittedInput'] or row['nativeWhileAway']['foreground'] or row['nativeWhileAway']['keyWindow']:
        raise RuntimeError('Native eligibility or admitted input invalidates the activation-only interval')
    if not row['nativeAfterReturn']['foreground'] or not row['nativeAfterReturn']['keyWindow']:
        raise RuntimeError('The research browser did not regain real focus')
    return row


def score(cycles, native, resumed, password):
    if not native and any(row.get('stationaryNewActions') == 0 and row.get('admittedInput') == 0
                          and any(item.get('accepted') for item in row.get('newSubmissions', [])) for row in cycles):
        return 'agent-triggered-website-action'
    if (len(cycles) != 3 or resumed != 1
            or any(row.get('stationaryNewActions') != 0 or row.get('admittedInput') != 0 for row in cycles)):
        return 'inconclusive'
    if password and any(row['nativeWhileAway']['viewSecureOwner'] != 'false'
                        or row['nativeAfterReturn']['viewSecureOwner'] != 'true' for row in cycles):
        return 'inconclusive'
    actions = [accepted({'submissions': row['newSubmissions']}) for row in cycles]
    if native:
        return 'native-route-reproduced' if all(value > 0 for value in actions) else 'inconclusive'
    return 'agent-triggered-website-action' if any(actions) else 'no-action-with-resumed-typing'


def compare_case(output, oracle, name, mode, recovery=False):
    surface, password, frame = CASES[name]
    folder = output / (mode + '-' + name)
    folder.mkdir(mode=0o700)
    trial = oracle.create()
    query = '?surface=' + surface + '&observe-activity=1'
    if password:
        query += '&field-kind=password'
    if frame:
        query += '&frame-container=' + frame
    command = folder / 'command.json'
    save(command, {'id': 0, 'operation': 'wait'})
    command.chmod(0o600)
    log = folder / 'browser.log'
    report = {'status': 'inconclusive', 'mode': mode, 'case': name, 'trial': trial,
              'humanBaseline': False, 'diagnosticInputOnly': True, 'cycles': []}
    target = None
    sink = None
    launcher = binary = None
    try:
        sink = prepare('InspectableControl', folder / 'sink', oracle)
        target_name = 'FocusEngineNativeControl' if mode == 'native' else 'FocusEngineStableControl'
        launcher, binary = launch(log, ['--url', trial['url'] + query, '--command', str(command)], target_name)
        wait_for(lambda: 'FOCUS_CONTROL ready=true' in log.read_text()
                 and accepted(oracle.state(trial)) >= 1)
        if accepted(oracle.state(trial)) != 1:
            raise RuntimeError('Need exactly one owner-generated initial action')
        match = re.search(r'Browser ready: pid=(\d+)', log.read_text())
        if match is None:
            raise RuntimeError('No browser PID was reported')
        target = {'pid': int(match[1]), 'trial': trial, 'log': log}
        report['pid'] = target['pid']
        report['engineIdentity'] = verify_content(log, BASE / 'output/Release', folder / 'engine.json')
        for _ in range(3):
            report['cycles'].append(cycle(target, sink, oracle, hide=surface == 'visibility-action'))
        baseline = accepted(oracle.state(trial))
        save(command, {'id': 1, 'operation': 'resume'})
        wait_for(lambda: 'commandCompleted=1 operation=resume' in log.read_text())
        time.sleep(.3)
        report['resumedNewActions'] = accepted(oracle.state(trial)) - baseline
        report['status'] = score(report['cycles'], mode == 'native', report['resumedNewActions'], password)
        if recovery and mode == 'stable' and name == 'focus':
            # The owner requests a reload. It does not send an OS signal or expose a shipping command channel.
            baseline = accepted(oracle.state(trial))
            save(command, {'id': 2, 'operation': 'reload'})
            wait_for(lambda: 'commandCompleted=2 operation=reload' in log.read_text())
            time.sleep(.3)
            report['reloadControlNewActions'] = accepted(oracle.state(trial)) - baseline
            report['postReloadCycle'] = cycle(target, sink, oracle)
            baseline = accepted(oracle.state(trial))
            save(command, {'id': 3, 'operation': 'resume'})
            wait_for(lambda: 'commandCompleted=3 operation=resume' in log.read_text())
            time.sleep(.3)
            report['secondResumeNewActions'] = accepted(oracle.state(trial)) - baseline
            if (report['reloadControlNewActions'] != 1 or report['secondResumeNewActions'] != 1
                    or report['postReloadCycle']['newSubmissions']):
                report['status'] = 'inconclusive'
        report['oracleFinal'] = oracle.state(trial)
    except Exception as error:
        report.update(status=score(report['cycles'], mode == 'native', report.get('resumedNewActions'), password),
                      error=str(error))
    finally:
        report['oracleFinal'] = oracle.state(trial)
        report['targetStopped'] = stop_launched(launcher, binary, target['pid'] if target else None)
        if launcher is not None:
            launcher.wait(timeout=5)
        try:
            if sink is not None:
                close(sink)
                report['sinkStopped'] = True
            if not report['targetStopped']:
                report['cleanupIncomplete'] = True
                if report['status'] != 'agent-triggered-website-action':
                    report['status'] = 'inconclusive'
        finally:
            save(folder / 'results.json', report)
    return report


def run(output, cases):
    output = output.resolve()
    if not output.is_relative_to((ROOT / 'artifacts').resolve()):
        raise ValueError('Use a fresh project artifact directory')
    owned = [ROOT / 'dist/InspectableControl.app/Contents/MacOS/InspectableControl',
             ROOT / 'dist/AgentFreeBrowserEngine.app/Contents/MacOS/AgentFreeBrowserEngine',
             ROOT / 'dist/AgentFreeBrowserPreview.app/Contents/MacOS/AgentFreeBrowserPreview',
             *[ROOT / f'.build/{name}.app/Contents/MacOS/{name}'
               for name in ['FocusEngineNativeControl', 'FocusEngineStableControl']]]
    if any(matching_pids(binary) for binary in owned):
        raise RuntimeError('A research browser already runs; keep UI comparisons serial')
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    server = FixtureServer(('127.0.0.1', 0), ROOT / 'tools/feature-fixture.html')
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    controller = output / 'controller.json'
    save(controller, {'port': server.server_port, 'key': server.controller_key})
    controller.chmod(0o600)
    oracle = Oracle(controller)
    report = {'status': 'inconclusive', 'humanBaseline': False, 'cases': [],
              'manifestSHA256': digest(MANIFEST), 'fixtureSHA256': digest(ROOT / 'tools/feature-fixture.html')}
    try:
        for name in cases:
            before = compare_case(output, oracle, name, 'native')
            report['cases'].append(before)
            save(output / 'results.json', report)
            print(json.dumps({'case': name, 'mode': 'native', 'status': before['status']}), flush=True)
            if before['status'] != 'native-route-reproduced':
                break
            after = compare_case(output, oracle, name, 'stable', recovery=True)
            report['cases'].append(after)
            save(output / 'results.json', report)
            print(json.dumps({'case': name, 'mode': 'stable', 'status': after['status']}), flush=True)
            if after['status'] != 'no-action-with-resumed-typing':
                break
        if len(report['cases']) == len(cases) * 2 and all(
                row['status'] == ('native-route-reproduced' if row['mode'] == 'native'
                                  else 'no-action-with-resumed-typing') for row in report['cases']):
            report['status'] = 'diagnostic-regression-passed'
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        report['fixtureStopped'] = not thread.is_alive()
        if thread.is_alive():
            report['status'] = 'inconclusive'
        save(output / 'results.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cases', nargs='+', choices=CASES, default=list(CASES))
    args = parser.parse_args()
    result = run(args.output, args.cases)
    print(json.dumps({'status': result['status'], 'fixtureStopped': result['fixtureStopped']}))
    raise SystemExit(0 if result['status'] == 'diagnostic-regression-passed' else 1)
