"""Run only unprivileged identity controls and prepare an unexecuted administrator plan."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import time

from prepare_identity_signal_run import prepare
from process_cleanup import matching_pids
from run_native import ROOT


def fault_control(binary, parent_only=False):
    process = subprocess.Popen([str(binary), "--same-user-watchdog-control"], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, start_new_session=True)
    row = {"kind": "kill-parent-only" if parent_only else "terminate-original-process-group", "verified": False}
    try:
        if not select.select([process.stdout], [], [], 5)[0]:
            raise RuntimeError("The owned fault control did not acknowledge its stopped child")
        stage = json.loads(process.stdout.readline())
        row["stage"] = stage
        if stage.get("stage") != "stopped-control" or stage.get("watchdogDetached") is not True:
            raise RuntimeError("The detached watchdog was not ready")
        if os.getsid(process.pid) != process.pid or os.getpgid(process.pid) != process.pid:
            raise RuntimeError("The owned parent does not have its private process group")
        for key in ["targetPID", "actorPID"]:
            if os.getpgid(stage[key]) != process.pid:
                raise RuntimeError("A test child left the owned process group")
        if os.getsid(stage["watchdogPID"]) != stage["watchdogPID"] or os.getpgid(stage["watchdogPID"]) != stage["watchdogPID"]:
            raise RuntimeError("The watchdog shares the interrupted process group")
        if parent_only:
            process.kill()
        else:
            os.killpg(process.pid, signal.SIGTERM)
        row["parentExitCode"] = process.wait(timeout=3)
        expected_exit = -signal.SIGKILL if parent_only else -signal.SIGTERM
        deadline = time.monotonic() + 7
        expected = {stage[key] for key in ["targetPID", "actorPID", "watchdogPID"]}
        while time.monotonic() < deadline:
            remaining = expected & matching_pids(binary)
            if not remaining:
                row["verified"] = row["parentExitCode"] == expected_exit
                break
            time.sleep(0.05)
        row["remainingPIDs"] = sorted(expected & matching_pids(binary))
        if not row["verified"]:
            raise RuntimeError("The detached recovery control did not clean up")
        return row
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=3)
        process.stdout.close()
        process.stderr.close()


def run(output):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    binary = ROOT / ".build/identity-signal-control"
    if matching_pids(binary):
        raise RuntimeError("An existing identity experiment must remain untouched")
    report = {"rootExperimentRun": False, "scope": "Fresh same-user children and safe unprivileged refusals only.", "controls": []}
    try:
        with (output / "build.log").open("w") as stream:
            subprocess.run(["bash", "scripts/build-identity-signal-control.sh"], cwd=ROOT,
                           stdout=stream, stderr=subprocess.STDOUT, check=True, timeout=30)
        report["binarySHA256"] = hashlib.sha256(binary.read_bytes()).hexdigest()
        report["plan"] = prepare(output / "reviewed-run-plan.json")
        for index in range(3):
            process = subprocess.run([str(binary), "--same-user-control"], capture_output=True, text=True, timeout=25)
            row = json.loads(process.stdout)
            row["repetition"] = index
            row["exitCode"] = process.returncode
            report["controls"].append(row)
            if process.returncode or not row.get("passed") or not row.get("cleanupVerified"):
                raise RuntimeError("The same-user signal control failed")
        recovered = subprocess.run([str(binary), "--same-user-watchdog-control"], capture_output=True, text=True, timeout=25)
        report["watchdogControl"] = [json.loads(line) for line in recovered.stdout.splitlines()]
        if recovered.returncode or not report["watchdogControl"][-1].get("passed") or report["watchdogControl"][-1].get("continued"):
            raise RuntimeError("The watchdog-only resume control failed")
        report["groupInterruption"] = fault_control(binary)
        report["parentKilled"] = fault_control(binary, parent_only=True)
        def inherited_signals():
            signal.signal(signal.SIGALRM, signal.SIG_IGN)
            signal.signal(signal.SIGCHLD, signal.SIG_IGN)
            signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGALRM, signal.SIGCHLD})
        inherited = subprocess.run([str(binary), "--same-user-control"], capture_output=True, text=True,
                                   timeout=25, preexec_fn=inherited_signals)
        report["inheritedSignalControl"] = json.loads(inherited.stdout)
        if inherited.returncode or not report["inheritedSignalControl"].get("passed"):
            raise RuntimeError("The inherited signal-state control failed")
        for args in [["--root-experiment"], ["--root-experiment", "1"], ["--same-user-control", "501"], ["--unknown"]]:
            process = subprocess.run([str(binary), *args], capture_output=True, text=True, timeout=25)
            row = json.loads(process.stdout)
            if process.returncode != 2 or row.get("status") != "refused":
                raise RuntimeError("A forbidden invocation did not refuse")
            report.setdefault("refusals", []).append({"arguments": args, "result": row, "exitCode": process.returncode})
        return report
    finally:
        report["remainingPIDs"] = sorted(matching_pids(binary))
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.output)
    print(json.dumps({"controls": len(report["controls"]), "refusals": len(report.get("refusals", [])),
                      "remainingPIDs": report["remainingPIDs"], "rootExperimentRun": report["rootExperimentRun"]}))
