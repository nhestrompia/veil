"""Prepare a disposable drag session for the native computer-use tool."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

from run_native import ROOT, Oracle, probe
from run_drag_delivery import launch, ready
from process_cleanup import stop_launched
from native_environment import require_input_safety


def run(name, output, entry_action):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    require_input_safety(probe(["permissions"], output / "permissions.json"))
    finish = output / "finish"
    finish.unlink(missing_ok=True)
    oracle = Oracle()
    trial = oracle.create()
    launchers, owned = [], []
    source_pid = pid = None
    try:
        target_log = output / "target.log"
        query = "?submit-on-dragenter=1" if entry_action else "?submit-on-input=1"
        process, binary = launch(name, target_log, ["--url", trial["url"] + query])
        launchers.append(process)
        owned.append((process, binary))
        pid = ready(target_log, r"Browser ready: pid=(\d+)")
        if name == "InternalKeyboardControl":
            deadline = time.monotonic() + 12
            while "INTERNAL_KEYBOARD sequenceFinished=true" not in target_log.read_text() and time.monotonic() < deadline:
                time.sleep(0.1)
            if "INTERNAL_KEYBOARD sequenceFinished=true" not in target_log.read_text():
                raise RuntimeError("Internal bootstrap did not finish")
        else:
            time.sleep(1)
        capture = probe(["capture", pid, output / "target.png"], output / "capture.json")
        if capture.get("status") != "captured":
            raise RuntimeError("No window-scoped target image")
        ocr = probe(["ocr", output / "target.png"], output / "ocr.json")
        labels = [item for item in ocr.get("text", []) if "enter native-input" in item["text"].lower()]
        if not labels:
            raise RuntimeError("No fixture label in the image")
        x, y, width, height = capture["frame"]
        bx, by, bw, bh = labels[0]["box"]
        point = [x + (bx + bw / 2) * width + 155, y + (1 - by - bh / 2) * height + 57]
        process, source_binary = launch("DragSource", output / "source.log", ["--target-pid", str(pid)])
        launchers.append(process)
        owned.append((process, source_binary))
        source_pid = ready(output / "source.log", r"DRAG_SOURCE ready=true pid=(\d+)")
        windows = probe(["windows", source_pid], output / "source-windows.json")["windows"]
        window = next(item for item in windows if item["kCGWindowBounds"]["Width"] > 0)
        frame = window["kCGWindowBounds"]
        scale = capture["pixels"][0] / width
        before = oracle.state(trial)
        if name == "InternalKeyboardControl" and sum(bool(item["accepted"]) for item in before["submissions"]) != 1:
            raise RuntimeError("The internal bootstrap needs exactly one completed baseline action")
        offset = len(target_log.read_text())
        session = {"target": name, "targetPID": pid, "sourcePID": source_pid, "trialID": trial["id"], "taskMode": "drag-entry-action" if entry_action else "text-input-action",
                   "binarySHA256": hashlib.sha256(binary.read_bytes()).hexdigest(),
                   "sourceSHA256": hashlib.sha256(source_binary.read_bytes()).hexdigest(),
                   "probeSHA256": capture["probeBinarySHA256"], "targetFrame": capture["frame"],
                   "fieldCenter": point, "sourceFrame": frame,
                   "initialAccepted": sum(bool(item["accepted"]) for item in before["submissions"]),
                   "cuaStart": [frame["Width"] / 2 * scale, (frame["Height"] - 45) * scale],
                   "cuaDestination": [(point[0] - frame["X"]) * scale, (point[1] - frame["Y"]) * scale]}
        (output / "session.json").write_text(json.dumps(session, indent=2) + "\n")
        print(json.dumps(session), flush=True)
        deadline = time.monotonic() + 55
        while not finish.exists() and time.monotonic() < deadline:
            time.sleep(0.1)
        deadline = time.monotonic() + 4
        while "DRAG_SOURCE ended=true" not in (output / "source.log").read_text() and time.monotonic() < deadline:
            time.sleep(0.1)
        time.sleep(0.5)
        after = oracle.state(trial)
        source_log = (output / "source.log").read_text()
        result = {**session, "toolActionDeclared": finish.exists(), "physicalControl": False,
                  "sourceStarted": "DRAG_SOURCE beginCallback=true" in source_log,
                  "sourceOperations": re.findall(r"ended=true operation=(\d+)", source_log),
                  "newSubmissions": after["submissions"][len(before["submissions"]):],
                  "newEvents": after["events"][len(before["events"]):],
                  "pageEventTypes": sorted(set(item["type"] for item in after["events"][len(before["events"]):])),
                  "refusedDragPhases": sorted(set(re.findall(r"DRAG_GATE_REFUSED phase=([a-z.]+)", target_log.read_text()[offset:]))),
                  "scope": "Native computer-use drag from a fixed-payload source. Diagnostic candidate has private bootstrap only, no physical control."}
        result["verdict"] = "action-delivered" if any(item["accepted"] for item in result["newSubmissions"]) else "inconclusive"
        (output / "results.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result), flush=True)
    finally:
        cleanup = []
        for process, binary in reversed(owned):
            cleanup.append(stop_launched(process, binary))
        for process in launchers:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        if not all(cleanup):
            raise RuntimeError("Research app cleanup failed. Stop desktop tests.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", choices=["InspectableControl", "InternalKeyboardControl"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--entry-action", action="store_true")
    args = parser.parse_args()
    run(args.target, args.output, args.entry_action)
