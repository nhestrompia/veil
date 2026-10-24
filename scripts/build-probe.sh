#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
app=dist/NativeProbe.app
mkdir -p .build/module-cache "$app/Contents/MacOS"
probe_build_key="$(python3 tools/probe_build_cache.py key)"
if python3 tools/probe_build_cache.py check "$probe_build_key"; then
    echo "NativeProbe inputs and signed artifact match. Existing binary retained."
    exit 0
fi
xcrun clang -Wall -Wextra -target arm64-apple-macosx14.0 -c Sources/Probe/HIDPosting.c -o .build/hid-posting.o
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -O \
    -target arm64-apple-macosx14.0 -module-cache-path .build/module-cache \
    -import-objc-header Sources/Probe/HIDPosting.h Sources/Probe/*.swift .build/hid-posting.o -o "$app/Contents/MacOS/NativeProbe"
cat > "$app/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleIdentifier</key><string>research.agentfreebrowser.probe</string>
<key>CFBundleName</key><string>NativeProbe</string>
<key>CFBundleExecutable</key><string>NativeProbe</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>LSUIElement</key><true/>
<key>LSMinimumSystemVersion</key><string>14.0</string>
</dict></plist>
EOF
codesign --force --sign - --options runtime "$app"
python3 tools/probe_build_cache.py record "$probe_build_key"
