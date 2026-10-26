"""Test independent page clocks against verified suspension of an owned renderer."""

import argparse
import json
import os
from pathlib import Path
import threading

from fixture import FixtureServer
from run_engine_timer_attack import run as timer_attack
from run_native import ROOT


def run(output, engine_root, sources, repetitions):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    server = FixtureServer(("127.0.0.1", 0), ROOT / "tools/feature-fixture.html")
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
    thread.start()
    controller = output / "controller.json"
    controller.touch(mode=0o600)
    controller.write_text(json.dumps({"port": server.server_port, "key": server.controller_key}))
    report = {"scope": "Local performance, wall, dedicated-worker, and independent-server timing channels. No engine clock patch or prevention claim.",
              "serverPID": os.getpid(), "serverPort": server.server_port, "runs": []}
    try:
        for repetition in range(repetitions):
            for source in sources:
                prefix = output / f"{repetition}-{source}"
                row = {"repetition": repetition, "clockSource": source, "status": "inconclusive"}
                report["runs"].append(row)
                try:
                    result = timer_attack(prefix, controller, engine_root, active_animation=True,
                                          intervention="pause", clock_source=source)
                except BaseException as error:
                    row["error"] = f"{type(error).__name__}: {error}"
                    raise
                row["result"] = result
                row["status"] = "recorded"
                print(json.dumps({"repetition": repetition, "clockSource": source,
                                  "statuses": [item["status"] for item in result["modes"]]}), flush=True)
                (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        report["fixtureShutdownVerified"] = not thread.is_alive()
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
        if thread.is_alive():
            raise RuntimeError("The owned clock fixture did not exit")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--engine-frameworks", type=Path, default=ROOT / ".build/webkit-engine/output/Release")
    parser.add_argument("--sources", nargs="+", choices=["performance", "wall", "worker", "server"],
                        default=["performance", "wall", "worker", "server"])
    parser.add_argument("--repetitions", type=int, choices=range(1, 4), default=1)
    args = parser.parse_args()
    run(args.output, args.engine_frameworks, args.sources, args.repetitions)
