# geekhoo plugins

[Native Codex C0 result](geeky-orchestration/evals/analyses/c0-codex-native-run-20261029/README.md):
native delegation worked, but the run stopped at the pre-task commit-rule conflict.
Current C0 readiness is blocked; no automatic retry is scheduled. The fix, a
docs-only `Tasks: none` gate rule, is specified in the
[Codex kickoff](geeky-orchestration/evals/analyses/c0-codex-native-run-20261029/handoff.md).

[Focused Codex native-wire preparation](geeky-orchestration/evals/analyses/c0-codex-native-preparation-20261029/README.md)
re-examines the failed trace and prepares Luna's direct Responses/V2 route.
The failed mapping bridge is bypassed for this profile; no evaluation was launched.

[Claude C0 overtime completion](geeky-orchestration/evals/analyses/c0-luna-overtime-20261028/README.md)
reached final-review PASS and cumulative parity **98.44** after 18m02s additional
active time. Original timeout remains preserved at parity95.14. Scores were read back from Langfuse.

[Luna C0 runtime results](geeky-orchestration/evals/analyses/c0-luna-sequential-20261028/README.md):
Codex failed in plan review on a bridge mapping error; Claude timed out during
final review after passing 13/13 oracle checks. Both runs are terminal and stopped.

[Luna/high C0 preparation](geeky-orchestration/evals/analyses/c0-luna-preparation-20261028/README.md)
records committed runner/workflow fixes and the owner's Luna qualification waiver.
Both MXC runners use LiteLLM and high effort; both evaluations remain held.

[Minimal real Claude/MXC Messages checks](geeky-orchestration/evals/analyses/mxc-claude-messages-20261027/README.md)
passed tool roundtrips for Luna, GLM, Haiku and MiMo. MiniMax/DeepSeek returned
upstream 404s on Messages. Both C0 evaluations remain stopped.

[The minimal reasoning bridge repair](geeky-orchestration/evals/analyses/bridge-reasoning-normalization-20261027/README.md)
passed 178 regressions and three live HTTP-bridge checks for MiniMax, DeepSeek and
MiMo. Both evaluations remain stopped; full workflow qualification is separate.

[Bounded LiteLLM retests](geeky-orchestration/evals/analyses/litellm-bounded-retest-20261027/README.md)
finished the limited generations and verified Luna's selected native opaque relay.
Other wire-contract and thinking-control gaps remain. Both evaluations stay stopped.

[Six small LiteLLM model probes](geeky-orchestration/evals/analyses/litellm-six-models-20261027/README.md)
returned basic HTTP 200 responses for every route. Selected bridge checks passed
for Luna, GLM and Haiku; native gaps and low-cap results are recorded separately.
Both C0 evaluations remain stopped.

[Responses API / Codex V2 contract tools](geeky-orchestration/evals/tools/responses_contract/README.md)
support offline plans/replay and explicit endpoint probes for later use.
No endpoint was contacted while creating them; both C0 evaluations remain stopped.

Fresh sequential [C0 results, 27 October](geeky-orchestration/evals/analyses/c0-fresh-sequential-20261027/README.md):
Codex stopped during research; Claude timed out during plan review. Neither
implemented the package. Both traced successfully to Langfuse; no further run is active.

The [offline follow-up](geeky-orchestration/evals/analyses/c0-root-causes-20261027/README.md)
adds planning budget checks and rejects the observed Codex tool-call text error.
Its upstream origin and live improvement remain unproved. Both evaluations stay stopped.

This repository publishes five local plugins. They cover DevExtreme page work,
design tokens, feature delivery, day-to-day engineering tasks, and sandboxed
Claude Code runs. Pick the plugin that matches the job.

The root includes a Claude Code marketplace plus Codex plugin manifests. Each
plugin has its own docs and checks.

Historical completed Windows MXC C0 records: [claudex-001 evaluation](geeky-orchestration/evals/analyses/c0-claudex-001-win-20261026/README.md).
Codex completed at 97.46 parity. Claude's later continuation completed review
and closeout at 98.33 cumulative parity; its earlier timeout remains at 90.33.
Both passed oracle 13/13, and Langfuse scores are verified. The cumulative
continuation includes additional time and context.

The [C0 remediation plan](geeky-orchestration/evals/analyses/c0-claudex-001-win-20261026/remediation-20261026/implementation-plan.md)
defines three follow-up changes now implemented and accepted through offline review.
The [implementation handoff](geeky-orchestration/evals/analyses/c0-claudex-001-win-20261026/remediation-20261026/handoff.md)
records evidence and acceptance separately from future evaluation authorization.

[Post-remediation non-chargeable MXC mocks](geeky-orchestration/evals/analyses/c0-post-remediation-mock-20261026/report.md)
passed the full scripted C0 oracle for both harnesses (13/13, three repetitions).
The original records identify stale terminal step metadata and measured timeout overhead.
The [minimal follow-up implementation](geeky-orchestration/evals/analyses/c0-post-remediation-mock-20261026/follow-up-implementation.md)
fixes the seed-step transition and maintains guarded H1 fixtures, with fresh offline
and bounded real-MXC evidence. Scripted reviews do not establish live-model behavior.

The [C0 operator readiness](geeky-orchestration/evals/c0-readiness.md) distinguishes
the recorded 28 mock checks from current mapping verification. Both evaluations
remain stopped pending separate explicit launch authorization.

The [Codex V2 wire mapper](geeky-orchestration/evals/analyses/codex-v2-litellm-mapping-20261027/README.md)
translates agent traffic before LiteLLM and restores explicit plaintext metadata.
Offline checks and one bounded synthetic live request pass. Both C0 evaluations
remain stopped; this diagnostic does not qualify a complete Codex/MXC workflow.

## Plugins

| Plugin | Use it for | Version | Docs |
|---|---|---:|---|
| `dx-webdev` | Pure HTML, JavaScript, and CSS pages built with DevExtreme jQuery widgets. | 0.2.3 | [README](dx-webdev/README.md) |
| `semantic-design-system` | Build, validate, and apply DTCG design tokens, including CSS output and optional MCP tools. | 0.3.0 | [README](semantic-design-system/README.md) |
| `geeky-orchestration` | Plan, review, implement, track, and archive feature work. | 0.3.0 | [README](geeky-orchestration/README.md) |
| `dev-workflows` | Reusable skills for planning, review, testing, browser and Figma work, environment setup, Git, docs, and session analysis. | 0.2.12 | [Packaging notes](dev-workflows/PACKAGING.md) |
| `mxc-sandbox` | Run the Claude Code CLI inside a Microsoft MXC sandbox (Windows, Linux, macOS) for isolated testing. | 0.2.1 | [README](mxc-sandbox/README.md) |

The versions in this table come from
`.claude-plugin/marketplace.json`. The Claude and Codex manifests inside each
plugin (Claude only for `mxc-sandbox`) should stay aligned with that entry.

## Install in Claude Code

Add the repository as a marketplace, then install one or more plugins:

```text
/plugin marketplace add https://github.com/geekhoo/plugins.git
/plugin install dx-webdev@geekhoo-plugins
/plugin install semantic-design-system@geekhoo-plugins
/plugin install geeky-orchestration@geekhoo-plugins
/plugin install dev-workflows@geekhoo-plugins
/plugin install mxc-sandbox@geekhoo-plugins
```

You only need to install the plugins you plan to use. The marketplace name is
`geekhoo-plugins`, and the install name is the plugin name in the table above.

`dev-workflows` lists two dependencies in
`dev-workflows/.codex-plugin/plugin.json`. They are the local
`geeky-orchestration` plugin and the official `figma` plugin from
`claude-plugins-official`.
Claude Code installs `dev-workflows` on its own, so install
`geeky-orchestration` and `figma` separately when you need those skills. The
marketplace allowlist in `.claude-plugin/marketplace.json` permits the
cross-marketplace `figma` dependency.

Each plugin folder except `mxc-sandbox` (which drives the Claude Code CLI
specifically) also has a `.codex-plugin` manifest. Load the plugin from
its directory with the Codex plugin workflow for your setup.
`geeky-orchestration` includes a projection script for Claude, Codex, Copilot,
Cursor, and generic Markdown agent files. See its
[cross-harness registration guide](geeky-orchestration/docs/cross-harness-agent-registration.md).

## Pick a starting point

Use `dx-webdev` when the output must be ordinary `index.html`, `styles.css`,
and `app.js` files. Its checks reject framework artifacts, JSX or TSX markers,
and ThemeBuilder output.

Use `semantic-design-system` when a project needs tokens. It reads
`design/tokens/` by default, validates DTCG token files, resolves aliases, and
builds semantic and component tokens into CSS custom properties. It also
includes an optional MCP server and a Figma sync skill with Claude and Codex
guidance.

Use `geeky-orchestration` when the work needs a structured path from research
to planning to implementation. Its planning files have frozen and mutable
sections. Python and PowerShell gates check folder shape, task schemas, kanban
state, Definition of Done, and commit messages. The optional MCP server runs
the same gates for MCP-capable agents.

Use `dev-workflows` when you need one skill instead of a full lifecycle. Its
library includes small tools such as environment checks, scope guards, browser
probes, repository validation, document checks, and Git hygiene. It also
includes larger workflows built from those tools.

Use `mxc-sandbox` when a Claude Code run should not see the whole machine: testing
a plugin or skill, trying prompts against an untrusted repo, or checking what a
hook or MCP server needs. It runs on Windows (ProcessContainer), Linux (Bubblewrap) and macOS
(Seatbelt, untested) and builds a small .NET host on first use.

## Repository layout

```text
.claude-plugin/marketplace.json     Claude Code marketplace metadata
dev-workflows/                      Composable workflow skills
dx-webdev/                          DevExtreme jQuery page workflows
geeky-orchestration/                Feature lifecycle and quality gates
semantic-design-system/             Design-token workflows and utilities
mxc-sandbox/                        Claude Code CLI inside Microsoft MXC (Windows, Linux, macOS)
docs/superpowers/                   Dated design notes and implementation plans
```

Inside a plugin, the important paths are usually:

- `.claude-plugin/plugin.json` for Claude Code metadata.
- `.codex-plugin/plugin.json` for Codex metadata and, where needed, host config.
- `skills/` for the written workflow instructions.
- `agents/`, `commands/`, `scripts/`, `references/`, `templates/`, `tests/`, or
  `mcp/` when that plugin provides them.

The canonical agent definitions for `geeky-orchestration` live in
`geeky-orchestration/agents/`. Its sync scripts generate the harness-specific
files under the root `.claude/`, `.codex/`, `.cursor/`, `.github/`, and
`.agents/` directories. Edit the canonical files, then run the sync script.

## Development checks

There is no root `package.json`, build, or test command. Run checks from the
plugin directory they belong to.

### `dx-webdev`

The scripts use Node.js and have no external npm dependencies:

```bash
cd dx-webdev
node scripts/generate-dx-page.js --spec references/example-page-spec.json --out tmp/generated-basic
node scripts/validate-dx-html-js.js --dir tmp/generated-basic
node scripts/audit-dx-output.js --dir tmp/generated-basic
node scripts/extract-design-tokens.js --tokens path/to/tokens.json --out tmp/tokens.css
```

For a syntax-only check:

```bash
node --check scripts/generate-dx-page.js
node --check scripts/validate-dx-html-js.js
node --check scripts/extract-design-tokens.js
node --check scripts/audit-dx-output.js
```

Generated files under `tmp/` are ignored.

### `semantic-design-system`

The package uses Node's built-in test runner:

```bash
cd semantic-design-system
npm test
npm run coverage
npm run validate:example
npm run build:example
```

The MCP server is registered by the plugin manifests. Its local command uses
Node, and its default output is `src/styles/tokens.css`.

### `geeky-orchestration`

Run the Python tests and preview agent projections without writing generated
files:

```bash
cd geeky-orchestration
python -m pytest -q
python scripts/sync-agents.py --dry-run --json
```

The quality-gate scripts need only the Python standard library. The optional
`geeky_mcp` server needs `uv` and the `mcp` package. Its
`mcp/.python-version` pins the server environment to Python 3.14. See the
[MCP notes](geeky-orchestration/mcp/README.md) before running it directly.

### `dev-workflows`

The bundled Python tests can be run with:

```bash
cd dev-workflows
python -m pytest -q
```

Some skills call tools supplied by other plugins. The dependency details and
the Figma setup are in [`dev-workflows/PACKAGING.md`](dev-workflows/PACKAGING.md).

### `mxc-sandbox`

Windows only. The wrapper builds the host into `%USERPROFILE%\.mxc-sandbox\bin`
(needs the .NET 10 SDK, or edit the host `.csproj` for 8/9) and probes the machine:

```powershell
cd mxc-sandbox
pwsh -NoProfile -File scripts/mxc.ps1 -Rebuild probe --workspace C:\repos\scratch
pwsh -NoProfile -File scripts/mxc.ps1 run --workspace C:\repos\scratch -- -p "Reply with exactly: PONG"
```

## License notes

License metadata belongs to each plugin. `semantic-design-system` and
`mxc-sandbox` are MIT.
`dx-webdev`, `geeky-orchestration`, and `dev-workflows` are marked `UNLICENSED`
in their manifests. DevExtreme assets and libraries remain subject to
DevExpress licensing terms in projects that use them.
