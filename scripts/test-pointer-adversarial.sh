#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
test_dir=$(mktemp -d "${TMPDIR:-/tmp}/pointer-adversarial.XXXXXXXX")
trap 'rm -rf "$test_dir"' EXIT
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library \
    -module-cache-path "$test_dir/module-cache" Sources/Browser/HIDSourcePolicy.swift \
    Sources/Browser/HIDPointerPolicy.swift Tests/HardwarePointerAdversarialTests.swift \
    -o "$test_dir/tests"
"$test_dir/tests"
