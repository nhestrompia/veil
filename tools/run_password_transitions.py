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
from run_focus_attack import activate


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


def private_entry_coverage(rows, actions):
    return (transition_outcome(rows, actions) != "inconclusive"
            and all(len(row.get("secureInputBeforeKeys", [])) == 13
                    and all(value == "true" for value in row["secureInputBeforeKeys"]) for row in rows))


def check_private_entry_focus(candidate, output, oracle):
    row = {"hideStatus": activate(candidate["pid"], "hide")}
    time.sleep(0.3)
    row["secureInputWhileHidden"] = secure_input_enabled()
    row["nativeFocusLossReleased"] = "ended=true reason=native-focus-loss releaseStatus=0" in candidate["log"].read_text()
    if row["hideStatus"] != "observed" or row["secureInputWhileHidden"] or not row["nativeFocusLossReleased"]:
        row["reason"] = "The private-entry owner did not verify release on native focus loss"
        return row
    reference = prepare("InspectableControl", output / "readable-control", oracle)
    try:
        row["readableAttempt"] = probe(["ax-action", reference["pid"]], output / "readable-input.json")
        time.sleep(0.3)
        row["readableActions"] = sum(bool(item["accepted"]) for item in oracle.state(reference["trial"])["submissions"])
    finally:
        close(reference)
        row["readableCleanupVerified"] = True
    row["unhideStatus"] = activate(candidate["pid"], "unhide")
    row["returnStatus"] = activate(candidate["pid"])
    time.sleep(0.2)
    row["secureInputBeforeNewSession"] = secure_input_enabled()
    deadline = time.monotonic() + 25
    while time.monotonic() < deadline:
        log = candidate["log"].read_text()
        if "PRIVATE_ENTRY resumeSequenceFinished=true" in log:
            break
        time.sleep(0.1)
    else:
        row["reason"] = "The new private-entry session did not finish"
        return row
    resume = log.split("PASSWORD_TRANSITION sequenceFinished=true", 1)[-1]
    row["resumeOwnershipEvents"] = [line for line in resume.splitlines() if line.startswith("FOCUS_DIAGNOSTIC phase=before-private-key")]
    row["acceptedActionsAfterResume"] = sum(bool(item["accepted"]) for item in oracle.state(candidate["trial"])["submissions"])
    row["secureInputAfterNewSession"] = secure_input_enabled()
    row["passed"] = (row.get("readableActions") == 1 and row["unhideStatus"] == row["returnStatus"] == "observed"
                     and not row["secureInputBeforeNewSession"] and not row["secureInputAfterNewSession"]
                     and row["acceptedActionsAfterResume"] == 6 and len(row["resumeOwnershipEvents"]) == 13
                     and all("secureInput=true" in line for line in row["resumeOwnershipEvents"]))
    return row


def run(output, controller, engine_root, private_entry=False):
    engine_environment(engine_root)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    require_input_safety(probe(["permissions"], output / "permissions.json"))
    oracle = Oracle(controller)
    report = {"humanBaseline": False, "externalAttack": False,
              "scope": "Private generated typing and per-view native protection bookkeeping. No OS confidentiality claim.",
              "privateEntrySession": private_entry, "privateEntryExpiryControl": private_entry, "modes": []}
    try:
        for mode in (["stable"] if private_entry else ["native", "stable"]):
            for name in ["InternalKeyboardControl", "InspectableControl"]:
                if matching_pids(ROOT / f"dist/{name}.app/Contents/MacOS/{name}"):
                    raise RuntimeError("A disposable browser is already running")
            with (output / f"build-{mode}.log").open("w") as stream:
                subprocess.run(["bash", str(ROOT / "scripts/diagnose-browser-keyboard.sh"), "--build-only",
                                "--feature-suite", "--capture-restricted", "--owner-readback", "--password-transitions",
                                "--engine-" + mode, *(["--private-entry-session"] if private_entry else [])],
                               stdout=stream, stderr=subprocess.STDOUT, cwd=ROOT, timeout=120, check=True)
            row = {"mode": mode, "status": "inconclusive"}
            report["modes"].append(row)
            candidate = None
            try:
                candidate = prepare("InternalKeyboardControl", output / f"{mode}-candidate", oracle, "?surface=form", engine_root)
                row.update(binarySHA256=candidate["binarySHA256"], engineIdentity=candidate["engineIdentity"])
                deadline = time.monotonic() + 35
                while time.monotonic() < deadline:
                    log = candidate["log"].read_text()
                    if private_entry and "expirySecureInput" not in row and "ended=true reason=expiry releaseStatus=0" in log:
                        row["expirySecureInput"] = secure_input_enabled()
                    if "PASSWORD_TRANSITION sequenceFinished=true" in log:
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
                if private_entry:
                    row["nativeViewOutcome"] = row["status"]
                    row["privateEntryCoverage"] = private_entry_coverage(row["transitions"], row["acceptedActions"])
                    row["focusReleaseControl"] = check_private_entry_focus(candidate, output, oracle)
                    row["status"] = ("private-entry-controls-passed" if row["privateEntryCoverage"]
                                     and row["focusReleaseControl"].get("passed") and row.get("expirySecureInput") is False
                                     else "inconclusive")
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
    parser.add_argument("--private-entry-session", action="store_true")
    args = parser.parse_args()
    run(args.output, args.controller, args.engine_frameworks, args.private_entry_session)
