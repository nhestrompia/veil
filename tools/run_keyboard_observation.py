"""Calibrate a passive observer with generated fake keys in a readable research app."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

from native_environment import require_input_safety
from process_cleanup import matching_pids, stop_launched
from run_loaded_page_attacks import close, prepare
from run_native import ROOT, Oracle, probe

OBSERVER = ROOT / "dist/KeyboardObservationProbe.app"
BINARY = OBSERVER / "Contents/MacOS/KeyboardObservationProbe"


def worked(report):
    observation = report.get("observation", {})
    return (report.get("acceptedSubmissions") == 1 and observation.get("expectedFakePhraseMatched") is True
            and observation.get("eventCount", 0) > 0 and observation.get("monitorRemoved") is True
            and report.get("observerCleanupVerified") is True and report.get("referenceCleanupVerified") is True)


def run(output, mode):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    oracle = Oracle()
    permissions = probe(["permissions"], output / "permissions.json")
    require_input_safety(permissions)
    if not permissions.get("postEvents") or not permissions.get("accessibility"):
        raise RuntimeError("NativeProbe needs its existing input and Accessibility grants")
    reference = prepare("InspectableControl", output / "reference", oracle)
    observer = None
    report = {"physicalControl": False, "mode": mode, "referencePID": reference["pid"],
              "observerSHA256": hashlib.sha256(BINARY.read_bytes()).hexdigest()}
    try:
        tree = probe(["ax-direct", reference["pid"]], output / "reference.ax.json")
        field = next((item for item in tree.get("elements", []) if item.get("AXRole") == "AXTextField"
                      and "Enter native-input" in [item.get("AXDescription"), item.get("AXTitle")]), None)
        if field is None:
            raise RuntimeError("Readable reference field unavailable. No observer or input launched.")
        point = [field["position"][0] + field["size"][0] / 2, field["position"][1] + field["size"][1] / 2]
        existing = matching_pids(BINARY)
        observation_path = output / "observer.json"
        observer = subprocess.Popen(["open", "-g", "-n", "-W", str(OBSERVER), "--stdout", str(observation_path),
                                     "--stderr", str(output / "observer.stderr"), "--args",
                                     "observe-pid" if mode == "pid" else "observe", str(reference["pid"])],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        observer.research_existing_pids = existing
        time.sleep(1)
        if observation_path.exists() and observation_path.read_text().strip():
            report["skippedInput"] = True
        else:
            report["input"] = probe(["input", reference["pid"], *point, "hid", "curve"], output / "input.json")
        try:
            observer.wait(timeout=20)
        except subprocess.TimeoutExpired:
            report["observerTimeout"] = True
        if observation_path.exists() and observation_path.read_text().strip():
            report["observation"] = json.loads(observation_path.read_text())
        report["acceptedSubmissions"] = sum(bool(item["accepted"]) for item in oracle.state(reference["trial"])["submissions"])
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        report["error"] = str(error)
    finally:
        try:
            if observer is not None:
                report["observerCleanupVerified"] = stop_launched(observer, BINARY, None)
                observer.terminate()
                try:
                    observer.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    observer.kill()
                    observer.wait()
            close(reference)
            report["referenceCleanupVerified"] = True
        finally:
            report["generatedControlWorked"] = worked(report)
            (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    if not report.get("observerCleanupVerified", True) or not report.get("referenceCleanupVerified"):
        raise RuntimeError("Observation control cleanup failed. Stop desktop tests.")
    print(json.dumps(report, indent=2), flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=["appkit", "pid"], default="pid")
    args = parser.parse_args()
    run(args.output, args.mode)
