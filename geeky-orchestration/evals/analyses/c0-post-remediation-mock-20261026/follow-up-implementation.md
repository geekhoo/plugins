# Minimal C0 follow-up implementation — 2026-10-26

Current source HEAD and implementation baseline: `2d30f483c4f322488c2843a8423f1a467a16171f` (unchanged). Changes are uncommitted. The user's later request authorizes this exact [follow-up plan](follow-up-plan.md), guarded mock-support promotion and bounded model-free verification. The plan's older planning-only authorization paragraph remains historical; its scope is unchanged. No source commit/push, paid contestant/provider/judge evaluation, sign-in or live telemetry operation occurred.

One implementation phase contains two sequential units. Lead `/root/sol_followup_implementation` is GPT-6.1-Sol/xhigh; `geeky-coder` workers `/root/sol_followup_implementation/luna_lifecycle` and `/root/sol_followup_implementation/luna_fixture` used GPT-6-Luna/max with cold, disjoint ownership and one writer at a time. The lead owns integration and records. The phase reviewer is `/root/sol_followup_implementation/phase_followup` (GPT-6.1-Sol/xhigh, code-architect). Phase and final-review verdicts are recorded separately below; passing commands alone do not issue acceptance.

## Delivered behavior and AC evidence

| Unit | Result and evidence |
|---|---|
| F1 lifecycle | Entering capture completes only the successfully returned `seed-oracle` step after the remaining-budget check. Failed seed, interrupted capture, unknown outcome and later failures retain their semantics. The final suite asserts both capture-time seed state and finalized success/crash/timeout postprocessing. Both fresh real-MXC positives finalize with every postprocessing entry completed; the timeout/oracle-fault retains completed seed, failed oracle and timeout. F1 is fixed and freshly verified. |
| F2 timing boundary | Remaining seconds are floored at invocation preparation; no expired recovery starts. Invocation measurement includes running-record handling and the synchronous MXC call through return; finalization is separate. Fake-host overrun accounting preserves truthful elapsed time and timeout. The fresh 30-second fault attempt supplied 28 seconds, measured 28.8078931 seconds for the invocation and 30.4207663 seconds for the attempt; finalization was 0.9793902 seconds. An absolute process-stop cutoff or maximum excess remains unproved. No margin was invented. |
| Maintained fixture/H1 | Selectively promoted the seven semantic support paths, keeping Python mock targets, `c0-wordstat`, `-MockAgent -NoTelemetry`, isolated fresh roots and denied egress. Actual kanban writes occur once; actual Python/Git results and skill-file reads provide existing supported trace shapes. Unchanged `Scorer.load/derive/rerun_commit` derives successful In Progress and Done anchors. H1 and scoring/parser formulas are unchanged. |

The current-byte offline positive fixtures selected implementation SHAs `8d0287175d6e5ae29f39e72ace61572cec7cbc18` (Claude) and `18440df27f5115dcc3cb9f5ca4f00bfd64872b76` (Codex), with all declared commands passing and source plus required tests in each delivery. The negative Codex fixture selected source-only `dc38a855df99f2a6c103f829d9782a8894ee96cd`; tests arrive in `9630724790c8746fa12b80abe9c5cd2a3f8339fd`, and final HEAD `46131cd119bf8354823ec6b92f08354608ae05f4` passes commands that fail at the selected earlier snapshot. Parsed Done call IDs/paths/times and non-fallback selection bases are in the machine evidence; none uses `no Done move` or injected expected timestamps.

## Verification and provenance

`C:/Python314/python.exe -m pytest -q -p no:cacheprovider` ran `evals/scripts/test_run_lifecycle.py`, `evals/mock-agent/test_c0_fixture.py`, `evals/adapters/codex/test_mock_codex.py`, `test_score_run.py` and `evals/scripts/test_codex_trace.py` under `geeky-orchestration/`: **147 passed, 1 optional native-proof skipped in 296.08s**, exit 0. PowerShell AST and scoped whitespace checks pass. A two-case sensitivity probe against the old helper fails exactly on seed `in-progress`, as expected. The final aggregate supersedes diagnostic/interrupted attempts and the earlier fixture run's post-test wording changes; exclusions and provenance are explicit in [follow-up-evidence.json](follow-up-evidence.json).

Fresh external root: `C:/repos/c0f-20261026-7c2b53`. A sparse derived harness retains the same pinned HEAD, then copies/hash-verifies ten current runtime/test/timing files. Runners copy the working mock/helper payloads; the committed plugin export excludes evals. The working diff SHA256 is `eaef65e66620c6c259fb043fd5c0ef1f3859cd005492e8f1cc16444cb982f090`; individual hashes bind new files as well. No source commit was needed to test current changes.

Exactly **3 real Windows MXC attempts / 3 top-level workload invocations** ran after the offline gate; no further run is scheduled.

| Check | Observed result |
|---|---|
| Claude full positive | Child 0/success, finalized, seed/all steps completed, oracle 13/13 ×3, candidate 17 tests. H1 selects `ebca998faa0761691fcdf1ee544336dd31c27ff0` for both tasks; 4/4 commands pass, no fallback, Done basis recognized. |
| Codex full positive | Child 0/success, finalized, seed/all steps completed, oracle 13/13 ×3, candidate 17 tests. H1 selects `7e8dc09923e6bf1374f1a641dd69ba568e7799bc` for both tasks; 4/4 commands pass, no fallback, Done basis recognized. |
| Claude timeout + oracle fault | Child 124/timeout; controller 1 is the expected injected directory-write exception. State incomplete, oracle failed, seed completed, raw capture retained. Injection `applied=true`, `original_bytes_removed=false`. |

Each positive uses fresh homes/state, a verified vetted MXC build, the Python workload and `--deny-net`; provider/telemetry environment was cleared without displaying secrets. No model executable fallback or real credential was loaded. The post-collection process check found zero matching Python/MXC workloads. Scripted verdicts and new synthetic composites remain ineligible for a model ranking; four scorer judgment items remain unresolved. Parser `model_calls` are synthetic trace counts, not inference or billing proof.

Preservation after-check: all **196** saved snapshots / **1,891,615 bytes**, **93** newer raw captures, **141** tracked historical live-C0 raw files and **8** frozen contracts are unchanged. Historical scores remain **97.46 / 90.33 / 98.33**. The once-only cache search found no retained source-bound `validation-cache.json`; full historical scorer replay remains **OPEN**, without candidate re-execution. Live telemetry compatibility/delivery and model obedience/speed remain unverified.

## Records and acceptance

Updated current pointers: repository README, plugin README, this analysis README/handoff, and dated follow-up links in the earlier remediation board/handoff. Original report, accuracy review, support snapshot, metrics, frozen follow-up plan, original contracts and dated implementation reviews remain untouched. Large new logs/captures stay in the external fresh root; compact source-bound hashes and paths are in [follow-up-evidence.json](follow-up-evidence.json).

Independent [phase review](phase-review.md): both units PASS; **READY TO ADVANCE**, zero required findings. Reviewer `/root/sol_followup_implementation/phase_followup` verified the current source/dependency/artifact/runtime hashes without rerunning checks. Final three-domain [impl-review](review-impl.md): lifecycle/deadline PASS WITH WARNINGS, fixture/H1 PASS, evidence/docs/boundaries PASS WITH WARNINGS; **Overall PASS**, zero required findings. Each GPT-6.1-Sol/xhigh code-reviewer ID and source/hash-bound reply is saved there. Parent/root independently verified all 11 source hashes, five unchanged dependencies, 17 external artifacts, three runtime-record hashes and all 196 original snapshots without product edits or test/runtime repetition. Implementation and required closeout are complete; changes remain uncommitted, and no further workload is scheduled.

## Publication update — 2026-10-26

The implementation-time statements above describe the reviewed pre-commit state. The
user subsequently authorized grouped source commits and a push. Lifecycle/timing work is
committed as `ebcbacd180550744c4c9832f6197610ccac44864`; the guarded fixture and runner
work is committed as `6462c6d27fe9c1a3508f8a8b090529b33be3a936`. Documentation/evidence
reconciliation is committed in the following history entry. No workload, test, provider,
judge or telemetry operation was run for publication.

Five of the eleven tested text files were CRLF in the tested working tree and normalized
to LF in Git according to repository settings. `follow-up-evidence.json` preserves the
tested working-tree SHA256 values. The normalized Git-blob-content SHA256 mappings are:

| File | Tested working-tree SHA256 | Git blob-content SHA256 |
|---|---|---|
| `geeky-orchestration/evals/QUICKSTART.md` | `f382e0ecdbfd79570cd92c1915ae9a81cfeff0ea2520d6f1371185753eb367d7` | `01a8dd75aa74ffbb0405f6b04422bef00fba052565e64f21c76470600c7fadce` |
| `geeky-orchestration/evals/adapters/codex/mock_codex.py` | `0666c649c86cabc8eaefd7c4f021b9792ae5234d34974bb37dcb45ef7562e665` | `73ab568c308fa46abfc9f722537003c48a5e13fd073ecb20a3bedacf6362845b` |
| `geeky-orchestration/evals/mock-agent/mock_claude.py` | `cd99d8fa233b63c6bac61ecd8e8df558cffd3c7e45a7c51c7f354d2829359f76` | `869d7412a17d5422d49e63ff08c0f023dd82326f69fcccca9748da62f124a5c9` |
| `geeky-orchestration/evals/scripts/run-baseline.ps1` | `c9a6ae7619d505d07a2b820c1a72f972639fe0e51e6701fe3579439c25af0409` | `a46df20bb2c9299955b71e5466310d053b34a193f32270c692c938d746508132` |
| `geeky-orchestration/evals/scripts/run-codex-baseline.ps1` | `14fa71730d60d3e1b5eb1ac81e3adee533947923d88a3c84f10b63546453a9dc` | `0bb4491906a8a8c309101507854d8f96240f46d81b90d5237261679526dd3c0f` |

The other six tested file blobs retain the exact tested-byte hashes. To locate the
documentation/evidence reconciliation commit, use `git log`; it is intentionally not
self-referenced here. Historical report, plan, reviewer records and raw captures remain
unchanged.
