"""Pair fresh native references with one unchanged physically calibrated browser."""

import argparse
import hashlib
import json
from pathlib import Path

from native_environment import require_input_safety
from process_cleanup import matching_pids
from run_device_session import ROUTES, active
from run_loaded_page_attacks import attack, close, prepare
from run_native import ROOT, Oracle, probe


def input_error(row):
    return any(row.get("attempt", {}).get("postResults", []))


def run(session_path, output, routes, repetitions):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    session = json.loads(session_path.read_text())
    session["log"] = Path(session["log"])
    active(session)
    oracle = Oracle(session.get("controller"))
    initial = oracle.state(session["trial"])
    if not any(item["accepted"] for item in initial["submissions"]) or "DEVICE_KEYBOARD bound=true" not in session["log"].read_text():
        raise RuntimeError("Need physical completion and device binding in the unchanged browser")
    if matching_pids(ROOT / "dist/InspectableControl.app/Contents/MacOS/InspectableControl"):
        raise RuntimeError("A readable reference already exists. Refusing duplicate controls.")
    permissions = probe(["permissions"], output / "permissions.json")
    require_input_safety(permissions)
    if not permissions.get("accessibility") or not permissions.get("postEvents"):
        raise RuntimeError("The frozen probe needs its existing Accessibility and event-posting grants")
    binary = ROOT / "dist/NativeProbe.app/Contents/MacOS/NativeProbe"
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    report = {"sessionPID": session["pid"], "binarySHA256": session["binarySHA256"],
              "probeBinarySHA256": digest, "trial": session["trial"]["id"], "permissions": permissions,
              "physicalBaselinePreviouslyConfirmed": True, "physicalInputAbsenceVerified": False,
              "scope": "Fresh matched native references; exact unchanged physical session; translated public fixture geometry.",
              "controls": [], "results": []}

    def save():
        report["newSubmissions"] = oracle.state(session["trial"])["submissions"][len(initial["submissions"]):]
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    for route in routes:
        for repetition in range(repetitions):
            active(session)
            if hashlib.sha256(binary.read_bytes()).hexdigest() != digest:
                raise RuntimeError("The native probe changed during the comparison")
            reference = prepare("InspectableControl", output / f"reference-{route}-{repetition}", oracle)
            control = {"route": route, "repetition": repetition, "verdict": "inconclusive", "cleanupVerified": False}
            try:
                initialization = probe(["ax-direct", reference["pid"]], output / f"reference-{route}-{repetition}.activation.json")
                control["foregroundInitializationStatus"] = initialization.get("status")
                if initialization.get("status") == "observed":
                    control.update(attack(reference, route, output / f"reference-{route}-{repetition}", oracle))
                else:
                    control["error"] = "Reference foreground activation was not verified; no input sent"
                if input_error(control):
                    control.update(verdict="inconclusive", reason="Native adapter reported a posting error")
            finally:
                try:
                    close(reference)
                    control["cleanupVerified"] = True
                finally:
                    report["controls"].append(control)
                    save()
            if control["verdict"] != "bypass":
                row = {"route": route, "repetition": repetition, "skipped": True,
                       "verdict": "inconclusive", "reason": "Fresh matched reference did not complete"}
            else:
                active(session)
                initialization = probe(["ax-direct", session["pid"]], output / f"candidate-{route}-{repetition}.activation.json")
                if initialization.get("status") != "observed":
                    report["stoppedEarly"] = True
                    report["stopReason"] = "Candidate foreground activation was not verified; no input sent"
                    save()
                    return report
                row = attack(session, route, output / f"candidate-{route}-{repetition}", oracle, control)
                row["foregroundInitializationStatus"] = initialization["status"]
                row["repetition"] = repetition
                if input_error(row) and row["verdict"] != "bypass":
                    row.update(verdict="inconclusive", reason="Native adapter reported a posting error")
            report["results"].append(row)
            save()
            print(json.dumps({key: row.get(key) for key in ["route", "repetition", "verdict", "skipped", "acceptedEvents", "refusedEvents"]}), flush=True)
            if row["verdict"] == "bypass" or row.get("acceptedEvents", 0):
                report["stoppedEarly"] = True
                report["stopReason"] = "Candidate accepted input or completed an action; isolate before further trials"
                save()
                return report
            if row.get("error") == "No owned normal research window":
                report.update(stoppedEarly=True, stopReason="Candidate window geometry unavailable; no further trials")
                save()
                return report
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--routes", nargs="+", choices=ROUTES, default=ROUTES)
    parser.add_argument("--repetitions", type=int, choices=range(1, 4), default=3)
    args = parser.parse_args()
    run(args.session.resolve(), args.output, args.routes, args.repetitions)
