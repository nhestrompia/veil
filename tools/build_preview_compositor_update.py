"""Stage a recorder layout repair without changing the granted app."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

from run_native import ROOT
from run_preview_compositor_comparison import verified_manifest


def revised_source(source):
    replacements = [
        ("(backdrop[kCGWindowLayer as String] as? Int) == 0,",
         "(backdrop[kCGWindowLayer as String] as? Int) == PreviewCompositorBackdrop.level.rawValue,"),
        ("let backdrop = NSWindow(contentRect: backdropFrame, styleMask: .borderless, backing: .buffered, defer: false)",
         "let backdrop = PreviewCompositorBackdrop.make(frame: backdropFrame)"),
        ("backdrop.level = .normal", "backdrop.level = PreviewCompositorBackdrop.level"),
    ]
    for old, new in replacements:
        if source.count(old) != 1:
            raise RuntimeError("The frozen recorder no longer matches this reviewed layout repair")
        source = source.replace(old, new)
    return source


def build(output):
    output = output.resolve()
    if not output.is_relative_to((ROOT / "artifacts").resolve()):
        raise ValueError("Use a fresh project artifact directory")
    manifest, binary = verified_manifest()
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    app = Path(manifest["path"])
    backup = output / "original" / app.name
    candidate = output / "candidate" / app.name
    shutil.copytree(app, backup, symlinks=True)
    shutil.copytree(app, candidate, symlinks=True)
    (output / "original-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    original = ROOT / "Sources/Diagnostics/PreviewCompositorProbe.swift"
    generated = ROOT / ".build/diagnostics/PreviewCompositorPanelProbe.swift"
    generated.parent.mkdir(parents=True, exist_ok=True)
    generated.write_text(revised_source(original.read_text()))
    source_paths = [ROOT / name for name in ["Sources/Diagnostics/RendererProcessScope.swift",
                    "Sources/Diagnostics/PreviewAXScope.swift", "Sources/Diagnostics/PreviewCompositorPixels.swift",
                    "Sources/Diagnostics/PreviewCompositorBackdrop.swift"]] + [generated]
    executable = candidate / "Contents/MacOS/PreviewCompositorProbe"
    subprocess.run(["xcrun", "swiftc", "-swift-version", "6", "-warnings-as-errors", "-parse-as-library", "-O",
                    "-target", "arm64-apple-macosx15.0", "-module-cache-path", str(ROOT / ".build/module-cache"),
                    *map(str, source_paths), "-o", str(executable)], check=True, timeout=90)
    subprocess.run(["codesign", "--force", "--sign", "-", "--options", "runtime", str(candidate)], check=True, timeout=15)
    subprocess.run(["codesign", "--verify", "--strict", str(candidate)], check=True, timeout=15)
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    if digest(binary) != manifest["executableSHA256"] or digest(backup / "Contents/MacOS/PreviewCompositorProbe") != manifest["executableSHA256"]:
        raise RuntimeError("The granted image changed during staging")
    sources = {str(path.relative_to(ROOT)): digest(path) for path in source_paths}
    sources["tools/build_preview_compositor_update.py"] = digest(Path(__file__))
    report = {"status": "staged", "installed": False, "permissionRequested": False,
              "app": str(app), "candidate": str(candidate), "backup": str(backup),
              "oldSHA256": manifest["executableSHA256"], "newSHA256": digest(executable), "sourceHashes": sources,
              "scopeChanged": False, "targetsChanged": False, "cropChanged": False, "durationChanged": False,
              "change": "Use a nonactivating panel one level below the target, with its exact level checked by the coverage guard.",
              "guardChanges": "Only the expected level of the helper's own backdrop changes from zero to minus one. Other ownership, geometry, foreground, opacity, overlap, and cleanup checks remain intact."}
    (output / "reviewed-update.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    report = build(parser.parse_args().output)
    print(json.dumps({key: report[key] for key in ["status", "installed", "oldSHA256", "newSHA256"]}))
