#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build/module-cache
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -O \
    -module-cache-path .build/module-cache Sources/Diagnostics/KeyboardObservationProbe.swift \
    -o .build/keyboard-observation-probe
