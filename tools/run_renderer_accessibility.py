"""Calibrate direct renderer AX actions before querying a physical browser session."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

from native_environment import require_input_safety
from process_cleanup import matching_pids, stop_launched
from run_device_session import active
from run_loaded_page_attacks import close, prepare
from run_native import ROOT, Oracle, probe

APP = ROOT / "dist/RendererAXProbe.app"
BINARY = APP / "Contents/MacOS/RendererAXProbe"


def renderer_probe(arguments, output, expected_hash):
    if hashlib.sha256(BINARY.read_bytes()).hexdigest() != expected_hash:
        raise RuntimeError("Renderer probe changed during calibration")
    existing = matching_pids(BINARY)
    launcher = subprocess.Popen(["open", "-g", "-n", "-W", str(APP), "--stdout", str(output),
                                 "--stderr", str(output.with_suffix(".stderr")), "--args", *map(str, arguments)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    launcher.research_existing_pids = existing
    result = {}
    try:
        try:
            launcher.wait(timeout=30)
        except subprocess.TimeoutExpired:
            result = {"status": "inconclusive", "error": "Renderer probe timed out"}
        if not result:
            result = json.loads(output.read_text())
    finally:
        cleaned = stop_launched(launcher, BINARY)
        if launcher.poll() is None:
            launcher.terminate()
            try:
                launcher.wait(timeout=3)
            except subprocess.TimeoutExpired:
                launcher.kill()
                launcher.wait()
        result["cleanupVerified"] = cleaned
        output.write_text(json.dumps(result, indent=2) + "\n")
        if not cleaned:
            raise RuntimeError("Renderer probe cleanup failed. Stop desktop tests.")
    return result


def reference_worked(row):
    observation = row.get("observation", {})
    return (observation.get("status") == "observed" and observation.get("accessibilityQueried") is True
            and observation.get("cleanupVerified") is True and row.get("markerRecovered") is True
            and row.get("acceptedActions") == 1
            and any(query.get("actionAttempted") is True and query.get("fixtureURLVerified") is True
                    and query.get("setValueError") == 0 and query.get("pressError") == 0
                    for query in observation.get("queries", [])))


def attempt(session, output, oracle, probe_hash):
    before = oracle.state(session["trial"])
    initialization = probe(["ax-direct", session["pid"]], output.with_suffix(".host-init.json"))
    observation = renderer_probe(["action", session["pid"], session["trial"]["url"]], output, probe_hash)
    time.sleep(0.3)
    after = oracle.state(session["trial"])
    markers = [marker for query in observation.get("queries", []) for marker in query.get("researchMarkers", [])]
    new = after["submissions"][len(before["submissions"]):]
    return {"pid": session["pid"], "hostInitializationStatus": initialization.get("status"),
            "observation": observation, "markerRecovered": before["secret"] in markers,
            "acceptedActions": sum(bool(item["accepted"]) for item in new), "newSubmissions": new}


def run(session_path, output, repetitions):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    session = json.loads(session_path.read_text())
    active(session)
    oracle = Oracle()
    if not any(item["accepted"] for item in oracle.state(session["trial"])["submissions"]) or "DEVICE_KEYBOARD bound=true" not in Path(session["log"]).read_text():
        raise RuntimeError("The unchanged candidate needs its completed physical baseline and device binding")
    if matching_pids(ROOT / "dist/InspectableControl.app/Contents/MacOS/InspectableControl"):
        raise RuntimeError("A readable reference already exists. Refusing duplicate research controls.")
    require_input_safety(probe(["permissions"], output / "native-permissions.json"))
    probe_hash = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    report = {"candidatePID": session["pid"], "candidateBinarySHA256": session["binarySHA256"],
              "rendererProbeSHA256": probe_hash, "controls": [], "results": [],
              "route": "Direct renderer AX root, exact ownership, fixed loopback fixture actions. No input tap."}

    def save():
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    report["permissions"] = renderer_probe(["permissions"], output / "permissions.json", probe_hash)
    if report["permissions"].get("accessibility") is not True:
        report["status"] = "inconclusive"
        report["reason"] = "Renderer probe needs its own approved Accessibility grant. No reference or AX attack launched."
        save()
        return report
    for repetition in range(repetitions):
        reference = prepare("InspectableControl", output / f"reference-{repetition}", oracle)
        row = {"repetition": repetition}
        try:
            row.update(attempt(reference, output / f"reference-{repetition}.json", oracle, probe_hash))
            row["controlWorked"] = reference_worked(row)
        finally:
            try:
                close(reference)
                row["referenceCleanupVerified"] = True
            finally:
                report["controls"].append(row)
                save()
        active(session)
        if not row["controlWorked"]:
            report["results"].append({"repetition": repetition, "skipped": True,
                                      "reason": "Direct renderer AX reference did not recover a marker and complete its action"})
            save()
            break
        candidate = attempt(session, output / f"candidate-{repetition}.json", oracle, probe_hash)
        candidate["repetition"] = repetition
        candidate["outcome"] = "autonomous-action" if candidate["acceptedActions"] else "no-action-observed"
        report["results"].append(candidate)
        save()
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, choices=range(1, 4), default=3)
    args = parser.parse_args()
    print(json.dumps(run(args.session.resolve(), args.output, args.repetitions), indent=2))
