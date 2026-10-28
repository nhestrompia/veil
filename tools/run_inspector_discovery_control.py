"""Calibrate private Cocoa inspector discovery on one disposable readable control."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import threading

from fixture import FixtureServer
from process_cleanup import matching_pids
from run_loaded_page_attacks import close, prepare
from run_native import ROOT, Oracle


def run(output):
    output = output.resolve()
    if not output.is_relative_to((ROOT / "artifacts").resolve()):
        raise ValueError("Use a fresh project artifact directory")
    if matching_pids(ROOT / "dist/InspectableControl.app/Contents/MacOS/InspectableControl"):
        raise RuntimeError("A readable reference already exists")
    binary = ROOT / ".build/inspector-discovery-control"
    if not binary.is_file():
        raise RuntimeError("Build the inspector discovery control first")
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    report = {"status": "inconclusive", "candidateLaunched": False, "inputPosted": False,
              "helperSHA256": hashlib.sha256(binary.read_bytes()).hexdigest()}
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
        completed = subprocess.run([str(binary), str(reference["pid"]), reference["trial"]["url"]],
                                   capture_output=True, text=True, timeout=18)
        report["helperStderrCharacters"] = len(completed.stderr)
        report["helperExitCode"] = completed.returncode
        if completed.returncode == 0:
            report["discovery"] = json.loads(completed.stdout)
            if report["discovery"].get("status") == "reference-discovered":
                report["status"] = "reference-discovered"
        report["submissions"] = oracle.state(reference["trial"])["submissions"]
        if report["submissions"]:
            raise RuntimeError("Discovery unexpectedly submitted a task")
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
            (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    if not report["fixtureStopped"]:
        raise RuntimeError("The local fixture did not stop")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    report = run(parser.parse_args().output)
    print(json.dumps(report))
    raise SystemExit(0 if report["status"] == "reference-discovered" else 1)
