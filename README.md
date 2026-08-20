# geekhoo plugins

This repository publishes four local plugins. They cover DevExtreme page work,
design tokens, feature delivery, and day-to-day engineering tasks. Pick the
plugin that matches the job.

The root includes a Claude Code marketplace plus Codex plugin manifests. Each
plugin has its own docs and checks.

## Plugins

| Plugin | Use it for | Version | Docs |
|---|---|---:|---|
| `dx-webdev` | Pure HTML, JavaScript, and CSS pages built with DevExtreme jQuery widgets. | 0.2.3 | [README](dx-webdev/README.md) |
| `semantic-design-system` | Build, validate, and apply DTCG design tokens, including CSS output and optional MCP tools. | 0.2.7 | [README](semantic-design-system/README.md) |
| `geeky-orchestration` | Plan, review, implement, track, and archive feature work. | 0.2.16 | [README](geeky-orchestration/README.md) |
| `dev-workflows` | Reusable skills for planning, review, testing, browser and Figma work, environment setup, Git, docs, and session analysis. | 0.2.12 | [Packaging notes](dev-workflows/PACKAGING.md) |

The versions in this table come from
`.claude-plugin/marketplace.json`. The Claude and Codex manifests inside each
plugin should stay aligned with that entry.

## Install in Claude Code

Add the repository as a marketplace, then install one or more plugins:

```text
/plugin marketplace add https://github.com/geekhoo/plugins.git
/plugin install dx-webdev@geekhoo-plugins
/plugin install semantic-design-system@geekhoo-plugins
/plugin install geeky-orchestration@geekhoo-plugins
/plugin install dev-workflows@geekhoo-plugins
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

Each plugin folder also has a `.codex-plugin` manifest. Load the plugin from
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

## Repository layout

```text
.claude-plugin/marketplace.json     Claude Code marketplace metadata
dev-workflows/                      Composable workflow skills
dx-webdev/                          DevExtreme jQuery page workflows
geeky-orchestration/                Feature lifecycle and quality gates
semantic-design-system/             Design-token workflows and utilities
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

## License notes

License metadata belongs to each plugin. `semantic-design-system` is MIT.
`dx-webdev`, `geeky-orchestration`, and `dev-workflows` are marked `UNLICENSED`
in their manifests. DevExtreme assets and libraries remain subject to
DevExpress licensing terms in projects that use them.
