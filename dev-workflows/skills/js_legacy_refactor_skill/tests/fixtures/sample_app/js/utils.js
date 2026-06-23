// Shared utilities (loaded first on every page).
var APP_VERSION = "1.0";
let cache = {};
const MAX = 10;

function init() {
  cache.ready = true;
  return APP_VERSION;
}

function saveData(payload) {
  cache.last = payload;
}

window.validateForm = function (form) {
  return !!form;
};

var formatLabel = (s) => s.trim();

implicitGlobal = 42;
