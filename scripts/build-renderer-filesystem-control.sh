#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build/module-cache
xcrun clang -std=c11 -Wall -Wextra -Werror -O2 \
    "$PWD/Sources/Diagnostics/RendererMetadataRead.c" -o .build/renderer-metadata-read
codesign --force --sign - --options runtime .build/renderer-metadata-read
codesign --verify --strict .build/renderer-metadata-read
for kind in Reference Sandbox NetworkSandbox; do
    name="RendererFilesystem${kind}"
    app="dist/$name.app"
    mkdir -p "$app/Contents/MacOS"
    xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -O \
        -D RENDERER_FILESYSTEM_CONTROL -module-cache-path .build/module-cache \
        "$PWD/Sources/Diagnostics/HeadlessRendererProbe.swift" \
        "$PWD/Sources/Diagnostics/RendererFilesystemControl.swift" \
        -o "$app/Contents/MacOS/$name"
    python3 - "$app" "$name" "$kind" <<'PY'
from pathlib import Path
import plistlib
import sys
app, name, kind = sys.argv[1:]
Path(app, 'Contents/Info.plist').write_bytes(plistlib.dumps({
    'CFBundleIdentifier': 'research.agentfreebrowser.rendererfilesystem' + kind.lower(),
    'CFBundleName': name, 'CFBundleExecutable': name,
    'CFBundlePackageType': 'APPL', 'LSUIElement': True,
}))
PY
    if [ "$kind" = NetworkSandbox ]; then
        codesign --force --sign - --options runtime --entitlements config/renderer-filesystem-network.entitlements "$app"
    elif [ "$kind" = Sandbox ]; then
        codesign --force --sign - --options runtime --entitlements config/renderer-filesystem.entitlements "$app"
    else
        codesign --force --sign - --options runtime "$app"
    fi
    codesign --verify --strict "$app"
done
