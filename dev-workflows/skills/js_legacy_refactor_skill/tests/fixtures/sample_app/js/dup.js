// Exact duplicate of utils.init (same normalized body) -> exact/near duplicate.
function init() {
  cache.ready = true;
  return APP_VERSION;
}

// Orphan file: not referenced by index.html, only by settings.html.
function settingsOnly() {
  return MAX;
}
