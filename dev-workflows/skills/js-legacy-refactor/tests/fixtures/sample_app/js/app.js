// Main app logic.
class Widget {
  constructor(name) {
    this.name = name;
  }
}

function saveData(payload) {
  // Divergent duplicate of utils.saveData (different body) -> override candidate.
  console.log("override", payload);
  return eval("1 + 1");
}

const handler = function clickHandler(ev) {
  return new Function("return 1")();
};

document.getElementById && (window.Widget = Widget);
