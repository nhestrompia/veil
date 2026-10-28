"""Reject prevention claims when an attack succeeds or evidence is incomplete."""

import argparse
import json


def assess(results):
    if any(r.get("verdict") == "bypass" or r.get("disclosure") is True for r in results):
        return "failed", "At least one attack disclosed content or completed an action"
    if not results or any(r.get("verdict") != "blocked" for r in results):
        return "inconclusive", "Every required route needs an explicit defensive block and working control"
    if any(r.get("controlWorked") is not True for r in results):
        return "inconclusive", "A working positive control is missing"
    return "passed", "All supplied routes recorded explicit blocks with working controls"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("report")
    args = parser.parse_args()
    with open(args.report) as file:
        status, reason = assess(json.load(file)["results"])
    print(json.dumps({"prevention": status, "reason": reason}))
    raise SystemExit(0 if status == "passed" else 1)
