"""Serve fixed disposable documents for the headless rendering baseline."""

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import re
import struct
import threading
import zlib


def yellow_png():
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
            + chunk(b"sRGB", b"\0") + chunk(b"IDAT", zlib.compress(b"\0\xff\xff\0\xff"))
            + chunk(b"IEND", b""))


class RendererFixture(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self):
        self.receipts = []
        self.receipt_lock = threading.Lock()
        super().__init__(("127.0.0.1", 0), RendererHandler)

    def requests_for(self, nonce):
        with self.receipt_lock:
            return [dict(item) for item in self.receipts if item["nonce"] == nonce]


class RendererHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        match = re.fullmatch(r"/(fixture|frame|fetch|image)/([0-9A-F]{8}(?:-[0-9A-F]{4}){3}-[0-9A-F]{12})", self.path)
        if not match:
            self.send_error(404)
            return
        route, nonce = match.groups()
        if route == "fixture":
            mime = "text/html; charset=utf-8"
            body = f"""<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1">
            <title>Loopback renderer control</title>
            <style>html,body{{margin:0;background:white}}div,canvas,img{{position:absolute;top:0;width:100px;height:100px}}
            #red{{left:0;background:rgb(255,0,0)}}#green{{left:100px;background:rgb(0,255,0)}}
            canvas{{left:200px}}img{{left:300px}}iframe{{position:absolute;top:200px;left:0;width:100px;height:100px;border:0}}</style>
            <div id="red"></div><div id="green"></div><canvas id="blue" width="100" height="100"></canvas>
            <img id="remote" src="/image/{nonce}"><iframe id="child" src="/frame/{nonce}"></iframe>
            <script>window.testNonce={json.dumps(nonce)};
            let c=document.getElementById('blue').getContext('2d');c.fillStyle='rgb(0,0,255)';c.fillRect(0,0,100,100);
            window.fixtureReady=fetch('/fetch/{nonce}',{{cache:'no-store'}}).then(r=>r.json()).then(r=>window.fetchedNonce=r.nonce);
            </script>""".encode()
        elif route == "frame":
            mime = "text/html; charset=utf-8"
            body = f"<!doctype html><style>body{{background:rgb(0,255,255)}}</style><script>window.frameNonce={json.dumps(nonce)}</script>".encode()
        elif route == "fetch":
            mime = "application/json"
            body = json.dumps({"nonce": nonce}).encode()
        else:
            mime, body = "image/png", yellow_png()
        with self.server.receipt_lock:
            self.server.receipts.append({"route": route, "nonce": nonce, "method": "GET", "status": 200})
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src 'self'; frame-src 'self'; connect-src 'self'")
        self.end_headers()
        self.wfile.write(body)


@contextmanager
def serve_renderer_fixture():
    server = RendererFixture()
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)
        if worker.is_alive():
            raise RuntimeError("Renderer fixture did not stop")
