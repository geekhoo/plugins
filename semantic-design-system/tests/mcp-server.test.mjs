import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import readline from 'node:readline';
import test from 'node:test';

const pluginRoot = path.resolve(import.meta.dirname, '..');

function startServer(projectDir) {
  const child = spawn(process.execPath, [path.join(pluginRoot, 'mcp', 'design-system-server.mjs')], {
    cwd: projectDir,
    env: {
      ...process.env,
      PLUGIN_ROOT: pluginRoot,
      PLUGIN_PROJECT_DIR: projectDir,
      DEFAULT_CSS_OUTPUT_FILE: 'src/styles/tokens.css',
      DEFAULT_CSS_PREFIX: 'ds'
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

// --- path containment, no-clobber, and tool annotations ---------------------

async function callTool(server, name, args) {
  const message = await server.request('tools/call', { name, arguments: args });
  return { isError: message.result.isError, text: message.result.content[0].text };
}

test('MCP tool annotations describe what each tool actually does', async () => {
  const projectDir = fs.mkdtempSync(path.join(os.tmpdir(), 'sds-mcp-annotations-'));
  const server = startServer(projectDir);

  try {
    await server.request('initialize', { protocolVersion: '2025-06-18' });
    const listed = await server.request('tools/list');
    const byName = Object.fromEntries(listed.result.tools.map(t => [t.name, t.annotations]));

    // validate_tokens is the only tool that touches nothing on disk.
    assert.equal(byName.validate_tokens.readOnlyHint, true);
    assert.equal(byName.validate_tokens.destructiveHint, false);

    // Everything else writes a file and can overwrite an existing one, so none
    // of them may claim readOnlyHint.
    for (const name of ['build_css_variables', 'extract_style_inventory', 'generate_token_skeleton']) {
      assert.equal(byName[name].readOnlyHint, false, `${name} writes files`);
      assert.equal(byName[name].destructiveHint, true, `${name} can overwrite files`);
    }
  } finally {
    server.close();
  }
});

test('MCP server refuses paths that escape the workspace root', async () => {
  const projectDir = fs.mkdtempSync(path.join(os.tmpdir(), 'sds-mcp-escape-'));
  const outside = fs.mkdtempSync(path.join(os.tmpdir(), 'sds-mcp-outside-'));
  fs.mkdirSync(path.join(outside, 'primitive'), { recursive: true });
  fs.writeFileSync(
    path.join(outside, 'primitive', 'x.tokens.json'),
    JSON.stringify({ primitive: { color: { $type: 'color', a: { $value: '#ffffff' } } } })
  );

  const tokenDir = path.join(projectDir, 'design', 'tokens', 'primitive');
  fs.mkdirSync(tokenDir, { recursive: true });
  fs.writeFileSync(
    path.join(tokenDir, 'base.tokens.json'),
    JSON.stringify({ primitive: { color: { $type: 'color', a: { $value: '#ffffff' } } } })
  );

  const server = startServer(projectDir);

  try {
    await server.request('initialize', { protocolVersion: '2025-06-18' });

    const ok = await callTool(server, 'validate_tokens', { tokenDir: 'design/tokens' });
    assert.equal(ok.isError, false, 'a legitimate in-root path must still work');

    const absolute = await callTool(server, 'validate_tokens', { tokenDir: outside });
    assert.equal(absolute.isError, true);
    assert.match(absolute.text, /Path escapes the allowed read root/);

    const traversal = await callTool(server, 'validate_tokens', { tokenDir: '../../elsewhere' });
    assert.equal(traversal.isError, true);
    assert.match(traversal.text, /Path escapes the allowed read root/);

    // A sibling directory sharing the root's name as a prefix. A naive
    // startsWith(root) containment check would wrongly allow this.
    const siblingPrefix = await callTool(server, 'validate_tokens', { tokenDir: `${projectDir}-evil` });
    assert.equal(siblingPrefix.isError, true);
    assert.match(siblingPrefix.text, /Path escapes the allowed read root/);

    const write = await callTool(server, 'build_css_variables', {
      tokenDir: 'design/tokens',
      outputFile: path.join(outside, 'stolen.css')
    });
    assert.equal(write.isError, true);
    assert.match(write.text, /Path escapes the allowed write root/);
    assert.equal(fs.existsSync(path.join(outside, 'stolen.css')), false);
  } finally {
    server.close();
  }
});

test('MCP server refuses a symlinked path that resolves outside the root', async () => {
  const projectDir = fs.mkdtempSync(path.join(os.tmpdir(), 'sds-mcp-symlink-'));
  const outside = fs.mkdtempSync(path.join(os.tmpdir(), 'sds-mcp-symlink-target-'));
  const link = path.join(projectDir, 'linked-tokens');

  try {
    // 'junction' works on Windows without elevation; 'dir' elsewhere.
    fs.symlinkSync(outside, link, process.platform === 'win32' ? 'junction' : 'dir');
  } catch {
    return; // no permission to create links in this environment
  }

  const server = startServer(projectDir);

  try {
    await server.request('initialize', { protocolVersion: '2025-06-18' });
    const escaped = await callTool(server, 'validate_tokens', { tokenDir: 'linked-tokens' });
    assert.equal(escaped.isError, true);
    assert.match(escaped.text, /Path escapes the allowed read root/);
  } finally {
    server.close();
  }
});

test('generate_token_skeleton refuses to clobber existing token files without force', async () => {
  const projectDir = fs.mkdtempSync(path.join(os.tmpdir(), 'sds-mcp-clobber-'));
  const server = startServer(projectDir);
  const userFile = path.join(projectDir, 'design', 'tokens', 'semantic', 'base.tokens.json');

  try {
    await server.request('initialize', { protocolVersion: '2025-06-18' });

    const first = await callTool(server, 'generate_token_skeleton', { outputDir: 'design/tokens' });
    assert.equal(first.isError, false);
    const firstResult = JSON.parse(first.text);
    assert.equal(firstResult.written.length, 4);
    assert.deepEqual(firstResult.overwritten, []);

    const authored = '{"semantic":{"color":{"$type":"color","mine":{"$value":"#abcdef"}}}}';
    fs.writeFileSync(userFile, authored);

    const second = await callTool(server, 'generate_token_skeleton', { outputDir: 'design/tokens' });
    assert.equal(second.isError, true);
    const secondResult = JSON.parse(second.text);
    assert.equal(secondResult.ok, false);
    assert.deepEqual(secondResult.written, []);
    assert.equal(secondResult.skipped.length, 4);
    assert.match(secondResult.error, /Refusing to overwrite/);
    assert.equal(fs.readFileSync(userFile, 'utf8'), authored, 'the user file must be untouched');

    const forced = await callTool(server, 'generate_token_skeleton', { outputDir: 'design/tokens', force: true });
    assert.equal(forced.isError, false);
    const forcedResult = JSON.parse(forced.text);
    assert.equal(forcedResult.overwritten.length, 4);
    assert.notEqual(fs.readFileSync(userFile, 'utf8'), authored);
  } finally {
    server.close();
  }
});
