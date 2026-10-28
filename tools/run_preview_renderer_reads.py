"""Compare scoped renderer reads without sending input or AX actions."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

from process_cleanup import matching_pids, stop_launched
from run_device_session import active
from run_loaded_page_attacks import close, prepare
from run_native import ROOT, Oracle, probe

APP = ROOT / "dist/PreviewRendererReadProbe.app"
BINARY = APP / "Contents/MacOS/PreviewRendererReadProbe"
MANIFEST = ROOT / "docs/evidence/preview-renderer-read-permission-manifest.json"


def validate_physical(session, physical):
    if (physical.get("operatorDeclaresPhysicalCompletion") is not True
            or physical.get("pid") != session["pid"]
            or physical.get("binarySHA256") != session["binarySHA256"]
            or physical.get("deviceBound") is not True
            or physical.get("acceptedSubmissions", 0) < 1):
        raise RuntimeError("Need the physical declaration for this exact browser session")


def observe(command, output, digest):
    if hashlib.sha256(BINARY.read_bytes()).hexdigest() != digest:
        raise RuntimeError("The reviewed renderer helper changed")
    if matching_pids(BINARY):
        raise RuntimeError("A renderer read helper already exists")
    if output.exists():
        raise RuntimeError("Use a new observation file")
    launcher = subprocess.Popen(["open", "-g", "-n", "-W", str(APP),
                                 "--stdout", str(output.with_suffix(".stdout")),
                                 "--stderr", str(output.with_suffix(".stderr")),
                                 "--args", *map(str, command), "--out", str(output)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    launcher.research_existing_pids = set()
    result = {}
    try:
        launcher.wait(timeout=25)
        result = json.loads(output.read_text())
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        result = {"status": "inconclusive", "error": str(error)}
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
        result["probeSHA256"] = digest
        output.write_text(json.dumps(result, indent=2) + "\n")
        if not cleaned:
            raise RuntimeError("Renderer helper cleanup failed")
    return result


def read_worked(observation, marker):
    return (observation.get("status") == "observed"
            and observation.get("accessibilityQueried") is True
            and observation.get("cleanupVerified") is True
            and any(query.get("kind") == "renderer" and marker in query.get("researchMarkers", [])
                    for query in observation.get("queries", [])))


def run(session_path, physical_path, output, discovery_only=False):
    if os.getuid() == 0:
        raise RuntimeError("Run as the ordinary user")
    session = json.loads(session_path.read_text())
    validate_physical(session, json.loads(physical_path.read_text()))
    active(session)
    manifest = json.loads(MANIFEST.read_text())
    digest = manifest["executableSHA256"]
    for name, expected in manifest["sourceHashes"].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError("A reviewed helper source changed")
    subprocess.run(["codesign", "--verify", "--strict", str(APP)], check=True, capture_output=True)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    oracle = Oracle(session["controller"])
    baseline = oracle.state(session["trial"])
    if not any(item["accepted"] for item in baseline["submissions"]) or "DEVICE_KEYBOARD bound=true" not in Path(session["log"]).read_text():
        raise RuntimeError("Physical session no longer has its baseline")
    report = {"previewPID": session["pid"], "previewSHA256": session["binarySHA256"],
              "discoveryOnly": discovery_only, "actionsSent": False, "inputPosted": False,
              "physicalInputAbsenceVerified": False, "bootstrapAttested": False,
              "references": [], "results": []}

    def save():
        report["newSubmissions"] = oracle.state(session["trial"])["submissions"][len(baseline["submissions"]):]
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    report["permissions"] = observe(["permissions"], output / "permissions.json", digest)
    report["ownership"] = observe(["discover", session["pid"]], output / "preview-discovery.json", digest)
    report["unrelatedTarget"] = observe(["discover", os.getpid()], output / "unrelated-target.json", digest)
    save()
    if report["ownership"].get("status") != "discovered" or not report["ownership"].get("rendererPIDs"):
        report["stopReason"] = "Preview renderer ownership is unavailable"
        save()
        return report
    if not discovery_only and report["permissions"].get("accessibility") is not True:
        report["stopReason"] = "New helper needs its separately approved Accessibility grant. No AX reads ran."
        save()
        return report
    if not discovery_only and manifest.get("permissionApproved") is not True:
        report["stopReason"] = "This helper's Accessibility use needs approval. No AX reads ran."
        save()
        return report
    if matching_pids(ROOT / "dist/InspectableControl.app/Contents/MacOS/InspectableControl"):
        raise RuntimeError("A readable reference already exists")
    for mode in (["discover"] if discovery_only else ["read", "read-token"]):
        reference = prepare("InspectableControl", output / f"reference-{mode}", oracle)
        control = {}
        try:
            if mode != "discover":
                activation = probe(["ax-direct", reference["pid"]], output / f"reference-{mode}-activation.json")
                if activation.get("status") != "observed":
                    raise RuntimeError("Reference foreground state is unavailable")
            control = observe([mode, reference["pid"]], output / f"reference-{mode}.json", digest)
            control["markerRecoveredFromRenderer"] = read_worked(control, oracle.state(reference["trial"])["secret"])
        finally:
            try:
                close(reference)
                control["referenceCleanupVerified"] = True
            finally:
                report["references"].append(control)
                save()
        active(session)
        if mode == "discover":
            break
        if not control.get("markerRecoveredFromRenderer"):
            report["stopReason"] = "Fresh renderer read reference did not recover its marker; candidate skipped"
            save()
            return report
        activation = probe(["ax-direct", session["pid"]], output / f"preview-{mode}-activation.json")
        if activation.get("status") != "observed":
            report["stopReason"] = "Preview foreground state is unavailable; no renderer query ran"
            save()
            return report
        result = observe([mode, session["pid"]], output / f"preview-{mode}.json", digest)
        result["markerRecoveredFromRenderer"] = read_worked(result, baseline["secret"])
        report["results"].append(result)
        save()
        if (result["markerRecoveredFromRenderer"] or result.get("status") != "observed"
                or any(query.get("traversalIncomplete") for query in result.get("queries", []))):
            report["stopReason"] = "Renderer marker recovered or query incomplete; stop before the next mode"
            save()
            return report
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--physical-control", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--discovery-only", action="store_true")
    args = parser.parse_args()
    result = run(args.session, args.physical_control, args.output, args.discovery_only)
    print(json.dumps({key: result.get(key) for key in ["stopReason", "newSubmissions", "discoveryOnly"]}))
