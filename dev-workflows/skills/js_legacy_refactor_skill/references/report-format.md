# JavaScript Refactor — Issue Report Format

Output template for the `js-legacy-refactor` skill's Pass 3 final report. Consult
this when writing the report; the no-regression rules and three-pass workflow stay
in `SKILL.md`.

## Issue report format

Use this exact structure for final reports:

```md
# JavaScript Refactor Report

## Status
PASS | BYPASS/PARTIAL | FAIL/REVERT REQUIRED

## Summary
- Files changed:
- Files intentionally not changed:
- Pages verified:
- Tests/probes run:

## Accepted refactors
| ID | Files | Change | Safety evidence |
|---|---|---|---|

## Bypassed refactors / issues
| ID | Severity | Location | Reason | Recommended fix |
|---|---|---|---|---|

## Behavior comparison
| Check | Baseline | Refactor | Result |
|---|---:|---:|---|

## Remaining risks
| Risk | Affected pages/files | Mitigation |
|---|---|---|
```

Severity values:

- `BLOCKER_REFRACTOR_BYPASSED`: a change would likely alter behavior or triggered an error.
- `HIGH_ORDER_DEPENDENCY`: hidden load-order or override dependency.
- `HIGH_GLOBAL_COLLISION`: duplicate/divergent global declaration.
- `MEDIUM_INLINE_SCRIPT`: inline script cannot safely move yet.
- `MEDIUM_DYNAMIC_CODE`: dynamic calls prevent confident static analysis.
- `LOW_CLEANUP`: safe follow-up cleanup opportunity.
