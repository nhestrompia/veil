import AppKit

@main
enum DeviceEventQueueTests {
    @MainActor static func main() {
        let app = DeviceKeyboardApplication.shared as! DeviceKeyboardApplication
        let gate = DeviceEventGate()
        let event = NSEvent.keyEvent(with: .keyDown, location: .zero, modifierFlags: [], timestamp: 0,
            windowNumber: 0, context: nil, characters: "x", charactersIgnoringModifiers: "x",
            isARepeat: false, keyCode: 7)!
        gate.authorize(event)
        app.postEvent(event, atStart: true)
        let queued = app.nextEvent(matching: .keyDown, until: Date(timeIntervalSinceNow: 1),
            inMode: .default, dequeue: true)!
        // Queue insertion copied this event in the initial live experiment.
        if queued === event {
            precondition(gate.consume(queued))
        } else {
            precondition(!gate.consume(queued), "A queue copy must not inherit authorization")
        }
        let copy = NSEvent(cgEvent: event.cgEvent!)!
        precondition(copy !== event)
        gate.authorize(event)
        precondition(!gate.consume(copy), "Matching event contents must not authorize a new object")
        gate.clear()
        precondition(!gate.consume(event), "Focus loss must invalidate pending events")
        let accepted = app.acceptedEventCount
        let refused = app.refusedEventCount
        app.dispatchDeviceEvent(event)
        precondition(app.acceptedEventCount == accepted + 1, "Direct application dispatch must accept its exact event")
        app.sendEvent(event)
        app.sendEvent(copy)
        precondition(app.refusedEventCount == refused + 2, "Replays and copied events must fail")
        var openedLocations = 0
        app.onOpenLocation = { openedLocations += 1 }
        let locationKey = NSEvent.keyEvent(with: .keyDown, location: .zero, modifierFlags: .command,
            timestamp: 0, windowNumber: 0, context: nil, characters: "l", charactersIgnoringModifiers: "l",
            isARepeat: false, keyCode: 37)!
        app.sendEvent(locationKey)
        precondition(openedLocations == 0, "Ambient shortcuts must not invoke navigation")
        app.dispatchDeviceEvent(locationKey)
        precondition(openedLocations == 1, "The authorized shortcut must invoke navigation")
        app.sendEvent(locationKey)
        precondition(openedLocations == 1, "Replayed shortcuts must fail")
        print("Device dispatch: exact identity, one-time delivery, copied-event rejection, and reset passed")
    }
}
