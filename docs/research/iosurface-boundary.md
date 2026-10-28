# IOSurface access between processes

Research date: 2026-10-23. Sources are Apple documentation and the installed macOS 27 SDK. This report contains no runtime test or graphics-buffer enumeration.

## Known identifiers and readable buffers are separate questions

An IOSurface-backed pixel buffer creates another access question beyond screenshots. Can a separate process recover its pixels through `IOSurfaceLookup` if that process knows its identifier? A useful first test shares the identifier for one fake buffer between cooperating research processes. That calibration does not establish how an attacker discovers a browser buffer's identifier.

The current source creates clear pixel buffers before displaying them through a layer with `preventsCapture`. Layer capture exclusion does not document confidentiality for the producer's clear memory. It also does not establish cross-process readability. Both claims need separate evidence.

## Apple distinguishes global surfaces from explicit transfer

`IOSurfaceGetID` returns an identifier for a surface. `IOSurfaceLookup` performs a lookup and retain by identifier. The public declaration permits a null result. Those APIs alone do not promise that every caller can access every surface. [Apple IOSurface functions](https://developer.apple.com/documentation/iosurface/iosurface-functions)

`kIOSurfaceIsGlobal` is a creation property. Apple's description says that a true value permits any task to look up the surface by its identifier. The current SDK marks the key deprecated since macOS 10.11 and gives the reason "Global surfaces are insecure". This is a warning against an explicit global allocation. It is not a documented statement that every default allocation is global. [Apple global property](https://developer.apple.com/documentation/iosurface/kiosurfaceisglobal)

Apple documents `IOSurfaceCreateMachPort` as a way to transfer a reference securely without making the surface global. `IOSurfaceLookupFromMachPort` recreates the surface reference from that transferred port. A shared numeric identifier and a transferred Mach right are different inputs. A calibration that shares the right cannot answer whether the identifier alone grants access. [Apple Mach-port transfer API](https://developer.apple.com/documentation/IOSurface/IOSurfaceCreateMachPort(_:))

The SDK also says IOSurface attachments cannot change underlying surface properties. Setting an attachment after allocation must not stand in for a creation-property test. The relevant declarations appear in `IOSurface.framework/Headers/IOSurfaceRef.h` and `IOSurfaceObjC.h` under the installed SDK's `System/Library/Frameworks` directory.

## Core Video defaults need measurement

Apple says the presence of `kCVPixelBufferIOSurfacePropertiesKey` requests IOSurface allocation. Its value is a dictionary of optional IOSurface properties. An empty dictionary requests the default options. The reviewed documentation does not specify whether that default permits cross-process lookup by numeric identifier on the current OS. [Apple Core Video allocation key](https://developer.apple.com/documentation/corevideo/kcvpixelbufferiosurfacepropertieskey)

The project's producer requests an empty dictionary for its BGRA allocation. The same allocation rule applies to any NV12 destination that uses an empty dictionary. The research must describe these cases as default allocation, rather than assume either global or private access.

`CVPixelBufferGetIOSurface` returns the backing surface or null. A successful allocation without a backing surface cannot test IOSurface lookup. The producer must retain the buffer until the reader finishes, so a released allocation cannot explain a lookup failure. [Apple backing-surface API](https://developer.apple.com/documentation/corevideo/cvpixelbuffergetiosurface(_:))

Apple cautions that identifier transfer does not automatically protect pool buffers from reuse while another process uses them. Mach-port transfer handles that coordination. This is a lifetime issue separate from permission to read. A small calibration should avoid a pool and hold each buffer unchanged until acknowledgement. [Apple pixel-buffer sharing discussion](https://developer.apple.com/documentation/corevideo/cvpixelbuffercreatewithiosurface(_:_:_:_:))

## Public protected-memory controls are not established

The reviewed public IOSurface headers expose dimensions, formats, plane layout, cache settings, names, and transfer functions. They do not expose a documented general-purpose secure-pixel creation option. The reviewed Apple entitlement documentation does not identify a macOS entitlement that turns arbitrary CPU-written IOSurface pixels into protected media memory.

This is a bounded research result. It does not prove that Apple has no private protected-media allocation path. It also does not prove that an ordinary application can access such a path through an undocumented dictionary key. Adding a property with a plausible name is not evidence that the kernel enforces confidentiality.

`AVSampleBufferDisplayLayer.preventsCapture` describes protection against screen capture. It does not state that it revokes access to existing references, changes the backing allocation's lookup policy, or erases the producer's clear copy. The calibration must test any claimed effect on lookup directly. [Apple layer protection API](https://developer.apple.com/documentation/avfoundation/avsamplebufferdisplaylayer/preventscapture)

## A bounded two-process calibration

The producer creates a single small buffer containing a fresh fake marker. A separate reader receives only the exact identifier that the producer created. The handshake contains no pixel bytes, Mach port, XPC surface object, or expected marker. An evaluator retains the expected marker for comparison.

The producer retains the same unchanged buffer throughout each trial. The reader calls `IOSurfaceLookup` for that one supplied identifier. If lookup succeeds, the reader requests a read-only lock and reads only the known fake allocation within its reported bounds. The test records allocation, lookup, lock, read, and marker-comparison results separately. It does not scan identifiers or inspect another application's surfaces.

The matched cases are:

| Producer allocation | Question |
| --- | --- |
| Direct `IOSurfaceCreate`, global property absent | What does direct default allocation permit? |
| Direct allocation, global property false | Does an explicit false value change the observed result? |
| Direct allocation, global property true | Does the documented global route supply a working positive control? |
| `CVPixelBufferCreate`, empty IOSurface properties | What does the browser's current allocation request permit? |
| Core Video allocation, global property false | Does the nested creation option change the result? |
| Core Video allocation, global property true | Does Core Video pass the explicit global request through? |

The global cases belong only to the isolated fake-buffer calibration. They must never change the browser's allocation policy. Deprecation is part of the recorded configuration.

A second comparison can attach each retained fake buffer to an unprotected or capture-protected display layer. The test then repeats the exact-ID read before and after enqueue. That comparison tests whether layer protection changes the observed access. The reader still receives no surface reference or pixel data.

## Interpretation limits

If default Core Video allocation is readable by exact identifier, the result proves conditional pixel access on that OS and process configuration. The browser attack still needs an independently justified identifier-disclosure route. An instrumented producer that prints the identifier does not supply that missing evidence.

If only explicit global allocations are readable, the result supports the importance of allocation policy. It does not prove that every browser intermediate buffer uses that policy. If every cross-process case fails, a missing positive control limits conclusions about the reader implementation or OS behavior.

If lookup succeeds but locking or reading fails, the result does not establish pixel disclosure. A correct fake-marker match establishes disclosure for the cooperating test allocation. A black screenshot remains irrelevant to that direct-buffer result.

No experiment in this report needs root, graphics-driver changes, another app's buffer, or system-wide identifier enumeration. A browser bypass requires additional evidence tied to the actual browser allocation and its independently discoverable identifier.
