# Canonical Eval Prompt

`/geeky-eval` sends one prompt, [`end-to-end.md`](end-to-end.md), to every contestant for every case. It runs as a single headless session. That keeps mid-session interaction to a minimum and tests how robustly geeky-orchestration runs the whole lifecycle from one instruction: `spec-research` → `geeky-plan` → `plan-review` → `geeky-implement` → `impl-review`, with fixes repeated until the verdict is PASS.

## Rules for the prompt

1. **Case-agnostic.** The prompt never names a case, a stack, a case file, or an expected solution. Case-specific input reaches the contestant only through `brief.md` and `contract.md` at the workspace root.
2. **The workflows run as they are.** The prompt doesn't change or override a skill. It only grants the authorization the workflows ask for, and answers the points where a skill would otherwise stop and ask a human (D16).
3. **No coaching.** The prompt doesn't restate the workflow rules: frozen artifacts, commit format, gates, never push, and so on. Adherence is what's being measured.
4. **Harness-neutral.** Workflows are named by skill, never by a harness-specific slash command or tool name.
5. **Versioned.** Every run records the prompt's content hash. A prompt change changes the baseline version (D36).

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
| impl-review `SKILL.md:127` | It asks whether to apply fixes for critical issues. |
