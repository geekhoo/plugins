# Report accuracy review - 2026-10-26

Independent read-only auditor: `/root/mock_observation_audit`. Main source revision: `d90bbd352d5722784180100bf5e431e91bc55210`. This checks observation/report accuracy, not a new implementation acceptance or a paid scoring judge.

## Verified evidence

- All 196 snapshots match SHA-256 and byte count, totaling 1,891,615bytes.
- All 19 main product file fingerprints match; HEAD unchanged. Both isolated support checkouts remain pinned; allseven support files in each match the saved manifest (14checks).
- Twelve attempts /13 top-level MXC workload invocations, including one authorized refusal recovery.
- Both full fixtures pass13/13 oracle tests×3,17 candidate tests, five scripted stages, three saved SCRIPTED MOCK replies. Candidate source/tests share the implementation commits. Local support regressions 25passed.
- Both fresh scorer outputs pass4/4 commands at their selected final candidate commits and retain four unresolved judgment items. Quality100 is supported artifact output; QACT/parity ranking remains unaccepted.
- Scope previews retain eight IDs per harness, repeat stability, evaluator separation, null unsupported metrics, scores_verified=false and zero HTTP publication.
- Codex timeout remains124 with partial captured evidence. Verified Claude timeout/oracle-fault remains124, incomplete, oracle failed and raw bytes preserved. The missed operator injection is correctly separated.
- F1 stale seed-oracle state and F2 measured deadline overhead are directly supported. No exact-deadline, model-obedience or account-billing claim is made.

## Wording findings and parent corrections

1. Replace 'at its own task commits' with 'at each task's scorer-selected final candidate commit'. Both tasks selected the final docs commits cf2ac57/c5b4f73, basis 'last commit naming it (no Done move)', rather than implementation commits e3d0961/b7b7841. Parent applied this correction and added the explicit H1 limitation to scoring discussion and handoff.
2. Remove the exhaustive 'only' runner-change claim. The isolated support also changes Claude mock User-token lookup and Codex slow/crash ValidateSet support. Parent updated the support description; accepted lifecycle logic remains unchanged.

All material result, integrity, scope and nonchargeable-execution claims checked out. Parent verified both mechanical corrections against the cited saved scorer and support-diff evidence; no new test/review pass was needed. No workload, network, secret read, write or source change occurred in the auditor lane.

## Final state

PASS for report accuracy after the two wording corrections. Actual product finding F1 and timing limit F2 remain open, explicitly recorded. No source-repository commit/push or future run is authorized by this review.
