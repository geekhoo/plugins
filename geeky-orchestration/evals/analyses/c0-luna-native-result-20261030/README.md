# Native Luna/high C0: not accepted at plan review

Run `20261029T160022Z-45641609` ended its model turn with process exit 0 after
1870.542 seconds (31m11s). **Actual workflow acceptance is false.** It stopped
during plan review with T2 Blocked; implementation and final review were
unreached. The budget was 6000 seconds with a 60-second reserve. This was not
a 30-minute timeout: roughly 69 minutes remained. Exactly one attempt ran,
without retries, resumes or overtime. All configured roles were Luna/high;
all seven observed native thread contexts also verify that model and effort.

Follow-up: the plan-freeze fixes and the next attempt are recorded in [c0-plan-freeze-native-result-20261030](../c0-plan-freeze-native-result-20261030/README.md).

## Blocking finding

T2 requires contracted read/decode error status, streams and wording, but its
own validation block checks compilation, help, normal output and invalid
`--top` only. Comprehensive tests belong to T3 in the next implementation
phase; they cannot supply evidence before the Phase 1 gate. The independent
alignment reviewer reported a Critical gap. Another malformed expectation
says stderr should end with the bare error prefix, while the root contract
requires its last line to start with that prefix.

Plan-review Phase 2 requires correcting critical document findings. In contrast,
AGENTS and geeky-plan freeze task bodies after planning. The MCP classifier
is phase-blind and returned `frozen: true` for T2. The model then stopped;
no task-edit attempt was denied. These instructions conflict. The operator
supplied no contract edit, continuation or bypass during the paid attempt.

The owner's subsequent [independent Terra/xhigh investigation](terra-investigation.md)
confirmed this conflict and the malformed stderr expectation, but qualified the
validation-deadlock interpretation: T2's AC and phase gate permitted additional
one-off checks before T3. The missing listed checks did not prove that all
validation was impossible. The mock's scripted review PASS never exercised this
semantic-correction/freeze branch. No proposed remediation was applied here.

## Actual evidence

| Measure | Result |
|---|---|
| Acceptance | Not accepted; model explicitly reported the block |
| Process | Exit 0, turn.completed; insufficient for acceptance |
| Specification | Complete, commit d03bfc723e1a6d03f502bc628d807c74ec616086 |
| Planning | Three-task draft; structural gates pass; not implementation-ready |
| Plan review | NEEDS ATTENTION; sequencing and sanity phases incomplete |
| Product code/tests | None; zero product Python files and tests executed |
| Oracle | 0/13; 13 missing-package setup errors, stable over three runs |
| QACT/parity | Withheld: strict scorer exit 2; no source-supported T1 implementation commit; final-HEAD fallback forbidden |
| Langfuse | 8 traces, 391 observations, zero truncated |
| Native records | Zero structured errors, tagged encrypted handoff parts or tool-search calls |
| Patch friction | 13 patch-command failures; 18 failed commands total |
| Cleanup | Verified; no run processes; dedicated store lock available |

The strict scorer produced no source-bound Quality input, so no parity
composite is manufactured. No alternate final-HEAD or fabricated validation
cache was used. No score was published. The final statement says Not accepted;
this is not a false-completion claim. Structural gate PASS does not clear
the reviewer's unresolved acceptance finding.

## Source and preservation

All three local commits passed literal credential scans before committing:
worker policy `a3a2c2d` (seven files), native protocol `0b4a5c0` (sixteen), and
evidence/records `1e921e0` (257). None was pushed. Official preparation and the
contestant export used clean committed `1e921e0`. Canonical prompt SHA-256:
`124eba9b416324a052c8e25031f1660200f52a05a74c9a1d9ce13527b270ddde`.
Retained tests: 290 passed and 64 subtests, plus ten readiness tests. All 15
source hashes were reverified; all 18 MXC build files matched their pins.

The terminal literal scan checked 101 files with zero hits. Raw capture,
solution.bundle, native ancestry and uncommitted planning files are preserved;
63 capture/snapshot files are pinned. Result records remain local/uncommitted;
the tested source commits are intact. No retry or continuation followed.

See [kanban](kanban.md), [handoff](handoff.md), [references](references.md) and
[result binding](evidence/results.json). Local full observations, operator
logs and snapshots are under `outputs/c0-luna-native-authorized-20261029/`.
