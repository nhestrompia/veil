"""Attempt fixed-phrase input in a pinned public-site research session."""

import argparse
import hashlib
import json
from pathlib import Path
import signal
import subprocess
import time

from native_environment import require_input_safety
from process_cleanup import matching_pids, process_matches
from run_native import ROOT, probe, stop_timed_out_probe
from website_challenge import pinned_image, save


def run(session_path, output, point, pause_approved):
    if not pause_approved:
        raise ValueError("The temporary mouse-utility pause needs user approval")
    output = output.resolve()
    if not output.is_relative_to((ROOT / "artifacts").resolve()):
        raise ValueError("Use a fresh project artifact directory")
    session = json.loads(session_path.read_text())
    target = {"AgentFreeBrowserEngine": "engine", "AgentFreeBrowserPreview": "preview", "InspectableControl": "control"}.get(session.get("target"))
    if target is None:
        raise ValueError("Use a pinned research browser session")
    _, _, binary, digest = pinned_image(target)
    if session["binarySHA256"] != digest or not process_matches(session["pid"], binary):
        raise RuntimeError("The research session changed")
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    original = output / "original-apps.json"
    helper = ROOT / ".build/ApprovedModifierPause"
    report = {"pid": session["pid"], "binarySHA256": digest, "point": point,
              "phrase": "native-input", "route": "hid-pid-window-keycodes",
              "userApprovedTemporaryPauseAndRestore": True, "restored": False,
              "websiteTaskOutcome": "requires-physical-review-or-readable-page-evidence"}
    log_path = Path(session["log"])
    previous = {}

    def interrupted(_number, _frame):
        raise TimeoutError("The public input attempt stopped")

    try:
        for number in [signal.SIGINT, signal.SIGTERM, signal.SIGALRM]:
            previous[number] = signal.signal(number, interrupted)
        signal.alarm(90)
        with (output / "pause.log").open("w") as stream:
            subprocess.run([str(helper), "pause", str(original)], check=True,
                           stdout=stream, stderr=subprocess.STDOUT, timeout=20)
        permissions = probe(["permissions"], output / "permissions.json", background=True)
        require_input_safety(permissions)
        if not permissions.get("postEvents"):
            raise RuntimeError("Existing probe event-posting access is ineffective")
        windows = probe(["windows", session["pid"]], output / "windows.json", background=True)
        frames = [w.get("kCGWindowBounds", {}) for w in windows.get("windows", [])
                  if w.get("kCGWindowLayer") == 0]
        if not any(all(k in f for k in ["X", "Y", "Width", "Height"]) and
                   f["X"] <= point[0] < f["X"] + f["Width"] and
                   f["Y"] + 40 <= point[1] < f["Y"] + f["Height"] for f in frames):
            raise RuntimeError("The input point is outside the research window content")
        if not process_matches(session["pid"], binary) or hashlib.sha256(binary.read_bytes()).hexdigest() != digest:
            raise RuntimeError("The target changed before input")
        offset = len(log_path.read_text())
        report["attempt"] = probe(["input", session["pid"], *point, "hid", "pid-window", "keycodes"],
                                  output / "input.json", background=True)
        time.sleep(.8)
        delta = log_path.read_text()[offset:]
        report.update(acceptedEvents=delta.count("INPUT_GATE_ACCEPTED"), refusedEvents=delta.count("INPUT_GATE_REFUSED"))
        report["afterAX"] = probe(["ax", session["pid"]], output / "after-ax.json", background=True)
    except BaseException as error:
        report["error"] = str(error)
        raise
    finally:
        signal.alarm(0)
        for pid_file in output.glob("*.json.pid"):
            stop_timed_out_probe(pid_file)
        remaining = matching_pids(ROOT / "dist/NativeProbe.app/Contents/MacOS/NativeProbe")
        report["remainingProbePIDsBeforeRestore"] = sorted(remaining)
        if remaining:
            save(output / "result.json", report)
            raise RuntimeError("Stop the remaining probe before restoring mouse hooks")
        try:
            if original.exists():
                with (output / "restore.log").open("w") as stream:
                    subprocess.run([str(helper), "restore", str(original)], check=True,
                                   stdout=stream, stderr=subprocess.STDOUT, timeout=20)
                report["restored"] = True
        finally:
            for number, handler in previous.items():
                signal.signal(number, handler)
            save(output / "result.json", report)
    print(json.dumps({k: report.get(k) for k in ["pid", "attempt", "acceptedEvents", "refusedEvents", "restored"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--point", type=float, nargs=2, required=True)
    parser.add_argument("--pause-approved", action="store_true")
    args = parser.parse_args()
    run(args.session, args.output, args.point, args.pause_approved)
