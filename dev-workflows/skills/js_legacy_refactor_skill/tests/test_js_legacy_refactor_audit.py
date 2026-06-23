"""Characterization tests for js_legacy_refactor_audit.py.

These lock the tool's observable behavior (audit inventory, duplicate
classification, risk detection, brace matching, comparison verdict) so the
audit/render/compare internals can be refactored without silent regressions.
"""

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE.parent / "tools" / "js_legacy_refactor_audit.py"
FIXTURE = HERE / "fixtures" / "sample_app"


def _load_tool():
    spec = importlib.util.spec_from_file_location("jl_audit", TOOL)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["jl_audit"] = mod
    spec.loader.exec_module(mod)
    return mod


jl = _load_tool()


def _audit(tmp_path):
    return jl.audit(FIXTURE, tmp_path / "out", scan_all_js=True)


def test_summary_counts(tmp_path):
    s = _audit(tmp_path)["summary"]
    assert s["html_pages"] == 2
    assert s["js_files_scanned"] == 3
    assert s["inline_script_units"] == 2
    assert s["event_handler_attributes"] == 3
    assert s["missing_scripts"] == 1
    assert s["remote_scripts"] == 1
    assert s["duplicate_symbols"] == 5
    assert s["risk_findings"] == 5


def test_duplicate_classification(tmp_path):
    dups = {d["symbol"]: d["classification"] for d in _audit(tmp_path)["duplicates"]}
    assert dups["init"] == "exact_or_near_duplicate"
    assert dups["handler"] == "exact_or_near_duplicate"
    assert dups["saveData"] == "divergent_duplicate_or_override"
    assert dups["Widget"] == "duplicate_declaration_name"


def test_risk_and_implicit_global_detection(tmp_path):
    a = _audit(tmp_path)
    assert {r["risk"] for r in a["risks"]} == {
        "document.write", "eval", "new Function", "timer string", "top-level this",
    }
    implicit = [d["symbol"] for d in a["declarations"]
                if d["kind"] == "suspect_implicit_global_assignment"]
    assert implicit == ["implicitGlobal"]


def test_missing_and_remote_scripts(tmp_path):
    a = _audit(tmp_path)
    assert [(m["page"], m["src"]) for m in a["missing_scripts"]] == [
        ("index.html", "js/missing.js"),
    ]
    assert [m["src"] for m in a["remote_scripts"]] == ["https://cdn.example.com/lib.js"]


def test_find_matching_brace():
    src = "function f(){ if (x) { return {a:1}; } }"
    open_idx = src.index("{")
    assert jl.find_matching_brace(src, open_idx) == len(src) - 1
    # string/comment braces must not be miscounted
    assert jl.find_matching_brace('{ s = "}"; /* } */ }', 0) == 19
    assert jl.find_matching_brace("{ unterminated", 0) == -1


def test_split_decl_names_and_arity():
    assert jl.split_decl_names("a = 1, b = 2, c") == ["a", "b", "c"]
    assert jl.split_decl_names("{x, y} = obj, plain") == ["plain"]
    assert jl.arity_from_params("") == 0
    assert jl.arity_from_params("a, b, c") == 3
    assert jl.arity_from_params("a, {b, c}, d") == 3


def test_compare_identical_is_pass(tmp_path):
    _audit(tmp_path)
    audit_json = tmp_path / "out" / "audit.json"
    out = jl.compare_audits(audit_json, audit_json, tmp_path / "cmp.md")
    assert "## Status: PASS" in out


def test_compare_detects_dropped_declaration(tmp_path):
    _audit(tmp_path)
    audit_json = json.loads((tmp_path / "out" / "audit.json").read_text(encoding="utf-8"))
    after = dict(audit_json)
    after["declarations"] = [d for d in audit_json["declarations"] if d["symbol"] != "init"]
    before_p = tmp_path / "before.json"
    after_p = tmp_path / "after.json"
    before_p.write_text(json.dumps(audit_json), encoding="utf-8")
    after_p.write_text(json.dumps(after), encoding="utf-8")
    out = jl.compare_audits(before_p, after_p, None)
    assert "REVIEW REQUIRED" in out
    assert "HIGH_GLOBAL_COLLISION" in out
