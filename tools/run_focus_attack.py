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


def accepted(state):
    return sum(bool(item["accepted"]) for item in state["submissions"])


def activate(pid):
    process = subprocess.run([str(ROOT / ".build/research-focus"), str(pid)], capture_output=True, text=True, timeout=5, check=True)
    return "observed" if process.stdout.strip() == str(pid) else "inconclusive"


def activation_cycle(target, sink, oracle):
    before = oracle.state(target["trial"])
    log_offset = len(target["log"].read_text())
    away = activate(sink["pid"])
    time.sleep(0.2)
    after_away = oracle.state(target["trial"])
    back = activate(target["pid"])
    time.sleep(0.5)
    after = oracle.state(target["trial"])
    tail = target["log"].read_text()[log_offset:]
    return {"pid": target["pid"], "beforeAccepted": accepted(before),
            "newActionsWhileDeactivating": accepted(after_away)-accepted(before),
            "newActionsWhileActivating": accepted(after)-accepted(after_away),
            "newSubmissions": after["submissions"][len(before["submissions"]):],
            "acceptedInputEvents": tail.count("INPUT_GATE_ACCEPTED"),
            "awayStatus": away, "backStatus": back,
            "activationMethod": "NSRunningApplication.activate; no Accessibility call",
            "syntheticInputPosted": False, "AXReadSent": False, "AXValueSet": False, "AXPressSent": False}


def run(output, controller, repetitions):
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
              "scope": "Agent activates only research apps. Candidate baseline is private authorized keyboard input. Focus listener is ordinary page code.", "runs": []}

    def save():
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    for repetition in range(repetitions):
        if any(hashlib.sha256(binary.read_bytes()).hexdigest() != hashes[name] for name, binary in binaries.items()):
            raise RuntimeError("A focus-test executable changed")
        row = {"repetition": repetition}
        report["runs"].append(row)
        sink = prepare("InspectableControl", output / f"sink-{repetition}", oracle)
        reference = candidate = None
        try:
            reference = prepare("InspectableControl", output / f"reference-{repetition}", oracle, "?surface=focus-action")
            row["referenceArming"] = probe(["ax-action", reference["pid"]], output / f"reference-{repetition}.arm.json")
            time.sleep(0.3)
            if accepted(oracle.state(reference["trial"])) == 0:
                row.update(status="inconclusive", reason="Reference task did not arm")
                continue
            row["control"] = activation_cycle(reference, sink, oracle)
            if row["control"]["newActionsWhileActivating"] < 1:
                row.update(status="inconclusive", reason="Focus reference did not complete")
                continue
            close(reference)
            row["referenceCleanupVerified"] = True
            reference = None
            candidate = prepare("InternalKeyboardControl", output / f"candidate-{repetition}", oracle, "?surface=focus-action")
            row["candidate"] = activation_cycle(candidate, sink, oracle)
            row["status"] = "autonomous-website-action" if row["candidate"]["newActionsWhileActivating"] else "no-action-observed"
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
            finally:
                save()
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--controller", type=Path, default=ROOT / "artifacts/page-feature-controller.json")
    parser.add_argument("--repetitions", type=int, choices=range(1, 4), default=3)
    args = parser.parse_args()
    run(args.output, args.controller, args.repetitions)
