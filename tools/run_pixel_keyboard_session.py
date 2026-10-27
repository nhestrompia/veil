"""Keep one frozen browser and a disposable fixture alive for physical testing."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import threading
import time

from fixture import FixtureServer
from run_native import ROOT, Oracle


def process_matches(pid, binary):
    result = subprocess.run(["ps", "-p", str(pid), "-o", "comm="],
                            capture_output=True, text=True, timeout=5)
    return result.returncode == 0 and result.stdout.strip() == str(binary)


def run(output, duration, target):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ROOT / "docs/evidence/pixel-keyboard-permission-manifest.json").read_text())
    entry = manifest["apps"][target]
    app = Path(entry["path"])
    binary = app / "Contents/MacOS" / target
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    if digest != entry["executableSHA256"]:
        raise RuntimeError("Browser differs from the permission manifest")
    processes = subprocess.check_output(["ps", "-axo", "comm="], text=True, timeout=5)
    if str(binary) in processes.splitlines():
        raise RuntimeError("This keyboard browser already runs; no new instance launched")
    server = FixtureServer(("127.0.0.1", 0))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    controller = output / "fixture-controller.json"
    controller.write_text(json.dumps({"port": server.server_port, "key": server.controller_key}))
    controller.chmod(0o600)
    oracle = Oracle(controller)
    trial = oracle.create()
    log_path = output / "browser.log"
    log_path.write_text("")
    pid = None
    report = {"target": target, "binarySHA256": digest, "trial": trial, "launchMethod": "LaunchServices",
              "inputPosted": False, "maximumDurationSeconds": duration,
              "internalCalibration": target == "PixelKeyboardRoutingControl"}

    def save():
        state = oracle.state(trial)
        report["acceptedSubmissions"] = sum(s["accepted"] for s in state["submissions"])
        report["events"] = state["events"]
        report["rendererLog"] = log_path.read_text().splitlines()
        (output / "session.json").write_text(json.dumps(report, indent=2) + "\n")

    try:
        started = time.monotonic()
        launched = subprocess.run(["open", "-n", "--stdout", str(log_path), "--stderr",
                                   str(output / "browser-error.log"), str(app), "--args", "--url", trial["url"]],
                                  capture_output=True, text=True, timeout=10)
        if launched.returncode:
            raise RuntimeError(launched.stderr.strip())
        while time.monotonic() - started < 20:
            match = re.search(r"PIXEL_RENDER ready pid=(\d+)", log_path.read_text())
            if match:
                pid = int(match[1])
                break
            time.sleep(0.1)
        if pid is None or not process_matches(pid, binary):
            raise RuntimeError("The launched app did not report a matching process")
        report["pid"] = pid
        report["listening"] = "permission=true openStatus=0" in log_path.read_text()
        if target == "PixelKeyboardExperiment" and not report["listening"]:
            raise RuntimeError("The normal app launch lacks effective keyboard observation")
        save()
        print(json.dumps({"ready": True, "pid": pid, "listening": report["listening"],
                          "report": str(output / "session.json")}), flush=True)
        accepted = 0
        while time.monotonic() - started < duration and not (output / "stop").exists():
            if not process_matches(pid, binary):
                break
            save()
            if report["acceptedSubmissions"] != accepted:
                accepted = report["acceptedSubmissions"]
                print(json.dumps({"acceptedSubmissions": accepted}), flush=True)
            time.sleep(1)
    finally:
        save()
        if pid is not None and process_matches(pid, binary):
            os.kill(pid, signal.SIGTERM)
            deadline = time.monotonic() + 4
            while time.monotonic() < deadline and process_matches(pid, binary):
                time.sleep(0.1)
            if process_matches(pid, binary):
                os.kill(pid, signal.SIGKILL)
        report["ownedAppStopped"] = pid is None or not process_matches(pid, binary)
        server.shutdown()
        server.server_close()
        worker.join(timeout=3)
        report["ownedFixtureStopped"] = not worker.is_alive()
        (output / "session.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({"finished": True, "ownedAppStopped": report["ownedAppStopped"]}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--duration", type=int, default=900, choices=range(60, 1801))
    parser.add_argument("--target", choices=["PixelKeyboardExperiment", "PixelKeyboardRoutingControl"],
                        default="PixelKeyboardExperiment")
    args = parser.parse_args()
    run(args.output, args.duration, args.target)
