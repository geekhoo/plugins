---
name: design-doc-verifier
description: >
  Use when asked to "verify against design", "check design doc", "review against spec",
  "does the code match", "audit the implementation", "how complete is this feature",
  "what's missing from the design", "is this done" / "check this" while a spec, SDD,
  AGENTS.md, CLAUDE.md, or feature doc is in context, when about to finalize or ship a
  feature while such a doc is in context, or to compare code to written requirements,
  acceptance criteria, or user stories — gap-analyze the codebase against the doc and
  report DONE/PARTIAL/MISSING/BROKEN.
---

# Design Doc Verifier

You are performing a structured gap analysis between a design document and a codebase.
The goal is to save Gerald time by automating the manual "read spec → scan code" loop
he would otherwise do before finalizing a feature.

## Step 0: Resolve inputs

If the user invoked the skill with a doc path, use it.
If no path was given, ask: "Which design document should I verify against? (path or paste content)"
If no source directory was given, default to the project root that contains the design doc,
or ask if there is genuine ambiguity (e.g., a mono-repo with multiple projects).

Gerald's common project roots for reference:
- `C:\Users\gerald.khoo\Codes\v2\` — ASP.NET Core + DevExtreme frontend
- `C:\Users\gerald.khoo\Codes\mf-dotnet\` — C# backend (CQRS/MediatR/EF Core)
- `C:\Users\gerald.khoo\Codes\mf-dx-cc\` — static frontend

## Step 1: Read and parse the design document

Read the full design document. Your job is to extract every discrete, verifiable
requirement — things the codebase must do or have in order to "pass" the design.

Look for requirements in:
- Numbered lists (`1.`, `1)`, `- [ ]`, `- [x]`)
- Headings followed by bullet or description blocks ("## Feature X", "### Acceptance Criteria")
- API endpoint tables or lists (`GET /api/...`, `POST /api/...`)
- Data model field lists ("Program has: id, name, budget, startDate")
- UI component descriptions ("The form must include a dropdown for status")
- Explicit "must / shall / should" language
- "Done criteria" or "Definition of Done" sections
- Constraints and non-functional requirements (pagination size, response time, field limits)

If the document has no explicit structure, extract requirements from every heading and
significant bullet point. When in doubt, include it — a false positive (marking something
as a requirement that turns out to be background context) is far less costly than missing
a real requirement.

Number requirements sequentially. Keep each requirement to one verifiable claim.
If a bullet covers multiple claims, split them.

**Example extractions:**

From `- Users can create a Program with name, budget, and start date`:
- Req 1: User can create a Program
- Req 2: Program has a name field
- Req 3: Program has a budget field
- Req 4: Program has a start date field

From `GET /api/programs — returns paginated list, 25 per page`:
- Req 5: GET /api/programs endpoint exists
- Req 6: Response is paginated at 25 items per page

## Step 2: Search for implementation evidence

For each requirement, search the codebase. Use multiple strategies — one search is
rarely enough to be confident. Load `references/search-strategies.md` for the
per-layer search heuristics (backend CQRS, DevExtreme frontend, UI specs, test coverage).

## Step 3: Classify each requirement

Apply these status labels conservatively. When uncertain, go one level lower
(i.e., if unsure between DONE and PARTIAL, call it PARTIAL).

| Status | Meaning | Evidence bar |
|--------|---------|-------------|
| ✅ DONE | Fully implemented | Clear code path exists end-to-end: model + handler/controller + (if UI required) UI component |
| ⚠️ PARTIAL | Some but not all layers implemented | e.g., model exists but no endpoint; endpoint exists but no UI; logic present but constraint wrong |
| ❌ MISSING | No evidence of implementation found | Thorough search turned up nothing |
| 🔴 BROKEN | Implementation exists but contradicts the spec | Wrong value, wrong behavior, hardcoded override, failing test |

**DONE requires evidence across all relevant layers.** A database field alone is not DONE
if the spec says the field is also exposed via API and shown in the UI.

**PARTIAL and BROKEN must always cite specific file:line references** so Gerald can jump
directly to the relevant code.

**MISSING** — before declaring MISSING, try at least 2–3 different search terms
(the exact phrase from the spec, a camelCase version, an abbreviation). Only declare
MISSING after a genuine effort.

## Step 4: Output the verification report

Use the exact format in `references/report-template.md` (table with per-requirement
status + evidence, summary counts, prioritized next steps). Load it before writing
the report. Keep the Evidence column concise (`ProgramsController.cs:42`, not a paragraph).

## Step 5: After the report

Offer to go deeper on any specific gap: "Want me to scaffold the missing CSV export
endpoint?" or "I can look for the closest existing code to build the budget field UI from."

This keeps the session productive — the verification report is the start of a fix
session, not just a status check.

## Edge cases

For AGENTS.md/CLAUDE.md docs, unstructured prose, very large codebases, ambiguous
requirements, and doc-references-another-doc, load `references/edge-cases.md`.
