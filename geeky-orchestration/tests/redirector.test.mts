// hooks/py-run.sh: run Python when it works, else the Node twin.
//
// Every case runs against stub interpreters placed first on PATH (healthy,
// hanging, killed, missing), so no test ever starts a real Python.

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { chmodSync, existsSync, mkdirSync, mkdtempSync, readFileSync, utimesSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { capture, serialize, BASELINE } from "../mcp/wire-baseline.mts";
import { ROOT } from "./helpers.mts";

const REDIRECTOR = join(ROOT, "hooks", "py-run.sh");
const GUARD_PY = join(ROOT, "hooks", "guard-planning-contract.py");
const FROZEN = JSON.stringify({ tool_name: "Edit", tool_input: { file_path: "/r/tasks/T1-a.md" } });

type Behaviour = "healthy" | "slow" | "hangs" | "forks" | "killed" | "missing" | "no-mcp";

/** A sandbox: stub bin dir first on PATH, a private cache dir, and a call log. */
function sandbox(stubs: Partial<Record<"python3" | "python" | "py" | "uv", Behaviour>>) {
  const root = mkdtempSync(join(tmpdir(), "geekyredirect"));
  const bin = join(root, "bin");
  const data = join(root, "data");
  const log = join(root, "calls.log");
  // unique per sandbox, so a leftover from another run is never mistaken for ours
  const marker = `43.${Math.floor(Math.random() * 9000) + 1000}`;
  mkdirSync(bin);
  for (const name of ["python3", "python", "py", "uv"] as const) {
    const behaviour = stubs[name] ?? "missing";
    const body = {
      // a probe ("-c ...") passes; a real run reports what it was asked to run
      healthy: `[ "$1" = "-c" ] && exit 0\ncase " $* " in *" -c "*) exit 0 ;; esac\necho "${name.toUpperCase()}-RAN $*"`,
      // can start, but cannot import the requested package
      "no-mcp": `case "$*" in *mcp*) exit 1 ;; esac\n[ "$1" = "-c" ] && exit 0\necho "${name.toUpperCase()}-RAN $*"`,
      // healthy, but only after the probe's watcher is surely asleep
      slow: `sleep 0.3\n[ "$1" = "-c" ] && exit 0\necho "${name.toUpperCase()}-RAN $*"`,
      hangs: "exec sleep 30",
      // hangs with a child, as `uv run` does with the interpreter it starts
      forks: `sleep ${marker} &\nwait`,
      killed: "kill -9 $$",
      missing: "exit 127",
    }[behaviour];
    writeFileSync(join(bin, name), `#!/bin/bash\necho "${name} [$PWD] $*" >> "${log}"\n${body}\n`);
    chmodSync(join(bin, name), 0o755);
  }
  const env = {
    HOME: root,
    PATH: [bin, dirname(process.execPath), "/usr/bin", "/bin"].join(":"),
    CLAUDE_PLUGIN_DATA: data,
    GEEKY_PY_PROBE_TIMEOUT: "1",
    GEEKY_UV_PROBE_TIMEOUT: "1",
  };
  const run = (args: string[], input = "", extraEnv: Record<string, string> = {}) => {
    const started = Date.now();
    const res = spawnSync("bash", [REDIRECTOR, ...args], { input, encoding: "utf8", env: { ...env, ...extraEnv } });
    return { status: res.status, stdout: res.stdout, stderr: res.stderr, ms: Date.now() - started };
  };
  const calls = () => (existsSync(log) ? readFileSync(log, "utf8").trim().split("\n").filter(Boolean) : []);
  const cached = (key = "python") => readFileSync(join(data, `runtime-${key}`), "utf8").trim();
  return { root, data, env, run, calls, cached, marker };
}

test("a healthy Python runs the .py, exactly as before", () => {
  const s = sandbox({ python3: "healthy" });
  const res = s.run([GUARD_PY, "--mode", "warn"], FROZEN);
  assert.equal(res.status, 0);
  assert.equal(res.stdout, `PYTHON3-RAN ${GUARD_PY} --mode warn\n`);
  assert.equal(s.cached(), "python:python3");
});

test("a probe that answers promptly does not pay the timeout", () => {
  // The timeout is a ceiling, not a cost: the watcher is cancelled as soon as
  // the probe exits, even when it exits after the watcher started sleeping.
  const s = sandbox({ python3: "slow" });
  const res = s.run([GUARD_PY], "", { GEEKY_PY_PROBE_TIMEOUT: "8" });
  assert.match(res.stdout, /^PYTHON3-RAN /);
  assert.ok(res.ms < 3000, `probe of a healthy Python took ${res.ms} ms with an 8 s timeout`);
});

test("probe order is python3, python, then py -3", () => {
  const s = sandbox({ python3: "killed", python: "missing", py: "healthy" });
  const res = s.run([GUARD_PY]);
  assert.equal(res.stdout, `PY-RAN -3 ${GUARD_PY}\n`);
  assert.equal(s.cached(), "python:py -3");
});

for (const behaviour of ["hangs", "killed", "missing"] as const) {
  test(`a Python that ${behaviour === "missing" ? "is missing" : behaviour} falls back to the Node twin`, () => {
    const s = sandbox({ python3: behaviour, python: behaviour });
    const res = s.run([GUARD_PY, "--mode", "block", "--exit-code"], FROZEN);
    assert.equal(res.status, 2, res.stderr);
    assert.equal(res.stdout, "");
    assert.match(res.stderr, /^\[geeky-orchestration\] \/r\/tasks\/T1-a\.md is a frozen task file/);
    assert.equal(s.cached(), "node");
    if (behaviour === "hangs") assert.ok(res.ms < 4500, `two 1 s probes should cost ~2 s, took ${res.ms} ms`);
  });
}

test("the stdin payload reaches the final process, not the probes", () => {
  const s = sandbox({ python3: "missing" });
  const res = s.run([GUARD_PY, "--mode", "warn"], FROZEN);
  assert.equal(res.status, 0);
  assert.match(res.stdout, /is a frozen task file/);
  const ok = s.run([GUARD_PY, "--mode", "warn"], JSON.stringify({ tool_name: "Edit", tool_input: { file_path: "/r/src/a.ts" } }));
  assert.deepEqual([ok.status, ok.stdout, ok.stderr], [0, "", ""]);
});

test("the decision is cached: a hanging Python is probed once, then skipped", () => {
  const s = sandbox({ python3: "hangs", python: "missing" });
  s.run([GUARD_PY], FROZEN);
  const probes = s.calls().length;
  const second = s.run([GUARD_PY], FROZEN);
  assert.equal(s.calls().length, probes, "second run must not probe");
  assert.ok(second.ms < 1000, `cached run took ${second.ms} ms`);

  // an expired cache is re-probed
  const old = new Date(Date.now() - 2 * 24 * 3600 * 1000);
  utimesSync(join(s.data, "runtime-python"), old, old);
  s.run([GUARD_PY], FROZEN);
  assert.ok(s.calls().length > probes, "expired cache must re-probe");
});

test("a cached route whose interpreter disappeared is re-decided", () => {
  const s = sandbox({ python3: "missing" });
  mkdirSync(s.data, { recursive: true });
  writeFileSync(join(s.data, "runtime-python"), "python:python9\n");
  const res = s.run([GUARD_PY, "--mode", "block", "--exit-code"], FROZEN);
  assert.equal(res.status, 2);
  assert.equal(s.cached(), "node");
});

test("GEEKY_RUNTIME forces a route without probing", () => {
  const s = sandbox({ python3: "hangs" });
  const viaNode = s.run([GUARD_PY, "--mode", "block", "--exit-code"], FROZEN, { GEEKY_RUNTIME: "node" });
  assert.equal(viaNode.status, 2);
  assert.deepEqual(s.calls(), []);
  const h = sandbox({ python3: "healthy" });
  assert.equal(h.run([GUARD_PY], "", { GEEKY_RUNTIME: "python" }).stdout, `PYTHON3-RAN ${GUARD_PY}\n`);
  assert.deepEqual(h.calls(), [`python3 [${process.cwd()}] ${GUARD_PY}`], "forced python must not probe");
});

test("--uv-with: uv when its environment imports the package", () => {
  const s = sandbox({ uv: "healthy", python3: "healthy" });
  const res = s.run(["--uv-with", "mcp>=1.2.0", join(ROOT, "mcp", "server.py")]);
  assert.equal(res.stdout, `UV-RAN run --with mcp>=1.2.0 python ${join(ROOT, "mcp", "server.py")}\n`);
  assert.equal(s.cached("mcp"), "uv");
});

test("--uv-with: a plain Python is used only if it can import the package", () => {
  const withMcp = sandbox({ python3: "healthy" });
  assert.match(withMcp.run(["--uv-with", "mcp>=1.2.0", join(ROOT, "mcp", "server.py")]).stdout, /^PYTHON3-RAN /);
  const without = sandbox({ python3: "no-mcp", uv: "hangs" });
  const res = without.run(["--uv-with", "mcp>=1.2.0", join(ROOT, "mcp", "server.py")],
    JSON.stringify({ jsonrpc: "2.0", id: 1, method: "ping" }) + "\n");
  assert.equal(res.stdout, `{"jsonrpc":"2.0","id":1,"result":{}}\n`);   // the Node server answered
  assert.equal(without.cached("mcp"), "node");
});

test("no Python and no Node twin is a clear error", () => {
  const s = sandbox({});
  const lonely = join(s.root, "orphan.py");
  writeFileSync(lonely, "");
  const res = s.run([lonely]);
  assert.equal(res.status, 1);
  assert.match(res.stderr, /no working Python 3 interpreter .*\n.*no Node 22\.18\+ to run .*orphan\.mts/);
});

test("both MCP launch configs go through the redirector to server.py", () => {
  const claude = JSON.parse(readFileSync(join(ROOT, ".mcp.json"), "utf8")).mcpServers.geeky;
  assert.deepEqual([claude.command, claude.args], ["bash",
    ["${CLAUDE_PLUGIN_ROOT}/hooks/py-run.sh", "--uv-with", "mcp>=1.2.0", "${CLAUDE_PLUGIN_ROOT}/mcp/server.py"]]);
  // Mirrors test_mcp_server.py's Codex invariant: no placeholders, relative cwd,
  // and the last argument still resolves to server.py.
  const codex = JSON.parse(readFileSync(join(ROOT, ".codex-plugin", "mcp.json"), "utf8")).mcpServers.geeky;
  assert.doesNotMatch(JSON.stringify(codex), /\$\{/);
  assert.ok(!codex.cwd.startsWith("/"));
  assert.equal(join(ROOT, codex.cwd, codex.args.at(-1)), join(ROOT, "mcp", "server.py"));
  assert.ok(existsSync(join(ROOT, codex.cwd, codex.args[0])), "redirector path must resolve from cwd");
});

test("end to end: the Codex launch line with no Python serves the baseline wire transcript", async () => {
  const s = sandbox({ python3: "killed", python: "missing", uv: "missing" });
  const saved = { ...process.env };
  Object.assign(process.env, s.env);   // capture() spawns with the inherited env
  try {
    const codex = JSON.parse(readFileSync(join(ROOT, ".codex-plugin", "mcp.json"), "utf8")).mcpServers.geeky;
    const { document } = await capture([codex.command, ...codex.args]);  // capture() runs with cwd = mcp/
    const canonical = (t: string) => t.replace(/<FIXTURE>[^"\s]*/g, (p) => p.replace(/\/{2,}/g, "/"));
    assert.equal(canonical(serialize(document)), canonical(readFileSync(BASELINE, "utf8")));
  } finally {
    for (const k of Object.keys(process.env)) if (!(k in saved)) delete process.env[k];
    Object.assign(process.env, saved);
  }
});

// --- review round 3 -------------------------------------------------------- //

test("package probes ask importlib.metadata from /, so the plugin's mcp/ folder cannot fake it", () => {
  const s = sandbox({ python3: "healthy" });
  s.run(["--uv-with", "mcp>=1.2.0", join(ROOT, "mcp", "server.py")]);
  // CHECK spans several lines, so read the raw log rather than one line per call
  const log = readFileSync(join(s.root, "calls.log"), "utf8");
  const probes = log.split(/^(?=python3 \[)/m).filter((c) => c.startsWith("python3 ") && c.includes(" -c "));
  assert.equal(probes.length, 2, "a Python route needs two good probes");
  for (const p of probes) {
    assert.match(p, /^python3 \[\/\] -c /);
    assert.match(p, /importlib\.metadata/);
    assert.match(p, /version\('mcp'\)/);
    assert.match(p, /'1\.2\.0'\.split/);
  }
});

test("one good probe out of two is not enough to pick Python", () => {
  const s = sandbox({ python3: "missing" });
  const flaky = join(s.root, "bin", "python3");
  // succeeds on the first probe only, like a Python that is killed intermittently
  writeFileSync(flaky, `#!/bin/bash\nif [ -e "${s.root}/once" ]; then kill -9 $$; fi\ntouch "${s.root}/once"\nexit 0\n`);
  const res = s.run([GUARD_PY, "--mode", "block", "--exit-code"], FROZEN);
  assert.equal(res.status, 2);
  assert.equal(s.cached(), "node");
});

test("a hung uv probe is killed with its whole process group", () => {
  const s = sandbox({ uv: "forks", python3: "missing" });
  const res = s.run(["--uv-with", "mcp>=1.2.0", join(ROOT, "mcp", "server.py")],
    JSON.stringify({ jsonrpc: "2.0", id: 1, method: "ping" }) + "\n", { GEEKY_PROBE_BUDGET: "1" });
  assert.equal(res.stdout, `{"jsonrpc":"2.0","id":1,"result":{}}\n`);
  // poll briefly: a killed orphan can still be listed until the kernel reaps it
  let survivors = "";
  for (let i = 0; i < 20; i++) {
    survivors = spawnSync("pgrep", ["-f", `sleep ${s.marker}`], { encoding: "utf8" }).stdout.trim();
    if (!survivors) break;
    spawnSync("sleep", ["0.05"]);
  }
  assert.equal(survivors, "", "the stub uv's child must not outlive the probe");
});

test("probing stays inside the budget even when every interpreter hangs", () => {
  const s = sandbox({ python3: "hangs", python: "hangs", py: "hangs" });
  const res = s.run([GUARD_PY, "--mode", "block", "--exit-code"], FROZEN, { GEEKY_PY_PROBE_TIMEOUT: "2" });
  assert.equal(res.status, 2);
  assert.ok(res.ms < 5000, `hooks.json allows 5 s; probing took ${res.ms} ms`);
});

test("a launch killed mid-probe leaves Node cached for the next one", async () => {
  const s = sandbox({ python3: "hangs" });
  const { spawn } = await import("node:child_process");
  const child = spawn("bash", [REDIRECTOR, GUARD_PY], { env: { ...s.env, GEEKY_PY_PROBE_TIMEOUT: "20", GEEKY_PROBE_BUDGET: "20" }, stdio: "ignore" });
  await new Promise((r) => setTimeout(r, 1500));
  child.kill("SIGKILL");
  assert.equal(s.cached(), "node");
  spawnSync("pkill", ["-f", join(s.root, "bin")]);
});

test("GEEKY_RUNTIME=python with no Python is an error, not a silent Node run", () => {
  const s = sandbox({});
  // no stubs and no /usr/bin (macOS keeps a real python3 there): genuinely no Python
  const res = s.run([GUARD_PY], "", { GEEKY_RUNTIME: "python", PATH: [dirname(process.execPath), "/bin"].join(":") });
  assert.equal(res.status, 1);
  assert.match(res.stderr, /GEEKY_RUNTIME=python, but no Python was found/);
});

test("without Node the redirector does not probe: old behaviour, first Python that starts", () => {
  const s = sandbox({ python3: "healthy" });
  const noNode = { PATH: [join(s.root, "bin"), "/usr/bin", "/bin"].join(":") };
  const res = s.run([GUARD_PY, "--mode", "warn"], "", noNode);
  assert.equal(res.stdout, `PYTHON3-RAN ${GUARD_PY} --mode warn\n`);
  assert.ok(!existsSync(join(s.data, "runtime-python")), "no decision to cache without a fallback");
});

test("--uv-with without a script is a usage error", () => {
  const s = sandbox({});
  assert.equal(s.run(["--uv-with", "mcp>=1.2.0"]).status, 2);
});

// --- review round 4 -------------------------------------------------------- //

test("fractional or unparsable timeout settings never break probing", () => {
  const settings: Record<string, string>[] = [{ GEEKY_PY_PROBE_TIMEOUT: "1.5" }, { GEEKY_PROBE_BUDGET: "2.5" }, { GEEKY_PROBE_BUDGET: "abc" },
    { GEEKY_PY_PROBE_TIMEOUT: "08" }, { GEEKY_PY_PROBE_TIMEOUT: "." }];
  for (const extra of settings) {
    const s = sandbox({ python3: "healthy" });
    const res = s.run([GUARD_PY], "", extra);
    assert.equal(res.stderr, "", `${JSON.stringify(extra)}: ${res.stderr}`);
    assert.match(res.stdout, /^PYTHON3-RAN /, JSON.stringify(extra));
    assert.equal(s.cached(), "python:python3", JSON.stringify(extra));
  }
});

test("a one-part version floor (mcp>=2) is still a floor", () => {
  const s = sandbox({ python3: "healthy" });
  s.run(["--uv-with", "mcp>=2", join(ROOT, "mcp", "server.py")]);
  assert.match(readFileSync(join(s.root, "calls.log"), "utf8"), /'2'\.split/);
});
