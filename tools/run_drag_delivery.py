"""Compare cross-app drag delivery on disposable website forms."""

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
from native_environment import observe_console


def stop_owned(pid, binary):
    if pid is None:
        return
    process = subprocess.run(["ps", "-p", str(pid), "-o", "comm="], capture_output=True, text=True)
    if process.stdout.strip() == str(binary):
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass


def ready(log, pattern):
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        match = re.search(pattern, log.read_text())
        if match:
            return int(match[1])
        time.sleep(0.1)
    raise RuntimeError("Research app readiness failed")


def launch(name, log, arguments):
    app = ROOT / f"dist/{name}.app"
    log.write_text("")
    process = subprocess.Popen(["open", "-n", "-W", str(app), "--stdout", str(log), "--stderr", str(log), "--args", *arguments],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return process, app / "Contents/MacOS" / name


def attempt(name, prefix, oracle):
    trial = oracle.create()
    target_log = prefix.with_suffix(".target.log")
    launcher, binary = launch(name, target_log, ["--url", trial["url"] + "?submit-on-input=1"])
    source_launcher = None
    source_pid = pid = None
    source_binary = ROOT / "dist/DragSource.app/Contents/MacOS/DragSource"
    result = {"target": name, "binarySHA256": hashlib.sha256(binary.read_bytes()).hexdigest(), "verdict": "inconclusive",
              "physicalControl": False, "scope": "Cross-app dragging into a disposable form. Candidate uses a separate internal bootstrap diagnostic."}
    try:
        pid = ready(target_log, r"Browser ready: pid=(\d+)")
        result["pid"] = pid
        if name == "InternalKeyboardControl":
            deadline = time.monotonic() + 12
            while "INTERNAL_KEYBOARD sequenceFinished=true" not in target_log.read_text() and time.monotonic() < deadline:
                time.sleep(0.1)
            if "INTERNAL_KEYBOARD sequenceFinished=true" not in target_log.read_text():
                raise RuntimeError("Internal bootstrap did not finish")
        else:
            time.sleep(1)
        capture = probe(["capture", pid, prefix.with_suffix(".png")], prefix.with_suffix(".capture.json"))
        if capture.get("status") != "captured":
            raise RuntimeError("The window-scoped control capture failed")
        ocr = probe(["ocr", prefix.with_suffix(".png")], prefix.with_suffix(".ocr.json"))
        labels = [item for item in ocr.get("text", []) if "enter native-input" in item["text"].lower()]
        if not labels:
            raise RuntimeError("The fixture field label was not readable")
        x, y, width, height = capture["frame"]
        bx, by, bw, bh = labels[0]["box"]
        point = [x + (bx + bw / 2) * width, y + (1 - by - bh / 2) * height + 57]
        result["fieldCenter"] = point
        source_log = prefix.with_suffix(".source.log")
        source_launcher, source_binary = launch("DragSource", source_log, ["--target-pid", str(pid)])
        source_pid = ready(source_log, r"DRAG_SOURCE ready=true pid=(\d+)")
        before = oracle.state(trial)
        offset = len(target_log.read_text())
        result["initialAcceptedSubmissions"] = sum(bool(item["accepted"]) for item in before["submissions"])
        result["input"] = probe(["research-drag", pid, source_pid, *point], prefix.with_suffix(".drag.json"))
        time.sleep(0.8)
        after = oracle.state(trial)
        result["newSubmissions"] = after["submissions"][len(before["submissions"]):]
        result["pageEventTypes"] = sorted({item["type"] for item in after["events"][len(before["events"]):]})
        result["sourceStarted"] = "DRAG_SOURCE began=true" in source_log.read_text()
        result["sourceOperations"] = re.findall(r"ended=true operation=(\d+)", source_log.read_text())
        result["acceptedEvents"] = target_log.read_text()[offset:].count("INPUT_GATE_ACCEPTED")
        result["refusedEvents"] = target_log.read_text()[offset:].count("INPUT_GATE_REFUSED")
        result["refusedDragPhases"] = sorted(set(re.findall(r"DRAG_GATE_REFUSED phase=([a-z.]+)", target_log.read_text()[offset:])))
        result["pageDragDelivered"] = any(kind in result["pageEventTypes"] for kind in ["dragenter", "dragover", "drop"])
        if any(item["accepted"] for item in result["newSubmissions"]):
            result["verdict"] = "action-delivered"
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        result["error"] = str(error)
    finally:
        stop_owned(source_pid, source_binary)
        stop_owned(pid, binary)
        for process in [source_launcher, launcher]:
            if process is not None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
    return result


def run(output, repetitions):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    permissions = probe(["permissions"], output / "permissions.json")
    report = {"results": [], "permissions": permissions, "environment": observe_console(),
              "probeBinarySHA256": permissions["probeBinarySHA256"],
              "dragSourceBinarySHA256": hashlib.sha256((ROOT / "dist/DragSource.app/Contents/MacOS/DragSource").read_bytes()).hexdigest()}
    if not all(permissions.get(key) for key in ["postEvents", "screenCapture"]):
        report["results"].append({"verdict": "inconclusive", "route": "permission-preflight",
                                  "error": "The existing probe grants are not effective. No drag or target launch occurred."})
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
        raise RuntimeError("The existing probe grants are not effective")
    oracle = Oracle()
    rows = report["results"]
    for repetition in range(repetitions):
        control = attempt("InspectableControl", output / f"control-{repetition}", oracle)
        rows.append(control)
        candidate = attempt("InternalKeyboardControl", output / f"candidate-{repetition}", oracle)
        candidate["controlWorked"] = control["verdict"] == "action-delivered"
        if (candidate["verdict"] == "inconclusive" and candidate["controlWorked"]
                and candidate.get("input", {}).get("status") == "attempted" and candidate.get("sourceStarted")
                and candidate.get("refusedDragPhases") and not candidate.get("pageDragDelivered")
                and candidate.get("initialAcceptedSubmissions") == 1):
            candidate["verdict"] = "drag-refused"
        rows.append(candidate)
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({"repetition": repetition, "control": control, "candidate": candidate}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/drag-delivery")
    parser.add_argument("--repetitions", type=int, choices=range(1, 4), default=1)
    args = parser.parse_args()
    run(args.output, args.repetitions)
