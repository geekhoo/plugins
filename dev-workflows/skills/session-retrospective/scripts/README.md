# session-retrospective scripts (from 2026-07-13 log analysis)

Reusable scanners for the retrospective flywheel (action-plan T27). All stdlib-only Python; invoke via `py -3` (Windows) or `python3` (POSIX). Never bare `python` on Windows — PATH may shadow it with the wrong interpreter.

Order of use:
1. `scan_logs.py <out.json>` — stream every ~/.claude JSONL, per-session metadata (both schemas)
2. `aggregate.py` — categories, monthly activity, tool mix, commands, errors, biggest sessions
3. `deep_scan.py` — all human messages + steering-signal classification -> deep_results.json
4. `deep_analyze.py` — steering totals, most-steered sessions, retry clusters, interrupts
5. `topics_recur.py` — topic recurrence spans (long-run saga detection)
6. `autonomy.py` — assistant:human ratio, wall-clock durations
7. `sagas.py <relpath...>` — replay human messages of specific sessions
8. `dig.py` — targeted digs (rejected tools, stall gaps, error sites)
9. `error_kinds.py`, `transcripts_topics.py` — error taxonomy, legacy-era topics
10. `retro_extras.py` — machine-vs-human split, path-normalized project dirs, dated event/error
    trend lines, main-vs-subagent token aggregates (standalone; see section below)

Paths inside scripts assume output JSON sits next to them — run from one working dir.
Fix-vehicle rule (T22): classify every finding as memory / skill / hook / plugin-script;
"session went dark" or "tool crashed unnoticed" findings MUST become hooks/scripts, not memories.

## retro_extras.py — pass-2 capabilities (added iteration #6, 2026-07-14)

Standalone, stdlib-only. Walks the whole corpus itself (does NOT read scan_results.json),
so it runs independently of steps 1–2. Folds four capabilities the pass-2 fresh scan
derived ad hoc so future retrospectives get them for free.

```
py -3 retro_extras.py [ROOT]                # ROOT defaults to ~/.claude; human report
py -3 retro_extras.py [ROOT] --json OUT.json # also dump per-session + summary JSON
```

1. **Machine-session filter** — a session is machine-generated when its first real user
   prompt matches a `.remember` template ("summarizing a Claude Code session", "memory
   consolidation agent", "maximum non-destructive compression"). Reported as machine-vs-human
   counts so totals stop being inflated by consolidation runs. (~44 machine / ~669 human here.)
2. **Path normalization** — project-dir keys are lowercased and 8.3 short-path user segments
   collapsed (`GERALD~1.KHO` / `gerald-1-kho` → `gerald.khoo`, lowercase drive `c--` == `C--`)
   so fragmented dirs merge. The two `AppData-Local-Temp` dirs (35 + 8) merge into one.
   NOTE: the username mapping is machine-specific — adjust the `gerald` regex in `norm_key()`
   for another user's 8.3 short name.
3. **Named event/error trend lines, dated** — `<synthetic>` model turns (the API-error/retry
   surface; this is the line the pass-2 notes called "529/overload"), API-error turns split by
   subtype (spend-limit / session-limit / auth-401 / overload-529), plus the minor classes:
   malformed tool-call JSON, missing required tool param, "No such tool available", and
   PowerShell UTF-16 spaced-output mangling (`T h e   o p e r a t i o n`, scanned across ALL
   tool output, not just error bodies). Detectors key on API-error EVENTS, never on raw
   command/tool text, so a log that merely prints "overloaded" in a shell command is not
   miscounted as an overload event.
4. **Usage/token columns** — output / cache-create / cache-read / input tokens per session and
   in aggregate, split main-vs-subagent (subagent = `isSidechain` or an `agent-*`/`subagents/`
   file).

Pass-2 headline reproduction (this corpus, 2026-07-14): ~44 machine sessions (pass-2: ~46),
57 synthetic/API-error turns (pass-2: ~59), main cache-read ~1.5B / cache-create ~111M /
output ~12.6M. Note: no literal 529/overloaded text survives in the current corpus's error
turns — that subtype reads 0; the "529/overload" pass-2 headline maps to the `<synthetic>`
API-error/retry population.
