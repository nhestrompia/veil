#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build/module-cache
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library \
    -module-cache-path .build/module-cache Sources/Browser/HIDSourcePolicy.swift \
    Sources/Browser/HIDPointerPolicy.swift Tests/HardwarePointerPolicyTests.swift \
    -o .build/hardware-pointer-policy-tests
.build/hardware-pointer-policy-tests
