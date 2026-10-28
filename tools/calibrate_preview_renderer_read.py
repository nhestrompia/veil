"""Calibrate one read-only route on a disposable reference, without a candidate."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import threading

from fixture import FixtureServer
from process_cleanup import matching_pids
from run_loaded_page_attacks import close, prepare
from run_native import ROOT, Oracle, probe
from run_preview_renderer_reads import APP, BINARY, MANIFEST, observe, read_worked


def verified_helper():
    if os.getuid() == 0:
        raise RuntimeError("Run as the ordinary user")
    manifest = json.loads(MANIFEST.read_text())
    if manifest.get("permissionApproved") is not True:
        raise RuntimeError("The helper's Accessibility use needs approval")
    digest = manifest["executableSHA256"]
    if hashlib.sha256(BINARY.read_bytes()).hexdigest() != digest:
        raise RuntimeError("The pinned helper changed")
    for name, expected in manifest["sourceHashes"].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError("A reviewed helper source changed")
    subprocess.run(["codesign", "--verify", "--strict", str(APP)], check=True, capture_output=True)
    return digest


def run(output, mode):
    if mode not in ["read", "read-token"]:
        raise RuntimeError("Use one read-only mode")
    digest = verified_helper()
    if matching_pids(ROOT / "dist/InspectableControl.app/Contents/MacOS/InspectableControl"):
        raise RuntimeError("A reference already exists")
    output = output.resolve()
    if not output.is_relative_to((ROOT / "artifacts").resolve()):
        raise ValueError("Use a fresh project artifact directory")
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    report = {"mode": mode, "scope": "Fresh readable reference only; no protected browser",
              "candidateQueried": False, "inputPosted": False, "actionsSent": False,
              "referenceWorked": False, "helperSHA256": digest}

    def save():
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    report["permissions"] = observe(["permissions"], output / "permissions.json", digest)
    if report["permissions"].get("accessibility") is not True:
        report["stopReason"] = "Accessibility is ineffective; no reference or AX read ran"
        save()
        return report
    server = FixtureServer(("127.0.0.1", 0))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    controller = output / "fixture-controller.json"
    controller.write_text(json.dumps({"port": server.server_port, "key": server.controller_key}))
    controller.chmod(0o600)
    oracle = Oracle(controller)
    reference = None
    try:
        reference = prepare("InspectableControl", output / "reference", oracle)
        activation = probe(["ax-direct", reference["pid"]], output / "activation.json")
        report["foregroundStatus"] = activation.get("status")
        if activation.get("status") != "observed":
            report["stopReason"] = "Reference foreground state unavailable; no renderer read ran"
            return report
        report["observation"] = observe([mode, reference["pid"]], output / "renderer.json", digest)
        state = oracle.state(reference["trial"])
        report["referenceWorked"] = read_worked(report["observation"], state["secret"])
        report["submissions"] = state["submissions"]
        return report
    finally:
        try:
            if reference is not None:
                close(reference)
                report["referenceCleanupVerified"] = True
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=3)
            report["fixtureStopped"] = not worker.is_alive()
            save()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=["read", "read-token"], default="read-token")
    args = parser.parse_args()
    result = run(args.output, args.mode)
    print(json.dumps({key: result.get(key) for key in ["referenceWorked", "stopReason", "candidateQueried", "referenceCleanupVerified", "fixtureStopped"]}))
