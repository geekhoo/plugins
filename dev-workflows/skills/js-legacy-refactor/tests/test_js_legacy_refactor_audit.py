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
# ---------------------------------------------------------------------------
# --referenced-only mode
#
# The `refonly` fixture exercises script-src resolution: a script shared by two
# pages, a repeat reference inside one page, a query string, a fragment, a
# missing file, remote and protocol-relative srcs, a relative <base href>, and
# two traversal attempts. One of those traversals targets the sibling directory
# `refonly_evil`, whose name shares a string prefix with the audit root, so a
# naive startswith() containment check would let it through.
# ---------------------------------------------------------------------------

REFONLY = HERE / "fixtures" / "refonly"
EVIL = HERE / "fixtures" / "refonly_evil"


def _refonly(tmp_path, scan_all_js):
    name = "all" if scan_all_js else "ref"
    return jl.audit(REFONLY, tmp_path / name, scan_all_js=scan_all_js)


def _symbols(audit):
    return {d["symbol"] for d in audit["declarations"]}


def test_referenced_only_analyzes_every_existing_referenced_file(tmp_path):
    """Core invariant. Every referenced local path that exists on disk must be
    analyzed, not merely named in the report."""
    a = _refonly(tmp_path, scan_all_js=False)
    analyzed = set(a["analyzed_units"])
    on_disk = [p for p in a["referenced_local_js"] if (REFONLY / p).is_file()]
    assert on_disk, "fixture must reference at least one existing file"
    assert set(on_disk) <= analyzed, sorted(set(on_disk) - analyzed)
    assert set(on_disk) <= set(a["file_hashes"])


def test_referenced_only_scans_the_referenced_files(tmp_path):
    a = _refonly(tmp_path, scan_all_js=False)
    assert sorted(a["referenced_local_js"]) == [
        "assets/based.js", "js/missing.js", "js/only_index.js", "js/shared.js",
    ]
    assert a["summary"]["js_files_scanned"] == 3
    assert {"sharedSymbol", "onlyIndexSymbol", "basedSymbol"} <= _symbols(a)


def test_referenced_only_unit_ids_match_scan_all_ids(tmp_path):
    """Ids must be identical across modes so the two outputs stay comparable."""
    ref = _refonly(tmp_path, scan_all_js=False)
    every = _refonly(tmp_path, scan_all_js=True)
    assert set(ref["analyzed_units"]) < set(every["analyzed_units"])
    # The one file scan-all adds is the unreferenced orphan.
    assert set(every["analyzed_units"]) - set(ref["analyzed_units"]) == {"js/orphan.js"}
    for unit in ref["analyzed_units"]:
        assert ref["file_hashes"][unit] == every["file_hashes"][unit]


def test_shared_script_dedups_to_one_unit(tmp_path):
    """js/shared.js is referenced twice by index.html and once by about.html."""
    a = _refonly(tmp_path, scan_all_js=False)
    assert a["analyzed_units"].count("js/shared.js") == 1
    assert a["referenced_local_js"].count("js/shared.js") == 1
    shared = [d for d in a["declarations"] if d["symbol"] == "sharedSymbol"]
    assert len(shared) == 1
    assert not a["duplicates"], "dedup failure would surface as a duplicate symbol"
    srcs = [s for p in a["pages"] if p["path"] == "index.html"
            for s in p["scripts"] if s.get("src") == "js/shared.js"]
    assert len(srcs) == 2, "the page inventory still records both tags"


def test_query_string_and_fragment_srcs_resolve(tmp_path):
    a = _refonly(tmp_path, scan_all_js=False)
    by_page = {p["path"]: p for p in a["pages"]}
    index_src = next(s for s in by_page["index.html"]["scripts"]
                     if s.get("src") == "js/only_index.js?v=2")
    about_src = next(s for s in by_page["about.html"]["scripts"]
                     if s.get("src") == "js/only_index.js#frag")
    assert index_src["resolved_path"] == "js/only_index.js"
    assert about_src["resolved_path"] == "js/only_index.js"
    assert index_src["exists"] is True and about_src["exists"] is True
    assert "onlyIndexSymbol" in _symbols(a)


def test_missing_referenced_file_is_reported_but_not_analyzed(tmp_path):
    a = _refonly(tmp_path, scan_all_js=False)
    assert [(m["page"], m["src"]) for m in a["missing_scripts"]] == [
        ("index.html", "js/missing.js"),
    ]
    assert "js/missing.js" in a["referenced_local_js"]
    assert "js/missing.js" not in a["analyzed_units"]


def test_relative_base_href_is_applied(tmp_path):
    """<base href="assets/"> on base_page.html: src="based.js" is assets/based.js,
    not a sibling of the page."""
    a = _refonly(tmp_path, scan_all_js=False)
    page = next(p for p in a["pages"] if p["path"] == "base_page.html")
    script = next(s for s in page["scripts"] if s.get("src") == "based.js")
    assert script["resolution_basis"] == "base_href"
    assert script["resolved_path"] == "assets/based.js"
    assert script["exists"] is True
    assert "assets/based.js" in a["analyzed_units"]
    assert "basedSymbol" in _symbols(a)


def test_root_relative_base_href_prefers_the_directory_holding_the_file(tmp_path):
    """A "/app/"-style base href cannot be mapped onto the audit root with
    certainty, so both candidates are tried and the resolution basis is recorded."""
    a = _audit(tmp_path)
    page = next(p for p in a["pages"] if p["path"] == "settings.html")
    script = next(s for s in page["scripts"] if s.get("src") == "js/utils.js")
    assert script["resolution_basis"] == "base_href_or_page"
    assert script["resolved_path"] == "js/utils.js"
    assert script["exists"] is True
    warnings = {w["severity"] for w in a["script_attribute_warnings"]
                if w["page"] == "settings.html"}
    assert "MEDIUM_BASE_HREF" in warnings


def test_traversal_out_of_root_is_refused(tmp_path):
    a = _refonly(tmp_path, scan_all_js=False)
    assert (EVIL / "evil.js").is_file(), "the escape target must really exist"
    refused = {e["src"] for e in a["escaping_scripts"]}
    assert refused == {"../refonly_evil/evil.js", "../../../../etc/passwd"}
    assert a["summary"]["escaping_scripts"] == 2
    for entry in a["escaping_scripts"]:
        assert entry["resolution_status"] == "outside_root"
        assert entry["resolved_path"] is None
    # Refused, never sanitized into the analysis or the reference list.
    assert "evilSymbol" not in _symbols(a)
    assert not any("evil" in u for u in a["analyzed_units"])
    assert not any("evil" in p or "passwd" in p for p in a["referenced_local_js"])
    assert not any("passwd" in m.get("src", "") for m in a["missing_scripts"])
    severities = {w["severity"] for w in a["script_attribute_warnings"]}
    assert "HIGH_PATH_ESCAPE" in severities


def test_sibling_prefix_directory_is_not_inside_root():
    """Guards the containment rule itself: string prefixes are not containment."""
    root = REFONLY.resolve()
    assert jl.is_within_root((root / "js" / "shared.js").resolve(), root)
    assert not jl.is_within_root((EVIL / "evil.js").resolve(), root)
    assert str((EVIL / "evil.js").resolve()).startswith(str(root))


def test_remote_scripts_stay_excluded(tmp_path):
    a = _refonly(tmp_path, scan_all_js=False)
    assert sorted(s["src"] for s in a["remote_scripts"]) == [
        "//cdn.example.com/proto-relative.js",
        "https://cdn.example.com/remote.js",
    ]
    for entry in a["remote_scripts"]:
        assert entry["resolved_path"] is None
    assert not any("cdn.example.com" in u for u in a["analyzed_units"])
    assert not any("cdn.example.com" in p for p in a["referenced_local_js"])


def test_inline_scripts_still_analyzed_in_referenced_only(tmp_path):
    a = _refonly(tmp_path, scan_all_js=False)
    assert a["summary"]["inline_script_units"] == 2
    assert {"indexInlineFlag", "aboutInlineFlag"} <= _symbols(a)


def test_orphan_detection_is_honest_per_mode(tmp_path):
    every = _refonly(tmp_path, scan_all_js=True)
    assert every["scan_mode"] == "all_js"
    assert every["orphan_detection"] == "complete"
    assert every["orphan_js"] == ["js/orphan.js"]
    assert every["summary"]["orphan_js_files"] == 1

    ref = _refonly(tmp_path, scan_all_js=False)
    assert ref["scan_mode"] == "referenced_only"
    assert ref["orphan_detection"] == "unavailable_referenced_only"
    assert ref["summary"]["orphan_js_files"] is None
    report = (tmp_path / "ref" / "report.md").read_text(encoding="utf-8")
    assert "Orphan JS detection: not available" in report
    assert "orphan js files: **not available**" in report


def test_referenced_only_report_lists_refusals(tmp_path):
    _refonly(tmp_path, scan_all_js=False)
    report = (tmp_path / "ref" / "report.md").read_text(encoding="utf-8")
    assert "## Refused script references" in report
    assert "../refonly_evil/evil.js" in report


def test_compare_flags_scan_mode_mismatch(tmp_path):
    _refonly(tmp_path, scan_all_js=True)
    _refonly(tmp_path, scan_all_js=False)
    out = jl.compare_audits(tmp_path / "all" / "audit.json",
                            tmp_path / "ref" / "audit.json", None)
    assert "REVIEW REQUIRED" in out
    assert "scan_mode" in out


def test_compare_survives_a_referenced_only_pair(tmp_path):
    _refonly(tmp_path, scan_all_js=False)
    audit_json = tmp_path / "ref" / "audit.json"
    out = jl.compare_audits(audit_json, audit_json, tmp_path / "cmp.md")
    assert "## Status: PASS" in out


def test_cli_referenced_only_round_trip(tmp_path, capsys):
    assert jl.main(["audit", str(REFONLY), "--out", str(tmp_path / "a"),
                    "--referenced-only"]) == 0
    assert jl.main(["audit", str(REFONLY), "--out", str(tmp_path / "b"),
                    "--referenced-only"]) == 0
    assert jl.main(["compare", str(tmp_path / "a" / "audit.json"),
                    str(tmp_path / "b" / "audit.json"),
                    "--out", str(tmp_path / "cmp.md")]) == 0
    assert "## Status: PASS" in (tmp_path / "cmp.md").read_text(encoding="utf-8")
    assert json.loads((tmp_path / "a" / "audit.json").read_text(
        encoding="utf-8"))["summary"]["js_files_scanned"] == 3


def test_base_dir_candidates_variants():
    root = REFONLY.resolve()
    page = root / "sub" / "page.html"
    assert jl.base_dir_candidates(page, root, []) == ("page_dir", [page.parent])
    assert jl.base_dir_candidates(page, root, [{"href": "assets/"}]) == (
        "base_href", [page.parent / "assets"])
    assert jl.base_dir_candidates(page, root, [{"href": "assets/x.html"}]) == (
        "base_href", [page.parent / "assets"])
    # A base href naming a file next to the page leaves the base dir at the page dir.
    assert jl.base_dir_candidates(page, root, [{"href": "x.html"}]) == (
        "base_href", [page.parent])
    basis, bases = jl.base_dir_candidates(page, root, [{"href": "/app/"}])
    assert basis == "base_href_or_page" and bases == [root / "app", page.parent]
    assert jl.base_dir_candidates(page, root, [{"href": "/"}]) == (
        "base_href_or_page", [root, page.parent])
    assert jl.base_dir_candidates(page, root, [{"href": "https://cdn.example.com/a/"}]) == (
        "remote_base_href", [])
    # Only the first base href counts, per the HTML spec.
    assert jl.base_dir_candidates(page, root, [{"href": "one/"}, {"href": "two/"}]) == (
        "base_href", [page.parent / "one"])


def test_remote_base_href_makes_relative_srcs_remote(tmp_path):
    app = tmp_path / "app"
    (app / "js").mkdir(parents=True)
    (app / "js" / "local.js").write_text("function localSymbol() {}\n", encoding="utf-8")
    (app / "page.html").write_text(
        '<html><head><base href="https://cdn.example.com/app/">'
        '<script src="js/local.js"></script></head><body></body></html>\n',
        encoding="utf-8")
    a = jl.audit(app, tmp_path / "out", scan_all_js=False)
    assert a["referenced_local_js"] == []
    assert a["analyzed_units"] == []
    assert [s["src"] for s in a["remote_scripts"]] == ["js/local.js"]
    assert a["remote_scripts"][0]["resolution_status"] == "remote"


def test_root_relative_src_resolves_against_the_audit_root(tmp_path):
    app = tmp_path / "app"
    (app / "js").mkdir(parents=True)
    (app / "js" / "root_rel.js").write_text("function rootRelSymbol() {}\n", encoding="utf-8")
    (app / "deep").mkdir()
    (app / "deep" / "page.html").write_text(
        '<html><head><script src="/js/root_rel.js"></script></head><body></body></html>\n',
        encoding="utf-8")
    a = jl.audit(app, tmp_path / "out", scan_all_js=False)
    script = a["pages"][0]["scripts"][0]
    assert script["resolution_basis"] == "root_relative_src"
    assert script["resolved_path"] == "js/root_rel.js"
    assert a["analyzed_units"] == ["js/root_rel.js"]
    assert "rootRelSymbol" in _symbols(a)


def test_directory_and_empty_srcs_do_not_crash(tmp_path):
    app = tmp_path / "app"
    (app / "js").mkdir(parents=True)
    (app / "page.html").write_text(
        '<html><head><script src="js/"></script><script src=""></script>'
        '<script src="js"></script></head><body></body></html>\n',
        encoding="utf-8")
    a = jl.audit(app, tmp_path / "out", scan_all_js=False)
    assert a["analyzed_units"] == []
    # "js/" and "" name no file at all; "js" is a directory inside the root, so it
    # is reported the same way a missing file is - referenced, but not analyzable.
    assert {e["src"] for e in a["escaping_scripts"]} == {"js/", ""}
    assert a["referenced_local_js"] == ["js"]
    assert [m["src"] for m in a["missing_scripts"]] == ["js"]
