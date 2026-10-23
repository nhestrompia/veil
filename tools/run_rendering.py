"""Test actual HTML pixels in protected and control sample-buffer layers."""

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path

from native_environment import observe_console
from run_native import ROOT, Oracle, probe


def run(targets, repetitions, output):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    summary = {"results": [], "humanBaseline": False,
               "routeContract": "HTML snapshots stay inside the renderer. External probe uses only native capture, OCR, and AX. No input bridge exists."}

    def save():
        (output / "results.json").write_text(json.dumps(summary, indent=2))

    summary["environment"] = observe_console()
    oracle = Oracle()
    summary["permissions"] = probe(["permissions"], output / "permissions.json")
    summary["system"] = subprocess.check_output(["sw_vers"], text=True)
    for target in targets:
        binary = ROOT / f"dist/{target}.app/Contents/MacOS/{target}"
        for repetition in range(repetitions):
            trial = oracle.create()
            prefix = output / f"{target}-{repetition}"
            record = {"target": target, "repetition": repetition, "trial": trial["id"],
                      "binarySHA256": hashlib.sha256(binary.read_bytes()).hexdigest(),
                      "route": "html-pixel-capture", "verdict": "inconclusive", "captures": {}}
            with prefix.with_suffix(".log").open("w") as log:
                process = subprocess.Popen([str(binary), "--url", trial["url"]], stdout=log, stderr=log)
                try:
                    deadline = time.monotonic() + 10
                    while time.monotonic() < deadline:
                        text = prefix.with_suffix(".log").read_text()
                        if "PIXEL_RENDER readiness" in text or "PIXEL_RENDER failed" in text:
                            break
                        time.sleep(0.2)
                    record["frameSubmitted"] = "PIXEL_RENDER first_frame" in text
                    record["rendererLog"] = text.splitlines()
                    if not record["frameSubmitted"]:
                        raise RuntimeError("No successful HTML frame submission; no capture-prevention inference")
                    time.sleep(0.5)
                    state = oracle.state(trial)
                    for route, command in [("screenkit", "capture"), ("display", "display-capture"), ("system", "system-capture")]:
                        png = prefix.with_suffix(f".{route}.png")
                        capture = probe([command, process.pid, png], prefix.with_suffix(f".{route}.json"))
                        if capture.get("status") == "captured":
                            ocr = probe(["ocr", png], prefix.with_suffix(f".{route}.ocr.json"))
                            capture["secretRecovered"] = state["secret"] in json.dumps(ocr)
                        record["captures"][route] = capture
                    ax = probe(["ax", process.pid], prefix.with_suffix(".ax.json"))
                    record["axDisclosure"] = state["secret"] in json.dumps(ax)
                    record["disclosure"] = record["axDisclosure"] or any(c.get("secretRecovered", False) for c in record["captures"].values())
                    if record["disclosure"]:
                        record["verdict"] = "bypass"
                    else:
                        record["reason"] = "No exact marker recovery. Human visibility, matched controls, and wider capture routes still required."
                except (RuntimeError, OSError, subprocess.SubprocessError) as error:
                    record["error"] = str(error)
                finally:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
            summary["results"].append(record)
            save()
            print(json.dumps(record), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--targets", nargs="+", default=["PixelControl", "PixelProtectedExperiment"],
                        choices=["PixelControl", "PixelProtectedExperiment", "PixelNV12Control", "PixelNV12ProtectedExperiment"])
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/pixel-rendering")
    args = parser.parse_args()
    run(args.targets, args.repetitions, args.output)
