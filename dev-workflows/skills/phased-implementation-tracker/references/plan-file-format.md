# Plan file format, example flow, and tips

Supporting reference for `phased-implementation-tracker`.

## Plan file format

```markdown
# Plan: {plan title}
Last updated: {YYYY-MM-DD}

## Steps
- [x] 1. First step (done)
- [-] 2. Second step (in progress)
- [ ] 3. Third step (pending)
- [~] 4. Fourth step (deferred)
- [!] 5. Fifth step (blocked: reason here)
```

## Status markers legend

| Marker | Status      | Meaning                                      |
|--------|-------------|----------------------------------------------|
| `[x]`  | DONE        | Completed in a prior or current session      |
| `[-]`  | IN-PROGRESS | Actively being worked on right now           |
| `[ ]`  | PENDING     | Not yet started                              |
| `[~]`  | DEFERRED    | Skipped for now; revisit later               |
| `[!]`  | BLOCKED     | Cannot proceed; add the reason after a colon |

Always write the current date (compute it at runtime) into "Last updated:" when
saving the file.

## Example flow

**Session 1** — user provides a 6-step plan. Tracker saves it, all PENDING.
Completes steps 1 and 2. Marks them `[x]`. Session ends.

**Session 2** — tracker reads file, shows that steps 1–2 are DONE, steps 3–6
are PENDING. Offers to start step 3. User says "defer step 3". Tracker marks it
`[~]`, moves to step 4. Step 4 gets stuck — user says "step 4 is blocked, waiting
for API keys". Tracker marks `[!] 4. ... (blocked: waiting for API keys)`. Session
ends with steps 5–6 PENDING.

**Session 3** — tracker reads file, shows the full picture, automatically
surfaces step 5 as next actionable item.

## Tips for good plan files

- Keep step titles short but meaningful — they're what the user sees at a glance.
- One plan per project (one `.phased-plan.md` per directory). If the user has a
  second parallel plan, ask whether to overwrite or handle it as a separate file
  with a different name.
- If the user reorganizes steps mid-plan (adds new steps, splits one into two),
  update the file to reflect the new structure and renumber cleanly.
