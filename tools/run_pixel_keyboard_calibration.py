"""Check process-local keyboard routing without claiming physical input."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import threading
import time

from fixture import FixtureServer
from run_native import ROOT, Oracle, probe


def run(output):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    server = FixtureServer(("127.0.0.1", 0))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    controller = output / "fixture-controller.json"
    controller.write_text(json.dumps({"port": server.server_port, "key": server.controller_key}))
    controller.chmod(0o600)
    oracle = Oracle(controller)
    trial = oracle.create()
    binary = ROOT / "dist/PixelKeyboardRoutingControl.app/Contents/MacOS/PixelKeyboardRoutingControl"
    result = {"target": "PixelKeyboardRoutingControl", "binarySHA256": hashlib.sha256(binary.read_bytes()).hexdigest(),
              "trial": trial["id"], "physicalInputTested": False, "systemInputPosted": False,
              "scope": "Compile-time control internally authorizes process-local NSEvents. The protected image excludes this generator."}
    with (output / "browser.log").open("w") as log:
        app = subprocess.Popen([str(binary), "--url", trial["url"]], stdout=log, stderr=log)
        try:
            deadline = time.monotonic() + 15
            state = oracle.state(trial)
            while time.monotonic() < deadline:
                state = oracle.state(trial)
                text = (output / "browser.log").read_text()
                if state["submissions"] or app.poll() is not None or "PIXEL_RENDER failed" in text:
                    break
                time.sleep(0.1)
            result["acceptedSubmissions"] = sum(s["accepted"] for s in state["submissions"])
            result["events"] = state["events"]
            result["rendererLog"] = (output / "browser.log").read_text().splitlines()
            result["passed"] = result["acceptedSubmissions"] == 1 and "PIXEL_RENDER failed" not in text
            result["capture"] = probe(["capture", app.pid, output / "routing-control.png"], output / "capture.json", background=True)
            if result["capture"].get("status") == "captured":
                result["ocr"] = probe(["ocr", output / "routing-control.png"], output / "ocr.json", background=True)
        finally:
            app.terminate()
            try:
                app.wait(timeout=4)
            except subprocess.TimeoutExpired:
                app.kill()
                app.wait()
            server.shutdown()
            server.server_close()
            worker.join(timeout=3)
            result["ownedAppStopped"] = app.poll() is not None
            result["ownedFixtureStopped"] = not worker.is_alive()
            (output / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result.get(k) for k in ["target", "passed", "acceptedSubmissions", "rendererLog"]}), flush=True)
    if not result["passed"]:
        raise RuntimeError("Keyboard routing did not complete the disposable task")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/pixel-keyboard-calibration")
    run(parser.parse_args().output)
