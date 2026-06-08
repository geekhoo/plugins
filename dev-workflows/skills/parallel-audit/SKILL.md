---
name: parallel-audit
description: This skill should be used when the user asks to "review", "audit", "get independent opinions", "deploy reviewers", or "validate a spec, branch, or design" from multiple lenses — spawn independent read-only reviewers and collate one severity-ranked report (reports only, does not fix).
user-invocable: true
argument-hint: "<target path/file/spec> [roles: e.g. security, spec-validation, data-model, perf]"
---

# Parallel Audit

Review a spec, codebase, branch, or design from several independent expert perspectives at once. Keep reviewers **read-only**; report findings and do not apply fixes. For a pure code-diff review, the `code-review` skill is the narrower tool; use parallel-audit when the target is a spec/doc/branch or when named domain lenses are wanted. For a broader orchestration framework with delegated coders and verification gates, use `parallel-review-orchestrator`.

Core principles: use independent reviewers (no shared bias); keep them read-only; report rather than fix; save findings with file:line references; then cross-validate.

## 1. Scope the target and roles
- Resolve the target from `$ARGUMENTS` (a path, file, folder, branch, or spec package).
- Pick 2–5 **distinct** roles. Defaults by target type:
  - **Code/branch:** correctness/bugs · security · performance · tests-and-edge-cases.
  - **Spec/docs:** spec-validation (internal consistency, authority gaps) · data-model · API-contract · dev-experience/ambiguity.
  - **Design:** accessibility · design-system-conformance · responsive/viewport.
- Each role reviews only what it needs — don't make every reviewer read everything.

## 2. Spawn reviewers in parallel
- Launch one subagent per role **in a single batched message** (parallel). Give each the same target but a role-specific charter.
- Each reviewer must return findings in a fixed shape:
  - `severity` (CRITICAL / HIGH / MEDIUM / LOW / NIT)
  - `location` (file:line or spec section)
  - `finding` (what's wrong)
  - `why` (impact / failure scenario)
  - `suggestion` (optional, non-binding)
  - `confidence` (high/med/low)
- Reviewers are **read-only** — explicitly forbid edits.

## 3. Collate and de-duplicate
- Merge all findings. When multiple roles flag the same location for **different reasons**, keep both. When for the **same** reason, keep the one with the most concrete failure scenario.
- Rank: correctness/security always outrank cleanup/style when trimming is required.
- Note disagreements between reviewers explicitly rather than silently picking one.

## 4. Report
Write `<target-dir>/audit-<YYYY-MM-DD>.md`: an executive summary (counts by severity), then findings grouped by severity with location + why + suggested fix + which role(s) raised it. Present the summary; ask which to act on. Do **not** apply fixes unless the user then asks (at which point hand off to an implementation skill/agent such as `implement`, or the `review-remediation` skill).

## Notes
- For high-stakes findings, optionally add a verification pass: a second skeptic reviewer tries to refute each CRITICAL/HIGH before it ships in the report.
- Windows: forward slashes in the Bash tool.
