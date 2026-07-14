---
name: handoff
description: >
  Use when the user says "handoff", "update handoff", "write handoff", "create
  handoff", "read handoff", "summarize this session", "reaching context limit",
  "what is done, what needs to be done", or invokes /handoff; and proactively at the
  very start of any session when a HANDOFF.md (or any *HANDOFF*.md / *handoff*.md
  variant) is found in the working directory — read and present it. When in doubt,
  invoke this skill rather than writing a handoff freehand.
---

# Handoff Skill

HANDOFF.md files are the memory bridge between sessions. When done well they let a cold-start agent — or a returning Gerald — pick up exactly where things left off without needing the conversation. When done poorly (or skipped) they create the "did you do this?" problem. This skill makes sure they're always done well.

## Choosing a mode

| Situation | Mode |
|---|---|
| End of session, "update handoff", "summarize this session", "reaching context limit" | **WRITE** |
| Session start with an existing HANDOFF.md, "read handoff" | **READ** |
| No handoff file exists, "create a handoff", "generate a handoff file" | **CREATE** |

Named variants (HANDOFF-V3.md, TESTING-HANDOFF.md, handoff-v2.1.md) follow all the same rules — if the user names a variant, use that name; when reading, search for any file matching `*HANDOFF*.md` or `*handoff*.md`.

**Session-start precedence:** when this skill, `phased-implementation-tracker` (a `.phased-plan.md` exists), and/or `resume-inventory` (user said "resume"/"continue") all want to fire, read and present the handoff first, then show plan status; on an explicit resume/continue, `resume-inventory` drives the worktree verification and this handoff is evidence input, not confirmed state.

---

## Mode 1: WRITE

Use at end of session, when context is getting long, or any time the user asks to record what happened.

### Step 1: Locate the file

1. Look in the current working directory for any `*HANDOFF*.md` or `*handoff*.md` file
2. If not found, check `docs/` subdirectory
3. If a path or folder was given in the request, use that
4. If still not found, ask the user where to put it (default: current directory as `HANDOFF.md`)

### Step 2: Compress existing history

If the file already exists and has prior session entries, compress them to save space while keeping the record intact. For each existing `## Session:` block, distill it to a single line under a `## Previous Sessions` section:

```
- {date} — {short title}: {one sentence of the most important thing done or decided}
```

Keep the existing `## Project Overview` section verbatim if one exists.

The goal is that previous sessions never vanish from the record — they're compressed, not deleted. Future agents can see the arc of the work.

### Step 3: Append new session entry

Write the file first — before summarising anything to the user. (The failure mode this skill exists to prevent is a cheerful summary of a session that was never actually saved.) After the compressed history, append a session entry using the exact template in `references/templates.md` (Context / Done This Session / Not Done / Key Decisions & Gotchas / Verification Instructions).

The "Not Done / Next Steps" section is the most important one for continuity. Write it so that a fresh Claude instance with only this file as context could act on it. That means:
- Every step is self-contained (no "continue what we were doing")
- File paths are absolute or relative-to-project-root
- Any prerequisite is mentioned explicitly
- Environment setup requirements are noted

### Step 4: Confirm to the user

After writing, tell the user:
- The path that was written
- The Next Steps list (copy it verbatim from what was written)

---

## Mode 2: READ

Use at session start when a HANDOFF.md exists, or when the user says "read handoff".

### Step 1: Find and read the file

Search the working directory (and `docs/`) for `*HANDOFF*.md` or `*handoff*.md`. Read the most recently modified one if multiple exist.

### Step 2: Present a compact status summary

Don't dump the whole file at the user — synthesise it:

```
Project: {1 sentence from Context or Project Overview}

Last session ({date} — {title}):
- Done: {bullet list of Done items from the most recent session}

Next steps:
- {Next Steps list, verbatim}
```

### Step 3: Offer to proceed

If the user has already given a task in the same message, skip this and just start working — the handoff has done its job.

Otherwise ask: "Shall I start on the next steps, or did you have something else in mind?"

---

## Mode 3: CREATE

Use when no HANDOFF.md exists and the user asks to create one, or when it's clearly needed but doesn't exist yet.

Same as WRITE, but prepend a Project Overview section before the first session entry — use the CREATE-mode template in `references/templates.md` (What this is / Key files / Requirements / Environment).

Then continue with the first session entry as in WRITE mode.

---

## Naming conventions

- Default: `HANDOFF.md` in project root
- Versioned: `HANDOFF-V2.md`, `handoff-v2.1.md` — follow the user's naming exactly
- Domain-specific: `TESTING-HANDOFF.md`, `API-HANDOFF.md` — follow the user's naming exactly
- Subfolder: if the user says "create a handoff in the v2.1 folder", write to `v2.1/HANDOFF.md` (or match their naming)

When reading, glob for `*HANDOFF*.md` and `*handoff*.md` to catch all variants.
