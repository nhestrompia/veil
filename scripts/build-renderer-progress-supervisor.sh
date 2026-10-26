#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
research_uid=$(/usr/bin/id -u)
research_gid=$(/usr/bin/id -g)
if [ "$research_uid" -lt 500 ] || [ "$research_gid" -eq 0 ]; then exit 2; fi
xcrun clang -std=c11 -Wall -Wextra -Werror -O2 -DAFB_PROGRESS_CONTROL \
    -DAFB_RESEARCH_UID="$research_uid" -DAFB_RESEARCH_GID="$research_gid" \
    "$PWD/Sources/Diagnostics/RendererIdentitySupervisor.c" -o .build/renderer-progress-supervisor
codesign --force --sign - --options runtime .build/renderer-progress-supervisor
codesign --verify --strict .build/renderer-progress-supervisor
.build/renderer-progress-supervisor --preflight
