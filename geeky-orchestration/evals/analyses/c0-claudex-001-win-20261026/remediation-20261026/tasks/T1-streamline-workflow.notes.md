# T1 implementation notes

State: implementation and bounded validation complete; **awaits parent review/phase acceptance in In Review**. This note does not move lanes or issue acceptance. No commit, push, runner launch, provider call, judge call, telemetry call or historical repair was performed.

Environment: Windows PowerShell 7, `C:/Python314/python.exe`, Python 3.14, pytest 9.1.1. Workdir for every validation command below: `C:/Users/gerald.khoo/geekhoo-plugins/geeky-orchestration`. Verified HEAD `53fb54b5f30ab0397c1fc154e83a6af942797322`; source baseline `8fff98b0f087f148d4f416f512dc9988d61a57aa` exists. Neither was reset or changed.

## Ownership, assumptions and delivered scope

One product writer: T1. Parent owns kanban, handoff and heartbeat; runner-preparation lane is read-only. Implementation was sequenced because shared workflow surfaces make concurrent writers unsafe. No additional worker was needed for this bounded edit.

Read canonical `agents/geeky-coder.md`, source `AGENTS.md`, task contract, implementation plan and references first. Repository-root AGENTS.md was absent; used the plugin's source AGENTS.md as directed. The supplied task body and source instructions govern; no events log was created. The memory registry was consulted only for the durable-source convention, then current repository state was verified; no historical commands or scores were used as fresh runtime proof.

Changed six product documents only:

- `skills/impl-review/SKILL.md`: requirement-based terminal verdict, immediate reply persistence with identity/input anchors, consolidation of valid saved sections and affected-domain remediation. Required findings include any severity; optional warnings/suggestions do not reopen acceptance.
- `skills/plan-review/SKILL.md`: initial whole-folder alignment covers the existing six sanity dimensions; independent sequencing remains required. Resume uses revisions/hashes and complete diffs, with conservative invalidation; final parent pass and all three validators run after corrections.
- `skills/geeky-implement/SKILL.md`: same-phase revised verdict and closeout-before-heartbeat ordering.
- `skills/geeky-implement/references/execution-protocol.md`: functional code/tests delivery, snapshot evidence binding without changing H1, same-phase revised verdict and source-bound closeout claims. Updated the existing commit summary's separate-test example to agree with step 16; phase batching and no per-task commit timing remain.
- `evals/prompts/end-to-end.md`: final-output paragraph only, requesting one concise completion report with evidence in its text and detailed artifacts retained.
- `evals/prompts/README.md`: prospective baseline/hash rules, unchanged report criteria/disabled rule, and affected required-fix reference. Historical decision D36 itself is preserved; README links it without changing scoring/expectations history.

Local fixtures, scripts, output logs and manifests are under `tasks/T1-evidence/`. They are evidence for this task, not a cache service, workflow stage, findings database, production report parser or new gate.

## Exact validation commands and results

All paths below are plugin-relative. Full stdout/stderr is retained in each log, followed by the actual process exit code. The task's required pytest run protects existing gate/scorer semantics; document walkthroughs supply the instruction-consistency evidence. No keyword-only test is presented as behavioral proof.

1. `& C:/Python314/python.exe -m pytest -q test_quality_gates.py test_score_run.py`
   - Exit 0; **44 passed in 16.64s**. Output: `tasks/T1-evidence/pytest.txt` (under this packet).
   - No production Python or tests changed. Later document wording corrections do not invalidate this gate/scorer evidence; those executable inputs are fingerprinted in `tested-state.json` and remain identical to HEAD. No broader rerun was needed.
2. `& C:/Python314/python.exe evals/analyses/c0-claudex-001-win-20261026/remediation-20261026/tasks/T1-evidence/check-local.py`
   - Final exit 0. Output: `T1-evidence/local-checks.txt`.
   - Verifies pinned HEAD/baseline; final-paragraph-only prompt diff; **2,191** protected tracked files' Git blob equality; raw file SHA-256 stability between validation passes; disabled rule; actual H1 selector on synthetic snapshot inputs; absent-test command rejection and later fixture success; separate Git-object/file-SHA labels.
   - The first attempt exited 1 because one pre-existing tracked Git link was treated as a file; full failure is retained in `local-checks-attempt1.txt`. Corrected the local evidence script to exclude Git-link traversal; one Git link is explicitly outside raw file hashing. No product code changed to resolve this fixture issue.
3. `& pwsh -NoProfile -File evals/analyses/c0-claudex-001-win-20261026/remediation-20261026/tasks/T1-evidence/check-prompt.ps1`
   - Exit 0. Output: `T1-evidence/prompt-checks.txt`.
   - Parses each real runner, executes only its existing `prompt` and `promptSha` assignment ASTs, compares rendered text and hashes. Does not invoke either runner's entry point.
4. `& C:/Python314/python.exe scripts/validate-planning-folder.py --path evals/analyses/c0-claudex-001-win-20261026/remediation-20261026`
   - Exit 0, `OK: planning folder valid. 3 task file(s) found. (warnings: missing feature-specification.md, draft.md)`; files are intentionally absent per task brief. Output: `T1-evidence/validate-planning-folder.py.txt`.
5. `& C:/Python314/python.exe scripts/validate-task-schema.py --path evals/analyses/c0-claudex-001-win-20261026/remediation-20261026`
   - Exit 0, `OK: 3 task file(s) checked, 0 failing.` Output: `T1-evidence/validate-task-schema.py.txt`.
6. `& C:/Python314/python.exe scripts/validate-kanban.py --path evals/analyses/c0-claudex-001-win-20261026/remediation-20261026`
   - Exit 0, `OK: 3 task(s) tracked, 3 task file(s). Backlog=2, Ready=0, In Progress=1, In Review=0, Blocked=0, Done=0`. Output: `T1-evidence/validate-kanban.py.txt`. This is the observed validation-time board, before the parent's later transition.
7. `git diff --check -- skills/geeky-implement/SKILL.md skills/geeky-implement/references/execution-protocol.md skills/impl-review/SKILL.md skills/plan-review/SKILL.md evals/prompts/end-to-end.md evals/prompts/README.md`
   - Exit 0. Output: `T1-evidence/diff-check.txt`; Git emitted existing checkout line-ending notices, no whitespace defects.

The synthetic snapshot commands (called by check-local.py, exact interpreter and cwd also in `snapshot-result.json`):

- `C:/Python314/python.exe -m pytest -q -p no:cacheprovider test_core.py` in `T1-evidence/snapshot-fixture/selected-delivery`: **exit 4**, `ERROR: file or directory not found: test_core.py`; `selected-delivery-pytest.txt`. This failure is the expected rejection evidence.
- The identical command in `T1-evidence/snapshot-fixture/later-final-head`: **exit 0, 1 passed**; `later-final-head-pytest.txt`.

These are local synthetic programs, not contestant code. Their 40-character IDs are explicitly synthetic immutable file-set manifests, not real Git commits. No fixture Git commits were created. The actual unchanged `task_commit` selector chooses the earlier delivery; file hashes show the missing test, and later success cannot replace that evidence. Production policy was not reimplemented in a new acceptance engine.

## Walkthrough of every AC and edge scenario

The tables below are manual semantic walkthroughs against the edited instructions and declared synthetic inputs. Expected decisions establish instruction consistency; they do not establish future model compliance, calibrated judge accuracy or measured savings. Anchors are plugin-relative, with line numbers at this tested state.

### AC1 — verdicts and optional warnings

Source: `skills/impl-review/SKILL.md:75` (required findings template), `:86` (requirement/evidence rule), `:93`/`:97` (persistence/consolidation), `:123`/`:128`/`:164` (Overall, remediation and follow-ups). Inputs: `T1-evidence/review-fixtures.json`.

| Input | Expected decision / check |
|---|---|
| V1: API PASS, Data PASS WITH WARNINGS for optional index tuning, Security PASS; evidence current and passing | Overall PASS. Keep the nonblocking warning; zero extra fix/review dispatches. |
| V2: warning-labeled finding violates mandatory AC | NEEDS FIXES regardless of warning label; required correction then only affected re-review. |
| V3: Security reply absent, or required evidence absent | NEEDS FIXES; two saved PASS verdicts cannot stand in for third reviewer/evidence. |
| V4: reviewer says PASS while its required finding remains unresolved | NEEDS FIXES; the contradictory verdict cannot discharge the unmet requirement. |
| Suggestions only, no requirement/evidence gaps | Retain follow-ups; no discretionary hardening or review to eliminate them. |

Result: PASS for instruction consistency. Reviewer count remains exactly three (`impl-review:160`); no gate was removed.

### AC2 — planning reuse, independent reviewers and final validators

Sources: `skills/plan-review/SKILL.md:20` (resume/invalidation), `:51` through `:70` (whole-folder alignment and all six dimensions), `:82` (post-fix checks), `:106`/`:110`/`:112` (sequencing corrections, final pass and all validators), `:131` (separate sequencing reviewer).

Synthetic baseline: alignment reviewer align-A and independent sequencing reviewer seq-B each saved current revision/file hashes and findings in existing `review-plan.md` sections; all required findings resolved. Completion markers by themselves are never validity proof.

| Case / delta against baseline | Expected reuse, invalidation and final decision |
|---|---|
| P-unchanged: hashes, dependencies and complete tracked/untracked diff unchanged | Reuse both reviewers; no fresh dispatch. For a resumed already-complete review, reuse its valid final checks too. For an initial final pass, consolidate current evidence and run the existing final validators. |
| P-mechanical: one spelling/path correction with unique solution and bounded references, no requirement/scope/order change | Parent checks actual changed content and affected references, records the finding resolved; reuse unaffected independent verdicts. Rerun all three validators after corrections. A marker or severity label alone cannot authorize reuse. |
| P-requirement: change required output, AC, task scope or coverage | Alignment invalid. Obtain fresh alignment verdict; sequencing can be reused only if dependency/order/gate/resource/validation-feasibility inputs are demonstrably unchanged. Final all-three validators follow corrections. |
| P-dependency: change dependency/order/phase/gate/resource or validation feasibility | Sequencing invalid; get fresh sequencing verdict. A local bounded scheduling change can preserve alignment only where coverage/references are unchanged. Final checks include changed references and all three validators. |
| P-task-IDs: rename task ID, dependency or order across plan/tasks/kanban | Retained full-recheck trigger: full Phase 1 alignment recheck, fresh affected sequencing verdict; no small-mechanical shortcut. All three final validators run. |
| P-six-files: six changed documents, even if corrections look mechanical | Retained >5 trigger: full Phase 1 recheck, plus fresh sequencing when its inputs are affected. Cannot reduce to a spot check. |
| P-missing-baseline or P-missing-diff | Full sanity and fresh affected verdicts; when affected scope is unknown, both reviewers are affected. No reuse from markers alone. |
| P-untracked: diff accidentally omits a newly added task/reference | Incomplete diff invalidates reuse. Inventory includes untracked additions; full sanity and fresh affected verdicts. |
| P-conflict or P-unbounded-impact | Full sanity and fresh affected verdicts. Unresolved required findings prevent READY FOR IMPLEMENTATION. |
| P-sequencing-correction-after-alignment | Reapply invalidation rules to final sequencing corrections, obtain fresh affected verdicts, then rerun task-schema, kanban and planning-folder validators after those corrections. Earlier validator successes cannot cover later corrections. |

Result: PASS for instruction consistency. Initial alignment still reads the entire folder, including accuracy, references, non-conflicting instructions, completeness, freshness and convention adherence. Independent sequencing is retained even when alignment is clean. The local actual three-validator run above passes; the hypothetical dispatch decisions are walkthrough evidence, not actual reviewer dispatches.

### AC3 — absent tests at selected committed delivery

Sources: execution protocol `:44` and `:168`; unchanged H1 selector `evals/scripts/score-run.py:595`; existing `TaskCommitTests` in `test_score_run.py:160`; historical `evals/analyses/c0-claudex-001-win-20261026/codex/report.md:55` onward.

Synthetic fixture: earlier task-named delivery at ct=200, Done at ct=250 after start at ct=150; later complete final delivery ct=500. Actual H1 selects synthetic `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`, never synthetic final `ffffffffffffffffffffffffffffffffffffffff`. Both core hashes match but the selected delivery omits `test_core.py`; its command exits 4. Later test success (1 passed) supplies no evidence for the earlier selected delivery. Expected **REJECT selected snapshot**, then fix the functional delivery/evidence without rewriting historical task anchors. Actual result: PASS for fixture rejection; exact manifests/commands are in `snapshot-result.json`.

Historical consequence remains unchanged: C0 Codex selected T1 `9336491` has 1/2 commands; tests arrive in `1d9e57e`; later final HEAD does not cure it. No candidate program was rerun or historical anchor repaired.

### AC4 — T4 BLOCKED with T3 READY

Sources: `skills/geeky-implement/SKILL.md:67`; execution protocol `:138` and `:166`. Inputs P1/P2 in `review-fixtures.json`.

T3 phase READY plus T4 phase BLOCKED remains **unaccepted** after a parent merely fixes the handoff. Expected T4 stays In Review pending a revised verdict for T4's same phase. T3's earlier READY is insufficient. Only a current T4 PASS / T4 phase READY from its reviewer, with required validation passing, allows the existing Done move and check-dod/kanban gates. The gate order/count is unchanged.

Historical anchors: `claude-code/router-fixed/manual-verdicts.json` entries `a.phase_verdict.P4`, `adh.phase_verdict.P4`, `dp11` retain failure; closeout `manual-verdicts.json` records reviewer `a5fa51b4a664cae32` reviewing `0a9b354` and a revised T4 verdict. Initial and cumulative results remain separate. Result: PASS for instruction consistency, no historical rewrite.

### AC5 — three saved replies and affected-domain dependency change

Sources: `skills/impl-review/SKILL.md:16`, `:26`, `:93`, `:97`, `:130`. Input: three full synthetic domain reply sections in `review-fixtures.json`, each with reviewer ID, revision, findings, verdict and completion marker.

V1 unchanged: replies are persisted one at a time on arrival, before waiting for others. On resume all three valid sections require **consolidation only, zero new reviewers**. V5 Data dependency changed with API/Security dependencies proven unchanged: reopen Data only and record why; preserve API/Security identity, evidence and verdicts. Unknown relevant revision/dependency validity cannot be accepted based only on its completion marker. Result: PASS for instruction consistency; no new generic review cache.

### AC6 — precise C0 CRLF/BOM and Git-object claims

Source: execution protocol `:205`; original C0 Codex `report.md:76` onward / `manual-verdicts.json` `a.final_report_claims`; original closeout `review-metadata-erratum.json`.

| Original evidence | Precise supported claim | Rejected overstatement |
|---|---|---|
| `tests/test_cli.py:17–23,78–82,101–119` covers CRLF/BOM through `python -m wordstat`; reviewer suggested narrower direct `cli.main` coverage | “Subprocess CLI CRLF/BOM coverage exists; the optional suggestion concerns direct `cli.main` coverage.” | “CLI-level CRLF/BOM tests are missing.” |
| Erratum `wordstat/cli.py` Git blob `1e189f2bce97b6f337141b5f660470b4e54d240a`; file SHA-256 `98e63b4ad7d264390d24fab040e277d95f443a5e7140242cdca1d9b28b67660e` | Distinct Git blob object ID and SHA-256 digest of file bytes | Labeling the 40-hex Git blob as SHA-256. |
| Erratum `tests/test_cli.py` Git blob `73cc01af2a51ecf1af7c5d3885360f68ce9af61d`; file SHA-256 `dfa7593e734ca7568138ac97a544b102bffe64eca2e5d72d91bcc7ddcbfda08f` | Same distinct labels, preserved original erratum | Rewriting candidate ledger or claiming its old label was correct. |

Result: PASS for scope/label consistency. check-local.py reads and checks the preserved erratum labels; raw hashes and Git blobs of the original reports/verdicts/erratum are in protected-files.json. Historical reports are evidence, not fresh candidate test runs.

### AC7 — no extra dispatch, timing remains T2, truthful closeout

Sources: impl-review `:26`/`:128`; plan-review `:20`/`:110`; execution protocol `:198` through `:205`; implement SKILL `:58`.

Existing valid acceptance/review evidence reuses the same reviewers and hashes; optional warning cleanup creates no dispatch. After authorized existing phase/final review passes, existing Run Summary, lane reconciliation and current required verdicts precede heartbeat done (C1 in review-fixtures.json). On interruption or missing required review, state remains incomplete and heartbeat paused with resume context (C2). Existing phase reviewer cadence, final three domains and gates remain. No timing/reserve plumbing or mandatory per-task timing was added; T2 owns it. Result: PASS for instruction consistency.

### AC8 — compact report retains the unchanged five criteria

Contract: `evals/telemetry/langfuse-evaluators/final_report_complete.judge.json:5`; rule `final_report_complete.rule.json:3` remains `enabled: false`. No evaluator code/config changed and no remote judge was used.

Input `T1-evidence/compact-report.md` is a synthetic final report. Manual criterion walkthrough:

1. C1: five named stages each has a substantive outcome; an unreached stage would need an explicit unreached row and truthful incomplete overall outcome.
2. C2: final command reports **12 passed, 1 skipped, exit 0** at the stated synthetic revision and names its output artifact.
3. C3: two synthetic commit SHAs and subjects are explicitly included; final revision is named.
4. C4: explicit none for deviations/blockers/interventions plus retained optional Data warning.
5. C5: each completion/PASS gives its command/gate result or named reviewer verdict in the report itself; paths alone are insufficient.

Expected PASS under all five unchanged criteria. `report-negative-cases.md` records concrete semantic mutations: omitted numeric tests fails C2; omitted SHAs/subjects fails C3; linked-only PASS fails C5; declared source state unreached but reported complete fails C1/C5; links alone fail C1–C5; an unresolved mandatory warning prevents supported PASS. This is a semantic walkthrough, not an automated judge result. Source-state contradictions cannot be detected reliably from fabricated output text alone; no such capability is claimed.

### AC9 — one paragraph changed, future baseline and preservation

Sources: canonical prompt `:21`; prompt README `:11`/`:13`; actual unchanged runner render/hash assignments `evals/scripts/run-baseline.ps1:161–162`, `run-codex-baseline.ps1:150–151`.

check-local.py compares full prompt line arrays against pinned HEAD and source baseline, asserting every line except the final paragraph is identical (normalizing only checkout CRLF for content comparison). `historical-prompt.md` stores exact historical Git blob bytes without replacing any historical file. check-prompt.ps1 executes each runner's actual existing assignment expressions; full rendered text and SHA-256 agree:

- New prospective rendered prompt SHA-256: `4d8ebd2f16b83a14c8f7278935105ab31e86b01e2b51098a7d7af0f07a17cf2e`.
- Historical rendered prompt SHA-256: `7c3ed1b8ab6eda83d9e221cb279293d66a732901cda6bc7bbf9979c57df7cdbc`, matching frozen C0 `run.json.prompt_sha256`.
- New local tracked runtime file-manifest fingerprint SHA-256: `073eef81f19ab35a6cbc1271f42ce4f3ce29fb9057ffd37c15c849e86af0265a`; full algorithm, kind and entries in `plugin-fingerprint.json`. This is working-file evidence, not a new Git commit ID or either runner's tamper hash. Future runners export committed plugin HEAD and record that `plugin_sha`; parent must retain the final commit in the future baseline record.

No case contracts, scoring formulas, H1 selection, historic prompt requirements, C0 scores or IDs changed. Protected manifest covers 2,191 tracked historical/case/scoring/frozen files; clean-filtered Git blob IDs match pinned HEAD, raw SHA-256 digests are recorded separately and stay stable across validation passes. One pre-existing Git link is excluded from raw-file traversal. Original comparison values Codex **97.46**, Claude initial **90.33**, Claude cumulative **98.33** are untouched, scoped historical populations. Result: PASS for local prompt/version/preservation checks.

## Tested state, limits and deferred work

`T1-evidence/tested-state.json` records exact SHA-256 for all six changed product files, the unchanged test/validator/scoring/runner/report-contract sources and local fixture scripts/reports; `T1-evidence/protected-files.json` records historical Git object IDs separately from raw file SHA-256. Evidence logs are the authoritative exact command results.

The semantic AC walkthrough is complete and the required tests/local checks pass. No measured savings, future compliance, calibrated judge behavior, native/MXC qualification, runtime-launch readiness or paid-evaluation readiness is claimed. Parent phase/final review remains required. T2/T3, runner metadata/telemetry, deadline reserve and accounting changes are deferred to their own contracts. No unrelated dead-code cleanup or wider documentation reconciliation was performed.

Stale-document disposition within T1 scope: changed impl-review's conflicting persistence/fix rules; plan-review's unconditional marker reuse/final reread; implement/protocol's old phase-verdict, separate-test example and closeout ordering; canonical repeated-report paragraph and prompt README baseline/fix reference. Historical packet and evaluation records remain frozen. Parent owns repository kanban/handoff and subsequent commit records.

Evidence-export tooling note: the first notes/hash refresh failed because Python 3.14 defaulted to cp1252 while the Markdown is UTF-8 (UnicodeDecodeError at byte 0x9d). Repeated the metadata export using explicit UTF-8 byte decoding; no source or validation-result change was needed. The outer PowerShell call continued to diff-check, so its exit 0 was not treated as proof of the failed metadata subcommand.

## Shared phase review - 2026-10-26

Reviewer: /root/phase_review (read-only canonical code-reviewer). Verdict: PASS for AC1-AC9; 44 passed; prompt/snapshot/scenario/validator evidence accepted. No blocking findings with confidence >=80; no optional changes requested. Phase: READY TO ADVANCE. Reviewer inspected the stable aggregate diff, untracked source/tests, saved commands/results and intentional sequential shared-file changes; no broad reruns or external calls. The full AC evidence remains in this note's mapping. Commit byte binding and final impl-review follow this phase gate.

## Parent commit binding - 2026-10-26

Phase commits: 6799ec22a0d202cdd05c98fe6db9eac2853816b2 (workflow), 572bc267d3d782fce720a19988283554a27c4729 (runners and required tests), 15760959e3bb6bb2094eb8e9a0153e200d9ecb28 (scopes/publisher and required tests; shared runbook). Parent compared all 19 product HEAD Git blobs with clean-filtered blobs computed from the tested working files, and separately verified all working-file SHA256 digests unchanged. No mismatch required an isolated rerun. Raw evidence is -text under existing .gitattributes; captured CRLF/trailing output bytes were retained. Product/notes whitespace passed with cr-at-eol and raw evidence excluded; raw diagnostic formatting is preserved, not reported as source whitespace success. Message gates passed before each commit. Final impl-review pending.

## Final acceptance and closeout - 2026-10-26

Task Done. /root/phase_review accepted its ACs/tests and the phase READY TO ADVANCE; all DoD/kanban gates passed. Final impl-review at 15760959e3bb6bb2094eb8e9a0153e200d9ecb28: /root/final_workflow PASS, /root/final_runner PASS, /root/final_accounting PASS WITH WARNINGS; Overall PASS, zero required findings. Two nonblocking accounting warnings retained (full scorer replay open; live compatibility/delivery unverified). Full domain findings/revision anchors are in ../review-impl.md. No optional fixes, test repetitions, new review process, paid run, publication or push. Later record-only commit preserves all 19 tested product code/test blobs; final plugin identity can be retrieved from git HEAD for a separately authorized future baseline.
