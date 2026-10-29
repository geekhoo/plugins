# Native C0 terminal handoff

Machine: Windows 11, PowerShell 7. Workdir:
`C:\Users\gerald.khoo\geekhoo-plugins`, branch `main`. Report <=300 words.

Read in order: this folder's README, failure-evidence.md, references.md,
evidence/results.json, evidence/verification.json, evidence/scoring-status.json,
then raw `../../baselines/c0-wordstat/20261029T062343Z-ffd63c3c/run.json` and
stream lines568-569. Verify through Git before acting that initial source
`9a031e607464d003b7960cf3cf390b96562ef30c`, gate fix
`629ae3f31dd230b859abaa2e9a2152ce1f3de5d5` and contestant plugin
`183aead10805fdc15ad5ec76dc97733c501e5a23` are ancestors of HEAD.

Verified state: exactly one native attempt consumed; terminal crash exit 1,
2511.334 contestant seconds, implementation T1 dispatched but no product package.
Candidate HEAD `8001c868b37977ac576189fb86fceef997e3f13d` contains reviewed
planning only. Oracle 0/13 with 13 setup errors is stable over 3 runs. Langfuse
readback23 traces / 920 observations. Parity composite unavailable because the
official scorer rejects the failed/incomplete trace. Cleanup verified; source
and candidate evidence remain preserved.

Takeover scope: read-only orientation and verification of the recorded result.
No retry, resume, provider probe, overtime, score publication or protocol fix
is authorized. Preserve raw captures, historical scores and source pins.
Never print credential values. Any later authorized commit/push must scan
every staged blob for literal credential values and all outgoing blobs before
public push. Never force, amend or bypass hooks.

Done: report the terminal evidence and unresolved implementation/scoring gaps,
then stop. Further live execution needs separate written authorization.
