"""Derive baseline-run measures from a run folder and merge them into run.json.

Usage: python analyze-run.py <run-folder> [--token-ceiling N] [--analysis-only]

Reads stream.jsonl (claude stream-json) and session.jsonl (Claude session transcript, which
carries the timestamps the stream lacks). Writes analysis.json and updates these run.json fields:
tokens (summed over every model in result.modelUsage), model_calls, latency_median_ms,
max_idle_gap_s, stages, impl_review_rounds, token_ceiling, over_token_ceiling.
--analysis-only writes analysis.json and leaves run.json untouched (re-analysing a stored run).

Subagent transcripts: when the run folder has subagents/agent-<id>.jsonl (+ .meta.json), tool calls found
only there (e.g. calls of workers dispatched by a subagent, which the stream omits) are added to the tool,
dispatch, validation and gate counts, deduplicated by tool_use id, and analysis.json gains
"subagent_transcripts" with a main / orchestrator-subagent / worker split. Tokens, model calls and latency
still come from the result event and session.jsonl only.

Gate runs are counted from each tool call's result: every gate summary line (OK/INVALID_*,
DOD_OK/DOD_INCOMPLETE, the check-commit verdict) is one run with its pass/fail. When a command
executes a gate but its output hides the summary, the run is counted from the command text
(each <gate>.py/.ps1 execution, multiplied by literal foreach lists and helper-function calls)
with an unknown result. Reading a gate script does not count. MCP gate tools count by their
"ok" field.
Stdlib only.
"""
import argparse
import collections
import datetime as dt
import json
import re
import statistics
import importlib.util
from pathlib import Path


def load_jsonl(path):
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("{"):
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass  # truncated last line
    return rows


def ts(event):
    t = event.get("timestamp")
    return dt.datetime.fromisoformat(t.replace("Z", "+00:00")) if t else None


def tool_uses(event):
    content = (event.get("message") or {}).get("content") or []
    return [c for c in content if isinstance(c, dict) and c.get("type") == "tool_use"]


def tool_results(event):
    """{tool_use_id: (text, is_error)} for the tool_result blocks of a user event."""
    content = (event.get("message") or {}).get("content")
    out = {}
    for c in content if isinstance(content, list) else []:
        if isinstance(c, dict) and c.get("type") == "tool_result":
            text = c.get("content")
            if isinstance(text, list):
                text = "\n".join(x.get("text", "") for x in text if isinstance(x, dict))
            out[c.get("tool_use_id")] = (text if isinstance(text, str) else "", bool(c.get("is_error")))
    return out


ORCHESTRATOR_AGENT = "geeky-implement-orchestrator"


def is_orchestrator_type(subagent_type):
    """True for the plugin's geeky-implement orchestrator subagent (plain or plugin-qualified name)."""
    return str(subagent_type or "").split(":")[-1] == ORCHESTRATOR_AGENT


def load_subagents(run_dir):
    """[(meta, events)] for each subagents/agent-<id>.jsonl (a Claude Code subagent session transcript) with
    its agent-<id>.meta.json (agentType, description, toolUseId of the spawning Agent call, spawnDepth)."""
    folder = Path(run_dir) / "subagents"
    out = []
    if not folder.is_dir():
        return out
    for f in sorted(folder.glob("agent-*.jsonl")):
        mp = f.with_name(f.name[:-len(".jsonl")] + ".meta.json")
        try:
            meta = json.loads(mp.read_text(encoding="utf-8-sig")) if mp.exists() else {}
        except ValueError:
            meta = {}
        meta.setdefault("agentId", f.name[len("agent-"):-len(".jsonl")])
        out.append((meta, load_jsonl(f)))
    return out


def transcript_calls(run_dir, known_ids=()):
    """Tool calls recorded only in subagent transcripts, with their results.

    Returns (calls, metas). Each call is a dict {id, name, input, parent, timestamp, result, result_timestamp}
    whose parent is the meta.toolUseId of the transcript, i.e. the Agent call that spawned the subagent, so
    calls nested under a subagent's own dispatches link to that dispatch. Calls whose id is in known_ids (the
    stream already carries them) are skipped, as is any id seen in an earlier transcript. metas maps
    toolUseId -> meta, with "_end" set to the transcript's last timestamp."""
    known = set(known_ids)
    calls, metas = [], {}
    for meta, events in load_subagents(run_dir):
        parent = meta.get("toolUseId")
        stamps = [e["timestamp"] for e in events if e.get("timestamp")]
        if parent:
            metas[parent] = dict(meta, _end=max(stamps) if stamps else None)
        results = {}
        for e in events:
            if e.get("type") == "user":
                for k, v in tool_results(e).items():
                    results[k] = (v, e.get("timestamp"))
        for e in events:
            if e.get("type") != "assistant":
                continue
            for c in tool_uses(e):
                if c.get("id") in known:
                    continue
                known.add(c.get("id"))
                res, rts = results.get(c.get("id"), (None, None))
                calls.append({"id": c.get("id"), "name": c.get("name"), "input": c.get("input") or {},
                              "parent": parent, "timestamp": e.get("timestamp"), "result": res,
                              "result_timestamp": rts})
    calls.sort(key=lambda c: c["timestamp"] or "")
    return calls, metas


GATES = ("validate-planning-folder", "validate-task-schema", "validate-kanban", "check-dod", "check-commit")
MCP_PREFIXES = ("mcp__geeky__", "mcp__plugin_geeky-orchestration_geeky__")
# One summary line per gate run (scripts/*.py and *.ps1 print the same text); group 1 is the verdict.
GATE_LINES = {
    "validate-task-schema": re.compile(r"\b(OK|INVALID_TASK_SCHEMA): \d+ task file\(s\) checked"),
    "validate-kanban": re.compile(r"\b(OK|INVALID_KANBAN): (?:\d+ task\(s\) tracked|[^{\s].* not found\.)"),
    "validate-planning-folder": re.compile(r"\b(OK: planning folder valid\.|INVALID_PLANNING_FOLDER: )"),
    "check-dod": re.compile(r"\b(DOD_OK|DOD_INCOMPLETE): \S"),
    "check-commit": re.compile(r"\b(OK: commit message valid\.|INVALID_COMMIT_MESSAGE:)"),
}
CODE_LINE = re.compile(r"print\(|Write-Output|Write-Host|\bf\"")
# A statement starting with one of these only reads or lists a gate script.
READER = re.compile(r"^(?:Get-Content|gc|cat|type|head|tail|less|more|Select-String|sls|grep|rg|findstr|"
                    r"Get-Item|Get-ChildItem|ls|dir|Test-Path|wc|sed|awk|echo|Write-Output|Write-Host)\b", re.I)
GATE_FILE = re.compile(r"(%s)\.(?:py|ps1)\b" % "|".join(GATES))
RUNNER = re.compile(r"(?:^|[\s&])(?:python[\d.]*|py|pwsh|powershell|bash|sh|uv)(?:\.exe)?\b|^&|^[\"']?[\w$:./\\{}()-]*$", re.I)


def _block(text, start):
    """End index (exclusive) of the {...} block whose opening brace is at text[start]."""
    depth = 0
    for i in range(start, len(text)):
        depth += {"{": 1, "}": -1}.get(text[i], 0)
        if depth == 0:
            return i + 1
    return len(text)


def _executed(text):
    """Counter of gate-script executions written literally in text (reads excluded)."""
    found = collections.Counter()
    for stmt in re.split(r"[;\n|{}]|&&", text):
        stmt = re.sub(r"^[\s(]*(?:\$[\w:]+\s*=\s*)?", "", stmt)
        if READER.match(stmt):
            continue
        for m in GATE_FILE.finditer(stmt):
            # run by an interpreter or invoked directly as the statement's first word
            if RUNNER.search(stmt[:m.start()]):
                found[m.group(1)] += 1
    return found


def _loop_items(spec):
    quoted = re.findall(r"['\"]([^'\"]*)['\"]", spec)
    if quoted:
        return quoted
    bare = [s for s in re.split(r"[,\s]+", spec.strip()) if s]
    # a single variable is a collection of unknown size; a comma list of variables ($m1,$m2) has one item each
    return bare if bare and (len(bare) > 1 or not bare[0].startswith("$")) else [None]


def static_gate_runs(cmd):
    """Gate executions implied by a shell command: literal calls, loops and helper functions."""
    runs = collections.Counter()
    # Helper functions: count the body's gate runs once per call of the function.
    for m in list(re.finditer(r"\bfunction\s+([\w-]+)\s*(?:\([^)]*\))?\s*\{", cmd, re.I)):
        end = _block(cmd, m.end() - 1)
        body = cmd[m.end():end - 1]
        rest = cmd[:m.start()] + cmd[end:]
        calls = len(re.findall(r"(?:^|[;{(|]|&&)\s*%s(?![\w:.\\/-])" % re.escape(m.group(1)), rest, re.M))
        for gate, n in static_gate_runs(body).items():
            runs[gate] += n * calls
        cmd = cmd[:m.start()] + " " * (end - m.start()) + cmd[end:]
    # Loops over literal lists: PowerShell foreach / ForEach-Object, bash for.
    loops = [(m, m.group(2), m.group(1)) for m in re.finditer(r"\bforeach\s*\(\s*\$(\w+)\s+in\s+([^)]*)\)\s*\{", cmd, re.I)]
    loops += [(m, m.group(1), "_") for m in re.finditer(
        r"((?:['\"][^'\"\n]*['\"]\s*,\s*)*['\"][^'\"\n]*['\"])\s*\|\s*(?:ForEach-Object|%)\s*\{", cmd, re.I)]
    for m, spec, var in sorted(loops, key=lambda x: x[0].start(), reverse=True):
        end = _block(cmd, m.end() - 1)
        body, items = cmd[m.end():end - 1], _loop_items(spec)
        if re.search(r"\$(?:\{%s\}|\(\$%s\)|%s)\.(?:py|ps1)\b" % ((re.escape(var),) * 3), body):
            runs.update(i for i in items if i in GATES)  # foreach($s in 'validate-kanban',...){ python "$p/$s.py" }
        for gate, n in _executed(body).items():
            runs[gate] += n * len(items)
        cmd = cmd[:m.start()] + " " * (end - m.start()) + cmd[end:]
    for m in reversed(list(re.finditer(r"\bfor\s+(\w+)\s+in\s+([^;\n]*?)\s*;?\s*do\b(.*?)\bdone\b", cmd, re.S))):
        items = m.group(2).split() or [None]
        if re.search(r"\$\{?%s\}?\.(?:py|ps1)\b" % re.escape(m.group(1)), m.group(3)):
            runs.update(i for i in items if i in GATES)
        for gate, n in _executed(m.group(3)).items():
            runs[gate] += n * len(items)
        cmd = cmd[:m.start()] + " " * (m.end() - m.start()) + cmd[m.end():]
    runs.update(_executed(cmd))
    return runs


def gate_outcomes(name, inp, result):
    """[(gate, passed)] for one tool call; passed is None when the run happened but its verdict is hidden."""
    text, is_error = result if result else ("", False)
    if name and name.startswith(MCP_PREFIXES):
        gate = name.split("__")[-1].removeprefix("geeky_").replace("_", "-")
        m = re.search(r'"ok"\s*:\s*(true|false)', text)
        return [(gate, None if is_error or not m else m.group(1) == "true")]
    cmd = inp.get("command", "") if isinstance(inp, dict) else ""
    if not isinstance(cmd, str) or not cmd:
        return []
    static = static_gate_runs(cmd)
    out = []
    for gate in GATES:
        if not static[gate]:
            continue  # only results of gates this command executes (not a cat of handoff.md, not a read of the script)
        seen = [m.group(1).startswith(("OK", "DOD_OK")) for line in text.splitlines() if not CODE_LINE.search(line)
                for m in [GATE_LINES[gate].search(line)] if m]
        out += [(gate, p) for p in seen] + [(gate, None)] * max(0, static[gate] - len(seen))
    return out


def thread_split(flat):
    """Tool calls, dispatches and gate runs split by thread: main (no parent), orchestrator (made by a
    geeky-implement-orchestrator subagent) and workers (any other subagent). flat: [(id, name, input, parent, result)]."""
    orch = {cid for cid, name, inp, _, _ in flat if name in ("Agent", "Task") and is_orchestrator_type(inp.get("subagent_type"))}
    out = {k: {"tool_calls": collections.Counter(), "dispatches": collections.Counter(), "gates": collections.Counter()}
           for k in ("main", "orchestrator", "workers")}
    for cid, name, inp, parent, res in flat:
        t = out["main" if not parent else "orchestrator" if parent in orch else "workers"]
        t["tool_calls"][name] += 1
        if name in ("Agent", "Task"):
            t["dispatches"][str(inp.get("subagent_type") or "general-purpose")] += 1
        for gate, _ in gate_outcomes(name, inp, res):
            t["gates"][gate] += 1
    return {k: {kk: dict(vv.most_common()) for kk, vv in v.items()} for k, v in out.items()}


def harness_name(run_dir, override=None):
    if override:
        return override
    path = Path(run_dir) / 'run.json'
    return json.loads(path.read_text(encoding='utf-8-sig')).get('harness', 'claude-code') if path.exists() else 'claude-code'


def trace_adapter():
    spec = importlib.util.spec_from_file_location('codex_trace', Path(__file__).with_name('codex-trace.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def codex_trace(run_dir, process_path=None):
    return trace_adapter().load(run_dir, process_path)


def analyze(run_dir: Path, harness=None, process_path=None):
    codex = codex_trace(run_dir, process_path) if harness_name(run_dir, harness) == 'codex' else None
    stream = codex['stream'] if codex is not None else load_jsonl(run_dir / "stream.jsonl")
    session = codex['session'] if codex is not None else load_jsonl(run_dir / "session.jsonl")
    result = next((e for e in reversed(stream) if e.get("type") == "result"), {})

    # Tokens: modelUsage covers every model and every turn; result.usage is the last turn only.
    usage = result.get("modelUsage") or {}
    fresh = sum(u.get("inputTokens", 0) for u in usage.values())
    cache_read = sum(u.get("cacheReadInputTokens", 0) for u in usage.values())
    cache_write = sum(u.get("cacheCreationInputTokens", 0) for u in usage.values())
    output = sum(u.get("outputTokens", 0) for u in usage.values())
    tokens = {
        "input": fresh + cache_read + cache_write,
        "cached_input": cache_read,
        "cache_creation": cache_write,
        "output": output,
        "total": fresh + cache_read + cache_write + output,
        "by_model": {m: {k: u.get(k, 0) for k in ("inputTokens", "cacheReadInputTokens",
                                                  "cacheCreationInputTokens", "outputTokens")}
                     for m, u in usage.items()},
        "cost_usd_estimate": round(sum(u.get("costUSD", 0) for u in usage.values()), 4),
    }
    if not usage:  # no final result (timeout/crash) or no accounting: usage is unknown, not zero
        tokens = {k: None for k in tokens}

    # Tool calls, subagents, skills and validations from the stream
    main_tools, sub_tools, subagents, skills = (collections.Counter() for _ in range(4))
    validations = collections.Counter()
    results = {}
    for e in stream:
        if e.get("type") == "user":
            results.update(tool_results(e))
    gates = collections.defaultdict(lambda: dict.fromkeys(("pass", "fail", "unknown", "main", "sub"), 0))
    # (id, name, input, parent, result) for every call: the stream's, then calls only in subagent transcripts
    flat = [(c.get("id"), c.get("name"), c.get("input") or {}, e.get("parent_tool_use_id"), results.get(c.get("id")))
            for e in stream if e.get("type") == "assistant" for c in tool_uses(e)]
    extra, metas = ([], codex['metas']) if codex is not None else transcript_calls(run_dir, {f[0] for f in flat})
    flat += [(c["id"], c["name"], c["input"], c["parent"], c["result"]) for c in extra]
    for cid, name, inp, parent, res in flat:
        sub = bool(parent)
        (sub_tools if sub else main_tools)[name] += 1
        if name in ("Agent", "Task"):
            subagents[inp.get("subagent_type") or "general-purpose"] += 1
        if name == "Skill":
            skills[str(inp.get("skill", "")).split(":")[-1]] += 1
        cmd = inp.get("command", "") if isinstance(inp, dict) else ""
        if isinstance(cmd, str) and re.search(r"pytest|unittest", cmd):
            validations["sub" if sub else "main"] += 1
        for gate, passed in gate_outcomes(name, inp, res):
            g = gates[gate]
            g[{True: "pass", False: "fail", None: "unknown"}[passed]] += 1
            g["sub" if sub else "main"] += 1
    threads = thread_split(flat) if metas else None

    # Stages: Skill invocations on the main thread, timed from the session file
    stamps = [t for t in (ts(e) for e in session) if t]
    end = max(stamps) if stamps else None
    starts = [(str(c["input"].get("skill", "")).split(":")[-1], ts(e))
              for e in session if e.get("type") == "assistant" and not e.get("isSidechain")
              for c in tool_uses(e) if c.get("name") == "Skill" and ts(e)]
    stages = []
    for i, (name, start) in enumerate(starts):
        stop = starts[i + 1][1] if i + 1 < len(starts) else end
        stages.append({"name": name, "started_utc": start.isoformat(), "ended_utc": stop.isoformat(),
                       "minutes": round((stop - start).total_seconds() / 60, 1)})

    # Latency: main-thread user event -> next assistant event; idle: largest gap between events
    latencies, gaps, pending, prev = [], [], None, None
    for e in session:
        t = ts(e)
        if not t:
            continue
        if prev:
            gaps.append((t - prev).total_seconds())
        prev = t
        if e.get("isSidechain"):
            continue
        if e.get("type") == "user":
            pending = t
        elif e.get("type") == "assistant" and pending:
            latencies.append((t - pending).total_seconds() * 1000)
            pending = None

    model_calls = len({(e.get("message") or {}).get("id") for e in session
                       if e.get("type") == "assistant" and (e.get("message") or {}).get("id")})

    out = {
        "tokens": tokens,
        "model_calls": model_calls or None,
        "latency_median_ms": round(statistics.median(latencies)) if latencies else None,
        "latency_samples": len(latencies),
        "max_idle_gap_s": round(max(gaps)) if gaps else None,
        "stages": stages or None,
        "impl_review_rounds": skills.get("impl-review") or None,
        "skill_invocations": dict(skills),
        "tool_calls_main": dict(main_tools.most_common()),
        "tool_calls_subagents": dict(sub_tools.most_common()),
        "subagent_dispatches": dict(subagents),
        "validation_runs": dict(validations),
        "gate_invocations": {k: v["main"] + v["sub"] for k, v in gates.items()},
        "gate_results": dict(gates),
        "duration_api_ms": result.get("duration_api_ms"),
    }
    if metas:  # subagent transcripts present: the counts above include their calls
        out["subagent_transcripts"] = {"transcripts": len(metas), "calls_only_in_transcripts": len(extra),
                                       "by_type": dict(collections.Counter(str(m.get("agentType")) for m in metas.values())),
                                       "threads": threads}
    if codex is not None:
        out.update(tokens=codex['tokens'] or {k: None for k in
                   ('input', 'cached_input', 'cache_creation', 'output', 'reasoning', 'total', 'by_model', 'cost_usd_estimate')},
                   model_calls=codex['model_calls'], latency_median_ms=None, latency_samples=0,
                   max_idle_gap_s=codex['max_idle_gap_s'], trace_complete=codex['trace_complete'],
                   trace_errors=codex['trace_errors'], trace_warnings=codex['trace_warnings'],
                   harness='codex', usage_by_thread=codex['usage_by_thread'],
                   skill_evidence='successful explicit SKILL.md reads; no workflow completion inferred')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--token-ceiling", type=int)
    ap.add_argument("--analysis-only", action="store_true", help="write analysis.json only; leave run.json as stored")
    ap.add_argument('--harness', choices=('claude-code', 'codex'))
    ap.add_argument('--out', type=Path, help='write derived files here, preserving the input run folder')
    ap.add_argument('--process-evidence', type=Path)
    args = ap.parse_args()

    analysis = analyze(args.run_dir, harness=args.harness, process_path=args.process_evidence)
    output = args.out or args.run_dir
    output.mkdir(parents=True, exist_ok=True)
    (output / "analysis.json").write_text(json.dumps(analysis, indent=2), encoding="utf-8")
    if args.analysis_only:
        print(json.dumps({k: analysis[k] for k in ("gate_invocations", "gate_results")}, indent=2))
        return

    run_path = args.run_dir / "run.json"
    run = json.loads(run_path.read_text(encoding="utf-8-sig"))
    tokens = {k: v for k, v in analysis["tokens"].items() if k != "by_model"}
    tokens["reasoning"] = analysis['tokens'].get('reasoning') if analysis.get('harness') == 'codex' else (run.get("tokens") or {}).get("reasoning")
    run["tokens"] = tokens
    for key in ("model_calls", "latency_median_ms", "max_idle_gap_s", "stages", "impl_review_rounds"):
        run[key] = analysis[key]
    if args.token_ceiling:
        run["token_ceiling"] = args.token_ceiling
        run["over_token_ceiling"] = tokens["total"] > args.token_ceiling if tokens['total'] is not None else None
    if analysis.get('harness') == 'codex':
        run['analysis_status'] = 'complete' if analysis['trace_complete'] else 'incomplete'
        run['trace_complete'] = analysis['trace_complete']
        run['trace_errors'] = analysis['trace_errors']
        run['token_ceiling_policy'] = 'informational-until-codex-baseline'
        if not analysis['trace_complete']:
            run['reference_eligible'] = False
    (output / 'run.json').write_text(json.dumps(run, indent=2), encoding="utf-8")
    print(json.dumps({k: run.get(k) for k in ("tokens", "model_calls", "latency_median_ms",
                                              "max_idle_gap_s", "impl_review_rounds",
                                              "token_ceiling", "over_token_ceiling")}, indent=2))


if __name__ == "__main__":
    main()
