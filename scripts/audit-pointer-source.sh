#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build/module-cache
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library \
    -module-cache-path .build/module-cache Sources/Browser/HIDSourcePolicy.swift \
    Sources/Diagnostics/PointerSourceAudit.swift -o .build/PointerSourceAudit
.build/PointerSourceAudit
