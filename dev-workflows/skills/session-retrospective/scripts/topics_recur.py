import json, re, collections
from pathlib import Path

ROOT = Path.home() / ".claude"
TOPICS = {
    "contract-replay/fixtures": re.compile(r"contract.replay|replay.gate|25 fixtures", re.I),
    "gap-backlog": re.compile(r"gap.backlog|integration-gaps|post-mf-stack", re.I),
    "spend/idempotency-txn": re.compile(r"SpendV1Controller|IdempotencyFilter|transaction nesting", re.I),
    "logic-map-builder": re.compile(r"logic map builder", re.I),
    "program-config/grid": re.compile(r"program.config|ProgramsV2|programsv2", re.I),
    "spendpage": re.compile(r"spendpage|spend page", re.I),
    "podman": re.compile(r"podman", re.I),
    "skill-install/reload": re.compile(r"reload-skills|install.*skill|skills we created", re.I),
    "memory-system": re.compile(r"\.remember|daily memory log|memory consolidation", re.I),
    "session-retrospective": re.compile(r"all our (conversations|sessions)|retrospective audit|inefficien", re.I),
    "figma": re.compile(r"figma", re.I),
    "auth/login-jwt": re.compile(r"\bjwt\b|auth(entication|orization)? (flow|token)|login endpoint", re.I),
    "knack-research": re.compile(r"knack", re.I),
    "devextreme-configurator": re.compile(r"configurator|dxdatagrid", re.I),
    "design-tokens": re.compile(r"design token|themebuilder", re.I),
}
# per-topic: set of session files (project era) whose USER messages mention it, with date range
hits = {k: {} for k in TOPICS}

for p in (ROOT / "projects").rglob("*.jsonl"):
    if "subagents" in [x.lower() for x in p.parts]: continue
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                try: rec = json.loads(line)
                except Exception: continue
                if rec.get("type") != "user": continue
                m = rec.get("message") or {}
                c = m.get("content")
                content = c if isinstance(c,str) else ("\n".join(b.get("text","") for b in c if isinstance(b,dict) and b.get("type")=="text") if isinstance(c,list) else "")
                if not content: continue
                ts = (rec.get("timestamp") or "")[:10]
                for k, rx in TOPICS.items():
                    if rx.search(content):
                        d = hits[k].setdefault(str(p.name)[:12], [ts, ts])
                        if ts:
                            if not d[0]: d[0]=ts
                            d[1] = max(d[1], ts) if d[1] else ts
    except Exception: pass

print(f"{'topic':28s} {'sessions':>8s}  span")
for k, v in sorted(hits.items(), key=lambda kv: -len(kv[1])):
    if not v: continue
    dates = [d for pair in v.values() for d in pair if d]
    span = f"{min(dates)} .. {max(dates)}" if dates else "?"
    print(f"{k:28s} {len(v):8d}  {span}")
