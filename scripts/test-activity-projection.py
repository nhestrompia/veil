"""Compile the real projection using the enum extracted from pinned WebKit."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def run(source):
    manifest = json.loads((ROOT / "engine/webkit-source-manifest.json").read_text())
    name = "Source/WebCore/page/ActivityState.h"
    expected = next(row for row in manifest["files"] if row["path"] == name)
    data = (source / name).read_bytes()
    if hashlib.sha256(data).hexdigest() != expected["sha256"]:
        raise RuntimeError("The pinned activity enum source changed")
    text = data.decode()
    declaration = re.search(r"enum class ActivityState : uint16_t \{[^}]+\};", text)
    if not declaration:
        raise RuntimeError("The expected activity enum declaration is absent")
    include = ROOT / ".build/activity-projection-include"
    include.mkdir(parents=True, exist_ok=True)
    license_header = text[:text.index("#pragma once")]
    (include / "WebCoreActivityEnum.h").write_text(license_header + "#pragma once\n#include <cstdint>\nnamespace WebCore {\n"
        + declaration.group() + "\n}\n")
    binary = ROOT / ".build/activity-projection-tests"
    command = ["xcrun", "clang++", "-std=c++20", "-Wall", "-Wextra", "-Werror", "-pedantic",
               "-I", str(ROOT / "engine"), "-I", str(include),
               str(ROOT / "Tests/ActivityProjectionTests.cpp"), "-o", str(binary)]
    subprocess.run(command, check=True)
    result = subprocess.run([str(binary)], capture_output=True, text=True, check=True)
    report = {"revision": manifest["revision"], "enumSHA256": expected["sha256"],
              "projectionSHA256": hashlib.sha256((ROOT / "engine/ContentActivityProjection.h").read_bytes()).hexdigest(),
              "statesChecked": 65536, "policiesChecked": 2, "compiledProjection": True,
              "compiledWebKitIntegration": False, "runtimeBrowserTested": False, "output": result.stdout.strip()}
    (ROOT / ".build/activity-projection-test-results.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=ROOT / ".build/webkit-source-94f9")
    run(parser.parse_args().source.resolve())
