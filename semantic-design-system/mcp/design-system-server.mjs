#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { DEFAULT_TOKEN_DIR } from '../scripts/token-utils.mjs';

const pluginRoot =
  process.env.PLUGIN_ROOT ||
  process.env.CODEX_PLUGIN_ROOT ||
  process.env.CLAUDE_PLUGIN_ROOT ||
  path.resolve(import.meta.dirname, '..');
const projectDir =
  process.env.PLUGIN_PROJECT_DIR ||
  process.env.CODEX_PROJECT_DIR ||
  process.env.CLAUDE_PROJECT_DIR ||
  process.cwd();
const defaultTokenDir = DEFAULT_TOKEN_DIR;
const defaultCssOutputFile = process.env.DEFAULT_CSS_OUTPUT_FILE || 'src/styles/tokens.css';
const defaultCssPrefix = process.env.DEFAULT_CSS_PREFIX || 'ds';

function asProjectPath(value, fallback) {
  const v = value || fallback;
  return path.isAbsolute(v) ? v : path.join(projectDir, v);
}

function runNode(script, args) {
  const result = spawnSync('node', [path.join(pluginRoot, 'scripts', script), ...args], {
    cwd: projectDir,
    encoding: 'utf8'
  });
  return {
    ok: result.status === 0,
    stdout: result.stdout?.trim() || '',
    stderr: result.stderr?.trim() || '',
    status: result.status
  };
}

function writeSkeleton(outputDir, productName = 'Product') {
  const dir = asProjectPath(outputDir, defaultTokenDir);
  fs.mkdirSync(path.join(dir, 'primitive'), { recursive: true });
  fs.mkdirSync(path.join(dir, 'semantic'), { recursive: true });
  fs.mkdirSync(path.join(dir, 'component'), { recursive: true });
  fs.mkdirSync(path.join(dir, 'themes'), { recursive: true });

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

  fs.writeFileSync(path.join(dir, 'primitive/base.tokens.json'), JSON.stringify(primitive, null, 2));
  fs.writeFileSync(path.join(dir, 'semantic/base.tokens.json'), JSON.stringify(semantic, null, 2));
  fs.writeFileSync(path.join(dir, 'component/button.tokens.json'), JSON.stringify(component, null, 2));
  fs.writeFileSync(path.join(dir, 'themes/dark.tokens.json'), JSON.stringify(dark, null, 2));
  return dir;
}

const tools = [
  {
    name: 'validate_tokens',
    description: 'Validate design token files (DTCG Format Module 2025.10) for missing types, non-standard $type values, unresolved aliases, circular references, primitive leakage, and literal color naming.',
    inputSchema: {
      type: 'object',
      properties: { tokenDir: { type: 'string', description: 'Project-relative or absolute token directory. Defaults to design/tokens.' } }
    }
  },
  {
    name: 'build_css_variables',
    description: 'Build CSS custom properties from semantic and component design tokens. Theme-aware: base tokens go to :root, files under themes/ become [data-theme="<name>"] overrides, and light/dark themes also emit a prefers-color-scheme block.',
    inputSchema: {
      type: 'object',
      properties: {
        tokenDir: { type: 'string', description: 'Project-relative or absolute token directory. Defaults to design/tokens.' },
        outputFile: { type: 'string', description: 'CSS output path. Defaults to src/styles/tokens.css.' },
        prefix: { type: 'string', description: 'CSS custom-property prefix. Defaults to ds.' }
      }
    }
  },
  {
    name: 'extract_style_inventory',
    description: 'Scan a web codebase and write a JSON inventory of discovered colors, dimensions, typography, shadows, transitions, z-indexes, breakpoints, and CSS variables.',
    inputSchema: {
      type: 'object',
      properties: { rootDir: { type: 'string' }, outputFile: { type: 'string' } }
    }
  },
  {
    name: 'generate_token_skeleton',
    description: 'Create a minimal primitive/semantic/component/theme token folder skeleton. Defaults to design/tokens in the project.',
    inputSchema: {
      type: 'object',
      properties: { outputDir: { type: 'string', description: 'Token directory to create. Defaults to design/tokens.' }, productName: { type: 'string' } }
    }
  }
];

function respond(id, result) {
  process.stdout.write(JSON.stringify({ jsonrpc: '2.0', id, result }) + '\n');
}

function error(id, code, message) {
  process.stdout.write(JSON.stringify({ jsonrpc: '2.0', id, error: { code, message } }) + '\n');
}

async function handle(message) {
  if (!message.id && message.method?.startsWith('notifications/')) return;

  if (message.method === 'initialize') {
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

  if (message.method === 'tools/call') {
    const name = message.params?.name;
    const args = message.params?.arguments || {};
    let result;

    if (name === 'validate_tokens') {
      result = runNode('validate-tokens.mjs', [asProjectPath(args.tokenDir, defaultTokenDir)]);
    } else if (name === 'build_css_variables') {
      result = runNode('build-css-vars.mjs', [
        asProjectPath(args.tokenDir, defaultTokenDir),
        asProjectPath(args.outputFile, defaultCssOutputFile),
        args.prefix || defaultCssPrefix
      ]);
    } else if (name === 'extract_style_inventory') {
      result = runNode('extract-style-inventory.mjs', [
        asProjectPath(args.rootDir, '.'),
        asProjectPath(args.outputFile, '.design-system/style-inventory.json')
      ]);
    } else if (name === 'generate_token_skeleton') {
      const dir = writeSkeleton(args.outputDir || defaultTokenDir, args.productName || 'Product');
      result = { ok: true, stdout: JSON.stringify({ ok: true, outputDir: dir }, null, 2), stderr: '', status: 0 };
    } else {
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
    try { handle(JSON.parse(line)); } catch (e) { error(null, -32700, e.message); }
  }
});
