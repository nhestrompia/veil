"""Run a separately approved, bounded native input-gate comparison on Veil."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from native_environment import require_input_safety
from pointer_attempt_review import review
from process_cleanup import matching_pids
from run_device_session import active
from run_loaded_page_attacks import arguments_for, close, prepare, translated_point
from run_native import ROOT, Oracle, probe, stop_timed_out_probe

ROUTES = ['hid', 'session', 'private', 'curve-hid', 'pid-keys-keycodes-hid']


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def window_frame(pid, path):
    data = probe(['ax', pid], path, background=True)
    windows = [e for e in data.get('elements', []) if e.get('AXRole') == 'AXWindow'
               and 'position' in e and 'size' in e]
    if len(windows) != 1:
        raise RuntimeError('Need exactly one owned research window with AX geometry')
    return windows[0]['position'] + windows[0]['size']


def run(plan_path):
    plan = json.loads(plan_path.read_text())
    if os.getuid() == 0 or plan.get('approved') is not True or plan.get('executed') is not False:
        raise RuntimeError('Need a fresh ordinary-user approval for this comparison')
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != plan['runnerSHA256']:
        raise RuntimeError('Reviewed runner changed')
    session_path = Path(plan['sessionFile'])
    session = json.loads(session_path.read_text())
    physical = json.loads(session_path.with_name('physical-control.json').read_text())
    if (session.get('target') != 'Veil' or session.get('fixtureSurface') != 'physical-mouse'
            or session['binarySHA256'] != plan['binarySHA256']
            or physical['pid'] != session['pid'] or physical['binarySHA256'] != session['binarySHA256']
            or physical['userResponse'] != 'Click recorded and wheel scrolls'):
        raise RuntimeError('Need the approved unchanged Veil physical control')
    if (plan.get('routes') != ROUTES or plan.get('repetitions') != 2
            or plan.get('maximumSeconds') != 240
            or plan.get('modifierApps') != ['com.lujjjh.LinearMouse', 'com.ethanbills.DockDoor']):
        raise ValueError('Unsupported comparison scope')
    helper = ROOT / '.build/ApprovedModifierPause'
    if hashlib.sha256(helper.read_bytes()).hexdigest() != plan['pauseHelperSHA256']:
        raise RuntimeError('Scoped pause helper changed')
    probe_binary = ROOT / 'dist/NativeProbe.app/Contents/MacOS/NativeProbe'
    if hashlib.sha256(probe_binary.read_bytes()).hexdigest() != plan['probeSHA256']:
        raise RuntimeError('Permissioned probe changed')
    if matching_pids(probe_binary):
        raise RuntimeError('Another native probe is running')
    active(session)
    output = Path(plan['output']).resolve()
    if not output.is_relative_to(ROOT / 'artifacts'):
        raise ValueError('Use a fresh artifact directory')
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    oracle = Oracle(session['controller'])
    log = Path(session['log'])
    report = {'binarySHA256': session['binarySHA256'], 'pid': session['pid'], 'results': [],
              'restored': False, 'taskCompletionComparison': False,
              'scope': 'Input admission after focus restoration. Candidate button is offscreen after human scrolling. This is not a matched task-completion or continuously bound-device test.'}
    original = output / 'original-apps.json'
    reference = None
    plan['executed'] = True
    save(plan_path, plan)

    def interrupted(_number, _frame):
        raise TimeoutError('Native comparison reached its four-minute limit')

    previous = {number: signal.signal(number, interrupted) for number in
                [signal.SIGINT, signal.SIGTERM, signal.SIGALRM]}
    signal.alarm(240)
    try:
        with (output / 'pause.log').open('w') as stream:
            subprocess.run([str(helper), 'pause', str(original)], stdout=stream,
                           stderr=subprocess.STDOUT, check=True, timeout=20)
        permissions = probe(['permissions'], output / 'permissions.json', background=True)
        report['permissions'] = permissions
        require_input_safety(permissions)
        if not permissions.get('postEvents') or not permissions.get('accessibility'):
            raise RuntimeError('The existing probe grants are ineffective')
        for repetition in range(2):
            for route in ROUTES:
                active(session)
                prefix = output / f'{repetition}-{route}'
                reference = prepare('InspectableControl', prefix.with_name(prefix.name + '-control'), oracle)
                ax = probe(['ax', reference['pid']], prefix.with_suffix('.control-ax.json'), background=True)
                button = next(e for e in ax.get('elements', [])
                              if 'Record physical click' in [e.get('AXTitle'), e.get('AXDescription')]
                              and 'position' in e and 'size' in e)
                point = [button['position'][i] + button['size'][i] / 2 for i in [0, 1]]
                geometry = {'windowFrame': window_frame(reference['pid'], prefix.with_suffix('.control-window.json')),
                            'fieldCenter': point}
                before = oracle.state(reference['trial'])
                control_attempt = probe(arguments_for(route, reference['pid'], point),
                                        prefix.with_suffix('.control-input.json'), background=True)
                time.sleep(.4)
                after = oracle.state(reference['trial'])
                worked = (control_attempt.get('status') == 'attempted'
                          and any(e['accepted'] for e in after['submissions'][len(before['submissions']):]))
                close(reference)
                reference = None
                row = {'route': route, 'repetition': repetition, 'controlWorked': worked,
                       'controlAttempt': control_attempt, 'verdict': 'inconclusive'}
                report['results'].append(row)
                if not worked:
                    report['stopReason'] = 'Readable control failed; candidate input skipped'
                    return report
                active(session)
                point = translated_point(geometry, window_frame(session['pid'], prefix.with_suffix('.veil-window.json')))
                before = oracle.state(session['trial'])
                offset = len(log.read_text())
                row['attempt'] = probe(arguments_for(route, session['pid'], point),
                                       prefix.with_suffix('.veil-input.json'), background=True)
                time.sleep(.4)
                after = oracle.state(session['trial'])
                delta = log.read_text()[offset:]
                row['interactionReview'] = review(before, after, delta)
                row['refusedEvents'] = delta.count('INPUT_GATE_REFUSED') + delta.count('INPUT_QUEUE_REFUSED')
                if row['interactionReview']['outcome'] != 'no-observed-interaction':
                    row['verdict'] = 'interaction-observed-origin-unresolved'
                elif row['attempt'].get('status') == 'attempted' and row['refusedEvents'] > 0:
                    row['verdict'] = 'input-gate-refused'
                save(output / 'results.json', report)
                if row['verdict'] != 'input-gate-refused':
                    report['stopReason'] = 'Observed interaction or inconclusive attempt; stop'
                    return report
        report['status'] = 'completed'
        return report
    except BaseException as error:
        report['error'] = str(error)
        raise
    finally:
        signal.alarm(0)
        try:
            if reference is not None:
                close(reference)
        finally:
            for path in output.glob('*.json.pid'):
                stop_timed_out_probe(path)
            remaining = matching_pids(probe_binary)
            report['remainingProbePIDsBeforeRestore'] = sorted(remaining)
            try:
                if remaining:
                    raise RuntimeError('Posting probe still runs; refuse restoring modifier hooks')
                if original.exists():
                    with (output / 'restore.log').open('w') as stream:
                        subprocess.run([str(helper), 'restore', str(original)], stdout=stream,
                                       stderr=subprocess.STDOUT, check=True, timeout=20)
                    report['restored'] = True
            finally:
                for number, handler in previous.items():
                    signal.signal(number, handler)
                save(output / 'results.json', report)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    print(json.dumps(run(parser.parse_args().plan)))
