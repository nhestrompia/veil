"""Collect synthetic input controls without claiming a physical baseline or a defense."""

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from native_environment import observe_console
from run_native import ROOT, probe


def run(routes, repetitions, output):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    summary = {"results": [], "humanBaselineVerified": False, "isInputDefense": False,
               "physicalInputAbsenceVerified": False,
               "routeContract": "Own native form. External AX locates the field; CGEvent types the fake value and Return. Device values and app events are separate observations."}

    def save():
        (output / "results.json").write_text(json.dumps(summary, indent=2))

    summary["environment"] = observe_console()
    app = ROOT / "dist/HIDObservation.app"
    for route in routes:
        for repetition in range(repetitions):
            prefix = output / f"{route}-{repetition}"
            dataset = prefix.with_suffix(".observations.json")
            dataset.unlink(missing_ok=True)
            launcher = subprocess.Popen(["open", "-n", "-W", str(app), "--args", "--observe",
                "--duration", "8", "--out", str(dataset)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            pid = None
            record = {"route": route, "repetition": repetition, "verdict": "inconclusive"}
            try:
                deadline = time.monotonic() + 8
                while not dataset.exists() and time.monotonic() < deadline:
                    time.sleep(0.1)
                if not dataset.exists():
                    raise RuntimeError("Observer has no ready file")
                ready = json.loads(dataset.read_text())
                pid = ready["pid"]
                if not ready["collecting"]:
                    raise RuntimeError("Input Monitoring grant is absent or observation did not start")
                tree = probe(["ax", pid], prefix.with_suffix(".ax.json"))
                field = next((e for e in tree.get("elements", []) if e.get("AXRole") == "AXTextField" and
                    (e.get("AXTitle") == "Enter native-input" or e.get("AXDescription") == "Enter native-input")), None)
                if not field:
                    raise RuntimeError("Observer field not found; no source comparison")
                x, y = field["position"]
                width, height = field["size"]
                args = ["input", pid, x + width / 2, y + height / 2,
                        route.removeprefix("curve-").removeprefix("keycodes-")]
                if route.startswith("curve-"):
                    args.append("curve")
                if route.startswith("keycodes-"):
                    args.append("keycodes")
                record["attempt"] = probe(args, prefix.with_suffix(".input.json"))
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline:
                    data = json.loads(dataset.read_text())
                    if not data["collecting"]:
                        break
                    time.sleep(0.2)
                record["acceptedFakeActions"] = data["acceptedFakeActions"]
                record["recordLimitReached"] = data["recordLimitReached"]
                record["deviceCategories"] = dict(Counter(e["category"] for e in data["records"] if e["origin"] == "device-value"))
                record["appEventTypes"] = dict(Counter(str(e["type"]) for e in data["records"] if e["origin"] == "app-event"))
                if data["acceptedFakeActions"] > 0 and not data["collecting"]:
                    record["verdict"] = "observed"
                else:
                    record["reason"] = "Synthetic action control or bounded collection did not complete"
            except (RuntimeError, OSError, KeyError, subprocess.SubprocessError) as error:
                record["error"] = str(error)
            finally:
                if pid is not None:
                    try:
                        os.kill(pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                launcher.terminate()
                try:
                    launcher.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    launcher.kill()
                    launcher.wait()
            summary["results"].append(record)
            save()
            print(json.dumps(record), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--routes", nargs="+", choices=["session", "hid", "private", "curve-hid", "keycodes-hid"],
                        default=["session", "hid", "private", "curve-hid", "keycodes-hid"])
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/hid-synthetic")
    args = parser.parse_args()
    run(args.routes, args.repetitions, args.output)
