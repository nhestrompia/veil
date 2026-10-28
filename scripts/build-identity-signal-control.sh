#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
research_uid=$(/usr/bin/id -u)
research_gid=$(/usr/bin/id -g)
if [ "$research_uid" -lt 500 ] || [ "$research_gid" -eq 0 ]; then
    echo 'Build this diagnostic as the ordinary research user.' >&2
    exit 2
fi
mkdir -p .build
xcrun clang -std=c11 -Wall -Wextra -Werror -O2 \
    -DAFB_RESEARCH_UID="$research_uid" -DAFB_RESEARCH_GID="$research_gid" \
    Sources/Diagnostics/IdentitySignalControl.c -o .build/identity-signal-control
codesign --force --sign - --options runtime .build/identity-signal-control
codesign --verify --strict .build/identity-signal-control
.build/identity-signal-control --preflight
