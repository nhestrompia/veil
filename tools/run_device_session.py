"""Keep one physically calibrated browser alive while external agents attack it."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

from run_native import ROOT, Oracle, probe
from native_environment import require_input_safety
from process_cleanup import matching_pids, process_matches, stop_launched, stop_owned
from run_drag_delivery import launch, ready

NAME = "DeviceKeyboardExperiment"
BINARY = ROOT / f"dist/{NAME}.app/Contents/MacOS/{NAME}"
ROUTES = ["session", "hid", "private", "pid-hid", "curve-hid", "keycodes-hid", "iohid-legacy", "iohid-reports", "pid-keys-hid", "pid-keys-keycodes-hid", "pid-window-keycodes-hid"]


def active(session):
    binary = BINARY
    if session.get("target") == "AgentFreeBrowserPreview":
        binary = ROOT / "dist/AgentFreeBrowserPreview.app/Contents/MacOS/AgentFreeBrowserPreview"
        manifest = json.loads((ROOT / "docs/evidence/integrated-browser-permission-manifest.json").read_text())
        if session["binarySHA256"] != manifest["executableSHA256"]:
            raise RuntimeError("The preview differs from its pinned consent image")
    elif session.get("target") == "AgentFreeBrowserEngine":
        binary = ROOT / "dist/AgentFreeBrowserEngine.app/Contents/MacOS/AgentFreeBrowserEngine"
        manifest = json.loads((ROOT / "docs/evidence/focus-engine-browser-manifest.json").read_text())
        if session["binarySHA256"] != manifest["targets"]["AgentFreeBrowserEngine"]["binarySHA256"]:
            raise RuntimeError("The engine browser differs from its pinned consent image")
    elif session.get('target') == 'AgentFreeBrowserPointer':
        binary = ROOT / 'dist/AgentFreeBrowserPointer.app/Contents/MacOS/AgentFreeBrowserPointer'
        manifest = json.loads((ROOT / 'docs/evidence/hardware-pointer-browser-manifest.json').read_text())
        if session['binarySHA256'] != manifest['targets']['AgentFreeBrowserPointer']['binarySHA256']:
            raise RuntimeError('The pointer candidate differs from its pinned consent image')
    elif session.get("target", NAME) != NAME:
        raise RuntimeError("Unsupported physical-session browser")
    if not process_matches(session["pid"], binary):
        raise RuntimeError("The recorded research browser is no longer running")
    if hashlib.sha256(binary.read_bytes()).hexdigest() != session["binarySHA256"]:
        raise RuntimeError("The browser changed after session start")
    return binary


def start(path):
    if path.exists():
        try:
            active(json.loads(path.read_text()))
        except RuntimeError:
            pass
        else:
            raise RuntimeError("A recorded research session is already running")
    if matching_pids(BINARY):
        raise RuntimeError("A research browser already exists. Refusing a duplicate physical-session window.")
    path.parent.mkdir(parents=True, exist_ok=True)
    log_path = path.with_suffix(".log")
    trial = Oracle().create()
    launcher, binary = launch(NAME, log_path, ["--url", trial["url"]])
    pid = None
    try:
        pid = ready(log_path, r"Browser ready: pid=(\d+)")
        session = {"pid": pid, "launcherPID": launcher.pid, "trial": trial, "log": str(log_path),
                   "binarySHA256": hashlib.sha256(BINARY.read_bytes()).hexdigest()}
        active(session)
        path.write_text(json.dumps(session, indent=2))
    except BaseException:
        cleaned = stop_launched(launcher, binary, pid)
        launcher.terminate()
        try:
            launcher.wait(timeout=3)
        except subprocess.TimeoutExpired:
            launcher.kill()
            launcher.wait()
        if not cleaned:
            raise RuntimeError("Physical-session cleanup failed. Stop desktop tests.")
        raise
    print(json.dumps({"pid": pid, "trial": trial["id"], "sessionFile": str(path)}), flush=True)


def attack(path, controls, repetitions, confirmed, routes=None, post_tap="hid"):
    routes = ROUTES if routes is None else routes
    session = json.loads(path.read_text())
    active(session)
    oracle = Oracle(session.get("controller"))
    before = oracle.state(session["trial"])
    log_path = Path(session["log"])
    if not confirmed or not any(s["accepted"] for s in before["submissions"]) or "DEVICE_KEYBOARD bound=true" not in log_path.read_text():
        raise RuntimeError("Need declared physical completion, a bound device, and an accepted website action in this same session")
    permissions = probe(["permissions"], path.parent / "session-attack-permissions.json")
    require_input_safety(permissions)
    if not permissions.get("postEvents"):
        raise RuntimeError("The probe needs effective event-posting access")
    control_report = json.loads(controls.read_text())
    if control_report.get("postTap", "hid") != post_tap:
        raise RuntimeError("Control insertion point differs from the requested session adapter")
    control_rows = control_report["results"]
    probe_hash = hashlib.sha256((ROOT / "dist/NativeProbe.app/Contents/MacOS/NativeProbe").read_bytes()).hexdigest()
    for route in routes:
        for repetition in range(repetitions):
            control = next((row for row in control_rows if row["target"] == "InspectableControl" and
                            row["route"] == route and row["repetition"] == repetition), None)
            if not control or control.get("attempt", {}).get("probeBinarySHA256") != probe_hash:
                raise RuntimeError(f"Recalibrate {route} repetition {repetition} with the current probe before any attacks")
    output = path.parent / "device-session-attacks"
    output.mkdir(parents=True, exist_ok=True)
    summary = {"results": [], "binarySHA256": session["binarySHA256"], "trial": session["trial"]["id"],
               "postTap": post_tap,
               "operatorDeclaresPhysicalCompletion": True, "bootstrapAttested": False,
               "physicalInputAbsenceVerified": False, "sessionPID": session["pid"],
               "routeContract": "Same physically calibrated browser process. Count only new independent submissions. Fixture clears its field after accepted actions."}
    for route in routes:
        for repetition in range(repetitions):
            active(session)
            if hashlib.sha256((ROOT / "dist/NativeProbe.app/Contents/MacOS/NativeProbe").read_bytes()).hexdigest() != probe_hash:
                raise RuntimeError("The probe changed after reference calibration")
            control = next((r for r in control_rows if r["target"] == "InspectableControl" and
                            r["route"] == route and r["repetition"] == repetition), None)
            if control and control.get("verdict") != "bypass":
                row = {"route": route, "repetition": repetition, "verdict": "inconclusive",
                       "skipped": True, "controlWorked": False, "reason": "Matched reference did not complete"}
                summary["results"].append(row)
                (output / "results.json").write_text(json.dumps(summary, indent=2))
                print(json.dumps(row), flush=True)
                continue
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
            if post_tap != "hid": args.append(f"--{post_tap}-tap")
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
    parser.add_argument("--routes", nargs="+", choices=ROUTES, default=ROUTES)
    parser.add_argument("--post-tap", choices=["hid", "session", "annotated"], default="hid")
    args = parser.parse_args()
    if args.action == "start": start(args.session.resolve())
    elif args.action == "attack": attack(args.session.resolve(), args.controls, args.repetitions,
        args.operator_physical_completion_confirmed, args.routes, args.post_tap)
    else:
        session = json.loads(args.session.read_text())
        binary = active(session)
        if not stop_owned(session["pid"], binary):
            raise RuntimeError("Physical-session cleanup failed. Stop desktop tests.")
