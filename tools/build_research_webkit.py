"""Apply the exact research patch and build within a bounded workspace directory."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile
import time

from prepare_webkit_activity import ROOT, PATCH, changed_sources, generate, read_sources
from prepare_webkit_source import MIN_FREE, git_command, git_environment, monitored, require_disk, revision_of, terminate_group

BASE = ROOT / ".build/webkit-engine"
CACHE = ROOT / ".build/webkit-source-94f9"


def stage(source):
    manifest, original = read_sources(CACHE)
    if revision_of(source) != manifest["revision"]:
        raise RuntimeError("Research source revision differs from the pinned revision")
    generate(CACHE, check=True)
    updated = changed_sources(original)
    expected = {**original, **updated}
    # Validate every old/new file before writing. A stopped application can resume.
    for name, text in expected.items():
        path = source / name
        if path.is_symlink() or not path.resolve().is_relative_to(source.resolve()):
            raise RuntimeError(f"Research source path escapes its checkout: {name}")
        actual = path.read_bytes().decode() if path.exists() else None
        allowed = [text, original.get(name)] if name in updated else [text]
        if actual not in allowed:
            raise RuntimeError(f"Refusing changed research source: {name}")
    for name, text in updated.items():
        path = source / name
        if path.exists() and path.read_bytes() == text.encode():
            continue
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as temporary:
            temporary.write(text)
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, path)
    receipt = {"revision": manifest["revision"],
               "patchSHA256": hashlib.sha256(PATCH.read_bytes()).hexdigest(),
               "files": {name: hashlib.sha256(text.encode()).hexdigest() for name, text in expected.items()},
               "engineCompiled": False, "engineRuntimeTested": False}
    for name, digest in receipt["files"].items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != digest:
            raise RuntimeError(f"Applied source identity differs: {name}")
    (BASE / "applied-source.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def build_environment(output):
    environment = git_environment()
    environment.update(WEBKIT_OUTPUTDIR=str(output),
                       CLANG_MODULE_CACHE_PATH=str(output / "ModuleCache"),
                       SWIFT_MODULE_CACHE_PATH=str(output / "SwiftModuleCache"),
                       TMPDIR=str(output / "Temporary"))
    for name in ["BUILD_WEBKIT_PRE_SCRIPT", "BUILD_WEBKIT_POST_SCRIPT"]:
        environment.pop(name, None)
    return environment


def engine_command(source, output):
    # Match the upstream engine invocation without its separate ImageDiff build.
    return ["/usr/bin/nice", "-n", "10", "/usr/bin/xcrun", "xcodebuild",
            "-scheme", "Everything up to WebKit",
            "-UseSanitizedBuildSystemEnvironment=YES", "-ShowBuildOperationDuration=YES",
            "-workspace", str(source / "WebKit.xcworkspace"),
            "-configuration", "Release", "-destination", "platform=macOS,devicetype=Mac,arch=arm64",
            f"SYMROOT={output}", f"OBJROOT={output}", "SDKROOT=macosx",
            "-jobs", "4", "ARCHS=arm64", "ONLY_ACTIVE_ARCH=YES",
            f"MACOSX_DEPLOYMENT_TARGET={platform.mac_ver()[0]}", "TMPDIR=$(TARGET_TEMP_DIR)/",
            "-derivedDataPath", str(output / "DerivedData"),
            f"SHARED_PRECOMPS_DIR={output / 'PrecompiledHeaders'}"]


def build(source, timeout):
    metal = subprocess.run(["xcrun", "metal", "--version"], capture_output=True, text=True, timeout=30)
    if metal.returncode:
        raise RuntimeError("The Metal compiler does not execute. Install Apple's MetalToolchain component first")
    if not (source / "Configurations/CommonBase.xcconfig").is_file():
        monitored(git_command("-C", str(source), "sparse-checkout", "add", "Configurations"),
                  source, source, BASE / "build-source-fetch.log")
    output = BASE / "output"
    if not output.resolve().is_relative_to(BASE.resolve()):
        raise RuntimeError("Build output escapes the workspace directory")
    output.mkdir(exist_ok=True)
    (output / "Temporary").mkdir(exist_ok=True)
    require_disk(BASE)
    log = BASE / "build.log"
    command = engine_command(source, output)
    report = {"command": command, "output": str(output), "source": str(source),
              "minimumFreeBytes": MIN_FREE, "timeoutSeconds": timeout,
              "metalCompiler": metal.stdout.strip(), "monitorPID": os.getpid(),
              "status": "running", "scope": "Everything up to WebKit scheme; ImageDiff excluded",
              "engineCompiled": False, "engineRuntimeTested": False}
    start = time.monotonic()
    result = BASE / "build-results.json"
    result.write_text(json.dumps(report, indent=2) + "\n")
    with log.open("wb") as stream:
        process = subprocess.Popen(command, cwd=source, env=build_environment(output),
                                   stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        report["processGroupPID"] = process.pid
        result.write_text(json.dumps(report, indent=2) + "\n")
        try:
            while process.poll() is None:
                require_disk(BASE)
                if time.monotonic() - start > timeout:
                    raise RuntimeError("Research engine build reached its time limit")
                if log.stat().st_size > 512 * 1024 ** 2:
                    raise RuntimeError("Research engine build log reached its size limit")
                time.sleep(1)
            report["exitCode"] = process.returncode
            report["status"] = "succeeded" if process.returncode == 0 else "failed"
            report["engineCompiled"] = process.returncode == 0
            if process.returncode:
                raise RuntimeError(f"Research engine build failed with exit {process.returncode}; see {log}")
        except BaseException as error:
            if report["status"] == "running":
                report["status"] = "stopped"
            report["error"] = f"{type(error).__name__}: {error}"
            terminate_group(process)
            raise
        finally:
            report["elapsedSeconds"] = round(time.monotonic() - start, 1)
            result.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--timeout", type=int, default=7200)
    args = parser.parse_args()
    if not 1 <= args.timeout <= 14400:
        parser.error("timeout must be between 1 and 14400 seconds")
    preparation = json.loads((BASE / "source-receipt.json").read_text())
    source = Path(preparation["source"])
    if source.parent.resolve() != BASE.resolve():
        raise RuntimeError("Research source must remain inside the workspace build directory")
    require_disk(BASE)
    stage(source)
    if args.build:
        build(source, args.timeout)
