#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build/module-cache
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library \
    -module-cache-path .build/module-cache \
    "$PWD/Sources/Diagnostics/SignalAuthorizationPolicy.swift" \
    "$PWD/Tests/SignalAuthorizationPolicyTests.swift" -o .build/signal-authorization-policy-tests
.build/signal-authorization-policy-tests
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library \
    -module-cache-path .build/module-cache \
    "$PWD/Sources/Diagnostics/SignalAuthorizationPolicy.swift" \
    "$PWD/Sources/Diagnostics/RendererProcessScope.swift" \
    "$PWD/Sources/Diagnostics/SignalAuthorization.swift" \
    -lEndpointSecurity -lbsm -o .build/signal-authorization
codesign --force --sign - --options runtime .build/signal-authorization
codesign --verify --strict .build/signal-authorization
.build/signal-authorization --preflight
