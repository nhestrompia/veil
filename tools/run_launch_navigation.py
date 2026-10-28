"""Measure unattended launch navigation against a disposable loopback server."""

import argparse
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import signal
import subprocess
import threading
import time

from run_native import ROOT


def run(repetitions, output, targets):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    records = []
    for name in targets:
        binary = ROOT / f"dist/{name}.app/Contents/MacOS/{name}"
        for repetition in range(repetitions):
            endpoint = "/launch/" + secrets.token_hex(12)
            visits = []

            class Handler(BaseHTTPRequestHandler):
                def log_message(self, *_): pass

                def do_GET(self):
                    if self.path == endpoint:
                        visits.append(time.monotonic())
                    page = b"<!doctype html><title>Launch navigation research</title><h1>Disposable launch navigation task</h1>"
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.send_header("Content-Length", str(len(page)))
                    self.end_headers()
                    self.wfile.write(page)

            server = HTTPServer(("127.0.0.1", 0), Handler)
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            log = output / f"{name}-{repetition}.log"
            log.write_text("")
            pid = None
            launcher = subprocess.Popen(["open", "-n", "-W", str(ROOT / f"dist/{name}.app"),
                "--stdout", str(log), "--stderr", str(log), "--args", "--url",
                f"http://127.0.0.1:{server.server_port}{endpoint}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            record = {"target": name, "repetition": repetition, "binarySHA256": hashlib.sha256(binary.read_bytes()).hexdigest(),
                      "route": "launch-url", "verdict": "inconclusive"}
            try:
                deadline = time.monotonic() + 6
                while time.monotonic() < deadline:
                    match = re.search(r"Browser ready: pid=(\d+)", log.read_text())
                    if match:
                        pid = int(match[1])
                        break
                    time.sleep(0.1)
                if pid is None:
                    raise RuntimeError("Browser readiness failed")
                time.sleep(2.5)
                record["documentRequests"] = len(visits)
                record["deviceBoundDuringTest"] = "DEVICE_KEYBOARD bound=true" in log.read_text()
                record["deviceReaderReady"] = "DEVICE_KEYBOARD permission=true openStatus=0" in log.read_text()
                record["pendingAddressLogged"] = "STARTUP_ADDRESS pendingPhysicalSubmit=true" in log.read_text()
                control = next((r for r in records if r["target"] == "InspectableControl" and
                                r["repetition"] == repetition and r["verdict"] == "bypass"), None)
                record["controlWorked"] = control is not None
                if visits: record["verdict"] = "internal-control-navigation-worked" if name == "AddressStartupControl" else "bypass"
                elif control and record["pendingAddressLogged"] and record["deviceReaderReady"] and not record["deviceBoundDuringTest"]:
                    record["verdict"] = "blocked-launch-route"
            except (RuntimeError, OSError) as error:
                record["error"] = str(error)
            finally:
                if pid is not None:
                    command = subprocess.run(["ps", "-p", str(pid), "-o", "comm="], capture_output=True, text=True).stdout.strip()
                    if command == str(binary): os.kill(pid, signal.SIGTERM)
                launcher.terminate()
                try: launcher.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    launcher.kill()
                    launcher.wait()
                server.shutdown()
                server.server_close()
                worker.join(timeout=2)
            records.append(record)
            print(json.dumps(record), flush=True)
            (output / "results.json").write_text(json.dumps({"results": records,
                "scope": "Only unattended --url navigation to a fresh disposable loopback endpoint. Not a human usability or general agent-prevention result.",
                "physicalInputAbsenceVerified": False}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/launch-navigation")
    parser.add_argument("--targets", nargs="+", choices=["InspectableControl", "DeviceKeyboardExperiment", "AddressStartupControl", "AgentFreeBrowserPreview"],
                        default=["InspectableControl", "DeviceKeyboardExperiment"])
    args = parser.parse_args()
    run(args.repetitions, args.output, args.targets)
