#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { DEFAULT_TOKEN_DIR, writeFileAtomic } from '../scripts/token-utils.mjs';

// A harness may pass a placeholder through unexpanded (e.g. the literal
// "${CLAUDE_PLUGIN_ROOT}"); treat those as unset instead of resolving them
// into a path that does not exist.
const envValue = (name) => {
  const v = process.env[name];
  return v && !v.includes('${') ? v : undefined;
};

const pluginRoot =
  envValue('PLUGIN_ROOT') ||
  envValue('CODEX_PLUGIN_ROOT') ||
  envValue('CLAUDE_PLUGIN_ROOT') ||
  path.resolve(import.meta.dirname, '..');
const projectDir =
  envValue('PLUGIN_PROJECT_DIR') ||
  envValue('CODEX_PROJECT_DIR') ||
  envValue('CLAUDE_PROJECT_DIR') ||
  process.cwd();
const defaultTokenDir = DEFAULT_TOKEN_DIR;
// userConfig values arrive as CLAUDE_PLUGIN_OPTION_<KEY>; DEFAULT_CSS_* is the
// Codex/manual path. ${user_config.*} is deliberately NOT used in .mcp.json --
// it breaks env substitution for the whole block (anthropics/claude-code#51573).
const defaultCssOutputFile =
  envValue('CLAUDE_PLUGIN_OPTION_CSS_OUTPUT_FILE') ||
  envValue('DEFAULT_CSS_OUTPUT_FILE') ||
  'src/styles/tokens.css';
const defaultCssPrefix =
  envValue('CLAUDE_PLUGIN_OPTION_CSS_PREFIX') ||
  envValue('DEFAULT_CSS_PREFIX') ||
  'ds';

const SUBPROCESS_TIMEOUT_MS = Number(envValue('DS_SUBPROCESS_TIMEOUT_MS')) || 60_000;
const SUBPROCESS_MAX_BUFFER = Number(envValue('DS_SUBPROCESS_MAX_BUFFER')) || 4 * 1024 * 1024;
const ROOTS_REQUEST_TIMEOUT_MS = 5_000;

// ---------------------------------------------------------------------------
// Workspace boundary
//
// MCP defines client-declared filesystem `roots` for exactly this problem
// (spec 2025-06-18, client/roots: "Servers SHOULD validate all paths against
// provided roots"). If the client advertises the roots capability we query
// `roots/list` and use the answer; otherwise we fall back to the configured
// project directory. Reads may span every declared root; writes are confined to
// a single, narrower root so a tool can never create or clobber files across
// the rest of the workspace.
// ---------------------------------------------------------------------------

let clientSupportsRoots = false;
let readRoots = [projectDir];
let writeRoots = [projectDir];
let rootsSource = 'fallback:projectDir';
let rootsReady = Promise.resolve();

// Resolve a path through any symlinks/junctions that actually exist, including
// when the target itself does not exist yet (the common case for writes). The
// deepest existing ancestor is realpath'd and the non-existent tail re-joined,
// so an escape through a symlinked parent directory cannot hide.
function realpathDeep(target) {
  const resolved = path.resolve(target);
  const tail = [];
  let cursor = resolved;
  for (;;) {
    try {
      const real = fs.realpathSync.native(cursor);
      return tail.length ? path.join(real, ...tail) : real;
    } catch {
      const parent = path.dirname(cursor);
      if (parent === cursor) return resolved;
      tail.unshift(path.basename(cursor));
      cursor = parent;
    }
  }
}

function isWithin(root, full) {
  const rel = path.relative(realpathDeep(root), full);
  if (rel === '') return true;
  // A prefix comparison is NOT enough here: "/app/data-evil" starts with
  // "/app/data". Only a relative path that never steps up and is not itself
  // absolute (different drive/UNC root) is genuinely inside.
  return rel !== '..' && !rel.startsWith(`..${path.sep}`) && !path.isAbsolute(rel);
}

// Refuse, never sanitize-and-repair: a path outside the boundary is an error,
// not something to be clamped back inside.
function resolveWithin(value, fallback, roots, label) {
  const raw = value == null || value === '' ? fallback : value;
  if (typeof raw !== 'string' || !raw.length) {
    throw new Error(`Missing ${label} path and no default is configured.`);
  }
  const candidate = path.isAbsolute(raw) ? raw : path.join(projectDir, raw);
  const full = realpathDeep(candidate);
  for (const root of roots) {
    if (isWithin(root, full)) return full;
  }
  throw new Error(
    `Path escapes the allowed ${label} root(s): ${JSON.stringify(raw)} resolves to ${full}; ` +
    `allowed ${label} roots: ${roots.join(path.delimiter)}`
  );
}

function applyRoots(list) {
  const dirs = [];
  for (const entry of Array.isArray(list) ? list : []) {
    const uri = entry && entry.uri;
    if (typeof uri !== 'string' || !uri.startsWith('file:')) continue;
    try { dirs.push(path.resolve(fileURLToPath(uri))); } catch { /* unusable root URI */ }
  }

  if (!dirs.length) {
    readRoots = [projectDir];
    writeRoots = [projectDir];
    rootsSource = clientSupportsRoots ? 'fallback:projectDir (client returned no usable file roots)' : 'fallback:projectDir';
    return;
  }

  readRoots = dirs;
  // Writes get the narrower surface. When the project directory sits inside a
  // declared root, that project directory *is* the write root; otherwise writes
  // are confined to the first declared root.
  const realProject = realpathDeep(projectDir);
  const containing = dirs.find(d => isWithin(d, realProject));
  writeRoots = [containing ? projectDir : dirs[0]];
  rootsSource = 'client:roots/list';
}

// ---------------------------------------------------------------------------
// Subprocess execution -- always bounded in both time and output size.
// ---------------------------------------------------------------------------

function runNode(script, args) {
  const result = spawnSync('node', [path.join(pluginRoot, 'scripts', script), ...args], {
    cwd: projectDir,
    encoding: 'utf8',
    timeout: SUBPROCESS_TIMEOUT_MS,
    maxBuffer: SUBPROCESS_MAX_BUFFER,
    killSignal: 'SIGKILL'
  });

  if (result.error) {
    const code = result.error.code;
    const reason =
      code === 'ETIMEDOUT' ? `${script} exceeded the ${SUBPROCESS_TIMEOUT_MS}ms time limit and was killed`
        : code === 'ENOBUFS' ? `${script} exceeded the ${SUBPROCESS_MAX_BUFFER}-byte output limit and was killed`
          : `${script} failed to run: ${result.error.message}`;
    return {
      ok: false,
      stdout: (result.stdout || '').trim(),
      stderr: JSON.stringify({ ok: false, error: reason }, null, 2),
      status: null
    };
  }

  if (result.signal) {
    return {
      ok: false,
      stdout: (result.stdout || '').trim(),
      stderr: JSON.stringify({ ok: false, error: `${script} was terminated by signal ${result.signal}` }, null, 2),
      status: null
    };
  }

  return {
    ok: result.status === 0,
    stdout: result.stdout?.trim() || '',
    stderr: result.stderr?.trim() || '',
    status: result.status
  };
}

// ---------------------------------------------------------------------------
// Token skeleton
// ---------------------------------------------------------------------------

function skeletonPayloads(productName) {
  const primitive = {
    primitive: {
      color: {
        $type: 'color',
        neutral: {
          0: { $value: { colorSpace: 'srgb', components: [1, 1, 1], hex: '#ffffff' } },
          900: { $value: { colorSpace: 'srgb', components: [0.08, 0.08, 0.08], hex: '#141414' } }
        },
        brand: {
          500: { $value: { colorSpace: 'srgb', components: [0.05, 0.38, 0.95], hex: '#0d61f2' } },
          600: { $value: { colorSpace: 'srgb', components: [0.03, 0.28, 0.75], hex: '#0848bf' } }
        }
      },
      space: {
        $type: 'dimension',
        0: { $value: { value: 0, unit: 'px' } },
        100: { $value: { value: 0.5, unit: 'rem' } },
        200: { $value: { value: 1, unit: 'rem' } },
        300: { $value: { value: 1.5, unit: 'rem' } }
      },
      radius: {
        $type: 'dimension',
        sm: { $value: { value: 0.25, unit: 'rem' } },
        md: { $value: { value: 0.5, unit: 'rem' } },
        pill: { $value: { value: 999, unit: 'px' } }
      }
    }
  };

  const semantic = {
    semantic: {
      color: {
        fg: {
          $type: 'color',
          default: { $value: '{primitive.color.neutral.900}', $description: `Default foreground for ${productName}.` },
          inverse: { $value: '{primitive.color.neutral.0}' },
          brand: { $value: '{primitive.color.brand.600}' }
        },
        bg: {
          $type: 'color',
          canvas: { $value: '{primitive.color.neutral.0}' },
          surface: { default: { $value: '{primitive.color.neutral.0}' } },
          action: { primary: { default: { $value: '{primitive.color.brand.500}' }, hover: { $value: '{primitive.color.brand.600}' } } }
        }
      },
      space: {
        $type: 'dimension',
        inset: { sm: { $value: '{primitive.space.100}' }, md: { $value: '{primitive.space.200}' }, lg: { $value: '{primitive.space.300}' } },
        inline: { sm: { $value: '{primitive.space.100}' }, md: { $value: '{primitive.space.200}' } },
        stack: { sm: { $value: '{primitive.space.100}' }, md: { $value: '{primitive.space.200}' }, lg: { $value: '{primitive.space.300}' } }
      },
      radius: {
        $type: 'dimension',
        control: { $value: '{primitive.radius.md}' },
        surface: { $value: '{primitive.radius.md}' },
        pill: { $value: '{primitive.radius.pill}' }
      }
    }
  };

  const component = {
    component: {
      button: {
        primary: {
          bg: {
            $type: 'color',
            default: { $value: '{semantic.color.bg.action.primary.default}' },
            hover: { $value: '{semantic.color.bg.action.primary.hover}' }
          },
          fg: { $type: 'color', default: { $value: '{semantic.color.fg.inverse}' } },
          radius: { $type: 'dimension', $value: '{semantic.radius.control}' }
        }
      }
    }
  };

  const dark = {
    semantic: {
      color: {
        fg: { $type: 'color', default: { $value: '{primitive.color.neutral.0}' }, inverse: { $value: '{primitive.color.neutral.900}' } },
        bg: { $type: 'color', canvas: { $value: '{primitive.color.neutral.900}' }, surface: { default: { $value: '{primitive.color.neutral.900}' } } }
      }
    }
  };

  return [
    ['primitive/base.tokens.json', primitive],
    ['semantic/base.tokens.json', semantic],
    ['component/button.tokens.json', component],
    ['themes/dark.tokens.json', dark]
  ];
}

// No-clobber by default: if any target file already exists the whole call is
// refused and nothing is written. `force: true` is the only way to overwrite,
// and the response always names what was written, skipped, and overwritten.
function writeSkeleton(outputDir, productName = 'Product', force = false) {
  const dir = resolveWithin(outputDir, defaultTokenDir, writeRoots, 'write');

  const planned = skeletonPayloads(productName).map(([relativePath, payload]) => ({
    relativePath,
    file: path.join(dir, ...relativePath.split('/')),
    contents: JSON.stringify(payload, null, 2)
  }));

  const existing = planned.filter(p => fs.existsSync(p.file));

  if (existing.length && !force) {
    return {
      ok: false,
      outputDir: dir,
      force: false,
      written: [],
      skipped: existing.map(p => p.relativePath),
      overwritten: [],
      error:
        `Refusing to overwrite ${existing.length} existing token file(s): ` +
        `${existing.map(p => p.relativePath).join(', ')}. ` +
        'Nothing was written. Pass force: true to overwrite them.'
    };
  }

  const written = [];
  const overwritten = [];
  for (const item of planned) {
    const preexisting = fs.existsSync(item.file);
    // Content is parsed back off disk before the rename, so a partial or
    // corrupt write never replaces a good file.
    writeFileAtomic(item.file, item.contents, text => { JSON.parse(text); });
    if (preexisting) overwritten.push(item.relativePath);
    else written.push(item.relativePath);
  }

  return { ok: true, outputDir: dir, force: Boolean(force), written, skipped: [], overwritten };
}

// ---------------------------------------------------------------------------
// Tool surface
// ---------------------------------------------------------------------------

const tools = [
  {
    name: 'validate_tokens',
    description: 'Validate design token files (DTCG Format Module 2025.10) for missing types, non-standard $type values, unresolved aliases, circular references, primitive leakage, and literal color naming. Read-only: writes nothing.',
    inputSchema: {
      type: 'object',
      properties: { tokenDir: { type: 'string', description: 'Project-relative or absolute token directory, which must resolve inside a client-declared root (or the project directory). Defaults to design/tokens.' } }
    },
    annotations: {
      title: 'Validate design tokens',
      readOnlyHint: true,
      destructiveHint: false,
      idempotentHint: true,
      openWorldHint: false
    }
  },
  {
    name: 'build_css_variables',
    description: 'Build CSS custom properties from semantic and component design tokens. Fails closed when an exposed token cannot be resolved; pass allowPartial to emit the resolvable subset instead. Theme-aware: base tokens go to :root, files under themes/ become [data-theme="<name>"] overrides, and light/dark themes also emit a prefers-color-scheme block. Overwrites the output CSS file.',
    inputSchema: {
      type: 'object',
      properties: {
        tokenDir: { type: 'string', description: 'Project-relative or absolute token directory (read). Defaults to design/tokens.' },
        outputFile: { type: 'string', description: 'CSS output path (written, and overwritten if present). Defaults to src/styles/tokens.css.' },
        prefix: { type: 'string', description: 'CSS custom-property prefix. Defaults to ds.' },
        allowPartial: { type: 'boolean', description: 'Emit the resolvable subset instead of failing when tokens cannot be resolved. Defaults to false.' }
      }
    },
    annotations: {
      title: 'Build CSS custom properties',
      readOnlyHint: false,
      destructiveHint: true,
      idempotentHint: true,
      openWorldHint: false
    }
  },
  {
    name: 'extract_style_inventory',
    description: 'Scan a web codebase and write a JSON inventory of discovered colors, dimensions, typography, shadows, transitions, z-indexes, breakpoints, and CSS variables. The scan is read-only, but the inventory file it produces is overwritten if present.',
    inputSchema: {
      type: 'object',
      properties: {
        rootDir: { type: 'string', description: 'Directory to scan (read). Defaults to the project directory.' },
        outputFile: { type: 'string', description: 'Inventory output path (written, and overwritten if present). Defaults to .design-system/style-inventory.json.' }
      }
    },
    annotations: {
      title: 'Extract style inventory',
      readOnlyHint: false,
      destructiveHint: true,
      idempotentHint: true,
      openWorldHint: false
    }
  },
  {
    name: 'generate_token_skeleton',
    description: 'Create a minimal primitive/semantic/component/theme token folder skeleton. Defaults to design/tokens in the project. Refuses to overwrite existing token files unless force is true.',
    inputSchema: {
      type: 'object',
      properties: {
        outputDir: { type: 'string', description: 'Token directory to create (written). Defaults to design/tokens.' },
        productName: { type: 'string' },
        force: { type: 'boolean', description: 'Overwrite token files that already exist. Defaults to false, which refuses the call and writes nothing when any target file is present.' }
      }
    },
    annotations: {
      title: 'Generate token skeleton',
      readOnlyHint: false,
      destructiveHint: true,
      idempotentHint: false,
      openWorldHint: false
    }
  }
];

// ---------------------------------------------------------------------------
// JSON-RPC plumbing
// ---------------------------------------------------------------------------

function send(payload) {
  process.stdout.write(JSON.stringify(payload) + '\n');
}

function respond(id, result) {
  send({ jsonrpc: '2.0', id, result });
}

function error(id, code, message) {
  send({ jsonrpc: '2.0', id, error: { code, message } });
}

const pendingOutgoing = new Map();
let nextOutgoingId = 1;

// Server-initiated request (used for roots/list). Ids are prefixed so they can
// never collide with the client's own id space.
function requestClient(method, params = {}, timeoutMs = ROOTS_REQUEST_TIMEOUT_MS) {
  const id = `sds-${nextOutgoingId++}`;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      pendingOutgoing.delete(id);
      reject(new Error(`Timed out waiting for ${method}`));
    }, timeoutMs);
    timer.unref?.();
    pendingOutgoing.set(id, {
      resolve: value => { clearTimeout(timer); resolve(value); },
      reject: err => { clearTimeout(timer); reject(err); }
    });
    send({ jsonrpc: '2.0', id, method, params });
  });
}

function refreshRoots() {
  if (!clientSupportsRoots) {
    applyRoots([]);
    return Promise.resolve();
  }
  return requestClient('roots/list')
    .then(result => applyRoots(result && result.roots))
    .catch(() => applyRoots([]));
}

async function callTool(name, args) {
  await rootsReady;

  if (name === 'validate_tokens') {
    return runNode('validate-tokens.mjs', [
      resolveWithin(args.tokenDir, defaultTokenDir, readRoots, 'read')
    ]);
  }

  if (name === 'build_css_variables') {
    const argv = [
      resolveWithin(args.tokenDir, defaultTokenDir, readRoots, 'read'),
      resolveWithin(args.outputFile, defaultCssOutputFile, writeRoots, 'write'),
      args.prefix || defaultCssPrefix
    ];
    if (args.allowPartial) argv.push('--allow-partial');
    return runNode('build-css-vars.mjs', argv);
  }

  if (name === 'extract_style_inventory') {
    return runNode('extract-style-inventory.mjs', [
      resolveWithin(args.rootDir, '.', readRoots, 'read'),
      resolveWithin(args.outputFile, '.design-system/style-inventory.json', writeRoots, 'write')
    ]);
  }

  if (name === 'generate_token_skeleton') {
    const outcome = writeSkeleton(args.outputDir, args.productName || 'Product', args.force === true);
    const text = JSON.stringify(outcome, null, 2);
    return { ok: outcome.ok, stdout: outcome.ok ? text : '', stderr: outcome.ok ? '' : text, status: outcome.ok ? 0 : 1 };
  }

  return null;
}

async function handle(message) {
  // Responses to requests this server issued (roots/list).
  if (message.id != null && pendingOutgoing.has(message.id) &&
      (Object.prototype.hasOwnProperty.call(message, 'result') ||
       Object.prototype.hasOwnProperty.call(message, 'error'))) {
    const waiter = pendingOutgoing.get(message.id);
    pendingOutgoing.delete(message.id);
    if (message.error) waiter.reject(new Error(message.error.message || 'client error'));
    else waiter.resolve(message.result);
    return;
  }

  if (message.method === 'notifications/initialized') {
    rootsReady = refreshRoots();
    return;
  }

  if (message.method === 'notifications/roots/list_changed') {
    rootsReady = refreshRoots();
    return;
  }

  if (!message.id && message.method?.startsWith('notifications/')) return;

  if (message.method === 'initialize') {
    clientSupportsRoots = Boolean(message.params?.capabilities?.roots);
    respond(message.id, {
      protocolVersion: message.params?.protocolVersion || '2024-11-05',
      capabilities: { tools: {} },
      serverInfo: { name: 'design-system-tools', version: '0.1.0' }
    });
    return;
  }

  if (message.method === 'tools/list') {
    respond(message.id, { tools });
    return;
  }

  if (message.method === 'workspace/roots' || message.method === 'design-system/roots') {
    // Diagnostic helper: report the boundary the server is actually enforcing.
    await rootsReady;
    respond(message.id, { source: rootsSource, readRoots, writeRoots });
    return;
  }

  if (message.method === 'tools/call') {
    const name = message.params?.name;
    const args = message.params?.arguments || {};

    let result;
    try {
      result = await callTool(name, args);
    } catch (e) {
      respond(message.id, {
        content: [{ type: 'text', text: JSON.stringify({ ok: false, tool: name, error: e.message }, null, 2) }],
        isError: true
      });
      return;
    }

    if (!result) {
      error(message.id, -32601, `Unknown tool: ${name}`);
      return;
    }

    respond(message.id, {
      content: [{ type: 'text', text: result.stdout || result.stderr || JSON.stringify(result) }],
      isError: !result.ok
    });
    return;
  }

  error(message.id, -32601, `Unsupported method: ${message.method}`);
}

let buffer = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => {
  buffer += chunk;
  let index;
  while ((index = buffer.indexOf('\n')) >= 0) {
    const line = buffer.slice(0, index).trim();
    buffer = buffer.slice(index + 1);
    if (!line) continue;
    let parsed;
    try { parsed = JSON.parse(line); } catch (e) { error(null, -32700, e.message); continue; }
    Promise.resolve(handle(parsed)).catch(e => error(parsed?.id ?? null, -32603, e.message));
  }
});
