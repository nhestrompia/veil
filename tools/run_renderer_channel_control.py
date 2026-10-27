"""Compare blocked and nonblocking pixel transport when its display client pauses."""

import argparse
from contextlib import contextmanager
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import signal
import socket
import subprocess
import threading
import time

from process_cleanup import matching_pids
from run_renderer_signal_reference import prefixed

ROOT = Path(__file__).resolve().parents[1]
DISPLAY = ROOT / 'dist/ChannelDisplayProbe.app/Contents/MacOS/ChannelDisplayProbe'
ACTOR = ROOT / '.build/channel-display-pause-actor'


@contextmanager
def fixture(port=0, nonce=None):
    nonce = secrets.token_hex(8) if nonce is None else nonce
    if (type(port) is not int or not (port == 0 or 1024 <= port <= 65535)
            or type(nonce) is not str or len(nonce) != 16 or any(value not in '0123456789abcdef' for value in nonce)):
        raise ValueError('Use the fixed local fixture format')
    receipts = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_): pass

        def do_GET(self):
            if self.path != '/channel/' + nonce:
                self.send_error(404)
                return
            receipts.append({'route': 'fixture', 'receivedNanoseconds': time.clock_gettime_ns(time.CLOCK_MONOTONIC)})
            body = ('''<!doctype html><style>html,body{margin:0;background:white}
            canvas{position:absolute;left:0;top:0}#tick{position:absolute;left:280px;top:0;width:60px;height:60px}</style>
            <canvas id="noise" width="256" height="256"></canvas><div id="tick"></div><script>
            window.fixtureNonce="''' + nonce + '''";window.fixtureTicks=0;
            let c=document.getElementById('noise').getContext('2d');let pixels=c.createImageData(256,256);let state=12345;
            for(let i=0;i<pixels.data.length;i+=4){for(let j=0;j<3;j++){state=(Math.imul(state,1664525)+1013904223)>>>0;
            pixels.data[i+j]=state>>>24;}pixels.data[i+3]=255;}c.putImageData(pixels,0,0);
            setInterval(()=>{fixtureTicks++;document.getElementById('tick').style.backgroundColor=
            `rgb(${fixtureTicks%255},200,80)`;},50);</script>''').encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}/channel/{nonce}', nonce, receipts
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


class Capture:
    def __init__(self, binary, args, fd, directory):
        self.binary = binary
        self.error_stream = (directory / (binary.name + '.stderr')).open('wb')
        self.process = subprocess.Popen([str(binary), *args], stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=self.error_stream, pass_fds=(fd,))
        self.raw = bytearray()
        self.lines = []
        self.error = None
        self.condition = threading.Condition()
        self.thread = threading.Thread(target=self.read, daemon=True)
        self.thread.start()

    def read(self):
        try:
            while line := self.process.stdout.readline(65537):
                with self.condition:
                    if len(line) > 65536 or len(self.raw) + len(line) > 3 * 1024 * 1024:
                        raise ValueError('Diagnostic output exceeded its bound')
                    self.raw.extend(line)
                    self.lines.append(line)
                    self.condition.notify_all()
        except Exception as error:
            self.error = str(error)

    def records(self, prefix):
        with self.condition:
            return prefixed(b''.join(self.lines), prefix + ' ')

    def await_record(self, prefix, timeout=7):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            records = self.records(prefix)
            if records: return records[0]
            if self.error or self.process.poll() is not None: break
            with self.condition: self.condition.wait(timeout=0.02)
        raise TimeoutError('No ' + prefix + ' record from ' + self.binary.name)

    def close(self, directory):
        if self.process.poll() is None:
            self.process.send_signal(signal.SIGCONT)
            self.process.terminate()
            try: self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=3)
        self.thread.join(timeout=2)
        (directory / (self.binary.name + '.stdout')).write_bytes(self.raw)
        self.process.stdout.close()
        self.error_stream.close()


def attack(identity, directory, interrupt=False):
    args = [str(ACTOR), '--reference', *[str(identity[key]) for key in ('pid', 'startedSeconds', 'startedMicroseconds')]]
    process = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stopped = None
    if interrupt:
        # The actor arms its independent recovery child before reporting a stopped display.
        line = process.stdout.readline(65537)
        values = prefixed(line, 'SIGNAL_STOPPED ')
        if len(values) != 1 or values[0]['observed'] is not True:
            process.kill()
            process.communicate(timeout=7)
            raise ValueError('Actor recovery control lacks a confirmed stopped target')
        stopped = values[0]
        process.kill()
        tail, stderr = process.communicate(timeout=7)
        stdout = line + tail
    else:
        try: stdout, stderr = process.communicate(timeout=9)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate(timeout=7)
            raise
    (directory / 'actor.stdout').write_bytes(stdout)
    (directory / 'actor.stderr').write_bytes(stderr)
    stopped_records = prefixed(stdout, 'SIGNAL_STOPPED ')
    if stopped is None and len(stopped_records) == 1:
        stopped = stopped_records[0]
    result = {'exitCode': process.returncode, 'signals': prefixed(stdout, 'SIGNAL_RESULT '),
        'interval': prefixed(stdout, 'CHANNEL_PAUSE_INTERVAL '), 'footer': prefixed(stdout, 'SIGNAL_ACTOR_RESULT '),
        'interrupted': interrupt, 'stopped': stopped}
    return result


def trial(directory, blocking=False, interrupt=False):
    directory.mkdir()
    name = 'ChannelBlockingProbe' if blocking else 'ChannelRendererProbe'
    renderer = ROOT / f'dist/{name}.app/Contents/MacOS/{name}'
    result = {'passed': False, 'rootRun': False, 'blocking': blocking, 'recoveryControl': interrupt}
    captures = []
    known = set()
    with fixture() as (url, nonce, receipts):
        sender, receiver = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
        session = secrets.token_bytes(16)
        for peer in (sender, receiver):
            peer.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024)
            peer.sendall(session)
        try:
            backend = Capture(renderer, ['--channel', str(sender.fileno()), '--fixture', url], sender.fileno(), directory)
            captures.append(backend)
            backend_ready = backend.await_record('CHANNEL_RENDERER_READY')
            known.add(backend_ready['host']['pid'])
            front = Capture(DISPLAY, ['--channel', str(receiver.fileno()), '--fixture', url], receiver.fileno(), directory)
            captures.append(front)
            sender.close()
            receiver.close()
            display_ready = front.await_record('CHANNEL_DISPLAY_READY')
            known.add(display_ready['host']['pid'])
            front.await_record('CHANNEL_FRAME_PRESENTED')
            actor = attack(display_ready['host'], directory, interrupt)
            result['actor'] = actor
            if actor.get('stopped'):
                known.add(actor['stopped']['watchdogPID'])
            backend.process.wait(timeout=18)
            front.process.wait(timeout=6)
            backend.thread.join(timeout=2)
            front.thread.join(timeout=2)
            produced = backend.records('CHANNEL_FRAME_PRODUCED')
            shown = front.records('CHANNEL_FRAME_PRESENTED')
            finals = backend.records('CHANNEL_RENDERER_RESULT')
            display_finals = front.records('CHANNEL_DISPLAY_RESULT')
            if len(finals) != 1 or len(display_finals) != 1:
                raise ValueError('Missing final native result')
            final = finals[0]
            display_final = display_finals[0]
            known.update(final['rolePIDs'].values())
            checks = {'nativeCompleted': final['completed'] and display_final['completed'],
                'noVisibleWindow': final['visibleWindows'] == display_final['visibleWindows'] == 0,
                'privateNavigation': final['acceptedCommands'] == 1 and final['refusedCommands'] == 0 and len(receipts) == 1,
                'pixelsPresented': len(shown) >= 2 and all(x['sample']['nonce'] == nonce for x in produced),
                'boundedQueue': final['peakBufferedBytes'] <= 2 * (2 * 1024 * 1024 + 48),
                'processExits': backend.process.returncode == front.process.returncode == 0,
                'postDisconnectProgress': any(x['channelClosed'] for x in produced),
                'boundedCapture': not backend.error and not front.error}
            if interrupt:
                known.add(actor['stopped']['watchdogPID'])
                checks['actorRecovery'] = actor['exitCode'] == -signal.SIGKILL and actor['stopped']['observed'] is True
            else:
                if len(actor['signals']) != 1 or len(actor['interval']) != 1 or len(actor['footer']) != 1:
                    raise ValueError('Missing calibrated pause record')
                row = actor['signals'][0]
                interval = actor['interval'][0]
                start, end = interval['beganNanoseconds'], interval['endedNanoseconds']
                inside = [x for x in produced if start < x['startedNanoseconds'] < x['finishedNanoseconds'] < end]
                spanning = [x for x in produced if x['startedNanoseconds'] < end and x['finishedNanoseconds'] > end
                            and x['finishedNanoseconds'] - x['startedNanoseconds'] >= 900_000_000]
                checks['pauseCalibrated'] = (actor['exitCode'] == 0 and row['stopReturn'] == row['continueReturn'] == 0
                    and row['observedStopped'] and row['identityStable'] and row['notStoppedAfter']
                    and actor['footer'][0]['passed'] and actor['footer'][0]['watchdogReaped'])
                checks['resumedPresentation'] = any(x['presentedNanoseconds'] > end for x in shown)
                if blocking:
                    checks['blockingControlStalls'] = not inside and bool(spanning)
                else:
                    checks['progressDuringPause'] = len(inside) >= 2 and inside[-1]['sample']['ticks'] > inside[0]['sample']['ticks']
                    checks['realBackpressure'] = final['wouldBlock'] > 0 and final['replacedFrames'] > 0
                    checks['staleFrameRefusal'] = display_final['staleFrames'] > 0
                result.update(pauseInterval=interval, framesCompletedWhilePaused=inside, framesSpanningResume=spanning)
            result.update(renderer=final, display=display_final, produced=produced, presented=shown, receipts=receipts, checks=checks)
            result['passed'] = all(checks.values())
        except Exception as error:
            result['error'] = str(error)
        finally:
            sender.close()
            receiver.close()
            for capture in reversed(captures): capture.close(directory)
    deadline = time.monotonic() + 5
    while True:
        live = {int(x) for x in subprocess.run(['/bin/ps', '-axo', 'pid='], capture_output=True, text=True, check=True).stdout.split()}
        remaining = sorted(known & live)
        if not remaining or time.monotonic() >= deadline: break
        time.sleep(0.05)
    result['remainingMeasuredPIDs'] = remaining
    result['measuredPIDs'] = sorted(known)
    result['passed'] = result['passed'] and not remaining
    (directory / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def run(directory, pairs):
    if os.getuid() < 500 or os.geteuid() != os.getuid(): raise ValueError('Use the ordinary research account')
    directory = directory.resolve()
    if not directory.is_relative_to(ROOT / 'artifacts'): raise ValueError('Use a workspace artifact directory')
    binaries = [DISPLAY, ACTOR, *[ROOT / f'dist/{name}.app/Contents/MacOS/{name}'
                for name in ('ChannelRendererProbe', 'ChannelBlockingProbe')]]
    if any(matching_pids(p) for p in binaries): raise ValueError('Existing diagnostics must remain untouched')
    directory.mkdir()
    result = {'rootRun': False, 'ordinaryUID': os.getuid(), 'pairs': [],
              'binaryHashes': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in binaries}}
    for index in range(pairs):
        control = trial(directory / f'blocking-{index+1}', blocking=True)
        candidate = trial(directory / f'candidate-{index+1}') if control['passed'] else None
        result['pairs'].append({'control': control, 'candidate': candidate})
        print(json.dumps({'pair': index+1, 'control': control['passed'], 'candidate': candidate and candidate['passed']}), flush=True)
        if not control['passed'] or not candidate['passed']: break
    if len(result['pairs']) == pairs and all(x['control']['passed'] and x['candidate']['passed'] for x in result['pairs']):
        result['recovery'] = trial(directory / 'actor-parent-death', interrupt=True)
    result['passed'] = (len(result['pairs']) == pairs and all(x['control']['passed'] and x['candidate'] and x['candidate']['passed']
                        for x in result['pairs']) and result.get('recovery', {}).get('passed') is True)
    (directory / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--pairs', type=int, choices=(1, 3), default=3)
    args = parser.parse_args()
    result = run(args.out, args.pairs)
    print(json.dumps({'passed': result['passed'], 'rootRun': False}))
    raise SystemExit(0 if result['passed'] else 1)
