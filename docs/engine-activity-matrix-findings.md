## Milestone 81: compare native and stable activity across frame types

The new controller builds each mode of the same isolated engine diagnostic. It runs a native control before accepting a stable result for each case. Failed controls cause explicit skips. Each case uses a fresh process, verified content framework mappings, and a private resumed typing control.

The cases cover password focus, ordinary blur, ordinary visibility, and focus plus visibility in three child-frame types. Those types are same-origin, cross-origin, and srcdoc. The controller stops if stable mode permits an autonomous website action. It preserves per-case receipts and verifies process cleanup.

These comparisons exercise page code that reacts to native activity. They do not prove physical usability, pointer support, or compatibility with every website. Timing behavior and independent element-focus commands remain separate tests.

The first complete matrix reproduced all nine native actions. Seven stable cases recorded no action and passed private resume. Both srcdoc cases recorded no action, but their resumed typing controls failed. All eighteen cases passed process cleanup. These two cases remain inconclusive in the original receipt.

A fresh srcdoc focus retry recorded no action and passed its resumed task. The first retry could not reach the stopped fixture and launched no app. The later retry used the restored fixture. All 111 Python checks pass, including missing-control skips and preservation of positive action evidence after a failed resume.

The fresh srcdoc visibility retry also recorded no action and passed one resumed task. Both retries passed cleanup and left Secure Event Input off. Their successful results do not erase the two original inconclusive cases. The resume failures remain unexplained.
