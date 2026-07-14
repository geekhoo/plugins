---
name: session-retrospective
description: Use when Gerald asks for the full log-mining retrospective over PAST Claude Code sessions — "run the retrospective", "retrospective flywheel", "mine the logs", "analyze work patterns across all sessions", "what patterns/stalls/sagas do the logs show", or the recurring (~monthly) work-patterns analysis that produces a findings report with fix classifications. Runs 10 deterministic stdlib-Python scanners over every ~/.claude JSONL (metadata, steering signals, topic recurrence, autonomy ratios, stall gaps, error taxonomy). Heavier than `session-friction-review` (fast counters, delta-since-last) and script-based unlike `self-audit` (subagent fan-out); prefer this when the deliverable is a quantitative multi-pattern report, not a quick pulse check.
---

# Session Retrospective — the log-mining flywheel

Quantitative retrospective over the whole `~/.claude/projects` transcript corpus
(~140 MB of JSONL; Python chosen because pwsh is too slow for this job). Iteration #5
of this flywheel produced the 12-pattern analysis behind `action-plan-2026-07-13.md`;
this skill exists so iteration #6 starts from tooling, not from scratch.

## Setup

The scanners write their JSON intermediates **next to themselves**, so never run them
in place inside the plugin. Copy `scripts/` from this skill into a scratch working
directory first, then run everything from there:

```powershell
Copy-Item "<this-skill>/scripts/*" $scratch/retro/ ; Set-Location $scratch/retro
```

Invocation chain (N1 — try in order, use the first that works; never assume bare
`python` resolves):

```
py -3 <script>   →   python3 <script>   →   python <script>
```

All scripts are stdlib-only — if the interpreter starts, they run. If a script itself
crashes, surface it in one line and fall back to a manual check of the same question;
never continue silently degraded.

## Run order

1. `scan_logs.py scan_results.json` — stream every `~/.claude` JSONL, per-session metadata (handles both transcript schemas). The output filename must be exactly `scan_results.json` in the script dir — later stages load it by that name.
2. `aggregate.py` — categories, monthly activity, tool mix, commands, errors, biggest sessions.
3. `deep_scan.py` — all human messages + steering-signal classification → `deep_results.json`.
4. `deep_analyze.py` — steering totals, most-steered sessions, retry clusters, interrupts.
5. `topics_recur.py` — topic recurrence spans (long-running saga detection).
6. `autonomy.py` — assistant:human message ratio, wall-clock durations.
7. `sagas.py <relpath...>` — replay the human messages of specific sessions found above.
8. `dig.py` — targeted digs: rejected tools, stall gaps, error sites.
9. `error_kinds.py`, `transcripts_topics.py` — error taxonomy; legacy-era topics.
10. `retro_extras.py [ROOT]` — standalone (walks the corpus itself, no `scan_results.json` needed): machine-vs-human session split, path-normalized/merged project dirs, dated event trend lines (`<synthetic>` API-error turns by subtype, minor tool/encoding classes), and main-vs-subagent token aggregates. See `scripts/README.md` for the capability detail and the 529-vs-`<synthetic>` note.

Stages 1–4 are the spine; 5–9 are follow-ups driven by what the spine surfaces; 10 is a self-contained cross-cut that also serves the A18 "verify prior fixes against recent logs" check.

## Findings: the fix-vehicle rule (T22)

Every finding in the retrospective report MUST be classified with the vehicle that
will fix it:

- **memory** — advice the model reads (behavioral rules, preferences)
- **skill** — a procedure the model follows on demand
- **hook** — a mechanism that runs even when the model has no turn
- **plugin-script** — a deterministic gate

Hard rule: any finding of the form **"the session went dark"** or **"a tool crashed
unnoticed"** MUST be classed hook or plugin-script — memories cannot fix what the
model never gets a turn to act on. (The stall class recurred across three
retrospectives precisely because it kept being answered with advice.)

## After the run

- Write the findings report next to the prior ones (`work-patterns-analysis-<date>.md`
  in `~/.claude`) so the next iteration is a delta, not a re-derivation.
- Turn findings into their vehicles before closing: memories via MEMORY.md, skills and
  scripts in the geekhoo-plugins marketplace (version bump + tests), hooks via
  `update-config`.
