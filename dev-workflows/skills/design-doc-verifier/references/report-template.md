# Verification report template

Use this exact format. Replace `{placeholders}` with actual values.

```
## Design Verification: {doc title or filename}
Date: {today's date}
Source: {directory scanned}

| # | Requirement | Status | Evidence |
|---|-------------|--------|----------|
| 1 | {requirement text} | ✅ DONE | {ClassName.Method, route, or file:line} |
| 2 | {requirement text} | ⚠️ PARTIAL | {what exists — file:line; what's missing} |
| 3 | {requirement text} | ❌ MISSING | No implementation found |
| 4 | {requirement text} | 🔴 BROKEN | {file:line — expected X, found Y} |

## Summary
- ✅ Done: {n}/{total} ({pct}%)
- ⚠️ Partial: {n} — {brief list of what's incomplete}
- ❌ Missing: {n} — {brief list of what's not started}
- 🔴 Broken: {n} — {brief list of what contradicts the spec}

## Recommended Next Steps
{Prioritized numbered list. Order by: Broken first (regressions), then Missing critical
paths, then Partial items, then cosmetic gaps. Be specific — name the file to edit,
the class to create, or the value to fix.}
```

Keep the Evidence column concise: `ProgramsController.Create (line 42)` or
`POST /api/programs — ProgramsController.cs:42` is better than a paragraph.
For MISSING, simply say "No implementation found" to keep the table readable;
put extra detail in the Next Steps section if needed.
