#!/usr/bin/env node
import fs from 'node:fs';
import { spawnSync } from 'node:child_process';
import path from 'node:path';

let input = '';
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  try {
    const event = input ? JSON.parse(input) : {};
    const filePath = event?.tool_input?.file_path || event?.tool_input?.path || '';
    const looksRelevant = /tokens?|design-system|\.css$|\.scss$|\.tsx?$|\.jsx?$/.test(filePath);
    if (!looksRelevant) return process.exit(0);

    const pluginRoot = process.env.CLAUDE_PLUGIN_ROOT || path.resolve(import.meta.dirname, '..');
    const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
    const tokenDir = process.env.CLAUDE_PLUGIN_OPTION_TOKEN_DIR || process.env.DEFAULT_TOKEN_DIR || 'tokens';
    const fullTokenDir = path.isAbsolute(tokenDir) ? tokenDir : path.join(projectDir, tokenDir);

    if (!fs.existsSync(fullTokenDir)) return process.exit(0);

    const result = spawnSync('node', [path.join(pluginRoot, 'scripts/validate-tokens.mjs'), fullTokenDir], {
      cwd: projectDir,
      encoding: 'utf8'
    });

    if (result.status !== 0) {
      console.log('semantic-design-system token validation reported issues:');
      console.log(result.stdout || result.stderr);
    }

    process.exit(0);
  } catch (error) {
    console.log(`semantic-design-system post-edit hook skipped: ${error.message}`);
    process.exit(0);
  }
});
