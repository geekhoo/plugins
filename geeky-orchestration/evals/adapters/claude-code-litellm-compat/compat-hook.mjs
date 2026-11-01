#!/usr/bin/env node
// compat-hook.mjs: PreToolUse hook for non-Claude models (for example gpt-6.1-sol through LiteLLM) driving
// Claude Code. It corrects tool-interface mismatches only and never changes what the model decides to do
// (which agents, how many, their prompts, worktree use). Claude models pass through untouched.
// Every intervention is appended to $CLAUDE_CONFIG_DIR/geeky-gpt-compat.log.jsonl for the run analysis.
//
// The model comes from the env the runner pins in the sandbox (hooks are not told the model name):
// GEEKY_COMPAT_MODEL, else CLAUDE_CODE_SUBAGENT_MODEL, else ANTHROPIC_DEFAULT_SONNET_MODEL.
import { appendFileSync, existsSync, readFileSync, writeSync } from "node:fs";
import { createHash } from "node:crypto";
import { tmpdir } from "node:os";
import { join } from "node:path";

const model = process.env.GEEKY_COMPAT_MODEL || process.env.CLAUDE_CODE_SUBAGENT_MODEL || process.env.ANTHROPIC_DEFAULT_SONNET_MODEL || "";
if (!model || /^claude-/i.test(model) || process.env.GEEKY_COMPAT_DISABLE === "1") process.exit(0);

let ev;
try { ev = JSON.parse(readFileSync(0, "utf8")); } catch { process.exit(0); }   // never break a call on bad input
const tool = ev.tool_name, input = ev.tool_input ?? {};
const configDir = process.env.CLAUDE_CONFIG_DIR || "";
const PLUGIN = "geeky-orchestration";
const STAGES = ["spec-research", "geeky-plan", "plan-review", "geeky-implement", "impl-review", "archive", "geeky-resume", "geeky-status"];
const AGENT_ROLES = ["geeky-orchestrator", "geeky-implement-orchestrator"];
const inputSha = createHash("sha256").update(JSON.stringify(input)).digest("hex").slice(0, 16);

function log(action, detail) {
  const line = JSON.stringify({ ts: new Date().toISOString(), model, session_id: ev.session_id, agent_id: ev.agent_id ?? null,
    tool, action, detail, input_sha256_16: inputSha, tool_use_id: ev.tool_use_id }) + "\n";
  for (const dir of [configDir, tmpdir()].filter(Boolean)) {
    try { appendFileSync(join(dir, "geeky-gpt-compat.log.jsonl"), line); return; } catch { /* try the next location */ }
  }
}
// writeSync: a buffered stdout write followed by exit can drop the JSON on a pipe
const out = (o) => { writeSync(1, JSON.stringify({ hookSpecificOutput: { hookEventName: "PreToolUse", ...o } })); process.exit(0); };
const deny = (reason, detail) => { log("deny", detail); out({ permissionDecision: "deny", permissionDecisionReason: reason }); };
// "allow" is what the 2026-11-02 MXC smoke test exercised; under bypassPermissions it skips nothing extra
const rewrite = (updatedInput, why, detail, extra = {}) => { log("rewrite", detail); out({ permissionDecision: "allow", permissionDecisionReason: why, updatedInput, ...extra }); };
const context = (text, detail) => { log("context", detail); out({ additionalContext: text }); };

const stageList = STAGES.slice(0, 5).map((s) => `${PLUGIN}:${s}`).join(", ");

if (tool === "Skill") {
  const name = String(input.skill ?? "");
  const bare = name.startsWith(`${PLUGIN}:`) ? name.slice(PLUGIN.length + 1) : name;
  // With the shim skill installed ($CLAUDE_CONFIG_DIR/skills/<role>/SKILL.md, generated from the plugin's role
  // file), the bare role name loads it. Without a config dir there is no shim to look up.
  if (AGENT_ROLES.includes(bare) && name === bare && configDir && existsSync(join(configDir, "skills", bare, "SKILL.md"))) {
    log("allow-shim", { skill: name }); process.exit(0);
  }
  if (AGENT_ROLES.includes(bare)) {
    deny(`"${name}" is not a skill: ${bare} is an agent role in the ${PLUGIN} plugin, and this session is already acting as the ${bare}. ` +
      `Do not invoke it. Run each workflow stage yourself with the Skill tool using the namespaced skill names: ${stageList} ` +
      `(pass the feature folder as args). Subagents are dispatched with the Agent tool using subagent_type values such as ` +
      `${PLUGIN}:code-explorer, ${PLUGIN}:code-architect, ${PLUGIN}:geeky-coder, ${PLUGIN}:code-reviewer.`, { skill: name });
  }
  if (!name.includes(":") && STAGES.includes(name)) {
    rewrite({ ...input, skill: `${PLUGIN}:${name}` }, `namespaced skill ${name} -> ${PLUGIN}:${name}`, { from: name, to: `${PLUGIN}:${name}` });
  }
  process.exit(0);
}

if (tool === "Agent" && input.run_in_background === true) {
  // Foreground: the call blocks and returns the worker's final report as its result, which is this harness's
  // receive step. Several Agent calls in one assistant message still run concurrently.
  rewrite({ ...input, run_in_background: false }, "foreground subagent: its report is returned as this tool's result",
    { subagent_type: input.subagent_type, description: input.description },
    { additionalContext: "This Agent call runs in the foreground: its result IS the worker's report (the collect/receive step). No separate wait tool exists or is needed." });
}

if (tool === "ToolSearch" && /\b(wait|receive|taskoutput|await)\b/i.test(String(input.query ?? ""))) {
  context("There is no wait or receive tool in this harness, and none is needed. Agent calls return the worker's report as their " +
    "tool result. If a background task or agent was started, its completion is delivered automatically into your context as a " +
    "<task-notification> message containing the full result: read it and continue the workflow. Do not stop or checkpoint for lack of a wait tool.",
    { query: input.query });
}

if (tool === "SendMessage") {
  const to = String(input.to ?? input.recipient ?? "");
  const isSubagent = /^a[0-9a-f]{8,}(-[0-9a-f]+)*$/.test(to);   // Claude Code agent ids: a<hex>[-<hex>...]
  if (input.notify_when_idle && isSubagent) {
    deny(`notify_when_idle does not apply to subagents. Subagent results are returned by the Agent call itself or delivered ` +
      `automatically as <task-notification> messages; read those and continue. Do not message finished agents (that resumes them).`, { to });
  }
  const allowed = ["to", "message", "summary", "notify_when_idle"];
  const extra = Object.keys(input).filter((k) => !allowed.includes(k));
  if (extra.length) {
    const cleaned = { to, message: input.message ?? (typeof input.content === "string" ? input.content : ""), ...(input.summary ? { summary: input.summary } : {}),
      ...(input.notify_when_idle !== undefined ? { notify_when_idle: input.notify_when_idle } : {}) };
    if (!cleaned.message) deny("SendMessage needs a non-empty 'message' field (fields: to, message, summary, notify_when_idle).", { dropped: extra });
    rewrite(cleaned, `SendMessage input normalized to its schema (dropped: ${extra.join(", ")})`, { dropped: extra });
  }
}
process.exit(0);
