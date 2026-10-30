# Independent Terra/xhigh failure investigation

Requested by the owner after the terminal run. Agent:
`/root/terra_failure_investigation`; selected model `gpt-6.1-terra`, reasoning
`xhigh`, cold context. Read-only source/capture review. No tests, source edits,
network actions, contestant launches or continuations were performed.

## Findings

**The workflow has contradictory edit/freeze instructions.** At tested source
`1e921e0`, `skills/plan-review/SKILL.md:97` requires correcting Critical findings
by editing affected documents. `skills/geeky-plan/SKILL.md:97` freezes task bodies
after planning, while `AGENTS.md:53` says to block instead of editing frozen
bodies mid-run. `mcp/server.py:309` has no lifecycle input and says a frozen
classification means do not edit. The model's stop followed explicit instructions,
but this does not prove validation was logically impossible.

**T2 is incomplete and contains a distinct contradictory expectation.** The root
contract requires status 3, empty stdout and distinct read/decode messages. T2's
AC requires those behaviors, but its listed validation omits them. Its required
invalid-`--top` check says stderr must end with the bare `wordstat: error: ` prefix;
the authoritative contract requires argparse's normal diagnostic, with the last
line starting with that prefix. The latter expectation warrants correction.

**The missing validation is not necessarily a T3 dependency deadlock.** T2's AC
already requires the behaviors; the Phase 1 gate requires AC satisfaction beyond
the listed commands. Additional one-off checks could supply evidence before T3
without constructing its pytest suite or editing the frozen task body. The
claim that T3 was the only possible evidence source is too strong. Whether the
model would have supplied those checks is unknown.

**Classification was not an enforced edit denial.** Native session.jsonl:1055
queries `geeky_check_frozen_artifact`; line 1058 returns frozen true, exit 2 and
the Blocked/handoff instruction. No T2 edit was attempted and denied. The hook
supports warn/block modes; the MCP query invokes block/exit-code mode to classify.

**Semantic review coverage was insufficient.** The PM review marked the broad
validation concern fixed after adding only a successful case and invalid `--top`.
The independent alignment review later found the missing read/decode evidence.
Structural validators establish shape and tracking, not semantic completeness.

**The mock did not exercise this branch.** `evals/mock-agent/c0_fixture.py:235`
writes a scripted plan-review PASS and dispatches no reviewer. Its positive
tests assert the scripted outcome; they cannot uncover a semantic correction
finding or the edit/freeze transition conflict. MCP evaluation examples cover
filename classification, not a corrected review lifecycle.

**Windows patch friction was separate.** The saved session contains repeated
UTF-8 argument/end-marker failures followed by successful patch operations at
lines 416 and 430. It was recoverable friction. The record does not establish
that it caused the terminal stop or the previous transport failure.

## Proposed minimal remediation, not applied

Define an auditable pre-implementation plan-review revision state consistently
across skills, guard and MCP guidance. Keep unknown/ambiguous state frozen and
keep implementation-time contracts protected. Revisions must invalidate affected
reviews and obtain fresh verdicts. Correct the error checks and stderr predicate
without changing the scoring rubric.

| Regression | Required result |
|---|---|
| Critical correction during pre-implementation review | Permitted revision, affected review invalidated and repeated |
| Task/plan/spec edit during implementation | Denied |
| Missing or ambiguous lifecycle state | Remains frozen |
| Mutable notes | Remain writable |
| Missing read/decode validation | Detected by semantic acceptance review |
| Argparse error check | Correct prefix/streams/status semantics |
| Structural PASS with missing AC evidence | Phase advancement rejected |
| Observed Windows patch forms | Supported invocation exercised; incompatible forms detected |

These recommendations have not been implemented or tested. The actual paid-run
result remains Not accepted, with no implementation and no strict composite.

## Evidence pointers

- Snapshot `final-workspace/contract.md:53,61`.
- Snapshot `docs/spec-001-feature/tasks/T2-cli-interface.md:29,36,40`.
- Snapshot `docs/spec-001-feature/implementation-plan.md:24,28`.
- Snapshot `docs/spec-001-feature/review-development-project-manager.md:9`.
- Raw capture `../../baselines/c0-wordstat/20261029T160022Z-45641609/session.jsonl:1055,1058`.
- Tested source `1e921e0`: plan-review/SKILL.md:97; geeky-plan/SKILL.md:97;
  AGENTS.md:53; mcp/server.py:309; hooks/guard-planning-contract.py:119.
- `evals/mock-agent/c0_fixture.py:235`; its tests:142; MCP evaluations.md:26.
