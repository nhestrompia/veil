"""Calibrate installed content restrictions without external input or user data."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from process_cleanup import matching_pids, stop_launched
from run_native import ROOT

APP = ROOT / "dist/ContentPolicyControl.app"
BINARY = APP / "Contents/MacOS/ContentPolicyControl"


def interfaces_restricted(row):
    control = row.get("controlPage", {}).get("interfaces", {})
    candidate = row.get("restrictedPage", {}).get("interfaces", {})
    return (row.get("status") == "observed" and row.get("policyAccepted") is True
            and row.get("effectiveConfigurationRestricted") is True and row.get("unknownFeatureRefused") is True
            and control.get("secure") is True and candidate.get("secure") is True
            and all(control.get(key) == value for key, value in {"share": "function", "clipboard": "object", "publicKey": "function"}.items())
            and all(candidate.get(key) == "undefined" for key in ["share", "clipboard", "publicKey"]))


def export_restricted(row):
    control = row.get("controlPage", {})
    candidate = row.get("restrictedPage", {})
    return (control.get("namedPasteboardMarkerRecovered") is True
            and candidate.get("selectionHasMarker") is True and candidate.get("selectionWriteAccepted") is False
            and candidate.get("namedPasteboardUnchanged") is True)


def run(output, repetitions):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    digest = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    report = {"binarySHA256": digest, "externalAttack": False, "humanBaseline": False,
              "scope": "Installed API exposure and private named-pasteboard diagnostic. No general clipboard or user content.", "runs": []}
    for repetition in range(repetitions):
        if hashlib.sha256(BINARY.read_bytes()).hexdigest() != digest:
            raise RuntimeError("The content diagnostic changed during calibration")
        path = output / f"{repetition}.json"
        existing = matching_pids(BINARY)
        if existing:
            raise RuntimeError("A content diagnostic already exists")
        launcher = subprocess.Popen(["open", "-g", "-n", "-W", str(APP), "--args", "--page-check", "--out", str(path)])
        launcher.research_existing_pids = existing
        row = {}
        try:
            launcher.wait(timeout=25)
            row = json.loads(path.read_text())
        finally:
            row["cleanupVerified"] = stop_launched(launcher, BINARY)
            if launcher.poll() is None:
                launcher.terminate()
                launcher.wait(timeout=3)
            row["interfaceRestrictionObserved"] = interfaces_restricted(row)
            row["exportOutcome"] = "restricted" if export_restricted(row) else "inconclusive"
            report["runs"].append(row)
            (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
            if not row["cleanupVerified"]:
                raise RuntimeError("Content diagnostic cleanup failed")
        print(json.dumps({"repetition": repetition, "interfacesRestricted": row["interfaceRestrictionObserved"],
                          "exportOutcome": row["exportOutcome"]}), flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, choices=range(1, 4), default=3)
    args = parser.parse_args()
    run(args.output, args.repetitions)
