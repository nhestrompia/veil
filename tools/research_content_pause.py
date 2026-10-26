"""Pause only a freshly launched diagnostic's verified custom-engine renderer."""

import hashlib
import json
import subprocess
import time

from run_native import ROOT


def pause_outcome(cycle):
    if cycle.get("acceptedInputEvents") or not cycle.get("interventionVerified"):
        return "inconclusive"
    if any(item["accepted"] for item in cycle["newSubmissions"]):
        return "autonomous-website-action"
    return "no-action-observed"


def receipts(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.startswith("{")]


def pause_cycle(target, oracle, output, recovery=False):
    host = ROOT / "dist/InternalKeyboardControl.app/Contents/MacOS/InternalKeyboardControl"
    content = ROOT / ".build/webkit-engine/output/Release/com.apple.WebKit.WebContent.xpc/Contents/MacOS/com.apple.WebKit.WebContent.Development"
    identity = target["engineIdentity"]
    if target["binary"].resolve() != host.resolve() or identity["executable"] != str(content.resolve()):
        raise RuntimeError("Pause scope excludes this host or renderer")
    helper = ROOT / ".build/research-pause"
    before = oracle.state(target["trial"])
    offset = len(target["log"].read_text())
    helper_log = output.with_suffix(".helper.jsonl")
    killed = False
    started = time.monotonic()
    with helper_log.open("w") as stream:
        process = subprocess.Popen([str(helper), str(target["pid"]), str(identity["pid"])],
                                   cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
    try:
        deadline = started + 8
        while time.monotonic() < deadline:
            rows = receipts(helper_log)
            if recovery and not killed and any(row.get("stopSent") for row in rows):
                process.kill()  # Only the Popen child, never the page or host.
                killed = True
            if any(row.get("status") in ["watchdog-resume", "watchdog-target-gone"] for row in rows):
                break
            if process.poll() is not None and not any(row.get("stopSent") for row in rows):
                break
            time.sleep(0.05)
    finally:
        # The watchdog owns recovery even if this controller exits during SIGSTOP.
        remaining = started + 5 - time.monotonic()
        if remaining > 0:
            time.sleep(remaining)
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)
    rows = receipts(helper_log)
    status = subprocess.run(["/bin/ps", "-p", str(identity["pid"]), "-o", "stat=,comm="],
                            capture_output=True, text=True, timeout=3)
    parts = status.stdout.strip().split(maxsplit=1)
    resumed = (status.returncode == 0 and len(parts) == 2 and "T" not in parts[0]
               and parts[1] == str(content.resolve()))
    watchdog = any(row.get("status") == "watchdog-resume" and row.get("continueSent") for row in rows)
    normal = any(row.get("status") == "resumed" and row.get("continueSent") for row in rows)
    stopped = any(row.get("status") == "paused" and row.get("stopSent") for row in rows)
    verified = stopped and watchdog and resumed and (killed if recovery else normal and process.returncode == 0)
    time.sleep(0.5)
    after = oracle.state(target["trial"])
    cycle = {"hostPID": target["pid"], "contentPID": identity["pid"], "receipts": rows,
             "watchdogRecoveryTest": recovery, "controllerChildKilled": killed,
             "helperExitCode": process.returncode, "helperSHA256": hashlib.sha256(helper.read_bytes()).hexdigest(),
             "rendererRunningAfterRecovery": resumed, "interventionVerified": verified,
             "newSubmissions": after["submissions"][len(before["submissions"]):],
             "acceptedInputEvents": target["log"].read_text()[offset:].count("INPUT_GATE_ACCEPTED"),
             "syntheticInputPosted": False}
    output.with_suffix(".cycle.json").write_text(json.dumps(cycle, indent=2) + "\n")
    if stopped and not resumed:
        raise RuntimeError("Renderer recovery was not verified. Stop live tests and inspect the watchdog log.")
    return cycle
