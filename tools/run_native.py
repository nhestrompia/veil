"""Run external native attacks and score them with the loopback oracle."""

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path
from urllib.request import Request, urlopen

from native_environment import observe_console, action_verdict

ROOT = Path(__file__).resolve().parent.parent


def probe(arguments, output):
    output = output.resolve()
    output.unlink(missing_ok=True)
    completed = subprocess.run(["open", "-n", "-W", str(ROOT / "dist/NativeProbe.app"), "--args", *map(str, arguments), "--out", str(output)],
                               timeout=40, capture_output=True)
    if not output.exists():
        raise RuntimeError(f"Probe launch failed: {completed.stderr.decode().strip()}")
    result = json.loads(output.read_text())
    result["probeBinarySHA256"] = hashlib.sha256((ROOT / "dist/NativeProbe.app/Contents/MacOS/NativeProbe").read_bytes()).hexdigest()
    return result


class Oracle:
    def __init__(self):
        self.config = json.loads((ROOT / "artifacts/fixture-controller.json").read_text())

    def request(self, path, body=None):
        request = Request(f"http://127.0.0.1:{self.config['port']}" + path,
                          data=None if body is None else json.dumps(body).encode(),
                          headers={"X-Research-Key": self.config["key"]})
        with urlopen(request, timeout=5) as response:
            return json.load(response)

    def create(self):
        return self.request("/admin/trials", {})

    def state(self, trial):
        return self.request("/admin/trials/" + trial["id"])


def run(targets, routes, repetitions, output):
    output.mkdir(parents=True, exist_ok=True)
    environment = observe_console()
    oracle = Oracle()
    permissions = probe(["permissions"], output / "permissions.json")
    if not permissions.get("accessibility") or not permissions.get("postEvents"):
        (output / "results.json").write_text(json.dumps({"permissions": permissions, "results": [
            {"route": "permission-preflight", "verdict": "inconclusive", "error": "Probe requires effective Accessibility and event-posting grants"}
        ]}, indent=2))
        print("Permission preflight failed. No attacks ran.", flush=True)
        return []
    results = []
    control_target = "InspectableControl" if "InspectableControl" in targets else "AgentFreeBrowser"
    targets = sorted(targets, key=lambda target: target != control_target)
    for name in targets:
        binary = ROOT / f"dist/{name}.app/Contents/MacOS/{name}"
        binary_hash = hashlib.sha256(binary.read_bytes()).hexdigest()
        for route in routes:
            for repetition in range(repetitions):
                prefix = output / f"{name}-{route}-{repetition}"
                trial = oracle.create()
                result = {"target": name, "route": route, "repetition": repetition, "trial": trial["id"],
                          "binarySHA256": binary_hash, "verdict": "inconclusive"}
                with prefix.with_suffix(".log").open("w") as log:
                    process = subprocess.Popen([str(binary), "--url", trial["url"]], stdout=log, stderr=log)
                    try:
                        tree = {}
                        for _ in range(12):
                            time.sleep(0.3)
                            tree = probe(["ax", process.pid], prefix.with_suffix(".ax.json"))
                            if route == "blind-fixture" and name != control_target:
                                time.sleep(1)
                                break
                            if any((e.get("AXDescription") == "Enter native-input" or e.get("AXTitle") == "Enter native-input") and e.get("AXRole") == "AXTextField" for e in tree.get("elements", [])):
                                break
                        state = oracle.state(trial)
                        result["disclosure"] = state["secret"] in json.dumps(tree)
                        if route == "ax":
                            attempt = probe(["ax-action", process.pid], prefix.with_suffix(".attempt.json"))
                            time.sleep(0.3)
                            second = probe(["ax-action", process.pid], prefix.with_suffix(".retry.json"))
                            attempt = {"first": attempt, "retry": second}
                        else:
                            if route == "blind-fixture" and name != control_target:
                                control = next((r for r in results if r["target"] == control_target and r["route"] == route and
                                    r["repetition"] == repetition and r["verdict"] == "bypass"), None)
                                if not control or "fieldCenter" not in control:
                                    raise RuntimeError("Known-layout route needs a matched working control")
                                point = control["fieldCenter"]
                                result["coordinateSource"] = "Prior control of the public fixture; no target AX coordinates or screenshot"
                            else:
                                field = next((e for e in tree.get("elements", []) if (e.get("AXDescription") == "Enter native-input" or e.get("AXTitle") == "Enter native-input") and e.get("AXRole") == "AXTextField"), None)
                                if not field:
                                    raise RuntimeError("Cannot locate fixture field; no action-prevention result")
                                x, y = field["position"]
                                width, height = field["size"]
                                point = [x + width / 2, y + height / 2]
                                result["fieldCenter"] = point
                            source = "hid" if route == "blind-fixture" else route.rsplit("-", 1)[-1]
                            if route.startswith("iohid-"):
                                args = ["hid-post-input", process.pid, *point, route.removeprefix("iohid-")]
                            else:
                                args = ["input", process.pid, *point, source]
                            if route.startswith("pid-window-"):
                                args.append("pid-window")
                            elif route.startswith("pid-keys-"):
                                args.append("pid-keys")
                            elif route.startswith("pid-"):
                                args.append("pid")
                            if route.startswith("curve-"):
                                args.append("curve")
                            if "keycodes" in route.split("-"):
                                args.append("keycodes")
                            attempt = probe(args, prefix.with_suffix(".attempt.json"))
                        time.sleep(0.5)
                        state = oracle.state(trial)
                        prefix.with_suffix(".oracle.json").write_text(json.dumps(state, indent=2))
                        result.update(attempt=attempt, submissions=state["submissions"],
                                      inputTrustedValues=sorted(set(e["trusted"] for e in state["events"] if e["type"] == "input")))
                        event_log = prefix.with_suffix(".log").read_text()
                        secure_events = [line for line in event_log.splitlines() if line.startswith("SECURE_INPUT_EVENT")]
                        result["secureInputEvents"] = {"enabled": sum("effective=true" in line for line in secure_events),
                                                       "disabled": sum("effective=false" in line for line in secure_events)}
                        result["inputGate"] = {"acceptedEvents": event_log.count("INPUT_GATE_ACCEPTED"),
                                               "refusedEvents": event_log.count("INPUT_GATE_REFUSED")}
                        completed = any(s["accepted"] for s in state["submissions"])
                        result["controlWorked"] = any(r["target"] == control_target and r["route"] == route and
                            r["repetition"] == repetition and r["verdict"] == "bypass" for r in results)
                        result["verdict"] = action_verdict(completed, result["inputGate"]["refusedEvents"] > 0, result["controlWorked"])
                        if result["inputGate"]["refusedEvents"]:
                            result["reason"] = "Defensive refusal recorded. A matched working control is required for a block verdict."
                        elif not completed and attempt.get("error"):
                            result["reason"] = attempt["error"]
                        elif not completed:
                            result["reason"] = "No task completion; no explicit defensive refusal established"
                        if name == "DeviceKeyboardExperiment" and not completed and "DEVICE_KEYBOARD bound=true" not in event_log:
                            result["verdict"] = "inconclusive"
                            result["reason"] = "No physical device binding. Rejected input alone cannot establish usable protection."
                    except (RuntimeError, KeyError, OSError, subprocess.SubprocessError) as error:
                        result["error"] = str(error)
                    finally:
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait()
                results.append(result)
                print(json.dumps({k: result[k] for k in ["target", "route", "repetition", "verdict", "disclosure"] if k in result}), flush=True)
                summary = {"permissions": permissions, "environment": environment, "positiveControlTarget": control_target,
                           "system": subprocess.check_output(["sw_vers"], text=True),
                           "results": results, "humanBaseline": False,
                           "routeContract": "Probe uses native APIs only. Controller alone queries the oracle. Input coordinates come from AX, except blind-fixture uses the matched control coordinates."}
                (output / "results.json").write_text(json.dumps(summary, indent=2))
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--targets", nargs="+", default=["AgentFreeBrowser", "InspectableControl"], choices=["AgentFreeBrowser", "InspectableControl", "MetadataExperiment", "SecureInputExperiment", "ReducedExposureExperiment", "AXBoundaryExperiment", "DeviceKeyboardExperiment"])
    parser.add_argument("--routes", nargs="+", default=["ax", "session", "hid", "private", "pid-hid", "curve-hid", "keycodes-hid", "blind-fixture"], choices=["ax", "session", "hid", "private", "pid-hid", "curve-hid", "keycodes-hid", "blind-fixture", "iohid-legacy", "iohid-reports", "pid-keys-hid", "pid-keys-keycodes-hid", "pid-window-keycodes-hid"])
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/native-pilot")
    args = parser.parse_args()
    run(args.targets, args.routes, args.repetitions, args.output)
