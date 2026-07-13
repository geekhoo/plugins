import json, re, collections, sys
from pathlib import Path
from datetime import datetime

ROOT = Path.home() / ".claude"

def iter_recs(p):
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            try: yield json.loads(line)
            except Exception: continue

print("########## DIG 1: rejected tools in d39bd9b4 (/update-config session, 17 rejects) ##########")
p = ROOT / "projects/C--Users-gerald-khoo--claude/d39bd9b4-b905-464d-8ffc-96eb11e12dd2.jsonl"
last_tool = {}
for rec in iter_recs(p):
    if rec.get("type") == "assistant":
        for b in (rec.get("message") or {}).get("content") or []:
            if isinstance(b, dict) and b.get("type") == "tool_use":
                last_tool[b.get("id")] = (b.get("name"), json.dumps(b.get("input"))[:150])
    if rec.get("type") == "user":
        c = (rec.get("message") or {}).get("content")
        if isinstance(c, list):
            for b in c:
                if isinstance(b, dict) and b.get("type")=="tool_result":
                    cc = b.get("content")
                    txt = cc if isinstance(cc,str) else json.dumps(cc)[:300] if cc else ""
                    if "doesn't want to proceed" in str(txt):
                        name, inp = last_tool.get(b.get("tool_use_id"), ("?","?"))
                        print(f"  REJECTED: {name}  input={inp}")

print("\n########## DIG 2: stall anatomy of 97c9accc (Jul 1-5 geeky-implement) ##########")
p = ROOT / "projects/C--Users-gerald-khoo-Codes-mf-stack/97c9accc-d2a5-4661-8a42-6049d39bbcc5.jsonl"
events = []
for rec in iter_recs(p):
    ts = rec.get("timestamp") or ""
    t = rec.get("type")
    if t == "assistant":
        for b in (rec.get("message") or {}).get("content") or []:
            if isinstance(b, dict) and b.get("type") == "tool_use":
                nm = b.get("name","")
                if nm in ("Agent","Task","TaskOutput","TaskStop","Bash","PowerShell") or "task" in nm.lower():
                    inp = json.dumps(b.get("input"))[:110]
                    events.append((ts, f"TOOL {nm} {inp}"))
    elif t == "user":
        c = (rec.get("message") or {}).get("content")
        if isinstance(c, str) and len(c) < 400 and not c.startswith("<"):
            events.append((ts, f"HUMAN: {c[:110]}"))
# find gaps > 60min between consecutive events
print("  -- timeline gaps > 90min --")
prev = None
for ts, ev in events:
    try: d = datetime.fromisoformat(ts.replace("Z","+00:00"))
    except Exception: continue
    if prev and (d - prev[0]).total_seconds() > 5400:
        print(f"  GAP {((d-prev[0]).total_seconds()/3600):5.1f}h  after: {prev[1][:100]}")
        print(f"         resumed by: {ev[:100]}")
    prev = (d, ev)
tooluse = collections.Counter(ev.split()[1] for ts,ev in events if ev.startswith("TOOL"))
print("  -- orchestration tool mix --", dict(tooluse.most_common(10)))

print("\n########## DIG 3: validator traceback ##########")
for rec in iter_recs(p):
    if rec.get("type")!="user": continue
    c = (rec.get("message") or {}).get("content")
    if isinstance(c, list):
        for b in c:
            if isinstance(b,dict) and b.get("type")=="tool_result":
                txt = str(b.get("content"))
                if "Traceback" in txt and "geeky" in txt.lower()[:400]:
                    print(" ", txt[:600].replace("\\n","\n  ")); break

print("\n########## DIG 4: write-before-read examples in subagent logs ##########")
count = 0
for sp2 in (ROOT/"projects").rglob("subagents/*.jsonl"):
    lt = {}
    for rec in iter_recs(sp2):
        if rec.get("type")=="assistant":
            for b in (rec.get("message") or {}).get("content") or []:
                if isinstance(b,dict) and b.get("type")=="tool_use":
                    lt[b.get("id")] = (b.get("name"), json.dumps(b.get("input"))[:120])
        if rec.get("type")=="user":
            c = (rec.get("message") or {}).get("content")
            if isinstance(c, list):
                for b in c:
                    if isinstance(b,dict) and b.get("type")=="tool_result" and b.get("is_error"):
                        txt = str(b.get("content"))
                        if "has not been read yet" in txt:
                            nm, inp = lt.get(b.get("tool_use_id"), ("?","?"))
                            if count < 8:
                                print(f"  {sp2.parent.parent.name[:12]}/{sp2.name[:20]}: {nm} {inp}")
                            count += 1
print(f"  total write-before-read in subagent logs: {count}")

print("\n########## DIG 5: contract-replay saga key human messages ##########")
RX = re.compile(r"contract.replay|replay.gate|25 fixtures", re.I)
msgs = []
for pp in (ROOT/"projects").rglob("*.jsonl"):
    if "subagents" in str(pp): continue
    for rec in iter_recs(pp):
        if rec.get("type")!="user": continue
        c = (rec.get("message") or {}).get("content")
        content = c if isinstance(c,str) else None
        if content and RX.search(content) and not content.startswith("<"):
            if not re.match(r"^(You are|# |\d+\. TASK)", content.strip()):
                msgs.append(((rec.get("timestamp") or "")[:16], re.sub(r"\s+"," ",content)[:200]))
msgs.sort()
seen = set()
for ts, m in msgs:
    k = m[:60]
    if k in seen: continue
    seen.add(k)
    print(f"  {ts}  {m}")
