"""Loopback-only test pages and an independent task oracle."""

import argparse
import json
import secrets
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlsplit


class FixtureServer(HTTPServer):
    def __init__(self, address):
        super().__init__(address, Handler)
        self.controller_key = secrets.token_hex(24)
        self.trials = {}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def respond(self, code, value, content_type="application/json"):
        data = value.encode() if isinstance(value, str) else json.dumps(value).encode()
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def body(self):
        size = int(self.headers.get("Content-Length", "0"))
        if size > 65536:
            raise ValueError("request too large")
        return json.loads(self.rfile.read(size)) if size else {}

    def handle_request(self, method):
        path = urlsplit(self.path).path
        if path == "/health":
            return self.respond(200, {"ready": True})
        if path.startswith("/admin/"):
            if not secrets.compare_digest(self.headers.get("X-Research-Key", ""), self.server.controller_key):
                return self.respond(403, {"error": "controller authorization required"})
            if path == "/admin/trials" and method == "POST":
                trial_id = secrets.token_hex(8)
                trial = {"id": trial_id, "secret": "AFB-" + secrets.token_hex(4).upper(),
                         "submissions": [], "events": []}
                self.server.trials[trial_id] = trial
                return self.respond(201, {"id": trial_id, "url": f"http://127.0.0.1:{self.server.server_port}/trial/{trial_id}"})
            trial = self.server.trials.get(path.removeprefix("/admin/trials/"))
            return self.respond(200, trial) if trial else self.respond(404, {"error": "unknown trial"})
        parts = path.strip("/").split("/")
        trial = self.server.trials.get(parts[1]) if len(parts) >= 2 and parts[0] == "trial" else None
        if not trial:
            return self.respond(404, {"error": "unknown page"})
        if method == "GET" and len(parts) == 2:
            page = Path(__file__).with_name("fixture.html").read_text()
            return self.respond(200, page.replace("{{SECRET}}", trial["secret"]), "text/html; charset=utf-8")
        if method == "POST" and parts[-1] == "action":
            note = self.body().get("note", "")
            accepted = note == "native-input"
            trial["submissions"].append({"accepted": accepted})
            return self.respond(200, {"accepted": accepted})
        if method == "POST" and parts[-1] == "events":
            events = self.body().get("events", [])
            if not isinstance(events, list):
                raise ValueError("events must be an array")
            for event in events[:200]:
                if isinstance(event, dict) and len(trial["events"]) < 5000:
                    trial["events"].append({k: event[k] for k in ["type", "trusted", "t", "x", "y"] if k in event})
            return self.respond(200, {"recorded": len(trial["events"])})
        self.respond(405, {"error": "unsupported operation"})

    def do_GET(self):
        self.handle_request("GET")

    def do_POST(self):
        try:
            self.handle_request("POST")
        except (ValueError, TypeError, AttributeError):
            self.respond(400, {"error": "invalid request"})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--state", type=Path, default=Path("artifacts/fixture-controller.json"))
    args = parser.parse_args()
    server = FixtureServer(("127.0.0.1", args.port))
    args.state.parent.mkdir(parents=True, exist_ok=True)
    args.state.write_text(json.dumps({"port": server.server_port, "key": server.controller_key}))
    args.state.chmod(0o600)
    print(json.dumps({"ready": True, "port": server.server_port, "controllerFile": str(args.state)}), flush=True)
    server.serve_forever()
