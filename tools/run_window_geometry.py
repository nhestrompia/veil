"""Test native window geometry using a scoped helper or computer-use receipts."""

import argparse
import json
from pathlib import Path
import subprocess
import time

from engine_runtime import engine_environment
from native_environment import require_input_safety
from run_engine_activity_matrix import build_diagnostic
from run_keyboard_observation import secure_input_enabled
from run_loaded_page_attacks import close, frame, prepare
from run_native import ROOT, Oracle, probe


def geometry_probe(arguments, output):
    output = output.resolve()
    app = ROOT / "dist/WindowGeometryProbe.app"
    subprocess.run(["open", "-n", "-W", str(app), "--stdout", str(output), "--stderr", str(output), "--args", *arguments],
                   capture_output=True, timeout=20, check=True)
    return json.loads(output.read_text())


def outcome(row, control_worked):
    if row.get("privateInputOverlap"):
        return "inconclusive"
    if row.get("newAcceptedActions", 0):
        return "autonomous-website-action"
    if row.get("acceptedInputEvents", 0):
        return "admitted-input"
    if control_worked and row.get("attempted"):
        if row.get("frameChanged"):
            return "no-page-action-observed"
        if row.get("refusedEvents", 0):
            return "window-gesture-blocked"
    return "inconclusive"


def run(output, controller, engine_root, operations, driver):
    if driver == "native" and "zoom" in operations:
        raise ValueError("The native geometry helper supports move and shrink only")
    engine_environment(engine_root)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    oracle = Oracle(controller)
    permissions = probe(["permissions"], output / "permissions.json")
    require_input_safety(permissions)
    report = {"humanBaseline": False, "driver": driver,
              "scope": "Native window gestures on disposable local pages after one authorized task. No keyboard input in the gesture phase.", "rows": []}
    try:
        build_diagnostic("stable", output / "build.log", resume=False)
        if driver == "native":
            report["geometryPreflight"] = geometry_probe(["--preflight"], output / "geometry-preflight.json")
            if not report["geometryPreflight"]["postEvents"]:
                report["stopReason"] = "The separate geometry helper has no effective posting access. No grant requested or geometry input posted."
                return report
            require_input_safety(report["geometryPreflight"])
        for operation in operations:
            control_worked = False
            for kind, name in [("reference", "InspectableControl"), ("candidate", "InternalKeyboardControl")]:
                row = {"operation": operation, "target": kind, "status": "inconclusive"}
                report["rows"].append(row)
                if kind == "candidate" and not control_worked:
                    row.update(skipped=True, reason="The matched reference did not complete a geometry-triggered task")
                    continue
                target = None
                prefix = output / f"{operation}-{kind}"
                try:
                    target = prepare(name, prefix, oracle, "?surface=" + ("move-action" if operation == "move" else "resize-action"),
                                     engine_root if kind == "candidate" else None)
                    if kind == "reference":
                        row["arming"] = probe(["ax-action", target["pid"]], prefix.with_suffix(".arm.json"))
                    row["pid"] = target["pid"]
                    row["binarySHA256"] = target["binarySHA256"]
                    if kind == "candidate":
                        row["engineIdentity"] = target["engineIdentity"]
                    deadline = time.monotonic() + 3
                    while time.monotonic() < deadline:
                        before = oracle.state(target["trial"])
                        if any(event["type"] == "geometry-ready" for event in before["events"]):
                            break
                        time.sleep(0.1)
                    else:
                        raise RuntimeError("The geometry task did not arm")
                    if sum(bool(item["accepted"]) for item in before["submissions"]) != 1:
                        raise RuntimeError("Geometry control needs exactly one initial task")
                    time.sleep(1)
                    stationary = oracle.state(target["trial"])
                    if len(stationary["submissions"]) != len(before["submissions"]):
                        raise RuntimeError("The stationary geometry control changed")
                    row["beforeFrame"] = frame(target["pid"], prefix.with_suffix(".before.json"))
                    before = oracle.state(target["trial"])
                    offset = len(target["log"].read_text())
                    if driver == "computer-use":
                        done = prefix.with_suffix(".done.json")
                        print(json.dumps({"status": "computer-use-ready", "operation": operation, "target": kind,
                                          "pid": target["pid"], "frame": row["beforeFrame"], "doneFile": str(done)}), flush=True)
                        deadline = time.monotonic() + (180 if kind == "reference" else 65)
                        while time.monotonic() < deadline and not done.exists():
                            time.sleep(0.1)
                        row["driverReceipt"] = json.loads(done.read_text()) if done.exists() else {"attempted": False, "reason": "No computer-use receipt before deadline"}
                    else:
                        result = geometry_probe([operation, str(target["pid"])], prefix.with_suffix(".geometry.json"))
                        row["driverReceipt"] = {"attempted": result.get("status") == "attempted", "result": result}
                    row["attempted"] = row["driverReceipt"].get("attempted") is True
                    time.sleep(0.4)
                    after = oracle.state(target["trial"])
                    tail = target["log"].read_text()[offset:]
                    row["afterFrame"] = frame(target["pid"], prefix.with_suffix(".after.json"))
                    row["frameChanged"] = row["beforeFrame"] != row["afterFrame"]
                    row["newAcceptedActions"] = sum(bool(item["accepted"]) for item in after["submissions"][len(before["submissions"]):])
                    row["acceptedInputEvents"] = tail.count("INPUT_GATE_ACCEPTED")
                    row["refusedEvents"] = tail.count("INPUT_GATE_REFUSED")
                    row["privateInputOverlap"] = "FOCUS_DIAGNOSTIC phase=before-private-key" in tail
                    row["geometryEvents"] = [event for event in after["events"] if event["type"].startswith("geometry-")]
                    observed = row["driverReceipt"].get("observedMarker")
                    row["freshMarkerDisclosed"] = isinstance(observed, str) and observed == before["secret"]
                    row["status"] = outcome(row, control_worked)
                    if kind == "reference":
                        control_worked = row["status"] == "autonomous-website-action" and row["frameChanged"]
                    print(json.dumps({"operation": operation, "target": kind, "status": row["status"],
                                      "frameChanged": row["frameChanged"], "freshMarkerDisclosed": row["freshMarkerDisclosed"]}), flush=True)
                finally:
                    if target:
                        close(target)
                        row["cleanupVerified"] = True
                    row["secureInputAfterCleanup"] = secure_input_enabled()
                    (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
        return report
    finally:
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--controller", type=Path, default=ROOT / "artifacts/page-feature-controller.json")
    parser.add_argument("--engine-frameworks", type=Path, default=ROOT / ".build/webkit-engine/output/Release")
    parser.add_argument("--operations", nargs="+", choices=["move", "shrink", "zoom"], default=["move", "shrink"])
    parser.add_argument("--driver", choices=["native", "computer-use"], default="native")
    args = parser.parse_args()
    run(args.output, args.controller, args.engine_frameworks, args.operations, args.driver)
