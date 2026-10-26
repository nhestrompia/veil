"""Measure an ordinary-user WKWebView with no window or external input."""

import argparse
import base64
from contextlib import nullcontext
import hashlib
import json
import os
from pathlib import Path
import selectors
import subprocess
import time

from process_cleanup import matching_pids, stop_launched
from headless_renderer_fixture import serve_renderer_fixture


ROOT = Path(__file__).resolve().parents[1]
BINARY = ROOT / "dist/HeadlessRendererProbe.app/Contents/MacOS/HeadlessRendererProbe"


def collect_stdout(process, limit=3 * 1024 * 1024, timeout=30):
    deadline = time.monotonic() + timeout
    output = bytearray()
    with selectors.DefaultSelector() as reader:
        reader.register(process.stdout, selectors.EVENT_READ)
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise subprocess.TimeoutExpired(process.args, timeout)
            if not reader.select(timeout=min(remaining, 0.25)):
                continue
            block = os.read(process.stdout.fileno(), 65536)
            if not block:
                break
            if len(output) + len(block) > limit:
                raise RuntimeError("Native result exceeds the report limit")
            output.extend(block)
    process.wait(timeout=max(0.001, deadline - time.monotonic()))
    return bytes(output)


def trial(directory, fixture=None, pipe_only=False):
    directory.mkdir()
    payload = directory / "payload"
    payload.mkdir()
    log = directory / "app.log"
    before = matching_pids(BINARY)
    if before:
        raise RuntimeError("A renderer probe already exists")
    result = {"verdict": "inconclusive", "controllerUID": os.getuid()}
    expected_verdict = ("same-user-loopback-baseline-passed" if fixture else
                        "same-user-pipe-baseline-passed" if pipe_only else "same-user-headless-baseline-passed")
    arguments = ["--pipe-only"] if pipe_only else [str(payload)]
    if fixture:
        arguments += ["--loopback-port", str(fixture.server_port)]
    with log.open("w") as stream:
        if pipe_only:
            process = subprocess.Popen([str(BINARY), *arguments], cwd=payload,
                                       stdout=subprocess.PIPE, stderr=stream)
            result["launchMethod"] = "direct-exec"
        else:
            process = subprocess.Popen(
                ["open", "-g", "-n", "-W", str(BINARY.parents[2]), "--stdout", str(log),
                 "--stderr", str(log), "--args", *arguments],
                stdout=stream, stderr=stream,
            )
            result["launchMethod"] = "launch-services"
        process.research_existing_pids = before
        try:
            if pipe_only:
                stdout = collect_stdout(process)
                stream.write("\n" + stdout.decode("utf-8"))
                stream.flush()
            else:
                process.wait(timeout=30)
            result["launcherExitCode"] = process.returncode
            lines = [line.removeprefix("HEADLESS_RENDERER_RESULT ")
                     for line in log.read_text().splitlines() if line.startswith("HEADLESS_RENDERER_RESULT ")]
            if len(lines) != 1:
                raise RuntimeError("Expected one complete native report")
            native = json.loads(lines[0])
            if pipe_only:
                encoded = native.pop("snapshotPNGBase64", "")
                if len(encoded) > 4 * ((2 * 1024 * 1024 + 2) // 3):
                    raise RuntimeError("Snapshot pipe exceeds the image limit")
                image = base64.b64decode(encoded, validate=True)
                if not image.startswith(b"\x89PNG\r\n\x1a\n"):
                    raise RuntimeError("Snapshot pipe did not contain a PNG")
                with (payload / "snapshot.png").open("xb") as destination:
                    destination.write(image)
                result["pipeImageBytes"] = len(image)
            result["native"] = native
            services = native.get("servicesAfterSnapshot", {})
            identities_known = all(services.get(name, {}).get("identity")
                                   for name in ("content", "gpu", "network"))
            result["allServiceIdentitiesKnown"] = identities_known
            same_user = identities_known and all(
                all(services[name]["identity"][field] == os.getuid()
                    for field in ("realUID", "effectiveUID", "savedUID"))
                for name in ("content", "gpu", "network"))
            result["allServicesSameUser"] = same_user
            pixels = payload / "snapshot.png"
            if pixels.is_file():
                result["snapshotSHA256"] = hashlib.sha256(pixels.read_bytes()).hexdigest()
            network_passed = True
            if fixture:
                nonce = native.get("javascript", {}).get("nonce")
                requests = fixture.requests_for(nonce)
                result["networkRequests"] = requests
                network_passed = native.get("networkDocumentPassed") is True and {
                    item["route"] for item in requests if item["status"] == 200
                } == {"fixture", "frame", "fetch", "image"}
                result["networkRequestsPassed"] = network_passed
            if (process.returncode == 0 and native.get("completed") is True
                    and native.get("javascriptPassed") is True and native.get("snapshotPassed") is True
                    and native.get("serviceIdentityStable") is True
                    and native.get("windowCountAtStart") == 0 and native.get("visibleWindowCountAtEnd") == 0
                    and identities_known and same_user and pixels.is_file() and network_passed
                    and (not pipe_only or (native.get("resultTransport") == "bounded-stdout-json"
                         and native.get("explicitSnapshotFileWrites") == 0))):
                result["verdict"] = expected_verdict
        except (RuntimeError, ValueError, OSError, subprocess.TimeoutExpired) as error:
            result["error"] = str(error)
        finally:
            result["cleanupVerified"] = stop_launched(process, BINARY)
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
            if not result["cleanupVerified"]:
                result["verdict"] = "inconclusive"
            if process.stdout is not None:
                process.stdout.close()
    (directory / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--repetitions", type=int, default=3, choices=range(1, 4))
    parser.add_argument("--network", action="store_true")
    parser.add_argument("--pipe", action="store_true")
    args = parser.parse_args()
    if args.network and args.pipe:
        parser.error("The pipe control accepts only the fixed inline fixture")
    if os.getuid() == 0 or os.geteuid() == 0:
        parser.error("This probe must run as an ordinary user")
    output = args.out.resolve()
    if not output.is_relative_to(ROOT / "artifacts"):
        parser.error("Output must be inside workspace artifacts")
    output.mkdir()
    results = []
    expected_verdict = ("same-user-loopback-baseline-passed" if args.network else
                        "same-user-pipe-baseline-passed" if args.pipe else "same-user-headless-baseline-passed")
    with serve_renderer_fixture() if args.network else nullcontext() as fixture:
        for index in range(args.repetitions):
            result = trial(output / f"trial-{index + 1}", fixture, args.pipe)
            results.append(result)
            if result["verdict"] != expected_verdict:
                break
            time.sleep(0.2)
    summary = {
        "milestone": 101 if args.pipe else 100 if args.network else 99,
        "mode": "pipe" if args.pipe else "loopback" if args.network else "inline",
        "scope": "Same-user fixture, no explicit window, no input, no privilege, no signal-denial claim",
        "temporaryServerCleanupVerified": args.network,
        "binarySHA256": hashlib.sha256(BINARY.read_bytes()).hexdigest(),
        "requestedTrials": args.repetitions,
        "trials": results,
        "allPassed": len(results) == args.repetitions and all(
            result["verdict"] == expected_verdict and result["cleanupVerified"]
            for result in results),
    }
    (output / "results.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"allPassed": summary["allPassed"], "trials": len(results), "output": str(output)}))


if __name__ == "__main__":
    main()
