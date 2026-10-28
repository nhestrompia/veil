"""Read and operate native semantics in a physically calibrated browser session."""

import argparse
import hashlib
import json
from pathlib import Path

from native_environment import require_input_safety
from run_device_session import active
from run_loaded_page_attacks import close, prepare
from run_native import ROOT, Oracle, probe


def attempt(session, prefix, oracle):
    before = oracle.state(session["trial"])
    results = {}
    for command, arguments in [("tree", ["ax"]), ("direct", ["ax-direct"]),
                               ("menu", ["ax-menu", "inspect"]), ("action", ["ax-action"])]:
        args = [arguments[0], session["pid"], *arguments[1:]]
        results[command] = probe(args, prefix.with_suffix(f".{command}.json"))
    after = oracle.state(session["trial"])
    return {"pid": session["pid"], "queries": results,
            "markerRecovered": before["secret"] in json.dumps(results),
            "readDisclosure": {key: before["secret"] in json.dumps(results[key]) for key in ["tree", "direct"]},
            "newSubmissions": after["submissions"][len(before["submissions"]):]}


def reference_worked(row):
    queries = row["queries"]
    return (all(row["readDisclosure"].values()) and all(queries[k].get("status") == "observed" for k in ["tree", "direct", "menu"])
            and any(item["title"] == "Select All" for item in queries["menu"].get("items", []))
            and queries["action"].get("status") == "attempted"
            and any(item["accepted"] for item in row["newSubmissions"]))


def run(session_path, output, repetitions, confirmed):
    session = json.loads(session_path.read_text())
    active(session)
    oracle = Oracle()
    if not confirmed or not any(item["accepted"] for item in oracle.state(session["trial"])["submissions"]) or "DEVICE_KEYBOARD bound=true" not in Path(session["log"]).read_text():
        raise RuntimeError("Need physical completion and binding in this unchanged session")
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    permissions = probe(["permissions"], output / "permissions.json")
    require_input_safety(permissions)
    if not permissions.get("accessibility"):
        raise RuntimeError("The probe needs effective Accessibility access")
    binary = ROOT / "dist/NativeProbe.app/Contents/MacOS/NativeProbe"
    probe_hash = hashlib.sha256(binary.read_bytes()).hexdigest()
    report = {"controls": [], "results": [], "sessionPID": session["pid"],
              "binarySHA256": session["binarySHA256"], "probeBinarySHA256": probe_hash,
              "permissions": permissions, "operatorDeclaresPhysicalCompletion": True,
              "routeContract": "Exact research-PID AX tree, focused and hit-test queries, File/Edit menus, setValue and press. No clipboard or nonresearch content."}

    def save():
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    for repetition in range(repetitions):
        reference = prepare("InspectableControl", output / f"reference-{repetition}", oracle)
        row = {"repetition": repetition}
        try:
            row.update(attempt(reference, output / f"reference-{repetition}", oracle))
            row["controlWorked"] = reference_worked(row)
        finally:
            try:
                close(reference)
                row["cleanupVerified"] = True
            except RuntimeError:
                row["cleanupVerified"] = False
                raise
            finally:
                report["controls"].append(row)
                save()
        active(session)
        if hashlib.sha256(binary.read_bytes()).hexdigest() != probe_hash:
            raise RuntimeError("The probe changed after reference calibration")
        if not row["controlWorked"]:
            candidate = {"repetition": repetition, "skipped": True, "reason": "Matched semantic reference did not work"}
        else:
            candidate = attempt(session, output / f"candidate-{repetition}", oracle)
            candidate["repetition"] = repetition
            candidate["controlWorked"] = True
        report["results"].append(candidate)
        save()
        print(json.dumps({k: candidate.get(k) for k in ["repetition", "skipped", "markerRecovered", "newSubmissions"]}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--operator-physical-completion-confirmed", action="store_true")
    args = parser.parse_args()
    run(args.session.resolve(), args.output, args.repetitions, args.operator_physical_completion_confirmed)
