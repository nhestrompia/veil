"""Use window-scoped images and generated input against a calibrated session."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

from run_device_session import active
from run_native import ROOT, Oracle, probe


def attempt(pid, trial, prefix, oracle, log_path):
    before = oracle.state(trial)
    offset = len(log_path.read_text())
    row = {"pid": pid, "verdict": "inconclusive", "route": "window-image-ocr-curved-hid"}
    try:
        capture = probe(["capture", pid, prefix.with_suffix(".png")], prefix.with_suffix(".capture.json"))
        row["capture"] = capture
        if capture.get("status") != "captured" or "frame" not in capture:
            raise RuntimeError("Window capture failed; no action-prevention inference")
        ocr = probe(["ocr", prefix.with_suffix(".png")], prefix.with_suffix(".ocr.json"))
        row["disclosure"] = before["secret"] in json.dumps(ocr)
        labels = [item for item in ocr.get("text", []) if "enter native-input" in item["text"].lower()]
        if not labels:
            raise RuntimeError("No OCR field label; no action-prevention inference")
        x, y, width, height = capture["frame"]
        bx, by, bw, bh = labels[0]["box"]
        point = [x + (bx + bw / 2) * width, y + (1 - by - bh / 2) * height + 57]
        row["fieldCenter"] = point
        row["coordinateSource"] = "OCR label and public fixture's 57-point offset; no AX tree"
        row["input"] = probe(["input", pid, *point, "hid", "curve"], prefix.with_suffix(".input.json"))
        time.sleep(0.5)
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        row["error"] = str(error)
    after = oracle.state(trial)
    row["newSubmissions"] = after["submissions"][len(before["submissions"]):]
    new_log = log_path.read_text()[offset:]
    row["acceptedEvents"] = new_log.count("INPUT_GATE_ACCEPTED")
    row["refusedEvents"] = new_log.count("INPUT_GATE_REFUSED")
    if any(item["accepted"] for item in row["newSubmissions"]):
        row["verdict"] = "bypass"
    return row


def run(session_path, output, repetitions, confirmed):
    session = json.loads(session_path.read_text())
    active(session)
    oracle = Oracle()
    state = oracle.state(session["trial"])
    log_path = Path(session["log"])
    if not confirmed or not any(item["accepted"] for item in state["submissions"]) or "DEVICE_KEYBOARD bound=true" not in log_path.read_text():
        raise RuntimeError("Need physical completion and device binding in this unchanged session")
    output.mkdir(parents=True, exist_ok=True)
    controls = []
    rows = []
    summary = {"results": rows, "controls": controls, "sessionPID": session["pid"],
               "binarySHA256": session["binarySHA256"], "operatorDeclaresPhysicalCompletion": True,
               "bootstrapAttested": False, "physicalInputAbsenceVerified": False,
               "routeContract": "Window-scoped ScreenCaptureKit image, Vision OCR, curved CGEvent typing. Count only new submissions in the physically calibrated process."}
    control_path = ROOT / "dist/InspectableControl.app"
    control_binary = control_path / "Contents/MacOS/InspectableControl"
    for repetition in range(repetitions):
        prefix = output / f"control-{repetition}"
        trial = oracle.create()
        log = prefix.with_suffix(".log")
        log.write_text("")
        launcher = subprocess.Popen(["open", "-n", "-W", str(control_path), "--stdout", str(log),
                                     "--stderr", str(log), "--args", "--url", trial["url"]],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pid = None
        try:
            for _ in range(60):
                match = re.search(r"Browser ready: pid=(\d+)", log.read_text())
                if match:
                    pid = int(match[1])
                    break
                time.sleep(0.1)
            if pid is None:
                raise RuntimeError("Control readiness failed")
            time.sleep(1)
            control = attempt(pid, trial, prefix, oracle, log)
            control["binarySHA256"] = hashlib.sha256(control_binary.read_bytes()).hexdigest()
            control["repetition"] = repetition
            controls.append(control)
        finally:
            if pid is not None:
                process = subprocess.run(["ps", "-p", str(pid), "-o", "comm="], capture_output=True, text=True)
                if process.stdout.strip() == str(control_binary):
                    os.kill(pid, signal.SIGTERM)
            launcher.terminate()
            try:
                launcher.wait(timeout=3)
            except subprocess.TimeoutExpired:
                launcher.kill()
                launcher.wait()
        active(session)
        row = attempt(session["pid"], session["trial"], output / f"candidate-{repetition}", oracle, log_path)
        row["controlWorked"] = control["verdict"] == "bypass"
        row["repetition"] = repetition
        if row["verdict"] != "bypass" and row["controlWorked"] and row.get("input", {}).get("status") == "attempted" and row["refusedEvents"] and not row["acceptedEvents"]:
            row["verdict"] = "blocked-action"
        rows.append(row)
        (output / "results.json").write_text(json.dumps(summary, indent=2))
        print(json.dumps({key: row.get(key) for key in ["repetition", "verdict", "disclosure", "controlWorked", "acceptedEvents", "refusedEvents"]}), flush=True)
        if row["acceptedEvents"] and row["verdict"] != "bypass":
            raise RuntimeError("Admitted input left uncertain form state; stop further trials")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", type=Path, default=ROOT / "artifacts/device-session.json")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/device-vision")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--operator-physical-completion-confirmed", action="store_true")
    args = parser.parse_args()
    run(args.session, args.output, args.repetitions, args.operator_physical_completion_confirmed)
