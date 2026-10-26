"""Calibrate the ordinary-user signal actor against disposable renderers."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import time

from prepare_renderer_identity_run import APP, ROOT, SUPERVISOR
from process_cleanup import matching_pids
from run_headless_renderer_probe import collect_stdout

ACTOR = ROOT / '.build/renderer-signal-actor'


def actor_arguments(native, isolated=False):
    identities = [native['host']] + [native['servicesAfterSnapshot'][role]['identity']
                                    for role in ('content', 'gpu', 'network')]
    values = []
    for identity in identities:
        for key in ('pid', 'startedSeconds', 'startedMicroseconds'):
            value = identity[key]
            if type(value) is not int or value < 0:
                raise ValueError('Invalid process identity')
            values.append(str(value))
    return [str(ACTOR), '--cross-user' if isolated else '--reference', *values]


def prefixed(output, prefix):
    return [json.loads(line[len(prefix):]) for line in output.decode().splitlines() if line.startswith(prefix)]


def run_actor(native, output, interrupt=False):
    process = subprocess.Popen(actor_arguments(native), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if not interrupt:
        stdout, stderr = process.communicate(timeout=9)
    else:
        data = bytearray()
        deadline = time.monotonic() + 3
        stopped = None
        while time.monotonic() < deadline:
            if select.select([process.stdout], [], [], 0.1)[0]:
                block = os.read(process.stdout.fileno(), 8192)
                if not block:
                    break
                data.extend(block)
                if len(data) > 16384:
                    raise RuntimeError('Unexpected actor output')
                rows = prefixed(bytes(data).rsplit(b'\n', 1)[0] + b'\n', 'SIGNAL_STOPPED ')
                if rows:
                    stopped = rows[0]
                    break
        if not stopped or not stopped['observed']:
            process.terminate()
            process.communicate(timeout=7)
            raise RuntimeError('The recovery control did not observe its stopped target')
        process.kill()
        tail, stderr = process.communicate(timeout=2)
        stdout = bytes(data) + tail
    output.with_suffix('.stdout').write_bytes(stdout)
    output.with_suffix('.stderr').write_bytes(stderr)
    rows = prefixed(stdout, 'SIGNAL_RESULT ')
    footer = prefixed(stdout, 'SIGNAL_ACTOR_RESULT ')
    result = {'exitCode': process.returncode, 'signals': rows, 'footer': footer,
              'interrupted': interrupt, 'actorUID': os.getuid()}
    if interrupt:
        result['stopped'] = stopped
        result['verified'] = process.returncode == -signal.SIGKILL
    else:
        result['verified'] = (process.returncode == 0 and len(rows) == 4
            and len(footer) == 1 and footer[0].get('passed') is True
            and all(row.get('expectedOutcome') is True for row in rows))
    return result


def trial(directory, interrupt=False):
    directory.mkdir()
    process = subprocess.Popen([str(SUPERVISOR), '--same-user-control'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    native = None
    attack = None

    def receive(line):
        nonlocal native, attack
        if line.startswith(b'HEADLESS_RENDERER_RESULT '):
            if native is not None:
                raise RuntimeError('Duplicate native report')
            native = json.loads(line[len(b'HEADLESS_RENDERER_RESULT '):])
            native.pop('snapshotPNGBase64', None)
            attack = run_actor(native, directory / 'actor', interrupt)

    try:
        output = collect_stdout(process, on_line=receive)
        (directory / 'supervisor.stdout').write_bytes(output)
        errors = process.stderr.read()
        (directory / 'supervisor.stderr').write_bytes(errors)
        footer = prefixed(output, 'SUPERVISOR_RESULT ')
        known = set()
        if native:
            known = {native['host']['pid']} | {native['servicesAfterSnapshot'][role]['pid']
                                               for role in ('content', 'gpu', 'network')}
        if attack and interrupt:
            known.add(attack['stopped']['watchdogPID'])
        deadline = time.monotonic() + 5
        while True:
            live = {int(line.split()[0]) for line in subprocess.run(['ps', '-axo', 'pid='],
                    capture_output=True, text=True, check=True).stdout.splitlines() if line.split()}
            remaining = sorted(known & live)
            if not remaining or time.monotonic() >= deadline:
                break
            time.sleep(0.05)
        result = {'interrupt': interrupt, 'native': native, 'actor': attack, 'supervisor': footer,
                  'supervisorExitCode': process.returncode, 'remainingMeasuredPIDs': remaining}
        result['verified'] = bool(native and attack and attack['verified']
            and native.get('completed') and native.get('javascriptPassed') and native.get('snapshotPassed')
            and len(footer) == 1 and footer[0].get('passed') and process.returncode == 0 and not remaining)
        (directory / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
        return result
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
        process.stdout.close()
        process.stderr.close()


def run(directory):
    if os.getuid() == 0 or os.geteuid() == 0:
        raise ValueError('This controller must never run as root')
    directory = directory.resolve()
    if not directory.is_relative_to(ROOT / 'artifacts'):
        raise ValueError('Use a workspace artifact directory')
    directory.mkdir()
    if any(matching_pids(path) for path in (SUPERVISOR, ACTOR, APP / 'Contents/MacOS/RendererIdentityProbe')):
        raise RuntimeError('Existing research processes must remain untouched')
    result = {'rootRun': False, 'actorSHA256': hashlib.sha256(ACTOR.read_bytes()).hexdigest(), 'trials': []}
    for index in range(3):
        item = trial(directory / f'reference-{index+1}')
        result['trials'].append(item)
        if not item['verified']:
            break
    if all(item['verified'] for item in result['trials']):
        result['recovery'] = trial(directory / 'actor-parent-death', interrupt=True)
    result['allPassed'] = (len(result['trials']) == 3 and all(item['verified'] for item in result['trials'])
                           and result.get('recovery', {}).get('verified') is True)
    (directory / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = run(args.out)
    print(json.dumps({'allPassed': result['allPassed'], 'rootRun': False}))
