import fs from 'node:fs';
import assert from 'node:assert/strict';

export function load(name) { return fs.readFileSync(new URL('./fixtures/' + name, import.meta.url), 'utf8'); }

export function parseFrames(text) {
  return text.split('\n\n').filter(Boolean).map((b) => {
    const lines = b.split('\n');
    const event = lines.find((l) => l.startsWith('event: ')).slice(7);
    const data = JSON.parse(lines.find((l) => l.startsWith('data: ')).slice(6));
    assert.equal(data.type, event);
    return data;
  });
}
