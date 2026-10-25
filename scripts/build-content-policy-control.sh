#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
app=dist/ContentPolicyControl.app
mkdir -p .build/module-cache "$app/Contents/MacOS"
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -O \
    -target arm64-apple-macosx14.0 -module-cache-path .build/module-cache \
    Sources/Browser/BrowserRuntimePolicy.swift Sources/Browser/RestrictedWebView.swift \
    Sources/Diagnostics/ContentPolicyControl.swift -o "$app/Contents/MacOS/ContentPolicyControl"
cat > "$app/Contents/Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>research.agentfreebrowser.contentpolicycontrol</string>
<key>CFBundleName</key><string>ContentPolicyControl</string>
<key>CFBundleExecutable</key><string>ContentPolicyControl</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>NSAppTransportSecurity</key><dict><key>NSAllowsLocalNetworking</key><true/></dict>
</dict></plist>
EOF
codesign --force --sign - --options runtime "$app"
codesign --verify --strict "$app"
