"""Calibrate external input routes, then test one guarded window per fresh candidate."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

from engine_runtime import engine_environment
from native_environment import require_input_safety
from process_cleanup import matching_pids
from run_focus_attack import activate
from run_keyboard_observation import secure_input_enabled
from run_loaded_page_attacks import attack, close, prepare
from run_native import ROOT, Oracle, probe


SURFACES = ["form", "textarea", "editable", "shadow-open", "shadow-closed", "spa", "iframe", "cross-frame", "srcdoc"]
ROUTES = ["hid", "curve-hid", "pid-keys-keycodes-hid"]


def guarded_verdict(result, window):
    if window.get("privateInputOverlap"):
        return "inconclusive"
    if any(item["accepted"] for item in result.get("newSubmissions", [])):
        return "bypass"
    if result.get("acceptedEvents", 0):
        return "admitted-input"
    if (result.get("verdict") == "blocked" and window.get("activeThroughout")
            and not any(result.get("attempt", {}).get("postResults", []))):
        return "blocked"
    return "inconclusive"


def window_attack(candidate, control, route, output, oracle):
    log = candidate["log"].read_text()
    marker = re.search(r"^PRIVATE_ENTRY_ATTACK ready=true startedWall=([0-9.]+) maximumSeconds=10 noFurtherPrivateTyping=true$", log, re.M)
    if not marker:
        raise RuntimeError("The candidate did not establish an external-only attack window")
    started = float(marker[1])
    offset = len(log)
    before_wall = time.time()
    before_mono = time.monotonic()
    secure_before = secure_input_enabled()
    if not started <= before_wall < started + 8 or not secure_before:
        return {"route": route, "verdict": "inconclusive", "reason": "Too little verified protected time remains. No input sent."}
    result = attack(candidate, route, output, oracle, control)
    after_wall = time.time()
    after_mono = time.monotonic()
    secure_after = secure_input_enabled()
    after_log = candidate["log"].read_text()
    active_tail = after_log[marker.end():]
    tail = after_log[offset:]
    clock_stable = abs((after_wall - before_wall) - (after_mono - before_mono)) < 0.1
    window = {"startedWall": started, "attemptStartedWall": before_wall, "attemptFinishedWall": after_wall,
              "clockStable": clock_stable, "secureInputBefore": secure_before, "secureInputAfter": secure_after,
              "privateInputOverlap": "FOCUS_DIAGNOSTIC phase=before-private-key" in tail,
              "leaseEnded": "PRIVATE_ENTRY ended=true" in active_tail,
              "activeThroughout": (clock_stable and secure_before and secure_after and after_wall < started + 9
                                   and "PRIVATE_ENTRY ended=true" not in active_tail)}
    result["window"] = window
    result["unscopedVerdict"] = result["verdict"]
    result["verdict"] = guarded_verdict(result, window)
    return result


def run(output, controller, engine_root, surfaces, routes):
    engine_environment(engine_root)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    oracle = Oracle(controller)
    permissions = probe(["permissions"], output / "permissions.json")
    require_input_safety(permissions)
    if not all(permissions.get(key) for key in ["accessibility", "postEvents", "screenCapture"]):
        raise RuntimeError("The frozen native probe needs its existing effective grants")
    report = {"humanBaseline": False, "scope": "External synthetic input after one private startup task. No further private typing in candidate.",
              "permissions": permissions, "rows": []}

    def save():
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    for name in ["InternalKeyboardControl", "InspectableControl"]:
        if matching_pids(ROOT / f"dist/{name}.app/Contents/MacOS/{name}"):
            raise RuntimeError("A disposable research browser already exists")
    try:
        with (output / "build.log").open("w") as stream:
            subprocess.run(["bash", str(ROOT / "scripts/diagnose-browser-keyboard.sh"), "--build-only", "--feature-suite",
                            "--owner-readback", "--capture-restricted", "--engine-stable", "--private-entry-session",
                            "--private-entry-attacks"], cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=120, check=True)
        binary = ROOT / "dist/InternalKeyboardControl.app/Contents/MacOS/InternalKeyboardControl"
        candidate_hash = hashlib.sha256(binary.read_bytes()).hexdigest()
        report["candidateSHA256"] = candidate_hash
        for surface in surfaces:
            for route in routes:
                row = {"surface": surface, "route": route, "verdict": "inconclusive"}
                report["rows"].append(row)
                reference = candidate = None
                prefix = output / f"{surface}-{route}"
                try:
                    reference = prepare("InspectableControl", prefix.with_name(prefix.name + "-reference"), oracle, "?surface=" + surface)
                    row["controlActivation"] = activate(reference["pid"])
                    control = attack(reference, route, prefix.with_name(prefix.name + "-reference"), oracle)
                    row["control"] = control
                    close(reference)
                    reference = None
                    row["referenceCleanupVerified"] = True
                    if control["verdict"] != "bypass":
                        row["reason"] = "The matched readable reference did not complete. Candidate skipped."
                        continue
                    if hashlib.sha256(binary.read_bytes()).hexdigest() != candidate_hash:
                        raise RuntimeError("The candidate changed after calibration")
                    candidate = prepare("InternalKeyboardControl", prefix.with_name(prefix.name + "-candidate"), oracle,
                                        "?surface=" + surface, engine_root)
                    row["baselineWorked"] = True
                    row["engineIdentity"] = candidate["engineIdentity"]
                    row["candidate"] = window_attack(candidate, control, route, prefix.with_name(prefix.name + "-candidate"), oracle)
                    row["verdict"] = row["candidate"]["verdict"]
                    deadline = time.monotonic() + 12
                    while time.monotonic() < deadline:
                        log = candidate["log"].read_text()
                        if "PRIVATE_ENTRY_ATTACK finished=true" in log:
                            break
                        time.sleep(0.1)
                    row["windowFinished"] = "PRIVATE_ENTRY_ATTACK finished=true" in log
                    row["expiryReleaseVerified"] = "ended=true reason=expiry releaseStatus=0" in log
                    row["secureInputAfterExpiry"] = secure_input_enabled()
                    row["finalAcceptedActions"] = sum(bool(item["accepted"]) for item in oracle.state(candidate["trial"])["submissions"])
                    if row["finalAcceptedActions"] > 1 and row["verdict"] not in ["bypass", "admitted-input"]:
                        row["verdict"] = "bypass"
                        row["reason"] = "An action occurred after the external attempt with no scheduled private input"
                    if row["verdict"] == "blocked" and (not row["windowFinished"] or not row["expiryReleaseVerified"] or row["secureInputAfterExpiry"]):
                        row.update(verdict="inconclusive", reason="The protected window did not verify orderly expiry")
                    print(json.dumps({key: row[key] for key in ["surface", "route", "verdict"]}), flush=True)
                except BaseException as error:
                    row["error"] = f"{type(error).__name__}: {error}"
                    raise
                finally:
                    try:
                        if reference:
                            close(reference)
                            row["referenceCleanupVerified"] = True
                        if candidate:
                            close(candidate)
                            row["candidateCleanupVerified"] = True
                        row["secureInputAfterCleanup"] = secure_input_enabled()
                        if row["secureInputAfterCleanup"]:
                            raise RuntimeError("Secure Event Input remains enabled after research cleanup")
                    finally:
                        save()
                if row["verdict"] in ["bypass", "admitted-input"]:
                    report["stopReason"] = "The candidate accepted external input or a website action"
                    return report
        return report
    finally:
        save()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--controller", type=Path, default=ROOT / "artifacts/page-feature-controller.json")
    parser.add_argument("--engine-frameworks", type=Path, default=ROOT / ".build/webkit-engine/output/Release")
    parser.add_argument("--surfaces", nargs="+", choices=SURFACES, default=SURFACES)
    parser.add_argument("--routes", nargs="+", choices=ROUTES, default=ROUTES)
    args = parser.parse_args()
    run(args.output, args.controller, args.engine_frameworks, args.surfaces, args.routes)
