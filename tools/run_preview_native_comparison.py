"""Run the approved comparison, then restore the two paused modifier apps."""

import json
import os
import signal
import subprocess
import time

from native_environment import require_input_safety
from process_cleanup import matching_pids
from run_device_session import active
from run_native import ROOT, probe, stop_timed_out_probe
from run_physical_session_attacks import run


def main():
    if os.getuid() == 0:
        raise RuntimeError("Run as the ordinary user")
    plan = ROOT / "docs/evidence/preview-input-resume-plan.json"
    approval = json.loads(plan.read_text())
    if approval.get("approved") is not True:
        raise RuntimeError("The temporary app pause needs approval")
    if approval.get("executed") is True:
        raise RuntimeError("This approved comparison already ran")
    session = ROOT / "artifacts/integrated-browser-134/physical-session/session.json"
    active(json.loads(session.read_text()))
    output = ROOT / "artifacts/integrated-browser-135/native-comparison"
    output.mkdir(exist_ok=False)
    helper = ROOT / ".build/ApprovedModifierPause"
    original = output / "original-apps.json"
    report = {"started": time.time(), "rootUsed": False, "routes": [], "restored": False}
    approval.update(executed=True, executionArtifactDirectory=str(output))
    plan.write_text(json.dumps(approval, indent=2) + "\n")

    def save():
        (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")

    def deadline(_signal, _frame):
        raise TimeoutError("Comparison time limit reached")

    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(600)
    try:
        with (output / "pause.log").open("w") as log:
            subprocess.run([str(helper), "pause", str(original)], check=True, stdout=log, stderr=subprocess.STDOUT, timeout=20)
        permissions = probe(["permissions"], output / "paused-permissions.json", background=True)
        require_input_safety(permissions)
        for route in ["hid", "keycodes-hid", "curve-hid", "session", "private", "pid-hid", "pid-keys-hid", "pid-keys-keycodes-hid", "pid-window-keycodes-hid", "iohid-legacy", "iohid-reports"]:
            result = run(session, output / route, [route], 1)
            report["routes"].append({"route": route, "controls": result["controls"], "results": result["results"], "stoppedEarly": result.get("stoppedEarly", False)})
            save()
            rows = result["results"]
            if result.get("stoppedEarly") or not rows or any(row.get("verdict") != "blocked" for row in rows):
                report["stopReason"] = result.get("stopReason", "Failed or inconclusive comparison; no further input")
                break
    except BaseException as error:
        report["error"] = str(error)
        raise
    finally:
        signal.alarm(0)
        # Do not restore modifying hooks while a native posting process is alive.
        for pid_file in output.rglob("*.json.pid"):
            stop_timed_out_probe(pid_file)
        remaining = matching_pids(ROOT / "dist/NativeProbe.app/Contents/MacOS/NativeProbe")
        report["remainingProbePIDsBeforeRestore"] = sorted(remaining)
        if remaining:
            save()
            raise RuntimeError("Native probe remains active; restore apps only after it stops")
        try:
            if original.exists():
                with (output / "restore.log").open("w") as log:
                    subprocess.run([str(helper), "restore", str(original)], check=True, stdout=log, stderr=subprocess.STDOUT, timeout=20)
                report["restored"] = True
        except BaseException as error:
            report["restorationError"] = str(error)
            raise
        finally:
            report["finished"] = time.time()
            save()
        print(json.dumps({key: report.get(key) for key in ["stopReason", "error", "restored"]}), flush=True)


if __name__ == "__main__":
    main()
