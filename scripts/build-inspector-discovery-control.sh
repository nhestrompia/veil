#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build/module-cache
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library \
    -target arm64-apple-macosx15.0 -module-cache-path .build/module-cache \
    "$PWD/Sources/Diagnostics/RendererProcessScope.swift" \
    "$PWD/Sources/Diagnostics/PreviewAXScope.swift" \
    "$PWD/Sources/Diagnostics/InspectorDiscoveryControl.swift" \
    -o .build/inspector-discovery-control
