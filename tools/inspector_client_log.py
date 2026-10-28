"""Reduce the research client's own logs to fixed event categories."""

import json
import re
import subprocess

from run_native import ROOT


def classify(rows):
    connections = {}
    for row in rows:
        if not isinstance(row, dict) or row.get("subsystem") != "com.apple.xpc":
            continue
        message = row.get("eventMessage")
        if not isinstance(message, str):
            continue
        handle = re.match(r"^\[(0x[0-9a-f]+)\]", message)
        if handle and message.endswith("name=com.apple.webinspector.debugger"):
            connections.setdefault(handle[1], len(connections) + 1)
    events = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        message = row.get("eventMessage")
        if not isinstance(message, str):
            continue
        handle = re.match(r"^\[(0x[0-9a-f]+)\]", message)
        event = None
        if row.get("subsystem") == "com.apple.WebInspector":
            if message == "webinspectord validation failed":
                event = "webinspectord-validation-failed"
            elif message.startswith("Created CURRENTMACHINE target:"):
                event = "current-machine-target-created"
        elif row.get("subsystem") == "com.apple.xpc" and handle and handle[1] in connections:
            if message.endswith("name=com.apple.webinspector.debugger"):
                event = "debugger-connection-activated"
            elif "XPC_ERROR_CONNECTION_INTERRUPTED" in message:
                event = "debugger-connection-interrupted"
            elif "invalidated" in message:
                event = "debugger-connection-invalidated"
        if event:
            entry = {"event": event}
            if handle and handle[1] in connections:
                entry["connection"] = connections[handle[1]]
            events.append(entry)
    return {"matchingLogRecords": len(rows), "rawMessagesSaved": False,
            "events": events[:64], "eventLimitReached": len(events) > 64}


def observe(pid):
    if type(pid) is not int or pid <= 1:
        raise ValueError("Use the research helper PID from its saved report")
    image = ROOT / ".build/inspector-discovery-control"
    predicate = (f"processIdentifier == {pid} AND processImagePath == {json.dumps(str(image))} "
                 'AND (subsystem == "com.apple.xpc" OR senderImagePath CONTAINS "/WebInspector.framework/")')
    completed = subprocess.run(["/usr/bin/log", "show", "--style", "json", "--last", "20m",
                                "--info", "--debug", "--predicate", predicate],
                               capture_output=True, text=True, timeout=15)
    result = {"probePID": pid, "exactImageFilter": str(image), "logExitCode": completed.returncode,
              "daemonLogsRead": False, "unrelatedProcessLogsRead": False}
    if completed.returncode != 0:
        result["status"] = "unavailable"
        return result
    try:
        rows = json.loads(completed.stdout)
        if not isinstance(rows, list):
            raise ValueError("Unexpected log response")
        result.update(classify(rows), status="observed")
    except ValueError:
        result["status"] = "invalid-response"
    return result
