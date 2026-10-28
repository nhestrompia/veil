#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build/module-cache
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library \
    -D DEVICE_KEYBOARD_EXPERIMENT -D DEVICE_POINTER_EXPERIMENT \
    -module-cache-path .build/module-cache Sources/Browser/AXBoundary.swift \
    Sources/Browser/RestrictedWebView.swift Sources/Browser/DeviceKeyboard.swift \
    Sources/Browser/HIDSourcePolicy.swift Sources/Browser/HIDPointerPolicy.swift \
    Sources/Browser/DevicePointer.swift Tests/HardwarePointerQueueTests.swift \
    -o .build/hardware-pointer-queue-tests
.build/hardware-pointer-queue-tests
