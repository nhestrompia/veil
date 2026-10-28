# Local inspector startup policy

A working native UI attack confirms that remote inspectability and local developer tools need separate controls. The new LocalInspectorControl keeps `WKWebView.isInspectable=false`. It omits only the startup rule that forces local developer extras off. The control uses the ordinary browser code, with a distinct window title and a 90-second termination timer.

With `-WebKitDebugDeveloperExtrasEnabled YES`, its page menu offered Inspect Element. The native UI tool opened the inspector and evaluated JavaScript through its Console. The read expression returned the correct trial path and marker. The action expression completed one task, which the independent fixture oracle recorded.

## Protected-shell comparison

Two fresh AgentFreeBrowser processes received the same launch argument. Both loaded their fixture page and opened its ordinary context menu. Neither menu contained Inspect Element. Neither inspection attempt opened the inspector or produced a website action.

The first protected trial also completed a separate ordinary-input control after its inspector phase. The oracle recorded no submission during inspection. It then recorded one refused submission after macOS capitalization changed the fake input, followed by one accepted submission with the exact value. Those later actions are normal input controls, not inspector bypasses.

These shells deliberately retain Accessibility and ordinary input. The comparison tests the local inspection configuration without device-input or capture restrictions. It does not establish that this shell is agent-resistant.

## Reproduction and evidence

`bash scripts/build-local-inspector-control.sh` generates a disposable control from the current browser source. The script removes exactly one startup-policy block. It preserves the false remote-inspection setting and uses the same sandbox entitlements as the protected shell. No production source changes.

`tools/prepare_inspector_control.py --target LocalInspectorControl` creates a fresh trial and waits for the native UI test. The controller also accepts the inspectable reference and the protected shell. It records oracle submissions and exact process cleanup. New results record whether the original target remains alive when observation ends.

The [four trial records](evidence/local-inspector-policy-results.json) include the successful control, two protected comparisons, and one failed UI attempt. That failed call lasted about 189 seconds and outlasted the diagnostic timer. It returned a relaunched empty window. The result remains inconclusive, and exact cleanup also removed that extra process. The retry used the existing UI binding and completed within the timer.

All four controller cleanups passed. The extra process also passed cleanup. The probe executable remained unchanged. No persistent preference, Safari setting, permission scope, or user browser profile changed.

## Limits

The two protected observations cover one local context-menu route. They do not exclude every inspector transport or future WebKit change. Remote inspector attachment remains separate. Physical visibility and usability of the latest restricted device browser also remain unverified.

The result supports the existing startup rule. It also shows why `isInspectable=false` alone cannot establish local inspection prevention on this installed framework. Agent-free status remains unproven.
