#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build/module-cache
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library \
    -module-cache-path .build/module-cache Sources/Diagnostics/FixedGeometryWindow.swift \
    Tests/FixedGeometryWindowTests.swift -o .build/fixed-geometry-window-tests
.build/fixed-geometry-window-tests
