// Entry so that `node --test test/` also works on Node 24+, where a bare directory argument is resolved as a
// module path instead of being scanned. On Node 22 the directory scan runs the *.test.mjs files directly.
(async () => {
  for (const f of ['map-request', 'stream', 'server', 'robust']) await import(`./${f}.test.mjs`);
})();
