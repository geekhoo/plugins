# Signal patterns to search for

Supporting reference for `self-audit`. Hypotheses, not a rigid checklist — always read surrounding context, don't pattern-match blindly:

- `is_error` / `"is_error":true` in tool_result blocks → a tool failed and needed a retry.
- The same tool called repeatedly with small variations → trial-and-error loop.
- Harness rejection strings: `"doesn't want to proceed with this tool use"`, `"STOP what you are doing"` → user rejected a tool call.
- Short sharp user messages: `no`, `don't`, `stop`, `that's not what I meant`, `wrong` → explicit correction.
- Assistant self-correction language: `let me reconsider`, `I made a mistake`, `apologies`, `that didn't work`, `actually` → backtracking.
- `command not found`, `exit code 1`, `Cancelled: parallel tool call` → environment/shell friction.
- Repeated identical first-prompts across sessions minutes apart → abandoned restarts (often infra/model-routing, not reasoning — check before blaming the assistant).
