# Isolated WebKit activity experiment

This directory contains a research patch for WebKit revision `94f9b7905e3ce9a3d7497f26b563adcad6b7525f`. It is not installed in the browser. The full engine and its integration code have not been built or tested.

The patch adds one configuration choice. Each WebPageProxy captures it as a constant policy. Native mode preserves outgoing state. Stable mode sets five activity flags before content-process updates and page creation. Native UI state, drawing, throttling, and Secure Event Input code stay unchanged.

## Reproduce the bounded checks

From the project root, fetch the twelve pinned source files and verify the generated patch:

```sh
python3 tools/prepare_webkit_activity.py --fetch --check
python3 scripts/test-activity-projection.py
```

The fetch refuses changed cached files and mismatched downloads. It does not fetch a full engine. Source lengths and hashes appear in webkit-source-manifest.json.

After editing ContentActivityProjection.h or the generator, regenerate the patch:

```sh
python3 tools/prepare_webkit_activity.py
```

Review the resulting patch before committing. The generator applies it with zero fuzz to temporary source copies and compares the exact output. It also checks that the native activity calculation remains unchanged.

The standalone C++ test compiles the actual projection header. It extracts the exact ActivityState enum declaration from the pinned, hash-verified source header. It checks all 65,536 native flag combinations in both modes. Checks cover native identity, the five required flags, preservation of every other flag, and idempotence. It does not compile WTF OptionSet, WebPageProxy, Cocoa integration, or a browser.

## Remaining gates

A full source inventory, bounded engine build, framework identity checks, native owner instrumentation, and live external comparisons remain required. Current password state must be protected before resumed input. Private generated input is a functional baseline, not physical-human evidence.

Keep the frozen physical browser and approved probes unchanged. [Design and acceptance gates](../docs/research/activity-boundary-plan.md).
