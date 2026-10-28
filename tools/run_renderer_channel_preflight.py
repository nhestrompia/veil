"""Calibrate the separate channel supervisor and actors as the ordinary user."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from process_cleanup import matching_pids
from run_renderer_channel_control import ROOT, fixture
import run_renderer_channel_launcher as lifecycle
from run_renderer_signal_reference import prefixed

SUPERVISOR = ROOT / '.build/renderer-channel-supervisor'
RENDERER = ROOT / 'dist/ChannelIsolatedRendererProbe.app/Contents/MacOS/ChannelIsolatedRendererProbe'
DISPLAY = ROOT / 'dist/ChannelIsolatedDisplayProbe.app/Contents/MacOS/ChannelIsolatedDisplayProbe'
RENDERER_ACTOR = ROOT / '.build/channel-renderer-signal-actor'
DISPLAY_ACTOR = ROOT / '.build/channel-display-signal-actor'
USER_KEYS = ('realUID', 'effectiveUID', 'savedUID')
GROUP_KEYS = ('realGID', 'effectiveGID', 'savedGID')


def records(raw, prefix):
    return prefixed(raw, prefix + ' ')


def identity_arguments(identity):
    values = [identity[key] for key in ('pid', 'startedSeconds', 'startedMicroseconds')]
    if any(type(value) is not int or value < 0 for value in values) or values[0] <= 1 or values[2] >= 1000000:
        raise ValueError('Invalid exact process identity')
    return [str(value) for value in values]


def actor(directory, native, display, isolated=False):
    identities = [display['host']] if display else [native['host'], *[native['services'][role] for role in ('content', 'gpu', 'network')]]
    binary = DISPLAY_ACTOR if display else RENDERER_ACTOR
    arguments = [str(binary), '--cross-user' if isolated and not display else '--reference']
    for identity in identities:
        arguments.extend(identity_arguments(identity))
    result = subprocess.run(arguments, stdin=subprocess.DEVNULL, capture_output=True, timeout=9)
    path = directory / ('display-actor' if display else 'renderer-actor')
    path.with_suffix('.stdout').write_bytes(result.stdout)
    path.with_suffix('.stderr').write_bytes(result.stderr)
    rows = records(result.stdout, 'SIGNAL_RESULT')
    footer = records(result.stdout, 'SIGNAL_ACTOR_RESULT')
    stopped = records(result.stdout, 'SIGNAL_STOPPED')
    return {'exitCode': result.returncode, 'signals': rows, 'footer': footer, 'stopped': stopped,
        'intervals': records(result.stdout, 'CHANNEL_PAUSE_INTERVAL'),
        'finishedNanoseconds': time.clock_gettime_ns(time.CLOCK_MONOTONIC)}


def one(raw, prefix):
    rows = records(raw, prefix)
    if len(rows) != 1: raise ValueError('Expected one ' + prefix)
    return rows[0]


def verify(raw, attacks, nonce, receipts, isolated=False):
    launch = one(raw, 'CHANNEL_LAUNCHER_READY')
    ready = one(raw, 'CHANNEL_ATTACK_READY')
    display_ready = one(raw, 'CHANNEL_DISPLAY_READY')
    renderer = one(raw, 'CHANNEL_RENDERER_RESULT')
    display = one(raw, 'CHANNEL_DISPLAY_RESULT')
    final = one(raw, 'CHANNEL_LAUNCHER_RESULT')
    identities = one(raw, 'CHANNEL_LAUNCHER_IDENTITIES')
    produced = records(raw, 'CHANNEL_FRAME_PRODUCED')
    shown = records(raw, 'CHANNEL_FRAME_PRESENTED')
    expected_uid = 4294967294 if isolated else os.getuid()
    expected_gid = 4294967294 if isolated else os.getgid()
    renderer_identities = [ready['host'], *[ready['services'][role] for role in ('content', 'gpu', 'network')]]
    def credentials(identity, uid, gid):
        return all(identity.get(key) == uid for key in USER_KEYS) and all(identity.get(key) == gid for key in GROUP_KEYS)
    checks = {'nativeCompleted': final['passed'] and renderer['completed'] and display['completed'],
        'allChildrenReaped': final['rendererReaped'] and final['displayReaped'] and final['watchdogReaped'] and final['watchdogNormalExit'],
        'cleanup': final['cleanupVerified'], 'noVisibleWindows': renderer['visibleWindows'] == display['visibleWindows'] == 0,
        'identityChecks': identities['initialKernelChecks'] and identities['rendererPostExec'] and identities['displayPostExec'] and not identities['identityViolation'],
        'rendererCredentials': all(credentials(item, expected_uid, expected_gid) for item in renderer_identities),
        'displayCredentials': credentials(display_ready['host'], os.getuid(), os.getgid()),
        'launcherIdentityBinding': launch['rendererPID'] == ready['host']['pid'] and launch['displayPID'] == display_ready['host']['pid']
            and launch['rendererUID'] == expected_uid and launch['displayUID'] == os.getuid()
            and launch['permanentDropChecked'] is isolated and launch['rootRun'] is isolated,
        'stableIdentities': renderer['host'] == ready['host'] and renderer['services'] == ready['services'] and renderer['serviceIdentitiesStable'],
        'fixture': renderer['acceptedCommands'] == 1 and renderer['refusedCommands'] == 0 and len(receipts) == 1
            and ready['sample']['nonce'] == nonce and all(row['sample']['nonce'] == nonce for row in produced),
        'pixelPresentation': len(shown) > 2 and display['presented'] == len(shown),
        'boundedQueue': renderer['peakBufferedBytes'] <= 2 * (2 * 1024 * 1024 + 48)}
    known = {launch[key] for key in ('rendererPID', 'displayPID', 'watchdogPID')} | {item['pid'] for item in renderer_identities}
    for kind, expected in (('renderer', renderer_identities), ('display', [display_ready['host']])):
        attack = attacks[kind]
        rows = attack['signals']
        checks[kind + 'ActorBound'] = (attack['exitCode'] == 0 and len(rows) == len(expected)
            and [row['pid'] for row in rows] == [item['pid'] for item in expected]
            and all(row['identityStable'] and row['notStoppedAfter'] and row['expectedOutcome'] for row in rows)
            and len(attack['footer']) == 1 and attack['footer'][0]['passed'] and attack['footer'][0]['watchdogReaped'])
        checks[kind + 'Signals'] = all(row['stopReturn'] == -1 and row['stopErrno'] == 1 and not row['observedStopped'] for row in rows) if isolated and kind == 'renderer' else (
            all(row['stopReturn'] == row['continueReturn'] == 0 and row['observedStopped'] for row in rows))
        known.update(row['watchdogPID'] for row in attack['stopped'])
    intervals = attacks['display']['intervals']
    if len(intervals) != 1: raise ValueError('Missing display pause interval')
    start, end = intervals[0]['beganNanoseconds'], intervals[0]['endedNanoseconds']
    inside = [row for row in produced if start < row['startedNanoseconds'] < row['finishedNanoseconds'] < end]
    checks['pageProgressDuringDisplayPause'] = len(inside) >= 2 and inside[-1]['sample']['ticks'] > inside[0]['sample']['ticks']
    checks['pageProgressAfterRendererActor'] = any(row['startedNanoseconds'] > attacks['renderer']['finishedNanoseconds']
        and row['sample']['ticks'] > ready['sample']['ticks'] for row in produced)
    checks['freshPixelsAfterResume'] = any(row['presentedNanoseconds'] > end for row in shown) and display['staleFrames'] > 0
    checks['realBackpressure'] = renderer['wouldBlock'] > 0 and renderer['replacedFrames'] > 0
    checks['progressAfterDisplayExit'] = any(row['channelClosed'] for row in produced)
    return {'passed': all(checks.values()), 'checks': checks, 'framesDuringDisplayPause': len(inside),
        'measuredPIDs': sorted(known), 'ready': ready, 'displayReady': display_ready, 'renderer': renderer,
        'display': display, 'launcher': final, 'identities': identities}


def trial(directory):
    directory.mkdir()
    result = {'passed': False, 'rootRun': False}
    with fixture() as (url, nonce, receipts):
        stdout_path = directory / 'supervisor.stdout'
        with stdout_path.open('wb') as output, (directory / 'supervisor.stderr').open('wb') as errors:
            process = subprocess.Popen([str(SUPERVISOR), '--control', url], stdin=subprocess.DEVNULL, stdout=output, stderr=errors)
            try:
                deadline = time.monotonic() + 7
                while time.monotonic() < deadline:
                    raw = stdout_path.read_bytes()
                    if len(raw) > 400 * 1024: raise ValueError('Oversized native output')
                    complete = raw.rsplit(b'\n', 1)[0] + b'\n' if b'\n' in raw else b''
                    if records(complete, 'CHANNEL_ATTACK_READY') and records(complete, 'CHANNEL_FRAME_PRESENTED'): break
                    if process.poll() is not None: raise ValueError('Native control ended before attack readiness')
                    time.sleep(0.01)
                else: raise TimeoutError('No calibrated page and display readiness')
                native = one(complete, 'CHANNEL_ATTACK_READY')
                display = one(complete, 'CHANNEL_DISPLAY_READY')
                attacks = {'renderer': actor(directory, native, None)}
                attacks['display'] = actor(directory, native, display)
                process.wait(timeout=24)
                raw = stdout_path.read_bytes()
                verification = verify(raw, attacks, nonce, receipts)
                known = [process.pid, *verification['measuredPIDs']]
                lifecycle.RENDERER, lifecycle.DISPLAY = RENDERER, DISPLAY
                cleanup = lifecycle.cleanup_check(known)
                result.update(exitCode=process.returncode, attacks=attacks, verification=verification,
                    measuredPIDs=known, **cleanup)
                result['passed'] = process.returncode == 0 and verification['passed'] and not cleanup['remainingMeasuredPIDs'] and not cleanup['remainingAppPIDs']
            except Exception as error:
                result['error'] = str(error)
            finally:
                # This ordinary controller waits for the native own-child deadline.
                process.wait(timeout=28)
    (directory / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def run(directory):
    if os.getuid() != 501 or os.geteuid() != os.getuid(): raise ValueError('Use the ordinary research account')
    directory = directory.resolve()
    if not directory.is_relative_to(ROOT / 'artifacts'): raise ValueError('Use a new workspace artifact directory')
    binaries = (SUPERVISOR, RENDERER, DISPLAY, RENDERER_ACTOR, DISPLAY_ACTOR)
    if any(matching_pids(path) for path in binaries): raise ValueError('Existing diagnostics must remain untouched')
    directory.mkdir()
    result = {'rootRun': False, 'ordinaryUID': os.getuid(), 'comparisons': [],
        'binaryHashes': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in binaries}}
    for index in range(3):
        row = trial(directory / f'comparison-{index+1}')
        result['comparisons'].append(row)
        print(json.dumps({'comparison': index+1, 'passed': row['passed'], 'error': row.get('error')}), flush=True)
        if not row['passed']: break
    result['passed'] = len(result['comparisons']) == 3 and all(row['passed'] for row in result['comparisons'])
    if result['passed']:
        lifecycle.LAUNCHER, lifecycle.RENDERER, lifecycle.DISPLAY = SUPERVISOR, RENDERER, DISPLAY
        result['lifecycle'] = lifecycle.run(directory / 'lifecycle')
        result['passed'] = result['lifecycle']['passed']
    (directory / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    result = run(parser.parse_args().out)
    print(json.dumps({'passed': result['passed'], 'rootRun': False}))
    raise SystemExit(0 if result['passed'] else 1)
