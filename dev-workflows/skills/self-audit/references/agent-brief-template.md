# Subagent brief template

Fill the `<<placeholders>>` and dispatch one filled copy per project group, all in a single turn. This is a template — tune the project-specific hints, keep the rest.

---

You're doing a retrospective audit of past Claude Code conversations to find patterns of inefficiency — places where Claude (the AI assistant) took more turns/tool-calls than necessary, got stuck, looped on a failing approach, misunderstood the request, or had to be corrected by the user — and how each was eventually resolved (self-corrected vs. explicit user correction). This feeds into updating Claude's persistent memory so the same mistakes don't recur. You are one of several parallel agents each covering a different project; your scope is the project at `<<PROJECT_PATH>>`.

## Already-known patterns — don't just re-report these unless you find something NEW

The following are already captured as feedback memories. Only flag a fresh instance if it reveals something new (a fix that didn't stick, or a meaningfully different/sharper variant). Prioritize patterns NOT on this list:

<<PASTE CURRENT MEMORY BASELINE HERE — the feedback_*.md summaries + user_profile, read fresh this run>>

## Project-specific hints

<<e.g. "this is a .NET backend — watch for build/test retry loops"; "Playwright session — watch for failed selectors / repeated screenshots"; "first prompt is a `<local-command-caveat>` placeholder, the real request is further down"; or "none">>

## What to look for (hypotheses, not a rigid checklist — read surrounding context)

- Tool calls that errored and needed a retry with a different approach (`is_error` in tool_result blocks)
- The same kind of tool call attempted repeatedly with small variations (trial-and-error loops)
- Explicit user corrections — short sharp messages ("no", "don't", "stop", "that's not what I meant"), rejected tool permissions, or harness rejection text ("doesn't want to proceed with this tool use" / "STOP what you are doing")
- Assistant self-correction/backtracking ("let me reconsider", "I made a mistake", "apologies", "that didn't work")
- Places where the assistant misunderstood the request and had to redo work after clarification
- Environment friction: `command not found`, non-zero exits, `Cancelled: parallel tool call`

## Transcript format (so you don't rediscover it)

Each line of a `.jsonl` transcript is one JSON object. `type` is `user`, `assistant`, `queue-operation`, or `attachment`. `message.content` is either a plain string or an array of content blocks — `{"type":"text",...}` for prose, `{"type":"tool_use","name":...,"input":...}` / `{"type":"tool_result",...}` for tool activity. Use the **Grep tool** (not shell grep) — it handles arbitrarily large files and works the same on Windows. Do NOT `Read()` a large transcript in full; grep for signal patterns first, then read small windows (-B/-A) around hits. (Some real transcripts exceed 1000 messages; individual JSONL lines can also blow the single-read token limit because of long thinking blocks — extract `"text":"..."` with `-o` if a raw line read overflows.)

## Your assigned files

<<LIST EXACT FILE PATHS + message counts, one per line>>

## Output format — exactly this, under ~500 words total

```
## <<PROJECT_PATH>>
### Sessions skimmed
- <id, message count, one-line topic>   (repeat per session)

### Incidents (cap at ~6 most significant — rank by cost × generalizability, not first-found)
1. **<short pattern name>** — session <short id>, ~<rough location>
   - What happened: <1-2 sentences>
   - Cost: <rough extra turns/tool-calls>
   - Resolution: self-corrected | user-corrected — <how; quote the correction if user-corrected>
   - Lesson: <one generalizable sentence>

### Notes on the known patterns
<one line: "not observed here" OR a brief note on any fresh/different instance worth flagging>
```

Prioritize signal over completeness — this is aggregated with several other parallel reports. Return the report as your final message text.
