import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

import {
  TOKEN_FILE_RE,
  collectTokens,
  cssVarName,
  loadTokenTree,
  resolveAlias,
  stripJsonComments,
  tokenValueToCss
} from '../scripts/token-utils.mjs';

test('stripJsonComments preserves JSON strings while removing comments', () => {
  const parsed = JSON.parse(stripJsonComments(`{
    "url": "https://example.com/a//b",
    // line comment
    "hex": "#ffffff",
    /* block comment */
    "value": 1
  }`));

  assert.equal(parsed.url, 'https://example.com/a//b');
  assert.equal(parsed.hex, '#ffffff');
  assert.equal(parsed.value, 1);
});

test('collectTokens resolves aliases and formats CSS values', () => {
  const tree = {
    primitive: {
      color: {
        $type: 'color',
        brand: {
          500: {
            $value: {
              colorSpace: 'srgb',
              components: [0.05, 0.38, 0.95],
              hex: '#0d61f2'
            }
          }
        }
      },
      space: {
        $type: 'dimension',
        200: { $value: { value: 1, unit: 'rem' } }
      }
    },
    semantic: {
      color: {
        action: {
          $type: 'color',
          primary: { $value: '{primitive.color.brand.500}' }
        }
      },
      space: {
        inset: {
          $type: 'dimension',
          md: { $value: '{primitive.space.200}' }
        }
      }
    }
  };

  const { tokens, aliases, errors } = collectTokens(tree);

  assert.deepEqual(errors, []);
  assert.equal(aliases.length, 2);
  assert.equal(tokenValueToCss(resolveAlias(tokens.get('semantic.color.action.primary').node.$value, tokens)), '#0d61f2');
  assert.equal(tokenValueToCss(resolveAlias(tokens.get('semantic.space.inset.md').node.$value, tokens)), '1rem');
  assert.equal(cssVarName('semantic.color.action.primary'), '--ds-color-action-primary');
  assert.equal(cssVarName('component.button.primary.bg.default', 'acme'), '--acme-component-button-primary-bg-default');
});

test('resolveAlias reports circular references', () => {
  const { tokens } = collectTokens({
    primitive: {
      color: {
        $type: 'color',
        a: { $value: '{primitive.color.b}' },
        b: { $value: '{primitive.color.a}' }
      }
    }
  });

  assert.throws(
    () => resolveAlias(tokens.get('primitive.color.a').node.$value, tokens, ['primitive.color.a']),
    /Circular alias: primitive\.color\.a -> primitive\.color\.b -> primitive\.color\.a/
  );
});

test('loadTokenTree reads only token files', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'sds-token-utils-'));
  fs.mkdirSync(path.join(dir, 'primitive'), { recursive: true });
  fs.writeFileSync(path.join(dir, 'package.json'), '{"name":"ignored"}');
  fs.writeFileSync(path.join(dir, 'primitive', 'base.tokens.json'), JSON.stringify({
    primitive: {
      color: {
        $type: 'color',
        neutral: {
          0: { $value: '#ffffff' }
        }
      }
    }
  }));

  const { files, tree } = loadTokenTree(dir);

  assert.equal(TOKEN_FILE_RE.test(path.join(dir, 'package.json')), false);
  assert.equal(files.length, 1);
  assert.equal(tree.primitive.color.neutral[0].$value, '#ffffff');
});
