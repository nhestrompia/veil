"""Measure website actions caused by external activation, with no posted input."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

from native_environment import require_input_safety
from process_cleanup import matching_pids
from run_loaded_page_attacks import close, prepare
from run_native import ROOT, Oracle, probe
from run_keyboard_observation import secure_input_enabled


def cycle_outcome(cycle):
    if any(item["accepted"] for item in cycle["newSubmissions"]):
        return "autonomous-website-action"
    if cycle["awayStatus"] == "observed" and cycle["backStatus"] == "observed":
        return "no-action-observed"
    return "inconclusive"


def accepted(state):
    return sum(bool(item["accepted"]) for item in state["submissions"])


def activate(pid, operation=None):
    args = [str(ROOT / ".build/research-focus")]
    if operation:
        args.append("--" + operation)
    process = subprocess.run([*args, str(pid)], capture_output=True, text=True, timeout=5, check=True)
    expected = ("targetHidden=true" if operation == "hide" else "targetHidden=false") if operation else str(pid)
    return "observed" if expected in process.stdout.splitlines() else "inconclusive"


def activation_cycle(target, sink, oracle, hide=False):
    before = oracle.state(target["trial"])
    log_offset = len(target["log"].read_text())
    secure_before = secure_input_enabled()
    away = activate(target["pid"], "hide") if hide else activate(sink["pid"])
    time.sleep(0.2)
    after_away = oracle.state(target["trial"])
    secure_away = secure_input_enabled()
    if hide:
        activate(target["pid"], "unhide")
    back = activate(target["pid"])
    time.sleep(0.5)
    after = oracle.state(target["trial"])
    tail = target["log"].read_text()[log_offset:]
    return {"pid": target["pid"], "beforeAccepted": accepted(before),
            "newActionsWhileDeactivating": accepted(after_away)-accepted(before),
            "newActionsWhileActivating": accepted(after)-accepted(after_away),
            "newSubmissions": after["submissions"][len(before["submissions"]):],
            "acceptedInputEvents": tail.count("INPUT_GATE_ACCEPTED"),
            "diagnosticFocusEvents": [line for line in tail.splitlines() if line.startswith("FOCUS_DIAGNOSTIC") or line.startswith("FOCUS_ACTIVATION_REFUSED")],
            "secureInputBefore": secure_before, "secureInputWhileAway": secure_away,
            "secureInputAfterReturn": secure_input_enabled(),
            "awayStatus": away, "backStatus": back,
            "activationMethod": "NSRunningApplication.hide/unhide/activate; no Accessibility call" if hide else "NSRunningApplication.activate; no Accessibility call",
            "syntheticInputPosted": False, "AXReadSent": False, "AXValueSet": False, "AXPressSent": False}


def run(output, controller, repetitions, surface="focus-action", hide=False, password=False, resume=False, engine_root=None, frame_container=None):
    if engine_root is not None:
        from engine_runtime import engine_environment
        engine_environment(engine_root)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    oracle = Oracle(controller)
    require_input_safety(probe(["permissions"], output / "permissions.json"))
    binaries = {name: ROOT / f"dist/{name}.app/Contents/MacOS/{name}" for name in ["NativeProbe", "InternalKeyboardControl", "InspectableControl"]}
    binaries["ResearchFocus"] = ROOT / ".build/research-focus"
    if any(matching_pids(binaries[name]) for name in ["InternalKeyboardControl", "InspectableControl"]):
        raise RuntimeError("A research reference or diagnostic already exists")
    hashes = {name: hashlib.sha256(binary.read_bytes()).hexdigest() for name, binary in binaries.items()}
    report = {"binarySHA256": hashes, "humanBaseline": False,
              "surface": surface, "hideCycle": hide, "passwordField": password, "frameContainer": frame_container,
              "scope": "Agent activates only research apps. Candidate baseline is private authorized keyboard input. Focus listener is ordinary page code.", "runs": []}

    def save():
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    suffix = f"?surface={surface}" + ("&field-kind=password" if password else "")
    if frame_container:
        suffix += "&frame-container=" + frame_container

    for repetition in range(repetitions):
        if any(hashlib.sha256(binary.read_bytes()).hexdigest() != hashes[name] for name, binary in binaries.items()):
            raise RuntimeError("A focus-test executable changed")
        row = {"repetition": repetition}
        report["runs"].append(row)
        sink = prepare("InspectableControl", output / f"sink-{repetition}", oracle)
        reference = candidate = None
        try:
            reference = prepare("InspectableControl", output / f"reference-{repetition}", oracle, suffix)
            row["referenceArming"] = probe(["ax-action", reference["pid"]], output / f"reference-{repetition}.arm.json")
            time.sleep(0.3)
            if accepted(oracle.state(reference["trial"])) == 0:
                row.update(status="inconclusive", reason="Reference task did not arm")
                continue
            row["control"] = activation_cycle(reference, sink, oracle, hide)
            if not any(item["accepted"] for item in row["control"]["newSubmissions"]):
                row.update(status="inconclusive", reason="Focus reference did not complete")
                continue
            close(reference)
            row["referenceCleanupVerified"] = True
            reference = None
            candidate = prepare("InternalKeyboardControl", output / f"candidate-{repetition}", oracle, suffix, engine_root)
            if engine_root is not None:
                row["engineIdentity"] = candidate["engineIdentity"]
            row["candidate"] = activation_cycle(candidate, sink, oracle, hide)
            row["status"] = cycle_outcome(row["candidate"])
            if resume:
                before_resume = accepted(oracle.state(candidate["trial"]))
                deadline = time.monotonic() + 12
                while time.monotonic() < deadline and "resumeSequenceFinished=true" not in candidate["log"].read_text():
                    time.sleep(0.1)
                row["privateResumeCompleted"] = "resumeSequenceFinished=true" in candidate["log"].read_text()
                resume_log = candidate["log"].read_text().split("sequenceFinished=true noDeviceReader=true", 1)[-1]
                row["privateResumeOwnershipEvents"] = [line for line in resume_log.splitlines()
                    if line.startswith("FOCUS_DIAGNOSTIC phase=before-private-key")]
                time.sleep(0.3)
                row["privateResumeNewActions"] = accepted(oracle.state(candidate["trial"])) - before_resume
            print(json.dumps({"repetition": repetition, "status": row["status"], "candidate": row["candidate"]}), flush=True)
        finally:
            try:
                if candidate:
                    close(candidate)
                    row["candidateCleanupVerified"] = True
                if reference:
                    close(reference)
                    row["referenceCleanupVerified"] = True
                close(sink)
                row["sinkCleanupVerified"] = True
                row["secureInputAfterCleanup"] = secure_input_enabled()
            finally:
                save()
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--controller", type=Path, default=ROOT / "artifacts/page-feature-controller.json")
    parser.add_argument("--repetitions", type=int, choices=range(1, 4), default=3)
    parser.add_argument("--surface", choices=["focus-action", "blur-action", "visibility-action"], default="focus-action")
    parser.add_argument("--hide", action="store_true")
    parser.add_argument("--password", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--engine-frameworks", type=Path)
    parser.add_argument("--frame-container", choices=["iframe", "cross-frame", "srcdoc"])
    args = parser.parse_args()
    run(args.output, args.controller, args.repetitions, args.surface, args.hide, args.password, args.resume, args.engine_frameworks, args.frame_container)
