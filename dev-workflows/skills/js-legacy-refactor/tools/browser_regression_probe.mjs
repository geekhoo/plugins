#!/usr/bin/env node
/**
 * Browser regression probe for legacy no-bundler HTML/JS/CSS apps.
 *
 * Requires Playwright:
 *   npm install --save-dev playwright
 *   npx playwright install chromium
 *
 * This tool snapshots console/runtime/network/global/DOM signals for HTML pages
 * before and after a refactor. It is a guardrail, not a replacement for the
 * app's real test suite or manual QA.
 */

import fs from 'node:fs';
import fsp from 'node:fs/promises';
import path from 'node:path';
import http from 'node:http';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';

function usage() {
  console.log(`
Usage:
  node tools/browser_regression_probe.mjs snapshot --root APP_ROOT [--url BASE_URL | --port 8123] [--pages index.html,a.html] --out snapshot.json [--audit audit.json] [--settle-ms 500] [--custom-js probe.js] [--store-dom]
  node tools/browser_regression_probe.mjs compare baseline.json after.json --out browser-compare.md [--ignore-dom]

Examples:
  node tools/browser_regression_probe.mjs snapshot --root . --port 8123 --pages index.html --audit .refactor_audit/baseline/audit.json --out .refactor_audit/browser-baseline.json
  node tools/browser_regression_probe.mjs compare .refactor_audit/browser-baseline.json .refactor_audit/browser-after.json --out .refactor_audit/browser-compare.md
`);
}

function parseArgs(argv) {
  const args = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (!next || next.startsWith('--')) {
        args[key] = true;
      } else {
        args[key] = next;
        i += 1;
      }
    } else {
      args._.push(a);
    }
  }
  return args;
}

function sha256(text) {
  return crypto.createHash('sha256').update(String(text), 'utf8').digest('hex');
}

function walkHtml(root) {
  const out = [];
  const ignore = new Set(['.git', '.hg', '.svn', 'node_modules', 'bower_components', '.refactor_audit', 'coverage']);
  function walk(dir) {
    for (const item of fs.readdirSync(dir, { withFileTypes: true })) {
      if (item.isDirectory()) {
        if (ignore.has(item.name) || item.name.startsWith('.')) continue;
        walk(path.join(dir, item.name));
      } else if (/\.x?html?$/i.test(item.name)) {
        out.push(path.relative(root, path.join(dir, item.name)).split(path.sep).join('/'));
      }
    }
  }
  walk(root);
  return out.sort();
}

function contentType(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const map = {
    '.html': 'text/html; charset=utf-8',
    '.htm': 'text/html; charset=utf-8',
    '.js': 'text/javascript; charset=utf-8',
    '.mjs': 'text/javascript; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.webp': 'image/webp',
    '.ico': 'image/x-icon',
    '.woff': 'font/woff',
    '.woff2': 'font/woff2',
    '.ttf': 'font/ttf',
  };
  return map[ext] || 'application/octet-stream';
}

async function startStaticServer(root, port) {
  const absRoot = path.resolve(root);
  const server = http.createServer(async (req, res) => {
    try {
      const url = new URL(req.url || '/', `http://${req.headers.host || '127.0.0.1'}`);
      let pathname = decodeURIComponent(url.pathname);
      if (pathname.endsWith('/')) pathname += 'index.html';
      const filePath = path.resolve(absRoot, '.' + pathname);
      if (!filePath.startsWith(absRoot)) {
        res.writeHead(403);
        res.end('Forbidden');
        return;
      }
      const stat = await fsp.stat(filePath).catch(() => null);
      if (!stat) {
        res.writeHead(404);
        res.end('Not found');
        return;
      }
      if (stat.isDirectory()) {
        const indexPath = path.join(filePath, 'index.html');
        const indexStat = await fsp.stat(indexPath).catch(() => null);
        if (!indexStat) {
          res.writeHead(403);
          res.end('Directory listing disabled');
          return;
        }
        res.writeHead(200, { 'Content-Type': contentType(indexPath) });
        fs.createReadStream(indexPath).pipe(res);
        return;
      }
      res.writeHead(200, { 'Content-Type': contentType(filePath) });
      fs.createReadStream(filePath).pipe(res);
    } catch (err) {
      res.writeHead(500);
      res.end(String(err && err.stack || err));
    }
  });
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(port, '127.0.0.1', resolve);
  });
  const address = server.address();
  return { server, url: `http://127.0.0.1:${address.port}` };
}

async function loadPlaywright() {
  try {
    return await import('playwright');
  } catch (err) {
    console.error('Playwright is required. Install with: npm install --save-dev playwright && npx playwright install chromium');
    throw err;
  }
}

function symbolsFromAudit(auditPath) {
  if (!auditPath) return [];
  const audit = JSON.parse(fs.readFileSync(auditPath, 'utf8'));
  const symbols = new Set();
  for (const d of audit.declarations || []) {
    if (d.kind === 'suspect_implicit_global_assignment') continue;
    if (d.symbol) symbols.add(d.symbol);
  }
  for (const page of audit.pages || []) {
    for (const ev of page.event_handlers || []) {
      const value = ev.value || '';
      const m = value.match(/\b([A-Za-z_$][\w$]*)\s*\(/);
      if (m) symbols.add(m[1]);
    }
  }
  return [...symbols].sort();
}

function toUrl(baseUrl, pagePath) {
  const clean = String(pagePath).replace(/^\/+/, '');
  return `${String(baseUrl).replace(/\/+$/, '')}/${clean}`;
}

async function snapshotPage(browser, pagePath, pageUrl, knownSymbols, options) {
  const page = await browser.newPage();
  const consoleMessages = [];
  const pageErrors = [];
  const failedRequests = [];
  const badResponses = [];

  page.on('console', msg => {
    const loc = msg.location();
    consoleMessages.push({ type: msg.type(), text: msg.text(), location: loc });
  });
  page.on('pageerror', err => {
    pageErrors.push({ message: err.message, stack: err.stack || null });
  });
  page.on('requestfailed', req => {
    failedRequests.push({ url: req.url(), method: req.method(), failure: req.failure() });
  });
  page.on('response', res => {
    const status = res.status();
    if (status >= 400) badResponses.push({ url: res.url(), status });
  });

  const started = Date.now();
  let gotoError = null;
  try {
    await page.goto(pageUrl, { waitUntil: 'load', timeout: Number(options.timeoutMs || 30000) });
  } catch (err) {
    gotoError = String(err && err.message || err);
  }
  const settleMs = Number(options.settleMs ?? 500);
  if (settleMs > 0) await page.waitForTimeout(settleMs);

  let customProbe = null;
  if (options.customJs) {
    try {
      const code = fs.readFileSync(options.customJs, 'utf8');
      customProbe = await page.evaluate(async (probeCode) => {
        // The custom file is an async function body. It must return JSON-serializable data.
        // Example content: return { buttons: document.querySelectorAll('button').length };
        const fn = new Function(`return (async () => { ${probeCode}\n })()`);
        return await fn();
      }, code);
    } catch (err) {
      customProbe = { error: String(err && err.stack || err) };
    }
  }

  const browserSnapshot = await page.evaluate((known) => {
    const previewValue = (value) => {
      const type = typeof value;
      if (value == null || type === 'string' || type === 'number' || type === 'boolean') return value;
      if (type === 'function') return `[function ${value.name || '<anonymous>'}/${value.length}]`;
      if (Array.isArray(value)) return `[array length=${value.length}]`;
      try {
        const tag = Object.prototype.toString.call(value);
        if (tag === '[object Object]') return `[object keys=${Object.keys(value).slice(0, 20).join(',')}]`;
        return tag;
      } catch {
        return '[unpreviewable]';
      }
    };
    const globals = {};
    for (const name of known) {
      let exists = false;
      let value;
      let error = null;
      try {
        exists = name in window;
        value = window[name];
      } catch (err) {
        error = String(err && err.message || err);
      }
      let desc = null;
      try {
        const d = Object.getOwnPropertyDescriptor(window, name);
        if (d) desc = {
          enumerable: !!d.enumerable,
          configurable: !!d.configurable,
          writable: 'writable' in d ? !!d.writable : undefined,
          hasGetter: typeof d.get === 'function',
          hasSetter: typeof d.set === 'function',
        };
      } catch {}
      globals[name] = {
        exists,
        own: Object.prototype.hasOwnProperty.call(window, name),
        type: typeof value,
        tag: value == null ? String(value) : Object.prototype.toString.call(value),
        functionName: typeof value === 'function' ? value.name : undefined,
        functionLength: typeof value === 'function' ? value.length : undefined,
        descriptor: desc,
        preview: previewValue(value),
        error,
      };
    }
    const body = document.body ? document.body.outerHTML : '';
    const text = document.body ? document.body.innerText : '';
    return {
      title: document.title,
      readyState: document.readyState,
      location: String(location.href),
      bodyOuterHTML: body,
      bodyText: text,
      bodyTextSample: text.slice(0, 5000),
      windowOwnKeys: Object.getOwnPropertyNames(window).sort(),
      globals,
    };
  }, knownSymbols);

  await page.close();

  return {
    page: pagePath,
    url: pageUrl,
    elapsedMs: Date.now() - started,
    gotoError,
    consoleMessages,
    consoleErrors: consoleMessages.filter(m => ['error'].includes(m.type)),
    consoleWarnings: consoleMessages.filter(m => ['warning'].includes(m.type)),
    pageErrors,
    failedRequests,
    badResponses,
    title: browserSnapshot.title,
    readyState: browserSnapshot.readyState,
    location: browserSnapshot.location,
    bodyOuterHTMLHash: sha256(browserSnapshot.bodyOuterHTML),
    bodyOuterHTMLLength: browserSnapshot.bodyOuterHTML.length,
    bodyTextHash: sha256(browserSnapshot.bodyText),
    bodyTextLength: browserSnapshot.bodyText.length,
    bodyTextSample: browserSnapshot.bodyTextSample,
    windowOwnKeysHash: sha256(JSON.stringify(browserSnapshot.windowOwnKeys)),
    windowOwnKeysCount: browserSnapshot.windowOwnKeys.length,
    knownGlobals: browserSnapshot.globals,
    customProbe,
    ...(options.storeDom ? { bodyOuterHTML: browserSnapshot.bodyOuterHTML } : {}),
  };
}

async function snapshotCommand(args) {
  const root = path.resolve(args.root || '.');
  const out = args.out;
  if (!out) throw new Error('--out is required');
  let server = null;
  let baseUrl = args.url;
  if (!baseUrl) {
    const port = args.port ? Number(args.port) : 0;
    const started = await startStaticServer(root, port);
    server = started.server;
    baseUrl = started.url;
  }
  const pages = args.pages ? String(args.pages).split(',').map(s => s.trim()).filter(Boolean) : walkHtml(root);
  const knownSymbols = symbolsFromAudit(args.audit);
  const { chromium } = await loadPlaywright();
  const browser = await chromium.launch({ headless: true });
  const snapshots = [];
  try {
    for (const p of pages) {
      const url = toUrl(baseUrl, p);
      console.log(`Snapshot ${p} -> ${url}`);
      snapshots.push(await snapshotPage(browser, p, url, knownSymbols, {
        settleMs: args['settle-ms'],
        timeoutMs: args['timeout-ms'],
        customJs: args['custom-js'],
        storeDom: !!args['store-dom'],
      }));
    }
  } finally {
    await browser.close();
    if (server) await new Promise(resolve => server.close(resolve));
  }
  const result = {
    schema: 'legacy-browser-js-refactor-browser-snapshot/v1',
    generatedAt: new Date().toISOString(),
    root,
    baseUrl,
    pages,
    knownSymbols,
    snapshots,
  };
  await fsp.mkdir(path.dirname(path.resolve(out)), { recursive: true });
  await fsp.writeFile(out, JSON.stringify(result, null, 2));
  console.log(`Wrote ${out}`);
}

function stableGlobalDescriptor(g) {
  if (!g) return null;
  return {
    exists: g.exists,
    own: g.own,
    type: g.type,
    tag: g.tag,
    functionName: g.functionName,
    functionLength: g.functionLength,
    descriptor: g.descriptor,
    preview: g.preview,
    error: g.error,
  };
}

function compareCommand(args) {
  const beforePath = args._[1];
  const afterPath = args._[2];
  if (!beforePath || !afterPath) throw new Error('compare requires baseline.json and after.json');
  const before = JSON.parse(fs.readFileSync(beforePath, 'utf8'));
  const after = JSON.parse(fs.readFileSync(afterPath, 'utf8'));
  const bPages = new Map((before.snapshots || []).map(s => [s.page, s]));
  const aPages = new Map((after.snapshots || []).map(s => [s.page, s]));
  const issues = [];
  const allPages = new Set([...bPages.keys(), ...aPages.keys()]);
  for (const page of [...allPages].sort()) {
    const b = bPages.get(page);
    const a = aPages.get(page);
    if (!b) { issues.push({ severity: 'HIGH', page, check: 'page', message: 'Page added in after snapshot.' }); continue; }
    if (!a) { issues.push({ severity: 'HIGH', page, check: 'page', message: 'Page missing in after snapshot.' }); continue; }

    const checks = [
      ['gotoError', b.gotoError, a.gotoError, 'HIGH'],
      ['pageErrors', JSON.stringify(b.pageErrors || []), JSON.stringify(a.pageErrors || []), 'HIGH'],
      ['consoleErrors', JSON.stringify(b.consoleErrors || []), JSON.stringify(a.consoleErrors || []), 'HIGH'],
      ['failedRequests', JSON.stringify(b.failedRequests || []), JSON.stringify(a.failedRequests || []), 'HIGH'],
      ['badResponses', JSON.stringify(b.badResponses || []), JSON.stringify(a.badResponses || []), 'HIGH'],
      ['title', b.title, a.title, 'MEDIUM'],
      ['readyState', b.readyState, a.readyState, 'MEDIUM'],
      ['bodyTextHash', b.bodyTextHash, a.bodyTextHash, 'MEDIUM'],
      ['customProbe', JSON.stringify(b.customProbe), JSON.stringify(a.customProbe), 'HIGH'],
    ];
    if (!args['ignore-dom']) {
      checks.push(['bodyOuterHTMLHash', b.bodyOuterHTMLHash, a.bodyOuterHTMLHash, 'MEDIUM']);
      checks.push(['bodyOuterHTMLLength', b.bodyOuterHTMLLength, a.bodyOuterHTMLLength, 'MEDIUM']);
    }
    for (const [check, bv, av, severity] of checks) {
      if (bv !== av) issues.push({ severity, page, check, message: `${check} changed.` });
    }

    const symbols = new Set([...Object.keys(b.knownGlobals || {}), ...Object.keys(a.knownGlobals || {})]);
    for (const sym of [...symbols].sort()) {
      const bg = stableGlobalDescriptor((b.knownGlobals || {})[sym]);
      const ag = stableGlobalDescriptor((a.knownGlobals || {})[sym]);
      if (JSON.stringify(bg) !== JSON.stringify(ag)) {
        issues.push({ severity: 'HIGH_GLOBAL_DELTA', page, check: `global:${sym}`, message: `Known global ${sym} changed.` });
      }
    }
  }

  const lines = [];
  lines.push('# Browser Regression Probe Comparison');
  lines.push('');
  lines.push(`Baseline: \`${beforePath}\``);
  lines.push(`After: \`${afterPath}\``);
  lines.push('');
  lines.push(`## Status: ${issues.length ? 'REVIEW REQUIRED' : 'PASS'}`);
  lines.push('');
  lines.push('| Metric | Baseline | After |');
  lines.push('|---|---:|---:|');
  lines.push(`| pages | ${(before.snapshots || []).length} | ${(after.snapshots || []).length} |`);
  lines.push(`| known symbols | ${(before.knownSymbols || []).length} | ${(after.knownSymbols || []).length} |`);
  lines.push('');
  if (issues.length) {
    lines.push('## Deltas requiring review');
    lines.push('| Severity | Page | Check | Message |');
    lines.push('|---|---|---|---|');
    for (const issue of issues) {
      lines.push(`| ${issue.severity} | ${issue.page} | ${issue.check} | ${issue.message} |`);
    }
  } else {
    lines.push('No browser deltas were detected by this probe. Existing automated tests and representative user-flow checks are still required for final sign-off.');
  }
  lines.push('');
  const output = lines.join('\n');
  if (args.out) {
    fs.mkdirSync(path.dirname(path.resolve(args.out)), { recursive: true });
    fs.writeFileSync(args.out, output);
  }
  console.log(output);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const cmd = args._[0];
  if (!cmd || args.help) { usage(); return; }
  if (cmd === 'snapshot') return await snapshotCommand(args);
  if (cmd === 'compare') return compareCommand(args);
  usage();
  throw new Error(`Unknown command: ${cmd}`);
}

main().catch(err => {
  console.error(err && err.stack || err);
  process.exit(1);
});
