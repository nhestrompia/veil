"""Let the person start each bounded physical-key sample from a readable page."""

import argparse
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import subprocess
import threading
import time

from native_environment import require_input_safety
from process_cleanup import matching_pids, stop_launched
from run_device_session import active
from run_drag_delivery import launch, ready
from run_keyboard_observation import BINARY, OBSERVER
from run_native import ROOT, Oracle, probe


def physical_reference_worked(row):
    observation = row.get("observation", {})
    return (row.get("newAcceptedSubmissions") == 1 and observation.get("expectedFakePhraseMatched") is True
            and observation.get("eventCount", 0) > 0 and observation.get("monitorRemoved") is True
            and row.get("observerCleanupVerified") is True)


class Controller:
    def __init__(self, session, output):
        self.session = session
        self.output = output
        self.oracle = Oracle()
        self.observer_hash = hashlib.sha256(BINARY.read_bytes()).hexdigest()
        self.lock = threading.RLock()
        self.finished = threading.Event()
        self.worker = None
        self.reference_pid = None
        self.reference_accepted = 0
        self.phase = "preparing"
        self.hint = "Preparing the research window."
        self.report = {"candidatePID": session["pid"], "binarySHA256": session["binarySHA256"],
                       "observerSHA256": self.observer_hash, "physicalSampleRequested": True,
                       "inputGeneratedByController": False, "samples": []}

    def save(self):
        with self.lock:
            (self.output / "results.json").write_text(json.dumps(self.report, indent=2) + "\n")

    def state(self):
        with self.lock:
            return {"phase": self.phase, "hint": self.hint}

    def set_state(self, phase, hint):
        with self.lock:
            self.phase, self.hint = phase, hint

    def start(self, candidate):
        with self.lock:
            required = "ready-candidate" if candidate else "ready-reference"
            if self.phase != required or self.worker is not None and self.worker.is_alive():
                return False
            if candidate and not physical_reference_worked(self.report["samples"][0]):
                return False
            self.phase, self.hint = "starting", "Starting the passive listener. Wait for its ready state."
            self.worker = threading.Thread(target=self.observe, args=(candidate,), daemon=True)
            self.worker.start()
            return True

    def accept_reference(self, note):
        with self.lock:
            accepted = self.phase == "listening-reference" and self.reference_accepted == 0 and note == "native-input"
            if accepted:
                self.reference_accepted += 1
                self.hint = "Sample recorded. Wait for the listener to finish."
            return accepted

    def observe(self, candidate):
        name = "candidate" if candidate else "reference"
        prefix = self.output / name
        pid = self.session["pid"] if candidate else self.reference_pid
        row = {"sample": name, "pid": pid, "inputGeneratedByController": False}
        observer = None
        try:
            active(self.session)
            if hashlib.sha256(BINARY.read_bytes()).hexdigest() != self.observer_hash:
                raise RuntimeError("Observer changed after control preparation")
            before = self.oracle.state(self.session["trial"]) if candidate else None
            foreground = subprocess.check_output([str(ROOT / ".build/research-focus"), str(pid)], text=True).strip()
            if foreground != str(pid):
                raise RuntimeError("The exact research target could not become frontmost")
            row["frontmostBeforeLaunch"] = int(foreground)
            existing = matching_pids(BINARY)
            log = prefix.with_suffix(".observer.json")
            observer = subprocess.Popen(["open", "-g", "-n", "-W", str(OBSERVER), "--stdout", str(log),
                                         "--stderr", str(prefix.with_suffix(".stderr")), "--args", "observe-pid", str(pid)],
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            observer.research_existing_pids = existing
            time.sleep(0.5)
            if log.exists() and log.read_text().strip() or not matching_pids(BINARY).difference(existing):
                raise RuntimeError("Observer stopped before the ready state")
            self.set_state("listening-candidate" if candidate else "listening-reference",
                           "Type native-input in the restricted browser, then Return. Stay in its window." if candidate else
                           "Ready: type native-input in the field below, then Return. Stay in this window.")
            try:
                observer.wait(timeout=20)
            except subprocess.TimeoutExpired:
                raise RuntimeError("Observer did not finish within its bounded interval")
            row["observation"] = json.loads(log.read_text())
            if candidate:
                after = self.oracle.state(self.session["trial"])
                row["newSubmissions"] = after["submissions"][len(before["submissions"]):]
                row["newAcceptedSubmissions"] = sum(bool(item["accepted"]) for item in row["newSubmissions"])
                active(self.session)
                row["candidateStillRunningUnchanged"] = True
            else:
                with self.lock:
                    row["newAcceptedSubmissions"] = self.reference_accepted
        except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as error:
            row["error"] = str(error)
        finally:
            if observer is not None:
                row["observerCleanupVerified"] = stop_launched(observer, BINARY, None)
                observer.terminate()
                try:
                    observer.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    observer.kill()
                    observer.wait()
            with self.lock:
                self.report["samples"].append(row)
                if not row.get("observerCleanupVerified"):
                    self.phase, self.hint = "inconclusive", "Observer cleanup failed. Stop desktop tests."
                elif candidate:
                    matched = row.get("observation", {}).get("expectedFakePhraseMatched")
                    self.phase = "complete"
                    self.hint = f"Sample 2 finished. Fake phrase observed: {bool(matched)}. Return here and choose Finish."
                elif physical_reference_worked(row):
                    self.phase, self.hint = "ready-candidate", "Sample 1 observed. Read the sample 2 instructions, then choose Start sample 2."
                else:
                    self.phase, self.hint = "inconclusive", "Sample 1 did not calibrate. No candidate sample will run. Choose Finish."
                self.save()
            if candidate:
                subprocess.run([str(ROOT / ".build/research-focus"), str(self.reference_pid)], capture_output=True)
            print(json.dumps(row), flush=True)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def respond(self, status, body, content_type="application/json"):
        data = body.encode() if isinstance(body, str) else json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == self.server.base:
            return self.respond(200, Path(__file__).with_name("keyboard-observation.html").read_text(), "text/html; charset=utf-8")
        if self.path == self.server.base + "/state":
            return self.respond(200, self.server.controller.state())
        self.respond(404, {})

    def do_POST(self):
        if self.headers.get("Origin") != self.server.origin:
            return self.respond(403, {})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 <= size <= 256:
                return self.respond(400, {})
            body = json.loads(self.rfile.read(size))
        except (ValueError, TypeError):
            return self.respond(400, {})
        controller = self.server.controller
        if self.path in [self.server.base + "/start-reference", self.server.base + "/start-candidate"]:
            success = controller.start(self.path.endswith("start-candidate"))
            return self.respond(200 if success else 409, {"started": success})
        if self.path == self.server.base + "/reference-action" and isinstance(body, dict):
            return self.respond(200, {"accepted": controller.accept_reference(body.get("note"))})
        if self.path == self.server.base + "/finish" and controller.state()["phase"] in ["complete", "inconclusive"]:
            controller.finished.set()
            return self.respond(200, {"finished": True})
        self.respond(409, {})


def run(session_path, output):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    session = json.loads(session_path.read_text())
    active(session)
    permissions = probe(["permissions"], output / "permissions.json")
    require_input_safety(permissions)
    controller = Controller(session, output)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.base = "/" + secrets.token_urlsafe(24)
    server.origin = f"http://127.0.0.1:{server.server_port}"
    server.controller = controller
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    launcher, binary = launch("InspectableControl", output / "reference.log", ["--url", server.origin + server.base])
    pid = None
    try:
        pid = ready(output / "reference.log", r"Browser ready: pid=(\d+)")
        controller.reference_pid = pid
        controller.report["referencePID"] = pid
        controller.report["referenceBinarySHA256"] = hashlib.sha256(binary.read_bytes()).hexdigest()
        controller.set_state("ready-reference", "Choose Start sample 1 when you are ready. No listener is active yet.")
        subprocess.run([str(ROOT / ".build/research-focus"), str(pid)], check=True, capture_output=True)
        controller.save()
        print(json.dumps({"ready": True, "referencePID": pid, "output": str(output)}), flush=True)
        controller.finished.wait(timeout=600)
    finally:
        if controller.worker is not None:
            controller.worker.join(timeout=25)
        server.shutdown()
        server.server_close()
        controller.report["referenceCleanupVerified"] = stop_launched(launcher, binary, pid)
        launcher.terminate()
        try:
            launcher.wait(timeout=3)
        except subprocess.TimeoutExpired:
            launcher.kill()
            launcher.wait()
        controller.save()
    if not controller.report["referenceCleanupVerified"]:
        raise RuntimeError("Interactive reference cleanup failed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.session.resolve(), args.output)
