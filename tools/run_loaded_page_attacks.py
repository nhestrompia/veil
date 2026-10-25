"""Attack an already-loaded diagnostic page without claiming physical calibration."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

from native_environment import observe_console, require_input_safety
from process_cleanup import stop_launched
from run_drag_delivery import launch, ready
from run_native import ROOT, Oracle, probe

ROUTES = ["ax", "hid", "session", "private", "curve-hid", "keycodes-hid",
          "pid-hid", "pid-keys-hid", "pid-keys-keycodes-hid", "pid-window-keycodes-hid",
          "iohid-legacy", "iohid-reports", "vision-curve"]


def frame(pid, output):
    windows = probe(["windows", pid], output)["windows"]
    for window in windows:
        bounds = window.get("kCGWindowBounds", {})
        if window.get("kCGWindowLayer") == 0 and bounds.get("Width", 0) >= 400 and bounds.get("Height", 0) >= 300:
            return [bounds[key] for key in ["X", "Y", "Width", "Height"]]
    raise RuntimeError("No owned normal research window")


def translated_point(control, target_frame):
    source = control["windowFrame"]
    if source[2:] != target_frame[2:]:
        raise RuntimeError("Reference and candidate window sizes differ")
    x, y = control["fieldCenter"]
    if not source[0] < x < source[0] + source[2] or not source[1] < y < source[1] + source[3]:
        raise RuntimeError("Reference field point is outside its window")
    return [target_frame[0] + x - source[0], target_frame[1] + y - source[1]]


def arguments_for(route, pid, point):
    if route == "ax":
        return ["ax-action", pid]
    if route.startswith("iohid-"):
        return ["hid-post-input", pid, *point, route.removeprefix("iohid-")]
    source = route if route in ["hid", "session", "private"] else "hid"
    arguments = ["input", pid, *point, source]
    if route in ["curve-hid", "vision-curve"]:
        arguments.append("curve")
    if route.startswith("pid-window-"):
        arguments.append("pid-window")
    elif route.startswith("pid-keys-"):
        arguments.append("pid-keys")
    elif route.startswith("pid-"):
        arguments.append("pid")
    if "keycodes" in route:
        arguments.append("keycodes")
    return arguments


def score_after_attempt(before, after, log_tail, attempted, control_worked):
    new = after["submissions"][len(before["submissions"]):]
    accepted = log_tail.count("INPUT_GATE_ACCEPTED")
    refused = log_tail.count("INPUT_GATE_REFUSED")
    verdict = "inconclusive"
    if any(item["accepted"] for item in new):
        verdict = "bypass"
    elif control_worked and attempted and refused > 0 and accepted == 0:
        verdict = "blocked"
    return {"newSubmissions": new, "acceptedEvents": accepted, "refusedEvents": refused,
            "newEventTypes": sorted({item["type"] for item in after["events"][len(before["events"]):]}),
            "verdict": verdict}


def prepare(name, output, oracle, url_suffix=""):
    trial = oracle.create()
    log = output.with_suffix(".log")
    launcher, binary = launch(name, log, ["--url", trial["url"] + url_suffix])
    session = {"launcher": launcher, "binary": binary, "pid": None, "trial": trial, "log": log}
    try:
        session["pid"] = ready(log, r"Browser ready: pid=(\d+)")
        if name == "InternalKeyboardControl":
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                state = oracle.state(trial)
                if "INTERNAL_KEYBOARD sequenceFinished=true" in log.read_text() and any(row["accepted"] for row in state["submissions"]):
                    break
                time.sleep(0.1)
            else:
                raise RuntimeError("Diagnostic startup did not complete")
            if sum(bool(row["accepted"]) for row in state["submissions"]) != 1:
                raise RuntimeError("Diagnostic startup needs exactly one accepted baseline action")
            time.sleep(0.4)
        else:
            time.sleep(1)
            if oracle.state(trial)["submissions"]:
                raise RuntimeError("Reference already has a submission before the attack")
        session["binarySHA256"] = hashlib.sha256(binary.read_bytes()).hexdigest()
        return session
    except BaseException:
        close(session)
        raise


def close(session):
    cleaned = stop_launched(session["launcher"], session["binary"], session["pid"])
    launcher = session["launcher"]
    launcher.terminate()
    try:
        launcher.wait(timeout=3)
    except subprocess.TimeoutExpired:
        launcher.kill()
        launcher.wait()
    if not cleaned:
        raise RuntimeError("Research app cleanup failed. Stop desktop tests.")


def attack(session, route, output, oracle, control=None, post_tap="hid"):
    pid, trial, log = session["pid"], session["trial"], session["log"]
    before = oracle.state(trial)
    offset = len(log.read_text())
    row = {"pid": pid, "route": route, "binarySHA256": session["binarySHA256"],
           "initialAcceptedSubmissions": sum(bool(item["accepted"]) for item in before["submissions"]),
           "controlWorked": control is not None and control["verdict"] == "bypass", "verdict": "inconclusive"}
    attempted = False
    try:
        if control is not None:
            probe_hash = hashlib.sha256((ROOT / "dist/NativeProbe.app/Contents/MacOS/NativeProbe").read_bytes()).hexdigest()
            if control["attempt"].get("probeBinarySHA256") != probe_hash:
                raise RuntimeError("The probe changed after reference calibration")
        point = None
        if route == "vision-curve":
            capture = probe(["capture", pid, output.with_suffix(".png")], output.with_suffix(".capture.json"))
            row["capture"] = capture
            if capture.get("status") != "captured":
                raise RuntimeError("Window image unavailable")
            ocr = probe(["ocr", output.with_suffix(".png")], output.with_suffix(".ocr.json"))
            row["disclosure"] = before["secret"] in json.dumps(ocr)
            labels = [item for item in ocr.get("text", []) if "enter native-input" in item["text"].lower()]
            if not labels:
                raise RuntimeError("No field label in target image. No input was sent.")
            x, y, width, height = capture["frame"]
            bx, by, bw, bh = labels[0]["box"]
            point = [x + (bx + bw / 2) * width, y + (1 - by - bh / 2) * height + 57]
            row["coordinateSource"] = "Target image OCR and public fixture layout"
        elif route != "ax":
            current_frame = frame(pid, output.with_suffix(".windows.json"))
            row["windowFrame"] = current_frame
            if control is not None:
                point = translated_point(control, current_frame)
                row["coordinateSource"] = "Matched reference point translated by public window geometry"
            else:
                tree = probe(["ax", pid], output.with_suffix(".ax.json"))
                field = next((item for item in tree.get("elements", []) if item.get("AXRole") == "AXTextField"
                              and "Enter native-input" in [item.get("AXDescription"), item.get("AXTitle")]), None)
                if field is None:
                    row["referenceFieldUnavailable"] = True
                    raise RuntimeError("Reference field is unavailable")
                point = [field["position"][0] + field["size"][0] / 2, field["position"][1] + field["size"][1] / 2]
                row["coordinateSource"] = "Readable reference Accessibility field"
        row["fieldCenter"] = point
        arguments = arguments_for(route, pid, point)
        if post_tap != "hid" and arguments[0] in ["input", "hid-post-input"]:
            arguments.append(f"--{post_tap}-tap")
        row["attempt"] = probe(arguments, output.with_suffix(".attempt.json"))
        attempted = row["attempt"].get("status") == "attempted"
        time.sleep(0.5)
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        row["error"] = str(error)
    after = oracle.state(trial)
    row.update(score_after_attempt(before, after, log.read_text()[offset:], attempted, row["controlWorked"]))
    return row


def run(output, repetitions, routes, post_tap):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    permissions = probe(["permissions"], output / "permissions.json")
    require_input_safety(permissions)
    if not all(permissions.get(key) for key in ["accessibility", "postEvents", "screenCapture"]):
        raise RuntimeError("The probe needs its existing effective grants")
    oracle = Oracle()
    report = {"permissions": permissions, "environment": observe_console(), "postTap": post_tap,
              "humanBaseline": False, "sessionOrigin": "private-diagnostic",
              "scope": "Repeated external actions after a private diagnostic startup. No physical binding or human usability claim.",
              "results": [], "cleanup": []}
    def save():
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    def close_checked(session):
        try:
            close(session)
        except BaseException:
            report["cleanup"].append({"pid": session["pid"], "verified": False})
            save()
            raise
        report["cleanup"].append({"pid": session["pid"], "verified": True})
        save()

    for repetition in range(repetitions):
        controls = {}
        for route in routes:
            prefix = output / f"reference-{repetition}-{route}"
            session = prepare("InspectableControl", prefix, oracle)
            try:
                row = attack(session, route, prefix, oracle, post_tap=post_tap)
                row.update(target="InspectableControl", repetition=repetition)
                controls[route] = row
                report["results"].append(row)
            finally:
                close_checked(session)
            print(json.dumps({key: row.get(key) for key in ["target", "route", "repetition", "verdict"]}), flush=True)
            if row.get("referenceFieldUnavailable"):
                report.update(stoppedEarly=True, stopReason="Readable reference field unavailable. No further trials ran.")
                save()
                return report
        usable = [route for route in routes if controls[route]["verdict"] == "bypass"]
        if not usable:
            continue
        session = prepare("InternalKeyboardControl", output / f"candidate-{repetition}", oracle)
        try:
            for route in routes:
                if route not in usable:
                    report["results"].append({"target": "InternalKeyboardControl", "route": route,
                        "repetition": repetition, "skipped": True, "verdict": "inconclusive",
                        "reason": "No matched working reference"})
                    continue
                row = attack(session, route, output / f"candidate-{repetition}-{route}", oracle, controls[route], post_tap)
                row.update(target="InternalKeyboardControl", repetition=repetition)
                report["results"].append(row)
                save()
                print(json.dumps({key: row.get(key) for key in ["target", "pid", "route", "repetition", "verdict", "disclosure"]}), flush=True)
                if row["verdict"] == "bypass":
                    return report
        finally:
            close_checked(session)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/loaded-page-attacks")
    parser.add_argument("--repetitions", type=int, choices=range(1, 4), default=1)
    parser.add_argument("--routes", nargs="+", choices=ROUTES, default=ROUTES)
    parser.add_argument("--post-tap", choices=["hid", "session", "annotated"], default="hid")
    args = parser.parse_args()
    run(args.output, args.repetitions, args.routes, args.post_tap)
