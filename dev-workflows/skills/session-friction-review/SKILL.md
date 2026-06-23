---
name: session-friction-review
description: Use when Gerald asks to quantify recurring friction across PAST Claude Code sessions (command/environment failures, *silent* non-blocking hook failures, sharp user corrections), or says "analyse our sessions", "where are we wasting time/rounds", "find conflicts/confusions/misunderstandings across sessions", "how are we doing", "review our collaboration", or wants a delta since the last review. Fast deterministic script scan (counts + --since delta, no subagents); for the deeper subagent-orchestrated retrospective use `self-audit`, and to inventory which conversations exist use `list-sessions`.
---

# Session Friction Review

Gerald has asked "examine all our sessions for conflicts / confusions / wasted rounds" three
times, and each time it was re-derived from scratch with ad-hoc greps. This skill bundles that
methodology so it is a one-command **delta**, not a fresh investigation.

## Quick path

```bash
py scripts/scan_friction.py            # full history, highest-friction sessions first
py scripts/scan_friction.py --since 2026-06-22   # only what's new since the last review
py scripts/scan_friction.py --top 10   # just the worst offenders
py scripts/scan_friction.py --format json   # for further computation
```

Plain stdlib Python; runs identically from PowerShell or Bash. On Windows invoke via `py`
(bare `python`/`python3` resolve via shims but `py` is the stable launcher - see
[[feedback-windows-shell]]).

## What it measures (and why these signatures)

Per top-level session transcript in `~/.claude/projects/*/` (subagent logs under `*/subagents/`
are skipped to avoid double counting):

| Signature | Why it matters |
|---|---|
| **SilentHook** (`Failed with non-blocking status code`) | The dangerous one. Non-blocking hook failures are invisible in normal use. 1,040 of these went unnoticed for ~a week in 2026-06 because an entire plugin safety layer (security-guidance, geeky guard) was dead from python-not-on-PATH. |
| **Python** (`python3: command not found` / `'python' is not recognized`) | Root cause of the above; also the model's own Unix-on-Windows reflex. |
| **Cmd** (other `command not found` / `is not recognized`) | Missing tools, Unix idioms on Windows. |
| **Corrections** (`that's not what`, `you keep`, `didn't ask`, ...) | Genuine misunderstandings. Historically RARE - Gerald is a terse director - so a rise here is a real signal worth reading in context. |
| **Apologies** (`you're absolutely right`, `my mistake`, ...) | Assistant concessions; often the tail of a wasted round. |

## How to interpret

- **SilentHook + Python spiking in a *recent* session** = the dead-hook pattern is back. Check
  `~/bin` is still on PATH and `py -3 -c ""` works (see [[feedback-windows-shell]]). This is the
  highest-value thing the scan can catch.
- **Corrections rising** = open those specific sessions and read the surrounding turns; this is
  where actual conflicts/misunderstandings live (rare, so worth the read).
- **Counts are transcript-line hits**, not distinct model actions - a single dead hook emits 2
  lines per tool call, so high counts usually mean "one broken thing fired a lot", not "many
  different mistakes". Read the `Top failing cmd` column to see what.

## After a review

- If it surfaces a NEW recurring pattern, capture the durable lesson as a `feedback` memory and
  add a one-line pointer to `MEMORY.md` - don't just fix the instance.
- Write findings to `analysis/collaboration-friction-analysis-<date>.md` so the next run is a
  delta against it, not a re-derivation. See the 2026-06-22 baseline.
- The fix is almost never "try harder next time" (doesn't persist) - it's an environment/config
  change or a skill/memory. Stop when the root cause is verified-fixed.
