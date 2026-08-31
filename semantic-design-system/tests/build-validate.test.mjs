import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
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

// --- build failure reporting -------------------------------------------------

function runBuild(projectDir, args) {
  const result = spawnSync(process.execPath, [
    path.join(pluginRoot, 'scripts', 'build-css-vars.mjs'),
    ...args
  ], { cwd: projectDir, encoding: 'utf8' });

  return {
    status: result.status,
    json: JSON.parse((result.status === 0 ? result.stdout : result.stderr).trim())
  };
}

function projectWith(files) {
  const projectDir = fs.mkdtempSync(path.join(os.tmpdir(), 'sds-build-fail-'));
  for (const [relative, payload] of Object.entries(files)) {
    writeJson(path.join(projectDir, 'design', 'tokens', ...relative.split('/')), payload);
  }
  return projectDir;
}

const DANGLING_ALIAS_PROJECT = {
  'primitive/base.tokens.json': {
    primitive: { color: { $type: 'color', blue: { 500: { $value: '#0000ff' } } } }
  },
  'semantic/base.tokens.json': {
    semantic: {
      color: {
        $type: 'color',
        action: { $value: '{primitive.color.blue.500}' },
        broken: { $value: '{primitive.color.DOES_NOT_EXIST}' }
      }
    }
  }
};

test('build CLI fails closed on an unresolvable exposed token and writes nothing', () => {
  const projectDir = projectWith(DANGLING_ALIAS_PROJECT);
  const outputFile = path.join(projectDir, 'src', 'styles', 'tokens.css');

  const { status, json } = runBuild(projectDir, ['design/tokens', 'src/styles/tokens.css', 'ds']);

  assert.equal(status, 1);
  assert.equal(json.ok, false);
  assert.equal(json.failed, 1);
  assert.equal(json.emitted, 0);
  assert.equal(fs.existsSync(outputFile), false, 'no CSS file may be written when the build fails');

  assert.deepEqual(json.failures, [{
    layer: 'base',
    tokenPath: 'semantic.color.broken',
    kind: 'missing-reference',
    error: 'Unresolved alias: primitive.color.DOES_NOT_EXIST'
  }]);
  assert.match(json.error, /semantic\.color\.broken/);
  assert.match(json.error, /--allow-partial/);
});

test('build CLI leaves a pre-existing CSS file untouched when the build fails', () => {
  const projectDir = projectWith(DANGLING_ALIAS_PROJECT);
  const outputFile = path.join(projectDir, 'src', 'styles', 'tokens.css');
  fs.mkdirSync(path.dirname(outputFile), { recursive: true });
  fs.writeFileSync(outputFile, '/* previous good build */\n');

  const { status } = runBuild(projectDir, ['design/tokens', 'src/styles/tokens.css', 'ds']);

  assert.equal(status, 1);
  assert.equal(fs.readFileSync(outputFile, 'utf8'), '/* previous good build */\n');
});

test('build CLI --allow-partial emits the resolvable subset with accurate counts', () => {
  const projectDir = projectWith(DANGLING_ALIAS_PROJECT);
  const { status, json } = runBuild(projectDir, ['design/tokens', 'src/styles/tokens.css', 'ds', '--allow-partial']);
  const css = fs.readFileSync(path.join(projectDir, 'src', 'styles', 'tokens.css'), 'utf8');

  assert.equal(status, 0);
  assert.equal(json.ok, true);
  assert.equal(json.allowPartial, true);
  assert.equal(json.partial, true);
  assert.equal(json.emitted, 1);
  assert.equal(json.variables, 1);
  assert.equal(json.failed, 1);
  assert.equal(json.skipped, 1, 'the primitive token is not exposed, so it is skipped rather than failed');
  assert.match(css, /--ds-color-action: #0000ff;/);
  assert.doesNotMatch(css, /broken/);
});

test('build CLI classifies circular aliases and unsupported value shapes separately', () => {
  const projectDir = projectWith({
    'semantic/base.tokens.json': {
      semantic: {
        color: {
          $type: 'color',
          loop: { $value: '{semantic.color.knot}' },
          knot: { $value: '{semantic.color.loop}' }
        },
        type: {
          $type: 'typography',
          body: { $value: { fontFamily: 'Inter', fontSize: { value: 1, unit: 'rem' }, fontWeight: 400 } }
        }
      }
    }
  });

  const { status, json } = runBuild(projectDir, ['design/tokens', 'src/styles/tokens.css', 'ds']);

  assert.equal(status, 1);
  assert.equal(json.failed, 3);

  const byPath = Object.fromEntries(json.failures.map(f => [f.tokenPath, f]));
  assert.equal(byPath['semantic.color.loop'].kind, 'circular-alias');
  assert.match(byPath['semantic.color.loop'].error, /Circular alias: semantic\.color\.loop -> semantic\.color\.knot/);
  assert.equal(byPath['semantic.color.knot'].kind, 'circular-alias');
  assert.equal(byPath['semantic.type.body'].kind, 'unsupported-value-shape');
  assert.match(byPath['semantic.type.body'].error, /\$type "typography" is not supported/);
});

test('build CLI attributes a theme-only breakage to that theme, not the base', () => {
  const projectDir = projectWith({
    'primitive/base.tokens.json': {
      primitive: { color: { $type: 'color', ink: { 900: { $value: '#141414' } } } }
    },
    'semantic/base.tokens.json': {
      semantic: { color: { $type: 'color', fg: { $value: '{primitive.color.ink.900}' } } }
    },
    'themes/dark.tokens.json': {
      semantic: { color: { $type: 'color', fg: { $value: '{primitive.color.ink.MISSING_IN_DARK}' } } }
    }
  });

  const { status, json } = runBuild(projectDir, ['design/tokens', 'src/styles/tokens.css', 'ds']);

  assert.equal(status, 1);
  assert.equal(json.failed, 1);
  assert.equal(json.failures[0].layer, 'theme:dark');
  assert.equal(json.failures[0].tokenPath, 'semantic.color.fg');
  assert.equal(json.failures[0].kind, 'missing-reference');
  assert.equal(fs.existsSync(path.join(projectDir, 'src', 'styles', 'tokens.css')), false);
});

test('build CLI rejects unknown options instead of treating them as paths', () => {
  const projectDir = projectWith(DANGLING_ALIAS_PROJECT);
  const { status, json } = runBuild(projectDir, ['design/tokens', 'src/styles/tokens.css', 'ds', '--force']);

  assert.equal(status, 1);
  assert.match(json.error, /Unknown option\(s\): --force/);
});

test('a clean build reports zero failures and a matching emitted count', () => {
  const { projectDir } = createTokenProject();
  const { status, json } = runBuild(projectDir, ['design/tokens', 'src/styles/tokens.css', 'ds']);

  assert.equal(status, 0);
  assert.equal(json.failed, 0);
  assert.equal(json.partial, false);
  assert.equal(json.emitted, json.variables);
});
