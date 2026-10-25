"""Fetch a pinned source dependency without changing the project's Git history."""

import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import tempfile
import time

from prepare_webkit_activity import MANIFEST, ROOT, read_sources

GIB = 1024 ** 3
MAX_METADATA = 2 * GIB
MAX_SOURCE = 6 * GIB
MIN_FREE = 60 * GIB
REMOTE = "https://github.com/WebKit/WebKit.git"
SOURCE_DIRECTORIES = ["Source", "Tools", "WebKitLibraries", "WebKit.xcworkspace"]


def require_disk(directory, minimum=MIN_FREE):
    if shutil.disk_usage(directory).free < minimum:
        raise RuntimeError("The WebKit disk reserve would be crossed")


def source_sizes(directory):
    metadata = source = 0
    for parent, _, files in os.walk(directory):
        for name in files:
            path = Path(parent) / name
            try:
                info = path.lstat()
            except FileNotFoundError:
                continue
            if stat.S_ISREG(info.st_mode):
                if path.is_relative_to(directory / ".git"):
                    metadata += info.st_size
                else:
                    source += info.st_size
    return metadata, source


def terminate_group(process):
    if process.poll() is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=3)
    except ProcessLookupError:
        process.wait(timeout=3)


def git_environment():
    environment = os.environ.copy()
    for name in ["GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
                 "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_COMMON_DIR"]:
        environment.pop(name, None)
    environment.update(GIT_TERMINAL_PROMPT="0", GIT_ASKPASS="/usr/bin/false",
                       GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_NOSYSTEM="1")
    return environment


def monitored(command, directory, source, log):
    require_disk(directory)
    environment = git_environment()
    last_progress = time.monotonic()
    with log.open("ab") as output:
        process = subprocess.Popen(command, cwd=directory, env=environment, stdout=output,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        try:
            while process.poll() is None:
                require_disk(directory)
                metadata, retained = source_sizes(source) if source.exists() else (0, 0)
                if metadata > MAX_METADATA or retained > MAX_SOURCE:
                    raise RuntimeError("The source dependency exceeds its storage budget")
                if time.monotonic() - last_progress >= 10:
                    print(json.dumps({"phase": "source-fetch", "gitMetadataBytes": metadata,
                                      "checkoutBytes": retained}), flush=True)
                    last_progress = time.monotonic()
                time.sleep(1)
            if process.returncode:
                raise RuntimeError(f"Source download failed with exit {process.returncode}; see {log}")
            require_disk(directory)
            metadata, retained = source_sizes(source)
            if metadata > MAX_METADATA or retained > MAX_SOURCE:
                raise RuntimeError("The source dependency exceeds its storage budget")
        except BaseException:
            terminate_group(process)
            raise


def git_command(*arguments):
    return ["git", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false",
            "-c", "credential.helper=", "-c", "http.extraHeader=", *arguments]


def revision_of(source):
    return subprocess.run(git_command("-C", str(source), "rev-parse", "HEAD"),
                          env=git_environment(), capture_output=True, text=True, check=True).stdout.strip()


def prepare(base):
    base = base.resolve()
    base.mkdir(parents=True, exist_ok=True)
    require_disk(base)
    manifest = json.loads(MANIFEST.read_text())
    revision = manifest["revision"]
    final = base / f"WebKit-{revision}"
    receipt = base / "source-receipt.json"
    if final.exists():
        if revision_of(final) != revision:
            raise RuntimeError("Existing source has a different revision")
        read_sources(final)
        recorded = json.loads((final / ".agentfreebrowser-source.json").read_text())
        if recorded["revision"] != revision:
            raise RuntimeError("Existing source receipt has a different revision")
        receipt.write_text(json.dumps(recorded, indent=2) + "\n")
        print(json.dumps({"status": "reused-pristine-source", "source": str(final)}), flush=True)
        return
    log = base / "source-fetch.log"
    with tempfile.TemporaryDirectory(prefix="clone-", dir=base) as temporary:
        staging = Path(temporary)
        source = staging / "WebKit"
        clone = git_command("clone", "--depth", "1", "--no-tags", "--filter=blob:none", "--sparse",
                            "--revision", revision, REMOTE, str(source))
        monitored(clone, staging, source, log)
        if revision_of(source) != revision:
            raise RuntimeError("The dependency clone resolved a different revision")
        monitored(git_command("-C", str(source), "sparse-checkout", "set", "--cone", *SOURCE_DIRECTORIES),
                  staging, source, log)
        read_sources(source)
        metadata, retained = source_sizes(source)
        report = {"revision": revision, "remote": REMOTE, "source": str(final),
                  "method": "shallow sparse dependency clone", "sourceDirectories": SOURCE_DIRECTORIES,
                  "gitMetadataBytes": metadata, "checkoutBytes": retained,
                  "pinnedFilesVerified": len(manifest["files"]), "minimumFreeBytes": MIN_FREE,
                  "engineBuilt": False, "engineExecuted": False}
        marker = source / ".agentfreebrowser-source.json"
        if marker.exists() or marker.is_symlink():
            raise RuntimeError("Source already contains the preparation receipt path")
        marker.write_text(json.dumps(report, indent=2) + "\n")
        source.rename(final)
    receipt.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / ".build/webkit-engine")
    prepare(parser.parse_args().output)
