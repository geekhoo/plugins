# Kickoff — execute the geeky_mcp SDK 2.x migration

Paste the block below verbatim into a fresh Claude Code session on the target
machine. It is self-contained: it assumes no conversation history and no access to
the session that produced the plan.

---

## Objective

Execute all four tasks in `docs/geeky-mcp-sdk-2x/plan.md` in the `geekhoo/plugins`
repository: move `geeky-orchestration/mcp/server.py` off its hard `mcp<2.0.0` pin
onto a dual-path import that runs on both the 1.x and 2.x Python MCP SDKs, give it an
accurate `serverInfo.version`, widen the three dependency constraints, and release.
The plan is the authority on task boundaries; the spec is the authority on decisions.
Do not redesign either — if you believe a decision is wrong, stop and say so rather
than silently deviating.

## Environment — verify, do not assume

Repository: `https://github.com/geekhoo/plugins`, branch `main`.

The working directory on this machine is **unknown to the author of this prompt**. If
you already have a clone, use it; otherwise clone it fresh. Establish the path before
anything else and name it explicitly in your first message.

Required tooling, all of which must be confirmed present before you start — report any
that are missing and stop rather than working around them:

- `git`
- `uv` (Astral) — the MCP server is launched as `uv run --with <spec> python server.py`
- `python` ≥ 3.10
- `node` — only needed if you run the `semantic-design-system` test suite; not
  required for this work

The originating machine was Windows, and some notes in the repo reflect that (forward
slashes for the Bash tool, PowerShell vs Bash separation). **Do not carry those over
if the target machine is not Windows.** Adapt shell syntax to the actual platform and
say which platform you are on.

## Ground truth to establish first

```bash
git fetch origin && git status --porcelain && git rev-parse HEAD origin/main
git merge-base --is-ancestor 8bd79d43f862c82a590217b0db72aac9da0599cb HEAD && echo "plan+spec present"
```

- The tree must be clean before you start. If it is not, stop and report what is dirty.
- If `HEAD` is behind `origin/main`, `git pull --ff-only` first. Never merge, never rebase
  onto a divergent history, never force.
- Commit `8bd79d4` is where the plan and spec landed. If the ancestor check fails, you
  are on the wrong history — stop.

## Read order

1. `docs/geeky-mcp-sdk-2x/plan.md` — the four tasks, in order, with acceptance criteria
2. `docs/geeky-mcp-sdk-2x/spec.md` — decisions D1–D4, invariants, error behavior
3. `geeky-orchestration/mcp/server.py` — the file being changed; note line 29 (the
   import) and line 42 (the constructor)
4. `geeky-orchestration/.mcp.json` and `geeky-orchestration/.codex-plugin/mcp.json` —
   the two launch configs that must stay in lockstep
5. `geeky-orchestration/mcp/pyproject.toml` — the third pin site
6. `geeky-orchestration/test_plugin_metadata.py` — the version-alignment contract
7. `geeky-orchestration/test_quality_gates.py` — the pattern for building a throwaway
   planning folder with `tempfile.TemporaryDirectory()`; reuse it in T1 rather than
   inventing a fixture layout

## Verified current state

- `geeky-orchestration` is at version `0.2.14` in three manifests that must agree:
  `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, and the matching entry in
  the root `.claude-plugin/marketplace.json`. `test_plugin_metadata.py` enforces this.
- All three pin sites currently carry `mcp<2.0.0`. That pin is deliberate and load-bearing
  until T2 lands: `mcp` 2.0.0 renamed `mcp.server.fastmcp.FastMCP` to
  `mcp.server.mcpserver.MCPServer`, and without the dual-path import the server dies at
  import before the MCP handshake.
- Test suites were green at `8bd79d4`: `python -m pytest -q` at repo root reported
  **45 passed, 18 subtests**. Re-run it before you change anything and confirm the same
  number; if it differs, report that before proceeding.
- The two SDK majors produce **semantically identical** `tools/list` and `tools/call`
  output for this server. That is the invariant T1 exists to protect.

## Constraints

- **Do not open or read anything under any `archives/` or `archive/` directory** in this
  repository.
- Keep both SDK majors working. Introducing any 2.x-only API (middleware, extensions,
  elicitation, caching hints, subscriptions, `structured_output`) turns the shim into a
  breaking change and violates spec D1. If a task appears to require one, stop and escalate.
- Do not change the six validator scripts under `geeky-orchestration/scripts/` or
  `geeky-orchestration/hooks/`, or their `--json` contracts. This work is transport and
  packaging only.
- Small, logically grouped commits, one per task. Conventional Commits format matching
  the repo: `type(scope): summary (version)`.
- Never `--no-verify`. Never force-push.
- **Do not push.** Leave the commits local and report the SHAs. The repository owner
  pushes.
- `uv run` inside `geeky-orchestration/mcp/` creates a `.venv` there. It is gitignored.
  Leave the tree as you found it.

## Expected outputs

- `geeky-orchestration/mcp/wire_baseline.py` — the A/B harness (T1)
- `geeky-orchestration/mcp/wire_baseline.json` — the captured 1.x baseline (T1)
- Modified `geeky-orchestration/mcp/server.py` (T2)
- Modified `.mcp.json`, `.codex-plugin/mcp.json`, `mcp/pyproject.toml` (T3)
- Version bump across the three manifests, plus the documentation sweep listed in T4
- One commit per task, SHAs reported

## Validation gates

Run these from the repository root unless stated otherwise. Report each by name with
the command, its exit code, and the salient output.

- **G1 — baseline reproducible.** Run the T1 harness twice on `mcp<2.0.0` and diff the
  two outputs. They must be byte-identical.
- **G2 — wire format unchanged.** Run the T1 harness on `mcp>=2.0.0` and diff against the
  committed baseline. Any difference outside `serverInfo` fails the migration — stop and
  report rather than updating the baseline to match.
- **G3 — both SDKs start.** The server completes a connection and lists **six** tools
  under both `--with "mcp<2.0.0"` and `--with "mcp>=2.0.0"`. Expected names:
  `geeky_validate_planning_folder`, `geeky_validate_task_schema`, `geeky_validate_kanban`,
  `geeky_check_dod`, `geeky_check_commit`, `geeky_check_frozen_artifact`.
- **G4 — no pin left behind.** `git ls-files | xargs grep -l "mcp<2.0.0"` prints nothing.
- **G5 — JSON still parses.** Both MCP configs and all manifests load as valid JSON. Note
  the trap recorded in T4: `geeky.manifest.json` holds the run command inside a JSON
  string, so a double-quoted specifier breaks the file. Use single quotes there.
- **G6 — suite green.** `python -m pytest -q` at repo root, 45 passed.
- **G7 — startup latency measured.** The host launches a stdio MCP server **twice** per
  connection (a `server/discover` probe process, then the session process), so startup
  cost is paid twice. Time a cold and a warm `uv run --with "mcp>=2.0.0" python server.py`
  startup and report both numbers. This gate is a measurement, not a pass/fail — but it
  must not be skipped, because it is the one cost the plan could not estimate in advance.

## Reporting contract

Lead your final message with gate status and raw evidence — the command, its exit code,
and the salient output — before any narrative. State any gate you did not run as
**"NOT RUN"** in those exact words, with the reason. Do not imply verification that did
not happen. Report the commit SHAs, and list anything you changed that the plan did not
anticipate.

If G2 fails, that is the signal to stop the whole migration and report, not to adjust the
baseline. The wire format not changing is the premise the entire plan rests on.

## Known assumptions, flagged as assumptions

- The plan assumes `uv` resolves `mcp` 2.x successfully on the target machine. If the
  target is offline or behind an index mirror that lacks 2.x, G2 and G3 cannot run — say
  so rather than improvising a substitute.
- The plan assumes the six validator scripts behave identically on the target platform.
  They are stdlib-only Python, so this should hold, but the T1 baseline is captured on
  whichever machine runs it — if you capture a baseline on a different platform than the
  one recorded in the repo, note it.

## Out of scope

- Pushing to `origin`.
- The `semantic-design-system` MCP server. It is hand-written JavaScript with no Python
  SDK dependency and is unaffected by this work.
- Teaching any server the stateless MCP v2 request shape. The dual-path import is
  sufficient; the SDK handles protocol negotiation.
- HTTP or SSE transports. This server is stdio-only.
