#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ "$#" -ne 1 ]; then
    echo "Supply a new absolute project artifact directory." >&2
    exit 2
fi
mkdir -p .build/module-cache
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -Onone -g \
    -target arm64-apple-macosx15.0 -module-cache-path .build/module-cache \
    -D DEVICE_KEYBOARD_EXPERIMENT -D INTEGRATED_BROWSER \
    Sources/Browser/AXBoundary.swift Sources/Browser/RestrictedWebView.swift \
    Sources/Browser/DeviceKeyboard.swift Sources/Browser/HIDSourcePolicy.swift \
    Tests/DeviceEventQueueTests.swift -o .build/integrated-event-tests
.build/integrated-event-tests
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -O \
    -target arm64-apple-macosx15.0 -module-cache-path .build/module-cache \
    -D DEVICE_KEYBOARD_EXPERIMENT -D INTEGRATED_BROWSER -D BROWSER_NAVIGATION_CONTROL \
    Sources/Browser/*.swift Sources/Diagnostics/BrowserNavigationControl.swift \
    -o .build/IntegratedBrowserNavigation
python3 tools/run_browser_navigation_control.py --integrated --out "$1"
