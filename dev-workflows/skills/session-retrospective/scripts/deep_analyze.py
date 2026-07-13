import json, re, collections
from pathlib import Path

sp = Path(__file__).parent
S = json.loads((sp / "deep_results.json").read_text(encoding="utf-8"))

def month(s): return (s.get("first_ts") or "")[:7]

# 1. steering totals by kind and by month
kinds = collections.Counter(); bym = collections.defaultdict(collections.Counter)
msgs_bym = collections.Counter()
for s in S:
    m = month(s)
    for um in s["user_msgs"]:
        if m: msgs_bym[m] += 1
        for fl in um["flags"]:
            kinds[fl] += 1
            if m: bym[m][fl] += 1
print("== STEERING FLAG TOTALS ==", dict(kinds))
print("\n== BY MONTH (msgs, corrections, quality-flags) ==")
for m in sorted(bym):
    c = bym[m]
    print(f"{m}: msgs={msgs_bym[m]:4d} correction={c.get('correction',0):3d} quality={c.get('quality-flag',0):3d} scope={c.get('scope-guard',0):3d} resume={c.get('resume',0):2d}")

# 2. most-steered sessions
def steer_score(s): return s["steer"].get("correction",0) + s["interrupts"]*2 + s["rejects"]
top = sorted(S, key=lambda s: -steer_score(s))[:15]
print("\n== MOST-STEERED SESSIONS ==")
for s in top:
    if steer_score(s)==0: break
    print(f"score={steer_score(s):2d} corr={s['steer'].get('correction',0)} int={s['interrupts']} rej={s['rejects']} msgs={len(s['user_msgs'])} [{s['cat']}] {month(s)} {s['path'][:80]}")

# 3. sample correction quotes chronologically (project era only)
print("\n== CORRECTION QUOTES (project era, chronological) ==")
quotes = []
for s in S:
    if s["cat"] == "transcript": continue
    for um in s["user_msgs"]:
        if "correction" in um["flags"] and um["text"] and len(um["text"])>15:
            quotes.append((um["ts"] or month(s), um["text"], s["path"][:60]))
quotes.sort(key=lambda q: q[0] or "")
for ts, txt, pth in quotes[:60]:
    print(f"{(ts or '?')[:10]}  {txt[:200]}")

# 4. repeated-prompt clusters (near-duplicate first user messages across sessions)
print("\n== REPEATED FIRST-PROMPT CLUSTERS (cross-session retries) ==")
firsts = collections.defaultdict(list)
for s in S:
    if not s["user_msgs"]: continue
    fu = s["user_msgs"][0]["text"].lower()
    fu = re.sub(r"[^a-z0-9 ]"," ",fu)
    key = " ".join(fu.split()[:12])
    if len(key) > 30: firsts[key].append((month(s), s["cat"], s["path"][:60]))
for k, v in sorted(firsts.items(), key=lambda kv: -len(kv[1])):
    if len(v) < 3: continue
    cats = collections.Counter(c for _,c,_ in v)
    print(f"{len(v):3d}x [{dict(cats)}] {k[:100]}")

# 5. interrupts & rejects detail
print("\n== INTERRUPT/REJECT SESSIONS ==")
for s in S:
    if s["interrupts"] or s["rejects"]:
        print(f"int={s['interrupts']} rej={s['rejects']} [{s['cat']}] {month(s)} {s['path'][:80]}")
