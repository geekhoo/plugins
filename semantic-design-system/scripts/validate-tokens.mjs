#!/usr/bin/env node
import { loadTokenTree, collectTokens, resolveAlias, projectPath, DEFAULT_TOKEN_DIR } from './token-utils.mjs';

// The 13 standard token types defined by the DTCG Format Module 2025.10
// (first stable release). Types outside this set are flagged as warnings rather
// than hard errors, since the spec permits tool-specific extension types.
const STANDARD_TYPES = new Set([
  'color', 'dimension', 'fontFamily', 'fontWeight', 'duration', 'cubicBezier',
  'number', 'strokeStyle', 'border', 'transition', 'shadow', 'gradient', 'typography'
]);

const tokenDir = projectPath(process.argv[2] || DEFAULT_TOKEN_DIR);
let failed = false;
const issues = [];
const warnings = [];

try {
  const { tree, files } = loadTokenTree(tokenDir);
  const { tokens, errors, aliases } = collectTokens(tree);
  issues.push(...errors);

  for (const alias of aliases) {
    if (!tokens.has(alias.to)) issues.push(`${alias.from}: unresolved alias {${alias.to}}`);
  }

  for (const token of tokens.values()) {
    try {
      resolveAlias(token.node.$value, tokens, [token.path]);
    } catch (error) {
      issues.push(`${token.path}: ${error.message}`);
    }
  }

  for (const token of tokens.values()) {
    if (token.path.startsWith('component.')) {
      const raw = JSON.stringify(token.node.$value);
      if (/\{primitive\./.test(raw)) {
        issues.push(`${token.path}: component token references primitive directly; prefer semantic alias unless intentional`);
      }
    }
    if (token.path.startsWith('semantic.color.') && /\b(white|black|gray|grey|blue|red|green|yellow)\b/i.test(token.path)) {
      issues.push(`${token.path}: semantic color path appears literal; prefer role-based naming`);
    }
    if (token.type && !STANDARD_TYPES.has(token.type)) {
      warnings.push(`${token.path}: non-standard $type "${token.type}"; DTCG 2025.10 defines ${[...STANDARD_TYPES].join(', ')}`);
    }
  }

  if (issues.length) failed = true;

  console.log(JSON.stringify({
    ok: !failed,
    tokenDir,
    files: files.length,
    tokens: tokens.size,
    aliases: aliases.length,
    issues,
    warnings
  }, null, 2));

  process.exit(failed ? 1 : 0);
} catch (error) {
  console.error(JSON.stringify({ ok: false, tokenDir, error: error.message }, null, 2));
  process.exit(1);
}
