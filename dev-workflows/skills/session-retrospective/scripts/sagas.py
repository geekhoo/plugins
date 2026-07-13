import json, re, sys
from pathlib import Path

ROOT = Path.home() / ".claude"
AUTOMATED = re.compile(r"^(You are|Base directory|# |## |<task-notification>|This session is being continued|Apply maximum non-destructive|\d+\. TASK:|Execute task|Environment: Windows)", re.I)

def human_msgs(path, maxlen=260):
    out = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            try: rec = json.loads(line)
            except Exception: continue
            if rec.get("type") != "user": continue
            if rec.get("isSidechain"): continue
            m = rec.get("message") or {}
            c = m.get("content")
            content = None
            if isinstance(c, str): content = c
            elif isinstance(c, list):
                texts = [b.get("text","") for b in c if isinstance(b,dict) and b.get("type")=="text"]
                content = "\n".join(texts)
            if not content or not content.strip(): continue
            if content.startswith("<") and "command-name" in content[:200]:
                cm = re.search(r"<command-name>([^<]+)</command-name>", content)
                ca = re.search(r"<command-args>([^<]*)</command-args>", content)
                out.append((rec.get("timestamp","")[:16], f"[CMD {cm.group(1) if cm else '?'} {ca.group(1)[:80] if ca else ''}]"))
                continue
            if content.startswith("<"): continue
            if "system-reminder" in content[:80]: continue
            if AUTOMATED.match(content.strip()): continue
            txt = re.sub(r"\s+"," ",content).strip()
            interrupted = "[Request interrupted" in content
            out.append((rec.get("timestamp","")[:16], ("(INT) " if interrupted else "") + txt[:maxlen]))
    return out

for arg in sys.argv[1:]:
    p = ROOT / arg
    print(f"\n{'='*100}\n### {arg}\n{'='*100}")
    for ts, txt in human_msgs(p):
        print(f"{ts}  {txt}")
