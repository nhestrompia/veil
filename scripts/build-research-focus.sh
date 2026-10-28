#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build/module-cache
xcrun swiftc -swift-version 6 -warnings-as-errors -O \
    -module-cache-path .build/module-cache Sources/Diagnostics/ResearchFocus.swift \
    -o .build/research-focus
