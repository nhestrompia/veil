#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build/module-cache dist
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -O \
    -target arm64-apple-macosx15.0 -module-cache-path .build/module-cache \
    Sources/HIDAttack/*.swift -o dist/VirtualDeviceProbe
codesign --force --sign - --options runtime dist/VirtualDeviceProbe
codesign --verify --strict dist/VirtualDeviceProbe
