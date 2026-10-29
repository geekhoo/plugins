# Native Codex C0 commit-gate fix

The specification-stage commit conflict is resolved by
`629ae3f31dd230b859abaa2e9a2152ce1f3de5d5`. Both gate twins accept a
case-insensitive `Tasks: none` line only for docs commits. Implementation
commits retain their task-reference rule. The specification skill, gate table
and MCP docstring now agree.

Validation on Windows 11 / PowerShell 7.6.5: `python -m pytest
geeky-orchestration/test_quality_gates.py -q` passed 10 tests and 12 subprocess
subtests using Python 3.14.7. The full skill command produces four paragraphs
including the subject; the regression preserves all of them. The default PATH
Python 3.13 lacked pytest, so this task uses `C:/Python314/python.exe`.
The required readiness check exited 0 with `inventory-ready`, no errors and
fresh source hashes; no pins needed changing. That first inventory predates
the fix commit and records its six dirty source files. A clean committed
inventory is required again for preparation.

The staged six-file literal credential scan passed before the fix commit.
The owner's rotated Codex Langfuse keys authenticated on one existing session
with exit 0 (4 traces, 100 observations). No credential values were printed.
Evidence is under local `outputs/c0-codex-native-fix-20261029/`.

The owner's 29 October instruction authorizes one native Codex C0 attempt
after preparation passes: Luna/high on eight roles, native LiteLLM, 6000/60
seconds, zero recoveries. It also authorizes fast-forward publication after
literal credential scans. No retry, resume, provider probe, overtime or score
publication is authorized. Preparation and the single launch have now completed;
the [terminal result](../c0-codex-native-fixed-run-20261029/README.md) is a crash
during implementation T1. The gate fix worked in the live specification commit.

Task T1 denotes W1/W2, the gate fix and regression proof. W3 records and commits
that proof; W4 prepares a fresh pinned export; W5 consumes the single launch.
See [kanban](kanban.md), [handoff](handoff.md) and [references](references.md).

Stale documents: the old native-run README receives only the requested
resolution note. Its handoff, kanban, raw capture and scores remain historical.
Root/plugin READMEs and `evals/c0-readiness.md` now point to this current record.
Earlier preparation recipes remain unchanged and must not be replayed.
