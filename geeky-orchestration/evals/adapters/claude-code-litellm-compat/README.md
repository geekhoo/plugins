# Claude Code compat layer for non-Claude models

Claude Code assumes a Claude model. When a GPT model drives it through LiteLLM, a few of its tool calls do not
fit the harness. This layer corrects those calls in the eval sandbox. It does not change the canonical prompt
or the exported plugin, and it is off for `claude-*` models.

## What it fixes

Found in the C2 runs of 2026-11-02 (`gpt-6.1-sol`, see
[the C2 analysis](../../analyses/c2-macos-mxc-20261102/README.md)):

| Mismatch | Effect without the layer | Correction |
|---|---|---|
| `Skill("geeky-orchestrator")` | `Unknown skill`: it is an agent role, not a skill. Attempt 1 then read the skill files by hand. | A shim skill named `geeky-orchestrator` holds the role text from `agents/geeky-orchestrator.md`. |
| Background `Agent` calls, then a search for a wait or receive tool | Attempt 1 found no wait tool and stopped BLOCKED, although the results had already arrived as task notifications. | The hook runs `Agent` calls in the foreground, so the call returns the worker's report. |
| `ToolSearch` for `wait`, `receive`, `TaskOutput` | Returns only `SendMessage`. | The hook adds a note: no wait tool exists, and results arrive as the Agent result or a `<task-notification>`. |
| `SendMessage` with `notify_when_idle` to a subagent, or extra fields (`type`, `recipient`, `content`) | Rejected, or a message to a finished agent resumes it and repeats its work. | `notify_when_idle` to a subagent is denied with the reason; extra fields are dropped. |
| Bare stage skill names (`spec-research`) | `Unknown skill`. | Rewritten to `geeky-orchestration:spec-research`. |

A PreToolUse hook cannot fix an unknown skill name: Claude Code validates the name before hooks run. That is
why the role is a shim skill rather than a hook rule.

## Related: the Responses bridge

The compat layer fixes tool calls. It does not fix what the gateway drops for GPT on its Messages route (prompt
cache, reasoning text, visible effort). [`mxc-sandbox/bridge`](../../../../mxc-sandbox/bridge/README.md) does; the
C2 launcher enables it with `BRIDGE=1`. The two are independent and can be used together.

## Files

- `compat-hook.mjs`: the PreToolUse hook (matcher `Skill|Agent|ToolSearch|SendMessage`). It reads the model
  from `GEEKY_COMPAT_MODEL`, `CLAUDE_CODE_SUBAGENT_MODEL` or `ANTHROPIC_DEFAULT_SONNET_MODEL` and exits for
  `claude-*`. Each intervention is appended to `$CLAUDE_CONFIG_DIR/geeky-gpt-compat.log.jsonl` (tool, action,
  detail, a hash of the original input).
- `make-shim.mjs`: writes `<config dir>/skills/geeky-orchestrator/SKILL.md` from the plugin's
  `agents/geeky-orchestrator.md`. The role body is copied unchanged under a short preamble, so the shim always
  matches the plugin version under test.

## Install

The macOS launcher (`~/.Projects/mxc-c0/launch-c2.sh`) installs the layer into the sandbox's isolated
`CLAUDE_CONFIG_DIR` (`$MXC_SANDBOX_HOME/home`) for non-`claude-*` models and removes it for Claude models:

```bash
node make-shim.mjs --agent <repo>/geeky-orchestration/agents/geeky-orchestrator.md --out "$CFGDIR/skills"
cp compat-hook.mjs "$CFGDIR/hooks/"
# $CFGDIR/settings.json
{"hooks": {"PreToolUse": [{"matcher": "Skill|Agent|ToolSearch|SendMessage",
  "hooks": [{"type": "command", "command": "<absolute node> \"$CLAUDE_CONFIG_DIR/hooks/compat-hook.mjs\"", "timeout": 15}]}]}}
```

Use an absolute node path: the hook process does not get the workload's `PATH`. Under Santa Lockdown, node is
allowed by TeamID.

## Disclosure

A run with the layer is not identical to a Claude run. The model sees one extra skill in its listing, and
background workers become foreground calls. Record the hook and shim hashes the launcher prints, and archive
the intervention log with the run. The first run with the layer (`gpt-6.1-sol` medium, 20261101T222922Z)
logged 1 shim load, 5 SendMessage rewrites, 1 notify_when_idle deny and 2 ToolSearch notes.

Known limits: the ToolSearch note assumes the build has no wait tool; the subagent id pattern is
`a<hex>[-<hex>]`, so a subagent addressed by name is not recognised; rewrites return `permissionDecision:
allow`, which matters only outside `bypassPermissions`.
