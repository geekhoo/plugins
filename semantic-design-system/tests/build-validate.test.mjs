import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

const pluginRoot = path.resolve(import.meta.dirname, '..');

function writeJson(file, payload) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(payload, null, 2));
}

function createTokenProject() {
  const projectDir = fs.mkdtempSync(path.join(os.tmpdir(), 'sds-build-validate-'));
  const tokenDir = path.join(projectDir, 'design', 'tokens');

  writeJson(path.join(tokenDir, 'primitive', 'base.tokens.json'), {
    primitive: {
      color: {
        $type: 'color',
        neutral: {
          0: { $value: { colorSpace: 'srgb', components: [1, 1, 1], hex: '#ffffff' } },
          900: { $value: { colorSpace: 'srgb', components: [0.08, 0.08, 0.08], hex: '#141414' } }
        },
        brand: {
          500: { $value: { colorSpace: 'srgb', components: [0.05, 0.38, 0.95], hex: '#0d61f2' } }
        }
      }
    }
  });

  writeJson(path.join(tokenDir, 'semantic', 'base.tokens.json'), {
    semantic: {
      color: {
        fg: {
          $type: 'color',
          default: { $value: '{primitive.color.neutral.900}' },
          inverse: { $value: '{primitive.color.neutral.0}' }
        },
        bg: {
          action: {
            primary: {
              $type: 'color',
              default: { $value: '{primitive.color.brand.500}' }
            }
          }
        }
      }
    }
  });

  writeJson(path.join(tokenDir, 'component', 'button.tokens.json'), {
    component: {
      button: {
        primary: {
          bg: {
            $type: 'color',
            default: { $value: '{semantic.color.bg.action.primary.default}' }
          },
          fg: {
            $type: 'color',
            default: { $value: '{semantic.color.fg.inverse}' }
          }
        }
      }
    }
  });

  writeJson(path.join(tokenDir, 'themes', 'dark.tokens.json'), {
    primitive: {
      color: {
        brand: {
          500: { $value: { colorSpace: 'srgb', components: [0, 0.8, 0.9], hex: '#00cce6' } }
        }
      }
    },
    semantic: {
      color: {
        fg: {
          $type: 'color',
          default: { $value: '{primitive.color.neutral.0}' },
          inverse: { $value: '{primitive.color.neutral.900}' }
        }
      }
    }
  });

  return { projectDir, tokenDir };
}

test('validate CLI accepts valid DTCG token trees', () => {
  const { projectDir } = createTokenProject();
  const stdout = execFileSync(process.execPath, [
    path.join(pluginRoot, 'scripts', 'validate-tokens.mjs'),
    'design/tokens'
  ], {
    cwd: projectDir,
    encoding: 'utf8'
  });

  const result = JSON.parse(stdout);
  assert.equal(result.ok, true);
  assert.equal(result.files, 4);
  assert.equal(result.issues.length, 0);
});

test('build CLI emits theme selectors and alias-propagated component overrides', () => {
  const { projectDir } = createTokenProject();
  const stdout = execFileSync(process.execPath, [
    path.join(pluginRoot, 'scripts', 'build-css-vars.mjs'),
    'design/tokens',
    'src/styles/tokens.css',
    'ds'
  ], {
    cwd: projectDir,
    encoding: 'utf8'
  });

  const result = JSON.parse(stdout);
  const css = fs.readFileSync(path.join(projectDir, 'src', 'styles', 'tokens.css'), 'utf8');

  assert.equal(result.ok, true);
  assert.deepEqual(result.themes, ['dark']);
  assert.match(css, /:root \{/);
  assert.match(css, /\[data-theme="dark"\] \{/);
  assert.match(css, /@media \(prefers-color-scheme: dark\)/);
  assert.match(css, /--ds-color-bg-action-primary-default: #0d61f2;/);
  assert.match(css, /--ds-color-bg-action-primary-default: #00cce6;/);
  assert.match(css, /--ds-component-button-primary-bg-default: #00cce6;/);
});

test('validate CLI warns but does not fail for non-standard DTCG extension types', () => {
  const projectDir = fs.mkdtempSync(path.join(os.tmpdir(), 'sds-validate-warning-'));
  writeJson(path.join(projectDir, 'design', 'tokens', 'semantic', 'base.tokens.json'), {
    semantic: {
      custom: {
        $type: 'asset',
        logo: { $value: 'logo.svg' }
      }
    }
  });

  const stdout = execFileSync(process.execPath, [
    path.join(pluginRoot, 'scripts', 'validate-tokens.mjs'),
    'design/tokens'
  ], {
    cwd: projectDir,
    encoding: 'utf8'
  });

  const result = JSON.parse(stdout);
  assert.equal(result.ok, true);
  assert.equal(result.issues.length, 0);
  assert.match(result.warnings[0], /non-standard \$type "asset"/);
});
