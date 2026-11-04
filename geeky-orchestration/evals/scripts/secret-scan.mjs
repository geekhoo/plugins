#!/usr/bin/env node
// secret-scan.mjs: fail when files or git history contain a secret. Run it before every commit or push of
// eval records, and over the whole branch before publishing.
//
//   node secret-scan.mjs <dir-or-file>...      scan files (text only)
//   node secret-scan.mjs --git <range>         scan added lines and messages of the commits in <range>
//   node secret-scan.mjs --staged              scan the staged diff
//
// Secrets: the environment's secret-named values, generic key shapes, and literal names listed in the file
// named by GEEKY_SECRET_DENYLIST (keep internal host/org names there, outside the repo). Values are never
// printed: each hit is reported as location + rule name. Exit 0 clean, 1 hits found, 2 usage error.
import { execFileSync } from "node:child_process";
import { pathToFileURL } from "node:url";
import { readFileSync, existsSync } from "node:fs";
import { allRules, findInText, isBinary } from "./secret-rules.mjs";
import { walk } from "./scrub-secrets.mjs";

export function scanFiles(paths, rules = allRules()) {
  const hits = [];
  for (const root of paths) {
    for (const f of walk(root)) {
      const buf = readFileSync(f);
      if (isBinary(buf)) continue;
      buf.toString("utf8").split("\n").forEach((line, i) => {
        for (const rule of findInText(line, rules)) hits.push({ where: `${f}:${i + 1}`, rule });
      });
    }
  }
  return hits;
}

/** Scan unified-diff text with `commit <sha>` markers; only added lines and commit messages count. */
export function scanPatch(patch, rules = allRules()) {
  const hits = [];
  let commit = "staged", file = null, inMsg = false;
  for (const line of patch.split("\n")) {
    if (line.startsWith("\u0001commit ")) { commit = line.slice(8, 20); file = null; inMsg = true; continue; }
    if (line.startsWith("diff --git ")) { inMsg = false; continue; }
    if (line.startsWith("+++ ")) { file = line.slice(4).replace(/^b\//, ""); continue; }
    const added = !inMsg && line.startsWith("+");
    if (!inMsg && !added) continue;
    for (const rule of findInText(added ? line.slice(1) : line, rules))
      hits.push({ where: inMsg ? `${commit} (message)` : `${commit} ${file}`, rule });
  }
  return hits;
}

const git = (args) => execFileSync("git", args, { maxBuffer: 2 ** 31 }).toString("utf8");

function main() {
  const args = process.argv.slice(2);
  let hits;
  if (args[0] === "--git" && args[1]) hits = scanPatch(git(["log", "-p", "--no-color", "--format=%x01commit %H%n%B", args[1]]));
  else if (args[0] === "--staged") hits = scanPatch(git(["diff", "--cached", "--no-color"]));
  else if (args.length && args.every((a) => !a.startsWith("--"))) {
    const missing = args.filter((p) => !existsSync(p));
    if (missing.length) { console.error(`secret-scan: not found: ${missing.join(", ")}`); process.exit(2); }
    hits = scanFiles(args);
  } else { console.error("usage: secret-scan.mjs <path>... | --git <range> | --staged"); process.exit(2); }
  const uniq = [...new Map(hits.map((h) => [`${h.where} ${h.rule}`, h])).values()];
  for (const h of uniq) console.log(`${h.where}  ${h.rule}`);
  console.error(`secret-scan: ${uniq.length} hit(s)`);
  process.exit(uniq.length ? 1 : 0);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  // exit 2 on any error, so a crash never reads as "hits found" (1) or "clean" (0)
  try { main(); } catch (e) { console.error(`secret-scan: error: ${e.message}`); process.exit(2); }
}
