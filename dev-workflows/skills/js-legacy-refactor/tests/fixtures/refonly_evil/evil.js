// Lives in a sibling directory whose name shares a string prefix with the audit
// root ("refonly" vs "refonly_evil"). A naive startswith() containment check lets
// this through; real path containment must refuse it. Never analyze this file.
function evilSymbol() {
  return "outside-the-audit-root";
}
