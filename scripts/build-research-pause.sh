#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build/module-cache
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library \
    -module-cache-path .build/module-cache \
    "$PWD/Sources/Diagnostics/ResearchPauseScope.swift" \
    "$PWD/Tests/ResearchPauseScopeTests.swift" -o .build/research-pause-scope-tests
.build/research-pause-scope-tests
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library \
    -module-cache-path .build/module-cache \
    "$PWD/Sources/Diagnostics/ResearchPauseScope.swift" \
    "$PWD/Sources/Diagnostics/RendererProcessScope.swift" \
    "$PWD/Sources/Diagnostics/ResearchPause.swift" -o .build/research-pause
