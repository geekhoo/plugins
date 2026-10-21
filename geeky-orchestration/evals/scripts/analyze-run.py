"""Derive baseline-run measures from a run folder and merge them into run.json.

Usage: python analyze-run.py <run-folder> [--token-ceiling N]

Reads stream.jsonl (claude stream-json) and session.jsonl (Claude session transcript, which
carries the timestamps the stream lacks). Writes analysis.json and updates these run.json fields:
tokens (summed over every model in result.modelUsage), model_calls, latency_median_ms,
max_idle_gap_s, stages, impl_review_rounds, token_ceiling, over_token_ceiling.
Stdlib only.
"""
import argparse
import collections
import datetime as dt
import json
import re
import statistics
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


def analyze(run_dir: Path):
    stream = load_jsonl(run_dir / "stream.jsonl")
    session = load_jsonl(run_dir / "session.jsonl")
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

    # Tool calls, subagents, skills and validations from the stream
    main_tools, sub_tools, subagents, skills = (collections.Counter() for _ in range(4))
    validations = collections.Counter()
    gates = collections.Counter()
    for e in stream:
        if e.get("type") != "assistant":
            continue
        sub = bool(e.get("parent_tool_use_id"))
        for c in tool_uses(e):
            name, inp = c.get("name"), c.get("input") or {}
            (sub_tools if sub else main_tools)[name] += 1
            if name in ("Agent", "Task"):
                subagents[inp.get("subagent_type") or "general-purpose"] += 1
            if name == "Skill":
                skills[str(inp.get("skill", "")).split(":")[-1]] += 1
            cmd = inp.get("command", "") if isinstance(inp, dict) else ""
            if re.search(r"pytest|unittest", cmd):
                validations["sub" if sub else "main"] += 1
            m = re.search(r"(validate-planning-folder|validate-task-schema|validate-kanban|check-dod|check-commit)", cmd)
            if m:
                gates[m.group(1)] += 1
            elif name and name.startswith("mcp__geeky__"):
                gates[name.split("__")[-1]] += 1

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

    return {
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
        "gate_invocations": dict(gates),
        "duration_api_ms": result.get("duration_api_ms"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("--token-ceiling", type=int)
    args = ap.parse_args()

    analysis = analyze(args.run_dir)
    (args.run_dir / "analysis.json").write_text(json.dumps(analysis, indent=2), encoding="utf-8")

    run_path = args.run_dir / "run.json"
    run = json.loads(run_path.read_text(encoding="utf-8-sig"))
    tokens = {k: v for k, v in analysis["tokens"].items() if k != "by_model"}
    tokens["reasoning"] = run.get("tokens", {}).get("reasoning")
    run["tokens"] = tokens
    for key in ("model_calls", "latency_median_ms", "max_idle_gap_s", "stages", "impl_review_rounds"):
        run[key] = analysis[key]
    if args.token_ceiling:
        run["token_ceiling"] = args.token_ceiling
        run["over_token_ceiling"] = tokens["total"] > args.token_ceiling
    run_path.write_text(json.dumps(run, indent=2), encoding="utf-8")
    print(json.dumps({k: run.get(k) for k in ("tokens", "model_calls", "latency_median_ms",
                                              "max_idle_gap_s", "impl_review_rounds",
                                              "token_ceiling", "over_token_ceiling")}, indent=2))


if __name__ == "__main__":
    main()
