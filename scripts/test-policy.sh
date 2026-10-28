#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build/module-cache
xcrun swiftc -swift-version 6 -parse-as-library -module-cache-path .build/module-cache \
    Sources/Browser/BrowserPolicy.swift Tests/PolicyTests.swift -o .build/policy-tests
.build/policy-tests
