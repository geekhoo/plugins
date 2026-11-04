#!/usr/bin/env node
// scrub-secrets.mjs: redact secrets in place in a run's stored files (transcripts, stream, stderr, subagents,
// exported observations) before they are hashed, uploaded or committed.
//
//   node scrub-secrets.mjs <dir-or-file>... [--report <file.json>]
//
// Secrets come from the environment (see secret-rules.mjs), never argv. Binary files are skipped. Prints a
// JSON summary (file and per-rule counts, never values) to stdout or to --report. Exit 0 unless an argument
// path does not exist (2).
import { readFileSync, writeFileSync, statSync, readdirSync, existsSync } from "node:fs";
import { pathToFileURL } from "node:url";
import { join } from "node:path";
import { allRules, scrubText, isBinary } from "./secret-rules.mjs";

export function* walk(p) {
  const st = statSync(p);
  if (st.isFile()) { yield p; return; }
  if (!st.isDirectory()) return;
  for (const e of readdirSync(p, { withFileTypes: true })) {
    if (e.name === ".git") continue;
    yield* walk(join(p, e.name));
  }
}

export function scrubPaths(paths, rules = allRules()) {
  const summary = { files_scanned: 0, files_changed: 0, binary_skipped: 0, counts: {}, files: [] };
  for (const root of paths) {
    for (const f of walk(root)) {
      const buf = readFileSync(f);
      if (isBinary(buf)) { summary.binary_skipped++; continue; }
      summary.files_scanned++;
      const { text, counts } = scrubText(buf.toString("utf8"), rules);
      const n = Object.values(counts).reduce((a, b) => a + b, 0);
      if (!n) continue;
      writeFileSync(f, text);
      summary.files_changed++;
      summary.files.push({ file: f, redactions: n });
      for (const [k, v] of Object.entries(counts)) summary.counts[k] = (summary.counts[k] || 0) + v;
    }
  }
  return summary;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const args = process.argv.slice(2);
  let report = null;
  const paths = [];
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--report") report = args[++i];
    else paths.push(args[i]);
  }
  if (!paths.length) { console.error("usage: scrub-secrets.mjs <dir-or-file>... [--report file.json]"); process.exit(2); }
  const missing = paths.filter((p) => !existsSync(p));
  if (missing.length) { console.error(`scrub-secrets: not found: ${missing.join(", ")}`); process.exit(2); }
  const out = JSON.stringify(scrubPaths(paths), null, 2) + "\n";
  if (report) writeFileSync(report, out); else process.stdout.write(out);
}
