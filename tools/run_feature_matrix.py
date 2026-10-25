"""Test a shared browser policy across editors and frames using diagnostic baselines."""

import argparse
import hashlib
import json
from pathlib import Path

from native_environment import require_input_safety
from process_cleanup import matching_pids
from run_loaded_page_attacks import attack, close, prepare
from run_native import ROOT, Oracle, probe

SURFACES = ["form", "textarea", "editable", "shadow-open", "shadow-closed", "spa", "iframe", "cross-frame", "srcdoc", "focus-action"]
ROUTES = ["hid", "curve-hid", "pid-keys-keycodes-hid", "vision-curve", "ax"]


def run(output, controller, surfaces, routes):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    oracle = Oracle(controller)
    permissions = probe(["permissions"], output / "permissions.json")
    require_input_safety(permissions)
    if not all(permissions.get(key) for key in ["accessibility", "postEvents", "screenCapture"]):
        raise RuntimeError("The frozen native probe needs its existing effective grants")
    names = ["InternalKeyboardControl", "InspectableControl", "NativeProbe"]
    binaries = {name: ROOT / f"dist/{name}.app/Contents/MacOS/{name}" for name in names}
    if any(matching_pids(binaries[name]) for name in names[:2]):
        raise RuntimeError("Another matrix research app exists; refusing duplicate controls")
    hashes = {name: hashlib.sha256(binary.read_bytes()).hexdigest() for name, binary in binaries.items()}
    report = {"binarySHA256": hashes, "permissions": permissions, "humanBaseline": False,
              "scope": "Private authorized keyboard baseline with diagnostic focus assistance, then external attacks. No HID or human-attestation claim.",
              "surfaces": []}

    def save():
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    def unchanged():
        if any(hashlib.sha256(binary.read_bytes()).hexdigest() != hashes[name] for name, binary in binaries.items()):
            raise RuntimeError("A matrix executable changed during comparison")

    for surface in surfaces:
        unchanged()
        row = {"surface": surface, "controls": [], "results": [], "baselineWorked": False}
        report["surfaces"].append(row)
        candidate = None
        try:
            try:
                candidate = prepare("InternalKeyboardControl", output / f"candidate-{surface}", oracle, f"?surface={surface}")
                if "focusAssistedByDiagnostic=true" not in candidate["log"].read_text():
                    raise RuntimeError("The feature-suite diagnostic build is required")
                row.update(pid=candidate["pid"], baselineWorked=True, focusAssistedByDiagnostic=True)
            except (RuntimeError, OSError) as error:
                row.update(status="inconclusive", baselineError=str(error))
                save()
                continue
            for route in routes:
                unchanged()
                before_preparation = oracle.state(candidate["trial"])
                prefix = output / f"reference-{surface}-{route}"
                reference = prepare("InspectableControl", prefix, oracle, f"?surface={surface}")
                control = {"route": route, "cleanupVerified": False}
                try:
                    probe(["ax-direct", reference["pid"]], prefix.with_suffix(".activation.json"))
                    control.update(attack(reference, route, prefix, oracle))
                finally:
                    try:
                        close(reference)
                        control["cleanupVerified"] = True
                    finally:
                        row["controls"].append(control)
                        save()
                after_reference = oracle.state(candidate["trial"])
                preparation_submissions = after_reference["submissions"][len(before_preparation["submissions"]):]
                if any(item["accepted"] for item in preparation_submissions):
                    result = {"route": route, "verdict": "bypass", "operationPhase": "reference-focus-transition",
                              "newSubmissions": preparation_submissions, "syntheticInputPosted": False}
                elif control.get("verdict") != "bypass":
                    result = {"route": route, "skipped": True, "verdict": "inconclusive", "reason": "The matched page-feature reference did not complete"}
                else:
                    activation = probe(["ax-direct", candidate["pid"]], output / f"candidate-{surface}-{route}.activation.json")
                    if activation.get("status") != "observed":
                        row.update(status="inconclusive", stopReason="Candidate foreground activation failed; no input sent")
                        save()
                        break
                    after_preparation = oracle.state(candidate["trial"])
                    new = after_preparation["submissions"][len(before_preparation["submissions"]):]
                    if any(item["accepted"] for item in new):
                        result = {"route": route, "verdict": "bypass", "operationPhase": "foreground-preparation",
                                  "newSubmissions": new, "syntheticInputPosted": False}
                    else:
                        result = attack(candidate, route, output / f"candidate-{surface}-{route}", oracle, control)
                    if any(result.get("attempt", {}).get("postResults", [])) and result["verdict"] != "bypass":
                        result.update(verdict="inconclusive", reason="Native adapter reported a posting error")
                row["results"].append(result)
                save()
                print(json.dumps({"surface": surface, "route": route, "verdict": result["verdict"], "skipped": result.get("skipped", False)}), flush=True)
                if result["verdict"] == "bypass" or result.get("acceptedEvents", 0):
                    row["stopReason"] = "Candidate accepted input or completed a new action"
                    save()
                    return report
        finally:
            if candidate:
                try:
                    close(candidate)
                    row["cleanupVerified"] = True
                finally:
                    save()
        save()
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--controller", type=Path, default=ROOT / "artifacts/page-feature-controller.json")
    parser.add_argument("--surfaces", nargs="+", choices=SURFACES, default=SURFACES)
    parser.add_argument("--routes", nargs="+", choices=ROUTES, default=ROUTES)
    args = parser.parse_args()
    run(args.output, args.controller, args.surfaces, args.routes)
