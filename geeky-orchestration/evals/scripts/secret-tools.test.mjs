// Tests for secret-rules / scrub-secrets / secret-scan.   node --test secret-tools.test.mjs
// Fake secrets are assembled at runtime so this file never matches the scanner itself.
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync, readFileSync, mkdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync, spawnSync } from "node:child_process";
import { envSecrets, allRules, scrubText, findInText, GENERIC_RULES } from "./secret-rules.mjs";
import { scrubPaths } from "./scrub-secrets.mjs";
import { scanFiles, scanPatch } from "./secret-scan.mjs";

const HERE = new URL(".", import.meta.url).pathname;
const fake = (prefix, n = 32) => prefix + "a1B2c3D4e5".repeat(Math.ceil(n / 10)).slice(0, n);
const GW = fake("sk-", 22);
const LF_SK = "sk-" + "lf-" + "0123abcd-4567-89ef-0123-456789abcdef";
const LF_PK = "pk-" + "lf-" + "fedcba98-7654-3210-fedc-ba9876543210";
const ENV = { ANTHROPIC_AUTH_TOKEN: GW, LANGFUSE_SECRET_KEY: LF_SK, LANGFUSE_PUBLIC_KEY: LF_PK,
  CLAUDE_CODE_MAX_OUTPUT_TOKENS: "32000", LANGFUSE_BASE_URL: "https://lf.example.test", HOME: "/Users/someone",
  GIT_TOKEN_FILE: "/tmp/token-file-path-not-a-secret", SHORT_KEY: "abc" };

test("envSecrets picks secret-named values and the derived Basic auth, skips non-secrets", () => {
  const names = envSecrets(ENV).map((s) => s.name).sort();
  assert.deepEqual(names, ["ANTHROPIC_AUTH_TOKEN", "LANGFUSE_BASIC_AUTH", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"]);
});

test("printenv dump in a JSONL transcript is fully redacted and stays valid JSON", () => {
  const dump = `ANTHROPIC_AUTH_TOKEN=${GW}\nCLAUDE_CODE_MESSAGING_TOKEN=${fake("m", 40)}\nOTHER_SECRET=${fake("Zz", 24)}\nPATH=/usr/bin`;
  const line = JSON.stringify({ type: "tool_result", content: dump });
  const { text, counts } = scrubText(line, allRules(ENV));
  assert.ok(!text.includes(GW));
  assert.ok(!text.includes(fake("m", 40)));
  assert.ok(!text.includes(fake("Zz", 24)));
  assert.ok(text.includes("PATH=/usr/bin"));
  assert.ok(counts["env:ANTHROPIC_AUTH_TOKEN"] >= 1 && counts["env-assignment"] >= 2);
  assert.doesNotThrow(() => JSON.parse(text));
});

test("Authorization headers and the base64 Langfuse pair are redacted", () => {
  const basic = Buffer.from(`${LF_PK}:${LF_SK}`).toString("base64");
  const { text } = scrubText(`OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic ${basic},x-v=4 / "Authorization": "Bearer ${GW}"`, allRules(ENV));
  assert.ok(!text.includes(basic) && !text.includes(GW));
});

test("generic shapes catch keys that were never in the environment", () => {
  const foreign = "sk-" + "lf-" + "99999999-aaaa-bbbb-cccc-dddddddddddd";
  const { text } = scrubText(`key ${foreign} and ${fake("sk-ant-", 30)}`, GENERIC_RULES);
  assert.ok(!text.includes(foreign) && !text.includes(fake("sk-ant-", 30)));
});

test("ordinary code and numbers are left alone", () => {
  const src = 'API_KEY=os.environ.get("API_KEY")\nMAX_TOKENS=4096\nconst task_key = "T3";\nSECRET_KEY=short';
  assert.equal(scrubText(src, GENERIC_RULES).text, src);
});

test("scrub is idempotent", () => {
  const rules = allRules(ENV);
  const once = scrubText(`X_TOKEN=${fake("q", 30)} ${GW}`, rules).text;
  assert.equal(scrubText(once, rules).text, once);
  assert.deepEqual(findInText(once, rules), []);
});

test("JSON-escaped secret forms are matched", () => {
  const odd = 'p@ss"word/with\\slash-long-enough';
  const rules = allRules({ DB_PASSWORD: odd });
  const { text } = scrubText(JSON.stringify({ v: odd }), rules);
  assert.ok(!text.includes(JSON.stringify(odd).slice(1, -1)));
});

test("denylist names are redacted case-insensitively", () => {
  const dir = mkdtempSync(join(tmpdir(), "st-"));
  try {
    writeFileSync(join(dir, "deny"), "# internal\nacmecorp\n");
    const { text } = scrubText("host gw.AcmeCorp.internal", allRules({ GEEKY_SECRET_DENYLIST: join(dir, "deny") }));
    assert.equal(text, "host gw.<redacted:name>.internal");
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test("scrubPaths rewrites text files in a run tree, skips binaries, reports no values", () => {
  const dir = mkdtempSync(join(tmpdir(), "st-"));
  try {
    mkdirSync(join(dir, "subagents"));
    writeFileSync(join(dir, "session.jsonl"), JSON.stringify({ out: `ANTHROPIC_AUTH_TOKEN=${GW}` }) + "\n");
    writeFileSync(join(dir, "subagents", "a.jsonl"), JSON.stringify({ k: LF_SK }) + "\n");
    writeFileSync(join(dir, "solution.bundle"), Buffer.concat([Buffer.from([0, 1, 2]), Buffer.from(GW)]));
    const s = scrubPaths([dir], allRules(ENV));
    assert.equal(s.files_changed, 2);
    assert.equal(s.binary_skipped, 1);
    assert.ok(!JSON.stringify(s).includes(GW));
    assert.ok(!readFileSync(join(dir, "session.jsonl"), "utf8").includes(GW));
    assert.deepEqual(scanFiles([dir], allRules(ENV)), []);
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test("scanPatch reports added lines and messages, ignores removed lines", () => {
  const patch = [
    "\u0001commit 0123456789abcdef0123", `msg mentions ${GW}`, "",
    "diff --git a/f.txt b/f.txt", "--- a/f.txt", "+++ b/f.txt",
    `-old ${LF_SK}`, `+new ${GW}`, " context",
  ].join("\n");
  const hits = scanPatch(patch, allRules(ENV));
  assert.deepEqual([...new Set(hits.map((h) => h.where))], ["0123456789ab (message)", "0123456789ab f.txt"]);
  assert.ok(!JSON.stringify(hits).includes(GW));
});

test("CLI: secret-scan exits 1 on a hit without printing the value; scrub then makes it exit 0", () => {
  const dir = mkdtempSync(join(tmpdir(), "st-"));
  try {
    writeFileSync(join(dir, "stderr.txt"), `ANTHROPIC_AUTH_TOKEN=${GW}\n`);
    const env = { ...process.env, ...ENV };
    const scan = spawnSync(process.execPath, [join(HERE, "secret-scan.mjs"), dir], { env, encoding: "utf8" });
    assert.equal(scan.status, 1);
    assert.ok(!scan.stdout.includes(GW) && !scan.stderr.includes(GW));
    execFileSync(process.execPath, [join(HERE, "scrub-secrets.mjs"), dir, "--report", join(tmpdir(), "st-report.json")], { env });
    const again = spawnSync(process.execPath, [join(HERE, "secret-scan.mjs"), dir], { env, encoding: "utf8" });
    assert.equal(again.status, 0, again.stdout);
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test("allowlist: case-app fixture tokens pass, other bearer values and literal env secrets do not", () => {
  const lv = "lv_" + "0123456789abcdef".repeat(2);
  const rules = allRules({});
  assert.deepEqual(findInText(`Authorization: Bearer ${lv}`, rules), []);
  assert.equal(scrubText(`Authorization: Bearer ${lv}`, rules).text, `Authorization: Bearer ${lv}`);
  assert.deepEqual(findInText(`Authorization: Bearer ${fake("zz", 30)}`, rules), ["auth-header"]);
  // the same value, once it is an environment secret, is redacted regardless of the allowlist
  const envRules = allRules({ APP_TOKEN: lv });
  assert.ok(!scrubText(`Authorization: Bearer ${lv}`, envRules).text.includes(lv));
});

test("extra allowlist file from GEEKY_SECRET_ALLOWLIST", () => {
  const dir = mkdtempSync(join(tmpdir(), "st-"));
  try {
    const v = fake("sk-", 24);
    writeFileSync(join(dir, "allow"), "# fixture\nsk-a1B2[A-Za-z0-9]+\n");
    assert.deepEqual(findInText(`key ${v}`, allRules({ GEEKY_SECRET_ALLOWLIST: join(dir, "allow") })), []);
    assert.deepEqual(findInText(`key ${v}`, allRules({})), ["api-key"]);
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test("CLI: --git and --staged scan a real repository; a git error exits 2, not 1", () => {
  const dir = mkdtempSync(join(tmpdir(), "st-git-"));
  try {
    const g = (...a) => execFileSync("git", ["-C", dir, "-c", "user.name=t", "-c", "user.email=t@t", ...a], { stdio: "pipe" });
    g("init", "-q");
    writeFileSync(join(dir, "a.txt"), "clean\n"); g("add", "."); g("commit", "-qm", "base");
    writeFileSync(join(dir, "a.txt"), `clean\nANTHROPIC_AUTH_TOKEN=${GW}\n`); g("add", ".");
    const env = { ...process.env, ...ENV };
    const cli = (...a) => spawnSync(process.execPath, [join(HERE, "secret-scan.mjs"), ...a], { cwd: dir, env, encoding: "utf8" });
    const staged = cli("--staged");
    assert.equal(staged.status, 1, staged.stderr);
    assert.match(staged.stdout, /staged a\.txt/);
    g("commit", "-qm", "leak");
    const range = cli("--git", "HEAD~1..HEAD");
    assert.equal(range.status, 1, range.stderr);
    assert.match(range.stdout, /a\.txt\s+env:ANTHROPIC_AUTH_TOKEN/);
    assert.ok(!range.stdout.includes(GW) && !range.stderr.includes(GW));
    assert.equal(cli("--git", "HEAD~1").status, 0);                 // history up to the base commit is clean
    assert.equal(cli("--git", "no-such-ref..HEAD").status, 2);     // git fails: error, not a verdict
  } finally { rmSync(dir, { recursive: true, force: true }); }
});
