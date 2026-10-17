# Geeky Implement Execution Protocol

# geeky-implement

geeky orchestrator that executes the geeky-plan package — drives tasks through the kanban, delegates geeky-coder + reviewer subagents, validates, commits per phase, and keeps handoff.md current. This is the *runtime* counterpart to the `geeky-plan` skill's *planning*.

## Input

`$ARGUMENTS`: a folder produced by `geeky-plan` containing at minimum `implementation-plan.md`, `kanban.md`, `tasks/Tx-*.md`, `handoff.md`, `references.md`.

**Pre-run preflight (STEP ZERO, always):** self-test the tooling before trusting it — `preflight.ps1` on Windows / `preflight.py` elsewhere, passing `-Path/--path <folder>`. It verifies the validators' own dependencies and compilability (a gate script crashing at import time once stalled a 91-hour run), checks handoff/kanban freshness, detects an active `.heartbeat` from a prior run, and reminds about pre-run re-auth for long runs. If it exits non-zero: STOP and report. If any *later* validator crashes mid-run (traceback rather than a clean fail), surface it in one line, manually check the same criteria, and continue or stop VISIBLY — never absorb a crash into a silent stall.

**Pre-run validation (FIRST STEP, always):** invoke the bundled validator. Pick the runtime by host OS (`${CLAUDE_PLUGIN_ROOT}` is the root of the `geeky-orchestration` plugin):

- **Windows (preferred):**
  ```
  pwsh -NoProfile -ExecutionPolicy Bypass -File "${CLAUDE_PLUGIN_ROOT}/scripts/validate-planning-folder.ps1" -Path "<folder>"
  ```
- **macOS / Linux / any host with Python 3:**
  ```
  python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-planning-folder.py" --path "<folder>"
  ```
  (Use `python3` if `python` is not on PATH.)

Both produce identical output and exit codes. If it exits non-zero, print its output and STOP. Do not attempt to regenerate planning artifacts — that is the `geeky-plan` skill's job. If the folder is missing entirely, ask the user.

**Scripts over MCP tools:** always prefer these bundled scripts to the `geeky_*` MCP tools — the MCP tools trigger per-call permission prompts mid-run and are subject to the `${CLAUDE_PLUGIN_ROOT}` interpolation bug. Use the MCP tools only when the scripts are genuinely unavailable. If `${CLAUDE_PLUGIN_ROOT}` is not interpolated in your environment, resolve the plugin root yourself (installed cache: `~/.claude/plugins/cache/<marketplace>/geeky-orchestration/<version>/`; or the source checkout) — do not stall on the placeholder.

Optional inline flags inside `$ARGUMENTS` (parse loosely from the string):
- `--phase=<name|number>` — scope this run to a single phase from `implementation-plan.md`. Default: run all Ready tasks through to Done or Blocked.
- `--dry-run` — produce the execution plan + parallelization decisions only; do not call coders or modify files.
- `--serial` — disable parallel execution for this run (override the default cap of 3).

## Context

To execute the planning package produced by `geeky-plan`: walk the kanban, delegate implementation to `geeky-coder` subagents, validate, run code review and PM-level review, consolidate findings, and keep the kanban, handoff, and per-task notes current.

Operating profile (DO NOT prompt to change mid-run; only respect inline flags above):

- **Autonomy:** fully autonomous from start until the backlog is empty, a task is moved to Blocked, or a validation/review step cannot be auto-resolved. Do not pause for confirmation between tasks.
- **Session grain:** default ONE phase per session. At each phase boundary: checkpoint `handoff.md`, set `.heartbeat` to `paused`, and prefer resuming in a fresh session over pushing through context compaction or token expiry. If the user explicitly asks for a full multi-phase run in one session, honor it — but remind them of the >1h re-auth preflight first.
- **Heartbeat:** maintain `<folder>/.heartbeat` (JSON `{"ts":"<ISO-8601 UTC>","task":"T<x>","status":"running|paused|done"}`). Write `running` at run start, refresh `ts`+`task` on EVERY lane move (same moments you update kanban), set `paused` on deliberate mid-run stop, `done` at run end. External watchdog hooks key on this file — a stale `running` heartbeat is how a dead run gets detected.
- **Review boundaries:** task review answers whether the task meets its ACs and passes its defined tests. Phase review checks the complete phase requirements and decides whether the next phase may start. Final implementation review belongs to `impl-review`; do not add another final-review layer.
- **Commits:** commit per phase, split into multiple small logically-grouped commits (e.g. one for schemas, one for service, one for tests), one concern per commit. **NEVER push to remote.** Never `--no-verify`, never amend, never force.
- **Parallelism:** up to 3 concurrent `geeky-coder` subagents when safe (see Parallelization Rules). Otherwise serial.

## Constitution

**DO THIS SEQUENTIALLY IN THIS ORDER.** All artifact reads and writes happen inside the folder passed in `$ARGUMENTS` (the planning package folder), except for the actual code changes which happen in the project tree the planning folder belongs to.

Hard rules — violations are bugs:

1. **Never modify** `implementation-plan.md`, `feature-specification.md`, `draft.md`, `references.md`, or any `tasks/Tx-*.md` file body. These are the planning contract. The bundled PreToolUse guard will warn if you try. If a task is wrong, add a note in `kanban.md` under Blocked and surface to the user.
2. **Always update** `kanban.md` on every lane move and `handoff.md` on every task completion or block.
3. **Never push** to a remote. Never use `--no-verify`, `--force`, or `--amend`.
4. **Respect declared dependencies.** A task is only eligible when every entry in its `Dependencies:` block is in the Done lane of `kanban.md`.
5. **Stop on Blocked.** When any task moves to Blocked, finalize state (handoff, kanban) and return to the user with a summary. Do not silently skip blocked tasks to keep going.
6. **One source of truth for status:** `kanban.md`. If `handoff.md` and `kanban.md` disagree, trust kanban and reconcile handoff.
7. **Delegate implementation using the canonical `geeky-coder` instructions.** Check the live harness role catalog before dispatch. A TOML file or generated projection does not prove the role is callable. If the role is unavailable, do not retry guessed or namespaced variants. Use an available generic role with the canonical agent body and task brief, preserving requested model settings. If the user requires the registered role itself, report the registration blocker instead of substituting it.

## Task events

Use one append-only `tasks/T<n>.events.jsonl` per task, for example `tasks/T3.events.jsonl`. The orchestrator creates it if absent on dispatch and includes its absolute path in coder/reviewer briefs. Participants read new entries when starting or resuming work and before returning a result. Record consequential progress, findings, blockers, decisions and inbound/outbound dependency changes; omit routine status chatter and reference evidence instead of copying logs.

Each line is a JSON object with `id` (unique within the task), `at` (UTC), `from`, `to`, `type`, `message`, and optional `refs`. Coders and read-only reviewers return event entries with their updates; the orchestrator appends them, preserving the sender and serializing complete-line writes. Do not rewrite previous entries. No acknowledgements are required unless a decision or action needs a response.

For cross-task consequences, append a linked event to each affected task's log and notify an active worker when its work must change. A log entry alone does not wake an agent. Events do not change frozen contracts, Kanban state or acceptance; keep existing notes behavior unchanged.

## Tasks

### Phase 0 — Load and analyze the planning package

1. Run the bundled validators (see Input). On failure, stop. In addition to the planning-folder validator, run the **task-file schema** gate now — it is the plan→implement boundary check (`${CLAUDE_PLUGIN_ROOT}` is the plugin root; `.ps1` on Windows, `.py` elsewhere; full matrix in `AGENTS.md` / `geeky.manifest.json`):

    ```
    python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-task-schema.py" --path "<folder>"
    ```

    If it exits non-zero, the task files are malformed — stop and surface to the user (do not silently fix frozen task bodies).

2. Read every file in the planning folder: `implementation-plan.md`, `kanban.md`, `references.md`, `handoff.md`, `feature-specification.md`, `draft.md`, the most recent `review-*.md`, and every file in `tasks/`. Use `TaskCreate` to track this run's own phases so progress is visible to the user.

2b. **Resume detection (idempotent re-entry).** This skill must be safe to re-invoke after a session cutoff, compaction, or interrupted run — re-invocation continues, never restarts:
   - Tasks in **Done** stay done. Never re-execute them, never re-run their validation, never redo their commits.
   - Tasks stuck in **In Progress** with no live coder are orphans from a cut-off run. Reconcile each against ground truth (git status/log, the declared file surface, any `tasks/Tx-*.notes.md`): if the work appears complete, run the task's validation block and route it through review → Done normally; if partial or absent, move it back to Ready with a kanban note (`<!-- reset from orphaned in_progress: YYYY-MM-DD -->`).
   - If `handoff.md` ends with a `RESUME:` line (see step 17), trust it as the starting hint but verify against kanban (kanban is the source of truth).
   - Then proceed with the normal eligibility walk — it naturally continues from wherever the previous run stopped.

3. Build an in-memory execution model:
   - **Task graph** — node per `Tx-*.md`, edges from each task's `Dependencies:` block.
   - **Phase grouping** — derive from `implementation-plan.md` headings if it has explicit phases, else from kanban grouping comments, else by dependency layer (tasks with no unmet deps = layer 0, etc.).
   - **File-overlap inference** — for each task, scan its `In scope` / `Module/System` / `Technical Notes` for filenames, modules, or package paths. Two tasks are file-conflicting if their declared surfaces overlap.
   - **Eligibility** — task is eligible iff it sits in kanban Ready AND every dependency is Done.

4. If `--dry-run` is set, print the execution model (phase order, per-phase batches, parallel groups with justifications) and STOP. Otherwise continue.

### Phase 1 — Execute each phase

For each phase, in plan order:

5. **Select the next batch** of eligible tasks. Batch size = min(3, eligible count, parallelism flag). A batch is parallel-safe iff:
   - no task in the batch depends on another task in the batch, AND
   - no two tasks in the batch have overlapping declared file surfaces, AND
   - none of them is marked P0-blocker-for-others in the implementation plan.
   Otherwise reduce batch size or fall back to serial. Record the justification in the per-task notes file (step 10).

6. **Move every task in the batch from Ready to In Progress** in `kanban.md`. Add a timestamp comment beside each: `<!-- in_progress: YYYY-MM-DD HH:MM -->`. Refresh `.heartbeat` (`ts` = now, `task` = batch's first task ID, `status` = `running`).

7. **Delegate implementation to `geeky-coder`.** When the batch has >1 task, send a SINGLE message with multiple `Agent` tool calls in parallel (this is required — do not serialize parallel work into separate messages). Each brief must be self-contained:
   - Full text of the task file (paste it — coders don't share your context).
   - **Verified absolute paths** for every file/folder the brief references — verify each exists (Glob/ls) before writing the brief; never pass an assumed path. Subagents don't share your context or memory, and assumed paths are a top wasted-turn cause.
   - Pointers to relevant sections of `implementation-plan.md` and `feature-specification.md` by heading + line range, not just filename.
   - Acceptance criteria copied verbatim.
   - The validation block from the task file (`Tests/Validation Before Next Task`). Within that block, run the cheapest check of the highest-risk assumption first once its prerequisites are available. Reuse established fixtures and helpers. Preserve required ordering and acceptance gates; an early diagnostic result does not replace them.
   - Explicit instruction: *do not modify files outside the declared In Scope surface; if you discover the scope is wrong, stop and report — do not silently expand.*
   - Give the worker authority to finish the bounded assignment, including compatible fixes and required checks. Ask for a consolidated return; interrupt only for blockers, scope decisions or ownership conflicts, not each small edit. Contact the worker only for new information, a blocker, a decision or a completed result; use completion waits instead of repeated status requests. User progress updates do not require another worker round trip.
   - Use the harness's actual dispatch schema and callable role name. Apply the canonical-instructions fallback above only when needed; record the substitution once.

8. **Verify the task's validation evidence** after each coder returns. Require the tested revision or file hashes, exact commands, exit status and results. Inspect the saved output; a bare claim of PASS is insufficient. Reuse passing evidence for unchanged code, dependencies and relevant environment. Execute missing checks or rerun only when evidence is invalidated, unreliable, or independent execution is explicitly required. Before repeating a test or review, record what changed or remains unproved, which evidence is invalidated, and the smallest check that resolves it. Reuse valid evidence unless a required check is missing or independent execution is explicitly mandated. If a required command fails:
   - Capture the failure output.
   - Re-delegate to `geeky-coder` once with the failure context for a fix attempt.
   - If it still fails, move the task to **Blocked** with a kanban note that includes the validation command and the failure summary, finalize state per the Constitution, and return to the user.

9. **Move the task(s) from In Progress to In Review.** Group compatible tasks into shared reviewer assignments when their context and timing make that useful; use separate assignments otherwise. A shared review batch holds progression of every included task until all its blocking findings are resolved and every task has passing required tests and a PASS verdict. Do not move any member to Done or advance its dependents before the batch clears. Preserve individual verdicts and valid evidence; only affected scope needs re-review. Record batch members and the hold/release in each task’s event log. For each assignment:
   - Give the reviewer the task template, task diff, ACs and validation evidence. Its decision is: **Does this task meet every AC and pass its defined tests?** Return an AC-by-AC result, test result and PASS or NEEDS FIXES; missing evidence cannot pass.
   - Inspect immediate dependencies only as needed to answer that question. Do not review the entire implementation chain or add acceptance requirements. Route unrelated findings separately; block this task only when a finding prevents its contract from being met or makes acceptance unsafe under an existing requirement.
   - Every blocking finding must cite the violated AC, defined test or existing mandatory constraint, concrete evidence, and the smallest necessary correction. Severity alone does not authorize extra scope. Record optional improvements as follow-ups.
   - Collect one complete finding set per task before remediation. Group findings by severity and keep a separate verdict for each task, even when reviews share a dispatch.

10. **Write a per-task notes file** `tasks/Tx-*.notes.md` (creating it, NOT editing the original task file) containing:
    - Parallelization decision and justification.
    - Coder summary (one paragraph).
    - Validation results (command + pass/fail).
    - Review findings, grouped by severity.
    - Resolution: which findings were fixed in this run vs deferred (with rationale).
    - Final diff scope (list of touched files).
    Keep review scope, any reopened evidence and the next action in these existing notes. Do not create another ledger or approval gate.

11. **Resolve findings:** batch compatible in-scope fixes from the completed review passes into one assignment per owner. Respect dependencies and shared files; do not dispatch one correction at a time when they can be fixed together. Rerun affected checks and review the changed scope plus the original findings. Preserve unaffected evidence. Blockers and majors within the review contract must be resolved before Done; record unrelated findings separately. Log deferred minors and nits in `handoff.md`.

Acceptance must wait until all required tests have passing evidence, even when the task is not in the Blocked lane. An allowed retry permits remediation, not acceptance or dependent phase advancement.

12. **Move to Done** in `kanban.md` only when validation is green AND no blocker/major findings remain AND any shared review batch has cleared. Before finalizing the move, run the **Definition-of-Done** gate for the task and the **kanban-integrity** gate, and fix until both exit 0:

    ```
    python "${CLAUDE_PLUGIN_ROOT}/scripts/check-dod.py" --path "<folder>" --task T<x>
    python "${CLAUDE_PLUGIN_ROOT}/scripts/validate-kanban.py" --path "<folder>"
    ```

    `check-dod` also prints the task's validation block. Match it to the verified evidence from step 8; printing the commands does not require another execution. Run `validate-kanban` after every lane move, not only at Done, so the board never drifts from truth. Refresh `.heartbeat` on the Done move. If either gate CRASHES (traceback / missing module rather than a clean non-zero): say so in one line, run the equivalent manual check (read the DoD block and verify each item; eyeball lane membership), record the crash in the per-task notes, and continue VISIBLY — a crashed gate must never become a silent stall.

13. **Repeat steps 5–12** until the current phase has no eligible Ready tasks left.

### Phase 2 — End of phase: PM review + commits

14. **PM-level review** at phase end. Delegate to the same agent type used in `geeky-plan` step 6 (development project manager / planning-coordinator). Brief it with:
    - Phase name and the list of Done task IDs.
    - The aggregated diff for the phase (`git diff` from the phase's starting commit to HEAD).
    - The per-task notes files for the phase.
    - The relevant section of `implementation-plan.md`.
    Review the complete phase requirements, combined behavior, cross-task interactions, shared contracts and phase-level validation. Use accepted task verdicts as inputs; do not repeat task reviews without changed dependencies, contradictory evidence or a concrete defect affecting the phase.
    Answer explicitly: **Can we move to the next phase?** Return **READY TO ADVANCE** or **BLOCKED**, with evidence for requirement coverage and any unmet requirement or dependency. All phase tasks must be accounted for; an unfinished required task cannot pass this gate.

15. **Integrate phase findings** in compatible batches using step 11. Resolve failures within the approved scope, then obtain an updated phase verdict. Do not start the next phase until **READY TO ADVANCE** is recorded. If a blocker cannot be resolved under the existing task contracts, mark Blocked and return with the exact unmet requirement. Minors that do not prevent advancement remain deferred.

16. **Commit the phase diff, split into multiple small logically-grouped commits.** Decide grouping by reading the diff yourself (one commit per concern: e.g. schemas, service, endpoints, tests, docs). Each commit message format:

    ```
    feat(<phase-short-name>): <what this commit changes>

    Tasks: T<x>, T<y>
    Refs: docs/<planning-folder>/tasks/Tx-*.md
    ```

    Use HEREDOC to pass multiline messages. Do NOT push. Do NOT amend. If a pre-commit hook fails, fix the underlying issue and create a NEW commit — do not skip hooks.

    Before each commit, validate the message with the **commit gate** (pipe the message via stdin or pass `--message`); fix until it exits 0:

    ```
    printf '%s' "$msg" | python "${CLAUDE_PLUGIN_ROOT}/scripts/check-commit.py"
    ```

17. **Update `handoff.md`** with a phase summary block:
    - Phase name, date, duration.
    - Tasks completed, tasks blocked (if any).
    - Commits created (short SHAs).
    - Phase review verdict, supporting evidence and any advancement blockers.
    - Deferred follow-ups added in this phase.
    - End with a single checkpoint line so any future session can resume with zero re-prompting: `RESUME: <next phase or "run complete"> — next eligible: <task IDs or none>`. Replace the previous `RESUME:` line each time (it is a cursor, not a log).

### Phase 3 — End of run

18. When all phases complete (or backlog is empty, or a task is blocked):
    - When all phases are accepted, route final implementation review to [impl-review](../../impl-review/SKILL.md). Invoke it when final review is authorized by the request or standing workflow; otherwise record it as the next step. Do not substitute another final review or claim final acceptance before its verdict. A phase-only run does not trigger package-wide review.
    - Once the authorized gates pass, finish required closeout and report completion. Do not add discretionary hardening, broader tests or another review. Reopen only for evidence of an unmet approved requirement or mandatory constraint; record optional work as a follow-up.
    - Set `.heartbeat` `status` to `done` (or `paused` if stopping mid-package, e.g. on Blocked).
    - Append a "Run Summary" section to `handoff.md` with: total tasks completed, total commits, blocked items, deferred follow-ups, suggested next-session start steps.
    - Verify `kanban.md` lane counts add up to the original task count.
    - Print to the user: a short status (Done count, Blocked count, Deferred count) and the path to the updated handoff. Suggest the `geeky-status` skill (`/geeky-status <folder>`) as the lightweight follow-up.

## Parallelization rules

When deciding whether to parallelize a batch, apply this checklist explicitly and write the result to the per-task notes file:

| Check | Pass condition |
|---|---|
| Declared dependencies | No task in batch depends on another task in batch (transitively) |
| File-surface overlap | Pairwise intersection of declared In Scope files/modules is empty |
| Shared mutable artifacts | None of the tasks edit the same migration, lockfile, or generated bundle |
| Coordination cost | Tasks are conceptually independent — a reviewer can review them without needing to read the other |
| Resource ceiling | Total concurrent coders ≤ 3 (or 1 if `--serial`) |

If any check fails for a candidate pair, demote to serial for that pair.

Task reviews may run together on stable diffs. Tests or reviewer probes that mutate the same database, fixtures, ports or files must be isolated or serialized. Phase review runs after its task verdicts are available.

Batch independent reads and compatible checks in one dispatch. A shared validation run may satisfy several tasks only when its command, configuration and tested revision meet each task's contract; retain a result for every task. Collect independent failures before remediation when safe. Stop dependent or destructive checks on failure. Separate product defects from harness and environment faults, then fix each compatible set together. Smoke new browser helpers before a broad acceptance run. Reserve broad final gates for a stable candidate unless the plan explicitly requires them earlier.

## Failure modes

After two unsuccessful correction cycles on the same issue, diagnose the cause before repeating the approach: product defect, test expectation, harness/fixture, environment, or unresolved requirement. Record the cause and bounded next action in existing notes. This does not grant extra retries or waive a failed gate; any earlier stop condition still applies.

These are recoverable — handle inline, do not stop the run:
- Coder reports a typo or import error → re-delegate once with the error log.
- Pre-commit hook fails on whitespace/lint → fix and create a new commit.
- Code-review surfaces minor/nit findings → log under Deferred, proceed.
- A gate/validator script CRASHES (traceback, missing module) → one-line surface, manual check of the same criteria, note it, continue; flag the plugin for a fix at run end. Never a silent stall.
- 401/auth-expiry symptoms mid-run → FIRST append a resume block to `handoff.md` (current task, exact state, next command) and set `.heartbeat` to `paused`; the session may be unrecoverable and the handoff is what survives.
- API-error interruption (`<synthetic>` model turn in the log = the API cut the turn off, no auto-resume; external, not your fault) → FIRST checkpoint (`handoff.md` + `.heartbeat` `paused`), then resume — the fix depends on the subtype, so read the turn's text:
  - **spend/usage limit** ("hit your monthly spend limit") → raise it at claude.ai/settings/usage or wait; a `/model` switch does NOT help (account-level quota).
  - **session limit** ("hit your session limit — resets …") → wait for the reset; `/model` does not help.
  - **401 / auth** ("run /login") → re-auth; the session may be unrecoverable, so the handoff is what survives.
  - **529 / overloaded** (genuine capacity) → `/model` switch (capacity is per-model) or wait; status.claude.com. Upstream: anthropics/claude-code #60577, #35801.

**Diagnosing a quiet/stalled run** — when a run has gone silent, check causes in THIS order (cheapest first; the first is external, not model quality):
1. **API-error interruption** — scan the session log tail for `<synthetic>` model turns (NOT for the string "529" — in this environment the real population is spend-limit / session-limit / 401; a genuine 529/overload has not actually occurred here). Fix per subtype above.
2. **Validator/gate crash** — a gate scripted itself into a traceback and the loop absorbed it.
3. **Logic/plan problem** — only after ruling out the external causes above. Misattributing an external interruption to "the model got stuck" wastes a wrong-fix cycle.

These STOP the run (mark Blocked, update handoff, return to user):
- A task's validation block fails after one retry.
- Code review surfaces a blocker that the coder cannot fix in one follow-up.
- Phase review remains BLOCKED after bounded remediation, or requires a change to the approved task contracts.
- A task's declared scope is materially wrong (file doesn't exist, dependency missing from plan).
- Any merge conflict between parallel coders (this means the parallelization decision was wrong — record the lesson in the notes file).

## Acceptance criteria

A successful run leaves the folder in this state:

1. `kanban.md` reflects current truth — every task is in exactly one lane, Done tasks have `[x]`, In Progress / Blocked tasks carry a timestamp comment.
2. `handoff.md` has a new "Run Summary" section at the bottom plus per-phase entries.
3. `tasks/Tx-*.notes.md` exists for every task touched in this run.
4. The project tree has commits (none pushed) that map cleanly to the phases executed.
5. No edits to `implementation-plan.md`, `feature-specification.md`, `draft.md`, `references.md`, or original `tasks/Tx-*.md` files.
6. If anything was blocked, the user sees a clear "Blocked: T<x> — <reason>" line and knows where to look.
7. `.heartbeat` is finalized (`done`, or `paused` with a matching resume block in `handoff.md`) — never left as a stale `running`.

A `--dry-run` invocation must produce the execution model output and modify nothing.

