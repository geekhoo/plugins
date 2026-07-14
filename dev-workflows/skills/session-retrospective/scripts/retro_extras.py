"""retro_extras.py -- four reusable retrospective capabilities.

Folded from the PROVEN 2026-07-13 pass-2 fresh scan into the standing scanner
set so the monthly retrospective gets them for free. Stdlib only.

    py -3 retro_extras.py [ROOT]           # human report to stdout
    py -3 retro_extras.py [ROOT] --json OUT # also dump machine-readable JSON

ROOT defaults to ~/.claude (the full corpus: projects/ + subagents/ + transcripts/).

Capabilities
------------
1. Machine-session filter
   A session is machine-generated when its first real user prompt matches a
   `.remember` template ("summarizing a Claude Code session", "memory
   consolidation agent", "maximum non-destructive compression"). Human vs
   machine counts are reported separately so retrospective totals stop being
   inflated by consolidation runs.

2. Path normalization
   Project-dir keys are lowercased and 8.3 short-path user segments collapsed
   (GERALD~1.KHO / gerald-1-kho == gerald.khoo, lowercase drive c-- == C--) so
   fragmented project dirs merge into a single logical project in reports.

3. Named event/error trend lines with dates
   <synthetic> model turns; API 529 / overloaded / rate-limit events; and the
   minor classes -- malformed tool-call JSON, missing required tool params,
   "No such tool available", and PowerShell UTF-16 spaced-output mangling
   ("T h e   o p e r a t i o n"). Each is a named line with a per-day histogram.
   Detectors key on API-error EVENTS (isApiErrorMessage / synthetic model /
   tool_result is_error bodies), never on raw command/tool text -- a session
   log that merely contains the word "overloaded" in a shell command is not an
   overload event.

4. Usage / token columns
   output / cache-create / cache-read / input tokens per session and in
   aggregate, split main-vs-subagent (subagent = isSidechain or an
   agent-*/subagents/ file).
"""
import json, os, re, sys, collections
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
REMEMBER_TEMPLATES = (
    "summarizing a claude code session",
    "memory consolidation agent",
    "maximum non-destructive compression",
)

# Real API overload/rate-limit events (not shell text that says "overloaded").
OVERLOAD_PAT = re.compile(r"overloaded|(?<!\d)529(?!\d)|rate.?limit|rate_limit", re.I)
# Synthetic no-op turns carry this text; everything else on a synthetic turn is
# a genuine API-error surface (spend/session limit, auth, overload).
SYNTH_NOOP = "no response requested"
API_ERR_SUBTYPE = (
    ("overload/529", re.compile(r"overloaded|(?<!\d)529(?!\d)|rate.?limit", re.I)),
    ("auth/401", re.compile(r"API Error: 401|/login|invalid authentication", re.I)),
    ("spend-limit", re.compile(r"monthly spend limit", re.I)),
    ("session-limit", re.compile(r"session limit", re.I)),
)
# Minor event classes.
MALFORMED_JSON_PAT = re.compile(
    r"is not valid JSON|invalid JSON|Unexpected token.*JSON|Could not parse tool|tool call.*malformed|Expected ',' or",
    re.I)
MISSING_PARAM_PAT = re.compile(
    r"required (?:property|parameter|field)|is a required|missing required|Required parameter|input.*required",
    re.I)
NO_TOOL_PAT = re.compile(r"No such tool available|Tool .* not found|not a valid tool", re.I)
# PowerShell UTF-16 mangling shows as single letters separated by spaces:
# "T h e   o p e r a t i o n   c o m p l e t e d". Detect a run of >=6 single
# chars separated by single spaces.
PS_UTF16_PAT = re.compile(r"(?:\b\w \b){6,}")


def date_of(ts):
    """YYYY-MM-DD from an ISO timestamp (or None)."""
    if not ts or not isinstance(ts, str):
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc).strftime("%Y-%m-%d")
    except Exception:
        return ts[:10] if len(ts) >= 10 else None


def project_key(rel):
    """Top project-dir segment from a path relative to ROOT, else '<root>'."""
    parts = rel.replace("\\", "/").split("/")
    if parts and parts[0] == "projects" and len(parts) > 1:
        return parts[1]
    return parts[0] if parts else "<root>"


def normalize_key(key):
    """Case-insensitive + 8.3 short-path collapse so fragmented dirs merge."""
    k = key.lower()
    # 8.3 short user segment -> long form (both the encoded '-' and raw '~'/'.').
    k = re.sub(r"gerald[~-]1[.-]kho", "gerald-khoo", k)
    return k


def is_subagent(rel, obj):
    if obj.get("isSidechain"):
        return True
    low = rel.lower()
    return "subagents" in low or os.path.basename(low).startswith("agent-")


def first_user_text(obj):
    """Text of a user turn under either the transcript or project schema."""
    content = obj.get("content")
    if content is None:
        m = obj.get("message")
        if isinstance(m, dict):
            c = m.get("content")
            if isinstance(c, str):
                content = c
            elif isinstance(c, list):
                texts = [b.get("text", "") for b in c
                         if isinstance(b, dict) and b.get("type") == "text"]
                content = "\n".join(texts) if texts else None
    return content if isinstance(content, str) else None


# ---------------------------------------------------------------------------
# Scan
# ---------------------------------------------------------------------------
def scan(root):
    files = []
    for dp, _dn, fns in os.walk(root):
        for fn in fns:
            if fn.endswith(".jsonl"):
                files.append(os.path.join(dp, fn))

    sessions = []                                   # per-file record
    events = {name: collections.Counter() for name in
              ("synthetic", "api_error", "overload", "malformed_tool_json",
               "missing_tool_param", "no_such_tool", "ps_utf16")}
    event_totals = collections.Counter()
    api_err_subtypes = collections.Counter()

    for path in files:
        rel = os.path.relpath(path, root)
        sub = False
        machine = False
        first_seen_user = False
        tin = tout = tcr = tcc = 0
        first_ts = None

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    if obj.get("isSidechain"):
                        sub = True
                    ts = obj.get("timestamp") or (obj.get("message") or {}).get("timestamp")
                    if ts and first_ts is None:
                        first_ts = ts
                    day = date_of(ts)
                    typ = obj.get("type", "")
                    msg = obj.get("message") if isinstance(obj.get("message"), dict) else {}

                    # (1) machine-session: first real user prompt vs templates
                    if typ == "user" and not first_seen_user:
                        txt = first_user_text(obj)
                        if txt and txt.strip() and "system-reminder" not in txt[:100]:
                            first_seen_user = True
                            low = txt.lower()
                            if any(t in low for t in REMEMBER_TEMPLATES):
                                machine = True

                    # (4) token usage
                    usage = msg.get("usage") or {}
                    tin += usage.get("input_tokens", 0) or 0
                    tout += usage.get("output_tokens", 0) or 0
                    tcr += usage.get("cache_read_input_tokens", 0) or 0
                    tcc += usage.get("cache_creation_input_tokens", 0) or 0

                    # (3) event detectors
                    model = msg.get("model")
                    synthetic = model == "<synthetic>"
                    if synthetic:
                        events["synthetic"][day] += 1
                        event_totals["synthetic"] += 1

                    # Collect this record's text for the API-error surface: any
                    # synthetic turn or an explicitly-flagged API-error record.
                    api_err = synthetic or bool(obj.get("isApiErrorMessage"))
                    syn_texts = []
                    if api_err:
                        c = msg.get("content")
                        if isinstance(c, str):
                            syn_texts.append(c)
                        elif isinstance(c, list):
                            syn_texts += [b.get("text", "") for b in c
                                          if isinstance(b, dict) and b.get("type") == "text"]
                    syn_joined = "\n".join(t for t in syn_texts if t).strip()
                    if syn_joined and SYNTH_NOOP not in syn_joined.lower():
                        # A genuine API-error surface (limit/auth/overload), dated.
                        events["api_error"][day] += 1
                        event_totals["api_error"] += 1
                        for label, rx in API_ERR_SUBTYPE:
                            if rx.search(syn_joined):
                                api_err_subtypes[label] += 1
                                break
                        if OVERLOAD_PAT.search(syn_joined):
                            events["overload"][day] += 1
                            event_totals["overload"] += 1

                    # tool_result bodies (BOTH schemas). Error bodies feed the
                    # minor-error detectors; ALL bodies feed the PowerShell
                    # UTF-16 mangling detector (it surfaces in NON-error output).
                    err_texts, all_tool_texts = [], []
                    if typ == "user":
                        c = msg.get("content")
                        if isinstance(c, list):
                            for b in c:
                                if isinstance(b, dict) and b.get("type") == "tool_result":
                                    body = b.get("content")
                                    if isinstance(body, list):
                                        body = " ".join(x.get("text", "") for x in body if isinstance(x, dict))
                                    body = str(body)
                                    all_tool_texts.append(body)
                                    if b.get("is_error"):
                                        err_texts.append(body)
                    if typ == "tool_result":                       # transcript schema
                        out = (obj.get("tool_output") or {})
                        body = out.get("output") if isinstance(out, dict) else out
                        if body:
                            all_tool_texts.append(str(body))
                            if obj.get("is_error") or (isinstance(out, dict) and out.get("is_error")):
                                err_texts.append(str(body))

                    err_joined = "\n".join(err_texts)
                    if err_joined:
                        if MALFORMED_JSON_PAT.search(err_joined):
                            events["malformed_tool_json"][day] += 1
                            event_totals["malformed_tool_json"] += 1
                        if MISSING_PARAM_PAT.search(err_joined):
                            events["missing_tool_param"][day] += 1
                            event_totals["missing_tool_param"] += 1
                        if NO_TOOL_PAT.search(err_joined):
                            events["no_such_tool"][day] += 1
                            event_totals["no_such_tool"] += 1
                    for body in all_tool_texts:
                        if PS_UTF16_PAT.search(body):
                            events["ps_utf16"][day] += 1
                            event_totals["ps_utf16"] += 1
                            break
        except OSError:
            continue

        sessions.append({
            "rel": rel,
            "project": normalize_key(project_key(rel)),
            "raw_project": project_key(rel),
            "subagent": sub or is_subagent(rel, {}),
            "machine": machine,
            "first_ts": first_ts,
            "in": tin, "out": tout, "cache_read": tcr, "cache_create": tcc,
        })

    return sessions, events, event_totals, api_err_subtypes


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def human(n):
    for unit, div in (("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(n) >= div:
            return f"{n/div:.1f}{unit}"
    return str(n)


def report(sessions, events, event_totals, api_err_subtypes):
    total = len(sessions)
    machine = [s for s in sessions if s["machine"]]
    human_s = [s for s in sessions if not s["machine"]]

    print(f"corpus: {total} session files\n")

    # (1) machine vs human
    print("== (1) MACHINE vs HUMAN SESSIONS ==")
    print(f"  machine (.remember): {len(machine)}")
    print(f"  human              : {len(human_s)}")
    by_proj_machine = collections.Counter(s["project"] for s in machine)
    for k, v in by_proj_machine.most_common():
        print(f"     {v:4d}  {k}")

    # (2) path normalization
    print("\n== (2) PROJECT DIRS (normalized) ==")
    raw = collections.Counter(s["raw_project"] for s in sessions)
    norm = collections.defaultdict(collections.Counter)
    for s in sessions:
        norm[s["project"]][s["raw_project"]] += 1
    print(f"  raw dirs: {len(raw)}  ->  normalized: {len(norm)}")
    for k in sorted(norm, key=lambda x: -sum(norm[x].values())):
        variants = norm[k]
        total_k = sum(variants.values())
        merged = f"  (merged {len(variants)})" if len(variants) > 1 else ""
        print(f"     {total_k:4d}  {k}{merged}")
        if len(variants) > 1:
            for rv, c in variants.most_common():
                print(f"            {c:4d}  <- {rv}")

    # (3) named event trend lines
    print("\n== (3) EVENT / ERROR TREND LINES (by day) ==")
    labels = {
        "synthetic": "<synthetic> model turns (API-error/retry surface)",
        "api_error": "API-error turns (limit / auth / overload; excl. no-op)",
        "overload": "  ^ of which 529 / overloaded / rate-limit",
        "malformed_tool_json": "malformed tool-call JSON",
        "missing_tool_param": "missing required tool param",
        "no_such_tool": "No such tool available",
        "ps_utf16": "PowerShell UTF-16 spaced-output mangling",
    }
    for name, label in labels.items():
        hist = events[name]
        tot = event_totals[name]
        days = {d: c for d, c in hist.items() if d}
        trend = ", ".join(f"{d} x{c}" for d, c in sorted(days.items()))
        print(f"  {label}: {tot} total")
        if trend:
            print(f"      {trend}")
        if name == "api_error" and api_err_subtypes:
            print(f"      subtypes: {dict(api_err_subtypes.most_common())}")

    # (4) token usage, main vs subagent
    print("\n== (4) TOKEN USAGE (main vs subagent) ==")
    def agg(rows):
        return {k: sum(r[k] for r in rows) for k in ("in", "out", "cache_read", "cache_create")}
    main = [s for s in sessions if not s["subagent"]]
    subs = [s for s in sessions if s["subagent"]]
    for label, rows in (("main", main), ("subagent", subs), ("ALL", sessions)):
        a = agg(rows)
        print(f"  {label:9s} n={len(rows):4d}  out={human(a['out']):>7}  "
              f"cache_create={human(a['cache_create']):>7}  "
              f"cache_read={human(a['cache_read']):>7}  in={human(a['in']):>7}")

    return {
        "total": total, "machine": len(machine), "human": len(human_s),
        "raw_dirs": len(raw), "normalized_dirs": len(norm),
        "event_totals": dict(event_totals),
        "event_days": {k: dict(v) for k, v in events.items()},
        "tokens_main": agg(main), "tokens_sub": agg(subs), "tokens_all": agg(sessions),
    }


def main(argv):
    root = os.path.expanduser(r"~/.claude")
    out_json = None
    args = argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--json":
            out_json = args[i + 1]
            i += 2
        else:
            root = args[i]
            i += 1
    sessions, events, event_totals, api_err_subtypes = scan(root)
    summary = report(sessions, events, event_totals, api_err_subtypes)
    if out_json:
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump({"summary": summary, "sessions": sessions}, f, indent=1)
        print(f"\nwrote {out_json}")


if __name__ == "__main__":
    main(sys.argv)
