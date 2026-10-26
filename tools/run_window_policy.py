"""Compare native zoom on readable diagnostic windows with and without a frame pin."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

from process_cleanup import matching_pids, stop_launched
from run_drag_delivery import launch, ready
from run_keyboard_observation import secure_input_enabled
from run_loaded_page_attacks import frame
from run_native import ROOT, Oracle, probe


def result(row, reference_worked):
    if row.get("newAcceptedActions", 0):
        return "geometry-triggered-action"
    if reference_worked and row.get("attempted") and row.get("policyRefusals", 0) and not row.get("frameChanged"):
        return "native-zoom-refused"
    return "inconclusive"


def run(output, controller, repetitions):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    binary = ROOT / "dist/WindowPolicyControl.app/Contents/MacOS/WindowPolicyControl"
    if matching_pids(binary):
        raise RuntimeError("An existing policy control must remain untouched")
    with (output / "build.log").open("w") as stream:
        subprocess.run(["bash", "scripts/build-window-policy.sh"], cwd=ROOT, stdout=stream,
                       stderr=subprocess.STDOUT, timeout=90, check=True)
    oracle = Oracle(controller)
    report = {"scope": "Readable AppKit geometry policy diagnostic. System WebKit, no physical-human or integrated browser claim.",
              "binarySHA256": hashlib.sha256(binary.read_bytes()).hexdigest(), "rows": []}
    try:
        for repetition in range(repetitions):
            reference_worked = False
            for mode in ["ordinary", "fixed"]:
                row = {"repetition": repetition, "mode": mode, "status": "inconclusive"}
                report["rows"].append(row)
                if mode == "fixed" and not reference_worked:
                    row["skipped"] = True
                    continue
                trial = oracle.create()
                prefix = output / f"{repetition}-{mode}"
                log = prefix.with_suffix(".log")
                launcher = None
                pid = None
                try:
                    args = ["--url", trial["url"] + "?surface=resize-action"]
                    if mode == "fixed":
                        args.append("--fixed-geometry")
                    launcher, _ = launch("WindowPolicyControl", log, args)
                    pid = ready(log, r"Browser ready: pid=(\d+)")
                    row["pid"] = pid
                    time.sleep(1)
                    row["arming"] = probe(["ax-action", pid], prefix.with_suffix(".arm.json"))
                    deadline = time.monotonic() + 4
                    while time.monotonic() < deadline:
                        before = oracle.state(trial)
                        if any(event["type"] == "geometry-ready" for event in before["events"]):
                            break
                        time.sleep(0.1)
                    else:
                        raise RuntimeError("The readable geometry fixture did not arm")
                    if sum(bool(item["accepted"]) for item in before["submissions"]) != 1:
                        raise RuntimeError("The startup task is not an independent single action")
                    time.sleep(1)
                    if len(oracle.state(trial)["submissions"]) != len(before["submissions"]):
                        raise RuntimeError("The stationary control changed before the attempt")
                    row["beforeFrame"] = frame(pid, prefix.with_suffix(".before.json"))
                    offset = len(log.read_text())
                    done = prefix.with_suffix(".done.json")
                    print(json.dumps({"status": "computer-use-ready", "mode": mode, "pid": pid,
                                      "repetition": repetition, "doneFile": str(done)}), flush=True)
                    deadline = time.monotonic() + 115
                    while time.monotonic() < deadline and not done.exists():
                        time.sleep(0.1)
                    row["receipt"] = json.loads(done.read_text()) if done.exists() else {"attempted": False, "reason": "No receipt before deadline"}
                    row["attempted"] = row["receipt"].get("attempted") is True
                    time.sleep(0.5)
                    after = oracle.state(trial)
                    row["afterFrame"] = frame(pid, prefix.with_suffix(".after.json"))
                    row["frameChanged"] = row["beforeFrame"] != row["afterFrame"]
                    row["newAcceptedActions"] = sum(bool(item["accepted"]) for item in after["submissions"][len(before["submissions"]):])
                    row["policyRefusals"] = log.read_text()[offset:].count("GEOMETRY_POLICY refused=")
                    row["pinActive"] = "GEOMETRY_POLICY pinned=true" in log.read_text()
                    row["geometryEvents"] = [event for event in after["events"] if event["type"].startswith("geometry-")]
                    row["status"] = result(row, reference_worked)
                    if mode == "ordinary":
                        reference_worked = row["status"] == "geometry-triggered-action" and row["frameChanged"]
                    print(json.dumps({key: row[key] for key in ["repetition", "mode", "status", "frameChanged", "newAcceptedActions", "policyRefusals"]}), flush=True)
                finally:
                    row["cleanupVerified"] = stop_launched(launcher, binary, pid)
                    row["secureInputAfterCleanup"] = secure_input_enabled()
                    (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
                    if not row["cleanupVerified"]:
                        raise RuntimeError("Temporary policy app did not exit")
    finally:
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--controller", type=Path, default=ROOT / "artifacts/page-feature-controller.json")
    parser.add_argument("--repetitions", type=int, choices=range(1, 4), default=1)
    args = parser.parse_args()
    run(args.output, args.controller, args.repetitions)
