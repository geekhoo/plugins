import json, re, collections
from pathlib import Path
from datetime import datetime

sp = Path(__file__).parent
data = json.loads((sp / "scan_results.json").read_text(encoding="utf-8"))

tr = [d for d in data if d["cat"]=="transcript" and isinstance(d.get("first_ts"), str)]
tr.sort(key=lambda d: d["first_ts"])

MODE_RE = re.compile(r"^\[([a-z-]+)\]")
modes = collections.Counter()
def clean(fu):
    if not fu: return ""
    fu = re.sub(r"\s+", " ", fu)
    m = MODE_RE.match(fu)
    if m:
        modes[m.group(1)] += 1
        # strip mode preamble up to '---'
        if "---" in fu:
            fu = fu.split("---",1)[1]
    return fu.strip()[:150]

# monthly sample of prompts
bym = collections.defaultdict(list)
for d in tr:
    fu = clean(d.get("first_user"))
    if fu: bym[d["first_ts"][:7]].append((d["first_ts"][:10], fu, d["size"]))

for m in sorted(bym):
    items = bym[m]
    print(f"\n===== {m} ({len(items)} sessions w/ prompts, {len([d for d in tr if d['first_ts'][:7]==m])} total) =====")
    items.sort(key=lambda x: -x[2])
    for ts, fu, sz in items[:18]:
        print(f"  {ts} {sz/1e3:6.0f}KB  {fu}")

print("\n== MODE PREFIXES ==", dict(modes.most_common()))

# keyword themes across all transcript first prompts
words = collections.Counter()
STOP = set("the a an to of and in for is with on this that it as be we i you our do can are use using from at by or not have need want will make made like all should какой".split())
for d in tr:
    fu = clean(d.get("first_user")) or ""
    for w in re.findall(r"[a-zA-Z][a-zA-Z0-9_.-]{3,}", fu.lower()):
        if w not in STOP: words[w] += 1
print("\n== TOP KEYWORDS (transcript first prompts) ==")
print(", ".join(f"{w}:{n}" for w,n in words.most_common(50)))
