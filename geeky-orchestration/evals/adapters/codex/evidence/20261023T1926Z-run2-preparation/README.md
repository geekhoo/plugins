# C1 run 2 preparation: targeted fixes and model-free proof

Prepared 2026-10-24 Asia/Singapore, plugin HEAD `bee7b14c3b17b00a6ce0b5643015226a1d7ef963`. [Operator guide](../../../../codex-c1-run2-guide.md) and [full retrospective](../../../../codex-c1-run1-retrospective.md).

No paid run 2, judge/API inference, sign-in, repository staging/commit/push or cleanup occurred. The owner handles Claude coordination; no further child-chat contact is authorized. A prior board post was blocked before execution; no message was sent.

## Fixes

- Codex task validation accepts explicit plain command bullets and fenced blocks. Requested reruns reject missing commands rather than accepting 0/0.
- Codex native child lifetimes come from own task lifecycle records, not spawn acknowledgments, with source provenance.
- Task ownership is recovered only from one canonical task-body read plus matching notes/product writes in the coder's own history. Conflicting/inherited/general prereads do not assign a task.
- No rubric formula, canonical prompt/skill/agent or original run-1 score change. Remaining lane-helper/finding recognition and reused-thread active-time precision are disclosed in the guide.

## Results

| Check | Result |
|---|---|
| Focused synthetic/saved-trace integration | 51 passed; three captured-proof environment variables enabled |
| Full adapter/trace/stage/run2/shared-scorer suite | 285 tests + 32 subtests passed, no skips, 137.06 seconds |
| Fresh Codex mock inside MXC | 7/7 groups; exit 0, is_error=false, empty stderr, zero model calls/tokens |
| Fresh real CLI with local scripted provider in MXC | 21/21 checks; exit 0; pinned build verified; external egress denied |
| Native diagnostic policy | install 0/catalogue 0/exec 1 approved exact root denial; zero unexpected errors |
| Native model matrix | Sol/medium main; Luna/max child, grandchild and default worker |
| All six Claude regressions | Exit 0; every raw dimension/composite equal within 1e-9: 77.2/77.0/86.7/97.9/93.8/98.3 |
| Frozen run-1 artifacts | All 57 manifest entries unchanged |

Fresh mock: `../../../../baselines/c1-csvledger/20261023T192610Z-e3ec171a`. Native attempt: that folder's `native-attempts/native-probe-a3cbfdc5`. See actual mock-summary, native-summary, stdout/stderr and MXC build provenance there. The lightweight mock is intentionally incomplete for scoring and does not solve C1; expected oracle setup failures do not invalidate its infrastructure checks.

The copied `claude-regression.json` retains the exact verifier invocation, scratch paths, per-run raw dimensions, original/supplementary preservation and source-stability proof. `verification.json` records parent integration results and commands; `source-manifest.json` plus `sources/` preserve exact current harness files for later reproduction. Snapshot files use an inert `.source` suffix so pytest cannot discover duplicate test modules; restore the manifest paths when reproducing. Historical CP2/3/4 evidence and the paid run-1 artifacts were not rewritten.

Core source SHA-256 at freeze:

- codex-trace.py: `3b52cbfea1cc9f41a62d4bb626f4e80da709b24278740a0d5fdd78d8ad510551`
- score-run.py: `9bcb243214231926fb6886ba8013555434f811394ef829277fd7c1095aec3f11`
- test_codex_run2_prep.py: `173c277fbb880721589458801370a56219ec2ff0404ece3029398e45352e1871`

No claim of fully automatic, directly comparable Codex process scoring is made. Review stage evidence and remaining parser uncertainty on the actual run. Run 1 remains 81.7 provisional.
