# Remaining agent-free gaps

Status after milestone 116: no integrated agent-free browser exists. The cross-user channel comparison passes. The ordinary usable candidate and separate diagnostics still cover different parts of the goal. Passing their checks does not combine their protections.

The existing PRD defines two outcomes. Action prevention stops an external agent from completing a website task. Disclosure prevention stops recovery of a fresh secret shown only inside the browser. The broad agent-free claim requires both, plus working human use. Physical typing observed by a listener is not an autonomous input bypass.

## Missing engineering

1. One visible browser must combine the isolated renderer, private display channel, and trusted human navigation. The current pair stays hidden and accepts one fixed local address. It has no interactive address bar, links, or form input across the process boundary. The earlier keyboard browser remains a separate build. Completion requires a person to navigate ordinary HTTPS pages and complete a form in the integrated target.
2. Physical input must cross that boundary without accepting agent input. The earlier working router supports one built-in keyboard and US ASCII. Mouse input is disabled. The channel carries only navigation and pixels. It carries no keyboard, pointer, or scroll events. Original HID timestamps also do not reach the receiver. Completion requires normal physical input and refusal of permissioned synthetic and semantic input on that same build.
3. Browser state must not supply an alternative action route. Earlier candidates completed tasks after focus, visibility, or process-clock changes without admitted input. Milestone 116 denies the tested renderer pause, but its fixture measures page progress rather than task prevention. Completion requires the previous successful attack fixtures to fail on the integrated build while legitimate activity still works.

The relevant code is [the channel](../Sources/Channel/RendererChannel.swift), [the fixed-fixture renderer](../Sources/Diagnostics/ChannelRendererProbe.swift), and [the earlier keyboard router](../Sources/Browser/DeviceKeyboard.swift). The recorded action bypasses are in [timing findings](clock-channel-findings.md) and [lifecycle findings](lifecycle-findings.md).

## Unresolved privacy research

A capture path must remain unreadable to a permissioned external agent while the person can read the actual page. Some window and filtered-display captures returned black against the usable keyboard candidate. Unfiltered display and other required capture paths remain unverified. The protected BGRA and NV12 experiments also looked black directly to the person. Those configurations failed the human-visible output requirement.

A permissioned keyboard observer recognized the fixed phrase during a physical task. That establishes the measured observation route. It does not establish an autonomous website action or recovery of an unknown page-only secret. Input refusal and keyboard privacy therefore need separate results.

Completion requires a validated human-visible output design and matched capture tests with effective grants. The current project has no general private-output solution. This remains a research uncertainty, not merely an unfinished interface feature. See [capture findings](source-policy-capture-findings.md), [physical visibility failures](route-calibration.md), and [keyboard observation](keyboard-readiness-findings.md).

## Missing final validation

The integrated build needs one attack report with working human and attacker controls. It must cover direct browser transports, accessibility, synthetic and blind input, capture, lifecycle changes, and browser-created exports or session residue. Fresh page secrets and task outcomes must come from an independent oracle. Required inconclusive results cannot count as blocks.

Remote-inspector discovery currently omits the restricted target, but that does not prove every direct attachment path refuses. Several native and capture routes retain failed controls. Previous successful attacks must repeat against the final integrated build. Ordinary websites must also preserve navigation, forms, frames, redirects, and normal sessions. See [inspection limits](safari-remote-findings.md) and [the PRD contract](../PRD.md).

This is not a demand to test every future model. It is a demand to test the capabilities available to an adaptive external agent. A finite matrix supports a bounded claim about those capabilities. It cannot establish a universal theorem about all websites and future agents.

## Scope that must stay fixed

Root attacks, modified browser binaries, kernel exploits, malicious hardware, and external cameras already sit outside this PoC's threat model. An agent's independent use of another browser or unrelated API credentials is also outside the browser claim. Those capabilities are not new prerequisites for completion.

The recent isolation work addresses a real zero-input action bypass. The delivery gap is that its result remains separate from the physical browser. The next engineering deliverable is one human-usable browser with the combined protections and one end-to-end attack report. More component-test passes alone do not establish that deliverable. Strict private output remains the largest unresolved research question.
