"""Measure native protection flags during private diagnostic editor transitions."""

import argparse
import json
from pathlib import Path
import subprocess
import time

from engine_runtime import engine_environment
from native_environment import require_input_safety
from process_cleanup import matching_pids
from run_keyboard_observation import secure_input_enabled
from run_loaded_page_attacks import close, prepare
from run_native import ROOT, Oracle, probe


PHASES = ["password-settled", "text-settled", "password-immediate", "text-immediate"]


def parse_transitions(log):
    rows = []
    for line in log.splitlines():
        if line.startswith("PASSWORD_TRANSITION begin="):
            values = dict(item.split("=", 1) for item in line.split()[1:])
            rows.append({"phase": values["begin"], "kind": values["kind"], "settleMS": int(values["settleMS"]),
                         "beforeOwner": values["beforeOwner"], "ownersBeforeKeys": [], "secureInputBeforeKeys": []})
        elif rows and line.startswith("FOCUS_DIAGNOSTIC phase=before-private-key"):
            values = dict(item.split("=", 1) for item in line.split()[1:])
            rows[-1]["ownersBeforeKeys"].append(values["viewSecureOwner"])
            rows[-1]["secureInputBeforeKeys"].append(values["secureInput"])
        elif rows and line.startswith("PASSWORD_TRANSITION end="):
            values = dict(item.split("=", 1) for item in line.split()[1:])
            if values["end"] != rows[-1]["phase"]:
                raise RuntimeError("Transition end does not match its start")
            rows[-1].update(afterOwner=values["afterOwner"], acceptedEvents=int(values["acceptedEvents"]))
    return rows


def transition_outcome(rows, actions):
    if [row["phase"] for row in rows] != PHASES or actions != 5:
        return "inconclusive"
    for row in rows:
        owners = [row["beforeOwner"], *row["ownersBeforeKeys"], row.get("afterOwner")]
        if row.get("acceptedEvents") != 26 or len(row["ownersBeforeKeys"]) != 13 or any(owner not in ["true", "false"] for owner in owners):
            return "inconclusive"
    if any(any(owner != ("true" if row["kind"] == "password" else "false")
                   for owner in [row["beforeOwner"], *row["ownersBeforeKeys"], row["afterOwner"]]) for row in rows):
        return "protection-state-gap-observed"
    return "protection-state-controls-passed"


def run(output, controller, engine_root):
    engine_environment(engine_root)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    require_input_safety(probe(["permissions"], output / "permissions.json"))
    oracle = Oracle(controller)
    report = {"humanBaseline": False, "externalAttack": False,
              "scope": "Private generated typing and per-view native protection bookkeeping. No OS confidentiality claim.", "modes": []}
    try:
        for mode in ["native", "stable"]:
            for name in ["InternalKeyboardControl", "InspectableControl"]:
                if matching_pids(ROOT / f"dist/{name}.app/Contents/MacOS/{name}"):
                    raise RuntimeError("A disposable browser is already running")
            with (output / f"build-{mode}.log").open("w") as stream:
                subprocess.run(["bash", str(ROOT / "scripts/diagnose-browser-keyboard.sh"), "--build-only",
                                "--feature-suite", "--capture-restricted", "--owner-readback", "--password-transitions",
                                "--engine-" + mode], stdout=stream, stderr=subprocess.STDOUT, cwd=ROOT, timeout=120, check=True)
            row = {"mode": mode, "status": "inconclusive"}
            report["modes"].append(row)
            candidate = None
            try:
                candidate = prepare("InternalKeyboardControl", output / f"{mode}-candidate", oracle, "?surface=form", engine_root)
                row.update(binarySHA256=candidate["binarySHA256"], engineIdentity=candidate["engineIdentity"])
                deadline = time.monotonic() + 35
                while time.monotonic() < deadline:
                    if "PASSWORD_TRANSITION sequenceFinished=true" in candidate["log"].read_text():
                        break
                    time.sleep(0.1)
                else:
                    row["reason"] = "The private transition sequence did not finish"
                    return report
                row["transitions"] = parse_transitions(candidate["log"].read_text())
                state = oracle.state(candidate["trial"])
                row["acceptedActions"] = sum(bool(item["accepted"]) for item in state["submissions"])
                row["fieldKindEvents"] = [item for item in state["events"] if item["type"].startswith("field-kind-")]
                row["status"] = transition_outcome(row["transitions"], row["acceptedActions"])
                print(json.dumps({"mode": mode, "status": row["status"], "acceptedActions": row["acceptedActions"],
                                  "transitions": row["transitions"]}), flush=True)
            finally:
                if candidate:
                    close(candidate)
                    row["cleanupVerified"] = True
                row["secureInputAfterCleanup"] = secure_input_enabled()
            if row["status"] == "inconclusive":
                report["stopReason"] = "The generated control did not establish complete transition data"
                return report
        return report
    finally:
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--controller", type=Path, default=ROOT / "artifacts/page-feature-controller.json")
    parser.add_argument("--engine-frameworks", type=Path, default=ROOT / ".build/webkit-engine/output/Release")
    args = parser.parse_args()
    run(args.output, args.controller, args.engine_frameworks)
