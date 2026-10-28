"""Compare signals against owned disposable CLI targets with different signatures."""

import argparse
import hashlib
import json
from pathlib import Path
import signal
import subprocess
import time

from run_native import ROOT
from process_cleanup import matching_pids


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def run(output):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    binaries = ROOT / ".build/signal-signing-control"
    binaries.mkdir(exist_ok=True)
    report = {"websiteTest": False, "humanBaseline": False,
              "scope": "Signals target only newly launched standalone CLI children. No browser or system process is targeted.",
              "macOS": subprocess.check_output(["/usr/bin/sw_vers", "-productVersion"], text=True).strip(),
              "trials": []}
    try:
        for mode in ["ordinary", "hardened"]:
            binary = binaries / mode
            if matching_pids(binary):
                raise RuntimeError("A disposable signing control already exists")
            subprocess.run(["xcrun", "clang", "-std=c11", "-Wall", "-Wextra", "-Werror",
                            str(ROOT / "Sources/Diagnostics/SignalControl.c"), "-o", str(binary)], check=True)
            command = ["/usr/bin/codesign", "--force", "--sign", "-"]
            if mode == "hardened":
                command += ["--options", "runtime"]
            subprocess.run([*command, str(binary)], capture_output=True, text=True, check=True)
            subprocess.run(["/usr/bin/codesign", "--verify", "--strict", str(binary)], check=True)
            signing = subprocess.run(["/usr/bin/codesign", "-d", "--verbose=2", str(binary)],
                                     capture_output=True, text=True, check=True).stderr
            runtime = any("runtime" in line for line in signing.splitlines() if line.startswith("CodeDirectory"))
            if runtime != (mode == "hardened"):
                raise RuntimeError("The target signature does not match the requested control")
            for recovery in [False, True]:
                row = {"mode": mode, "watchdogRecovery": recovery, "runtimeFlag": runtime,
                       "binarySHA256": hashlib.sha256(binary.read_bytes()).hexdigest(),
                       "signing": signing.splitlines(), "status": "inconclusive"}
                report["trials"].append(row)
                log = output / f"{mode}-{'recovery' if recovery else 'normal'}.jsonl"
                with log.open("w") as stream:
                    process = subprocess.Popen([str(binary)], stdout=stream, stderr=subprocess.STDOUT, cwd=ROOT)
                try:
                    deadline = time.monotonic() + 2
                    while time.monotonic() < deadline and not read_rows(log):
                        time.sleep(0.02)
                    ready = read_rows(log)[0]
                    if not ready.get("ready") or ready.get("pid") != process.pid:
                        raise RuntimeError("The owned CLI control did not become ready")
                    row["pid"] = process.pid
                    time.sleep(0.25)
                    before = subprocess.check_output(["/bin/ps", "-p", str(process.pid), "-o", "comm="], text=True).strip()
                    if before != str(binary.resolve()):
                        raise RuntimeError("The owned child executable changed")
                    process.send_signal(signal.SIGSTOP)
                    row["stopSent"] = True
                    time.sleep(0.1)
                    state = subprocess.check_output(["/bin/ps", "-p", str(process.pid), "-o", "stat="], text=True).strip()
                    row["stoppedStateObserved"] = "T" in state
                    if not recovery:
                        time.sleep(0.9)
                        process.send_signal(signal.SIGCONT)
                        row["continueSent"] = True
                    process.wait(timeout=6)
                    rows = read_rows(log)
                    row.update(receipts=rows, exitCode=process.returncode, cleanupVerified=True)
                    finished = next((item for item in rows if item.get("completed")), {})
                    watchdog = any(item.get("watchdogResumed") for item in rows)
                    if process.returncode == 0 and watchdog and row["stoppedStateObserved"] and finished.get("maximumGapSeconds", 0) > 0.8:
                        row["status"] = "external-pause-observed"
                finally:
                    # Only this Popen child. The independent watchdog also resumes it.
                    if process.poll() is None:
                        process.send_signal(signal.SIGCONT)
                        try:
                            process.wait(timeout=6)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait(timeout=3)
                    row["cleanupVerified"] = process.poll() is not None
                print(json.dumps({key: row.get(key) for key in ["mode", "watchdogRecovery", "runtimeFlag", "status", "cleanupVerified"]}), flush=True)
        return report
    finally:
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
