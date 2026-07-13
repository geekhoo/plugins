import json, os, re, sys, collections
from pathlib import Path

ROOT = Path.home() / ".claude"
out = []

def categorize(p: Path):
    parts = [x.lower() for x in p.parts]
    if "transcripts" in parts: return "transcript"
    if "subagents" in parts: return "subagent"
    if "tests" in parts: return "fixture"
    if "projects" in parts: return "project"
    return "other"

def first_ts(rec):
    return rec.get("timestamp") or (rec.get("message") or {}).get("timestamp")

CMD_RE = re.compile(r"<command-name>([^<]+)</command-name>")

for p in ROOT.rglob("*.jsonl"):
    cat = categorize(p)
    info = {
        "path": str(p.relative_to(ROOT)),
        "cat": cat,
        "size": p.stat().st_size,
        "lines": 0,
        "first_ts": None, "last_ts": None,
        "cwd": None,
        "first_user": None,
        "user_msgs": 0, "assistant_msgs": 0,
        "tools": collections.Counter(),
        "errors": 0,
        "commands": collections.Counter(),
        "models": set(),
        "version": None,
    }
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line: continue
                info["lines"] += 1
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                ts = first_ts(rec)
                if ts:
                    if info["first_ts"] is None: info["first_ts"] = ts
                    info["last_ts"] = ts
                if info["cwd"] is None and rec.get("cwd"): info["cwd"] = rec.get("cwd")
                if info["version"] is None and rec.get("version"): info["version"] = rec.get("version")
                t = rec.get("type")
                if t == "user":
                    # transcript schema: content is str; project schema: message.content
                    content = rec.get("content")
                    if content is None:
                        m = rec.get("message") or {}
                        c = m.get("content")
                        if isinstance(c, str): content = c
                        elif isinstance(c, list):
                            texts = [b.get("text","") for b in c if isinstance(b,dict) and b.get("type")=="text"]
                            content = "\n".join(texts) if texts else None
                    if isinstance(content, str) and content.strip():
                        cm = CMD_RE.search(content)
                        if cm:
                            info["commands"][cm.group(1).strip()] += 1
                        if not content.startswith("<") or cm:
                            info["user_msgs"] += 1
                            if info["first_user"] is None and "system-reminder" not in content[:100]:
                                info["first_user"] = content[:400]
                elif t == "assistant":
                    info["assistant_msgs"] += 1
                    m = rec.get("message") or {}
                    if m.get("model"): info["models"].add(m["model"])
                    c = m.get("content")
                    if isinstance(c, list):
                        for b in c:
                            if isinstance(b, dict) and b.get("type") == "tool_use":
                                info["tools"][b.get("name","?")] += 1
                elif t == "tool_use":
                    info["tools"][rec.get("tool_name","?")] += 1
                # errors
                if '"is_error":true' in line or '"is_error": true' in line or rec.get("isApiErrorMessage"):
                    info["errors"] += 1
                if t == "user":
                    m = rec.get("message") or {}
                    c = m.get("content")
                    if isinstance(c, list):
                        for b in c:
                            if isinstance(b, dict) and b.get("type")=="tool_result" and b.get("is_error"):
                                info["errors"] += 1
    except Exception as e:
        info["error_reading"] = str(e)
    info["tools"] = dict(info["tools"].most_common(15))
    info["commands"] = dict(info["commands"])
    info["models"] = sorted(info["models"])
    out.append(info)

outfile = Path(sys.argv[1])
outfile.write_text(json.dumps(out), encoding="utf-8")
print(f"scanned {len(out)} files")
