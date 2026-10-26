"""Measure an ordinary-user WKWebView with no window or external input."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from process_cleanup import matching_pids, stop_launched


ROOT = Path(__file__).resolve().parents[1]
BINARY = ROOT / "dist/HeadlessRendererProbe.app/Contents/MacOS/HeadlessRendererProbe"


def trial(directory):
    directory.mkdir()
    payload = directory / "payload"
    payload.mkdir()
    log = directory / "app.log"
    before = matching_pids(BINARY)
    if before:
        raise RuntimeError("A renderer probe already exists")
    result = {"verdict": "inconclusive", "controllerUID": os.getuid()}
    with log.open("w") as stream:
        process = subprocess.Popen(
            ["open", "-g", "-n", "-W", str(BINARY.parents[2]), "--stdout", str(log),
             "--stderr", str(log), "--args", str(payload)],
            stdout=stream, stderr=stream,
        )
        process.research_existing_pids = before
        try:
            process.wait(timeout=30)
            result["launcherExitCode"] = process.returncode
            lines = [line.removeprefix("HEADLESS_RENDERER_RESULT ")
                     for line in log.read_text().splitlines() if line.startswith("HEADLESS_RENDERER_RESULT ")]
            if len(lines) != 1:
                raise RuntimeError("Expected one complete native report")
            native = json.loads(lines[0])
            result["native"] = native
            services = native.get("servicesAfterSnapshot", {})
            identities_known = all(services.get(name, {}).get("identity")
                                   for name in ("content", "gpu", "network"))
            result["allServiceIdentitiesKnown"] = identities_known
            same_user = identities_known and all(
                all(services[name]["identity"][field] == os.getuid()
                    for field in ("realUID", "effectiveUID", "savedUID"))
                for name in ("content", "gpu", "network"))
            result["allServicesSameUser"] = same_user
            pixels = payload / "snapshot.png"
            if pixels.is_file():
                result["snapshotSHA256"] = hashlib.sha256(pixels.read_bytes()).hexdigest()
            if (process.returncode == 0 and native.get("completed") is True
                    and native.get("javascriptPassed") is True and native.get("snapshotPassed") is True
                    and native.get("serviceIdentityStable") is True
                    and native.get("windowCountAtStart") == 0 and native.get("visibleWindowCountAtEnd") == 0
                    and identities_known and same_user and pixels.is_file()):
                result["verdict"] = "same-user-headless-baseline-passed"
        except (RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
            result["error"] = str(error)
        finally:
            result["cleanupVerified"] = stop_launched(process, BINARY)
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
            if not result["cleanupVerified"]:
                result["verdict"] = "inconclusive"
    (directory / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--repetitions", type=int, default=3, choices=range(1, 4))
    args = parser.parse_args()
    if os.getuid() == 0 or os.geteuid() == 0:
        parser.error("This probe must run as an ordinary user")
    output = args.out.resolve()
    if not output.is_relative_to(ROOT / "artifacts"):
        parser.error("Output must be inside workspace artifacts")
    output.mkdir()
    results = []
    for index in range(args.repetitions):
        result = trial(output / f"trial-{index + 1}")
        results.append(result)
        if result["verdict"] != "same-user-headless-baseline-passed":
            break
        time.sleep(0.2)
    summary = {
        "milestone": 99,
        "scope": "Same-user inline fixture, no window, no input, no privilege, no signal-denial claim",
        "binarySHA256": hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        "requestedTrials": args.repetitions,
        "trials": results,
        "allPassed": len(results) == args.repetitions and all(
            result["verdict"] == "same-user-headless-baseline-passed" and result["cleanupVerified"]
            for result in results),
    }
    (output / "results.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"allPassed": summary["allPassed"], "trials": len(results), "output": str(output)}))


if __name__ == "__main__":
    main()
