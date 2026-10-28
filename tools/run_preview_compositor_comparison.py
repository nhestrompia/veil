"""Measure unfiltered compositor streams with owned opaque coverage."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from process_cleanup import matching_pids, stop_launched
from run_device_session import active
from run_loaded_page_attacks import close, prepare
from run_native import ROOT, Oracle, probe
from run_pixel_agent_audit import marker_recovery
from run_preview_renderer_reads import validate_physical

MANIFEST = ROOT / "docs/evidence/preview-compositor-permission-manifest.json"


def verified_manifest():
    manifest = json.loads(MANIFEST.read_text())
    binary = Path(manifest["path"]) / "Contents/MacOS/PreviewCompositorProbe"
    if hashlib.sha256(binary.read_bytes()).hexdigest() != manifest["executableSHA256"]:
        raise RuntimeError("The pinned compositor helper changed")
    for name, digest in manifest["sourceHashes"].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise RuntimeError("A pinned compositor source changed")
    subprocess.run(["codesign", "--verify", "--strict", manifest["path"]], check=True, capture_output=True, timeout=10)
    return manifest, binary


def invoke(arguments, output):
    manifest, binary = verified_manifest()
    if arguments != ["permissions"]:
        if len(arguments) != 3 or arguments[0] not in ["coverage", "sequence"]:
            raise ValueError("Use scoped coverage or a compositor sequence")
        if arguments[0] == "sequence" and not manifest.get("permissionApproved"):
            raise RuntimeError("This helper's Screen Recording request needs approval")
    output = output.resolve()
    if not output.is_relative_to((ROOT / "artifacts").resolve()) or output.suffix != ".json":
        raise ValueError("Use a report within project artifacts")
    if matching_pids(binary) or output.exists():
        raise RuntimeError("Use a fresh helper and report")
    launcher = subprocess.Popen(["open", "-g", "-n", "-W", manifest["path"],
                                 "--stdout", str(output.with_suffix(".stdout")),
                                 "--stderr", str(output.with_suffix(".stderr")),
                                 "--args", *map(str, arguments), "--out", str(output)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    launcher.research_existing_pids = set()
    result = {}
    try:
        launcher.wait(timeout=30)
        result = json.loads(output.read_text())
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        result = {"status": "inconclusive", "error": str(error)}
    finally:
        cleaned = stop_launched(launcher, binary)
        if launcher.poll() is None:
            launcher.terminate()
            try:
                launcher.wait(timeout=3)
            except subprocess.TimeoutExpired:
                launcher.kill()
                launcher.wait()
        result["cleanupVerified"] = cleaned
        result["probeSHA256"] = manifest["executableSHA256"]
        output.write_text(json.dumps(result, indent=2) + "\n")
        if not cleaned:
            raise RuntimeError("Compositor helper cleanup failed")
    return result


def fully_audited(row):
    stages = row.get("stages", [])
    return (row.get("status") == "audited" and row.get("streamStopped") is True
            and row.get("cleanupVerified") is True and row.get("backdropClosed") is True
            and row.get("completeFrames", 0) > 0
            and row.get("auditedFrames") == row["completeFrames"]
            and 0 <= row.get("nonuniformFrames", -1) <= row["completeFrames"]
            and len(stages) == 3
            and [stage.get("filter") for stage in stages] == ["unfiltered-display", "owned-apps", "unfiltered-display"]
            and all(stage.get("completeFrames", 0) > 0
                    and stage.get("auditedFrames") == stage["completeFrames"]
                    and stage.get("elapsedSeconds", 0) >= 3 for stage in stages))


def score(before, candidate, after):
    if not all(fully_audited(row) for row in [before, candidate, after]):
        return "inconclusive"
    if not all(all(row.get("stageMarkers", [])) and len(row.get("stageMarkers", [])) == 3 for row in [before, after]):
        return "inconclusive"
    if candidate.get("markerRecovered"):
        return "marker-recovered"
    if candidate["nonuniformFrames"] == 0:
        return "all-delivered-complete-frames-spatially-uniform"
    return "nonuniform-output-marker-not-recovered"


def capture(session, prefix, oracle, command="sequence"):
    activation = probe(["ax-direct", session["pid"]], prefix.with_suffix(".activation.json"), background=True)
    if activation.get("status") != "observed":
        return {"status": "inconclusive", "reason": "Research foreground state unavailable"}
    windows = probe(["windows", session["pid"]], prefix.with_suffix(".windows.json"), background=True)
    owned = [row for row in windows.get("windows", [])
             if row.get("kCGWindowOwnerPID") == session["pid"] and row.get("kCGWindowLayer") == 0
             and row.get("kCGWindowAlpha") == 1
             and 600 <= row.get("kCGWindowBounds", {}).get("Width", 0) <= 4096
             and 400 <= row.get("kCGWindowBounds", {}).get("Height", 0) <= 4096]
    if len(owned) != 1:
        return {"status": "inconclusive", "reason": "Need exactly one ordinary research window"}
    result = invoke([command, session["pid"], owned[0]["kCGWindowNumber"]], prefix.with_suffix(".json"))
    if command == "coverage":
        return result
    result.update(markerRecovered=False, markerChecks=[], stageMarkers=[False] * 3)
    if not fully_audited(result):
        return result
    marker = oracle.state(session["trial"])["secret"]
    paths = result.get("images", []) + ([result["firstNonuniformImage"]] if result.get("firstNonuniformImage") else [])
    for index, raw in enumerate(paths):
        path = Path(raw).resolve()
        if not path.is_relative_to(prefix.parent.resolve()) or not path.is_file():
            raise RuntimeError("Compositor image is outside this trial")
        if result["nonuniformFrames"] == 0:
            continue
        ocr = probe(["ocr", path], prefix.with_suffix(f".ocr-{index}.json"), background=True)
        recovery = marker_recovery(ocr, marker)
        recovered = any(recovery.values())
        result["markerChecks"].append({"image": str(path), "markerRecovery": recovery})
        result["markerRecovered"] |= recovered
        for stage in range(3):
            if f".stage-{stage}-sample-" in path.name:
                result["stageMarkers"][stage] |= recovered
    return result


def run(session_path, physical_path, output):
    session = json.loads(session_path.read_text())
    validate_physical(session, json.loads(physical_path.read_text()))
    active(session)
    oracle = Oracle(session["controller"])
    baseline = oracle.state(session["trial"])
    if not any(row["accepted"] for row in baseline["submissions"]) or "DEVICE_KEYBOARD bound=true" not in Path(session["log"]).read_text():
        raise RuntimeError("Need the unchanged completed physical session")
    if matching_pids(ROOT / "dist/InspectableControl.app/Contents/MacOS/InspectableControl"):
        raise RuntimeError("A readable reference already exists")
    output = output.resolve()
    if not output.is_relative_to((ROOT / "artifacts").resolve()):
        raise ValueError("Use a fresh project artifact directory")
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    report = {"previewPID": session["pid"], "previewSHA256": session["binarySHA256"],
              "inputPosted": False, "physicalInputAbsenceVerified": False, "verdict": "inconclusive"}

    def save():
        report["newSubmissions"] = oracle.state(session["trial"])["submissions"][len(baseline["submissions"]):]
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    def reference(label):
        control = prepare("InspectableControl", output / label, oracle)
        result = {}
        try:
            result = capture(control, output / label, oracle)
            return result
        finally:
            close(control)
            result["referenceCleanupVerified"] = True

    report["permissions"] = invoke(["permissions"], output / "permissions.json")
    if not report["permissions"].get("screenRecordingGranted"):
        report["stopReason"] = "Screen Recording is ineffective; no capture or reference ran"
        save()
        return report
    report["before"] = reference("before")
    save()
    if not fully_audited(report["before"]) or report["before"].get("stageMarkers") != [True] * 3:
        report["stopReason"] = "Readable reference failed; no candidate capture ran"
        save()
        return report
    active(session)
    report["candidate"] = capture(session, output / "candidate", oracle)
    save()
    if not fully_audited(report["candidate"]):
        report["stopReason"] = "Candidate stream incomplete; no blocking result"
        save()
        return report
    active(session)
    report["after"] = reference("after")
    active(session)
    report["verdict"] = score(report["before"], report["candidate"], report["after"])
    save()
    probe(["ax-direct", session["pid"]], output / "restore-preview.json", background=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--physical-control", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.session, args.physical_control, args.output)
    print(json.dumps({key: result.get(key) for key in ["verdict", "stopReason", "newSubmissions"]}))
