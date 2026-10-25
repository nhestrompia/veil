"""Keep one disposable local-inspector reference alive for native UI research."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

from native_environment import require_input_safety
from process_cleanup import stop_launched
from run_drag_delivery import launch, ready
from run_native import ROOT, Oracle, probe


def run(output):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    permissions = probe(["permissions"], output / "permissions.json")
    require_input_safety(permissions)
    finish = output / "finish"
    finish.unlink(missing_ok=True)
    oracle = Oracle()
    trial = oracle.create()
    log = output / "reference.log"
    launcher, binary = launch("InspectableControl", log,
        ["-WebKitDebugDeveloperExtrasEnabled", "YES", "--url", trial["url"]])
    pid = None
    try:
        pid = ready(log, r"Browser ready: pid=(\d+)")
        time.sleep(1)
        before = oracle.state(trial)
        if before["submissions"]:
            raise RuntimeError("Reference has a submission before inspector attachment")
        session = {"pid": pid, "trialID": trial["id"], "url": trial["url"],
                   "binarySHA256": hashlib.sha256(binary.read_bytes()).hexdigest(),
                   "developerExtrasRequested": True, "persistentPreferencesChanged": False}
        (output / "session.json").write_text(json.dumps(session, indent=2) + "\n")
        print(json.dumps(session), flush=True)
        deadline = time.monotonic() + 240
        while not finish.exists() and time.monotonic() < deadline:
            time.sleep(0.1)
        time.sleep(0.5)
        after = oracle.state(trial)
        result = {**session, "operatorFinished": finish.exists(), "humanBaseline": False,
                  "newSubmissions": after["submissions"][len(before["submissions"]):],
                  "scope": "Readable local-inspector reference only. No protected-browser attachment claim."}
        (output / "results.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result), flush=True)
    finally:
        cleaned = stop_launched(launcher, binary, pid)
        launcher.terminate()
        try:
            launcher.wait(timeout=3)
        except subprocess.TimeoutExpired:
            launcher.kill()
            launcher.wait()
        (output / "cleanup.json").write_text(json.dumps({"pid": pid, "verified": cleaned}) + "\n")
        if not cleaned:
            raise RuntimeError("Inspector reference cleanup failed. Stop desktop tests.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/local-inspector-control")
    run(parser.parse_args().output)
