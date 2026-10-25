# Claude C0 status

Historical board for the provider-blocked attempts. Superseded for current state
by [router-fixed/kanban.md](router-fixed/kanban.md): retry timed out after passing
implementation tests; parity 90.33 published and verified.

## Done

- Launch Claude on the same case, alias, prompt/export and Windows MXC setup.
- Verify initial MCP connectivity and shared input equality with Codex.
- Preserve the provider-blocked segment and run-local header change.
- Attempt one same-session startup-header recovery without changing the task/model.
- Honor the user's fresh restart request in the same workspace/config folders.
- Supply geeky-resume instructions and explicit granted plugin-root variables.
- Verify the fresh restart fails before tools; preserve all prior state.
- Capture Langfuse records and publish execution-health status without a fake parity grade.

## Blocked

- Specification, planning, implementation and final review: provider HTTP400
  MissingSessionID prevents the model from continuing.
- Header propagation through the request path needs diagnosis before more paid attempts.

## Not claimed

- No implementation completion, no model-quality failure score, no qualification rerun.
- No fourth attempt, repository commit or push is scheduled.
