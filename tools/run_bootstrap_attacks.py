"""Attack fresh keyboard bindings without claiming a physical-input control."""

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

ROUTES = ["session", "hid", "private", "iohid-legacy", "iohid-reports"]


def run(output, repetitions):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    permission = probe(["permissions"], output / "permissions.json")
    if not permission.get("postEvents"):
        raise RuntimeError("The probe needs its existing effective posting grant")
    oracle = Oracle()
    rows = []
    for route in ROUTES:
        for repetition in range(repetitions):
            for name in ["InspectableControl", "DeviceKeyboardExperiment"]:
                trial = oracle.create()
                prefix = output / f"{name}-{route}-{repetition}"
                log = prefix.with_suffix(".log")
                log.write_text("")
                app = ROOT / f"dist/{name}.app"
                binary = app / f"Contents/MacOS/{name}"
                launcher = subprocess.Popen(["open", "-n", "-W", str(app), "--stdout", str(log), "--stderr", str(log),
                                             "--args", "--url", trial["url"]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                pid = None
                row = {"target": name, "route": route, "repetition": repetition, "trial": trial["id"],
                       "binarySHA256": hashlib.sha256(binary.read_bytes()).hexdigest(), "verdict": "inconclusive"}
                try:
                    for _ in range(60):
                        match = re.search(r"Browser ready: pid=(\d+)", log.read_text())
                        if match:
                            pid = int(match[1])
                            break
                        time.sleep(0.1)
                    if pid is None:
                        raise RuntimeError("Research browser readiness failed")
                    time.sleep(0.6)
                    attempt = probe(["bootstrap-input", pid, route], prefix.with_suffix(".attempt.json"))
                    time.sleep(0.5)
                    state = oracle.state(trial)
                    logs = log.read_text()
                    row.update({"attempt": attempt, "submissions": state["submissions"],
                                "deviceBound": "DEVICE_KEYBOARD bound=true" in logs,
                                "deviceReaderReady": "DEVICE_KEYBOARD permission=true openStatus=0" in logs,
                                "acceptedEvents": logs.count("INPUT_GATE_ACCEPTED"),
                                "refusedEvents": logs.count("INPUT_GATE_REFUSED"), "pageEvents": len(state["events"])})
                    control = next((item for item in rows if item["target"] == "InspectableControl" and
                                    item["route"] == route and item["repetition"] == repetition), None)
                    row["controlWorked"] = control is not None and control["verdict"] == "bypass"
                    if any(item["accepted"] for item in state["submissions"]):
                        row["verdict"] = "bypass"
                    elif name == "DeviceKeyboardExperiment" and row["deviceBound"]:
                        row["verdict"] = "binding-observed-during-attack"
                    elif name == "DeviceKeyboardExperiment" and row["controlWorked"] and row["deviceReaderReady"] and row["refusedEvents"] and not row["acceptedEvents"] and attempt.get("status") == "attempted" and not any(attempt.get("postResults", [])):
                        row["verdict"] = "bootstrap-not-observed"
                except (RuntimeError, OSError, subprocess.SubprocessError) as error:
                    row["error"] = str(error)
                finally:
                    if pid is not None:
                        process = subprocess.run(["ps", "-p", str(pid), "-o", "comm="], capture_output=True, text=True)
                        if process.stdout.strip() == str(binary):
                            os.kill(pid, signal.SIGTERM)
                    launcher.terminate()
                    try:
                        launcher.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        launcher.kill()
                        launcher.wait()
                rows.append(row)
                (output / "results.json").write_text(json.dumps({"results": rows, "humanBaseline": False,
                    "physicalInputAbsenceVerified": False,
                    "scope": "Fresh-process software Space/Return bootstrap and fixed fake task. Absence of binding is an observation, not usable protection or device attestation."}, indent=2))
                print(json.dumps({key: row.get(key) for key in ["target", "route", "repetition", "verdict", "deviceReaderReady", "deviceBound", "acceptedEvents", "refusedEvents", "error"]}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/bootstrap-attacks")
    parser.add_argument("--repetitions", type=int, default=3)
    args = parser.parse_args()
    run(args.output, args.repetitions)
