#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build/module-cache
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library \
    -module-cache-path .build/module-cache Sources/Diagnostics/FakeKeyMatcher.swift \
    Tests/FakeKeyMatcherTests.swift -o .build/fake-key-tests
.build/fake-key-tests
