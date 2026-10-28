"""Reuse the signed research probe only when its inputs and artifact match."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "dist/NativeProbe.app"
BINARY = APP / "Contents/MacOS/NativeProbe"
MANIFEST = ROOT / ".build/native-probe-cache.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def input_key():
    files = [ROOT / "scripts/build-probe.sh", Path(__file__).resolve()]
    files.extend(path for path in (ROOT / "Sources/Probe").iterdir() if path.suffix in [".swift", ".h", ".c"])
    commands = [["xcrun", "swiftc", "-version"], ["xcrun", "clang", "--version"],
                ["xcrun", "--find", "swiftc"], ["xcrun", "--show-sdk-path"], ["xcrun", "--show-sdk-build-version"]]
    inputs = {"files": {str(path.relative_to(ROOT)): digest(path) for path in sorted(files)},
              "toolchain": [subprocess.check_output(command, text=True, stderr=subprocess.DEVNULL).strip() for command in commands]}
    return hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()


def artifact_matches(key):
    try:
        manifest = json.loads(MANIFEST.read_text())
        if not isinstance(manifest, dict) or manifest.get("inputKey") != key or not os.access(BINARY, os.X_OK) or manifest.get("binarySHA256") != digest(BINARY):
            return False
    except (OSError, ValueError):
        return False
    return subprocess.run(["codesign", "--verify", "--strict", str(APP)],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def main():
    command = sys.argv[1]
    if command == "key":
        print(input_key())
        return
    key = sys.argv[2]
    if command == "check":
        sys.exit(0 if artifact_matches(key) else 1)
    if command != "record":
        raise ValueError("Use key, check, or record")
    if input_key() != key:
        raise RuntimeError("Probe inputs changed during the build. Run the build again.")
    subprocess.run(["codesign", "--verify", "--strict", str(APP)], check=True)
    MANIFEST.write_text(json.dumps({"inputKey": key, "binarySHA256": digest(BINARY)}, indent=2) + "\n")


if __name__ == "__main__":
    main()
