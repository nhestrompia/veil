"""Exercise native descriptor handoff and two-child cleanup without elevation."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import time

from process_cleanup import matching_pids
from run_renderer_channel_control import ROOT, DISPLAY, fixture
from run_renderer_signal_reference import prefixed

LAUNCHER = ROOT / '.build/renderer-channel-launcher'
RENDERER = ROOT / 'dist/ChannelRendererProbe.app/Contents/MacOS/ChannelRendererProbe'


def records(stdout, prefix):
    return prefixed(stdout, prefix + ' ')


def cleanup_check(known):
    deadline = time.monotonic() + 6
    while True:
        live = {int(x) for x in subprocess.run(['/bin/ps', '-axo', 'pid='], capture_output=True, text=True, check=True).stdout.split()}
        remaining = sorted(set(known) & live)
        app_pids = sorted(matching_pids(RENDERER) | matching_pids(DISPLAY))
        if (not remaining and not app_pids) or time.monotonic() >= deadline:
            return {'remainingMeasuredPIDs': remaining, 'remainingAppPIDs': app_pids}
        time.sleep(0.05)


def collect(stdout):
    ready = records(stdout, 'CHANNEL_LAUNCHER_READY')
    if len(ready) != 1:
        raise ValueError('Expected one native launcher readiness record')
    known = [ready[0][key] for key in ('rendererPID', 'displayPID', 'watchdogPID')]
    renderer = records(stdout, 'CHANNEL_RENDERER_RESULT')
    if len(renderer) == 1:
        known += list(renderer[0]['rolePIDs'].values())
    return known


def run_trial(directory, mode, inherited=False):
    directory.mkdir()
    def signals():
        signal.signal(signal.SIGALRM, signal.SIG_IGN)
        signal.signal(signal.SIGCHLD, signal.SIG_IGN)
        signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGALRM, signal.SIGCHLD})
    with fixture() as (url, nonce, receipts):
        process = subprocess.Popen([str(LAUNCHER), mode, url], stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=signals if inherited else None)
        stdout, stderr = process.communicate(timeout=28)
    (directory / 'native.stdout').write_bytes(stdout)
    (directory / 'native.stderr').write_bytes(stderr)
    known = [process.pid, *collect(stdout)]
    final = records(stdout, 'CHANNEL_LAUNCHER_RESULT')
    if len(final) != 1:
        raise ValueError('Expected one native launcher result')
    final = final[0]
    checks = {'ordinaryUID': records(stdout, 'CHANNEL_LAUNCHER_READY')[0]['ordinaryUID'] == os.getuid(),
        'reapedChildren': final['rendererReaped'] and final['displayReaped'] and final['watchdogReaped'],
        'cleanup': final['cleanupVerified'] and final['watchdogNormalExit'],
        'boundedOutput': len(stdout) < 400 * 1024}
    if mode == '--control':
        renderer = records(stdout, 'CHANNEL_RENDERER_RESULT')
        display = records(stdout, 'CHANNEL_DISPLAY_RESULT')
        produced = records(stdout, 'CHANNEL_FRAME_PRODUCED')
        shown = records(stdout, 'CHANNEL_FRAME_PRESENTED')
        checks.update(normalExit=process.returncode == 0 and final['passed'],
            nativeControls=len(renderer) == len(display) == 1 and renderer[0]['completed'] and display[0]['completed'],
            fixture=len(receipts) == 1 and len(produced) > 2 and all(row['sample']['nonce'] == nonce for row in produced),
            pixels=len(shown) > 2 and display[0]['presented'] == len(shown),
            noVisibleWindows=renderer[0]['visibleWindows'] == display[0]['visibleWindows'] == 0,
            orderedStartup=final['displayStartedAfterRendererReady'],
            continuedAfterDisplayExit=any(row['channelClosed'] for row in produced))
    else:
        checks['controlledFailure'] = process.returncode == 1 and final['passed'] is False
        checks['expectedFailure'] = final['outputLimitExceeded'] if mode == '--output-limit-control' else final['deadlineReached']
    result = {'mode': mode, 'inheritedSignals': inherited, 'exitCode': process.returncode,
        'launcher': final, 'checks': checks, 'measuredPIDs': sorted(set(known)), **cleanup_check(known)}
    result['passed'] = all(checks.values()) and not result['remainingMeasuredPIDs'] and not result['remainingAppPIDs']
    (directory / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def parent_fault(directory, kind):
    directory.mkdir()
    with fixture() as (url, _, _):
        process = subprocess.Popen([str(LAUNCHER), '--stalled-control' if kind != 'closed-output' else '--control', url],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        if not select.select([process.stdout], [], [], 4)[0]:
            raise TimeoutError('No native launcher readiness')
        first = process.stdout.readline(65537)
        ready = records(first, 'CHANNEL_LAUNCHER_READY')
        if len(ready) != 1:
            raise ValueError('Expected initial launcher readiness')
        known = [process.pid, *collect(first)]
        if kind == 'parent-death':
            process.kill()
            stdout, stderr = process.communicate(timeout=8)
            expected = -signal.SIGKILL
        elif kind == 'group-termination':
            if os.getpgid(process.pid) != process.pid or os.getsid(ready[0]['watchdogPID']) != ready[0]['watchdogPID']:
                raise ValueError('Unexpected disposable process sessions')
            os.killpg(process.pid, signal.SIGTERM)
            stdout, stderr = process.communicate(timeout=8)
            expected = -signal.SIGTERM
        else:
            process.stdout.close()
            process.wait(timeout=8)
            stdout, stderr = b'', process.stderr.read()
            expected = 1
    (directory / 'native.stdout').write_bytes(first + stdout)
    (directory / 'native.stderr').write_bytes(stderr)
    result = {'kind': kind, 'exitCode': process.returncode, 'measuredPIDs': sorted(set(known)),
        'auxiliaryWebKitRolesMeasured': False, **cleanup_check(known)}
    result['passed'] = process.returncode == expected and not result['remainingMeasuredPIDs'] and not result['remainingAppPIDs']
    (directory / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def run(directory):
    if os.getuid() != 501 or os.geteuid() != os.getuid():
        raise ValueError('Use this Mac ordinary research account')
    directory = directory.resolve()
    if not directory.is_relative_to(ROOT / 'artifacts'):
        raise ValueError('Use a new workspace artifact directory')
    for binary in (LAUNCHER, RENDERER, DISPLAY):
        if matching_pids(binary): raise ValueError('Existing diagnostics must remain untouched')
    directory.mkdir()
    result = {'rootRun': False, 'ordinaryUID': os.getuid(), 'trials': [], 'faults': [],
        'binaryHashes': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (LAUNCHER, RENDERER, DISPLAY)}}
    modes = [('--control', False), ('--control', True), ('--control', False),
             ('--deadline-control', False), ('--output-limit-control', False), ('--stalled-control', False)]
    for index, (mode, inherited) in enumerate(modes):
        row = run_trial(directory / f'trial-{index+1}', mode, inherited)
        result['trials'].append(row)
        print(json.dumps({'trial': index+1, 'mode': mode, 'passed': row['passed']}), flush=True)
        if not row['passed']: break
    if len(result['trials']) == len(modes) and all(row['passed'] for row in result['trials']):
        for kind in ('parent-death', 'group-termination', 'closed-output'):
            row = parent_fault(directory / kind, kind)
            result['faults'].append(row)
            print(json.dumps({'fault': kind, 'passed': row['passed']}), flush=True)
            if not row['passed']: break
    refusals = []
    for args in ([], ['--root-smoke', 'http://127.0.0.1:8765/channel/0123456789abcdef'],
                 ['--control', 'https://example.com/'], ['--control', 'http://127.0.0.1:80/channel/0123456789abcdef'],
                 ['--control', 'http://127.0.0.1:8765/channel/0123456789abcdef?extra=1'],
                 ['--control', 'http://127.0.0.1:8765/channel/0123456789abcdeg']):
        refused = subprocess.run([str(LAUNCHER), *args], capture_output=True, timeout=3)
        refusals.append({'arguments': args, 'exitCode': refused.returncode, 'passed': refused.returncode == 64 and not refused.stdout})
    result['refusals'] = refusals
    result['passed'] = (len(result['trials']) == len(modes) and all(row['passed'] for row in result['trials'])
        and len(result['faults']) == 3 and all(row['passed'] for row in result['faults']) and all(row['passed'] for row in refusals))
    (directory / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    result = run(parser.parse_args().out)
    print(json.dumps({'passed': result['passed'], 'rootRun': False}))
    raise SystemExit(0 if result['passed'] else 1)
