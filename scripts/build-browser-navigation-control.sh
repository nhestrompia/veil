#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ "$(/usr/bin/id -u)" -eq 0 ]; then exit 2; fi
app=dist/BrowserNavigationControl.app
mkdir -p .build/module-cache "$app/Contents/MacOS"
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -O -target arm64-apple-macosx14.0 \
    -module-cache-path .build/module-cache -D BROWSER_NAVIGATION_CONTROL \
    Sources/Browser/*.swift Sources/Diagnostics/BrowserNavigationControl.swift \
    -o "$app/Contents/MacOS/BrowserNavigationControl"
python3 - "$app" <<'PY'
from pathlib import Path
import plistlib
import sys
Path(sys.argv[1], 'Contents/Info.plist').write_bytes(plistlib.dumps({
    'CFBundleIdentifier': 'research.agentfreebrowser.navigationcontrol',
    'CFBundleName': 'BrowserNavigationControl', 'CFBundleExecutable': 'BrowserNavigationControl',
    'CFBundlePackageType': 'APPL', 'LSUIElement': True,
    'NSAppTransportSecurity': {'NSAllowsLocalNetworking': True},
}))
PY
codesign --force --sign - --options runtime --entitlements config/browser.entitlements "$app"
codesign --verify --strict "$app"
