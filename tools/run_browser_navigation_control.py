"""Check browser controls against a disposable local HTTP fixture."""

import argparse
from contextlib import contextmanager
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import threading
import time

from process_cleanup import matching_pids
from run_headless_renderer_probe import collect_stdout

ROOT = Path(__file__).resolve().parents[1]
BINARY = ROOT / 'dist/BrowserNavigationControl.app/Contents/MacOS/BrowserNavigationControl'


@contextmanager
def fixture():
    nonce = secrets.token_hex(8)
    prefix = '/navigation/' + nonce
    receipts = []
    visits = {}
    lock = threading.Lock()
    stopping = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_GET(self):
            if self.path not in {prefix + '/' + part for part in ('a', 'b', 'slow', 'drop')}:
                self.send_error(404)
                return
            route = self.path.rsplit('/', 1)[1]
            with lock:
                visits[route] = visits.get(route, 0) + 1
                visit = visits[route]
                receipts.append({'route': route, 'visit': visit})
            if route == 'drop':
                self.close_connection = True
                self.connection.shutdown(socket.SHUT_RDWR)
                return
            body = (f'<!doctype html><title>Navigation {route}</title>'
                    f'<script>window.fixtureVisit={visit};</script><p>Local fixture {route}</p>').encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Content-Length', str(len(body) + (100000 if route == 'slow' else 0)))
            self.end_headers()
            try:
                self.wfile.write(body)
                self.wfile.flush()
                if route == 'slow':
                    for _ in range(50):
                        if stopping.wait(0.1):
                            break
                        self.wfile.write(b' ' * 2000)
                        self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}{prefix}', receipts
    finally:
        stopping.set()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def run(directory, integrated=False):
    if os.getuid() == 0 or os.geteuid() == 0:
        raise ValueError('Use an ordinary user')
    directory = directory.resolve()
    if not directory.is_relative_to(ROOT / 'artifacts'):
        raise ValueError('Use a workspace artifact directory')
    directory.mkdir(parents=True)
    binary = ROOT / '.build/IntegratedBrowserNavigation' if integrated else BINARY
    if matching_pids(binary):
        raise RuntimeError('An existing navigation control must remain untouched')
    result = {'passed': False, 'ordinaryUID': os.getuid(), 'rootRun': False,
              'binarySHA256': hashlib.sha256(binary.read_bytes()).hexdigest(), 'integrated': integrated}
    with fixture() as (url, receipts), (directory / 'app.stderr').open('wb') as errors:
        process = subprocess.Popen([str(binary), '--fixture', url], stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=errors)
        try:
            stdout = collect_stdout(process, timeout=30, limit=65536)
            (directory / 'app.stdout').write_bytes(stdout)
            reports = [json.loads(line.removeprefix('BROWSER_NAVIGATION_RESULT '))
                       for line in stdout.decode().splitlines() if line.startswith('BROWSER_NAVIGATION_RESULT ')]
            if len(reports) != 1:
                raise RuntimeError('Expected one navigation report')
            native = reports[0]
            known = {native['pid']} | set(native.get('rolePIDs', {}).values())
            known = {pid for pid in known if type(pid) is int and pid > 1}
            deadline = time.monotonic() + 5
            while True:
                live = {int(row) for row in subprocess.run(['/bin/ps', '-axo', 'pid='],
                        capture_output=True, text=True, check=True).stdout.split()}
                remaining = sorted(known & live)
                if not remaining or time.monotonic() >= deadline:
                    break
                time.sleep(0.05)
            counts = {route: sum(item['route'] == route for item in receipts)
                      for route in ('a', 'b', 'slow', 'drop')}
            result.update(native=native, hostExitCode=process.returncode,
                          receipts=list(receipts), requestCounts=counts, remainingMeasuredPIDs=remaining)
            result['passed'] = (process.returncode == 0 and native.get('passed') is True
                and len(native.get('checks', {})) == (14 if integrated else 10) and all(native['checks'].values())
                and len(native.get('rolePIDs', {})) == 3 and not remaining
                and counts['a'] >= 1 and counts['b'] >= 2 and counts['slow'] >= 1 and counts['drop'] >= 1)
        except Exception as error:
            result['error'] = str(error)
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
            process.stdout.close()
    (directory / 'results.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--integrated', action='store_true')
    args = parser.parse_args()
    result = run(args.out, integrated=args.integrated)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['passed'] else 1)
