"""Compare direct File/Edit menu exposure without using clipboard data."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

from run_native import ROOT, Oracle, probe


def run(output):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    permission = probe(["permissions"], output / "permissions.json")
    if not permission.get("accessibility"):
        raise RuntimeError("The probe needs its existing effective Accessibility grant")
    rows = []
    for name in ["InspectableControl", "DeviceKeyboardExperiment"]:
        trial = Oracle().create()
        app = ROOT / f"dist/{name}.app"
        binary = app / f"Contents/MacOS/{name}"
        log = output / f"{name}.log"
        log.write_text("")
        launcher = subprocess.Popen(["open", "-n", "-W", str(app), "--stdout", str(log), "--stderr", str(log),
                                     "--args", "--url", trial["url"]], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pid = None
        try:
            for _ in range(60):
                match = re.search(r"Browser ready: pid=(\d+)", log.read_text())
                if match:
                    pid = int(match[1])
                    break
                time.sleep(0.1)
            if pid is None:
                raise RuntimeError("Research browser readiness failed")
            result = probe(["ax-menu", pid, "inspect"], output / f"{name}.json")
            row = {"target": name, "binarySHA256": hashlib.sha256(binary.read_bytes()).hexdigest(),
                   "attempt": result, "verdict": "inconclusive"}
            if name == "InspectableControl" and result.get("status") == "observed" and any(item["title"] == "Select All" for item in result.get("items", [])):
                row["verdict"] = "content-menu-exposed"
            if name == "DeviceKeyboardExperiment" and rows[0]["verdict"] == "content-menu-exposed" and result.get("status") == "observed" and not result.get("items"):
                row["verdict"] = "content-menus-absent"
            rows.append(row)
            print(json.dumps(row), flush=True)
            (output / "results.json").write_text(json.dumps({"results": rows, "clipboardAccessed": False,
                "scope": "Direct File/Edit menu queries only. No physical task, device-origin, capture, or general action-prevention claim."}, indent=2))
        finally:
            if pid is not None:
                process = subprocess.run(["ps", "-p", str(pid), "-o", "comm="], capture_output=True, text=True)
                if process.stdout.strip() == str(binary):
                    os.kill(pid, signal.SIGTERM)
            launcher.terminate()
            try:
                launcher.wait(timeout=3)
            except subprocess.TimeoutExpired:
                launcher.kill()
                launcher.wait()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/menu-boundary-fixed")
    run(parser.parse_args().output)
