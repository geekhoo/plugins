"""Per task: first Done insertion ("+- [x] Tn"), handoff.md in the same patch, DOD_OK before, validate_kanban OK after."""
import json, re, sys, pathlib

run = pathlib.Path(sys.argv[1])
calls, ev = {}, []
for f in [run / "session.jsonl"]:
    for line in f.open(encoding="utf-8"):
        o = json.loads(line); p = o.get("payload", {}); t = p.get("type")
        if t == "function_call":
            calls[p["call_id"]] = (o["timestamp"], p["name"], p.get("arguments", ""))
        elif t == "function_call_output" and p.get("call_id") in calls:
            ts, n, a = calls[p["call_id"]]; out = p.get("output"); out = out if isinstance(out, str) else json.dumps(out)
            ev.append((ts, n, a, out))
ev.sort(key=lambda e: e[0])
done, dod, vk = {}, [], []
for ts, n, a, out in ev:
    if n == "exec_command":
        for tid in re.findall(r"DOD_OK: (T\d+)", out):
            dod.append((ts, tid))
        if "kanban.md" in a and "apply-patch" in a:
            cmd = json.loads(a).get("cmd", a)
            for tid in re.findall(r"\n\+- \[x\] (T\d+)\b", cmd):
                if tid not in done:
                    done[tid] = (ts, "handoff.md" in cmd, ".heartbeat" in cmd)
        if "validate-kanban" in a and "OK" in out[:400]:
            vk.append(ts)
    elif n.endswith("validate_kanban") and "OK" in out[:400]:
        vk.append(ts)
for tid in sorted(done, key=lambda t: int(t[1:])):
    ts, hand, hb = done[tid]
    before = [d for d in dod if d[1] == tid and d[0] <= ts]
    after = [v for v in vk if v >= ts]
    print(tid, "done", ts, "handoff_same_patch", hand, "heartbeat", hb,
          "dod_ok_before", len(before), "validate_kanban_after", after[0] if after else None)
