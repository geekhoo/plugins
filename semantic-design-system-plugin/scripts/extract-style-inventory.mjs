#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { walkFiles, projectPath } from './token-utils.mjs';

const root = projectPath(process.argv[2] || '.');
const outputFile = projectPath(process.argv[3] || '.design-system/style-inventory.json');

const styleFile = f => /\.(css|scss|sass|less|tsx|ts|jsx|js|vue|svelte|html)$/.test(f);
const files = walkFiles(root, styleFile);

const patterns = {
  colors: /#(?:[0-9a-fA-F]{3,8})\b|rgba?\([^)]*\)|hsla?\([^)]*\)/g,
  dimensions: /(?:^|[\s:,(])(-?\d*\.?\d+)(px|rem|em|vh|vw|vmin|vmax|%)\b/g,
  fontSizes: /font-size\s*[:=]\s*([^;,'"}\n]+)/g,
  fontWeights: /font-weight\s*[:=]\s*([^;,'"}\n]+)/g,
  radii: /border-radius\s*[:=]\s*([^;,'"}\n]+)/g,
  shadows: /box-shadow\s*[:=]\s*([^;\n]+)/g,
  zIndex: /z-index\s*[:=]\s*(-?\d+)/g,
  transitions: /transition(?:-duration)?\s*[:=]\s*([^;\n]+)/g,
  mediaQueries: /@media[^{]+/g,
  cssVars: /var\(--[^)]+\)|--[a-zA-Z0-9_-]+\s*:/g
};

function add(map, value, file) {
  const key = String(value).trim();
  if (!key) return;
  if (!map[key]) map[key] = { count: 0, files: [] };
  map[key].count++;
  if (map[key].files.length < 8 && !map[key].files.includes(file)) map[key].files.push(file);
}

const inventory = Object.fromEntries(Object.keys(patterns).map(k => [k, {}]));

for (const file of files) {
  let text = '';
  try { text = fs.readFileSync(file, 'utf8'); } catch { continue; }
  const rel = path.relative(root, file);

  for (const [category, pattern] of Object.entries(patterns)) {
    pattern.lastIndex = 0;
    let match;
    while ((match = pattern.exec(text))) {
      add(inventory[category], match[1] && category !== 'colors' && category !== 'cssVars' ? match[0].trim() : match[0].trim(), rel);
    }
  }
}

const sorted = {};
for (const [category, values] of Object.entries(inventory)) {
  sorted[category] = Object.fromEntries(
    Object.entries(values).sort((a, b) => b[1].count - a[1].count || a[0].localeCompare(b[0]))
  );
}

const result = {
  ok: true,
  root,
  filesScanned: files.length,
  generatedAt: new Date().toISOString(),
  inventory: sorted
};

fs.mkdirSync(path.dirname(outputFile), { recursive: true });
fs.writeFileSync(outputFile, JSON.stringify(result, null, 2), 'utf8');
console.log(JSON.stringify({ ok: true, root, outputFile, filesScanned: files.length }, null, 2));
