# Broader cache setting and content lookup

The fifth full build still reported zero-exit/no-output failures in WebGPU and PAL after Swift caching was disabled. The narrower switch did not clear all failing tasks. The monitor stopped through its own cleanup. The failed evidence remains saved.

The sixth build uses COMPILATION_CACHE_ENABLE_CACHING=NO. This is the exact umbrella setting that passed the narrow JavaScriptCore target. Both Swift and C++ compilation caching are disabled for this isolated build. The complete engine remains unverified.

The diagnostic now reads its own content process executable through proc_pidpath. It no longer depends on NSRunningApplication listing an XPC helper. The expected workspace path requirement remains. This change compiles but has no positive custom-engine runtime result yet.

All 100 Python checks pass. The prepared engine-stable diagnostic compiles in Swift 6 with warnings as errors. The frozen physical browser and probes remain unchanged. Native password ownership, current editor state before resumed input, and the complete lifecycle matrix remain runtime gates.

Source staging now compares decoded bytes without universal newline conversion. A CRLF change must cause refusal before any other file changes. The new regression check passes.

See [saved evidence](evidence/engine-build-retry-results.json).
