# PM-Style Planning Review

**Verdict:** PASS after fixes — package is ready for independent plan-review.

## Scope and coverage

- Root `contract.md` remains the source of truth and the spec does not add behavior.
- `draft.md` maps every brief and contract requirement (R1-R6 and the additional interface/stack constraints) to T1. T1 maps back to those requirements.
- Task validation is scoped to this task and enumerates tests for AC1-AC8, including stream/exit checks and expected byte output. Expected file error suffixes are copied verbatim: `<path>: cannot read file` and `<path>: not valid UTF-8`; usage predicate is verbatim: `^wordstat: error: `.

## Sequencing and dependencies

- One task in one phase is appropriate for the greenfield CLI; no prerequisites or integration sequencing are omitted.
- T1 is Ready and has no dependencies. No task is placed in multiple lanes.
- Package boundaries stay within `wordstat/` and `tests/`, with no runtime dependency expansion.

## Required fixes

- Initial semantic review (`/root/plan_semantic_review`) found that the original AC2 stdin test could pass if stdin were read and discarded. T1 now keeps a subprocess stdin pipe open and empty, requires prompt completion using the supplied FILE, and fails/terminates on timeout.
- Initial sequence review (`/root/plan_sequence_review`) found missing evidence for rejecting a second FILE and for the explicit `sys.stdout.reconfigure` call. T1 AC1/AC7 now assert second-positional usage failure; AC5 now uses a recording stdout spy to assert the exact call as well as process-level LF bytes.
- Final semantic re-review by `/root/plan_semantic_final`: **PASS**. It confirmed AC1-AC8 task-local checks, exact error wording/predicate positions, open-empty stdin timeout evidence, second-FILE usage rejection, direct stdout reconfiguration assertion, and deterministic simulated `PermissionError` evidence.
- Sequencing re-review by `/root/plan_sequence_recheck`: **PASS**. It confirmed the single-task phase remains coherent and the second-FILE, stdin, and stdout-reconfiguration checks are explicit.
- The semantic reviewer additionally found actual permission-denied testing platform-dependent. T1 now deterministically simulates `open()` raising `PermissionError` and checks exit 3, exact `<path>: cannot read file`, and empty stdout; actual OS permission testing is supplementary only.
- Both final reviewers passed after incorporating all initial findings. This PM-style review is not a substitute for the separately authorized plan-review stage.

## Suggestions

- Keep raw-byte assertions for newline and JSON output, alongside the direct reconfigure-call test.
- Keep the simulated `PermissionError` assertion mandatory across platforms; actual OS-level permission denial may remain supplementary.
