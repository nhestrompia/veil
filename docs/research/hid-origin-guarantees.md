# HID origin guarantees

Research date: 2026-10-25. This review uses current Apple documentation and Apple's published IOHIDFamily source. It runs no device operation or input attack.

## Device identity does not establish human input

Before this change, the keyboard router accepted Space from any matching keyboard while its window had focus. It then binds that `IOHIDDevice` object. Removal clears the binding. This prevents a different device from inheriting an existing binding, but the initial device remains unauthenticated. The code already logs `bootstrapAttested=false`. [Current router](../../Sources/Browser/DeviceKeyboard.swift)

Apple supports software devices that dispatch input reports. CoreHID clients communicate with physical and virtual peripherals through the same framework. A callback therefore needs a source policy before it can authorize application input. [Apple CoreHID overview](https://developer.apple.com/documentation/corehid), [Apple virtual-device guide](https://developer.apple.com/documentation/corehid/creatingvirtualdevices)

The reviewed public contracts supply no attestation that a report represents a person's intended action. This is an absence of a documented guarantee, not proof that every software source is indistinguishable.

## Developer and private entitlements differ

Apple documents `com.apple.developer.hid.virtual.device` as a virtual-device entitlement. The published resource client accepts this entitlement or `com.apple.hid.manager.user-access-device`. Only the latter path sets its internal `_privileged` flag. Device creation overwrites the privilege property with that result. [Apple entitlement](https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.developer.hid.virtual.device), [Apple resource-client source, initWithTask and createDevice](https://github.com/apple-oss-distributions/IOHIDFamily/blob/main/IOHIDFamily/IOHIDResourceUserClient.cpp)

That distinction affects published device identity. `IOHIDUserDevice::initWithProperties` forces the virtual-device marker true without private privilege. Its `newTransportString` returns `Virtual` without that privilege, even when the caller requests another transport. Vendor, product, and location getters read the supplied dictionary. [Apple user-device source, lines 60-82, 124-135, 168-191, and 267-276](https://github.com/apple-oss-distributions/IOHIDFamily/blob/main/IOHIDFamily/IOHIDUserDevice.cpp#L60)

Thus, caller-set metadata does not establish that a normally entitled developer can spoof every published field. The transport and virtual marker have stronger source evidence than vendor or product numbers. This evidence describes the reviewed implementation, not every device driver or deployed macOS build.

The marker's string is `HIDVirtualDevice`, despite the spelling of its constant, `kIOHIDVirtualHIDevice`. The installed public `IOHIDParameter.h` declares that constant. The header supplies no general human-origin guarantee. [Apple parameter header, line 58](https://github.com/apple-oss-distributions/IOHIDFamily/blob/main/IOHIDSystem/IOKit/hidsystem/IOHIDParameter.h#L58)

## Legacy posting needs a separate refusal

With `kIOHIDPostHIDManagerEvent`, `IOHIDSystem::extPostEventGated` creates an `IOHIDKeyboardDevice` attached to the system object. It separately creates an `IOHIDPointingDevice`. These classes post generated reports through `handleReport`. [Apple system source, lines 2992-3024](https://github.com/apple-oss-distributions/IOHIDFamily/blob/main/IOHIDSystem/IOHIDSystem.cpp#L2992), [Apple keyboard source, lines 288-326](https://github.com/apple-oss-distributions/IOHIDFamily/blob/main/IOHIDSystem/IOHIDKeyboardDevice.cpp#L288), [Apple pointer source, lines 401-413](https://github.com/apple-oss-distributions/IOHIDFamily/blob/main/IOHIDSystem/IOHIDPointingDevice.cpp#L401)

Both classes inherit `IOHIDDeviceShim`. Its transport starts unset. It derives a transport only through an `IOHIDevice` provider. With the direct system provider, its transport getter can return null. This source does not force the virtual marker true for that path. A rule that rejects only an explicit virtual marker misses this source hypothesis. [Apple shim source, lines 38-90 and 161-187](https://github.com/apple-oss-distributions/IOHIDFamily/blob/main/IOHIDSystem/IOHIDDeviceShim.cpp#L38)

The keyboard shim's matching function also requires the compatibility-interface property. An ordinary keyboard match need not expose this shim. Missing callbacks therefore do not prove that the shim lacks software input capability. [Apple keyboard matching source, lines 397-405](https://github.com/apple-oss-distributions/IOHIDFamily/blob/main/IOHIDSystem/IOHIDKeyboardDevice.cpp#L397)

## Source policy justified by this evidence

A conservative policy can reject these known software routes before binding. The following rules are proposed research policy, not a complete hardware authentication scheme.

- Reject an explicit virtual marker or `Virtual` transport.
- Reject a service or ancestor that conforms to `IOHIDUserDevice` or `IOHIDResourceDeviceUserClient`.
- Reject the keyboard and pointer shim classes when their provider is `IOHIDSystem`.
- Reject missing, malformed, cyclic, or incomplete topology.
- Allow only a hardware ancestry measured for the supported machine. Keep unknown devices refused until a separate physical control succeeds.

Use actual object classes, not an `IOClass` property from a device dictionary. `IOObjectGetClass` reads the kernel's metaclass. `IOObjectConformsTo` checks that class and its subclasses. These APIs give a stronger check against caller-supplied descriptive properties. They do not certify human intent. [Apple class API](https://developer.apple.com/documentation/iokit/1514756-ioobjectgetclass), [Apple conformance API](https://developer.apple.com/documentation/iokit/1514505-ioobjectconformsto)

Do not reject every compatibility shim solely from its base class. Apple also uses shim code to bridge hardware providers. A broad rejection could remove usable physical input. The built-in keyboard's actual ancestry must precede an allow rule. [Apple shim provider handling](https://github.com/apple-oss-distributions/IOHIDFamily/blob/main/IOHIDSystem/IOHIDDeviceShim.cpp#L50)

## Current machine observations

The root agent ran a read-only registry audit during this research. One keyboard service used the FIFO transport and the Apple hardware chain below. A second keyboard service used the system shim chain. Both lacked a virtual marker. [Read-only audit](../evidence/hid-source-audit.json)

```text
AppleHIDTransportHIDDevice
AppleHIDTransportInterface
AppleHIDTransportProtocolSCMFIFO
AppleHIDTransportDeviceFIFO
AppleDockChannelDevice
AppleDockChannel
AppleARMIODevice
```

The corrected audit also found an existing vendor-specific service with the following software chain. It reported USB transport and a true `HIDVirtualDevice` marker.

```text
IOHIDUserDevice
IOHIDResourceDeviceUserClient
IOHIDResource
IOResources
```

This observation does not identify its creating process, entitlement, or input capabilities. It shows why transport alone cannot classify this software service. The system shim lacks the virtual marker, which supports the separate ancestry check. The initial audit used the wrong marker key. The corrected audit replaces that result.

A narrow candidate can accept only the exact FIFO prefix above for keyboard usage. It must refuse unknown sources. That limit supports this Mac's configuration only. Physical input after the policy change still needs its own control.

## Next autonomous experiment

The immediate audit can become a reproducible policy check. It needs no device open, report callback, synthetic input, new grant, event hook, or driver installation.

1. Enumerate keyboard services through IOKit registry matching.
2. Read only transport, virtual-marker state, actual service class, and ancestor classes.
3. Stop traversal at a fixed depth and record incomplete traversal as unknown.
4. Evaluate the proposed refusal rules without changing the browser.
5. Save aggregate results and class chains without names, serial numbers, vendor numbers, product numbers, or location identifiers.

Apple exposes service handles through `IOHIDDeviceGetService`. Registry APIs expose parents and classes. Parent traversal returns retained handles that the caller must release. A single-parent walk covers the first parent only. Complete policy must refuse unexamined alternate ancestry or inspect all parents. [Apple HID service API collection](https://developer.apple.com/documentation/iokit/iohiddevice_h_user-space), [Apple parent API](https://developer.apple.com/documentation/iokit/1514454-ioregistryentrygetparententry), [Apple IOKit access API](https://developer.apple.com/documentation/iokit/iokitlib_h)

This audit can show whether a narrow filter preserves a plausible built-in keyboard source. It cannot replace physical action evidence. A missing software-device control leaves the filter's attack result unmeasured.

A later creation-only control can request USB transport and a false virtual marker, then inspect the actual published service. It must use a legitimate entitled executable and send zero reports. The present creation probe lacks that entitlement. Its three refused trials supply no entitled positive control. [Probe source](../../Sources/HIDAttack/VirtualDeviceProbe.swift), [Saved creation results](../evidence/virtual-device-results.json)

## Remaining guarantee

A registry service identity lasts within the OS session. Apple documents entry IDs as valid until reboot. An identity can support binding to an existing object. It does not prove who caused each report. [Apple registry identity API](https://developer.apple.com/documentation/iokit/1514719-ioregistryentrygetregistryentryi)

The project still lacks a documented guarantee that approved hardware routes cannot receive software-generated actions through any permitted driver path. It also lacks authenticated human consent for initial binding. Those gaps remain separate from ordinary CGEvent refusal.

Apple's source links above target mutable `main` as read on the research date. This review does not establish binary equivalence with macOS 26.6. No privileged entitlement, root operation, driver installation, or permission change occurred.
