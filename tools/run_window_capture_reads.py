"""Read only the current owned diagnostic and score its capture channels."""

import argparse
import hashlib
import json
from pathlib import Path

from process_cleanup import matching_pids
from run_native import ROOT, probe
from run_pixel_agent_audit import marker_recovery


def run(output):
    output = output.resolve()
    session = json.loads((output / "session.json").read_text())
    binary = ROOT / "dist/InternalKeyboardControl.app/Contents/MacOS/InternalKeyboardControl"
    if (hashlib.sha256(binary.read_bytes()).hexdigest() != session["binarySHA256"]
            or session["pid"] not in matching_pids(binary)):
        raise RuntimeError("The recorded diagnostic process or image changed")
    rows = []
    routes = (["capture", "display-capture", "system-capture"] if session["windowOnly"] else
              ["isolated-compositor-capture", "isolated-stream-capture"])
    for route in routes:
        image = output / (route + ".png")
        arguments = [route, session["pid"]]
        if not session["windowOnly"]:
            arguments += [session["targetWindowID"], session["backdropWindowID"]]
        arguments.append(image)
        result = probe(arguments, output / (route + ".json"), background=True)
        ocr = (probe(["ocr", image], output / (route + "-ocr.json"), background=True)
               if result.get("status") == "captured" and image.exists() else {})
        row = {"route": route, "probe": result, "ocrAvailable": isinstance(ocr.get("text"), list),
               "markerRecovery": marker_recovery(ocr, session["secret"]),
               "backdropLabelRecovered": "controlled research backdrop" in json.dumps(ocr).lower()}
        rows.append(row)
        (output / "capture-attempts.json").write_text(json.dumps({
            "testedBinarySHA256": session["binarySHA256"], "rows": rows,
            "scope": "Capture observations only. Missing markers need matched readable references and physical visibility."}, indent=2) + "\n")
        print(json.dumps(row), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
