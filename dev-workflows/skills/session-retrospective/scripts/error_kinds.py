import json, re, collections
from pathlib import Path

ROOT = Path.home() / ".claude" / "projects"
kinds = collections.Counter()
samples = {}

PATTERNS = [
    ("not-recognized (cmd missing)", re.compile(r"is not recognized as|command not found|CommandNotFoundException", re.I)),
    ("python3-missing", re.compile(r"python3(?::| was not found|' is not)", re.I)),
    ("path/file-not-found", re.compile(r"No such file or directory|Cannot find path|does not exist", re.I)),
    ("permission/denied", re.compile(r"Access is denied|EPERM|EACCES|PermissionError", re.I)),
    ("bash-vs-pwsh syntax", re.compile(r"ParserError|is not a PowerShell|Unexpected token|Missing terminator", re.I)),
    ("edit old_string mismatch", re.compile(r"old_string.*not found|String to replace not found|found multiple times", re.I)),
    ("file-not-read-yet", re.compile(r"has not been read yet|must Read", re.I)),
    ("permission-denied-by-user", re.compile(r"User rejected|user doesn't want|Permission to use .* denied|requested permissions", re.I)),
    ("api/overload", re.compile(r"overloaded|rate limit|529|API Error", re.I)),
    ("timeout", re.compile(r"timed out|timeout", re.I)),
    ("port-in-use", re.compile(r"EADDRINUSE|address already in use|port.*in use", re.I)),
    ("git", re.compile(r"fatal: |not a git repository", re.I)),
    ("hook-blocked", re.compile(r"hook|Hook", re.I)),
]

for p in ROOT.rglob("*.jsonl"):
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if '"is_error":true' not in line and '"is_error": true' not in line:
                    continue
                # extract tool_result content text
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                m = rec.get("message") or {}
                c = m.get("content")
                texts = []
                if isinstance(c, list):
                    for b in c:
                        if isinstance(b, dict) and b.get("type")=="tool_result" and b.get("is_error"):
                            cc = b.get("content")
                            if isinstance(cc, str): texts.append(cc)
                            elif isinstance(cc, list):
                                texts += [x.get("text","") for x in cc if isinstance(x,dict)]
                txt = "\n".join(texts)[:2000]
                if not txt: continue
                matched = False
                for name, rx in PATTERNS:
                    if rx.search(txt):
                        kinds[name] += 1
                        if name not in samples: samples[name] = txt[:180].replace("\n"," ")
                        matched = True
                        break
                if not matched:
                    kinds["other"] += 1
                    key = "other:" + txt[:40]
                    if kinds[key] == 0: pass
                    kinds[key] += 1
    except Exception:
        pass

print("== ERROR KINDS (projects/*) ==")
for k, n in kinds.most_common(40):
    print(f"{n:5d}  {k}")
print("\n== SAMPLES ==")
for k, s in samples.items():
    print(f"[{k}] {s}\n")
