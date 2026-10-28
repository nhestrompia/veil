"""Calibrate the frozen compositor probe without a physical-browser session."""

import argparse
import json
from pathlib import Path
import threading
import time

from fixture import FixtureServer
from process_cleanup import matching_pids
from run_loaded_page_attacks import close, prepare
from run_native import ROOT, Oracle
from run_preview_compositor_comparison import capture, fully_audited, invoke


def await_setup(output, reference, seconds=60):
    (output / "ready.json").write_text(json.dumps({"pid": reference["pid"], "target": "InspectableControl",
                                                 "maximumWaitSeconds": seconds}) + "\n")
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if (output / "stop").exists():
            return False
        if (output / "setup-complete").exists():
            return True
        time.sleep(0.1)
    return False


def calibrate(output, coverage_only=False, wait_for_setup=False):
    output = output.resolve()
    if not output.is_relative_to((ROOT / "artifacts").resolve()):
        raise ValueError("Use a fresh project artifact directory")
    if matching_pids(ROOT / "dist/InspectableControl.app/Contents/MacOS/InspectableControl"):
        raise RuntimeError("A readable reference already exists")
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    report = {"status": "inconclusive", "inputPosted": False, "candidateLaunched": False,
              "coverageOnly": coverage_only, "waitForSetup": wait_for_setup}

    def save():
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    report["permissions"] = invoke(["permissions"], output / "permissions.json")
    if not coverage_only and not report["permissions"].get("screenRecordingGranted"):
        report["reason"] = "The approved grant is ineffective; no reference ran"
        save()
        return report
    server = FixtureServer(("127.0.0.1", 0))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    reference = None
    try:
        worker.start()
        controller = output / "fixture-controller.json"
        controller.write_text(json.dumps({"port": server.server_port, "key": server.controller_key}))
        controller.chmod(0o600)
        oracle = Oracle(controller)
        reference = prepare("InspectableControl", output / "reference", oracle)
        report["referencePID"] = reference["pid"]
        if wait_for_setup and not await_setup(output, reference):
            report["reason"] = "Bounded setup did not complete; no capture ran"
        else:
            report["reference"] = capture(reference, output / "reference", oracle,
                                          "coverage" if coverage_only else "sequence")
            report["submissions"] = oracle.state(reference["trial"])["submissions"]
            row = report["reference"]
            if coverage_only:
                report["status"] = "coverage-verified" if row.get("status") == "coverage-verified" else "inconclusive"
            elif fully_audited(row) and row.get("stageMarkers") == [True] * 3:
                report["status"] = "calibrated"
            else:
                report["reason"] = "Readable control failed; no candidate ran"
    except Exception as error:
        report["error"] = str(error)
    finally:
        try:
            if reference is not None:
                close(reference)
                report["referenceCleanupVerified"] = True
        finally:
            if worker.is_alive():
                server.shutdown()
            server.server_close()
            if worker.ident is not None:
                worker.join(timeout=3)
            report["fixtureStopped"] = not worker.is_alive()
            save()
    if not report.get("fixtureStopped"):
        raise RuntimeError("The local fixture did not stop")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--coverage-only", action="store_true")
    parser.add_argument("--wait-for-setup", action="store_true")
    args = parser.parse_args()
    result = calibrate(args.output, args.coverage_only, args.wait_for_setup)
    print(json.dumps({key: result.get(key) for key in ["status", "reason", "error", "referenceCleanupVerified", "fixtureStopped"]}))
    raise SystemExit(0 if result["status"] in ["calibrated", "coverage-verified"] else 1)
