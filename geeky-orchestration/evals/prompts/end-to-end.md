Use the geeky-orchestration workflows to take the requirement in `brief.md` and `contract.md` at the repository root from specification to a reviewed, accepted implementation, all in this one session.

This is explicit end-to-end authorization for the `geeky-orchestrator` to chain these workflows in order without pausing for confirmation:

1. `spec-research`, with `{{PLANNING_FOLDER}}` as the feature folder.
2. `geeky-plan` on `{{PLANNING_FOLDER}}`.
3. `plan-review` on `{{PLANNING_FOLDER}}`.
4. `geeky-implement` on `{{PLANNING_FOLDER}}`. This is an explicit request for a full multi-phase run in this session.
5. `impl-review` on `{{PLANNING_FOLDER}}`. Final review is authorized and fixes are approved in advance. Apply the fixes it calls for and run `impl-review` again, repeating until its overall verdict is PASS.

Wherever a workflow would stop to ask a human, use these answers:

- **Feature folder:** use `{{PLANNING_FOLDER}}`. Do not ask to confirm it.
- **Precedence:** `contract.md` is authoritative. Research and planning support it; they never change what it requires.
- **Researchers disagree:** decide using `contract.md` and the evidence. Record the decision and the alternative in the specification.
- **Flags or questions about scope, priority or trade-offs:** decide them yourself, choosing the option closest to `contract.md`. Record each decision and its reason in `handoff.md`, then continue.
- **Session length:** skip the re-authentication reminder.

You are authorized to make the commits these workflows' procedures make. Do not run any workflow other than these. Do not wait for human input at any point. If a workflow cannot continue, record the reason in `handoff.md` and stop.

When you finish, give one concise completion report: the overall outcome; a table for the five stages, each with its substantive verdict or explicit unreached status, artifact path and brief supporting command/result, gate or reviewer verdict; final numeric test results with their evidence; commits made (short SHAs or subjects) and final revision; and deviations, blockers, interventions and deferred warnings, or an explicit statement that there were none. Include the evidence basis for each passing stage in the response itself, beyond links. Keep the detailed reports in the artifacts required by each workflow.
