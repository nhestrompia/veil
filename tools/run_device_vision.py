"""Use window-scoped images and generated input against a calibrated session."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

from run_device_session import active
from run_native import ROOT, Oracle, probe
from native_environment import require_input_safety
from process_cleanup import stop_launched
from run_drag_delivery import launch, ready
from run_loaded_page_attacks import translated_point


def attempt(pid, trial, prefix, oracle, log_path, reference=None):
    prefix = prefix.resolve()
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
        if labels:
            x, y, width, height = capture["frame"]
            bx, by, bw, bh = labels[0]["box"]
            point = [x + (bx + bw / 2) * width, y + (1 - by - bh / 2) * height + 57]
            row["coordinateSource"] = "Target image OCR and public fixture layout"
        elif reference is not None:
            point = translated_point({"windowFrame": reference["capture"]["frame"],
                                      "fieldCenter": reference["fieldCenter"]}, capture["frame"])
            row["coordinateSource"] = "Matched reference geometry after target OCR failed"
        else:
            raise RuntimeError("No OCR field label; no action-prevention inference")
        row["fieldCenter"] = point
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
    output = output.resolve()
    session = json.loads(session_path.read_text())
    active(session)
    oracle = Oracle()
    state = oracle.state(session["trial"])
    log_path = Path(session["log"])
    if not confirmed or not any(item["accepted"] for item in state["submissions"]) or "DEVICE_KEYBOARD bound=true" not in log_path.read_text():
        raise RuntimeError("Need physical completion and device binding in this unchanged session")
    output.mkdir(parents=True, exist_ok=True)
    permissions = probe(["permissions"], output / "permissions.json")
    require_input_safety(permissions)
    if not permissions.get("screenCapture") or not permissions.get("postEvents"):
        raise RuntimeError("The probe needs effective capture and event-posting access")
    controls = []
    rows = []
    summary = {"results": rows, "controls": controls, "sessionPID": session["pid"],
               "binarySHA256": session["binarySHA256"], "operatorDeclaresPhysicalCompletion": True,
               "bootstrapAttested": False, "physicalInputAbsenceVerified": False,
               "routeContract": "Window-scoped ScreenCaptureKit image, Vision OCR, curved CGEvent typing. Count only new submissions in the physically calibrated process."}
    def save():
        (output / "results.json").write_text(json.dumps(summary, indent=2))

    for repetition in range(repetitions):
        prefix = output / f"control-{repetition}"
        trial = oracle.create()
        log = prefix.with_suffix(".log")
        launcher, control_binary = launch("InspectableControl", log, ["--url", trial["url"]])
        pid = None
        control = {"verdict": "inconclusive", "repetition": repetition}
        try:
            pid = ready(log, r"Browser ready: pid=(\d+)")
            time.sleep(1)
            control = attempt(pid, trial, prefix, oracle, log)
            control["binarySHA256"] = hashlib.sha256(control_binary.read_bytes()).hexdigest()
            control["repetition"] = repetition
        except (RuntimeError, OSError, subprocess.SubprocessError) as error:
            control["error"] = str(error)
        finally:
            cleaned = stop_launched(launcher, control_binary, pid)
            launcher.terminate()
            try:
                launcher.wait(timeout=3)
            except subprocess.TimeoutExpired:
                launcher.kill()
                launcher.wait()
            control["cleanupVerified"] = cleaned
            controls.append(control)
            save()
            if not cleaned:
                raise RuntimeError("Vision reference cleanup failed. Stop desktop tests.")
        active(session)
        if control["verdict"] != "bypass":
            rows.append({"repetition": repetition, "verdict": "inconclusive", "controlWorked": False,
                         "skipped": True, "reason": "Matched vision reference did not complete"})
            save()
            continue
        current_probe = hashlib.sha256((ROOT / "dist/NativeProbe.app/Contents/MacOS/NativeProbe").read_bytes()).hexdigest()
        if control.get("input", {}).get("probeBinarySHA256") != current_probe:
            raise RuntimeError("The probe changed after vision reference calibration")
        row = attempt(session["pid"], session["trial"], output / f"candidate-{repetition}", oracle, log_path, control)
        row["controlWorked"] = control["verdict"] == "bypass"
        row["repetition"] = repetition
        if row["verdict"] != "bypass" and row["controlWorked"] and row.get("input", {}).get("status") == "attempted" and row["refusedEvents"] and not row["acceptedEvents"]:
            row["verdict"] = "blocked-action"
        rows.append(row)
        save()
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
