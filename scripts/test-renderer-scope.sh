#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build/module-cache
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library \
    -module-cache-path .build/module-cache \
    "$PWD/Sources/Diagnostics/RendererProcessScope.swift" \
    "$PWD/Tests/RendererScopeTests.swift" -o .build/renderer-scope-tests
.build/renderer-scope-tests
