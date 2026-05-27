#!/usr/bin/env node
import { loadTokenTree, collectTokens, resolveAlias, projectPath } from './token-utils.mjs';

const tokenDir = projectPath(process.argv[2] || process.env.DEFAULT_TOKEN_DIR || 'tokens');
let failed = false;
const issues = [];

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
  }

  if (issues.length) failed = true;

  console.log(JSON.stringify({
    ok: !failed,
    tokenDir,
    files: files.length,
    tokens: tokens.size,
    aliases: aliases.length,
    issues
  }, null, 2));

  process.exit(failed ? 1 : 0);
} catch (error) {
  console.error(JSON.stringify({ ok: false, tokenDir, error: error.message }, null, 2));
  process.exit(1);
}
