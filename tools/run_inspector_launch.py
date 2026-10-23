"""Measure the installed WebKit preference and the process-local startup policy."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def run(output, repetitions):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    app = ROOT / "dist/InspectorLaunchControl.app"
    binary = app / "Contents/MacOS/InspectorLaunchControl"
    results = []
    for repetition in range(repetitions):
        for argument, apply_policy in [("NO", False), ("YES", False), ("YES", True)]:
            path = output / f"{repetition}-{argument}-{apply_policy}.json"
            path.unlink(missing_ok=True)
            command = ["open", "-n", "-W", str(app), "--args",
                       "-WebKitDebugDeveloperExtrasEnabled", argument,
                       "-ResearchSentinel", "preserve-me", "--out", str(path)]
            if apply_policy:
                command.append("--apply-policy")
            subprocess.run(command, check=True, timeout=20)
            result = json.loads(path.read_text())
            result.update(argument=argument, repetition=repetition)
            expected = argument == "YES" and not apply_policy
            result["passed"] = (result["getterSupported"]
                                and result["requestedLaunchDefault"] == (argument == "YES")
                                and result["developerExtrasEnabled"] == expected
                                and result["effectiveLaunchDefault"] == expected
                                and not result["isInspectable"]
                                and result["unrelatedArgumentPreserved"]
                                and (not apply_policy or result["policyAccepted"]))
            results.append(result)
    report = {"binarySHA256": hashlib.sha256(binary.read_bytes()).hexdigest(), "runs": results,
              "scope": "Installed framework property calibration. No external inspector attachment or browser bypass claim."}
    (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"runs": len(results), "passed": sum(item["passed"] for item in results)}))
    if not all(item["passed"] for item in results):
        raise RuntimeError("Inspector preference calibration failed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/inspector-launch")
    parser.add_argument("--repetitions", type=int, choices=range(1, 6), default=3)
    args = parser.parse_args()
    run(args.output, args.repetitions)
