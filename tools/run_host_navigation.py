"""Test a scoped native Reload action with independent fixture lifecycle evidence."""

import argparse
import hashlib
import json
from pathlib import Path
import time

from native_environment import require_input_safety
from process_cleanup import matching_pids
from run_device_session import active
from run_loaded_page_attacks import close, prepare
from run_native import ROOT, Oracle, probe
from run_renderer_accessibility import BINARY, renderer_probe


def page_ready_count(state):
    return sum(item.get("type") == "page-ready" for item in state["events"])


def reload_worked(row):
    observation = row.get("observation", {})
    return (row.get("newPageReadyEvents") == 1 and row.get("newAcceptedFormActions") == 0
            and observation.get("status") == "observed" and observation.get("accessibilityQueried") is True
            and observation.get("cleanupVerified") is True
            and any(query.get("processKind") == "host" and query.get("navigationContextVerified") is True
                    and query.get("reloadActionAttempted") is True and query.get("reloadPressError") == 0
                    for query in row.get("observation", {}).get("queries", [])))


def attempt(session, prefix, oracle, probe_hash):
    before = oracle.state(session["trial"])
    observation = renderer_probe(["host-reload-token", session["pid"], session["trial"]["url"]], prefix, probe_hash)
    deadline = time.monotonic() + 3
    after = oracle.state(session["trial"])
    while page_ready_count(after) == page_ready_count(before) and time.monotonic() < deadline:
        time.sleep(0.1)
        after = oracle.state(session["trial"])
    new = after["submissions"][len(before["submissions"]):]
    return {"pid": session["pid"], "observation": observation,
            "newPageReadyEvents": page_ready_count(after) - page_ready_count(before),
            "newAcceptedFormActions": sum(bool(item["accepted"]) for item in new),
            "newSubmissions": new}


def run(session_path, output):
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
              "probeSHA256": probe_hash, "formTaskAttempted": False,
              "scope": "Native Reload on the exact research fixture. Page-ready events corroborate navigation, not form completion."}

    def save():
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    report["permissions"] = renderer_probe(["permissions"], output / "permissions.json", probe_hash)
    if report["permissions"].get("accessibility") is not True:
        report["status"] = "inconclusive"
        save()
        return report
    reference = prepare("InspectableControl", output / "reference", oracle)
    try:
        report["control"] = attempt(reference, output / "reference.json", oracle, probe_hash)
        report["control"]["controlWorked"] = reload_worked(report["control"])
    finally:
        try:
            close(reference)
            report["referenceCleanupVerified"] = True
        finally:
            save()
    if not report["control"]["controlWorked"]:
        report["candidate"] = {"skipped": True, "reason": "Matched Reload reference failed"}
    else:
        active(session)
        report["candidate"] = attempt(session, output / "candidate.json", oracle, probe_hash)
        report["candidate"]["reloadWorked"] = reload_worked(report["candidate"])
    save()
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.session.resolve(), args.output), indent=2))
