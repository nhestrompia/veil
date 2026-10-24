"""Score a diagnostic build's private input sequence with the local oracle."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

from run_native import ROOT, Oracle, probe
from process_cleanup import matching_pids, stop_launched


def run(output, external_reads, stream, submit_on_input=False):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    app = ROOT / "dist/InternalKeyboardControl.app"
    binary = app / "Contents/MacOS/InternalKeyboardControl"
    oracle = Oracle()
    trial = oracle.create()
    url = trial["url"] + ("?submit-on-input=1" if submit_on_input else "")
    log = output / "control.log"
    log.write_text("")
    existing = matching_pids(binary)
    launcher = subprocess.Popen(["open", "-n", "-W", str(app), "--stdout", str(log), "--stderr", str(log),
                                 "--args", "--url", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    launcher.research_existing_pids = existing
    pid = None
    result = None
    try:
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            text = log.read_text()
            match = re.search(r"Browser ready: pid=(\d+)", text)
            if match:
                pid = int(match[1])
            state = oracle.state(trial)
            if "INTERNAL_KEYBOARD sequenceFinished=true" in text and any(item["accepted"] for item in state["submissions"]):
                break
            time.sleep(0.1)
        text = log.read_text()
        state = oracle.state(trial)
        result = {"binarySHA256": hashlib.sha256(binary.read_bytes()).hexdigest(), "pid": pid,
                  "startupAddressPreserved": "INTERNAL_KEYBOARD startupAddressPreserved=true" in text,
                  "locationHasEditor": "INTERNAL_KEYBOARD locationHasEditor=true" in text,
                  "locationUsesRestrictedEditor": "INTERNAL_KEYBOARD locationUsesRestrictedEditor=true" in text,
                  "inputTriggeredSubmit": "INTERNAL_KEYBOARD inputTriggeredSubmit=true" in text,
                  "acceptedSubmissions": sum(bool(item["accepted"]) for item in state["submissions"]),
                  "noDeviceReader": "INTERNAL_KEYBOARD sequenceFinished=true noDeviceReader=true" in text,
                  "humanBaseline": False, "windowSharingEnabled": "INTERNAL_KEYBOARD windowSharingEnabled=true" in text,
                  "scope": "Diagnostic-only private authorized events through the normal application and WebKit path. Not an external bypass, physical control, or HID attestation."}
        if external_reads and result["acceptedSubmissions"]:
            backdrop = re.search(r"INTERNAL_CAPTURE targetWindow=(\d+) backdropWindow=(\d+)", text)
            if stream and not backdrop:
                raise RuntimeError("The stream diagnostic requires an owned research backdrop")
            if backdrop:
                mode = "stream" if stream else "compositor"
                command = "isolated-stream-capture" if stream else "isolated-compositor-capture"
                composite = probe([command, pid, *backdrop.groups(), output / f"{mode}.png"], output / f"{mode}.json")
                result["isolatedStream" if stream else "isolatedCompositor"] = composite
                if composite.get("status") == "captured":
                    ocr = probe(["ocr", output / f"{mode}.png"], output / f"{mode}.ocr.json")
                    result[f"{mode}MarkerDisclosed"] = state["secret"] in json.dumps(ocr)
                    result["backdropLabelRecovered"] = "controlled research backdrop" in json.dumps(ocr).lower()
            else:
                read = probe(["ax-direct", pid], output / "direct-ax.json")
                result["directAX"] = {"status": read.get("status"), "elements": len(read.get("elements", [])),
                                      "markerDisclosed": state["secret"] in json.dumps(read)}
                capture = probe(["capture", pid, output / "window.png"], output / "capture.json")
                result["capture"] = capture
                if capture.get("status") == "captured":
                    ocr = probe(["ocr", output / "window.png"], output / "ocr.json")
                    result["captureMarkerDisclosed"] = state["secret"] in json.dumps(ocr)
                system = probe(["system-capture", pid, output / "system.png"], output / "system.json")
                result["systemCapture"] = system
                if system.get("status") == "captured":
                    ocr = probe(["ocr", output / "system.png"], output / "system.ocr.json")
                    result["systemMarkerDisclosed"] = state["secret"] in json.dumps(ocr)
        (output / "results.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result), flush=True)
    finally:
        cleaned = stop_launched(launcher, binary, pid)
        launcher.terminate()
        try:
            launcher.wait(timeout=3)
        except subprocess.TimeoutExpired:
            launcher.kill()
            launcher.wait()
        if not cleaned:
            raise RuntimeError("Research app cleanup failed. Stop desktop tests.")
    if (not result or result["inputTriggeredSubmit"] != submit_on_input
            or not all(result[key] for key in ["startupAddressPreserved", "locationHasEditor", "locationUsesRestrictedEditor", "acceptedSubmissions", "noDeviceReader"])):
        raise RuntimeError("Internal keyboard functionality failed; inspect the diagnostic-only log")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/internal-keyboard-control")
    parser.add_argument("--external-reads", action="store_true")
    parser.add_argument("--stream", action="store_true")
    parser.add_argument("--submit-on-input", action="store_true")
    args = parser.parse_args()
    if args.stream and not args.external_reads:
        parser.error("--stream requires --external-reads")
    run(args.output, args.external_reads, args.stream, args.submit_on_input)
