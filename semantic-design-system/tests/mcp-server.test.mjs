import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import readline from 'node:readline';
import test from 'node:test';

const pluginRoot = path.resolve(import.meta.dirname, '..');

function startServer(projectDir, { codex = false, env = {} } = {}) {
  const config = JSON.parse(fs.readFileSync(path.join(pluginRoot, '.codex-plugin', 'mcp.json'), 'utf8'))
    .mcpServers['design-system-tools'];
  const child = spawn(process.execPath, codex ? config.args : [path.join(pluginRoot, 'mcp', 'design-system-server.mjs')], {
    cwd: codex ? path.resolve(pluginRoot, config.cwd) : projectDir,
    env: {
      ...process.env,
      PLUGIN_ROOT: pluginRoot,
      PLUGIN_PROJECT_DIR: codex ? '' : projectDir,
      CODEX_PROJECT_DIR: '',
      CLAUDE_PROJECT_DIR: '',
      DEFAULT_CSS_OUTPUT_FILE: 'src/styles/tokens.css',
      DEFAULT_CSS_PREFIX: 'ds',
      ...env
    },
    stdio: ['pipe', 'pipe', 'pipe']
  });

  const pending = new Map();
  const stderr = [];
  const lines = readline.createInterface({ input: child.stdout });
  let nextId = 1;

  child.stderr.on('data', chunk => stderr.push(chunk.toString('utf8')));
  child.on('exit', code => {
    for (const { reject } of pending.values()) {
      reject(new Error(`MCP server exited with code ${code}: ${stderr.join('')}`));
    }
    pending.clear();
  });

  lines.on('line', line => {
    const message = JSON.parse(line);
    const waiter = pending.get(message.id);
    if (!waiter) return;
    pending.delete(message.id);
    waiter.resolve(message);
  });

  function request(method, params = {}) {
    const id = nextId++;
    const message = { jsonrpc: '2.0', id, method, params };
    child.stdin.write(`${JSON.stringify(message)}\n`);
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        pending.delete(id);
        reject(new Error(`Timed out waiting for ${method}: ${stderr.join('')}`));
      }, 5000);
      pending.set(id, {
        resolve: value => {
          clearTimeout(timeout);
          resolve(value);
        },
        reject
      });
    });
  }

  return {
    request,
    close() {
      child.kill();
      lines.close();
    }
  };
}

test('MCP server lists tools and runs skeleton, validate, and build calls', async () => {
  const projectDir = fs.mkdtempSync(path.join(os.tmpdir(), 'sds-mcp-'));
  const server = startServer(projectDir);

  try {
    const initialized = await server.request('initialize', { protocolVersion: '2024-11-05' });
    assert.equal(initialized.result.serverInfo.name, 'design-system-tools');

    const listed = await server.request('tools/list');
    assert.deepEqual(
      listed.result.tools.map(tool => tool.name).sort(),
      ['build_css_variables', 'extract_style_inventory', 'generate_token_skeleton', 'validate_tokens']
    );

    const skeleton = await server.request('tools/call', {
      name: 'generate_token_skeleton',
      arguments: { outputDir: 'design/tokens', productName: 'MCP Test' }
    });
    assert.equal(skeleton.result.isError, false);
    assert.equal(fs.existsSync(path.join(projectDir, 'design', 'tokens', 'primitive', 'base.tokens.json')), true);

    const validate = await server.request('tools/call', {
      name: 'validate_tokens',
      arguments: { tokenDir: 'design/tokens' }
    });
    assert.equal(validate.result.isError, false);

    const build = await server.request('tools/call', {
      name: 'build_css_variables',
      arguments: {
        tokenDir: 'design/tokens',
        outputFile: 'src/styles/tokens.css',
        prefix: 'ds'
      }
    });
    assert.equal(build.result.isError, false);
    assert.equal(fs.existsSync(path.join(projectDir, 'src', 'styles', 'tokens.css')), true);
  } finally {
    server.close();
  }
});

test('Codex launch resolves bundled scripts and requires explicit project paths', async () => {
  const projectDir = fs.mkdtempSync(path.join(os.tmpdir(), 'sds-codex-'));
  const server = startServer(projectDir, {
    codex: true,
    env: { PLUGIN_ROOT: path.join(projectDir, 'another-plugin') }
  });
  const tokenDir = path.join(projectDir, 'design', 'tokens');

  try {
    const initialized = await server.request('initialize', { protocolVersion: '2024-11-05' });
    assert.equal(initialized.result.serverInfo.name, 'design-system-tools');

    const missingProject = await server.request('tools/call', {
      name: 'generate_token_skeleton', arguments: {}
    });
    assert.equal(missingProject.error.code, -32602);
    assert.match(missingProject.error.message, /absolute path|project directory/i);

    const skeleton = await server.request('tools/call', {
      name: 'generate_token_skeleton', arguments: { outputDir: tokenDir }
    });
    assert.equal(skeleton.result.isError, false);
    const validate = await server.request('tools/call', {
      name: 'validate_tokens', arguments: { tokenDir }
    });
    assert.equal(validate.result.isError, false);
    const outputFile = path.join(projectDir, 'tokens.css');
    const build = await server.request('tools/call', {
      name: 'build_css_variables', arguments: { tokenDir, outputFile }
    });
    assert.equal(build.result.isError, false);
    assert.equal(fs.existsSync(outputFile), true);
  } finally {
    server.close();
  }
});
