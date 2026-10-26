"""Test hide-induced timer gaps after a stationary no-action control."""

import argparse
import json
from pathlib import Path
import time

from engine_runtime import engine_environment
from native_environment import require_input_safety
from run_engine_activity_matrix import build_diagnostic
from run_focus_attack import accepted, activation_cycle, cycle_outcome
from run_keyboard_observation import secure_input_enabled
from run_loaded_page_attacks import close, prepare
from run_native import ROOT, Oracle, probe


def run(output, controller, engine_root, active_animation=False):
    engine_environment(engine_root)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    require_input_safety(probe(["permissions"], output / "permissions.json"))
    oracle = Oracle(controller)
    report = {"humanBaseline": False, "scope": "Local timer-gap action after private authorized startup. No external input posted.",
              "stationarySeconds": 3, "hiddenSeconds": 3, "activeAnimation": active_animation, "modes": []}

    def save():
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    try:
        for mode in ["native", "stable"]:
            build_diagnostic(mode, output / f"build-{mode}.log", resume=False)
            row = {"mode": mode, "status": "inconclusive"}
            report["modes"].append(row)
            sink = candidate = None
            try:
                sink = prepare("InspectableControl", output / f"{mode}-sink", oracle)
                candidate = prepare("InternalKeyboardControl", output / f"{mode}-candidate", oracle,
                                    "?surface=timer-gap-action&observe-activity=1" + ("&active-animation=1" if active_animation else ""), engine_root)
                row["binarySHA256"] = candidate["binarySHA256"]
                row["engineIdentity"] = candidate["engineIdentity"]
                before = oracle.state(candidate["trial"])
                row["initialAcceptedActions"] = accepted(before)
                if row["initialAcceptedActions"] != 1:
                    row["reason"] = "The timer action occurred before the stationary control"
                    return report
                offset = len(candidate["log"].read_text())
                time.sleep(3)
                after = oracle.state(candidate["trial"])
                row["stationaryNewActions"] = accepted(after) - accepted(before)
                row["stationaryAcceptedInputEvents"] = candidate["log"].read_text()[offset:].count("INPUT_GATE_ACCEPTED")
                if row["stationaryNewActions"] or row["stationaryAcceptedInputEvents"]:
                    row["reason"] = "The stationary control changed before external activation"
                    return report
                row["candidate"] = activation_cycle(candidate, sink, oracle, hide=True, away_seconds=3)
                row["status"] = cycle_outcome(row["candidate"])
                row["timerGapEvents"] = [event for event in oracle.state(candidate["trial"])["events"]
                                         if event.get("type") == "timer-gap-trigger"]
                print(json.dumps({"mode": mode, "status": row["status"], "timerGapEvents": row["timerGapEvents"]}), flush=True)
            except BaseException as error:
                row["error"] = f"{type(error).__name__}: {error}"
                raise
            finally:
                try:
                    if candidate:
                        close(candidate)
                        row["candidateCleanupVerified"] = True
                    if sink:
                        close(sink)
                        row["sinkCleanupVerified"] = True
                    row["secureInputAfterCleanup"] = secure_input_enabled()
                finally:
                    save()
            if mode == "native" and row["status"] != "autonomous-website-action":
                report["stopReason"] = "The native-engine control did not reproduce a timer action"
                return report
        return report
    finally:
        save()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--controller", type=Path, default=ROOT / "artifacts/page-feature-controller.json")
    parser.add_argument("--engine-frameworks", type=Path, default=ROOT / ".build/webkit-engine/output/Release")
    parser.add_argument("--active-animation", action="store_true")
    args = parser.parse_args()
    run(args.output, args.controller, args.engine_frameworks, args.active_animation)
