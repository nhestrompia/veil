"""Compare scoped continuous capture on one physical browser session."""

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

MANIFEST = ROOT / "docs/evidence/preview-stream-permission-manifest.json"


def verified_manifest():
    manifest = json.loads(MANIFEST.read_text())
    binary = Path(manifest["path"]) / "Contents/MacOS/PreviewStreamCaptureProbe"
    if hashlib.sha256(binary.read_bytes()).hexdigest() != manifest["executableSHA256"]:
        raise RuntimeError("The pinned stream helper changed")
    for name, digest in manifest["sourceHashes"].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise RuntimeError("A pinned stream helper source changed")
    subprocess.run(["codesign", "--verify", "--strict", manifest["path"]], check=True, capture_output=True, timeout=10)
    return manifest, binary


def invoke(arguments, output):
    manifest, binary = verified_manifest()
    if arguments != ["permissions"]:
        if not manifest.get("permissionApproved"):
            raise RuntimeError("This helper's Screen Recording request needs approval")
        if len(arguments) != 3 or arguments[0] not in ["window", "display"]:
            raise ValueError("Use an owned-window or app-filtered display stream")
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
        launcher.wait(timeout=50)
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
            raise RuntimeError("Stream helper cleanup failed; stop tests")
    return result


def fully_audited(row):
    return (row.get("status") == "audited" and row.get("streamStopped") is True
            and row.get("cleanupVerified") is True and row.get("completeFrames", 0) > 0
            and row.get("durationSeconds") == 30 and row.get("elapsedSeconds", 0) >= 30
            and row.get("auditedFrames") == row["completeFrames"]
            and 0 <= row.get("nonBlackFrames", -1) <= row["completeFrames"])


def score(before, candidate, after):
    if not all(fully_audited(row) for row in [before, candidate, after]):
        return "inconclusive"
    if not before.get("markerRecovered") or not after.get("markerRecovered"):
        return "inconclusive"
    if candidate.get("markerRecovered"):
        return "marker-recovered"
    if candidate["nonBlackFrames"] == 0:
        return "all-delivered-complete-frames-black"
    return "nonblack-output-marker-not-recovered"


def capture(session, mode, prefix, oracle):
    activation = probe(["ax-direct", session["pid"]], prefix.with_suffix(".activation.json"))
    if activation.get("status") != "observed":
        return {"status": "inconclusive", "reason": "Target foreground state unavailable; no stream ran"}
    windows = probe(["windows", session["pid"]], prefix.with_suffix(".windows.json"))
    owned = [row for row in windows.get("windows", [])
             if row.get("kCGWindowOwnerPID") == session["pid"] and row.get("kCGWindowLayer") == 0]
    if len(owned) != 1:
        return {"status": "inconclusive", "reason": "Need exactly one owned ordinary window"}
    result = invoke([mode, session["pid"], owned[0]["kCGWindowNumber"]], prefix.with_suffix(".json"))
    result["markerRecovered"] = False
    result["markerChecks"] = []
    if not fully_audited(result):
        return result
    marker = oracle.state(session["trial"])["secret"]
    paths = result.get("images", []) + ([result["firstColoredImage"]] if result.get("firstColoredImage") else [])
    for index, raw in enumerate(paths):
        path = Path(raw).resolve()
        if not path.is_relative_to(prefix.parent.resolve()) or not path.is_file():
            raise RuntimeError("Stream image is outside this trial")
        if result["nonBlackFrames"] == 0:
            continue
        ocr = probe(["ocr", path], prefix.with_suffix(f".ocr-{index}.json"), background=True)
        recovery = marker_recovery(ocr, marker)
        result["markerChecks"].append({"image": str(path), "markerRecovery": recovery})
        if any(recovery.values()):
            result["markerRecovered"] = True
            break
    return result


def run(session_path, physical_path, output, mode):
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
    report = {"mode": mode, "previewPID": session["pid"], "previewSHA256": session["binarySHA256"],
              "inputPosted": False, "physicalInputAbsenceVerified": False, "verdict": "inconclusive"}

    def save():
        report["newSubmissions"] = oracle.state(session["trial"])["submissions"][len(baseline["submissions"]):]
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    def reference(label):
        control = prepare("InspectableControl", output / label, oracle)
        result = {}
        try:
            result = capture(control, mode, output / label, oracle)
            return result
        finally:
            close(control)
            result["referenceCleanupVerified"] = True

    report["permissions"] = invoke(["permissions"], output / "permissions.json")
    if not report["permissions"].get("screenRecordingGranted"):
        report["stopReason"] = "Screen Recording is ineffective; no stream or reference ran"
        save()
        return report
    report["before"] = reference("before")
    save()
    if not fully_audited(report["before"]) or not report["before"].get("markerRecovered"):
        report["stopReason"] = "Readable reference failed; no candidate stream ran"
        save()
        return report
    active(session)
    report["candidate"] = capture(session, mode, output / "candidate", oracle)
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
    probe(["ax-direct", session["pid"]], output / "restore-preview.json")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--physical-control", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=["window", "display"], default="window")
    args = parser.parse_args()
    result = run(args.session, args.physical_control, args.output, args.mode)
    print(json.dumps({key: result.get(key) for key in ["verdict", "stopReason", "newSubmissions"]}))
