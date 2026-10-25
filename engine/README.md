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

A bounded engine build, framework identity checks, native owner instrumentation, and live external comparisons remain required. Current password state must be protected before resumed input. Private generated input is a functional baseline, not physical-human evidence.

Keep the frozen physical browser and approved probes unchanged. [Design and acceptance gates](../docs/research/activity-boundary-plan.md).

## Prepare full source

The full source dependency is available at the pinned revision. Run the preparation tool before applying a patch:

```sh
python3 tools/prepare_webkit_source.py
```

The tool uses an isolated shallow sparse clone. It retains Configurations, Source, Tools, WebKitLibraries, and WebKit.xcworkspace. It checks the revision and twelve pinned files. Reuse requires pristine files and the source receipt.

The preparation limits Git metadata to 2 GiB and checked-out files to 6 GiB. It preserves 60 GiB of free disk space. Cleanup stops only its own process group. The actual download retained about 1.8 GB. The archive endpoint returned HTTP 422, so the tool uses the official Git dependency method.

The full-source audit found one live activity sender and one shared creation assignment. Remote pages, process swaps, and recovery use that creation path. Initial empty documents precede projection into WebCore. A separate SetInitialFocus route can change element focus. These limits require runtime tests.

Milestone 64 saved pristine source. Milestone 66 applied the exact patch and started the bounded build. The next build must set WEBKIT_OUTPUTDIR inside the workspace before invoking upstream scripts. Native ownership and runtime framework identity remain open gates.

See [the full-source audit](../docs/research/activity-full-source-audit.md) and [preparation evidence](../docs/evidence/engine-source-results.json).

## Apply and build the research engine

Apply the exact patch to the isolated checkout:

```sh
python3 tools/build_research_webkit.py
```

The tool checks the pinned revision and every affected old or new file before writing. Unknown changes cause refusal. A partial application can resume. Atomic file replacement and final hashes check the result.

Start the bounded build:

```sh
python3 tools/build_research_webkit.py --build
```

The build uses the upstream Everything up to WebKit scheme. It includes engine dependencies. Four jobs run at reduced priority. Outputs, temporary files, module caches, and derived data stay inside the workspace. WEBKIT_OUTPUTDIR prevents upstream user-preference cleanup. The build preserves 60 GiB of free disk space. Its default limit is two hours. Failure cleanup targets only its own process group.

The first attempt stopped before compilation because root configurations were absent. The source list now includes Configurations. The dependency scheme also replaces the incomplete WebKit-only scheme. The corrected attempt started compilation. No completed engine or runtime result exists yet.

The build log and receipts are in .build/webkit-engine/. A successful command does not prove which frameworks a research browser loads. Check UI and content-process framework identities before live claims. The frozen physical browser and permissioned probes remain unchanged.
