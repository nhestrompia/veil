"""Exercise safe refusals without creating an Endpoint Security client."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from run_native import ROOT


def command(helper, arguments):
    result = subprocess.run([str(helper), *arguments], capture_output=True, text=True, timeout=5)
    return {"exitCode": result.returncode, "result": json.loads(result.stdout)}


def run(output):
    output = output.resolve()
    if not output.is_relative_to(ROOT / "artifacts"):
        raise RuntimeError("Preflight evidence must stay in workspace artifacts")
    output.mkdir(parents=True, exist_ok=False)
    helper = ROOT / ".build/signal-authorization"
    target = ROOT / ".build/signal-signing-control/hardened"
    report = {"enforcementVerified": False, "clientCreated": False, "cases": [],
              "helperSHA256": hashlib.sha256(helper.read_bytes()).hexdigest()}

    def manifest(name, data, mode=0o600):
        folder = output / name
        folder.mkdir()
        path = folder / "signal-target.json"
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
        with os.fdopen(descriptor, "w") as stream:
            stream.write(data)
        os.chmod(path, mode)
        return path

    def refusal(name, path, expected):
        row = {"case": name, **command(helper, ["--run", str(path)])}
        row["passed"] = row["exitCode"] == 1 and row["result"].get("error") == expected
        report["cases"].append(row)
        if not row["passed"]:
            raise RuntimeError("The preflight helper did not return the expected safe refusal")

    process = None
    try:
        report["preflight"] = command(helper, ["--preflight"])
        state = report["preflight"]["result"]
        if state.get("endpointSecurityEntitlement") or state.get("runningAsRoot"):
            raise RuntimeError("This refusal test requires an unentitled, unprivileged helper. Do not run live enforcement here.")
        if state.get("clientCreated") or state.get("eventsSubscribed"):
            raise RuntimeError("The preflight unexpectedly created an ES client")
        with (output / "target.jsonl").open("w") as stream:
            process = subprocess.Popen([str(target)], stdout=stream, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline and not (output / "target.jsonl").stat().st_size:
            time.sleep(0.02)
        snapshot = command(helper, ["--target", str(process.pid)])
        if snapshot["exitCode"] or snapshot["result"].get("path") != str(target) or snapshot["result"].get("pid") != process.pid:
            raise RuntimeError("The owned disposable target did not produce a scoped snapshot")
        report["targetSnapshot"] = snapshot["result"]
        raw = json.dumps(snapshot["result"]) + "\n"
        good = manifest("valid", raw)
        refusal("missing-prerequisites", good, "missingPrerequisites")
        refusal("public-manifest", manifest("public", raw, 0o644), "invalidManifest")
        refusal("oversized-manifest", manifest("oversized", " " * 8193), "invalidManifest")
        stale = {**snapshot["result"], "startedSeconds": snapshot["result"]["startedSeconds"] + 1}
        refusal("stale-process-identity", manifest("stale", json.dumps(stale)), "invalidTarget")
        alias = output / "alias"
        alias.mkdir()
        link = alias / "signal-target.json"
        link.symlink_to(good)
        refusal("symlink-manifest", link, "invalidManifest")
        wrong_name = good.parent / "other.json"
        wrong_name.write_text(raw)
        refusal("wrong-manifest-name", wrong_name, "invalidManifest")
        process.wait(timeout=6)
        report["targetExitCode"] = process.returncode
        if process.returncode != 0:
            raise RuntimeError("The disposable target did not exit normally")
        report["status"] = "safe-refusals-verified"
        print(json.dumps({"status": report["status"], "casesPassed": len(report["cases"]),
                          "enforcementVerified": False}), flush=True)
        return report
    finally:
        if process:
            try:
                process.wait(timeout=6)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
            report["targetCleanupVerified"] = process.poll() is not None
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
