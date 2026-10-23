# Mouse-behavior experiment

Status: synthetic baseline trajectories and a source-state filter experiment exist. No physical-human dataset or trained behavioral classifier exists yet. See the [filter findings](../input-filter-findings.md).

## Question and decision

Can native mouse behavior make computer-use attacks meaningfully harder at an acceptable rate of false blocks for people?

This experiment evaluates resistance. It does not establish human origin or replace input-access controls. A successful result against basic scripts is insufficient. The attacker can know the detector, replay independently collected human traces, and adapt generated paths.

The first 2 to 3-day feasibility pass includes only a small collection and evasion pilot. A reliable estimate for a low rate of false blocks requires a larger follow-up. Do not delay the native-input test to build a classifier.

## Collection

Collect only inside a local, harmless HTML fixture in the WKWebView shell. Participants consent to collection. Do not record browsing histories, account credentials, page text, or raw typed content.

Use target acquisition, clicks, scrolling, drag, form focus, and navigation tasks. Include mouse and trackpad use, slow and fast movement, pauses, mistakes, and corrections. Include different target sizes, display scales, and layouts. Document missing participant groups and devices.

Record native event timestamps and pointer coordinates alongside fixture events and task outcomes. Store relative coordinates where possible. Keep session, participant, device, and fixture identifiers separate from the features used by the detector.

Record native source metadata for diagnosis, but evaluate its contribution separately. A source label must not leak the class into a supposed behavior-only model. Likewise, do not let fixture URLs, participant IDs, collection order, or artificial sampling differences identify the class.

Candidate features include velocity, acceleration, curvature, pauses, corrective movement, click dwell, and scroll timing. These are hypotheses to test, not established human invariants. Begin with simple rules or a small model. Keep the decision explainable enough to diagnose false blocks.

## Attack families

| Family | Attacker behavior | What it tests |
| --- | --- | --- |
| Basic control | Straight paths, fixed delays, and conventional automation calls. | The detector works against simple examples. |
| Generated movement | Curved paths, varied speed, pauses, overshoot, corrections, and varied click timing. | The detector survives more realistic generation. |
| Human-trace replay | Replay traces from independent sessions. Translate, rescale, retime, and combine them for new targets. | Previously human movement does not provide a trivial evasion path. |
| Adaptive generation | Give the attacker the rules or model and a declared feedback budget. Let it change paths after rejection. | Resistance remains after the attacker learns the detector. |
| Alternative input | Use keyboard navigation, paste, scrolling, AX activation, and AX value setters without the mouse path. | The browser remains resistant outside the classifier's chosen input type. |
| Combined agent | Read screenshots, plan actions, and use the strongest available input route. | The experiment improves actual task outcomes rather than an offline score. |

Run a version with no inspection of the browser's private state. A second, informed attacker may know the classifier and thresholds. Record those privileges instead of mixing the results.

## Evaluation design

Split training, tuning, and final evaluation by participant and session. Also hold out device configurations and task layouts where the sample permits. Do not split individual movement samples randomly across sets from the same trace.

Freeze the model and thresholds before final evaluation. Adaptive attackers can tune against a development environment. Report the number of queries and adaptation time, then test on fresh tasks and sessions. Do not tune the final threshold after inspecting the held-out outcomes.

Compare the same shell under four conditions: no detector, metadata rules alone, behavior alone, and both combined. Keep layout, permissions, task, and attack budget comparable. Both mouse and trackpad users must remain in the human evaluation.

Measure these outcomes:

- False blocks per legitimate session and human task completion, with uncertainty and actual sample sizes.
- Agent task completion under each attack family, including the strongest combined route.
- Successful disclosure before detection and successful actions before a block.
- Median task duration, action count, adaptation time, and detector latency.
- Compatibility with keyboard use, VoiceOver, input methods, and other legitimate tools.

Offline classification accuracy is diagnostic. The primary result is end-to-end attacker success at a fixed human cost. A block after submission does not prevent that submission. A block after the first screenshot does not undo disclosure.

## Follow-up acceptance

The [PRD](../../PRD.md) proposes at most 1% false blocks per legitimate session and at least a 50% relative reduction in adaptive task completion. These are proposed product targets, not results. Report uncertainty. A small pilot cannot establish the false-block target.

The 30 attempts per condition proposed for later task evaluation are a screening minimum, not statistical proof of either threshold. Plan the human sample separately around the precision needed for the false-block estimate.

Promote behavior into a resistant MVP only if the gain survives adaptive generation, trace replay, alternative inputs, and human usability checks. If only simple scripts fail, retain a limited detector result. If human costs erase the benefit, stop the detector and preserve the evidence.

Passing this experiment never supplies an unforgeable human-input credential. The [platform research](browser-feasibility.md) explains the native metadata limits. The [Antiagent review](antiagent-review.md) records why matching the tested script is insufficient.
