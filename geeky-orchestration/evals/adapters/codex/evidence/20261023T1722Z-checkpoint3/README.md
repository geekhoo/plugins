# Checkpoint 3 evidence — not a contestant baseline

Windows 11, PowerShell 7, base `bee7b14`. Only saved traces and deterministic
local validations were executed. No paid models or judges, staging, repository
commits or pushes. Stop before checkpoint 4.

The final combined suite passes **139 tests and 10 subtests**. The native fixture
trace contains two threads, seven recorded model responses from the local scripted
provider, zero tokens and one passing MCP commit gate. Its analysis is complete.
The analyzer and scorer CLI smoke test exits 0. That smoke combines the CP2 local
fixture trace with a cloned historical solution workspace; its score is plumbing
evidence and must never be reported as a Codex contestant result.

The shared analyzer/scorer route Codex through `codex-trace.py`; QACT formulas,
weights, caps, manual judgement and task validation rules remain shared. Patch
normalization excludes deleted lines from current evidence. MCP task parameters
are unwrapped for DoD attribution. Missing/errored/incomplete evidence blocks
scoring. Child histories are excluded and cumulative usage counted once per
thread. Unknown API latency and cost stay null; the existing task-time formula
uses raw duration when latency is unavailable.

Historical reference composites:

| Run | Timestamp | Composite |
|---|---|---:|
| 1 | 20261020T114232Z | 77.2 |
| 2 | 20261020T155628Z | 77.0 |
| 3 | 20261022T065938Z | 86.7 |
| 4 | 20261022T125647Z | 97.9 |
| 5 | 20261023T062603Z | 93.8 |
| 6 | 20261023T104412Z | 98.3 |

Verification uses `verify-claude-regression.py`, git-archives the six committed
fixtures, clones their solution bundles to scratch, reruns analysis and scoring
with committed manual verdicts and full per-task validations, and compares raw
Q/A/C/T and composite values to tolerance 1e-9 (not merely displayed rounding).
Original fixtures and source hashes are checked before/after.

Runs 2, 4, 5 and 6 depended on untracked `.heartbeat` files absent from the Git
bundles. Exact raw files are copied from their retained historical workspaces
only after checking each workspace HEAD matches its bundle HEAD. Source paths,
SHA-256 and copied bytes are preserved; no status or timestamp is fabricated.
Without these files the committed scorer also differs, so they are an explicit
reproduction dependency. Earlier reports expose that gap and source drift while
the adapter was being fixed; the final frozen-source report is authoritative.

`claude-regression.json` records the final six-run result and command provenance.
`native-analysis.json`, `fixture-score.json` and `unit-tests.txt` contain the
local pipeline/test evidence. `source-manifest.json` fingerprints final changed
implementation files. Raw traces, credentials and caches are not copied here.
All evidence in this folder is excluded from contestant means and scoring.
