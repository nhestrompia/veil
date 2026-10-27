#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
research_uid=$(/usr/bin/id -u)
research_gid=$(/usr/bin/id -g)
if [ "$research_uid" -lt 500 ] || [ "$research_gid" -eq 0 ]; then exit 2; fi
mkdir -p .build/module-cache
for name in ChannelIsolatedRendererProbe ChannelIsolatedDisplayProbe; do
    app="dist/$name.app"
    mkdir -p "$app/Contents/MacOS"
    if [ "$name" = ChannelIsolatedDisplayProbe ]; then
        source=Sources/Diagnostics/ChannelDisplayProbe.swift
    else
        source=Sources/Diagnostics/ChannelRendererProbe.swift
    fi
    xcrun swiftc -swift-version 6 -warnings-as-errors -parse-as-library -O -no-stdlib-rpath -target arm64-apple-macosx14.0 \
        -module-cache-path .build/module-cache -D CHANNEL_IDENTITY_CONTROL Sources/Channel/RendererChannel.swift \
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
    -DAFB_RESEARCH_GID="$research_gid" -DAFB_PRIVILEGED_CHANNEL_CONTROL \
    "$PWD/Sources/Diagnostics/RendererChannelLauncher.c" -o .build/renderer-channel-supervisor
codesign --force --sign - --options runtime .build/renderer-channel-supervisor
codesign --verify --strict .build/renderer-channel-supervisor
for role in renderer display; do
    if [ "$role" = renderer ]; then define=AFB_CHANNEL_RENDERER_CONTROL; else define=AFB_CHANNEL_STAGED_DISPLAY; fi
    xcrun clang -std=c11 -Wall -Wextra -Werror -O2 -DAFB_RESEARCH_UID="$research_uid" -D"$define" \
        "$PWD/Sources/Diagnostics/RendererSignalActor.c" -o ".build/channel-$role-signal-actor"
    codesign --force --sign - --options runtime ".build/channel-$role-signal-actor"
    codesign --verify --strict ".build/channel-$role-signal-actor"
done
