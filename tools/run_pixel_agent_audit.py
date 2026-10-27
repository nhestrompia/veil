"""Exercise external observation and AX actions against the pixel prototype."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import threading
import time

from fixture import FixtureServer
from run_native import ROOT, Oracle, probe


def marker_recovery(ocr, expected):
    text = json.dumps(ocr, ensure_ascii=False)
    # Vision emitted Cyrillic E for a visible Latin E in the first clear control.
    aliases = str.maketrans({"А": "A", "В": "B", "С": "C", "Е": "E", "Α": "A", "Β": "B", "Ε": "E"})
    return {"exact": expected in text, "visualHexAliases": expected in text.translate(aliases)}


def run(output, launch_only=False, launch_targets=None):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    server = FixtureServer(("127.0.0.1", 0))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    controller = output / "fixture-controller.json"
    controller.write_text(json.dumps({"port": server.server_port, "key": server.controller_key}))
    controller.chmod(0o600)
    oracle = Oracle(controller)
    permissions = probe(["permissions"], output / "permissions.json", background=True)
    report = {"routes": [], "permissions": permissions,
              "scope": "External captures and owned-process AX. Oracle data scores outcomes only.",
              "humanInputBridge": False, "humanTaskCompletionVerified": False,
              "inputHooksInstalled": False, "administratorAccessUsed": False}

    def save():
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    def record(row):
        report["routes"].append(row)
        save()
        print(json.dumps({k: row.get(k) for k in ["target", "route", "observation", "actionCompleted", "error"] if k in row}), flush=True)

    try:
        for name in ([] if launch_only else ["InspectableControl", "PixelH264Control", "PixelH264ProtectedExperiment"]):
            binary = ROOT / f"dist/{name}.app/Contents/MacOS/{name}"
            digest = hashlib.sha256(binary.read_bytes()).hexdigest()
            trial = oracle.create()
            prefix = output / name
            log_path = prefix.with_suffix(".log")
            with log_path.open("w") as log:
                app = subprocess.Popen([str(binary), "--url", trial["url"]], stdout=log, stderr=log)
                try:
                    for _ in range(75):
                        text = log_path.read_text()
                        if "PIXEL_RENDER readiness" in text or "Browser ready:" in text:
                            break
                        if app.poll() is not None or "PIXEL_RENDER failed" in text:
                            raise RuntimeError("Research target did not become ready")
                        time.sleep(0.2)
                    else:
                        raise RuntimeError("Research target readiness timed out")
                    time.sleep(0.4)
                    common = {"target": name, "pid": app.pid, "binarySHA256": digest,
                              "trial": trial["id"]}
                    for route, command in [("ax-tree", "ax"), ("ax-direct", "ax-direct"),
                                           ("ax-action", "ax-action")]:
                        before = oracle.state(trial)
                        try:
                            result = probe([command, app.pid], output / f"{name}-{route}.json", background=True)
                            after = oracle.state(trial)
                            completed = any(s["accepted"] for s in after["submissions"][len(before["submissions"]):])
                            observed = after["secret"] in json.dumps(result)
                            record({**common, "route": route, "probe": result,
                                    "observation": "marker-recovered" if observed else "marker-not-recovered",
                                    "actionCompleted": completed,
                                    "verdict": "bypass" if completed or observed else "inconclusive"})
                        except (RuntimeError, OSError, subprocess.SubprocessError) as error:
                            record({**common, "route": route, "observation": "unavailable", "error": str(error), "verdict": "inconclusive"})
                    for route, command in [("screenshot-window", "capture"),
                                           ("screenshot-filtered-display", "display-capture"),
                                           ("screenshot-system-window", "system-capture")]:
                        image = output / f"{name}-{route}.png"
                        subprocess.run(["open", "-a", str(binary.parents[2])], check=True, timeout=10)
                        try:
                            result = probe([command, app.pid, image], output / f"{name}-{route}.json", background=True)
                            ocr = probe(["ocr", image], output / f"{name}-{route}.ocr.json", background=True) if result.get("status") == "captured" and image.exists() else {}
                            recovery = marker_recovery(ocr, oracle.state(trial)["secret"])
                            observed = recovery["exact"] or recovery["visualHexAliases"]
                            record({**common, "route": route, "probe": result,
                                    "observation": "marker-recovered" if observed else "marker-not-recovered",
                                    "ocrAvailable": bool(ocr), "markerRecovery": recovery,
                                    "verdict": "disclosure" if observed else "inconclusive"})
                        except (RuntimeError, OSError, subprocess.SubprocessError) as error:
                            record({**common, "route": route, "observation": "unavailable", "error": str(error), "verdict": "inconclusive"})
                    record({**common, "route": "synthetic-pointer-and-keys", "observation": "not-run",
                            "reason": "Modifying mouse hooks are active. Pixel targets also have no input bridge. Neither condition proves resistance.",
                            "desktopInputSafety": permissions.get("desktopInputSafety"), "verdict": "inconclusive"})
                    record({**common, "route": "renderer-process-AX", "observation": "not-run",
                            "reason": "Frozen renderer helper permits only its existing exact host identities. Pixel targets need a separately reviewed helper scope.",
                            "verdict": "inconclusive"})
                finally:
                    app.terminate()
                    try:
                        app.wait(timeout=4)
                    except subprocess.TimeoutExpired:
                        app.kill()
                        app.wait()
        server.page_template = ROOT / "tools/launch-action-fixture.html"
        for name in (launch_targets or ["PixelH264Control", "PixelH264ProtectedExperiment"]):
            trial = oracle.create()
            binary = ROOT / f"dist/{name}.app/Contents/MacOS/{name}"
            with (output / f"{name}-launch-action.log").open("w") as log:
                app = subprocess.Popen([str(binary), "--url", trial["url"]], stdout=log, stderr=log)
                try:
                    state = oracle.state(trial)
                    deadline = time.monotonic() + 10
                    while time.monotonic() < deadline and not state["submissions"]:
                        time.sleep(0.1)
                        state = oracle.state(trial)
                    completed = any(row["accepted"] for row in state["submissions"])
                    record({"target": name, "pid": app.pid, "binarySHA256": hashlib.sha256(binary.read_bytes()).hexdigest(),
                            "route": "launch-url-navigation", "trial": trial["id"],
                            "observation": "page-script-ran" if completed else "no-accepted-action",
                            "actionCompleted": completed, "inputSent": False,
                            "verdict": "bypass" if completed else "inconclusive",
                            "scope": "The agent chose a launch URL. The disposable page commits a harmless action on load. No input bridge is involved."})
                finally:
                    app.terminate()
                    try:
                        app.wait(timeout=4)
                    except subprocess.TimeoutExpired:
                        app.kill()
                        app.wait()
        report["ownedTargetsStopped"] = True
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=3)
        report["ownedFixtureStopped"] = not worker.is_alive()
        save()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/pixel-agent-audit")
    parser.add_argument("--launch-only", action="store_true")
    parser.add_argument("--launch-targets", nargs="+", choices=["PixelH264Control", "PixelH264ProtectedExperiment", "PixelKeyboardExperiment"])
    args = parser.parse_args()
    run(args.output, args.launch_only, args.launch_targets)
