"""Keep the existing internal browser diagnostic alive for a physical capture check."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import threading
import time

from fixture import FixtureServer
from process_cleanup import matching_pids, stop_launched
from run_native import ROOT, Oracle


def run(output, window_only=False):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    output.chmod(0o700)
    if (output / "session.json").exists():
        raise RuntimeError("Use a new directory for each capture session")
    app = ROOT / "dist/InternalKeyboardControl.app"
    binary = app / "Contents/MacOS/InternalKeyboardControl"
    existing = matching_pids(binary)
    if existing:
        raise RuntimeError("An internal diagnostic already runs")
    subprocess.run(["codesign", "--verify", "--strict", str(app)], check=True, timeout=10)
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    shutil.copy2(binary, output / "tested-image")
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
    report = {"binarySHA256": digest, "trial": trial, "physicalObservation": "pending",
              "systemInputPosted": False, "internalSequence": True, "deviceReaderStarted": False,
              "windowOnly": window_only}
    launcher = None
    pid = None

    def persist():
        temporary = output / "session.tmp"
        temporary.write_text(json.dumps(report, indent=2) + "\n")
        temporary.replace(output / "session.json")

    def save():
        text = log_path.read_text()
        state = oracle.state(trial)
        report["acceptedInternalSubmissions"] = sum(s["accepted"] for s in state["submissions"])
        report["secret"] = state["secret"]
        report["events"] = state["events"]
        report["windowSharingEnabled"] = "INTERNAL_KEYBOARD windowSharingEnabled=true" in text
        report["rendererLog"] = text.splitlines()
        windows = re.search(r"INTERNAL_CAPTURE targetWindow=(\d+) backdropWindow=(\d+)", text)
        if windows:
            report["targetWindowID"], report["backdropWindowID"] = map(int, windows.groups())
        persist()

    try:
        started = time.monotonic()
        launcher = subprocess.Popen(["open", "-n", "-W", "--stdout", str(log_path), "--stderr",
                                     str(output / "app-error.log"), str(app), "--args", "--url", trial["url"]],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        launcher.research_existing_pids = existing
        while time.monotonic() - started < 20:
            text = log_path.read_text()
            match = re.search(r"Browser ready: pid=(\d+)", text)
            if match:
                pid = int(match[1])
                report["pid"] = pid
            save()
            if pid and report["acceptedInternalSubmissions"] and "INTERNAL_KEYBOARD sequenceFinished=true" in text:
                break
            time.sleep(0.1)
        else:
            raise RuntimeError("The internal browser did not finish its fixed task")
        if not window_only and "targetWindowID" not in report:
            raise RuntimeError("This capture session requires its owned compact backdrop")
        print(json.dumps({"ready": True, "pid": pid, "windowSharingEnabled": report["windowSharingEnabled"],
                          "acceptedInternalSubmissions": report["acceptedInternalSubmissions"],
                          "report": str(output / "session.json")}), flush=True)
        while time.monotonic() - started < 600 and not (output / "stop").exists():
            if pid not in matching_pids(binary):
                break
            save()
            time.sleep(1)
    finally:
        try:
            save()
        finally:
            cleaned = stop_launched(launcher, binary, pid)
            if launcher:
                launcher.terminate()
                try:
                    launcher.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    launcher.kill()
                    launcher.wait()
            server.shutdown()
            server.server_close()
            worker.join(timeout=3)
            report["ownedHostStopped"] = cleaned
            report["ownedFixtureStopped"] = not worker.is_alive()
            persist()
            print(json.dumps({"finished": True, "ownedHostStopped": cleaned,
                              "ownedFixtureStopped": report["ownedFixtureStopped"]}), flush=True)
            if not cleaned:
                raise RuntimeError("Research host cleanup failed; stop further desktop tests")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--window-only", action="store_true")
    args = parser.parse_args()
    run(args.output, args.window_only)
