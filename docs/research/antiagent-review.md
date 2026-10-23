# What Antiagent established

Reviewed October 23, 2026, at `/Users/nhestrompia/Projects/antiagent`.

Antiagent found useful ways to stop particular automation clients. It did not establish a way to prevent adaptive agents from using a website. Its best reusable asset is the experiment method: test a working attacker, keep positive controls, record actual outcomes, and reject a claim when one bypass succeeds.

## Review scope

The source checkout reports HEAD `678b007b5e38a6ec275eeff72a0c435ad2843ec9`. This review reads the current working files, including staged changes. The checkout contains one staged modification and 336 staged deletions. Many deleted files are historical image and recording evidence. These changes predate this review.

I reviewed the root README, canonical spec, findings, selected JSON results, detector code, combined defense, and strict verifier. I did not restore deleted files or rerun live browser experiments. Historical results below come from the project's records, not new measurements.

The previous website-only deployment constraint belongs to Antiagent. The new browser project deliberately changes that constraint. Antiagent's spec is background evidence, not the specification for this browser.

## Results that matter for the browser

| Experiment | What worked | What did not work | Consequence |
| --- | --- | --- | --- |
| Randomized canvas | Fixed replay fell from 30/30 completions to 0/30 in the recorded trials. Native action selectors disappeared. | Drawing instrumentation completed 30/30 randomized tasks. A screenshot-only assistant completed 1/1. | Keep layout stable for people. Randomization is not the browser's protection mechanism. |
| Combined defense | Default Playwright, suppressed-marker locators, page-created clicks, and a canvas hook each stopped in 3/3 trials. | Screenshot/OCR/CDP completed 3/3. An assistant also completed 1/1 through visual tools. | The browser must deny the controller's access, rather than depend on page detection. |
| Combined temporal guards | The Runtime-enabled control stopped in 3/3 sessions. | Bare CDP completed 3/3 without Runtime or Debugger. Each session used 194 screenshots. | Optional debugger behavior cannot supply a mandatory agent signal. |
| Current-stack acceptance | The strict verifier rejects completed sessions before it considers errors. | One session completed. Two sessions had OCR errors, which remain inconclusive. | Keep failure, explicit refusal, and unavailable evidence separate. |
| DRM overlay | Encrypted playback worked in the documented Chrome environment. | A transparent protected video did not hide the separate canvas. An opaque overlay also hid it from people. | Do not transfer media protection claims to arbitrary HTML. |
| Interface inside encrypted media | Native computer-use capture and the view screenshot omitted the recorded interface. Encrypted canvas copies were black. | Compositor screenshots recovered the interface. The experiment was a prerecorded image, not an interactive web app. | Preserve this as a route-specific result. Do not use DRM as the MVP browser architecture. |
| Optional Playwright artifacts | Bindings, clock installation, and snapshot instrumentation triggered particular gates. | Clients without those features and bare screenshot/input clients still passed. Late detection could follow disclosure. | A missing marker never establishes human control. |
| Closed roots and workers | Closed roots stopped standard role locators. Worker rendering stopped a main-page drawing observer. | Privileged DOM inspection, accessibility access, worker interception, and screenshots supplied other routes. | Keep normal web rendering. Rewriting every website would add compatibility costs without closing the known bypass. |
| Integrity and API locks | Locks stopped later replacement. Integrity rejected named resource substitutions while the HTML trust anchor remained intact. | Preload hooks ran first. HTML replacement removed an integrity anchor. Intact-page screenshot input also worked. | These controls protect particular resources or execution order. They do not revoke the browser controller. |

The recorded sample sizes describe those fixtures and clients. They are not estimates for all agents or websites.

Sources for these rows:

- [Randomized canvas findings](/Users/nhestrompia/Projects/antiagent/docs/randomized-canvas-findings.md) and [JSON results](/Users/nhestrompia/Projects/antiagent/docs/randomized-canvas-results.json).
- [Combined defense findings](/Users/nhestrompia/Projects/antiagent/docs/combined-defense-findings.md) and [JSON results](/Users/nhestrompia/Projects/antiagent/docs/combined-defense-results.json).
- [Combined guards findings](/Users/nhestrompia/Projects/antiagent/docs/combined-guards-findings.md) and [JSON results](/Users/nhestrompia/Projects/antiagent/docs/combined-guards-results.json).
- [Current-stack check](/Users/nhestrompia/Projects/antiagent/docs/current-stack-verification.md) and [JSON results](/Users/nhestrompia/Projects/antiagent/docs/current-stack-verification-results.json).
- [Phase 0 findings](/Users/nhestrompia/Projects/antiagent/docs/phase0-findings.md) and [protected interface findings](/Users/nhestrompia/Projects/antiagent/docs/protected-ui-findings.md).
- [Binding findings](/Users/nhestrompia/Projects/antiagent/docs/playwright-artifact-findings.md) and [instrumentation findings](/Users/nhestrompia/Projects/antiagent/docs/playwright-instrumentation-findings.md).
- [Closed roots](/Users/nhestrompia/Projects/antiagent/docs/shadow-findings.md), [workers](/Users/nhestrompia/Projects/antiagent/docs/worker-findings.md), [API locks](/Users/nhestrompia/Projects/antiagent/docs/hardening-findings.md), and [integrity](/Users/nhestrompia/Projects/antiagent/docs/integrity-findings.md).

## Implementation checks

`src/automation-artifacts.js` inspects optional property names. Its comment correctly limits the detector to optional instrumentation. `src/combined-defense.js` runs those checks in website code and implements canvas rendering, temporal noise, and pointer constraints. None of those modules owns the external debugger transport.

`scripts/benchmark-bare-cdp.mjs` requires explicit blocks under `--require-blocking`. It rejects any completed task, empty results, errors, or sessions without an explicit block. This makes it more useful than a benchmark that passes because it reproduced an expected bypass.

On October 23, I ran the saved-results check:

```sh
cd /Users/nhestrompia/Projects/antiagent
node scripts/benchmark-bare-cdp.mjs --verify-results docs/current-stack-verification-results.json --require-blocking
```

It exited with code 1 and `Agent-proof acceptance failed: a session completed the task`. This checks the saved evidence and acceptance logic. It does not reproduce the live attack. The script creates its artifact directory before reading results, but this invocation writes no new result file.

## Reuse and discard

Reuse the randomized recipient/amount/confirmation task as one adversarial fixture. Also test ordinary HTML forms, because the browser must work without canvas rewrites. Reuse the raw CDP attacker against an exposed control browser, OCR tooling, paired capture controls, command logs, and strict outcome rules. Adapt each transport to WebKit rather than assume Chrome's runner can attach to WKWebView.

Do not carry Shaka, DRM assets, BotD, temporal noise, decoys, pointer puzzles, or page-level integrity gates into the browser by default. Their measured benefits do not close the surviving observation and input routes. Human usability and accessibility were also unmeasured in several Antiagent experiments.

The browser can own its inspection settings, integrations, and session handling. Desktop capture and operating-system accessibility remain separate paths. The [online feasibility report](browser-feasibility.md) evaluates those paths. The [PRD](../../PRD.md) turns the unresolved paths into explicit acceptance gates.
