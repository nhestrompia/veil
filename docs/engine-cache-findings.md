# Swift compilation-cache comparison

Correction from milestone 74: quiet-mode zero-exit messages are cosmetic. A forced PAL compile emitted one and exited zero. Earlier full-build cache attribution was unsupported because the monitors were interrupted before final exit. The current build uses normal logging and upstream cache defaults. See [the correction](engine-log-findings.md).

The fourth full build reached Swift tasks in JavaScriptCore, WebGPU, and PAL. Xcode reported successful command exit codes but treated those tasks as failed. The log contained cache-miss messages and no source diagnostic for those failures. The build monitor stopped through its own cleanup before the comparison.

A narrow JavaScriptCore build disabled compilation caching. Its Swift tasks compiled, and the framework linked successfully. The comparison retained the deployment target, source, and target-local temporary directory. The broader cache setting also changed C++ compilation, so this result alone does not isolate every cache component.

The installed Xcode Swift.xcspec declares SWIFT_ENABLE_COMPILE_CACHE. Its default comes from COMPILATION_CACHE_ENABLE_CACHING. The full build now sets only SWIFT_ENABLE_COMPILE_CACHE to NO. This leaves C++ caching enabled. That narrower setting remains a full-build experiment.

The fifth full build restarted. A completed custom engine and runtime tests remain pending. Do not treat the successful JavaScriptCore target as a successful WebKit integration build.

Apple documents the umbrella setting as a compilation cache. See [Build settings reference](https://developer.apple.com/documentation/xcode/build-settings-reference). The local Swift.xcspec supplied the exact narrower setting for Xcode 27.1.

See [saved evidence](evidence/engine-cache-results.json).
