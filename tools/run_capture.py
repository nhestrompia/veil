"""Capture target windows and attempt screenshot/OCR/native-input operation."""

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

from run_native import ROOT, Oracle, probe
from native_environment import observe_console


def run(targets, repetitions, output):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    environment = observe_console()
    oracle = Oracle()
    permissions = probe(["permissions"], output / "permissions.json")
    results = []
    for name in targets:
        binary = ROOT / f"dist/{name}.app/Contents/MacOS/{name}"
        for repetition in range(repetitions):
            trial = oracle.create()
            prefix = output / f"{name}-{repetition}"
            with prefix.with_suffix(".log").open("w") as log:
                process = subprocess.Popen([str(binary), "--url", trial["url"]], stdout=log, stderr=log)
                try:
                    time.sleep(1.5)
                    captures = {}
                    for route, command in [("screenkit", "capture"), ("compositor", "compositor-capture"), ("system", "system-capture")]:
                        try:
                            captures[route] = probe([command, process.pid, prefix.with_suffix(f".{route}.png")], prefix.with_suffix(f".{route}.json"))
                        except (RuntimeError, subprocess.SubprocessError) as error:
                            captures[route] = {"status": "inconclusive", "error": str(error)}
                    screenshot, system = captures["screenkit"], captures["system"]
                    state = oracle.state(trial)
                    record = {"target": name, "trial": trial["id"], "repetition": repetition,
                              "route": "screenkit-ocr-cgevent", "verdict": "inconclusive", "environment": environment,
                              "binarySHA256": hashlib.sha256(binary.read_bytes()).hexdigest(),
                              "screenkit": screenshot, "compositorCapture": captures["compositor"], "systemCapture": system}
                    ocr = {}
                    selected_capture = None
                    for route, capture in captures.items():
                        if capture.get("status") == "captured":
                            text = probe(["ocr", prefix.with_suffix(f".{route}.png")], prefix.with_suffix(f".{route}.ocr.json"))
                            record[route + "Disclosure"] = state["secret"] in json.dumps(text)
                            if selected_capture is None and "frame" in capture and any(
                                "enter native-input" in item["text"].lower() for item in text.get("text", [])):
                                selected_capture = capture
                                ocr = text
                                record["inputImageRoute"] = route
                    labels = [item for item in ocr.get("text", []) if "enter native-input" in item["text"].lower()]
                    if labels and selected_capture is not None:
                        x, y, width, height = selected_capture["frame"]
                        bx, by, bw, bh = labels[0]["box"]
                        field_x = x + (bx + bw / 2) * width
                        field_y = y + (1 - by - bh / 2) * height + 57
                        record["input"] = probe(["input", process.pid, field_x, field_y, "hid", "curve"], prefix.with_suffix(".input.json"))
                        record["coordinateDerivation"] = "OCR label center plus public fixture's 57-point field offset; no AX tree"
                    else:
                        record["reason"] = "No OCR label or capture frame; no action-prevention inference"
                    time.sleep(0.4)
                    state = oracle.state(trial)
                    prefix.with_suffix(".oracle.json").write_text(json.dumps(state, indent=2))
                    record["submissions"] = state["submissions"]
                    record["disclosure"] = any(record.get(route + "Disclosure", False) for route in captures)
                    if any(s["accepted"] for s in state["submissions"]):
                        record["verdict"] = "bypass"
                    results.append(record)
                    print(json.dumps({k: record.get(k) for k in ["target", "repetition", "screenkitDisclosure", "compositorDisclosure", "systemDisclosure", "inputImageRoute", "verdict"]}), flush=True)
                finally:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
            (output / "results.json").write_text(json.dumps({"permissions": permissions, "results": results,
                "humanBaseline": False, "routeContract": "Agent uses ScreenCaptureKit images, Vision OCR, and CGEvent input. No AX or browser-content API."}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--targets", nargs="+", default=["AgentFreeBrowser", "InspectableControl"], choices=["AgentFreeBrowser", "InspectableControl", "MetadataExperiment", "SecureInputExperiment", "ReducedExposureExperiment", "AXBoundaryExperiment"])
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/capture-pilot")
    args = parser.parse_args()
    run(args.targets, args.repetitions, args.output)
