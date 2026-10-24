# C1 Codex runs: Claude review report

2026-10-24. Reviewer: a Claude Code session in `C:\Users\gerald.khoo\geekhoo-plugins` on branch `main`. HEAD is `bee7b14` and origin/main is level with it (0 0). All Codex work since `bee7b14` is uncommitted. This review edited and committed nothing in the repo. Its scratch outputs are under `C:\Users\gerald.khoo\AppData\Local\Temp\claude\C--Users-gerald-khoo-geekhoo-plugins\0ba8396d-1a03-4095-806d-0697f8a2c1ea\scratchpad\`.

## 1. Summary

- **Three Codex C1 runs completed, and all three pass the oracle 118/118, stable over 3 runs.** Scored by the same QACT rules as Claude run 6, they come to 96.3–96.9, 98.0 and 99.6. Claude run 6 has 98.3.
- **The stored Codex scores (81.7 and 89.8) were too low**, almost entirely because the scorer misread the trace. The contestants missed little.
- **Automatic Codex scoring covers run 2's trace shape only.** `codex-process.py` (in `analyses/c1-final-parity-20261024/`) derives run 2's process facts from raw rollouts. Unaided, the scorer gives 98.04 (A 33/34, complete), matching the annotated result; this review re-ran that. Run 1 still relies on a hand-built process-evidence file. Run 3 relies on reviewed corrections: its heredoc kanban writes aren't supported, and the strict raw score exits 1. Claude runs need none of this.
- **Claude runs 1–6 still reproduce exactly** under the current working-tree scorer.

## 2. Scores

| Run | Folder | Models (main / workers) | Tokens | Wall | Stored | Codex repaired | This review |
|---|---|---|---|---|---|---|---|
| Codex 1 | `20261023T182024Z-5fa13924` | Sol/medium / Luna/max | 17.73M | 22.5 min | 81.7 | 96.3 | 96.9 (96.9–97.6) |
| Codex 2 | `20261023T194430Z-c5e04f3f` | Sol/medium / Sol/medium, delegated orchestrator | 13.97M | 22.5 min | 89.8 | 98.0 | 98.0 (94.7–99.5) |
| Codex 3 | `20261023T230041Z-2c3b5489` | Sol/high / medium coders, xhigh reviewers (UNVERIFIED), delegated orchestrator | 18.12M | 23.5 min | none | 99.6 (`derived-final`) | **99.6** (99.55–99.56) |
| Claude 6 | `20261023T104412Z` | Sonnet 5.5 | 8.13M | 40.9 min | 98.3 | 98.3 | 98.3 |
| Claude 4 | `20261022T125647Z` | Sonnet 5.5 | 15.51M | 41.1 min | 97.9 | 97.9 | 97.9 |

### Dimensions in this review

| | Weight | Codex 1 | Codex 2 | Codex 3 | Claude 6 |
|---|---|---|---|---|---|
| Quality | 0.35 | 95.9 | 100 | 100 | 98.6 |
| Adherence | 0.35 | 100 (28/28) | 97.1 (33/34) | 100 (34/34) | 100 (63/63) |
| Consistency | 0.20 | 100 | 100 | 100 | 100 |
| Task tier | 0.10 | 83.1 (Codex: 77.7) | 90.7 | 95.6 | 87.6 |

### What each scorer path gives

The table shows the working-tree `score-run.py` on each Codex run. The "No help" path uses neither manual verdicts nor process evidence.

| Run | No help | With Codex manual verdicts | With Codex process evidence + `--require-complete` |
|---|---|---|---|
| Codex 1 | 74.07 | 86.83 | 96.3 |
| Codex 2 | 63.59 (composite withheld under `--require-complete`) | 86.68 | 98.0 |
| Codex 3 | 60.60 | 63.18 | 99.6 |

### How each Codex score was built

- **Codex 1.** Q 95.9: P 118/118; S 300/414 = 0.725; D 5/5 at the tasks' own commits (T1 `a8a5f34`, T2 `20ed68b`). A 28/28 and C 23/23 come from the trace audit. T2 had two review rounds: NEEDS FIXES at rollout 01a16a09 line 200, then PASS at line 219, so R = 0.5.
  - The review counted T1 at 2 attempts and got T 83.1.
  - Codex counts 3 attempts (calls 107, 109 and 110) and gets T 77.7, composite 96.3. Whether 107 and 109 are separate attempts or one failure run twice is UNRESOLVED.
- **Codex 2.** Q 100: S 300/275 capped at 1; D 4/4 at `97185c1`, `4dc447d` and `c39a486`. A 33/34: four commit-message rows the scorer had dropped all pass. The failure is the final report's false claim that hook configuration was unavailable. C 100. T 90.7 from attempts 1/1/2 and d 347.9/185.3/292.2 s. The review matches Codex's repaired 98.0.
- **Codex 3.** Q 100: S 300/243 capped at 1; D 5/5 at own commits `8691b4a`, `0c14247` and `5e1aa0d`. A 34/34. DPC 23/23, OC 1.0. T 95.63: one attempt and one review round per task, d 146.8/401.9/250.5 s. The review matches Codex's `derived-final` exactly.

**Method.** For each run, read-only auditors checked every failing or n/a check against `session.jsonl` and the child rollouts, under the same rules as Claude run 6:
- D86 and D92: check-dod passing in the same call as the Done move counts as before-Done.
- D93: a delegated orchestrator's calls count as orchestrator calls.
- D27: validation reruns use each task's own commit.

The reviewer spot-checked the key evidence lines in each run. Codex 3 had a mechanical rescore done in a scratch clone of its bundle.

## 3. Why the scorer can't read Codex traces

The scorer pattern-matches tool calls, and its patterns were written against Claude Code transcripts. Each row below is a shape the contestant really produced and the scorer missed.

| Scorer expects | Codex produced | Checks it breaks | Fixtures |
|---|---|---|---|
| A kanban edit or `Set-Content` on `kanban.md` | `$p='…kanban.md'` with `Set-Content $p` inside `exec_command` (runs 1–2); a Python heredoc piped into `python -` calling `Path(...).write_text` (run 3) | handoff_batch, gates_before_done, kanban_after_moves, dp08, dp10, dp14, D27 commit selection | R1 `session.jsonl` #296, #302, #424. R2 rollout 01a16a51 ordinals 139–383. R3 rollout 01a16aff-374e lines 231–525 |
| Skill invocations marking stage starts | All skills pre-read at the start | Stage attribution, dp01, dp04, dp16, commit_msg rows | R2 `session.jsonl` 14–17. R3 `run.json` shows one stage |
| `Agent` calls with `subagent_type: geeky-coder` | `spawn_agent` from a delegated orchestrator, opaque or encrypted brief | Coder ownership, V, T and `geeky_coder_used` | R1 #186, #309. R2 ordinals 145, 205. R3 coder threads 01a16b04, 01a16b07, 01a16b09 |
| The task named in the reviewer's brief | Encrypted brief; task IDs appear only in the reviewer's final message | task_review, phase_verdict, Task tier R | R2 01a16a57 msg 208, 01a16a5c msg 256. R3 rollout 01a16aff lines 331, 524 |
| A command result in the same call | pytest or `check-commit` output arriving in a later `write_stdin` poll | Attempts, dp12 | R2 01a16a58 222→232. R3 rollout 01a16aff line 539 |
| A re-review counted as its own round | `followup_task` on the same thread | R stays 1 when it should be 0.5 | R1 #407 |
| `## Run Summary` | `## Implementation Run Summary` (non-strict regex) | run_summary, dp15 | R1 #434; R3 handoff.md |
| A critical finding in Claude format | Critical finding inside a Codex `agent_message` | critical_fix, dp17 | R1 commit 663206c; R3 commit 7f010e2, rollout 01a16aff line 610 |
| A spawn paired with its run span | Child rollout lifetimes | Researcher concurrency read as 0; dp07 reads max 0 coders | R1 #22, #28, #34 |
| Commands in fenced blocks | Plain-bullet validation commands | D shows 0/0 (vacuous) | R1 `T1-core.md:42`. Fixed in the working tree |
| A Done move to anchor the D27 commit | (no Done move found) | Reruns fall back to the docs-only final commit | R1 `d05528f`, R2 `7c34d2b`, R3 `c9a6775` |

The D27 fallback is a knock-on from the first row: with no Done move found, the scorer reran validation at the final commit and still reported "at each task's commit".

## 4. Codex's repair and its limit

What Codex built (uncommitted, in `evals/analyses/c1-consistent-rescore-20261024/` and `c1-checkpoint5-20261024/`):
- A process-evidence input format: records bound by file hash, record index, timestamp and visible text.
- A validation cache binding task, full SHA, command and result.
- `--require-complete`, which withholds the composite when inputs are missing.
- A frozen replay of Claude runs 1–6.
- New decisions D94–D98.

The reviewer confirmed the source hashes in the working tree: `score-run.py` 34a54671…, `analyze-run.py` f74fadd1…, `codex-trace.py` cf6e8798…. Claude runs 1–6 reproduce at 77.1888, 77.0058, 86.7346, 97.8916, 93.8247 and 98.2718.

The limit is in `builders/build-process-evidence.py.source`. It hard-codes, for each run, which record is which task, lane move, review verdict and commit. Two examples:

```
b.coder(root, 185, c1, "T1", "P1", 195)
b.review(root, ..., [(199, "fail", False), (218, "pass", True)], ["T2"], "P2")
```

The hashes stop invented text. They don't stop a wrong mapping, and no one else has reviewed these mappings, though this review's independent audits agree with them on runs 2 and 3. So defects 1, 2, 4, 5 and 6 are fixed through annotation, not parsing.

**Update (final-parity, 08:00).** `codex-process.py` now extracts run 2's facts with no per-run constants, and they match the hand-built file. The exceptions are two stage starts, 0.5 s and 7.3 s earlier, and neither changes a score. A withheld strict composite now exits 1. Codex's suite gave 286 passed and 3 skipped, and Claude runs 1–6 still reproduce under scorer hash `cf11e6f7`; this review verified both. Neither run 1 nor run 3 is covered yet.

Other gaps in checkpoint 5:
- `--require-complete` exited 0 when it withheld the composite. Final-parity fixed this.
- D95 calls the Codex scores "source-backed, complete" without saying the process evidence is hand-built.
- The closeout itself says no fails-before, passes-after test was written for each defect.

## 5. Parity status (the owner's goal)

| Surface | Status |
|---|---|
| Skills, agents, gate scripts, MCP gates | Same named workflow material; access checked by pre-flight |
| Agent tool and model restrictions | Not identical. Codex projections omit the canonical tool and model metadata; the model matrix is set through role layers |
| Guard hook | **Gap.** Codex parity pre-flights say `runtime_verified: false`. In run 2, `trustStatus` was untrusted, the session had 0 hook-run events, and the matcher wouldn't catch `exec_command` writes. Shell writes bypass Claude's guard too |
| Containment | `trusted-exec.py` uses `danger-full-access`, `--ignore-user-config` and `--ignore-rules` inside outer MXC (confirmed by Codex, recorded in D96). Not re-probed by this review |
| Scoring | **Partial.** Claude: automatic parser plus judgement items. Codex: automatic for run 2's shape. Run 1 is hand-built, and run 3 is reviewed corrections (heredoc lane writes unsupported) |
| Trace data | Codex has no API latency or cost figures. Call counts differ in scope: Codex counts all threads, Claude the main session only |

## 6. Contestant behaviour findings

None of these is a skill edit. They are for the owner.

- **Task granularity.** Codex planned 2–3 tasks to Claude's 7–10, which gives smaller adherence denominators (28–34 against 63–81).
- **Lane discipline.**
  - R2 lane labels were future-dated: the label said 04:02 SGT, but the write happened at 03:52 SGT. Dp08 checks only that a label exists.
  - In R3, T3 jumped Backlog → Ready → In Progress in one edit, against D88. Validate-kanban rejected it twice before the fix.
- **D92 revert.** R3 ran check-dod after validate-kanban with no move back out of Done on failure. It didn't matter, because every check passed.
- **Commits.**
  - Tracking files went into code commits (R2: 4dc447d and c39a486).
  - In R3, geeky-plan had no commit of its own; its files went into the plan-review commit.
- **Reporting.**
  - The R2 final report falsely claimed hooks were unavailable.
  - The R3 final report says all three impl-review domains passed. It doesn't say the money verdict was carried over from round 1, though handoff.md does.
- **Encoding.** One R3 lane write crashed on cp1252 and was retried.
- **Real defects caught by review.**
  - R1: a Unicode-date normalisation defect, fixed in 663206c.
  - R3: a critical input finding, fixed in 7f010e2 and re-reviewed.

## 7. Comparison limits

- **Single runs.** Each run is one execution. Three oracle repeats check one artifact; they aren't three agent runs.
- **Confounds.** Worker model, reasoning level, delegation policy and the operator harness all changed between Codex runs. The Claude runs used different plugin SHAs.
- **No causal claims.** None of this supports a claim of model superiority, or of Sol/medium against Luna/max.
- **Tokens and time.** Codex finished about 45% faster than Claude 6 but used 1.7–2.2× the tokens. Tokens aren't money; Codex cost is unknown.
- **Reference eligibility.** Codex is calibration-only (D53). The 12M C1 ceiling was calibrated on Claude runs.

## 8. Recommendations

1. **Extend `codex-process.py` to runs 1 and 3.** Run 2 is done. For runs 1 and 3, accept the extractor when it reproduces their hand or reviewed evidence, or when each difference shows a mapping error. Add red-before/green-after tests from raw slices, covering run 3's Python-heredoc kanban write and collapsed stages and run 1's variable-path exec writes. Scoring parity follows from this.
2. **Make hook parity a pre-flight gate.** Require a trusted hook that provably fires and a matcher that covers `exec_command` writes. Without these, a Codex run isn't comparable.
3. **`--require-complete` exit code:** fixed in final-parity, which now exits 1. Keep a test for it.
4. **Label hand-built or reviewed evidence as such** in D95 and on the scorecard, for runs 1 and 3, until item 1 lands.
5. **Settle R1 T1's attempt count** (calls 107/109/110) and record the rule.
6. **Process efficiency.** Run each own-commit validation once and score from the cache. Use one scoring pass per run. Lead every report with completeness. Run 2's closeout ran 10 pytest invocations and took 10 minutes 22 seconds.
7. **Rubric candidates** (versioned and applied to both harnesses): timestamp plausibility for dp08, and granularity as a breakdown-only measure. Codex chose to keep the current rules for now (D97).
8. **Commit the Codex work** in logical groups (scorer and trace, tests, adapter, analyses and evidence, docs and decisions), only when the owner asks. More than 46 paths are uncommitted.
9. **Run a paid Claude C1 on current HEAD** to test the corrected D92 order, which is still untested in a paid run.

## 9. Open items and UNVERIFIED

- **UNVERIFIED:** Codex's 306-test suite (not re-run by this review).
- **UNVERIFIED:** R3 reviewer reasoning (xhigh is taken from `run.json`, not from rollout `turn_context`).
- **UNVERIFIED:** the R3 oracle's 3-run stability beyond the PASSED-line count.
- **UNVERIFIED:** R2's T1/T2 own-commit results (text-only provenance, no timestamps).
- **Record drift:** the scorecard, `lessons-learned.md`, plugin README and AGENTS.md (the D92 gate order) were updated with this report. The decision doc has no run 3 entry yet. The adapter kanban still ends with the historical "provisional 81.7" closeout line.
- **Still running:** two `codex` processes were alive at 07:3x on 2026-10-24. Codex was still writing `derived-final` in the R3 folder, and this review read it while it was changing.
- **Not tested:** the scorer's rerun path on Claude runs (only `--no-rerun` reproduction was checked).
- **Supplied to Codex:**
  - `codex-scorer-repair-prompt.md`: the defects, 13 questions and the parity goal. Checkpoint 5 answered it.
  - `codex-checkpoint5-supplement.md`: the extractor and the exit-code, labelling and test items. Not yet answered as of this report.
