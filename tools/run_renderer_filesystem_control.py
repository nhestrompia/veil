"""Compare fixed canary writes and headless rendering in disposable apps."""

import argparse
import base64
import errno
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from process_cleanup import matching_pids, stop_launched
from run_headless_renderer_probe import collect_stdout


ROOT = Path(__file__).resolve().parents[1]
MARKER = b"AFB-filesystem-control\n"
ADDITION = b"AFB-test-write\n"
PREFIX = b"HEADLESS_RENDERER_RESULT "
READER = ROOT / ".build/renderer-metadata-read"


def collect_report_file(process, path, receive):
    deadline = time.monotonic() + 30
    position = 0
    output = bytearray()
    line_start = 0
    while True:
        if path.exists():
            if path.stat().st_size > 3 * 1024 * 1024:
                raise RuntimeError("Native report exceeds the result limit")
            with path.open("rb") as stream:
                stream.seek(position)
                block = stream.read(3 * 1024 * 1024 + 1)
            position += len(block)
            if len(output) + len(block) > 3 * 1024 * 1024:
                raise RuntimeError("Native report exceeds the result limit")
            output.extend(block)
            while (end := output.find(b"\n", line_start)) >= 0:
                receive(bytes(output[line_start:end]))
                line_start = end + 1
        if process.poll() is not None:
            return bytes(output)
        if time.monotonic() >= deadline:
            raise subprocess.TimeoutExpired(process.args, 30)
        time.sleep(0.05)


def external_identity(host_pid, native):
    before = native.get("servicesBeforeSnapshot", {})
    after = native.get("servicesAfterSnapshot", {})
    roles = ("content", "gpu", "network")
    pids = [after.get(role, {}).get("pid") for role in roles]
    if any(type(pid) is not int or pid <= 1 for pid in pids):
        raise RuntimeError("A service PID is unknown")
    if any(before.get(role, {}).get("pid") != pid for role, pid in zip(roles, pids)):
        raise RuntimeError("A service PID changed during the snapshot")
    records = []
    for _ in range(2):
        read = subprocess.run([str(READER), str(host_pid), *map(str, pids)], capture_output=True, timeout=2)
        if read.returncode:
            raise RuntimeError(f"External identity reader refused: {read.returncode}")
        records.append(json.loads(read.stdout))
    return {"first": records[0], "second": records[1], "stable": records[0] == records[1],
            "rolePIDSource": "owner-side-private-getters",
            "rolesResponsibleToHost": all(records[0][role]["responsiblePID"] == host_pid for role in roles),
            "rolesShareHostResponsibility": all(records[0][role]["responsiblePID"]
                == records[0]["host"]["responsiblePID"] for role in roles)}


def trial(directory, kind, launch_services=False):
    directory.mkdir()
    payload = directory / "payload"
    payload.mkdir()
    canary = payload / "outside-canary"
    canary.write_bytes(MARKER)
    canary.chmod(0o600)
    name = "RendererFilesystem" + kind
    binary = ROOT / f"dist/{name}.app/Contents/MacOS/{name}"
    existing = matching_pids(binary)
    if existing:
        raise RuntimeError("A filesystem research app already exists")
    result = {"kind": kind, "verdict": "inconclusive", "controllerUID": os.getuid(),
              "launchMethod": "launch-services" if launch_services else "direct-exec",
              "binarySHA256": hashlib.sha256(binary.read_bytes()).hexdigest()}
    native = None
    process = None

    def receive(line):
        nonlocal native
        if not line.startswith(PREFIX):
            return
        if native is not None:
            raise RuntimeError("Duplicate native report")
        native = json.loads(line[len(PREFIX):])
        try:
            host_pid = native.get("host", {}).get("pid") if launch_services else process.pid
            if type(host_pid) is not int or host_pid <= 1:
                raise RuntimeError("The research host PID is unknown")
            result["externalIdentity"] = external_identity(host_pid, native)
        except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired) as error:
            result["externalIdentityError"] = str(error)

    with (directory / "stderr.log").open("wb") as error_stream:
        arguments = ["--pipe-only", "--canary", str(canary)]
        stdout_path = directory / "stdout.log"
        if launch_services:
            process = subprocess.Popen(["open", "-g", "-n", "-W", str(binary.parents[2]),
                                       "--stdout", str(stdout_path), "--stderr", str(directory / "stderr.log"),
                                       "--args", *arguments], stdout=subprocess.DEVNULL, stderr=error_stream)
        else:
            process = subprocess.Popen([str(binary), *arguments], cwd=payload,
                                       stdout=subprocess.PIPE, stderr=error_stream)
        process.research_existing_pids = existing
        result["launchedPID"] = process.pid
        try:
            if launch_services:
                collect_report_file(process, stdout_path, receive)
            else:
                output = collect_stdout(process, on_line=receive)
                stdout_path.write_bytes(output)
            result["exitCode"] = process.returncode
            if native is None:
                raise RuntimeError("No native report")
            result["native"] = native
            filesystem = native.get("filesystemControl", {})
            outside = filesystem.get("outside", {})
            temporary = filesystem.get("temporaryFile", {})
            actual = canary.read_bytes()
            result["canarySHA256After"] = hashlib.sha256(actual).hexdigest()
            result["canaryMatchedExpected"] = actual == (MARKER + ADDITION if kind == "Reference" else MARKER)
            result["outsideWriteControlPassed"] = (
                outside.get("status") == "appended" if kind == "Reference" else
                outside.get("status") == "open-denied" and outside.get("errno") in (errno.EACCES, errno.EPERM))
            result["temporaryFileControlPassed"] = all(temporary.get(key) is True for key in
                                                       ("created", "written", "readMatched", "removed"))
            encoded = native.pop("snapshotPNGBase64", "")
            if len(encoded) > 4 * ((2 * 1024 * 1024 + 2) // 3):
                raise RuntimeError("Image exceeds the result limit")
            image = base64.b64decode(encoded, validate=True)
            if image.startswith(b"\x89PNG\r\n\x1a\n"):
                (payload / "snapshot.png").write_bytes(image)
                result["snapshotSHA256"] = hashlib.sha256(image).hexdigest()
            else:
                raise RuntimeError("Missing PNG result")
            observation = result.get("externalIdentity", {})
            result["nativeRoleIdentitiesKnown"] = all(
                native.get("servicesAfterSnapshot", {}).get(role, {}).get("identity") is not None
                for role in ("content", "gpu", "network"))
            if (process.returncode == 0 and native.get("completed") is True
                    and native.get("javascriptPassed") is True and native.get("snapshotPassed") is True
                    and native.get("serviceIdentityStable") is True
                    and native.get("visibleWindowCountAtEnd") == 0
                    and native.get("explicitSnapshotFileWrites") == 0
                    and filesystem.get("canaryPath") == str(canary)
                    and result["canaryMatchedExpected"] and result["outsideWriteControlPassed"]
                    and result["temporaryFileControlPassed"] and observation.get("stable") is True
                    and observation.get("rolePIDSource") == "owner-side-private-getters"):
                result["verdict"] = "reference-control-passed" if kind == "Reference" else "sandbox-control-passed"
        except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired) as error:
            result["error"] = str(error)
            if native is not None:
                native.pop("snapshotPNGBase64", None)
                result["native"] = native
        finally:
            result["cleanupVerified"] = stop_launched(process, binary)
            if process.poll() is None:
                process.kill()
            process.wait(timeout=2)
            if process.stdout is not None:
                process.stdout.close()
            if not result["cleanupVerified"]:
                result["verdict"] = "inconclusive"
    (directory / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--repetitions", type=int, choices=range(1, 4), default=3)
    parser.add_argument("--launch-services", action="store_true")
    parser.add_argument("--sandbox-kind", choices=("Sandbox", "NetworkSandbox"), default="Sandbox")
    args = parser.parse_args()
    if os.getuid() == 0 or os.geteuid() == 0:
        parser.error("Run only as the ordinary research user")
    directory = args.out.resolve()
    if not directory.is_relative_to(ROOT / "artifacts"):
        parser.error("Output must be inside workspace artifacts")
    directory.mkdir()
    results = []
    for index in range(args.repetitions):
        reference = trial(directory / f"pair-{index + 1}-reference", "Reference", args.launch_services)
        results.append(reference)
        if reference["verdict"] != "reference-control-passed":
            break
        sandbox = trial(directory / f"pair-{index + 1}-sandbox", args.sandbox_kind, args.launch_services)
        results.append(sandbox)
        if sandbox["verdict"] != "sandbox-control-passed":
            break
    summary = {"milestone": 102, "scope": "Same-user host App Sandbox controls; no service-wide or cross-user isolation claim",
               "requestedPairs": args.repetitions, "sandboxKind": args.sandbox_kind, "trials": results,
               "metadataReaderSHA256": hashlib.sha256(READER.read_bytes()).hexdigest(),
               "allPassed": len(results) == 2 * args.repetitions and all(
                   item["verdict"] != "inconclusive" and item["cleanupVerified"] for item in results)}
    (directory / "results.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"allPassed": summary["allPassed"], "trials": len(results), "output": str(directory)}))


if __name__ == "__main__":
    main()
