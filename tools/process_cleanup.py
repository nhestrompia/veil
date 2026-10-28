"""Stop only verified research executables and wait for their exit."""

import os
import signal
import subprocess
import time


def matching_pids(binary):
    process = subprocess.run(["ps", "-axo", "pid=,comm="], capture_output=True, text=True, check=True)
    rows = [line.strip().split(None, 1) for line in process.stdout.splitlines()]
    return {int(row[0]) for row in rows if len(row) == 2 and row[1] == str(binary)}


def stop_launched(launcher, binary, pid=None):
    if launcher is None:
        return True
    targets = {pid} if pid is not None else matching_pids(binary) - launcher.research_existing_pids
    return all([stop_owned(target, binary) for target in targets])


def process_matches(pid, binary):
    process = subprocess.run(["ps", "-p", str(pid), "-o", "stat=,comm="], capture_output=True, text=True)
    fields = process.stdout.strip().split(None, 1)
    return len(fields) == 2 and not fields[0].startswith("Z") and fields[1] == str(binary)


def stop_owned(pid, binary):
    if pid is None or pid <= 1 or not process_matches(pid, binary):
        return True
    try:
        for action in [signal.SIGTERM, signal.SIGKILL]:
            if not process_matches(pid, binary):
                return True
            os.kill(pid, action)
            deadline = time.monotonic() + 1
            while time.monotonic() < deadline:
                if not process_matches(pid, binary):
                    return True
                time.sleep(0.02)
    except ProcessLookupError:
        return True
    return not process_matches(pid, binary)
