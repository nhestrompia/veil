"""Let an agent start and manage the real native browser without human setup."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import secrets
import subprocess
import sys
import time

from process_cleanup import process_matches
from run_native import ROOT
from website_challenge import TARGETS, custom_challenge, load_challenge, pinned_image


def artifact_path(path):
    path = path.resolve()
    if not path.is_relative_to((ROOT / 'artifacts').resolve()):
        raise ValueError('Use a session inside project artifacts')
    return path


def status(path):
    path = artifact_path(path)
    if path.name != 'session.json':
        raise ValueError('Use the session.json returned by start')
    session = json.loads(path.read_text())
    target = next((key for key in ['engine', 'pointer', 'control'] if TARGETS[key] == session.get('target')), None)
    if target is None:
        raise ValueError('Not an agent-browser session')
    _, app, binary, digest = pinned_image(target)
    if (session.get('binarySHA256') != digest or session.get('binaryPath') != str(binary)
            or session.get('appPath') != str(app)):
        raise RuntimeError('The recorded browser identity changed')
    running = session.get('status') == 'running' and process_matches(session['pid'], binary)
    log = path.parent / 'browser.log'
    text = log.read_text() if log.exists() else ''
    return {**session, 'running': running, 'sessionFile': str(path),
            'taskFile': str(path.parent / 'AGENT-TASK.md'),
            'attemptTemplate': str(path.parent / 'attempt-template.json'),
            'challengeFile': str(path.parent / 'challenge.json'),
            'startupAddressGateLogged': 'STARTUP_ADDRESS pendingPhysicalSubmit=true' in text,
            'contentProcessReported': 'FOCUS_ENGINE contentVerified=true' in text,
            'admittedInputEvents': text.count('INPUT_GATE_ACCEPTED'),
            'refusedInputEvents': text.count('INPUT_GATE_REFUSED'),
            'refusedQueueEvents': text.count('INPUT_QUEUE_REFUSED'),
            'hardwarePointerArmCount': text.count('HARDWARE_POINTER armed=true'),
            'hardwarePointerBindingObserved': 'HARDWARE_POINTER bound=true' in text,
            'websiteOutcome': 'not-independently-scored',
            'providedAutomationEndpoint': None,
            'launcherInjectsInput': False, 'launcherEnablesDebugging': False}


def start(target, output, seconds, label, url=None, task=None, challenge=None):
    if not 15 <= seconds <= 900:
        raise ValueError('Use a session duration from 15 to 900 seconds')
    if challenge and (url or task):
        raise ValueError('Use either --challenge or both --url and --task')
    if challenge:
        load_challenge(challenge)
    else:
        custom_challenge(url or '', task)
    pinned_image(target)
    output = artifact_path(output)
    if output.exists():
        raise ValueError('Use a fresh session directory')
    output.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    worker_log = output.with_name(output.name + '.launcher.log')
    command = [sys.executable, str(ROOT / 'tools/website_challenge.py'),
               '--target', target, '--mode', 'agent-only', '--output', str(output),
               '--seconds', str(seconds), '--agent-label', label]
    if challenge:
        command += ['--challenge', str(challenge.resolve())]
    else:
        command += ['--url', url, '--task', task]
    with worker_log.open('x') as stream:
        worker_log.chmod(0o600)
        worker = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.DEVNULL,
                                  stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
    session = output / 'session.json'
    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if all((output / name).is_file() for name in ['session.json', 'AGENT-TASK.md', 'attempt-template.json']):
                result = status(session)
                if result['running']:
                    return result
            if worker.poll() is not None:
                error = json.loads(session.read_text()).get('error') if session.exists() else None
                raise RuntimeError(error or f'Browser startup failed; see {worker_log}')
            time.sleep(.1)
        raise RuntimeError(f'Browser startup timed out; see {worker_log}')
    except BaseException:
        if output.is_dir():
            (output / 'stop').touch()
        if worker.poll() is None:
            worker.terminate()
            try:
                worker.wait(timeout=8)
            except subprocess.TimeoutExpired:
                raise RuntimeError(f'Session cleanup is pending; inspect {worker_log}')
        raise


def stop(path):
    path = artifact_path(path)
    state = status(path)
    (path.parent / 'stop').touch()
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        state = status(path)
        if state.get('ownedHostStopped') is True:
            return state
        time.sleep(.1)
    return {**state, 'stopRequested': True, 'cleanupPending': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    launch = sub.add_parser('start', help='Launch the actual app and return its PID and task')
    launch.add_argument('--target', choices=['engine', 'pointer', 'control'], default='engine')
    launch.add_argument('--url')
    launch.add_argument('--task')
    launch.add_argument('--challenge', type=Path, help='Reuse an earlier challenge in a readable control')
    launch.add_argument('--agent-label', default='')
    launch.add_argument('--seconds', type=int, default=600)
    launch.add_argument('--output', type=Path)
    for name in ['status', 'stop']:
        sub.add_parser(name).add_argument('--session', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'start':
            name = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S') + '-' + secrets.token_hex(3)
            output = args.output or ROOT / 'artifacts/agent-runs' / name
            result = start(args.target, output, args.seconds, args.agent_label, args.url, args.task, args.challenge)
        else:
            result = status(args.session) if args.command == 'status' else stop(args.session)
        print(json.dumps(result, indent=2))
        return 1 if result.get('cleanupPending') else 0
    except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as error:
        print(json.dumps({'status': 'error', 'error': str(error), 'humanAssistanceRequested': False}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
