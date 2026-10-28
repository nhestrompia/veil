"""Use remaining approved native trials after automatically detecting a physical re-arm."""

import argparse
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
from run_loaded_page_attacks import frame, translated_point
from run_native import ROOT, Oracle, probe, stop_timed_out_probe
from website_challenge import save


def armed(log):
    lines = [line for line in log.splitlines() if line.startswith('HARDWARE_POINTER armed=')]
    return bool(lines and lines[-1].startswith('HARDWARE_POINTER armed=true'))


def run(plan_path, output, session_path=None, reviewed_retry=False):
    if os.getuid() == 0:
        raise RuntimeError('Run as the ordinary user')
    plan = json.loads(plan_path.read_text())
    prior_output = Path(plan['output'])
    prior = json.loads((prior_output / 'results.json').read_text())
    session = json.loads((session_path or Path(plan['sessionFile'])).read_text())
    if (plan.get('approved') is not True or plan.get('executed') is not True or not prior.get('restored')
            or prior.get('binarySHA256') != session['binarySHA256']):
        raise RuntimeError('Need the approved completed comparison and unchanged live session')
    continuation = plan_path.with_name(plan_path.stem + ('-armed-reviewed-retry-consumed.json' if reviewed_retry else '-armed-consumed.json'))
    if continuation.exists():
        raise RuntimeError('The remaining armed comparison already ran')
    routes = [row for row in prior['results'] if row['verdict'] == 'blocked' and row['controlWorked']]
    if len(routes) != 4 or any(row['repetition'] != 0 for row in routes) or plan['repetitions'] != 3:
        raise RuntimeError('Need exactly the four calibrated routes with two remaining approved trials each')
    pause_used = (prior_output / 'restore.log').stat().st_mtime - (prior_output / 'pause.log').stat().st_mtime
    used = {row['route']: 1 for row in routes}
    if reviewed_retry:
        earlier = ROOT / 'artifacts/hardware-pointer-154/armed-native-clicks'
        overlap_assessment = json.loads((earlier / 'reviewed-assessment.json').read_text())
        attempted = json.loads((earlier / 'results.json').read_text())
        if (overlap_assessment.get('reviewedAssessment') != 'inconclusive-physical-input-overlap'
                or not attempted.get('restored') or attempted['binarySHA256'] != session['binarySHA256']):
            raise RuntimeError('Need the reviewed overlapping trial and unchanged candidate')
        for row in attempted['results']:
            if row.get('attempt', {}).get('status') == 'attempted': used[row['route']] += 1
        pause_used += (earlier / 'restore.log').stat().st_mtime - (earlier / 'pause.log').stat().st_mtime
    remaining_trials = {route: 3 - count for route, count in used.items()}
    if any(count < 0 or count > 2 for count in remaining_trials.values()):
        raise RuntimeError('Approved per-route trial budget exhausted')
    remaining_seconds = min(60, int(plan['maximumSeconds'] - pause_used - 10))
    if remaining_seconds < 40:
        raise RuntimeError('Insufficient remaining pause budget')
    output = output.resolve()
    if not output.is_relative_to((ROOT / 'artifacts').resolve()):
        raise ValueError('Use a fresh project artifact directory')
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    log = Path(session['log'])
    oracle = Oracle(session['controller'])
    before_wait = oracle.state(session['trial'])
    baseline_count = len(before_wait['submissions'])
    report = {'pid': session['pid'], 'binarySHA256': session['binarySHA256'], 'results': [],
              'originalApprovalPlan': str(plan_path), 'restored': False, 'status': 'waiting-for-physical-rearm',
              'pauseBudgetSecondsRemaining': remaining_seconds}
    save(output / 'results.json', report)
    print(json.dumps({'waitingForPhysicalClick': True, 'pid': session['pid']}), flush=True)
    deadline = time.monotonic() + 180
    quiet_since = None
    quiet_signature = None
    while time.monotonic() < deadline:
        active(session)
        state = oracle.state(session['trial'])
        new = state['submissions'][baseline_count:]
        text = log.read_text()
        if any(item['accepted'] for item in new) and armed(text):
            signature = (len(state['submissions']), text.count('INPUT_GATE_ACCEPTED'))
            if signature != quiet_signature:
                quiet_signature = signature
                quiet_since = time.monotonic()
            elif quiet_since is not None and time.monotonic() - quiet_since >= 10:
                break
        else:
            quiet_since = None
            quiet_signature = None
        time.sleep(.1)
    else:
        report['status'] = 'physical-rearm-not-observed'
        save(output / 'results.json', report)
        return report
    # The existing approval permits three trials per route. Only two remain.
    save(continuation, {'originalPlan': str(plan_path), 'pid': session['pid'], 'remainingTrialsByRoute': remaining_trials,
                        'routes': [row['route'] for row in routes], 'executed': True})
    report.update(status='running', oracleBefore=state, armedAtStart=True, quietSecondsBeforeInput=10,
                  remainingTrialsByRoute=remaining_trials, physicalInputAbsenceVerified=False,
                  reviewedRetry=reviewed_retry)
    helper = ROOT / '.build/ApprovedModifierPause'
    import hashlib
    if hashlib.sha256(helper.read_bytes()).hexdigest() != plan['pauseHelperSHA256']:
        raise RuntimeError('Scoped pause helper changed')
    if matching_pids(ROOT / 'dist/NativeProbe.app/Contents/MacOS/NativeProbe'):
        raise RuntimeError('Another native probe is running')
    original = output / 'original-apps.json'

    def interrupted(_signal, _frame):
        raise TimeoutError('Remaining native comparison budget reached')

    previous = {number: signal.signal(number, interrupted) for number in [signal.SIGINT, signal.SIGTERM, signal.SIGALRM]}
    signal.alarm(remaining_seconds)
    try:
        with (output / 'pause.log').open('w') as stream:
            subprocess.run([str(helper), 'pause', str(original)], check=True, stdout=stream, stderr=subprocess.STDOUT, timeout=20)
        permissions = probe(['permissions'], output / 'permissions.json', background=True)
        require_input_safety(permissions)
        if not permissions.get('postEvents'):
            raise RuntimeError('Existing posting grant ineffective')
        for remaining_index in range(max(remaining_trials.values())):
            for calibration in routes:
                if remaining_index >= remaining_trials[calibration['route']]: continue
                repetition = used[calibration['route']] + remaining_index
                active(session)
                if not armed(log.read_text()):
                    raise RuntimeError('Pointer disarmed; stop instead of claiming an armed attack')
                route = calibration['route']
                source_prefix = prior_output / f'0-{route}'
                ax = json.loads(source_prefix.with_suffix('.control-ax.json').read_text())
                button = next(element for element in ax['elements']
                              if 'Record hardware click' in [element.get('AXTitle'), element.get('AXDescription')]
                              and 'position' in element and 'size' in element)
                geometry = json.loads(source_prefix.with_suffix('.control-frame.json').read_text())
                window = next(window for window in geometry['windows'] if window.get('kCGWindowLayer') == 0)
                bounds = window['kCGWindowBounds']
                control = {'windowFrame': [bounds[key] for key in ['X', 'Y', 'Width', 'Height']],
                           'fieldCenter': [button['position'][i] + button['size'][i] / 2 for i in [0, 1]]}
                prefix = output / f'{repetition}-{route}'
                point = translated_point(control, frame(session['pid'], prefix.with_suffix('.frame.json')))
                before = oracle.state(session['trial'])
                offset = len(log.read_text())
                arguments = ['input', session['pid'], *point, route if route in ['hid', 'session', 'private'] else 'hid']
                if route == 'curve-hid': arguments += ['curve']
                attempt = probe(arguments, prefix.with_suffix('.input.json'), background=True)
                time.sleep(.4)
                after = oracle.state(session['trial'])
                delta = log.read_text()[offset:]
                row = {'route': route, 'repetition': repetition, 'attempt': attempt, 'controlEvidence': str(source_prefix),
                       'armedBefore': True, 'armedAfter': armed(log.read_text()),
                       'acceptedEvents': delta.count('INPUT_GATE_ACCEPTED'),
                       'refusedEvents': delta.count('INPUT_GATE_REFUSED') + delta.count('INPUT_QUEUE_REFUSED'),
                       'newSubmissions': after['submissions'][len(before['submissions']):], 'verdict': 'inconclusive'}
                row['interactionReview'] = review(before, after, delta)
                if any(item['accepted'] for item in row['newSubmissions']): row['verdict'] = 'bypass'
                elif (row['armedAfter'] and attempt.get('status') == 'attempted'
                      and row['interactionReview']['outcome'] == 'no-observed-interaction'
                      and row['refusedEvents'] > 0):
                    row['verdict'] = 'blocked'
                report['results'].append(row)
                save(output / 'results.json', report)
                if row['verdict'] != 'blocked':
                    report['status'] = row['verdict']
                    return report
        report['status'] = 'no-new-actions-in-calibrated-armed-trials'
    except BaseException as error:
        report.update(status='inconclusive', error=str(error))
        raise
    finally:
        signal.alarm(0)
        for path in output.glob('*.json.pid'): stop_timed_out_probe(path)
        remaining = matching_pids(ROOT / 'dist/NativeProbe.app/Contents/MacOS/NativeProbe')
        report['remainingProbePIDsBeforeRestore'] = sorted(remaining)
        if remaining:
            save(output / 'results.json', report)
            raise RuntimeError('Posting probe remains active; do not restore hooks')
        try:
            if original.exists():
                with (output / 'restore.log').open('w') as stream:
                    subprocess.run([str(helper), 'restore', str(original)], check=True, stdout=stream, stderr=subprocess.STDOUT, timeout=20)
                report['restored'] = True
        finally:
            for number, handler in previous.items(): signal.signal(number, handler)
            try: report['oracleAfter'] = oracle.state(session['trial'])
            except Exception as error: report['oracleError'] = str(error)
            save(output / 'results.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--session', type=Path)
    parser.add_argument('--reviewed-retry', action='store_true')
    args = parser.parse_args()
    print(json.dumps(run(args.plan, args.output, args.session, args.reviewed_retry)))
