#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build/module-cache dist
# The global-policy control deliberately references the deprecated kIOSurfaceIsGlobal key.
xcrun swiftc -swift-version 6 -parse-as-library -O \
    -target arm64-apple-macosx14.0 -module-cache-path .build/module-cache \
    Sources/SurfaceProbe/*.swift -o dist/SurfaceProbe
codesign --force --sign - --options runtime dist/SurfaceProbe
codesign --verify --strict dist/SurfaceProbe
