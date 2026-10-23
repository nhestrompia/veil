"""Keep one physically calibrated browser alive while external agents attack it."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

from run_native import ROOT, Oracle, probe

NAME = "DeviceKeyboardExperiment"
BINARY = ROOT / f"dist/{NAME}.app/Contents/MacOS/{NAME}"
ROUTES = ["session", "hid", "private", "pid-hid", "curve-hid", "keycodes-hid", "iohid-legacy", "iohid-reports", "pid-keys-hid", "pid-keys-keycodes-hid", "pid-window-keycodes-hid"]


def active(session):
    process = subprocess.run(["ps", "-p", str(session["pid"]), "-o", "comm="], capture_output=True, text=True)
    if process.stdout.strip() != str(BINARY):
        raise RuntimeError("The recorded research browser is no longer running")
    if hashlib.sha256(BINARY.read_bytes()).hexdigest() != session["binarySHA256"]:
        raise RuntimeError("The browser changed after session start")


def start(path):
    if path.exists():
        try:
            active(json.loads(path.read_text()))
        except RuntimeError:
            pass
        else:
            raise RuntimeError("A recorded research session is already running")
    path.parent.mkdir(parents=True, exist_ok=True)
    log_path = path.with_suffix(".log")
    trial = Oracle().create()
    log_path.write_text("")
    launcher = subprocess.Popen(["open", "-n", "-W", str(ROOT / f"dist/{NAME}.app"),
                                "--stdout", str(log_path), "--stderr", str(log_path), "--args", "--url", trial["url"]],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    pid = None
    for _ in range(60):
        match = re.search(r"Browser ready: pid=(\d+)", log_path.read_text())
        if match:
            pid = int(match[1])
            break
        time.sleep(0.1)
    if pid is None:
        launcher.terminate()
        raise RuntimeError("Research browser readiness failed")
    session = {"pid": pid, "launcherPID": launcher.pid, "trial": trial, "log": str(log_path),
               "binarySHA256": hashlib.sha256(BINARY.read_bytes()).hexdigest()}
    path.write_text(json.dumps(session, indent=2))
    active(session)
    print(json.dumps({"pid": pid, "trial": trial["id"], "sessionFile": str(path)}), flush=True)


def attack(path, controls, repetitions, confirmed):
    session = json.loads(path.read_text())
    active(session)
    oracle = Oracle()
    before = oracle.state(session["trial"])
    log_path = Path(session["log"])
    if not confirmed or not any(s["accepted"] for s in before["submissions"]) or "DEVICE_KEYBOARD bound=true" not in log_path.read_text():
        raise RuntimeError("Need declared physical completion, a bound device, and an accepted website action in this same session")
    control_rows = json.loads(controls.read_text())["results"]
    output = path.parent / "device-session-attacks"
    output.mkdir(parents=True, exist_ok=True)
    summary = {"results": [], "binarySHA256": session["binarySHA256"], "trial": session["trial"]["id"],
               "operatorDeclaresPhysicalCompletion": True, "bootstrapAttested": False,
               "physicalInputAbsenceVerified": False, "sessionPID": session["pid"],
               "routeContract": "Same physically calibrated browser process. Count only new independent submissions. Fixture clears its field after accepted actions."}
    for route in ROUTES:
        for repetition in range(repetitions):
            active(session)
            control = next((r for r in control_rows if r["target"] == "InspectableControl" and
                            r["route"] == route and r["repetition"] == repetition), None)
            if not control or "fieldCenter" not in control:
                raise RuntimeError(f"Missing working control for {route} repetition {repetition}")
            old_state = oracle.state(session["trial"])
            offset = len(log_path.read_text())
            prefix = output / f"{route}-{repetition}"
            if route.startswith("iohid-"):
                args = ["hid-post-input", session["pid"], *control["fieldCenter"], route.removeprefix("iohid-")]
            else:
                source = route.rsplit("-", 1)[-1]
                args = ["input", session["pid"], *control["fieldCenter"], source]
                if route.startswith("pid-window-"): args.append("pid-window")
                elif route.startswith("pid-keys-"): args.append("pid-keys")
                elif route.startswith("pid-"): args.append("pid")
                if route.startswith("curve-"): args.append("curve")
                if "keycodes" in route.split("-"): args.append("keycodes")
            attempt = probe(args, prefix.with_suffix(".attempt.json"))
            time.sleep(0.5)
            state = oracle.state(session["trial"])
            new_submissions = state["submissions"][len(old_state["submissions"]):]
            new_log = log_path.read_text()[offset:]
            accepted = new_log.count("INPUT_GATE_ACCEPTED")
            refused = new_log.count("INPUT_GATE_REFUSED")
            verdict = "inconclusive"
            if any(s["accepted"] for s in new_submissions): verdict = "bypass"
            elif refused and not accepted and attempt.get("status") == "attempted" and control["verdict"] == "bypass" and not any(attempt.get("postResults", [])): verdict = "blocked"
            row = {"route": route, "repetition": repetition, "verdict": verdict, "controlWorked": control["verdict"] == "bypass",
                   "attempt": attempt, "newSubmissions": new_submissions, "acceptedEvents": accepted, "refusedEvents": refused}
            summary["results"].append(row)
            (output / "results.json").write_text(json.dumps(summary, indent=2))
            print(json.dumps(row), flush=True)
            if accepted and verdict != "bypass":
                raise RuntimeError("Input entered the page without completion. Stop before contaminated form state affects later routes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["start", "attack", "stop"])
    parser.add_argument("--session", type=Path, default=ROOT / "artifacts/device-session.json")
    parser.add_argument("--controls", type=Path, default=ROOT / "artifacts/device-controls-expanded/results.json")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--operator-physical-completion-confirmed", action="store_true")
    args = parser.parse_args()
    if args.action == "start": start(args.session.resolve())
    elif args.action == "attack": attack(args.session.resolve(), args.controls, args.repetitions, args.operator_physical_completion_confirmed)
    else:
        session = json.loads(args.session.read_text())
        active(session)
        os.kill(session["pid"], signal.SIGTERM)
