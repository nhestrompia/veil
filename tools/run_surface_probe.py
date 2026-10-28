"""Calibrate access to cooperating fake buffers. Never enumerate desktop surfaces."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import select

ROOT = Path(__file__).resolve().parent.parent


def run(repetitions, output):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    binary = ROOT / "dist/SurfaceProbe"
    summary = {"binarySHA256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "system": subprocess.check_output(["sw_vers"], text=True), "results": [],
        "scope": "Known-ID cooperating fake-buffer calibration. No Mach ports, browser pixels, ID discovery, or surface enumeration."}
    for kind in ["direct", "pixelBuffer"]:
        for policy in ["defaults", "local", "global"]:
            for repetition in range(repetitions):
                writer = subprocess.Popen([str(binary), "write", kind, policy], stdin=subprocess.PIPE,
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                record = {"kind": kind, "policy": policy, "repetition": repetition, "verdict": "inconclusive"}
                try:
                    if not select.select([writer.stdout], [], [], 10)[0]:
                        raise RuntimeError("Writer readiness timed out")
                    ready = json.loads(writer.stdout.readline())
                    if ready.get("status") != "ready":
                        record["writer"] = ready
                    else:
                        reader = subprocess.run([str(binary), "read", str(ready["surfaceID"])], capture_output=True, text=True, timeout=10)
                        observed = json.loads(reader.stdout)
                        record["surfaceID"] = ready["surfaceID"]
                        record["reader"] = observed
                        record["exactNonceRecovered"] = observed.get("observedNonce") == ready["expectedNonce"]
                        if record["exactNonceRecovered"]:
                            record["verdict"] = "known-id-readable"
                        elif observed.get("status") == "lookup-unavailable":
                            record["verdict"] = "known-id-unavailable"
                except (RuntimeError, OSError, ValueError, subprocess.SubprocessError) as error:
                    record["error"] = str(error)
                finally:
                    try:
                        writer.communicate("done\n", timeout=5)
                    except (BrokenPipeError, subprocess.TimeoutExpired):
                        writer.kill()
                        writer.communicate()
                summary["results"].append(record)
                print(json.dumps(record), flush=True)
                (output / "results.json").write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/surface-calibration")
    args = parser.parse_args()
    run(args.repetitions, args.output)
