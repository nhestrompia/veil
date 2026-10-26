"""Exercise only ordinary-user supervisor controls and prepare an unrun plan."""

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import time

from prepare_renderer_identity_run import APP, ROOT, SUPERVISOR, prepare, stage_script
from process_cleanup import matching_pids


def records(output, prefix):
    return [json.loads(line[len(prefix):]) for line in output.decode().splitlines() if line.startswith(prefix)]


def run_control(output, mode, inherited=False):
    def signals():
        signal.signal(signal.SIGALRM, signal.SIG_IGN)
        signal.signal(signal.SIGCHLD, signal.SIG_IGN)
        signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGALRM, signal.SIGCHLD})
    run = subprocess.run([str(SUPERVISOR), mode], capture_output=True, timeout=36,
                         preexec_fn=signals if inherited else None)
    output.with_suffix(".stdout").write_bytes(run.stdout)
    output.with_suffix(".stderr").write_bytes(run.stderr)
    footer = records(run.stdout, "SUPERVISOR_RESULT ")
    if len(footer) != 1:
        raise RuntimeError("Expected one supervisor lifecycle record")
    result = {"mode": mode, "exitCode": run.returncode, "lifecycle": footer[0], "inheritedSignals": inherited}
    if mode == "--same-user-control":
        native = records(run.stdout, "HEADLESS_RENDERER_RESULT ")
        if len(native) != 1:
            raise RuntimeError("Expected one inline renderer record")
        native = native[0]
        encoded = native.pop("snapshotPNGBase64", "")
        if len(encoded) > 4 * ((2 * 1024 * 1024 + 2) // 3):
            raise RuntimeError("Image exceeds the result limit")
        image = base64.b64decode(encoded, validate=True)
        if not image.startswith(b"\x89PNG\r\n\x1a\n"):
            raise RuntimeError("The result is not a PNG")
        output.with_suffix(".png").write_bytes(image)
        result["imageSHA256"] = hashlib.sha256(image).hexdigest()
        result["native"] = native
        services = native.get("servicesAfterSnapshot", {})
        identities = [native.get("host")] + [services.get(role, {}).get("identity")
                                             for role in ("content", "gpu", "network")]
        result["sameUserCredentials"] = all(identity and all(identity[field] == os.getuid()
            for field in ("realUID", "effectiveUID", "savedUID")) for identity in identities)
        result["verified"] = (run.returncode == 0 and footer[0].get("passed") is True
            and result["sameUserCredentials"] and native.get("completed") is True
            and native.get("javascriptPassed") is True and native.get("snapshotPassed") is True
            and native.get("serviceIdentityStable") is True and native.get("identityControl") is True
            and native.get("explicitSnapshotFileWrites") == 0 and native.get("visibleWindowCountAtEnd") == 0
            and footer[0].get("postExecIdentityObserved") is True)
    else:
        result["verified"] = run.returncode == 1 and footer[0].get("cleanupVerified") is True
        if mode == "--output-limit-control":
            result["verified"] &= footer[0].get("outputLimitExceeded") is True and footer[0]["bytesRelayed"] <= 3 * 1024 * 1024
        elif mode == "--deadline-control":
            result["verified"] &= footer[0].get("deadlineReached") is True
        elif mode == "--watchdog-control":
            result["verified"] &= footer[0].get("hostSignal") == signal.SIGTERM and footer[0].get("watchdogNormalExit") is True
    return result


def fault_control(directory, kind):
    mode = "--same-user-control" if kind == "closed-output" else "--watchdog-control"
    process = subprocess.Popen([str(SUPERVISOR), mode], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, start_new_session=True)
    result = {"kind": kind, "verified": False}
    try:
        data = bytearray()
        wanted = "SUPERVISOR_READY " if kind == "closed-output" else "SUPERVISOR_STOPPED "
        deadline = time.monotonic() + 5
        stage = None
        ready = None
        while time.monotonic() < deadline:
            if not select.select([process.stdout], [], [], 0.2)[0]:
                continue
            block = os.read(process.stdout.fileno(), 8192)
            if not block:
                break
            data.extend(block)
            if len(data) > 65536:
                raise RuntimeError("Unexpected preflight stage size")
            complete = bytes(data).rsplit(b"\n", 1)[0] + b"\n"
            for line in complete.decode().splitlines():
                if line.startswith("SUPERVISOR_READY "):
                    ready = json.loads(line[len("SUPERVISOR_READY "):])
                if line.startswith(wanted):
                    stage = json.loads(line[len(wanted):])
            if stage:
                break
        if not stage or not ready or ready.get("watchdogDetached") is not True:
            raise RuntimeError("The owned-child watchdog was not acknowledged")
        host, watchdog = stage["hostPID"], stage["watchdogPID"]
        result["stage"] = stage
        if os.getpgid(process.pid) != process.pid or os.getsid(watchdog) != watchdog:
            raise RuntimeError("Unexpected research process sessions")
        if kind == "original-group":
            if os.getpgid(host) != process.pid:
                raise RuntimeError("The disposable host left its process group")
            os.killpg(process.pid, signal.SIGTERM)
            expected = -signal.SIGTERM
        elif kind == "parent-only":
            process.kill()
            expected = -signal.SIGKILL
        else:
            process.stdout.close()
            expected = -signal.SIGPIPE
        result["parentExitCode"] = process.wait(timeout=5)
        identities = {process.pid, host, watchdog}
        app_binary = APP / "Contents/MacOS/RendererIdentityProbe"
        deadline = time.monotonic() + 6
        while time.monotonic() < deadline:
            remaining = identities & (matching_pids(SUPERVISOR) | matching_pids(app_binary))
            if not remaining:
                break
            time.sleep(0.05)
        result["remainingPIDs"] = sorted(remaining)
        result["verified"] = result["parentExitCode"] == expected and not remaining
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=3)
        if not process.stdout.closed:
            process.stdout.close()
        process.stderr.close()
        directory.write_text(json.dumps(result, indent=2) + "\n")
    return result


def run(directory):
    if os.getuid() == 0 or os.geteuid() == 0:
        raise ValueError("No privileged preflight is allowed")
    directory = directory.resolve()
    if not directory.is_relative_to(ROOT / "artifacts"):
        raise ValueError("Use a workspace artifact directory")
    directory.mkdir()
    if matching_pids(SUPERVISOR) or matching_pids(APP / "Contents/MacOS/RendererIdentityProbe"):
        raise RuntimeError("An existing research process must remain untouched")
    result = {"milestone": 103, "rootRun": False, "controls": [], "faults": [], "refusals": []}
    try:
        for index in range(3):
            control = run_control(directory / f"inline-{index + 1}", "--same-user-control")
            result["controls"].append(control)
            if not control["verified"]:
                raise RuntimeError("The inline rendering control failed")
        for mode in ("--watchdog-control", "--deadline-control", "--output-limit-control"):
            control = run_control(directory / mode[2:], mode)
            result["controls"].append(control)
            if not control["verified"]:
                raise RuntimeError("A supervisor limit/recovery control failed")
        inherited = run_control(directory / "inherited-signals", "--same-user-control", inherited=True)
        result["controls"].append(inherited)
        if not inherited["verified"]:
            raise RuntimeError("Inherited signal state was not normalized")
        for kind in ("original-group", "parent-only", "closed-output"):
            fault = fault_control(directory / f"fault-{kind}.json", kind)
            result["faults"].append(fault)
            if not fault["verified"]:
                raise RuntimeError("An interrupted supervisor did not recover its child")
        for arguments in (["--root-smoke"], ["--root-smoke", "1"], ["--same-user-control", "501"], ["--unknown"]):
            refused = subprocess.run([str(SUPERVISOR), *arguments], capture_output=True, timeout=3)
            item = {"arguments": arguments, "exitCode": refused.returncode, "emptyOutput": not refused.stdout}
            result["refusals"].append(item)
            if refused.returncode != 64 or refused.stdout:
                raise RuntimeError("An unprivileged forbidden invocation did not refuse")
        result["plan"] = prepare(directory / "reviewed-run-plan.json")
        plan = result["plan"]
        script = stage_script(plan["manifest"], os.getuid(), plan["libraries"], stage_uid=os.getuid())
        rehearsal = subprocess.run(["/usr/bin/env", "-i", "PATH=/usr/bin:/bin:/usr/sbin:/sbin", "LC_ALL=C", "/bin/sh", "-c", script],
                                  capture_output=True, timeout=40)
        (directory / "staging-rehearsal.stdout").write_bytes(rehearsal.stdout)
        (directory / "staging-rehearsal.stderr").write_bytes(rehearsal.stderr)
        staged = records(rehearsal.stdout, "STAGING_RESULT ")
        result["unprivilegedStagingRehearsal"] = {"uid": os.getuid(), "exitCode": rehearsal.returncode, "footer": staged,
            "onlyDifference": "The copy step expects the ordinary stage owner. Administrator mode must still refuse."}
        if rehearsal.returncode or len(staged) != 1 or staged[0].get("helperExitCode") != 64 or staged[0].get("stagingRemoved") is not True:
            raise RuntimeError("The unprivileged staging rehearsal failed")
        result["allPassed"] = True
    except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired, subprocess.CalledProcessError) as error:
        result["error"] = str(error)
        result["allPassed"] = False
    finally:
        result["remainingSupervisorPIDs"] = sorted(matching_pids(SUPERVISOR))
        result["remainingProbePIDs"] = sorted(matching_pids(APP / "Contents/MacOS/RendererIdentityProbe"))
        result["allPassed"] = result.get("allPassed", False) and not result["remainingSupervisorPIDs"] and not result["remainingProbePIDs"]
        (directory / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = run(args.out)
    print(json.dumps({key: result.get(key) for key in ("allPassed", "error", "rootRun", "remainingSupervisorPIDs", "remainingProbePIDs")}))
