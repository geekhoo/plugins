import json, collections
from pathlib import Path
from datetime import datetime

sp = Path(__file__).parent
S = json.loads((sp / "deep_results.json").read_text(encoding="utf-8"))

def dur_h(s):
    try:
        a = datetime.fromisoformat(s["first_ts"].replace("Z","+00:00"))
        b = datetime.fromisoformat(s["last_ts"].replace("Z","+00:00"))
        return (b-a).total_seconds()/3600
    except Exception: return None

bym = collections.defaultdict(lambda: [0,0])
for s in S:
    m = (s.get("first_ts") or "")[:7]
    if not m: continue
    bym[m][0] += s["assistant_msgs"]
    bym[m][1] += len(s["user_msgs"])
print("== AUTONOMY: assistant msgs per human msg, by month ==")
for m in sorted(bym):
    a,u = bym[m]
    print(f"{m}: assistant={a:6d} human={u:5d} ratio={a/max(u,1):6.1f}")

print("\n== LONGEST WALL-CLOCK SESSIONS ==")
withd = [(dur_h(s), s) for s in S if dur_h(s)]
withd.sort(key=lambda x: -x[0])
for d, s in withd[:12]:
    print(f"{d:6.1f}h  [{s['cat']}] {(s['first_ts'] or '')[:10]}  msgs={len(s['user_msgs']):3d} asst={s['assistant_msgs']:5d}  {s['path'][:75]}")
