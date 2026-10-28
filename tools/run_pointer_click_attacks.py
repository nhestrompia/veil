"""Run an approved, bounded native click matrix against the physical pointer session."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from native_environment import require_input_safety
from process_cleanup import matching_pids
from pointer_attempt_review import review
from run_device_session import active
from run_loaded_page_attacks import close, frame, prepare, translated_point
from run_native import ROOT, Oracle, probe, stop_timed_out_probe
from website_challenge import save

ROUTES = ['hid', 'session', 'private', 'curve-hid', 'pid-window-keycodes-hid']


def run(plan_path):
    if os.getuid() == 0:
        raise RuntimeError('Run as the ordinary user')
    plan = json.loads(plan_path.read_text())
    if plan.get('approved') is not True or plan.get('executed') is not False:
        raise RuntimeError('Need a fresh approved mouse-utility pause and native comparison plan')
    session_path = Path(plan['sessionFile'])
    session = json.loads(session_path.read_text())
    physical = json.loads(session_path.with_name('physical-control.json').read_text())
    if (session.get('target') != 'AgentFreeBrowserPointer' or session.get('fixtureSurface') != 'pointer-click'
            or physical.get('pid') != session['pid'] or physical.get('binarySHA256') != session['binarySHA256']
            or physical.get('userReportedPhysicalClick') is not True or physical.get('acceptedSubmissions') != 1):
        raise RuntimeError('Need the verified physical pointer click session')
    active(session)
    if (plan.get('routes') != ROUTES or plan.get('repetitions') not in [1, 2, 3]
            or plan.get('maximumSeconds') != 240
            or plan.get('modifierApps') != ['com.lujjjh.LinearMouse', 'com.ethanbills.DockDoor']):
        raise ValueError('Unsupported bounded comparison scope')
    helper = ROOT / '.build/ApprovedModifierPause'
    if hashlib.sha256(helper.read_bytes()).hexdigest() != plan['pauseHelperSHA256']:
        raise RuntimeError('The scoped modifier helper changed')
    if matching_pids(ROOT / 'dist/NativeProbe.app/Contents/MacOS/NativeProbe'):
        raise RuntimeError('Another native probe is running')
    output = Path(plan['output']).resolve()
    if not output.is_relative_to((ROOT / 'artifacts').resolve()):
        raise ValueError('Use a fresh project artifact directory')
    output.mkdir(exist_ok=False, parents=True, mode=0o700)
    original = output / 'original-apps.json'
    oracle = Oracle(session['controller'])
    report = {'pid': session['pid'], 'binarySHA256': session['binarySHA256'], 'results': [],
              'restored': False, 'initialOracle': oracle.state(session['trial']), 'armedPointerAttack': False,
              'scope': 'Loaded page after focus loss. Control launch disarms the pointer. No claim of an armed-pointer attack.'}
    plan.update(executed=True)
    save(plan_path, plan)

    def interrupted(_signal, _frame):
        raise TimeoutError('Native pointer comparison deadline reached')

    previous = {number: signal.signal(number, interrupted) for number in [signal.SIGINT, signal.SIGTERM, signal.SIGALRM]}
    signal.alarm(240)
    reference = None
    try:
        with (output / 'pause.log').open('w') as stream:
            subprocess.run([str(helper), 'pause', str(original)], check=True, stdout=stream, stderr=subprocess.STDOUT, timeout=20)
        permissions = probe(['permissions'], output / 'permissions.json', background=True)
        require_input_safety(permissions)
        if not permissions.get('postEvents') or not permissions.get('accessibility'):
            raise RuntimeError('The existing probe grants are ineffective')
        for repetition in range(plan['repetitions']):
            for route in ROUTES:
                active(session)
                prefix = output / f'{repetition}-{route}'
                reference = prepare('InspectableControl', prefix.with_name(prefix.name + '-control'), oracle)
                ax = probe(['ax', reference['pid']], prefix.with_suffix('.control-ax.json'), background=True)
                button = next((element for element in ax.get('elements', [])
                               if 'Record hardware click' in [element.get('AXTitle'), element.get('AXDescription')]
                               and 'position' in element and 'size' in element), None)
                if button is None:
                    raise RuntimeError('Matched readable click button unavailable')
                point = [button['position'][index] + button['size'][index] / 2 for index in [0, 1]]
                control_geometry = {'windowFrame': frame(reference['pid'], prefix.with_suffix('.control-frame.json')),
                                    'fieldCenter': point}
                control_before = oracle.state(reference['trial'])
                arguments = ['input', reference['pid'], *point, route if route in ['hid', 'session', 'private'] else 'hid']
                if route == 'curve-hid': arguments += ['curve']
                if route == 'pid-window-keycodes-hid': arguments += ['pid-window', 'keycodes']
                control_attempt = probe(arguments, prefix.with_suffix('.control-input.json'), background=True)
                time.sleep(.4)
                control_after = oracle.state(reference['trial'])
                control_worked = (control_attempt.get('status') == 'attempted'
                                  and any(item['accepted'] for item in control_after['submissions'][len(control_before['submissions']):]))
                close(reference)
                reference = None
                row = {'route': route, 'repetition': repetition, 'controlWorked': control_worked,
                       'controlAttempt': control_attempt, 'verdict': 'inconclusive'}
                report['results'].append(row)
                if not control_worked:
                    report['stopReason'] = 'Matched readable control failed; no candidate input for this route'
                    return report
                active(session)
                point = translated_point(control_geometry, frame(session['pid'], prefix.with_suffix('.candidate-frame.json')))
                before = oracle.state(session['trial'])
                log = Path(session['log'])
                offset = len(log.read_text())
                arguments[1:4] = [session['pid'], *point]
                row['candidateAttempt'] = probe(arguments, prefix.with_suffix('.candidate-input.json'), background=True)
                time.sleep(.4)
                after = oracle.state(session['trial'])
                delta = log.read_text()[offset:]
                row.update(newSubmissions=after['submissions'][len(before['submissions']):],
                           acceptedEvents=delta.count('INPUT_GATE_ACCEPTED'),
                           refusedEvents=delta.count('INPUT_GATE_REFUSED') + delta.count('INPUT_QUEUE_REFUSED'))
                row['interactionReview'] = review(before, after, delta)
                if any(item['accepted'] for item in row['newSubmissions']):
                    row['verdict'] = 'bypass'
                elif (row['candidateAttempt'].get('status') == 'attempted' and row['refusedEvents'] > 0
                      and row['interactionReview']['outcome'] == 'no-observed-interaction'):
                    row['verdict'] = 'blocked'
                save(output / 'results.json', report)
                if row['verdict'] != 'blocked':
                    report['stopReason'] = 'Failed or inconclusive candidate trial; stop further input'
                    return report
    except BaseException as error:
        report['error'] = str(error)
        raise
    finally:
        signal.alarm(0)
        try:
            if reference is not None:
                close(reference)
        except BaseException as error:
            report['referenceCleanupError'] = str(error)
        for path in output.glob('*.json.pid'):
            stop_timed_out_probe(path)
        remaining = matching_pids(ROOT / 'dist/NativeProbe.app/Contents/MacOS/NativeProbe')
        report['remainingProbePIDsBeforeRestore'] = sorted(remaining)
        if remaining:
            save(output / 'results.json', report)
            raise RuntimeError('Native posting process remains active; do not restore modifier hooks')
        try:
            if original.exists():
                with (output / 'restore.log').open('w') as stream:
                    subprocess.run([str(helper), 'restore', str(original)], check=True, stdout=stream, stderr=subprocess.STDOUT, timeout=20)
                report['restored'] = True
        except BaseException as error:
            report['restorationError'] = str(error)
            raise
        finally:
            for number, handler in previous.items():
                signal.signal(number, handler)
            try:
                report['finalOracle'] = oracle.state(session['trial'])
            except Exception as error:
                report['finalOracleError'] = str(error)
            save(output / 'results.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    result = run(parser.parse_args().plan)
    print(json.dumps({key: result.get(key) for key in ['results', 'stopReason', 'restored']}))
