"""Compare the calibrated token route on one unchanged physical preview."""

import argparse
import json
from pathlib import Path

from calibrate_preview_renderer_read import verified_helper
from process_cleanup import matching_pids
from run_device_session import active
from run_loaded_page_attacks import close, prepare
from run_native import ROOT, Oracle, probe
from run_preview_renderer_reads import observe, read_worked, validate_physical


def run(session_path, physical_path, output):
    session = json.loads(session_path.read_text())
    validate_physical(session, json.loads(physical_path.read_text()))
    active(session)
    digest = verified_helper()
    if matching_pids(ROOT / "dist/InspectableControl.app/Contents/MacOS/InspectableControl"):
        raise RuntimeError("A reference already exists")
    output = output.resolve()
    if not output.is_relative_to((ROOT / "artifacts").resolve()):
        raise ValueError("Use a fresh project artifact directory")
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    oracle = Oracle(session["controller"])
    baseline = oracle.state(session["trial"])
    if not any(item["accepted"] for item in baseline["submissions"]) or "DEVICE_KEYBOARD bound=true" not in Path(session["log"]).read_text():
        raise RuntimeError("Need physical completion and device binding in this unchanged session")
    report = {"mode": "read-token", "candidatePID": session["pid"], "candidateSHA256": session["binarySHA256"],
              "helperSHA256": digest, "inputPosted": False, "actionsSent": False,
              "operatorDeclaresPhysicalCompletion": True, "physicalInputAbsenceVerified": False,
              "bootstrapAttested": False, "candidateQueried": False}

    def save():
        report["newSubmissions"] = oracle.state(session["trial"])["submissions"][len(baseline["submissions"]):]
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    report["permissions"] = observe(["permissions"], output / "permissions.json", digest)
    if report["permissions"].get("accessibility") is not True:
        report["stopReason"] = "The helper's Accessibility grant is ineffective"
        save()
        return report
    reference = prepare("InspectableControl", output / "reference", oracle)
    try:
        activation = probe(["ax-direct", reference["pid"]], output / "reference-activation.json")
        if activation.get("status") != "observed":
            report["stopReason"] = "Reference foreground state unavailable; no renderer query ran"
            return report
        observation = observe(["read-token", reference["pid"]], output / "reference-renderer.json", digest)
        state = oracle.state(reference["trial"])
        report["reference"] = {"observation": observation, "markerRecoveredFromRenderer": read_worked(observation, state["secret"]),
                               "submissions": state["submissions"]}
    finally:
        try:
            close(reference)
            report["referenceCleanupVerified"] = True
        finally:
            save()
    if not report["reference"]["markerRecoveredFromRenderer"]:
        report["stopReason"] = "Token reference did not recover its marker; candidate skipped"
        save()
        return report
    active(session)
    activation = probe(["ax-direct", session["pid"]], output / "candidate-activation.json")
    if activation.get("status") != "observed":
        report["stopReason"] = "Candidate foreground state unavailable; no renderer query ran"
        save()
        return report
    observation = observe(["read-token", session["pid"]], output / "candidate-renderer.json", digest)
    report["candidateQueried"] = observation.get("accessibilityQueried") is True
    report["candidate"] = observation
    recovered = read_worked(observation, baseline["secret"])
    incomplete = observation.get("status") != "observed" or any(q.get("traversalIncomplete") for q in observation.get("queries", []))
    report["readOutcome"] = ("renderer-marker-recovered" if recovered else "inconclusive" if incomplete
                             else "marker-not-recovered-in-bounded-scan")
    active(session)
    save()
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--physical-control", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.session, args.physical_control, args.output)
    print(json.dumps({key: result.get(key) for key in ["readOutcome", "stopReason", "candidateQueried", "newSubmissions"]}))
