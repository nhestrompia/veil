#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build/module-cache
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -Onone -g \
    -D DEVICE_KEYBOARD_EXPERIMENT -target arm64-apple-macosx14.0 \
    -module-cache-path .build/module-cache Sources/Browser/AXBoundary.swift \
    Sources/Browser/DeviceKeyboard.swift Sources/Browser/HIDSourcePolicy.swift Tests/DeviceEventQueueTests.swift -o .build/device-queue-tests
.build/device-queue-tests
