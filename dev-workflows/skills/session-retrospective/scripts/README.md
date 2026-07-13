# session-retrospective scripts (from 2026-07-13 log analysis)

Reusable scanners for the retrospective flywheel (action-plan T27). All stdlib-only Python; invoke via `py -3` / `python3` / `python`.

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

Paths inside scripts assume output JSON sits next to them — run from one working dir.
Fix-vehicle rule (T22): classify every finding as memory / skill / hook / plugin-script;
"session went dark" or "tool crashed unnoticed" findings MUST become hooks/scripts, not memories.
