# Fresh-session handoff

Target: Gerald's Windows machine, PowerShell 7. Workdir: `C:\Users\gerald.khoo\geekhoo-plugins`.
Report budget: 600 words plus commands/evidence links.

Before acting, run `git rev-parse HEAD`, `git status --short` and `git diff --stat`. Verify source baseline `8fff98b0f087f148d4f416f512dc9988d61a57aa` exists through Git and inspect changes since it before using the implementation anchors. The later local planning-review commit is expected; the pin identifies reviewed source, not a required current HEAD. Do not reset to the pin or overwrite other work. Find the review commit with `git log -1 --format=fuller -- geeky-orchestration/evals/analyses/c0-claudex-001-win-20261026/remediation-20261026/review-plan.md`.

Read in order:

1. `geeky-orchestration/AGENTS.md`.
2. This folder's `implementation-plan.md`, `references.md`, `review-plan.md`, `kanban.md`.
3. `tasks/T1-streamline-workflow.md`, `tasks/T2-bound-runner.md`, `tasks/T3-scope-and-readback.md` in that order.
4. The task's implementation anchors and linked C0 reports.

Current verified state: both external reviews, the side-review proposals and C0 evidence were checked against pinned source. The packet incorporates the three approved planning additions. T1 removes review/output overhead independently; T2 supplies runner/optional timing controls; T3 supplies scope/readback. Formal four-phase planning verification and its current verdict are recorded in `review-plan.md`; the earlier informal review is retained as history. Optional duplicate specification/draft documents are intentionally omitted. No runner, skill, prompt, scorer, candidate or raw evidence has been changed. No evaluation, provider/judge call, live telemetry access/publication or push was performed. The invoked plan-review workflow authorizes its local planning commit. No implementation task is Done.

Takeover scope: when the user requests implementation, execute T1 → T2 → T3 with one writer and parent integration. Product/test changes go through `geeky-coder` under repository workflow rules. Use independent read-only reviewer domains after writes stop. An explicitly invoked plan-review permits the lead's required packet corrections and local commit under that skill; its reviewer assignments remain read-only. This handoff grants no additional implementation, evaluation or push authority.

Validation environment verified on 2026-10-26: PowerShell 7.6.5 and `C:\Python314\python.exe` with pytest 9.1.1. The task briefs' `python -m pytest` examples require this interpreter (invoke it with `& 'C:\Python314\python.exe' -m pytest ...`) or a verified equivalent. Default PATH Python 3.13 lacks pytest. Only version probes and planning validators ran during review; no implementation test result is implied.

Preserve historical prompt bytes/requirements, scores/IDs, raw captures, H1 selection and the owner qualification waiver. T1 permits one prospective change to the canonical prompt's final-output paragraph, preserving all five report criteria and recording a new prompt hash/baseline under D36. No coaching or case-contract change is allowed. Initial Codex 97.46, Claude timeout 90.33 and cumulative Claude 98.33 describe different scopes. Do not add model calls, paid retries, qualification probes, judges or live score publication. Preserve unknown backend identity, billed cost and cumulative token counts.

Done criteria: all three task AC sets have offline evidence, including terminal-verdict scenarios, conservative planning-review invalidation, compact-report compatibility and prompt hash checks; planning/board state is consistent; phase reviewer accepts each task and the phase; final implementation review clears required findings; README, touched skill/prompt/runbook/telemetry guidance, kanban, references and this handoff reflect actual changes. All tasks and gates precede consideration of a separately authorized evaluation. No expanded outbox, orchestration engine, platform migration or arbitrary-trace work is required.

Remaining uncertainty: reserve sizing and model obedience need a separately authorized future run. Linux/macOS runner behavior and descendant cleanup remain unproven. Missing full replay inputs leave the corresponding replay check open, not silently waived.
