#!/usr/bin/env python3
"""
Legacy Browser JavaScript Refactor Audit Tool

Dependency-free static scanner for no-bundler HTML/JS/CSS apps. It inventories
HTML script loading order, inline scripts, declarations, duplicate symbols, and
high-risk patterns before/after a no-regression JavaScript refactor.

This is intentionally conservative. It over-reports risks rather than missing
load-order or global-scope hazards.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as _dt
import hashlib
import html.parser
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import unquote, urlparse

IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "bower_components",
    "vendor",
    "dist",
    "build",
    ".refactor_audit",
    "coverage",
    "__pycache__",
}

JS_EXTENSIONS = {".js", ".mjs", ".cjs"}
HTML_EXTENSIONS = {".html", ".htm", ".xhtml"}

IDENT = r"[A-Za-z_$][\w$]*"
FUNCTION_DECL_RE = re.compile(rf"\bfunction\s+({IDENT})\s*\(([^)]*)\)\s*\{{", re.M)
CLASS_DECL_RE = re.compile(rf"\bclass\s+({IDENT})\b", re.M)
WINDOW_ASSIGN_RE = re.compile(rf"\b(?:window|globalThis|self)\.({IDENT})\s*=", re.M)
FUNCTION_ASSIGN_RE = re.compile(
    rf"(?:(?:\bvar|\blet|\bconst)\s+|\b(?:window|globalThis|self)\.|^|[;{{}}\n]\s*)"
    rf"({IDENT})\s*=\s*(?:async\s+)?function\s*(?:{IDENT})?\s*\(([^)]*)\)\s*\{{",
    re.M,
)
ARROW_ASSIGN_RE = re.compile(
    rf"(?:\bvar|\blet|\bconst)\s+({IDENT})\s*=\s*(?:async\s*)?(?:\([^)]*\)|{IDENT})\s*=>",
    re.M,
)
VAR_DECL_RE = re.compile(rf"\b(var|let|const)\s+([^;\n]+)", re.M)
POSSIBLE_ASSIGN_RE = re.compile(rf"(?<![\w$.])({IDENT})\s*=(?!=|>)", re.M)
EVENT_ATTR_RE = re.compile(r"^on[a-z0-9_:-]+$", re.I)

RISK_PATTERNS: List[Tuple[str, re.Pattern[str], str]] = [
    ("document.currentScript", re.compile(r"\bdocument\.currentScript\b"), "Moving or externalizing this code can change currentScript."),
    ("document.write", re.compile(r"\bdocument\.write\s*\("), "Parser-timing side effect; moving code can change DOM output."),
    ("eval", re.compile(r"\beval\s*\("), "Dynamic code prevents confident static dependency analysis."),
    ("new Function", re.compile(r"\bnew\s+Function\s*\("), "Dynamic code prevents confident static dependency analysis."),
    ("dynamic import", re.compile(r"\bimport\s*\("), "Dynamic module import changes load graph at runtime."),
    ("dynamic script element", re.compile(r"createElement\s*\(\s*['\"]script['\"]\s*\)", re.I), "Runtime script insertion can hide dependencies."),
    ("script append", re.compile(r"appendChild\s*\(\s*[^)]*script", re.I), "Runtime script insertion can hide dependencies."),
    ("timer string", re.compile(r"\bset(?:Timeout|Interval)\s*\(\s*['\"]", re.I), "String timers depend on global names."),
    ("string global dispatch", re.compile(r"\b(?:window|globalThis|self)\s*\["), "Dynamic global lookup depends on exact exported names."),
    ("prototype mutation", re.compile(rf"\b{IDENT}\.prototype\.{IDENT}\s*="), "Prototype mutation is global side-effectful."),
    ("top-level this", re.compile(r"(^|[;\n])\s*this\b", re.M), "Top-level this differs in modules/strict wrappers."),
]


@dataclasses.dataclass
class ScriptTag:
    index: int
    line: int
    attrs: Dict[str, str]
    content: str


class HTMLInventoryParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.scripts: List[ScriptTag] = []
        self.event_handlers: List[Dict[str, Any]] = []
        self.base_hrefs: List[Dict[str, Any]] = []
        self._in_script = False
        self._script_attrs: Dict[str, str] = {}
        self._script_line = 0
        self._script_buf: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        attr_map = {k.lower(): (v if v is not None else "") for k, v in attrs}
        line, _ = self.getpos()
        if tag.lower() == "base" and "href" in attr_map:
            self.base_hrefs.append({"line": line, "href": attr_map.get("href", "")})
        for name, value in attr_map.items():
            if EVENT_ATTR_RE.match(name):
                self.event_handlers.append({
                    "tag": tag.lower(),
                    "attribute": name,
                    "value": value,
                    "line": line,
                })
        if tag.lower() == "script":
            self._in_script = True
            self._script_attrs = attr_map
            self._script_line = line
            self._script_buf = []

    def handle_data(self, data: str) -> None:
        if self._in_script:
            self._script_buf.append(data)

    def handle_entityref(self, name: str) -> None:
        if self._in_script:
            self._script_buf.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if self._in_script:
            self._script_buf.append(f"&#{name};")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._in_script:
            self.scripts.append(ScriptTag(
                index=len(self.scripts),
                line=self._script_line,
                attrs=self._script_attrs,
                content="".join(self._script_buf),
            ))
            self._in_script = False
            self._script_attrs = {}
            self._script_line = 0
            self._script_buf = []


def read_text(path: Path) -> str:
    data = path.read_bytes()
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def normalize_js_fragment(text: str) -> str:
    # Conservative normalized hash: removes comments and whitespace. This is not a parser.
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//[^\n\r]*", "", text)
    text = re.sub(r"\s+", "", text)
    return text


def is_probably_javascript_script(attrs: Dict[str, str]) -> bool:
    typ = attrs.get("type", "").strip().lower()
    if typ in ("", "text/javascript", "application/javascript", "application/ecmascript", "text/ecmascript", "module"):
        return True
    if "javascript" in typ or typ.endswith("/ecmascript"):
        return True
    return False


def is_remote_src(src: str) -> bool:
    parsed = urlparse(src)
    return bool(parsed.scheme and parsed.scheme not in ("file",)) or src.startswith("//")


def strip_url_query_fragment(src: str) -> str:
    parsed = urlparse(src)
    path = parsed.path if parsed.scheme else src.split("?", 1)[0].split("#", 1)[0]
    return unquote(path)


def relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def walk_files(root: Path, extensions: set[str]) -> List[Path]:
    results: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith(".")]
        current = Path(dirpath)
        for filename in filenames:
            path = current / filename
            if path.suffix.lower() in extensions:
                results.append(path)
    return sorted(results)


def find_matching_brace(text: str, open_brace_index: int) -> int:
    """Return matching closing brace index or -1. Handles common strings/comments approximately."""
    depth = 0
    i = open_brace_index
    n = len(text)
    in_string: Optional[str] = None
    in_regex = False
    in_line_comment = False
    in_block_comment = False
    escaped = False
    while i < n:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if in_line_comment:
            if ch in "\r\n":
                in_line_comment = False
            i += 1
            continue
        if in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == in_string:
                in_string = None
            i += 1
            continue
        if ch == "/" and nxt == "/":
            in_line_comment = True
            i += 2
            continue
        if ch == "/" and nxt == "*":
            in_block_comment = True
            i += 2
            continue
        if ch in ("'", '"', "`"):
            in_string = ch
            i += 1
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def split_decl_names(decl_text: str) -> List[str]:
    # Extract simple identifiers from a var/let/const declaration list. Destructuring is ignored.
    names: List[str] = []
    depth = 0
    token = []
    parts: List[str] = []
    for ch in decl_text:
        if ch in "([{":
            depth += 1
        elif ch in ")]}" and depth > 0:
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(token))
            token = []
        else:
            token.append(ch)
    if token:
        parts.append("".join(token))
    for part in parts:
        part = part.strip()
        if not part or part[0] in "[{":
            continue
        m = re.match(rf"({IDENT})\b", part)
        if m:
            names.append(m.group(1))
    return names


def arity_from_params(params: str) -> int:
    params = params.strip()
    if not params:
        return 0
    # Count parameters before first rest/default destructuring ambiguity conservatively.
    depth = 0
    count = 1
    for ch in params:
        if ch in "([{":
            depth += 1
        elif ch in ")]}" and depth > 0:
            depth -= 1
        elif ch == "," and depth == 0:
            count += 1
    return count


def line_for_index(text: str, idx: int) -> int:
    return text.count("\n", 0, idx) + 1


def collect_declarations(unit_id: str, text: str, source_kind: str) -> List[Dict[str, Any]]:
    declarations: List[Dict[str, Any]] = []
    declared_names: set[str] = set()

    for m in FUNCTION_DECL_RE.finditer(text):
        name = m.group(1)
        params = m.group(2)
        open_idx = m.end() - 1
        close_idx = find_matching_brace(text, open_idx)
        body = text[m.start(): close_idx + 1] if close_idx >= 0 else text[m.start(): m.end()]
        body_norm = normalize_js_fragment(body)
        declarations.append({
            "symbol": name,
            "kind": "function_decl",
            "unit": unit_id,
            "source_kind": source_kind,
            "line": line_for_index(text, m.start()),
            "arity": arity_from_params(params),
            "body_hash": sha256_text(body_norm),
            "source_hash": sha256_text(body),
        })
        declared_names.add(name)

    for m in FUNCTION_ASSIGN_RE.finditer(text):
        name = m.group(1)
        params = m.group(2)
        open_idx = m.end() - 1
        close_idx = find_matching_brace(text, open_idx)
        body = text[m.start(): close_idx + 1] if close_idx >= 0 else text[m.start(): m.end()]
        declarations.append({
            "symbol": name,
            "kind": "function_assignment",
            "unit": unit_id,
            "source_kind": source_kind,
            "line": line_for_index(text, m.start()),
            "arity": arity_from_params(params),
            "body_hash": sha256_text(normalize_js_fragment(body)),
            "source_hash": sha256_text(body),
        })
        declared_names.add(name)

    for m in ARROW_ASSIGN_RE.finditer(text):
        name = m.group(1)
        declarations.append({
            "symbol": name,
            "kind": "arrow_assignment",
            "unit": unit_id,
            "source_kind": source_kind,
            "line": line_for_index(text, m.start()),
            "arity": None,
            "body_hash": None,
            "source_hash": None,
        })
        declared_names.add(name)

    for m in CLASS_DECL_RE.finditer(text):
        name = m.group(1)
        declarations.append({
            "symbol": name,
            "kind": "class_decl",
            "unit": unit_id,
            "source_kind": source_kind,
            "line": line_for_index(text, m.start()),
            "arity": None,
            "body_hash": None,
            "source_hash": None,
        })
        declared_names.add(name)

    for m in VAR_DECL_RE.finditer(text):
        kind = m.group(1)
        for name in split_decl_names(m.group(2)):
            declarations.append({
                "symbol": name,
                "kind": f"{kind}_decl",
                "unit": unit_id,
                "source_kind": source_kind,
                "line": line_for_index(text, m.start()),
                "arity": None,
                "body_hash": None,
                "source_hash": None,
            })
            declared_names.add(name)

    for m in WINDOW_ASSIGN_RE.finditer(text):
        name = m.group(1)
        line = line_for_index(text, m.start())
        # Avoid double-counting `window.foo = function (...) {}` as both a function
        # assignment and a generic explicit global assignment.
        if any(d["symbol"] == name and d["unit"] == unit_id and d["line"] == line and d["kind"] == "function_assignment" for d in declarations):
            declared_names.add(name)
            continue
        declarations.append({
            "symbol": name,
            "kind": "explicit_global_assignment",
            "unit": unit_id,
            "source_kind": source_kind,
            "line": line,
            "arity": None,
            "body_hash": None,
            "source_hash": None,
        })
        declared_names.add(name)

    # Suspect unqualified assignments. Over-reports; useful for investigation.
    assignment_skip = {
        "if", "for", "while", "switch", "return", "var", "let", "const", "function", "class",
        "case", "throw", "new", "typeof", "delete", "void", "yield", "await", "else", "do",
    }
    for m in POSSIBLE_ASSIGN_RE.finditer(text):
        name = m.group(1)
        start = m.start(1)
        before = text[max(0, start - 30):start]
        if name in assignment_skip or name in declared_names:
            continue
        if re.search(r"(?:var|let|const)\s+$", before):
            continue
        if before.rstrip().endswith((".", "?.")):
            continue
        declarations.append({
            "symbol": name,
            "kind": "suspect_implicit_global_assignment",
            "unit": unit_id,
            "source_kind": source_kind,
            "line": line_for_index(text, m.start()),
            "arity": None,
            "body_hash": None,
            "source_hash": None,
        })

    return declarations


def collect_risks(unit_id: str, text: str, source_kind: str) -> List[Dict[str, Any]]:
    risks: List[Dict[str, Any]] = []
    for key, pattern, message in RISK_PATTERNS:
        for m in pattern.finditer(text):
            risks.append({
                "risk": key,
                "unit": unit_id,
                "source_kind": source_kind,
                "line": line_for_index(text, m.start()),
                "message": message,
                "snippet": text[m.start(): min(len(text), m.start() + 120)].splitlines()[0][:120],
            })
    return risks


def analyze_html_file(path: Path, root: Path) -> Dict[str, Any]:
    text = read_text(path)
    parser = HTMLInventoryParser()
    parser.feed(text)
    rel = relative(path, root)
    scripts: List[Dict[str, Any]] = []

    for tag in parser.scripts:
        attrs = tag.attrs
        src = attrs.get("src")
        typ = attrs.get("type", "")
        js_like = is_probably_javascript_script(attrs)
        item: Dict[str, Any] = {
            "index": tag.index,
            "line": tag.line,
            "attrs": attrs,
            "type": typ,
            "is_javascript_like": js_like,
            "is_inline": src is None,
            "src": src,
            "async": "async" in attrs,
            "defer": "defer" in attrs,
            "nomodule": "nomodule" in attrs,
            "integrity": attrs.get("integrity"),
            "crossorigin": attrs.get("crossorigin"),
            "nonce": attrs.get("nonce"),
        }
        if src:
            item["remote"] = is_remote_src(src)
            item["src_without_query"] = strip_url_query_fragment(src)
            if not item["remote"]:
                resolved = (path.parent / item["src_without_query"]).resolve()
                item["resolved_path"] = relative(resolved, root)
                item["exists"] = resolved.exists()
            else:
                item["resolved_path"] = None
                item["exists"] = None
        else:
            item["content_sha256"] = sha256_text(tag.content)
            item["content_length"] = len(tag.content)
            item["unit_id"] = f"{rel}#inline-script-{tag.index}"
        scripts.append(item)

    return {
        "path": rel,
        "sha256": sha256_text(text),
        "scripts": scripts,
        "event_handlers": parser.event_handlers,
        "base_hrefs": parser.base_hrefs,
    }


def build_duplicate_map(declarations: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for decl in declarations:
        if decl["kind"] == "suspect_implicit_global_assignment":
            continue
        groups.setdefault(decl["symbol"], []).append(decl)
    duplicates: List[Dict[str, Any]] = []
    for symbol, items in sorted(groups.items()):
        if len(items) <= 1:
            continue
        body_hashes = sorted({i.get("body_hash") for i in items if i.get("body_hash")})
        kinds = sorted({i.get("kind") for i in items})
        arities = sorted({str(i.get("arity")) for i in items if i.get("arity") is not None})
        if body_hashes and len(body_hashes) == 1 and len(kinds) <= 2:
            classification = "exact_or_near_duplicate"
        elif len(body_hashes) > 1:
            classification = "divergent_duplicate_or_override"
        else:
            classification = "duplicate_declaration_name"
        duplicates.append({
            "symbol": symbol,
            "count": len(items),
            "classification": classification,
            "kinds": kinds,
            "arities": arities,
            "body_hashes": body_hashes,
            "locations": [{
                "unit": i["unit"],
                "line": i["line"],
                "kind": i["kind"],
                "arity": i.get("arity"),
            } for i in items],
        })
    return duplicates


def audit(root: Path, out: Path, scan_all_js: bool = True) -> Dict[str, Any]:
    root = root.resolve()
    html_files = walk_files(root, HTML_EXTENSIONS)
    js_files = walk_files(root, JS_EXTENSIONS) if scan_all_js else []

    pages: List[Dict[str, Any]] = []
    referenced_js: set[str] = set()
    missing_scripts: List[Dict[str, Any]] = []
    remote_scripts: List[Dict[str, Any]] = []
    script_attribute_warnings: List[Dict[str, Any]] = []
    inline_units: Dict[str, str] = {}

    for html_path in html_files:
        page = analyze_html_file(html_path, root)
        pages.append(page)
        for script in page["scripts"]:
            if not script.get("is_javascript_like"):
                continue
            if script.get("is_inline"):
                unit_id = script.get("unit_id")
                # Re-parse content by matching index from parser result.
                parser = HTMLInventoryParser()
                parser.feed(read_text(html_path))
                idx = script["index"]
                inline_units[unit_id] = parser.scripts[idx].content if idx < len(parser.scripts) else ""
            else:
                if script.get("remote"):
                    remote_scripts.append({"page": page["path"], **script})
                else:
                    rp = script.get("resolved_path")
                    if rp:
                        referenced_js.add(rp)
                    if script.get("exists") is False:
                        missing_scripts.append({"page": page["path"], **script})
            if script.get("async"):
                script_attribute_warnings.append({
                    "page": page["path"],
                    "script_index": script["index"],
                    "line": script["line"],
                    "severity": "HIGH_ORDER_DEPENDENCY",
                    "message": "async script has no deterministic ordering relative to other async/downloaded scripts.",
                    "src": script.get("src"),
                })
            if script.get("defer") and script.get("is_inline"):
                script_attribute_warnings.append({
                    "page": page["path"],
                    "script_index": script["index"],
                    "line": script["line"],
                    "severity": "MEDIUM_INLINE_SCRIPT",
                    "message": "defer on inline classic scripts has no effect; do not rely on it for ordering.",
                    "src": script.get("src"),
                })
            if page.get("base_hrefs"):
                script_attribute_warnings.append({
                    "page": page["path"],
                    "script_index": script["index"],
                    "line": script["line"],
                    "severity": "MEDIUM_BASE_HREF",
                    "message": "<base href> exists; resolved script paths may differ from simple filesystem resolution.",
                    "src": script.get("src"),
                })

    js_units: Dict[str, str] = {}
    for js_path in js_files:
        js_units[relative(js_path, root)] = read_text(js_path)

    all_units: Dict[str, Tuple[str, str]] = {}
    for unit_id, text in js_units.items():
        all_units[unit_id] = (text, "external_js")
    for unit_id, text in inline_units.items():
        all_units[unit_id] = (text, "inline_script")

    declarations: List[Dict[str, Any]] = []
    risks: List[Dict[str, Any]] = []
    file_hashes: Dict[str, str] = {}
    for unit_id, (text, source_kind) in sorted(all_units.items()):
        file_hashes[unit_id] = sha256_text(text)
        declarations.extend(collect_declarations(unit_id, text, source_kind))
        risks.extend(collect_risks(unit_id, text, source_kind))

    duplicates = build_duplicate_map(declarations)
    all_js_set = set(js_units.keys())
    orphan_js = sorted(all_js_set - referenced_js)

    result: Dict[str, Any] = {
        "schema": "legacy-browser-js-refactor-audit/v1",
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "root": str(root),
        "summary": {
            "html_pages": len(pages),
            "js_files_scanned": len(js_units),
            "referenced_local_js_files": len(referenced_js),
            "orphan_js_files": len(orphan_js),
            "inline_script_units": len(inline_units),
            "event_handler_attributes": sum(len(p["event_handlers"]) for p in pages),
            "declarations": len(declarations),
            "duplicate_symbols": len(duplicates),
            "risk_findings": len(risks),
            "missing_scripts": len(missing_scripts),
            "remote_scripts": len(remote_scripts),
        },
        "pages": pages,
        "referenced_local_js": sorted(referenced_js),
        "orphan_js": orphan_js,
        "missing_scripts": missing_scripts,
        "remote_scripts": remote_scripts,
        "script_attribute_warnings": script_attribute_warnings,
        "file_hashes": file_hashes,
        "declarations": declarations,
        "duplicates": duplicates,
        "risks": risks,
    }

    out.mkdir(parents=True, exist_ok=True)
    (out / "audit.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    (out / "report.md").write_text(render_audit_report(result), encoding="utf-8")
    return result


def render_audit_report(a: Dict[str, Any]) -> str:
    s = a["summary"]
    lines: List[str] = []
    lines.append("# Legacy Browser JavaScript Refactor Static Audit")
    lines.append("")
    lines.append(f"Generated: `{a['generated_at']}`")
    lines.append("")
    lines.append("## Summary")
    for key, value in s.items():
        lines.append(f"- {key.replace('_', ' ')}: **{value}**")
    lines.append("")

    if a["missing_scripts"]:
        lines.append("## Missing referenced scripts")
        lines.append("| Page | Script index | Line | src | Resolved path |")
        lines.append("|---|---:|---:|---|---|")
        for item in a["missing_scripts"][:100]:
            lines.append(f"| {item.get('page')} | {item.get('index')} | {item.get('line')} | `{item.get('src')}` | `{item.get('resolved_path')}` |")
        lines.append("")

    if a["script_attribute_warnings"]:
        lines.append("## Script loading warnings")
        lines.append("| Severity | Page | Script index | Line | src | Message |")
        lines.append("|---|---|---:|---:|---|---|")
        for item in a["script_attribute_warnings"][:150]:
            lines.append(f"| {item.get('severity')} | {item.get('page')} | {item.get('script_index')} | {item.get('line')} | `{item.get('src')}` | {item.get('message')} |")
        lines.append("")

    if a["duplicates"]:
        lines.append("## Duplicate declarations")
        lines.append("| Symbol | Count | Classification | Kinds | Locations |")
        lines.append("|---|---:|---|---|---|")
        for dup in a["duplicates"][:200]:
            loc = "; ".join(f"{x['unit']}:{x['line']} ({x['kind']})" for x in dup["locations"][:8])
            if len(dup["locations"]) > 8:
                loc += f"; +{len(dup['locations']) - 8} more"
            lines.append(f"| `{dup['symbol']}` | {dup['count']} | {dup['classification']} | {', '.join(dup['kinds'])} | {loc} |")
        lines.append("")

    implicit = [d for d in a["declarations"] if d["kind"] == "suspect_implicit_global_assignment"]
    if implicit:
        lines.append("## Suspect implicit global assignments")
        lines.append("These are conservative findings. Inspect before changing behavior.")
        lines.append("")
        lines.append("| Symbol | Unit | Line |")
        lines.append("|---|---|---:|")
        for item in implicit[:200]:
            lines.append(f"| `{item['symbol']}` | {item['unit']} | {item['line']} |")
        lines.append("")

    if a["risks"]:
        lines.append("## Dynamic-code and parser-timing risks")
        lines.append("| Risk | Unit | Line | Message | Snippet |")
        lines.append("|---|---|---:|---|---|")
        for r in a["risks"][:200]:
            snippet = str(r.get("snippet", "")).replace("|", "\\|")
            lines.append(f"| {r['risk']} | {r['unit']} | {r['line']} | {r['message']} | `{snippet}` |")
        lines.append("")

    event_count = sum(len(p["event_handlers"]) for p in a["pages"])
    if event_count:
        lines.append("## HTML event-handler attributes")
        lines.append("| Page | Tag | Attribute | Line | Value |")
        lines.append("|---|---|---|---:|---|")
        for p in a["pages"]:
            for ev in p["event_handlers"][:100]:
                val = str(ev.get("value", "")).replace("|", "\\|")[:120]
                lines.append(f"| {p['path']} | {ev.get('tag')} | {ev.get('attribute')} | {ev.get('line')} | `{val}` |")
        lines.append("")

    if a["orphan_js"]:
        lines.append("## JS files not directly referenced by scanned HTML")
        lines.append("These may be dynamically loaded, test files, unused files, or referenced by pages outside the scan root.")
        lines.append("")
        for path in a["orphan_js"][:200]:
            lines.append(f"- `{path}`")
        if len(a["orphan_js"]) > 200:
            lines.append(f"- ... +{len(a['orphan_js']) - 200} more")
        lines.append("")

    lines.append("## Recommended next step")
    lines.append("Run the browser regression probe on the main HTML pages before making consolidation changes.")
    lines.append("")
    return "\n".join(lines)


def page_script_signature(page: Dict[str, Any]) -> List[Dict[str, Any]]:
    sig: List[Dict[str, Any]] = []
    for s in page.get("scripts", []):
        sig.append({
            "index": s.get("index"),
            "is_inline": s.get("is_inline"),
            "src": s.get("src"),
            "resolved_path": s.get("resolved_path"),
            "type": s.get("type"),
            "async": s.get("async"),
            "defer": s.get("defer"),
            "nomodule": s.get("nomodule"),
            "content_sha256": s.get("content_sha256") if s.get("is_inline") else None,
        })
    return sig


def compare_audits(before_path: Path, after_path: Path, out: Optional[Path]) -> str:
    before = json.loads(before_path.read_text(encoding="utf-8"))
    after = json.loads(after_path.read_text(encoding="utf-8"))
    issues: List[Dict[str, Any]] = []

    before_pages = {p["path"]: p for p in before.get("pages", [])}
    after_pages = {p["path"]: p for p in after.get("pages", [])}
    for page in sorted(set(before_pages) | set(after_pages)):
        if page not in before_pages:
            issues.append({"severity": "HIGH", "area": "pages", "item": page, "message": "Page added after refactor."})
            continue
        if page not in after_pages:
            issues.append({"severity": "HIGH", "area": "pages", "item": page, "message": "Page missing after refactor."})
            continue
        b_sig = page_script_signature(before_pages[page])
        a_sig = page_script_signature(after_pages[page])
        if b_sig != a_sig:
            issues.append({"severity": "HIGH_ORDER_DEPENDENCY", "area": "script_sequence", "item": page, "message": "Script sequence/attributes/inline hashes changed. Requires explicit runtime proof."})

    b_symbols = {(d["symbol"], d["kind"], d["unit"]) for d in before.get("declarations", []) if d["kind"] != "suspect_implicit_global_assignment"}
    a_symbols = {(d["symbol"], d["kind"], d["unit"]) for d in after.get("declarations", []) if d["kind"] != "suspect_implicit_global_assignment"}
    removed = sorted(b_symbols - a_symbols)
    added = sorted(a_symbols - b_symbols)
    if removed:
        issues.append({"severity": "HIGH_GLOBAL_COLLISION", "area": "declarations", "item": "removed", "message": f"{len(removed)} declaration records disappeared.", "examples": removed[:20]})
    if added:
        issues.append({"severity": "MEDIUM", "area": "declarations", "item": "added", "message": f"{len(added)} declaration records were added.", "examples": added[:20]})

    b_missing = {(m.get("page"), m.get("src"), m.get("resolved_path")) for m in before.get("missing_scripts", [])}
    a_missing = {(m.get("page"), m.get("src"), m.get("resolved_path")) for m in after.get("missing_scripts", [])}
    if b_missing != a_missing:
        issues.append({"severity": "HIGH", "area": "missing_scripts", "item": "delta", "message": "Missing referenced script set changed.", "before_only": sorted(b_missing - a_missing), "after_only": sorted(a_missing - b_missing)})

    b_risks = {(r.get("risk"), r.get("unit"), r.get("line")) for r in before.get("risks", [])}
    a_risks = {(r.get("risk"), r.get("unit"), r.get("line")) for r in after.get("risks", [])}
    if b_risks != a_risks:
        issues.append({"severity": "MEDIUM", "area": "risk_findings", "item": "delta", "message": "Risk findings changed. Inspect whether code moved or behavior changed.", "removed_count": len(b_risks - a_risks), "added_count": len(a_risks - b_risks)})

    lines: List[str] = []
    lines.append("# Static Audit Comparison")
    lines.append("")
    lines.append(f"Baseline: `{before_path}`")
    lines.append(f"After: `{after_path}`")
    lines.append("")
    status = "PASS" if not issues else "REVIEW REQUIRED"
    lines.append(f"## Status: {status}")
    lines.append("")
    lines.append("## Summary")
    lines.append("| Metric | Baseline | After |")
    lines.append("|---|---:|---:|")
    keys = sorted(set(before.get("summary", {})) | set(after.get("summary", {})))
    for k in keys:
        lines.append(f"| {k.replace('_', ' ')} | {before.get('summary', {}).get(k, '')} | {after.get('summary', {}).get(k, '')} |")
    lines.append("")
    if issues:
        lines.append("## Deltas requiring review")
        lines.append("| Severity | Area | Item | Message |")
        lines.append("|---|---|---|---|")
        for i in issues:
            lines.append(f"| {i['severity']} | {i['area']} | {i['item']} | {i['message']} |")
            if i.get("examples"):
                lines.append(f"|  |  | examples | `{i['examples']}` |")
    else:
        lines.append("No static deltas detected by this tool. Runtime/browser probes are still required for no-regression sign-off.")
    lines.append("")
    output = "\n".join(lines)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(output, encoding="utf-8")
    return output


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Audit/refactor-guard helper for legacy browser JS apps.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_audit = sub.add_parser("audit", help="Create static script/declaration inventory.")
    p_audit.add_argument("root", type=Path, help="Application root to scan.")
    p_audit.add_argument("--out", type=Path, required=True, help="Output directory for audit.json and report.md.")
    p_audit.add_argument("--referenced-only", action="store_true", help="Only inventory JS referenced from scanned HTML. Default scans all JS too.")

    p_compare = sub.add_parser("compare", help="Compare two audit.json files.")
    p_compare.add_argument("before", type=Path)
    p_compare.add_argument("after", type=Path)
    p_compare.add_argument("--out", type=Path, help="Markdown output path.")

    args = parser.parse_args(argv)
    if args.cmd == "audit":
        result = audit(args.root, args.out, scan_all_js=not args.referenced_only)
        print(f"Wrote {args.out / 'audit.json'}")
        print(f"Wrote {args.out / 'report.md'}")
        print(json.dumps(result["summary"], indent=2))
        return 0
    if args.cmd == "compare":
        output = compare_audits(args.before, args.after, args.out)
        print(output)
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
