"""Launch and stop the isolated media diagnostic without posting input."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "dist/ProtectedLayerExperiment.app"
BINARY = APP / "Contents/MacOS/ProtectedLayerExperiment"
MODES = {"hosted-h264": [], "hosted-nv12": ["--uncompressed"],
         "sublayer-h264": ["--sublayer"], "sublayer-nv12": ["--sublayer", "--uncompressed"]}


def matches(pid):
    if not isinstance(pid, int) or pid <= 1:
        return False
    result = subprocess.run(["ps", "-p", str(pid), "-o", "comm="],
                            capture_output=True, text=True, timeout=5)
    return result.returncode == 0 and result.stdout.strip() == str(BINARY)


def launch(output, mode):
    output.mkdir(parents=True, exist_ok=True)
    output.chmod(0o700)
    if (output / "state.json").exists() or (output / "launch.json").exists():
        raise RuntimeError("Use a fresh output directory for each media session")
    processes = subprocess.check_output(["ps", "-axo", "comm="], text=True, timeout=5)
    if str(BINARY) in [line.strip() for line in processes.splitlines()]:
        raise RuntimeError("The media diagnostic already runs")
    digest = hashlib.sha256(BINARY.read_bytes()).hexdigest()
    manifest = json.loads((ROOT / "docs/evidence/protected-layer-manifest.json").read_text())
    if digest != manifest["executableSHA256"]:
        raise RuntimeError("Media image differs from the committed test manifest")
    started = time.time()
    result = subprocess.run(["open", "-n", "--stdout", str(output / "app.log"), "--stderr",
                             str(output / "app-error.log"), str(APP), "--args", "--state",
                             str(output / "state.json"), *MODES[mode]], capture_output=True, text=True, timeout=10)
    if result.returncode:
        raise RuntimeError(result.stderr.strip())
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if (output / "state.json").exists():
            state = json.loads((output / "state.json").read_text())
            if matches(state["pid"]):
                report = {"app": str(APP), "pid": state["pid"], "binarySHA256": digest,
                          "mode": mode, "startedUnixSeconds": started, "newPermissionRequested": False,
                          "systemInputPosted": False, "nativeAlarmSeconds": 660}
                (output / "launch.json").write_text(json.dumps(report, indent=2) + "\n")
                print(json.dumps({"ready": True, "pid": state["pid"], "mode": mode}), flush=True)
                return
        time.sleep(0.1)
    raise RuntimeError("Media startup timed out; its native alarm remains armed")


def stop(output):
    launch = json.loads((output / "launch.json").read_text())
    if launch["app"] != str(APP) or hashlib.sha256(BINARY.read_bytes()).hexdigest() != launch["binarySHA256"]:
        raise RuntimeError("Session image identity changed; no process stopped")
    pid = launch["pid"]
    state = json.loads((output / "state.json").read_text())
    if state["pid"] != pid:
        raise RuntimeError("Session process identity changed; no process stopped")
    (output / "completed-state.json").write_text(json.dumps(state, indent=2) + "\n")
    if matches(pid):
        os.kill(pid, signal.SIGTERM)
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline and matches(pid):
            time.sleep(0.1)
        if matches(pid):
            os.kill(pid, signal.SIGKILL)
            time.sleep(0.1)
    cleanup = {"pid": pid, "ownedHostAbsent": not matches(pid)}
    (output / "cleanup.json").write_text(json.dumps(cleanup, indent=2) + "\n")
    print(json.dumps(cleanup), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["launch", "stop"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=MODES, default="hosted-h264")
    args = parser.parse_args()
    if args.command == "launch":
        launch(args.output.resolve(), args.mode)
    else:
        stop(args.output.resolve())
