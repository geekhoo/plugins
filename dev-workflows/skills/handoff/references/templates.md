# Handoff file templates

## WRITE mode — session entry template

After the compressed history, append:

```markdown
## Session: {YYYY-MM-DD} — {3-6 word title summarising the main thing accomplished}

### Context
{1-2 sentences: what larger project or goal this work belongs to, and why it matters}

### Done This Session
- {Concrete completed item — include file paths where relevant}
- {Another completed item}

### Not Done / Next Steps
- {Specific, ordered, actionable item — written for a cold-start agent with zero conversation memory}
- {Include: file paths, doc references, API names, env var names, anything the next agent needs}
- {Ordered by priority: most urgent first}

### Key Decisions & Gotchas
- {A decision made and the reason behind it}
- {A problem that was hit and how it was resolved}
- {A thing that will bite the next agent if they don't know about it}

### Verification Instructions
- {How to confirm the Done items actually work}
- {Specific: command to run, URL to visit, thing to look for in output}
```

## CREATE mode — Project Overview template

Prepend before the first session entry:

```markdown
# HANDOFF — {Project or Feature Name}

## Project Overview

### What this is
{2-4 sentences: what the project/feature does, why it exists, who it's for}

### Key files and locations
- `{path}` — {what it is}
- `{path}` — {what it is}

### Requirements and specs
- {Link or path to requirements doc, if any}
- {Any key constraints or non-negotiables}

### Environment and setup
- {How to run the project locally}
- {Any env vars, config files, or dependencies to know about}

---
```
