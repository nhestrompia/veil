# Xcode temporary-directory correction

The full build stopped because Xcode's custom Mach interface rule could not create temporary files. The assigned shared directory was inside OBJROOT. The rule's sandbox denies that directory.

A narrow reproduction used the actual generated sandbox profile. Creating a temporary directory in the shared location failed. The same operation in TARGET_TEMP_DIR passed. Direct Mach generation outside that sandbox also passed.

The build now passes `TMPDIR=$(TARGET_TEMP_DIR)/` as an Xcode setting. Each target gets its own writable temporary directory. Outputs remain inside the workspace. The correction does not disable script sandboxing or change engine source.

The narrow WTF target then passed. It generated MachExceptions.h, MachExceptionsUser.c, MachExceptionsServer.h, and MachExceptionsServer.c. The original target failed before this change. This live comparison exercises the failed build path.

The full incremental build restarted with the correction. It remains incomplete. Runtime framework identities, lifecycle resistance, and resumed password protection remain unverified for the custom engine.

See [saved evidence](evidence/engine-temp-results.json).
