#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build/module-cache
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library \
    -module-cache-path .build/module-cache \
    "$PWD/Sources/Diagnostics/PrivateEntryPolicy.swift" \
    "$PWD/Tests/PrivateEntryPolicyTests.swift" -o .build/private-entry-policy-tests
.build/private-entry-policy-tests
