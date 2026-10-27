#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
research_uid=$(/usr/bin/id -u)
if [ "$research_uid" -lt 500 ]; then exit 2; fi
mkdir -p .build/module-cache
for name in ChannelRendererProbe ChannelBlockingProbe ChannelDisplayProbe; do
    app="dist/$name.app"
    mkdir -p "$app/Contents/MacOS"
    defines=(-D CHANNEL_DIAGNOSTIC_CONTROL)
    if [ "$name" = ChannelDisplayProbe ]; then
        source=Sources/Diagnostics/ChannelDisplayProbe.swift
    else
        source=Sources/Diagnostics/ChannelRendererProbe.swift
        if [ "$name" = ChannelBlockingProbe ]; then defines+=(-D CHANNEL_BLOCKING_CONTROL); fi
    fi
    xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -O -target arm64-apple-macosx14.0 \
        -module-cache-path .build/module-cache "${defines[@]}" Sources/Channel/RendererChannel.swift \
        Sources/Diagnostics/ChannelProbeSupport.swift Sources/Browser/BrowserRuntimePolicy.swift "$source" \
        -o "$app/Contents/MacOS/$name"
    python3 - "$app" "$name" <<'PY'
from pathlib import Path
import plistlib, sys
Path(sys.argv[1], 'Contents/Info.plist').write_bytes(plistlib.dumps({
    'CFBundleIdentifier': 'research.agentfreebrowser.' + sys.argv[2].lower(),
    'CFBundleName': sys.argv[2], 'CFBundleExecutable': sys.argv[2],
    'CFBundlePackageType': 'APPL', 'LSUIElement': True,
    'NSAppTransportSecurity': {'NSAllowsLocalNetworking': True},
}))
PY
    codesign --force --sign - --options runtime "$app"
    codesign --verify --strict "$app"
done
xcrun clang -std=c11 -Wall -Wextra -Werror -O2 -DAFB_RESEARCH_UID="$research_uid" \
    -DAFB_CHANNEL_DISPLAY_CONTROL "$PWD/Sources/Diagnostics/RendererSignalActor.c" -o .build/channel-display-pause-actor
codesign --force --sign - --options runtime .build/channel-display-pause-actor
codesign --verify --strict .build/channel-display-pause-actor
xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -O -module-cache-path .build/module-cache \
    Sources/Channel/RendererChannel.swift Tests/RendererChannelTests.swift -o .build/renderer-channel-tests
