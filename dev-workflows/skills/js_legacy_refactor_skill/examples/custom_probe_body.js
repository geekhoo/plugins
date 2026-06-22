// Optional browser probe body for browser_regression_probe.mjs --custom-js.
// This code runs inside the browser page after load and must return JSON-serializable data.
// Customize per app before use.
return {
  visibleButtons: Array.from(document.querySelectorAll('button')).filter(b => !!(b.offsetWidth || b.offsetHeight || b.getClientRects().length)).length,
  forms: document.querySelectorAll('form').length,
  dialogs: document.querySelectorAll('[role="dialog"], dialog').length,
  activeElementTag: document.activeElement ? document.activeElement.tagName : null
};
