#!/usr/bin/env node
import fs from 'node:fs';
import { spawnSync } from 'node:child_process';
import path from 'node:path';

// PostToolUse runs *after* the edit has landed, so this hook deliberately never
// blocks and always exits 0. What it must not do is fail silently: a validation
// failure -- or a failure of the check itself -- is reported through
// `hookSpecificOutput.additionalContext`, which is the documented channel for
// getting text in front of the model from a non-blocking PostToolUse hook.
// Plain stdout only reaches the transcript, which is why the JSON envelope is used.

const SUBPROCESS_TIMEOUT_MS = Number(process.env.DS_SUBPROCESS_TIMEOUT_MS) || 30_000;
const SUBPROCESS_MAX_BUFFER = Number(process.env.DS_SUBPROCESS_MAX_BUFFER) || 4 * 1024 * 1024;

function emit(additionalContext, systemMessage) {
  const payload = {
    hookSpecificOutput: {
      hookEventName: 'PostToolUse',
      additionalContext
    }
  };
  // `systemMessage` surfaces the same event to the user in the transcript.
  if (systemMessage) payload.systemMessage = systemMessage;
  // Exactly one JSON document on stdout: appending human-readable text after it
  // would make the whole stream unparseable and drop it back to a transcript-only
  // message that the model never sees.
  process.stdout.write(JSON.stringify(payload) + '\n');
}

let input = '';
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  let stage = 'parsing hook input';
  try {
    const event = input ? JSON.parse(input) : {};
    const filePath = event?.tool_input?.file_path || event?.tool_input?.path || event?.tool_input?.new_path || '';
    const looksRelevant = /(?:^|[\\/])design[\\/]tokens[\\/].*\.tokens(\.jsonc?)?$/.test(filePath) ||
      /\.tokens(\.jsonc?)?$/.test(filePath);
    // Nothing to check: not a token file. Stay quiet.
    if (!looksRelevant) return process.exit(0);

    stage = 'resolving plugin and project directories';
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
    // Standardized, config-free location relative to the project/working folder.
    const fullTokenDir = path.join(projectDir, 'design', 'tokens');

    // Nothing to check: this project has no standard token directory. Stay quiet.
    if (!fs.existsSync(fullTokenDir)) return process.exit(0);

    stage = 'running scripts/validate-tokens.mjs';
    const validator = path.join(pluginRoot, 'scripts/validate-tokens.mjs');
    if (!fs.existsSync(validator)) {
      emit(
        `semantic-design-system post-edit check COULD NOT RUN: validator not found at ${validator}. ` +
        'Token validation did NOT happen; do not treat the edit as validated.',
        'semantic-design-system: token validator missing'
      );
      return process.exit(0);
    }

    const result = spawnSync('node', [validator, fullTokenDir], {
      cwd: projectDir,
      encoding: 'utf8',
      timeout: SUBPROCESS_TIMEOUT_MS,
      maxBuffer: SUBPROCESS_MAX_BUFFER,
      killSignal: 'SIGKILL'
    });

    // The check itself broke (spawn failure, timeout, output overflow) -- this is
    // NOT the same as "the tokens are fine".
    if (result.error) {
      emit(
        `semantic-design-system post-edit check COULD NOT RUN while ${stage}: ${result.error.code || ''} ${result.error.message}`.trim() +
        '\nToken validation did NOT happen; do not treat the edit as validated.',
        'semantic-design-system: token validation could not run'
      );
      return process.exit(0);
    }

    if (result.signal) {
      emit(
        `semantic-design-system post-edit check COULD NOT RUN: validator terminated by signal ${result.signal}. ` +
        'Token validation did NOT happen; do not treat the edit as validated.',
        'semantic-design-system: token validation could not run'
      );
      return process.exit(0);
    }

    if (result.status !== 0) {
      const detail = (result.stdout || result.stderr || '').trim() || '(validator produced no output)';
      emit(
        `semantic-design-system token validation FAILED for ${filePath} (exit ${result.status}).\n` +
        `${detail}\nFix the reported issues in ${fullTokenDir} before relying on these tokens.`,
        'semantic-design-system: token validation failed'
      );
      return process.exit(0);
    }

    // Passed: stay quiet.
    process.exit(0);
  } catch (error) {
    // Reached only when the hook itself broke, never for "nothing to check" --
    // those paths return above without output.
    emit(
      `semantic-design-system post-edit hook ERRORED while ${stage}: ${error.message}. ` +
      'Token validation did NOT happen; do not treat the edit as validated.',
      'semantic-design-system: post-edit hook error'
    );
    process.exit(0);
  }
});
