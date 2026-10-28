# External inspector discovery control

Milestone 145 runs three unattended Cocoa discovery controls against fresh readable references. None discovers its fixture page. The final control creates a local-machine target but finds no owned application. No attachment test or protected-browser comparison follows. These failures establish no browser protection.

## Scope and implementation

InspectorDiscoveryControl accepts only the hash-pinned InspectableControl process. PreviewAXScope rejects other hosts, changed identities, and unrelated renderers. The URL must identify the private loopback fixture. The client queries application identifiers only for the verified host and its verified renderers. It reads page URLs only within those applications. It saves no unrelated page metadata.

The native diagnostic uses installed Objective-C method encodings before each dynamic call. It loads the fixed WebInspector framework and constructs a manager in its own process. It sends no debugger message, opens no channel, posts no input, and requests no macOS grant. Its discovery loop has an eight-second bound and a 15-second alarm.

The Python runner starts one readable reference and one private fixture. It gives the native child an 18-second timeout. It records only the character count of native stderr. It closes the reference and fixture on success or failure. It never launches the protected preview.

## Three measured controls

The first control constructs RWIManager through new. It finds no current-machine target. Metadata then identifies sharedManager as a separate class method. The second control uses sharedManager but still finds no current-machine target.

Further metadata identifies explicit local-target creation and removal methods. The third control uses those exact methods in the helper process. It observes the local-machine target, then requests its removal during cleanup. It finds zero owned applications and zero matching fixture pages. All three children exit normally. The independent oracle records zero submissions in every trial.

The result narrows the client initialization problem. It does not establish a connection to the daemon or the daemon's admission decision. The installed private API remains undocumented here. Missing signing information, a lifecycle step, or another client requirement could explain the result. No entitlement requirement is established by these trials.

## Reproduction and checks

```sh
bash scripts/build-inspector-discovery-control.sh
PYTHONPATH=tools python3 tools/run_inspector_discovery_control.py \
  --output artifacts/FRESH
```

Swift 6 compilation with warnings as errors passes. Four native boundary controls refuse before manager initialization. They cover missing arguments, an external URL, an unrelated PID, and an invalid port. All three references and fixtures stop. The client process also exits. The preview and granted recorder retain their pinned hashes.

The source and builder remain separate from every permissioned app. No browser image changes, new grant, administrator access, or physical input occurs. The pending system alert does not affect this experiment because the client captures no screen content and requires no foreground input.

See [results](evidence/inspector-discovery-control-results.json) and [client research](research/cocoa-inspector-client.md). The next client step must establish reference discovery and connection state before attachment or script evaluation. Agent-free acceptance remains unmet.
