#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
package="$PWD/.build/preview-compositor-tests"
mkdir -p "$package/Tests/PixelTests"
cat > "$package/Package.swift" <<'SWIFT'
// swift-tools-version: 6.0
import PackageDescription
let package = Package(name: "CompositorChecks", platforms: [.macOS(.v15)], targets: [.testTarget(name: "PixelTests")])
SWIFT
cp Sources/Diagnostics/PreviewCompositorPixels.swift Tests/PreviewCompositorPixelsTests.swift "$package/Tests/PixelTests/"
CLANG_MODULE_CACHE_PATH="$package/module-cache" SWIFTPM_MODULECACHE_OVERRIDE="$package/module-cache" \
    swift test --package-path "$package" --cache-path "$package/cache" --disable-sandbox
