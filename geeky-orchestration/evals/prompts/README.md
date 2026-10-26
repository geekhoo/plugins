# Canonical eval prompt

The existing baseline runners render one prompt, [`end-to-end.md`](end-to-end.md), to every contestant for every case. It runs as a single headless session. That keeps mid-session interaction to a minimum and tests how robustly geeky-orchestration runs the whole lifecycle from one instruction: `spec-research` → `geeky-plan` → `plan-review` → `geeky-implement` → `impl-review`, with fixes repeated until the verdict is PASS.

The `/geeky-eval` skill remains planned. The runner scripts are the implemented entrypoints. See [operator readiness](../c0-readiness.md) for the offline check and separate live authorization requirements.

## Rules for the prompt

1. **Case-agnostic.** The prompt never names a case, a stack, a case file, or an expected solution. Case-specific input reaches the contestant only through `brief.md` and `contract.md` at the workspace root.
2. **The workflows run as they are.** The prompt doesn't change or override a skill. It only grants the authorization the workflows ask for, and answers the points where a skill would otherwise stop and ask a human (D16).
3. **No coaching.** The prompt doesn't restate the workflow rules: frozen artifacts, commit format, gates, never push, and so on. Adherence is what's being measured.
4. **Harness-neutral.** Workflows are named by skill, never by a harness-specific slash command or tool name.
5. **Versioned.** Every run records the rendered prompt's `prompt_sha256` and committed `plugin_sha`. A prompt change creates a new future baseline under [D36](../../docs/agent-eval-decisions.md), alongside its expectations/reference versions; historical runs retain their original prompt bytes, requirements, IDs and scores.

The 2026-10-26 compact-report revision changes only the final-output paragraph: one concise report supplies stage verdicts/evidence, numeric tests, commits/final revision and deviations/follow-ups; each workflow's detailed artifact is still required. The five existing `final_report_complete` criteria and its disabled rule are unchanged. Both baseline runners render the same template using the established planning-folder substitution and record its SHA-256 through their existing hash paths. Record the changed plugin fingerprint with the new baseline; local uncommitted-file fingerprints are validation evidence, not a substitute for the committed `plugin_sha` exported by runners.

## Placeholder

| Placeholder | Value |
|---|---|
| `{{PLANNING_FOLDER}}` | `docs/spec-001-feature/`, the same for every case |

## Stop-and-ask points the prompt answers

| Skill (source) | Where it would stop or ask |
|---|---|
| geeky-orchestrator | It won't chain stages without end-to-end authorization. |
| spec-research `SKILL.md:23` | It asks you to confirm the folder name when `docs/` is empty. |
| spec-research `SKILL.md:101` | It flags researcher disagreements for a user decision. |
| geeky-plan `SKILL.md:16,20` | It asks for the requirement or the folder. |
| plan-review `SKILL.md:71,100,148` | It flags judgment calls, trade-offs, and scope or priority questions for the user. |
| geeky-implement `execution-protocol.md:25` | It asks if the folder is missing. |
| geeky-implement `execution-protocol.md:41`, `SKILL.md:70` | It defaults to one phase per session, and gives a re-auth reminder before a full run. |
| geeky-implement `execution-protocol.md:194` | It runs final review only "when final review is authorized". |
| impl-review `SKILL.md` Phase 5 | It asks whether to apply required fixes unless already authorized. |
