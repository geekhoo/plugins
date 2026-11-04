// secret-rules.mjs: shared secret detection for scrub-secrets.mjs and secret-scan.mjs.
//
// Two sources of secrets:
//   1. literal values of secret-named variables in the current environment (the run's own keys), plus the
//      Basic-auth value derived from the Langfuse key pair;
//   2. generic shapes (Langfuse/Anthropic/OpenAI-style keys, Authorization headers, NAME=value lines from an
//      env dump) that catch keys which never were in this process's environment.
// Values are only ever read from the environment or files, never from argv: on hosts that log process
// arguments (endpoint agents such as Santa) argv is itself a leak.
import { readFileSync, existsSync } from "node:fs";

const SECRET_NAME = /(^|_)(KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIALS?|AUTHORIZATION|HEADERS|COOKIE)(_|$)/i;
const NOT_SECRET_NAME = /(_FILE|_PATH|_DIR|_URL|_HOST|_PORT|_ID|_LIMIT|_MAX|_COUNT|_HELPER|_TYPE|_MODE|_VERSION)$/i;
const MIN_LEN = 12;

const jsonEscaped = (s) => JSON.stringify(s).slice(1, -1);
const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

/** Secret values from an environment object: [{ name, value }], longest first, de-duplicated. */
export function envSecrets(env = process.env) {
  const out = new Map();
  const add = (name, value) => {
    if (typeof value !== "string") return;
    const v = value.trim();
    if (v.length < MIN_LEN || v.startsWith("/") || /^\d+$/.test(v) || /^(true|false)$/i.test(v)) return;
    if (!out.has(v)) out.set(v, name);
  };
  for (const [name, value] of Object.entries(env)) {
    if (SECRET_NAME.test(name) && !NOT_SECRET_NAME.test(name)) add(name, value);
  }
  if (env.LANGFUSE_PUBLIC_KEY && env.LANGFUSE_SECRET_KEY) {
    add("LANGFUSE_BASIC_AUTH", Buffer.from(`${env.LANGFUSE_PUBLIC_KEY}:${env.LANGFUSE_SECRET_KEY}`).toString("base64"));
  }
  return [...out].map(([value, name]) => ({ name, value })).sort((a, b) => b.value.length - a.value.length);
}

const lines = (file) => readFileSync(file, "utf8").split("\n").map((l) => l.trim()).filter((l) => l && !l.startsWith("#"));

/** Extra literal deny patterns (internal host or org names) from the file named by GEEKY_SECRET_DENYLIST. */
export function denyPatterns(env = process.env) {
  return env.GEEKY_SECRET_DENYLIST ? lines(env.GEEKY_SECRET_DENYLIST) : [];
}

/** Known non-secrets that look like secrets (fixture tokens a case app issues in its own tests): regexes,
 *  one per line, matched against the whole hit, from secret-allow.txt next to this file and the file named
 *  by GEEKY_SECRET_ALLOWLIST. They apply to generic shapes only; a literal environment value is never allowed. */
export function allowPatterns(env = process.env) {
  const files = [new URL("./secret-allow.txt", import.meta.url).pathname, env.GEEKY_SECRET_ALLOWLIST];
  return files.filter((f) => f && existsSync(f)).flatMap(lines).map((l) => new RegExp("^(?:" + l + ")$"));
}

// A secret-looking value ends at whitespace, a quote, a backslash (JSON escape), a comma/semicolon or end…
const END = String.raw`(?=[\s"'\\,;]|$)`;
// …and starts at a non-word character or right after a JSON escape: in a JSON string an env dump reads
// "…\nANTHROPIC_AUTH_TOKEN=…", where \b would fail because of the "n".
const START = String.raw`(?<=^|\\[nrt]|[^A-Za-z0-9_])`;
const rx = (body, flags = "g") => new RegExp(START + body, flags);
export const GENERIC_RULES = [
  { rule: "langfuse-key", re: rx(String.raw`(?:sk|pk)-lf-[0-9a-f][0-9a-f-]{20,}`), rep: "<redacted:langfuse-key>" },
  { rule: "anthropic-key", re: rx(String.raw`sk-ant-[A-Za-z0-9_-]{20,}`), rep: "<redacted:anthropic-key>" },
  { rule: "api-key", re: rx(String.raw`sk-(?:proj-)?[A-Za-z0-9_]{20,}`), rep: "<redacted:api-key>" },
  { rule: "auth-header", re: /(Authorization["']?\s*[=:]\s*["']?(?:Basic|Bearer)\s+)[A-Za-z0-9+/=._-]{16,}/gi, rep: "$1<redacted>" },
  { rule: "env-assignment",
    re: rx(String.raw`([A-Z][A-Z0-9_]*(?:TOKEN|SECRET|_KEY|PASSWORD|PASSWD|CREDENTIALS?)=)(?!<redacted)[A-Za-z0-9_\-.+/=:]{16,}` + END),
    rep: "$1<redacted>" },
];

/** Literal rules for the given secrets (raw and JSON-escaped forms) and deny patterns. */
export function literalRules(secrets, deny = []) {
  const rules = [];
  for (const { name, value } of secrets) {
    const forms = new Set([value, jsonEscaped(value)]);
    for (const f of forms) rules.push({ rule: `env:${name}`, re: new RegExp(esc(f), "g"), rep: `<redacted:${name}>` });
  }
  for (const d of deny) rules.push({ rule: "denylist", re: new RegExp(esc(d), "gi"), rep: "<redacted:name>" });
  return rules;
}

/** All rules: literal values first (most specific), then generic shapes with the allowlist attached. */
export function allRules(env = process.env) {
  const allow = allowPatterns(env);
  return [...literalRules(envSecrets(env), denyPatterns(env)), ...GENERIC_RULES.map((r) => ({ ...r, allow }))];
}

const allowed = (rule, hit) => !!rule.allow?.some((a) => a.test(hit));

/** Replace every match; returns { text, counts: { rule: n } }. Never returns matched values. */
export function scrubText(text, rules) {
  const counts = {};
  for (const r of rules) {
    r.re.lastIndex = 0;
    text = text.replace(r.re, (...m) => {
      if (allowed(r, m[0])) return m[0];
      counts[r.rule] = (counts[r.rule] || 0) + 1;
      return r.rep.replace(/\$(\d)/g, (_, i) => m[Number(i)] ?? "");
    });
  }
  return { text, counts };
}

/** Rule names that match a line (allowlisted hits excluded), without values. */
export function findInText(text, rules) {
  const hits = [];
  for (const r of rules) {
    r.re.lastIndex = 0;
    for (const m of text.matchAll(r.re)) if (!allowed(r, m[0])) { hits.push(r.rule); break; }
  }
  return hits;
}

/** True when the buffer looks binary (NUL in the first 8 KiB). */
export const isBinary = (buf) => buf.subarray(0, 8192).includes(0);
