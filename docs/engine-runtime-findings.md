# Engine startup and identity gates

Milestone 67 adds diagnostic-only configuration and identity checks. The private activity choice requires exact getter and setter signatures. UI startup requires WebKit, WebCore, and JavaScriptCore images inside the research output directory.

After the private baseline, the diagnostic identifies its own content process. The controller checks its executable and mapped framework paths. Missing maps or unexpected framework paths cause refusal before external attacks. These positive identity checks remain untested against a completed custom engine.

A real system-framework fallback test refused startup before window creation. Four local checks cover incomplete builds, system paths, incomplete maps, and complete expected maps. All 99 Python checks pass. The diagnostic compiles in Swift 6 with warnings as errors.

The engine diagnostic uses an ad hoc signature without hardened runtime so its own process can load custom frameworks. This affects only InternalKeyboardControl. The physical browser and approved probes remain frozen. Engine modes refuse logical host overrides. The loader environment applies only to the diagnostic child.

The second build reached Metal shaders and stopped because the actual compiler was absent. Apple's MetalToolchain component 27A266a downloaded successfully. Its compiler reports version 32023.921 and executes. The third attempt uses quiet logs and a macOS 26 deployment target. It remains incomplete.

The earlier launcher-path check was insufficient. The build now executes the Metal version command before compilation. Per-attempt build receipts preserve failure evidence. Runtime lifecycle and native ownership checks still require a completed, identified engine.

See [saved evidence](evidence/engine-runtime-gates-results.json) and [build instructions](../engine/README.md).
