#!/usr/bin/env node
/**
 * sync-agents.js
 *
 * Node.js equivalent of sync-agents.py — zero external dependencies (stdlib only).
 * Project utility for projecting canonical plugin agents (agents/*.md) into
 * harness-specific locations/formats so they can be discovered/registered by
 * multiple coding harnesses.
 *
 * Canonical source (this plugin):
 *   <plugin-root>/agents/*.md
 *
 * Generated projections:
 *   Claude Code:     <project-root>/.claude/agents/*.md
 *   Copilot/VS Code: <project-root>/.github/agents/*.agent.md
 *   Codex CLI:       <project-root>/.codex/agents/*.toml
 *   Cursor (exp):    <project-root>/.cursor/agents/*.md
 *   Generic Markdown:<project-root>/.agents/*.md
 *
 * Contract (matches sync-agents.py):
 *   Exit 0 on success, 1 on validation or write failures.
 *   Human summary on stdout.
 *   Optional --json for machine-readable output.
 *
 * Usage:
 *   node sync-agents.js [--source <dir>] [--project-root <dir>]
 *                        [--targets claude,copilot,codex,cursor,generic]
 *                        [--agents <comma-separated-names>]
 *                        [--dry-run] [--json]
 */

"use strict";

const fs   = require("fs");
const path = require("path");

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const SUPPORTED_TARGETS = ["claude", "copilot", "codex", "cursor", "generic"];

// ---------------------------------------------------------------------------
// CLI arg parsing  (no third-party libs)
// ---------------------------------------------------------------------------

function parseArgs(argv) {
  const here       = path.resolve(__dirname);
  const pluginRoot = path.resolve(here, "..");
  const repoRoot   = path.resolve(pluginRoot, "..");

  const defaults = {
    source:      path.join(pluginRoot, "agents"),
    projectRoot: repoRoot,
    targets:     SUPPORTED_TARGETS.join(","),
    agents:      "",
    dryRun:      false,
    asJson:      false,
  };

  const args = { ...defaults };
  const raw  = argv.slice(2);

  for (let i = 0; i < raw.length; i++) {
    const a = raw[i];
    if (a === "--dry-run")                   { args.dryRun = true; }
    else if (a === "--json")                 { args.asJson = true; }
    else if (a === "--source")               { args.source = raw[++i]; }
    else if (a.startsWith("--source="))      { args.source = a.slice("--source=".length); }
    else if (a === "--project-root")         { args.projectRoot = raw[++i]; }
    else if (a.startsWith("--project-root=")){ args.projectRoot = a.slice("--project-root=".length); }
    else if (a === "--targets")              { args.targets = raw[++i]; }
    else if (a.startsWith("--targets="))     { args.targets = a.slice("--targets=".length); }
    else if (a === "--agents")                { args.agents = raw[++i]; }
    else if (a.startsWith("--agents="))       { args.agents = a.slice("--agents=".length); }
    else if (a === "--help" || a === "-h") {
      console.log([
        "Usage: node sync-agents.js [options]",
        "",
        "Options:",
        `  --source <dir>         Canonical agent .md directory (default: ${defaults.source})`,
        `  --project-root <dir>   Repo root for .claude/.github/.codex/.cursor/.agents (default: ${defaults.projectRoot})`,
        `  --targets <list>       Comma-separated: claude,copilot,codex,cursor,generic (default: all)`,
        "  --agents <list>        Comma-separated canonical agent names (default: all)",
        "  --dry-run              Preview only; do not write files",
        "  --json                 Emit JSON summary to stdout",
        "  --help                 Show this help",
      ].join("\n"));
      process.exit(0);
    }
  }

  return args;
}

// ---------------------------------------------------------------------------
// YAML frontmatter parser  (hand-rolled, no yaml lib needed)
// ---------------------------------------------------------------------------

function stripQuotes(value) {
  const v = value.trim();
  if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) {
    return v.slice(1, -1);
  }
  return v;
}

/**
 * Parse YAML frontmatter from a markdown string.
 * Returns { fm: { [key]: string }, body: string }.
 * Supports scalar values, block scalars (|, |-, >, >-), and basic lists.
 */
function parseFrontmatter(mdText) {
  const lines = mdText.split(/\r?\n/);
  if (!lines.length || lines[0].trim() !== "---") {
    throw new Error("missing YAML frontmatter opening '---'");
  }

  let endIdx = null;
  for (let i = 1; i < lines.length; i++) {
    if (lines[i].trim() === "---") { endIdx = i; break; }
  }
  if (endIdx === null) throw new Error("missing YAML frontmatter closing '---'");

  const fmLines = lines.slice(1, endIdx);
  const body    = lines.slice(endIdx + 1).join("\n").replace(/^\n+/, "");

  const fm = {};
  let i    = 0;

  while (i < fmLines.length) {
    const raw = fmLines[i];
    if (!raw.trim() || raw.trim().startsWith("#")) { i++; continue; }

    const m = raw.match(/^([A-Za-z0-9_-]+)\s*:\s*(.*)$/);
    if (!m) { i++; continue; }

    const key   = m[1].trim();
    const value = m[2].trimEnd();

    if (["|", "|-", ">", ">-"].includes(value)) {
      i++;
      const block = [];
      while (i < fmLines.length) {
        const nxt = fmLines[i];
        if (nxt.startsWith(" ") || nxt.startsWith("\t") || !nxt.trim()) {
          block.push(nxt.startsWith(" ") ? nxt.slice(1) : nxt);
          i++;
        } else break;
      }
      let joined = block.join("\n").replace(/^\n+|\n+$/, "");
      if (value.startsWith(">")) {
        // fold: join non-empty lines with a space
        joined = joined.split("\n").map(l => l.trim()).filter(Boolean).join(" ");
      }
      fm[key] = joined;
      continue;
    }

    fm[key] = stripQuotes(value.trim());
    i++;
  }

  return { fm, body };
}

function parseTools(rawTools) {
  if (!rawTools) return [];
  let raw = rawTools.trim();
  if (raw.startsWith("[") && raw.endsWith("]")) raw = raw.slice(1, -1);
  return raw.split(",").map(p => stripQuotes(p.trim())).filter(Boolean);
}

// ---------------------------------------------------------------------------
// Agent loading & validation
// ---------------------------------------------------------------------------

function loadAgent(filePath) {
  const text          = fs.readFileSync(filePath, "utf8");
  const { fm, body }  = parseFrontmatter(text);

  const name = (fm.name || "").trim();
  const desc = (fm.description || "").trim();

  if (!name) throw new Error(`${path.basename(filePath)}: missing 'name' in frontmatter`);
  if (!desc) throw new Error(`${path.basename(filePath)}: missing 'description' in frontmatter`);
  if (!body.trim()) throw new Error(`${path.basename(filePath)}: empty agent prompt body`);

  return {
    sourceFile:  filePath,
    name,
    description: desc,
    model:       (fm.model  || "").trim() || null,
    color:       (fm.color  || "").trim() || null,
    tools:       parseTools(fm.tools),
    body:        body.trimEnd() + "\n",
  };
}

function discoverAgents(sourceDir) {
  if (!fs.existsSync(sourceDir) || !fs.statSync(sourceDir).isDirectory()) {
    throw new Error(`missing source directory: ${sourceDir}`);
  }
  const files = fs.readdirSync(sourceDir)
    .filter(f => f.endsWith(".md"))
    .sort()
    .map(f => path.join(sourceDir, f));
  if (!files.length) throw new Error(`no *.md agent files found in ${sourceDir}`);
  return files;
}

function ensureUniqueNames(agents) {
  const seen = {};
  for (const agent of agents) {
    if (seen[agent.name]) {
      throw new Error(
        `duplicate agent name '${agent.name}' in ${path.basename(seen[agent.name])} and ${path.basename(agent.sourceFile)}`
      );
    }
    seen[agent.name] = agent.sourceFile;
  }
}

function ensureTargets(rawTargets) {
  const targets = rawTargets.split(",").map(t => t.trim().toLowerCase()).filter(Boolean);
  const bad = targets.filter(t => !SUPPORTED_TARGETS.includes(t));
  if (bad.length) throw new Error(`unsupported target(s): ${bad.join(", ")}`);
  if (!targets.length) throw new Error("no targets specified");
  return targets;
}

function ensureAgentFilter(rawAgents) {
  const names = rawAgents.split(",").map(name => name.trim()).filter(Boolean);
  if (names.length !== new Set(names).size) {
    throw new Error("duplicate agent name in --agents filter");
  }
  return names;
}

function selectAgents(agents, names) {
  if (!names.length) return agents;
  const requested = new Set(names);
  const available = new Set(agents.map(agent => agent.name));
  const missing = [...requested].filter(name => !available.has(name)).sort();
  if (missing.length) throw new Error(`unknown agent name(s): ${missing.join(", ")}`);
  return agents.filter(agent => requested.has(agent.name));
}

// ---------------------------------------------------------------------------
// Renderers
// ---------------------------------------------------------------------------

function yamlBlock(key, value) {
  const safe = value.replace(/\r\n/g, "\n").replace(/^\n+|\n+$/, "");
  return `${key}: >-\n  ` + safe.split("\n").join("\n  ");
}

function renderClaude(agent) {
  const lines = [
    "---",
    `name: ${agent.name}`,
    yamlBlock("description", agent.description),
  ];
  if (agent.tools.length) lines.push(`tools: ${agent.tools.join(", ")}`);
  if (agent.model)        lines.push(`model: ${agent.model}`);
  if (agent.color)        lines.push(`color: ${agent.color}`);
  lines.push("---", "", agent.body.trimEnd(), "");
  return lines.join("\n");
}

function renderCopilot(agent) {
  // Compatibility-safe: keep persona + instructions; omit tool mapping
  // (Copilot tool IDs differ by version and would break registration if wrong).
  return [
    "---",
    `name: ${agent.name}`,
    yamlBlock("description", agent.description),
    "---",
    "",
    agent.body.trimEnd(),
    "",
  ].join("\n");
}

function tomlEscape(value) {
  // Escape triple-double-quotes inside TOML multiline strings.
  return value.replace(/"""/g, '\\"\\"\\"');
}

function renderCodex(agent) {
  // Required fields per Codex custom agent TOML schema.
  const escapedDesc = agent.description.replace(/"/g, '\\"');
  return (
    `name = "${agent.name}"\n` +
    `description = "${escapedDesc}"\n` +
    `developer_instructions = """\n` +
    `${tomlEscape(agent.body.trimEnd())}\n` +
    `"""\n`
  );
}

function renderCursor(agent) {
  // Experimental best-effort projection.
  return [
    "---",
    `name: ${agent.name}`,
    yamlBlock("description", agent.description),
    "---",
    "",
    agent.body.trimEnd(),
    "",
  ].join("\n");
}

function renderGeneric(agent) {
  return [
    "---",
    `name: ${agent.name}`,
    yamlBlock("description", agent.description),
    "---",
    "",
    agent.body.trimEnd(),
    "",
  ].join("\n");
}

// ---------------------------------------------------------------------------
// File writer
// ---------------------------------------------------------------------------

function writeFile(filePath, content, dryRun) {
  if (dryRun) return;
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, content, { encoding: "utf8" });
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function main() {
  const args = parseArgs(process.argv);

  try {
    const targets     = ensureTargets(args.targets);
    const agentFilter = ensureAgentFilter(args.agents);
    const sourceDir   = path.resolve(args.source);
    const projectRoot = path.resolve(args.projectRoot);

    const sourceFiles      = discoverAgents(sourceDir);
    const discoveredAgents = sourceFiles.map(loadAgent);
    ensureUniqueNames(discoveredAgents);
    const agents = selectAgents(discoveredAgents, agentFilter);

    const generated = [];

    for (const agent of agents) {
      if (targets.includes("claude")) {
        const out = path.join(projectRoot, ".claude", "agents", `${agent.name}.md`);
        writeFile(out, renderClaude(agent), args.dryRun);
        generated.push({ target: "claude", source: agent.sourceFile, output: out });
      }
      if (targets.includes("copilot")) {
        const out = path.join(projectRoot, ".github", "agents", `${agent.name}.agent.md`);
        writeFile(out, renderCopilot(agent), args.dryRun);
        generated.push({ target: "copilot", source: agent.sourceFile, output: out });
      }
      if (targets.includes("codex")) {
        const out = path.join(projectRoot, ".codex", "agents", `${agent.name}.toml`);
        writeFile(out, renderCodex(agent), args.dryRun);
        generated.push({ target: "codex", source: agent.sourceFile, output: out });
      }
      if (targets.includes("cursor")) {
        const out = path.join(projectRoot, ".cursor", "agents", `${agent.name}.md`);
        writeFile(out, renderCursor(agent), args.dryRun);
        generated.push({ target: "cursor", source: agent.sourceFile, output: out });
      }
      if (targets.includes("generic")) {
        const out = path.join(projectRoot, ".agents", `${agent.name}.md`);
        writeFile(out, renderGeneric(agent), args.dryRun);
        generated.push({ target: "generic", source: agent.sourceFile, output: out });
      }
    }

    const summary = {
      ok:             true,
      dry_run:        args.dryRun,
      source_dir:     sourceDir,
      project_root:   projectRoot,
      targets,
      discovered_agent_count: discoveredAgents.length,
      agent_filter:   agentFilter,
      agent_count:    agents.length,
      generated_count: generated.length,
      generated,
      notes: [
        "Claude projection preserves tools/model/color.",
        "Copilot projection uses compatibility-safe frontmatter without explicit tool mapping.",
        "Codex projection emits required TOML fields: name, description, developer_instructions.",
        "Cursor projection is best-effort and should be validated against installed Cursor version.",
        "Generic Markdown is for manual import or future adapters; automatic discovery is not implied.",
      ],
    };

    if (args.asJson) {
      console.log(JSON.stringify(summary, null, 2));
    } else {
      const mode = args.dryRun ? "DRY-RUN" : "WROTE";
      console.log(`${mode}: ${generated.length} projection file(s) from ${agents.length} canonical agent(s).`);
      for (const item of generated) {
        console.log(`  - [${item.target}] ${item.output}`);
      }
    }

    process.exit(0);

  } catch (err) {
    const payload = { ok: false, error: err.message };
    if (args.asJson) {
      console.log(JSON.stringify(payload, null, 2));
    } else {
      console.error(`ERROR: ${err.message}`);
    }
    process.exit(1);
  }
}

main();
