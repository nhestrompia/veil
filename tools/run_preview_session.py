"""Hold the pinned preview and one private fixture for a physical control."""

import argparse
import hashlib
import json
from pathlib import Path
import signal
import subprocess
import threading
import time

from fixture import FixtureServer
from process_cleanup import matching_pids, stop_launched
from run_device_session import active
from run_drag_delivery import launch, ready
from run_native import ROOT, Oracle


def run(output):
    output = output.resolve()
    if not output.is_relative_to((ROOT / 'artifacts').resolve()):
        raise ValueError('Use a fresh project artifact directory')
    manifest = json.loads((ROOT / 'docs/evidence/integrated-browser-permission-manifest.json').read_text())
    name = 'AgentFreeBrowserPreview'
    app = ROOT / 'dist' / (name + '.app')
    binary = app / 'Contents/MacOS' / name
    if not manifest.get('permissionApproved') or not manifest.get('effectiveGrantConfirmed'):
        raise RuntimeError('The preview needs approved effective Input Monitoring')
    if hashlib.sha256(binary.read_bytes()).hexdigest() != manifest['executableSHA256'] or matching_pids(binary):
        raise RuntimeError('The pinned preview changed or already runs')
    subprocess.run(['codesign', '--verify', '--strict', str(app)], check=True, timeout=10)
    output.mkdir(parents=True, mode=0o700)
    preflight = output / 'permission.log'
    subprocess.run(['open', '-g', '-n', '-W', '--stdout', str(preflight), '--stderr',
                    str(output / 'permission.stderr'), str(app), '--args', '--permissions'], check=True, timeout=15)
    if 'DEVICE_KEYBOARD permission=true' not in preflight.read_text():
        raise RuntimeError('The preview grant is no longer effective')
    server = FixtureServer(('127.0.0.1', 0))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    controller = output / 'fixture-controller.json'
    controller.write_text(json.dumps({'port': server.server_port, 'key': server.controller_key}))
    controller.chmod(0o600)
    oracle = Oracle(controller)
    trial = oracle.create()
    launcher = None
    pid = None
    session = {'target': name, 'binarySHA256': manifest['executableSHA256'], 'controller': str(controller),
               'trial': trial, 'log': str(output / 'browser.log'), 'operatorDeclaresPhysicalCompletion': False,
               'systemInputPosted': False, 'maximumSessionSeconds': 3600}

    def persist():
        temporary = output / 'session.tmp'
        temporary.write_text(json.dumps(session, indent=2) + '\n')
        temporary.replace(output / 'session.json')

    def interrupted(_number, _frame):
        raise SystemExit('The bounded preview session stopped')

    for number in [signal.SIGTERM, signal.SIGINT, signal.SIGALRM]:
        signal.signal(number, interrupted)
    signal.alarm(3600)
    try:
        launcher, _ = launch(name, Path(session['log']), ['--url', trial['url']])
        pid = ready(Path(session['log']), r'Browser ready: pid=(\d+)')
        session.update(pid=pid, launcherPID=launcher.pid)
        active(session)
        if 'DEVICE_KEYBOARD permission=true openStatus=0' not in Path(session['log']).read_text():
            raise RuntimeError('The preview did not open its keyboard reader')
        persist()
        print(json.dumps({'ready': True, 'pid': pid, 'sessionFile': str(output / 'session.json'),
                          'binarySHA256': session['binarySHA256']}), flush=True)
        deadline = time.monotonic() + 3590
        while time.monotonic() < deadline and not (output / 'stop').exists():
            active(session)
            state = oracle.state(trial)
            session['acceptedSubmissions'] = sum(s['accepted'] for s in state['submissions'])
            session['deviceBound'] = 'DEVICE_KEYBOARD bound=true' in Path(session['log']).read_text()
            persist()
            time.sleep(.25)
    finally:
        clean = stop_launched(launcher, binary, pid)
        if launcher is not None:
            if launcher.poll() is None:
                launcher.terminate()
            try:
                launcher.wait(timeout=3)
            except subprocess.TimeoutExpired:
                launcher.kill()
                launcher.wait(timeout=3)
        server.shutdown()
        server.server_close()
        worker.join(timeout=3)
        signal.alarm(0)
        session.update(ownedHostStopped=clean, ownedFixtureStopped=not worker.is_alive())
        persist()
        if not clean or worker.is_alive():
            raise RuntimeError('Preview session cleanup did not complete')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args().output)
