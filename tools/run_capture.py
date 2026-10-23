"""Capture target windows and attempt screenshot/OCR/native-input operation."""

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

from run_native import ROOT, Oracle, probe
from native_environment import NativeEnvironmentUnavailable, require_unlocked


def run(targets, repetitions, output):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    try:
        require_unlocked()
    except NativeEnvironmentUnavailable as error:
        (output / "results.json").write_text(json.dumps({"results": [{"route": "environment-preflight", "verdict": "inconclusive", "error": str(error)}]}, indent=2))
        raise
    oracle = Oracle()
    permissions = probe(["permissions"], output / "permissions.json")
    results = []
    for name in targets:
        binary = ROOT / f"dist/{name}.app/Contents/MacOS/{name}"
        for repetition in range(repetitions):
            require_unlocked()
            trial = oracle.create()
            prefix = output / f"{name}-{repetition}"
            with prefix.with_suffix(".log").open("w") as log:
                process = subprocess.Popen([str(binary), "--url", trial["url"]], stdout=log, stderr=log)
                try:
                    time.sleep(1.5)
                    require_unlocked()
                    captures = {}
                    for route, command in [("screenkit", "capture"), ("system", "system-capture")]:
                        try:
                            captures[route] = probe([command, process.pid, prefix.with_suffix(f".{route}.png")], prefix.with_suffix(f".{route}.json"))
                        except (RuntimeError, subprocess.SubprocessError) as error:
                            captures[route] = {"status": "inconclusive", "error": str(error)}
                    screenshot, system = captures["screenkit"], captures["system"]
                    state = oracle.state(trial)
                    record = {"target": name, "trial": trial["id"], "repetition": repetition,
                              "route": "screenkit-ocr-cgevent", "verdict": "inconclusive",
                              "binarySHA256": hashlib.sha256(binary.read_bytes()).hexdigest(),
                              "screenkit": screenshot, "systemCapture": system}
                    ocr = {}
                    for route, capture in [("screenkit", screenshot), ("system", system)]:
                        if capture.get("status") == "captured":
                            text = probe(["ocr", prefix.with_suffix(f".{route}.png")], prefix.with_suffix(f".{route}.ocr.json"))
                            record[route + "Disclosure"] = state["secret"] in json.dumps(text)
                            if route == "screenkit":
                                ocr = text
                    labels = [item for item in ocr.get("text", []) if "enter native-input" in item["text"].lower()]
                    if labels and "frame" in screenshot:
                        x, y, width, height = screenshot["frame"]
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
                    record["disclosure"] = record.get("screenkitDisclosure", False) or record.get("systemDisclosure", False)
                    if any(s["accepted"] for s in state["submissions"]):
                        record["verdict"] = "bypass"
                    results.append(record)
                    print(json.dumps({k: record.get(k) for k in ["target", "repetition", "screenkitDisclosure", "systemDisclosure", "verdict"]}), flush=True)
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
    parser.add_argument("--targets", nargs="+", default=["AgentFreeBrowser", "InspectableControl"], choices=["AgentFreeBrowser", "InspectableControl", "MetadataExperiment", "SecureInputExperiment", "ReducedExposureExperiment"])
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/capture-pilot")
    args = parser.parse_args()
    run(args.targets, args.repetitions, args.output)
