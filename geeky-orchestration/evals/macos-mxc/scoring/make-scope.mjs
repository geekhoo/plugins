#!/usr/bin/env node
// make-scope.mjs: build the publish-run copy of run.json (adds .telemetry identity only) and the
// geeky-eval.inputs/1 evaluation scope for one MXC C2 run, in the shape of the r2 analysis
// (evals/analyses/c0-macos-mxc-sonnet-20261030/claude-code/evaluation-inputs.json).
//
//   node make-scope.mjs --run <baselines/case/stamp> --out <analysis dir> --scope-id <id> \
//     --env mxc-claude-mac --desc "<description>"
// Needs in <out>: langfuse-observations.json, harness-coverage.json, manual-verdicts.json, score.json.
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { join, basename, resolve } from "node:path";

const argv = process.argv.slice(2);
const flag = (name) => { const i = argv.indexOf(name); if (i < 0 || !argv[i + 1]) throw new Error(`missing ${name}`); return argv[i + 1]; };
const run = resolve(flag("--run")), out = resolve(flag("--out")), scopeId = flag("--scope-id"), env = flag("--env"), desc = flag("--desc");
const sha = (p) => createHash("sha256").update(readFileSync(p)).digest("hex");
const json = (p) => JSON.parse(readFileSync(p, "utf8"));
for (const f of ["langfuse-observations.json", "harness-coverage.json", "manual-verdicts.json", "score.json"])
  if (!existsSync(join(out, f))) throw new Error(`missing ${join(out, f)}`);

const runJson = json(join(run, "run.json"));
const cov = json(join(out, "harness-coverage.json"));
const obs = json(join(out, "langfuse-observations.json"));
const sid = runJson.native_otel?.session_attribute ?? runJson.native_session_id ?? runJson.session_id;
if (!sid) throw new Error("no session id in run.json");

// 1. publish-run copy: identical to run.json except .telemetry, so langfuse-scores.py targets the right env/session.
const stamp = basename(run);
const pubDir = join(out, "publish-run", stamp);
mkdirSync(pubDir, { recursive: true });
const pub = { ...runJson, telemetry: {
  enabled: false,
  source: "native OTel spans + post-run transcript upload (run.json native_otel); upstream hook disabled (-NoTelemetry)",
  derived_by: "source-reviewed copy for langfuse-scores.py: run.json + harness-coverage.json",
  session_id: sid, agent_family: "claude-code", environment: env, delivered: true,
  observations: Array.isArray(obs) ? obs.length : null, coverage_complete: Boolean(cov.complete) } };
const pubPath = join(pubDir, "run.json");
writeFileSync(pubPath, JSON.stringify(pub, null, 2) + "\n");

// 2. evaluation scope, every input bound by path + sha256 + ancestry.
const src = (id, path, ancestry = []) => ({ id, path, sha256: sha(path), ancestry });
const sources = [
  src("run", join(run, "run.json")),
  src("session", join(run, "session.jsonl")),
  src("stream", join(run, "stream.jsonl")),
  src("transcript-upload", join(run, "telemetry/upload.json"), ["session"]),
  src("observations-export", join(run, "telemetry/observations.json"), ["transcript-upload"]),
  src("observations", join(out, "langfuse-observations.json"), ["observations-export"]),
  src("harness-coverage", join(out, "harness-coverage.json"), ["observations"]),
  src("manual-verdicts", join(out, "manual-verdicts.json"), ["session", "stream"]),
  src("score", join(out, "score.json"), ["run", "session", "stream", "manual-verdicts"]),
  src("publish-run", pubPath, ["run", "harness-coverage"]),
];
const ex = runJson.execution ?? {};
const iso6 = (t) => t.replace(/(\.\d{6})\d*Z$/, "$1Z");
const inv = ex.invocations ?? [];
if (inv.length !== 1) throw new Error(`expected one invocation (zero recoveries), got ${inv.length}`);
const nSub = existsSync(join(run, "subagents")) ? readFileSync(join(run, "telemetry/upload.json"), "utf8") && json(join(run, "telemetry/upload.json")).counts?.subagents : null;
const scope = {
  schema: "geeky-eval.inputs/1", scope_id: scopeId, kind: "initial", parent_scope_id: null, description: desc,
  configuration: { prompt_sha256: runJson.prompt_sha256, plugin_sha: runJson.plugin_sha },
  sources,
  segments: [{ segment_id: ex.segment_id, attempt_id: ex.attempt_id, authorization_reference: ex.authorization_reference,
    start: iso6(inv[0].started_utc), end: iso6(inv[0].ended_utc) }],
  ownership: { method: "native", rule: "single initial segment: every captured row, observation and artifact belongs to this attempt (zero recoveries)" },
  metric_default: { scope_id: scopeId, population: `segment ${String(ex.segment_id).slice(0, 8)}: main session + ${nSub ?? "?"} subagents, one attempt`,
    source_ids: ["run", "session"], additive: false, complete: true },
  metrics: {
    coverage: { source_ids: ["harness-coverage"], population: `langfuse-coverage.py harness points over the ${Array.isArray(obs) ? obs.length : "?"} uploaded observations` },
    cost: { complete: false, population: "analyze-run list-price estimate; gateway billing not observed" },
    backend: { source_ids: ["run"], population: `LiteLLM gateway (${runJson.model ?? ex.configuration?.model}) via a local TLS proxy` },
  },
};
const scopePath = join(out, "evaluation-inputs.json");
writeFileSync(scopePath, JSON.stringify(scope, null, 2) + "\n");
console.log(JSON.stringify({ publish_run: pubPath, scope: scopePath, session_id: sid, environment: env, sources: sources.length }));
