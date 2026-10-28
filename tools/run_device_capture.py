"""Compare scoped screenshot routes in an unchanged physically calibrated session."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from run_device_session import active
from run_loaded_page_attacks import close, prepare
from run_native import ROOT, Oracle, probe

ROUTES = ["capture", "display-capture", "system-capture"]


def capture(pid, trial, route, prefix, oracle):
    prefix = prefix.resolve()
    row = {"pid": pid, "route": route, "observation": "inconclusive"}
    try:
        row["capture"] = probe([route, pid, prefix.with_suffix(".png")], prefix.with_suffix(".capture.json"))
        if row["capture"].get("status") != "captured":
            raise RuntimeError("Capture did not produce a target image")
        row["imageSHA256"] = hashlib.sha256(prefix.with_suffix(".png").read_bytes()).hexdigest()
        ocr = probe(["ocr", prefix.with_suffix(".png")], prefix.with_suffix(".ocr.json"))
        if "text" not in ocr:
            raise RuntimeError("OCR did not return an observation")
        row["markerRecovered"] = oracle.state(trial)["secret"] in json.dumps(ocr)
        row["observation"] = "marker-recovered" if row["markerRecovered"] else "marker-not-recovered"
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        row["error"] = str(error)
    return row


def run(session_path, output, repetitions, confirmed, routes=ROUTES):
    session = json.loads(session_path.read_text())
    active(session)
    oracle = Oracle()
    before = oracle.state(session["trial"])
    if not confirmed or not any(item["accepted"] for item in before["submissions"]) or "DEVICE_KEYBOARD bound=true" not in Path(session["log"]).read_text():
        raise RuntimeError("Need physical completion and binding in the unchanged session")
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    permissions = probe(["permissions"], output / "permissions.json")
    if not permissions.get("screenCapture"):
        raise RuntimeError("The probe needs effective Screen Recording access")
    probe_binary = ROOT / "dist/NativeProbe.app/Contents/MacOS/NativeProbe"
    probe_hash = hashlib.sha256(probe_binary.read_bytes()).hexdigest()
    report = {"controls": [], "results": [], "permissions": permissions,
              "sessionPID": session["pid"], "binarySHA256": session["binarySHA256"],
              "probeBinarySHA256": probe_hash, "operatorDeclaresPhysicalCompletion": True,
              "routeContract": "Read-only target-window captures. Display filter includes only that window. No input, no unfiltered display capture."}

    def save():
        report["newSubmissions"] = oracle.state(session["trial"])["submissions"][len(before["submissions"]):]
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    for route in routes:
        for repetition in range(repetitions):
            prefix = output / f"{route}-{repetition}"
            control = {"route": route, "repetition": repetition, "observation": "inconclusive"}
            reference = None
            try:
                reference = prepare("InspectableControl", prefix.with_suffix(".reference"), oracle)
                control.update(capture(reference["pid"], reference["trial"], route,
                                       prefix.with_name(prefix.name + "-control"), oracle))
                control["binarySHA256"] = reference["binarySHA256"]
            except (OSError, RuntimeError, subprocess.SubprocessError) as error:
                control["error"] = str(error)
                if reference is None:
                    raise
            finally:
                if reference is not None:
                    try:
                        close(reference)
                        control["cleanupVerified"] = True
                    except RuntimeError:
                        control["cleanupVerified"] = False
                        report["controls"].append(control)
                        save()
                        raise
                report["controls"].append(control)
                save()
            active(session)
            if hashlib.sha256(probe_binary.read_bytes()).hexdigest() != probe_hash:
                raise RuntimeError("Probe changed after reference capture")
            if control.get("markerRecovered") is not True or control.get("capture", {}).get("probeBinarySHA256") != probe_hash:
                row = {"route": route, "repetition": repetition, "observation": "inconclusive",
                       "skipped": True, "reason": "No matched marker recovery with the frozen probe"}
            else:
                row = capture(session["pid"], session["trial"], route, prefix.with_name(prefix.name + "-candidate"), oracle)
                row.update({"repetition": repetition, "controlWorked": True})
            report["results"].append(row)
            save()
            print(json.dumps(row), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--routes", nargs="+", choices=ROUTES, default=ROUTES)
    parser.add_argument("--operator-physical-completion-confirmed", action="store_true")
    args = parser.parse_args()
    run(args.session.resolve(), args.output, args.repetitions, args.operator_physical_completion_confirmed, args.routes)
