#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build/module-cache
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library \
  -module-cache-path .build/module-cache Sources/Browser/HIDSourcePolicy.swift \
  Sources/Browser/HIDPointerPolicy.swift Sources/Browser/PhysicalMousePolicy.swift \
  Tests/PhysicalMousePolicyTests.swift -o .build/physical-mouse-policy-tests
.build/physical-mouse-policy-tests
