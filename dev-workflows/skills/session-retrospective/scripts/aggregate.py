import json, collections, re, sys
from pathlib import Path
from datetime import datetime

sp = Path(__file__).parent
data = json.loads((sp / "scan_results.json").read_text(encoding="utf-8"))

def week(ts):
    if not ts: return None
    try:
        d = datetime.fromisoformat(ts.replace("Z","+00:00"))
        return d.strftime("%G-W%V")
    except Exception: return None

def month(ts):
    if ts is None: return None
    if isinstance(ts, (int, float)):
        try:
            return datetime.utcfromtimestamp(ts/1000 if ts > 1e12 else ts).strftime("%Y-%m")
        except Exception: return None
    return ts[:7]

cats = collections.Counter(d["cat"] for d in data)
print("== CATEGORIES ==", dict(cats))

# activity per month by category
act = collections.defaultdict(collections.Counter)
for d in data:
    m = month(d["first_ts"])
    if m: act[m][d["cat"]] += 1
print("\n== SESSIONS PER MONTH (by category) ==")
for m in sorted(act):
    print(m, dict(act[m]))

# projects distribution (main project sessions only)
proj = collections.Counter()
projsz = collections.Counter()
for d in data:
    if d["cat"] == "project" and "subagents" not in d["path"]:
        top = d["path"].split("\\")[1] if "\\" in d["path"] else d["path"]
        proj[top] += 1
        projsz[top] += d["size"]
print("\n== PROJECT SESSION COUNTS ==")
for k, v in proj.most_common(20):
    print(f"{v:4d}  {projsz[k]/1e6:7.1f}MB  {k}")

# tool usage overall
tools = collections.Counter()
for d in data:
    for t, n in d["tools"].items(): tools[t] += n
print("\n== TOP 30 TOOLS ==")
for t, n in tools.most_common(30): print(f"{n:6d}  {t}")

# commands
cmds = collections.Counter()
for d in data:
    for c, n in d["commands"].items(): cmds[c] += n
print("\n== TOP 30 SLASH COMMANDS ==")
for c, n in cmds.most_common(30): print(f"{n:5d}  {c}")

# errors
tot_err = sum(d["errors"] for d in data)
tot_lines = sum(d["lines"] for d in data)
print(f"\n== ERRORS == total tool-error/api-error lines: {tot_err} across {tot_lines} lines")
worst = sorted(data, key=lambda d: -d["errors"])[:12]
for d in worst:
    print(f"{d['errors']:5d} err / {d['lines']:6d} lines  [{d['cat']}] {d['path'][:90]}  first={month(d['first_ts'])}")

# models
models = collections.Counter()
for d in data:
    for m in d["models"]: models[m] += 1
print("\n== MODELS (file count containing) ==", dict(models.most_common(12)))

# biggest sessions
print("\n== 15 BIGGEST SESSIONS ==")
for d in sorted(data, key=lambda d: -d["size"])[:15]:
    fu = (d["first_user"] or "").replace("\n"," ")[:110]
    print(f"{d['size']/1e6:6.1f}MB {d['lines']:6d}ln [{d['cat']}] {month(d['first_ts'])} {d['path'][:70]}\n        >> {fu}")

# first user messages for project sessions, chronological
print("\n== PROJECT SESSION FIRST PROMPTS (chronological) ==")
ps = [d for d in data if d["cat"]=="project" and d["first_user"] and isinstance(d["first_ts"], str)]
ps.sort(key=lambda d: d["first_ts"])
for d in ps:
    fu = re.sub(r"\s+"," ", d["first_user"])[:140]
    _home = str(Path.home())
    cwd = (d["cwd"] or "?").replace(_home, "~").replace("C:\\Users\\gerald.khoo", "~")
    print(f"{d['first_ts'][:10]} [{cwd[:45]:45s}] {fu}")
