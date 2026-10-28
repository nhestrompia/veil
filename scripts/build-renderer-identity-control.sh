#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
research_uid=$(/usr/bin/id -u)
research_gid=$(/usr/bin/id -g)
if [ "$research_uid" -lt 500 ] || [ "$research_gid" -eq 0 ]; then
    exit 2
fi
app=dist/RendererIdentityProbe.app
mkdir -p .build/module-cache "$app/Contents/MacOS"
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -O \
    -D RENDERER_IDENTITY_CONTROL -module-cache-path .build/module-cache \
    "$PWD/Sources/Diagnostics/HeadlessRendererProbe.swift" -o "$app/Contents/MacOS/RendererIdentityProbe"
python3 - "$app" <<'PY'
from pathlib import Path
import plistlib
import sys
Path(sys.argv[1], 'Contents/Info.plist').write_bytes(plistlib.dumps({
    'CFBundleIdentifier': 'research.agentfreebrowser.rendereridentityprobe',
    'CFBundleName': 'RendererIdentityProbe', 'CFBundleExecutable': 'RendererIdentityProbe',
    'CFBundlePackageType': 'APPL', 'LSUIElement': True,
}))
PY
codesign --force --sign - --options runtime "$app"
codesign --verify --strict "$app"
xcrun clang -std=c11 -Wall -Wextra -Werror -O2 \
    -DAFB_RESEARCH_UID="$research_uid" -DAFB_RESEARCH_GID="$research_gid" \
    "$PWD/Sources/Diagnostics/RendererIdentitySupervisor.c" -o .build/renderer-identity-supervisor
codesign --force --sign - --options runtime .build/renderer-identity-supervisor
codesign --verify --strict .build/renderer-identity-supervisor
.build/renderer-identity-supervisor --preflight
