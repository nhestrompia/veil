"""Measure a fresh page challenge after calibrated renderer signal attempts."""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from process_cleanup import matching_pids
from run_headless_renderer_probe import collect_stdout
from run_renderer_signal_reference import actor_arguments, prefixed

ROOT = Path(__file__).resolve().parents[1]
BINARY = ROOT / 'dist/RendererProgressProbe.app/Contents/MacOS/RendererProgressProbe'
ACTOR = ROOT / '.build/renderer-progress-actor'
ROLES = ('host', 'content', 'gpu', 'network')


def identities(report, phase='servicesAfterSnapshot'):
    return {'host': report['host'], **{role: report[phase][role]['identity'] for role in ROLES[1:]}}


def verify_progress(ready, native, attack, isolated=False):
    initial = ready['progressBefore']
    after = native['progressAfter']
    nonce = ready['javascript']['nonce']
    signals = attack['signals']
    before_ids = identities(ready)
    expected_uid = 4294967294 if isolated else attack['actorUID']
    credentials = ('realUID', 'effectiveUID', 'savedUID')
    identity_stable = before_ids == identities(native) == identities(native, 'servicesAfterProgress')
    sampled_uid = all(all(record[key] == expected_uid for key in credentials)
                      for record in before_ids.values())
    ticks = initial['ticks'], after['ticks']
    timing = (ready['readyMonotonicNanoseconds'], attack['startedMonotonicNanoseconds'],
              attack['finishedMonotonicNanoseconds'], native['progressSampleStartedMonotonicNanoseconds'],
              native['progressSampleFinishedMonotonicNanoseconds'])
    checks = {
        'renderingBaseline': all(ready.get(key) is True for key in
            ('progressControl', 'javascriptPassed', 'snapshotPassed', 'baselineSnapshotPassed', 'serviceIdentityStable')),
        'freshDocumentChallenge': bool(nonce and initial['nonce'] == nonce == after['nonce']
            and native['expectedChallenge'] and after['challenge'] == native['expectedChallenge'] == after['domChallenge']),
        'timerProgress': all(type(value) is int for value in ticks) and 0 <= ticks[0] < ticks[1],
        'challengeStrictlyAfterActor': all(type(value) is int and value > 0 for value in timing)
            and all(first < second for first, second in zip(timing, timing[1:])),
        'stableRoleIdentities': identity_stable and sampled_uid
            and len({record['pid'] for record in before_ids.values()}) == 4,
        'calibratedActor': attack['exitCode'] == 0 and len(signals) == 4
            and {row['role'] for row in signals} == set(ROLES)
            and len(attack['footer']) == 1 and attack['footer'][0].get('passed') is True
            and attack['footer'][0].get('crossUser') is isolated
            and attack['footer'][0].get('recoveryComplete') is True
            and attack['footer'][0].get('watchdogReaped') is True
            and all(row['pid'] == before_ids[row['role']]['pid'] and row['expectedOutcome'] is True
                    and row['identityStable'] is True and row['notStoppedAfter'] is True
                    and row['actorUID'] == attack['actorUID'] and row['targetUID'] == expected_uid
                    and (row['stopReturn'] == -1 and row['stopErrno'] == 1 and row['observedStopped'] is False
                         and (row['continueReturn'] == -1 and row['continueErrno'] == 1
                              or row['continueReturn'] == 0 and row['sameSessionContinue'] is True
                              and row['actorPOSIXSession'] > 0 and row['actorPOSIXSession'] == row['targetPOSIXSession'])
                         if isolated else row['stopReturn'] == 0 and row['observedStopped'] is True and row['continueReturn'] == 0)
                    for row in signals),
        'postAttackRendering': all(native.get(key) is True for key in
            ('completed', 'progressPassed', 'progressIdentityStable', 'snapshotPassed'))
            and native['visibleWindowCountAtEnd'] == 0,
    }
    return {'passed': all(checks.values()), 'checks': checks}


def attack_renderer(ready, directory, isolated=False):
    args = actor_arguments(ready, isolated=isolated)
    args[0] = str(ACTOR)
    started = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
    process = subprocess.run(args, capture_output=True, timeout=9)
    finished = time.clock_gettime_ns(time.CLOCK_MONOTONIC)
    (directory / 'actor.stdout').write_bytes(process.stdout)
    (directory / 'actor.stderr').write_bytes(process.stderr)
    return {'actorUID': os.getuid(), 'exitCode': process.returncode,
            'startedMonotonicNanoseconds': started, 'finishedMonotonicNanoseconds': finished,
            'signals': prefixed(process.stdout, 'SIGNAL_RESULT '),
            'footer': prefixed(process.stdout, 'SIGNAL_ACTOR_RESULT ')}


def trial(directory, use_actor=True, supervised=False):
    directory.mkdir()
    ready = None
    attack = None
    result = {'passed': False, 'ordinaryUID': os.getuid(), 'rootRun': False,
              'useActor': use_actor, 'supervised': supervised}

    def receive(line):
        nonlocal ready, attack
        if line.startswith(b'RENDERER_PROGRESS_READY '):
            if ready is not None:
                raise ValueError('Duplicate readiness report')
            ready = json.loads(line.removeprefix(b'RENDERER_PROGRESS_READY '))
            if use_actor:
                attack = attack_renderer(ready, directory)

    with (directory / 'app.stderr').open('wb') as errors:
        args = [str(ROOT / '.build/renderer-progress-supervisor'), '--same-user-control'] if supervised else [str(BINARY), '--pipe-only']
        process = subprocess.Popen(args, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=errors)
        try:
            stdout = collect_stdout(process, timeout=28, limit=3 * 1024 * 1024, on_line=receive)
            (directory / 'app.stdout').write_bytes(stdout)
            reports = prefixed(stdout, 'HEADLESS_RENDERER_RESULT ')
            if ready is None or len(reports) != 1:
                raise ValueError('Expected readiness and one final report')
            native = reports[0]
            encoded = native.pop('snapshotPNGBase64', '')
            png = base64.b64decode(encoded, validate=True)
            if len(png) > 2 * 1024 * 1024 or not png.startswith(b'\x89PNG\r\n\x1a\n'):
                raise ValueError('Invalid final snapshot')
            (directory / 'snapshot.png').write_bytes(png)
            known = {record['pid'] for record in identities(ready).values()}
            if supervised:
                supervisors = prefixed(stdout, 'SUPERVISOR_RESULT ')
                supervisor_ready = prefixed(stdout, 'SUPERVISOR_READY ')
                if len(supervisors) != 1 or len(supervisor_ready) != 1 or supervisors[0].get('passed') is not True:
                    raise ValueError('The ordinary-user supervisor control failed')
                result.update(supervisor=supervisors[0], supervisorReady=supervisor_ready[0])
                known.add(supervisor_ready[0]['watchdogPID'])
            if attack:
                verification = verify_progress(ready, native, attack)
                result.update(actor=attack, verification=verification)
            else:
                result['verification'] = {'passed': all(native.get(key) is True for key in
                    ('completed', 'javascriptPassed', 'baselineSnapshotPassed', 'progressPassed',
                     'snapshotPassed', 'progressIdentityStable')) and native.get('visibleWindowCountAtEnd') == 0}
            deadline = time.monotonic() + 5
            while True:
                live = {int(value) for value in subprocess.run(['/bin/ps', '-axo', 'pid='],
                        capture_output=True, text=True, check=True).stdout.split()}
                remaining = sorted(known & live)
                if not remaining or time.monotonic() >= deadline:
                    break
                time.sleep(0.05)
            result.update(ready=ready, native=native, hostExitCode=process.returncode,
                          remainingMeasuredPIDs=remaining, snapshotSHA256=hashlib.sha256(png).hexdigest())
            result['passed'] = process.returncode == 0 and result['verification']['passed'] and not remaining
        except Exception as error:
            result.update(error=str(error), ready=ready, actor=attack)
        finally:
            if process.poll() is None:
                # The PID is this controller's unreaped direct child, never a reported service.
                process.send_signal(signal.SIGCONT)
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
            process.stdout.close()
    (directory / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def run(directory, supervised=False):
    if os.getuid() == 0 or os.geteuid() == 0:
        raise ValueError('Use an ordinary user')
    directory = directory.resolve()
    if not directory.is_relative_to(ROOT / 'artifacts'):
        raise ValueError('Use a workspace artifact directory')
    if matching_pids(BINARY) or matching_pids(ACTOR):
        raise ValueError('Existing research processes must remain untouched')
    directory.mkdir()
    result = {'rootRun': False, 'supervised': supervised,
              'binarySHA256': hashlib.sha256(BINARY.read_bytes()).hexdigest(),
              'actorSHA256': hashlib.sha256(ACTOR.read_bytes()).hexdigest(), 'references': []}
    result['baseline'] = trial(directory / 'baseline', use_actor=False, supervised=supervised)
    if result['baseline']['passed']:
        for index in range(3):
            reference = trial(directory / f'reference-{index+1}', supervised=supervised)
            result['references'].append(reference)
            if not reference['passed']:
                break
    result['passed'] = result['baseline']['passed'] and len(result['references']) == 3 \
        and all(item['passed'] for item in result['references'])
    (directory / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--supervised', action='store_true')
    args = parser.parse_args()
    result = run(args.out, supervised=args.supervised)
    print(json.dumps({'passed': result['passed'], 'references': len(result['references']), 'rootRun': False}))
    raise SystemExit(0 if result['passed'] else 1)
