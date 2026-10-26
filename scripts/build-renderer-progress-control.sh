#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
research_uid=$(/usr/bin/id -u)
if [ "$research_uid" -lt 500 ]; then exit 2; fi
app=dist/RendererProgressProbe.app
mkdir -p .build/module-cache "$app/Contents/MacOS"
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -O \
    -D RENDERER_IDENTITY_CONTROL -D RENDERER_PROGRESS_CONTROL -module-cache-path .build/module-cache \
    "$PWD/Sources/Diagnostics/HeadlessRendererProbe.swift" -o "$app/Contents/MacOS/RendererProgressProbe"
python3 - "$app" <<'PY'
from pathlib import Path
import plistlib
import sys
Path(sys.argv[1], 'Contents/Info.plist').write_bytes(plistlib.dumps({
    'CFBundleIdentifier': 'research.agentfreebrowser.rendererprogressprobe',
    'CFBundleName': 'RendererProgressProbe', 'CFBundleExecutable': 'RendererProgressProbe',
    'CFBundlePackageType': 'APPL', 'LSUIElement': True,
}))
PY
codesign --force --sign - --options runtime "$app"
codesign --verify --strict "$app"
xcrun clang -std=c11 -Wall -Wextra -Werror -O2 -DAFB_RESEARCH_UID="$research_uid" \
    -DAFB_PROGRESS_CONTROL "$PWD/Sources/Diagnostics/RendererSignalActor.c" -o .build/renderer-progress-actor
codesign --force --sign - --options runtime .build/renderer-progress-actor
codesign --verify --strict .build/renderer-progress-actor
