#!/usr/bin/env node
// make-shim.mjs: write the geeky-orchestrator shim skill from the plugin's own role file, so the shim always
// matches the plugin version under test.
//
//   node make-shim.mjs --agent <plugin>/agents/geeky-orchestrator.md --out <CLAUDE_CONFIG_DIR>/skills
// Writes <out>/geeky-orchestrator/SKILL.md and prints the SHA-256 of the role body it copied.
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";

const argv = process.argv.slice(2);
const flag = (n) => { const i = argv.indexOf(n); if (i < 0 || !argv[i + 1]) throw new Error(`missing ${n}`); return argv[i + 1]; };
const agentPath = resolve(flag("--agent")), outDir = resolve(flag("--out"));
const src = readFileSync(agentPath, "utf8");
const m = src.match(/^---\n[\s\S]*?\n---\n([\s\S]*)$/);
if (!m) throw new Error(`${agentPath}: no frontmatter`);
const body = m[1].replace(/^\n+/, "");
const pluginDir = dirname(dirname(agentPath));

const skill = `---
name: geeky-orchestrator
description: Role definition for this session acting as the geeky-orchestration plugin's geeky-orchestrator, the control plane that chains spec-research, geeky-plan, plan-review, geeky-implement and impl-review. Load when told to act as, or authorize, the geeky-orchestrator.
---

This session is the geeky-orchestrator. \`geeky-orchestrator\` is an agent role in the \`geeky-orchestration\` plugin, not a workflow skill. This compatibility skill reproduces the role definition from the plugin's \`agents/geeky-orchestrator.md\` (body unchanged, below) so you can take on the role directly.

Run each workflow stage with the Skill tool using the plugin's namespaced skill names: \`geeky-orchestration:spec-research\`, \`geeky-orchestration:geeky-plan\`, \`geeky-orchestration:plan-review\`, \`geeky-orchestration:geeky-implement\`, \`geeky-orchestration:impl-review\` (pass the feature folder as args). Dispatch workers with the Agent tool using the plugin's agent types (\`geeky-orchestration:code-explorer\`, \`geeky-orchestration:code-architect\`, \`geeky-orchestration:geeky-coder\`, \`geeky-orchestration:code-reviewer\`). An Agent call returns the worker's report as its result; background completions arrive automatically as \`<task-notification>\` messages.

Relative links in the role text are relative to the plugin's \`agents/\` folder. When this skill was generated the plugin was at \`${pluginDir}\`; the plugin used in this session is the one loaded with \`--plugin-dir\`, and the base directory shown when any \`geeky-orchestration:\` skill loads.

---

${body}`;
mkdirSync(join(outDir, "geeky-orchestrator"), { recursive: true });
writeFileSync(join(outDir, "geeky-orchestrator", "SKILL.md"), skill);
console.log(JSON.stringify({ shim: join(outDir, "geeky-orchestrator", "SKILL.md"),
  role_body_sha256: createHash("sha256").update(body).digest("hex"), source: agentPath }));
