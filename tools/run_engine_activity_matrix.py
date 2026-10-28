"""Compare native and projected activity on the same isolated WebKit build."""

import argparse
import json
from pathlib import Path
import subprocess

from engine_runtime import engine_environment
from process_cleanup import matching_pids
from run_focus_attack import run as run_focus
from run_native import ROOT


CASES = [
    ("password-focus", "focus-action", True, None),
    ("blur", "blur-action", False, None),
    ("visibility", "visibility-action", False, None),
    *[(f"{frame}-{kind}", f"{kind}-action", False, frame)
      for frame in ["iframe", "cross-frame", "srcdoc"] for kind in ["focus", "visibility"]],
]


def build_diagnostic(mode, output, resume=True):
    for name in ["InternalKeyboardControl", "InspectableControl"]:
        binary = ROOT / f"dist/{name}.app/Contents/MacOS/{name}"
        if matching_pids(binary):
            raise RuntimeError("A disposable research app exists before the diagnostic build")
    command = ["/bin/bash", str(ROOT / "scripts/diagnose-browser-keyboard.sh"),
               "--feature-suite", "--capture-restricted", "--owner-readback",
               f"--engine-{mode}", "--build-only"]
    if resume:
        command.append("--focus-resume")
    with output.open("w") as stream:
        subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                       timeout=120, check=True)


def run(output, controller, engine_root, cases):
    engine_environment(engine_root)
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    report = {"humanBaseline": False,
              "scope": "Disposable local lifecycle comparisons. Private typing is a routing control, not physical-human proof.",
              "engineRoot": str(engine_root.resolve()), "cases": []}
    native = {}

    def save():
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    save()
    try:
        for mode in ["native", "stable"]:
            build_diagnostic(mode, output / f"build-{mode}.log")
            for name, surface, password, frame in CASES:
                if name not in cases:
                    continue
                row = {"case": name, "mode": mode, "status": "running"}
                report["cases"].append(row)
                save()
                if mode == "stable" and native.get(name, {}).get("status") != "autonomous-website-action":
                    row.update(status="inconclusive", skipped=True,
                               reason="The matched native-engine trial did not reproduce an autonomous action")
                    save()
                    continue
                try:
                    result = run_focus(output / f"{mode}-{name}", controller, 1, surface,
                                       True, password, True, engine_root, frame, True)
                    trial = result["runs"][0]
                    if mode == "native":
                        native[name] = trial
                    row.update(status=trial["status"],
                               acceptedInputEvents=trial.get("candidate", {}).get("acceptedInputEvents"),
                               privateResumeCompleted=trial.get("privateResumeCompleted", False),
                               privateResumeNewActions=trial.get("privateResumeNewActions"),
                               candidateCleanupVerified=trial.get("candidateCleanupVerified", False),
                               sinkCleanupVerified=trial.get("sinkCleanupVerified", False),
                               secureInputAfterCleanup=trial.get("secureInputAfterCleanup"),
                               evidence=str(output / f"{mode}-{name}" / "results.json"))
                    if not row["candidateCleanupVerified"] or not row["sinkCleanupVerified"]:
                        raise RuntimeError("A lifecycle comparison did not verify process cleanup")
                    if not row["privateResumeCompleted"] or row["privateResumeNewActions"] != 1:
                        row["reason"] = "The private resume control did not complete exactly one action"
                        if row["status"] != "autonomous-website-action":
                            row["status"] = "inconclusive"
                        if mode == "native":
                            native.pop(name, None)
                    print(json.dumps(row), flush=True)
                    if mode == "stable" and row["status"] == "autonomous-website-action":
                        report["stopReason"] = "Stable activity allowed an autonomous website action"
                        return report
                except BaseException as error:
                    row.update(status="inconclusive", error=f"{type(error).__name__}: {error}")
                    raise
                finally:
                    save()
        return report
    finally:
        save()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--controller", type=Path, default=ROOT / "artifacts/page-feature-controller.json")
    parser.add_argument("--engine-frameworks", type=Path, default=ROOT / ".build/webkit-engine/output/Release")
    parser.add_argument("--cases", nargs="+", choices=[case[0] for case in CASES], default=[case[0] for case in CASES])
    args = parser.parse_args()
    run(args.output, args.controller, args.engine_frameworks, args.cases)
