#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
research_uid=$(/usr/bin/id -u)
if [ "$research_uid" -lt 500 ]; then exit 2; fi
mkdir -p .build
xcrun clang -std=c11 -Wall -Wextra -Werror -O2 -DAFB_RESEARCH_UID="$research_uid" \
    "$PWD/Sources/Diagnostics/RendererChannelLauncher.c" -o .build/renderer-channel-launcher
codesign --force --sign - --options runtime .build/renderer-channel-launcher
codesign --verify --strict .build/renderer-channel-launcher
