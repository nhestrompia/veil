#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build/module-cache
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library \
    -module-cache-path .build/module-cache Sources/Browser/HIDSourcePolicy.swift \
    Tests/HIDSourcePolicyTests.swift -o .build/hid-source-tests
.build/hid-source-tests
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library \
    -module-cache-path .build/module-cache Sources/Browser/HIDSourcePolicy.swift \
    Sources/Diagnostics/HIDSourceAudit.swift -o .build/hid-source-audit
.build/hid-source-audit
