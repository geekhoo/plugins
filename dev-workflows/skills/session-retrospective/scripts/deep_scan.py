import json, re, collections, sys
from pathlib import Path

ROOT = Path.home() / ".claude"
OUT = Path(__file__).parent / "deep_results.json"

STEER = [
    ("correction", re.compile(r"\b(no[,.!]|not what i|that'?s wrong|incorrect|you did(n'?t| not)|why did you|i said|i asked|i told|instead of|revert|undo|roll ?back|regression|you broke|broke the|still (not|broken|failing|wrong)|again[,.!? ]|didn'?t work|does ?n'?t work|not working|same (error|issue|problem)|missed|you skipped|stop[,.!]|wait[,.!])", re.I)),
    ("scope-guard", re.compile(r"\b(only|just|don'?t (change|touch|modify)|keep it simple|too (much|many|complex)|over-?engineer|minimal|scope)\b", re.I)),
    ("quality-flag", re.compile(r"\b(hallucinat|made up|fabricat|assum|verify|double.?check|are you sure|prove|evidence|validate)\b", re.I)),
    ("frustration", re.compile(r"(\?\?|!!|wtf|seriously|come on|argh|useless|waste)", re.I)),
]
INTERRUPT = "[Request interrupted by user"
REJECT = "doesn't want to proceed"
RESUME = re.compile(r"\b(where (were|are) we|continue|resume|carry on|pick up|where we left)\b", re.I)
TODO_NUDGE = "TODO CONTINUATION"

sessions = []
for p in ROOT.rglob("*.jsonl"):
    parts = [x.lower() for x in p.parts]
    if "tests" in parts: continue
    cat = "transcript" if "transcripts" in parts else ("subagent" if "subagents" in parts else "project")
    s = {"path": str(p.relative_to(ROOT)), "cat": cat, "first_ts": None, "last_ts": None,
         "cwd": None, "user_msgs": [], "interrupts": 0, "rejects": 0, "todo_nudges": 0,
         "assistant_msgs": 0, "steer": collections.Counter()}
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if REJECT in line: s["rejects"] += 1
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                ts = rec.get("timestamp")
                if isinstance(ts, str):
                    if s["first_ts"] is None: s["first_ts"] = ts
                    s["last_ts"] = ts
                if s["cwd"] is None and rec.get("cwd"): s["cwd"] = rec["cwd"]
                t = rec.get("type")
                if t == "assistant":
                    s["assistant_msgs"] += 1
                    continue
                if t != "user": continue
                content = rec.get("content")
                if content is None:
                    m = rec.get("message") or {}
                    c = m.get("content")
                    if isinstance(c, str): content = c
                    elif isinstance(c, list):
                        texts = [b.get("text","") for b in c if isinstance(b,dict) and b.get("type")=="text"]
                        content = "\n".join(texts)
                if not isinstance(content, str) or not content.strip(): continue
                if content.startswith("<local-command") or content.startswith("<command-name>"): continue
                if INTERRUPT in content:
                    s["interrupts"] += 1
                    content = content.replace(INTERRUPT + " to send the following message]", "").replace(INTERRUPT + "]","").strip()
                    if not content: continue
                if TODO_NUDGE in content:
                    s["todo_nudges"] += 1
                    continue
                if "system-reminder" in content[:60]: continue
                flags = []
                for name, rx in STEER:
                    if rx.search(content): flags.append(name)
                if RESUME.search(content[:200]): flags.append("resume")
                for fl in flags: s["steer"][fl] += 1
                s["user_msgs"].append({"ts": ts if isinstance(ts,str) else None,
                                       "text": re.sub(r"\s+"," ",content)[:280],
                                       "flags": flags})
    except Exception as e:
        s["error"] = str(e)
    s["steer"] = dict(s["steer"])
    sessions.append(s)

OUT.write_text(json.dumps(sessions), encoding="utf-8")
n_u = sum(len(s["user_msgs"]) for s in sessions)
print(f"{len(sessions)} sessions, {n_u} human user messages captured")
print("interrupts:", sum(s['interrupts'] for s in sessions),
      "rejects:", sum(s['rejects'] for s in sessions),
      "todo_nudges:", sum(s['todo_nudges'] for s in sessions))
