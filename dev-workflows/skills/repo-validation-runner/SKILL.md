---
name: repo-validation-runner
description: Use when the user asks to "validate", "run all checks", "complete QA", "prove completion", or "test everything"; run build, lint, typecheck, unit, integration, browser, docs, and migration checks and trace results to repo evidence.
---

# Repo Validation Runner

## Overview

Run repository-grounded validation without inventing commands. Treat completion as proven only when checks are traced to current repo evidence or explicitly skipped with reasons.

The bundled command detector is only a candidate finder. It does not replace the validation matrix, execution, skipped-check accounting, or final risk report.

## Prerequisites and Clarification

- Identify the repo root, target change set, protected paths, external systems, and user-owned work before running checks.
- Inspect evidence first: `package.json`, lockfiles, `.csproj`, `.sln`, `pyproject.toml`, `pytest.ini`, `Makefile`, CI files, README, AGENTS, and test folders.
- Ask before destructive commands, deployments, external writes, credentialed workflows, or suites that repo evidence marks as expensive.
- Ask when "all checks" could mean long-running or unclear suites and the repo does not define validation boundaries.

## Workflow

1. Detect stack and candidate commands from repo files. If useful, run:
   `py <skill>/scripts/detect_validation_commands.py <repo>`
   Treat its JSON output as suggestions; review `inspected_categories` and `unsupported_categories` before building the matrix.
2. Build a validation matrix covering applicable categories: lint, typecheck, unit, integration, build, browser, docs, migrations, and domain checks.
3. For complex repos, write the matrix before execution, with command, cwd, evidence, expected signal, and skip criteria.
4. Run safe, grounded commands. Capture command, cwd, exit status, key output, and failure risk.
5. Classify failures by likely cause: product defect, test expectation drift, environment/setup, dependency/tooling, flaky/timing, or unknown.
6. Mark unrun checks with reasons instead of omitting them.
7. Report pass/fail status, exact evidence, skipped checks, and remaining risk.

## Verification Gates

| Gate | Requirement |
|---|---|
| G0 Scope | Repo root and target change set are known. |
| G1 Evidence | Commands are derived from inspected files or user instruction. |
| G2 Plan | Complex validation has a written matrix before execution. |
| G3 Execution | Checks run within allowed scope. |
| G4 Validation | Commands ran, or were explicitly skipped with reasons. |
| G5 Reporting | Final report includes results, evidence, assumptions, and residual risk. |

## Acceptance Criteria

- Every run command is traceable to repo evidence or direct user instruction.
- Completion claims match validation results; do not call work complete after failed or skipped required checks.
- Failures include likely cause and next diagnostic step.
- The final answer includes exact commands, cwd, exit status, key result, skipped checks, and remaining risk.

## Expected Outcome

Produce a validation appendix or status report that proves what was checked, what failed, what was skipped, and what risk remains.

## Common Mistakes

- Running familiar commands before reading repo manifests.
- Treating one smoke test as "all checks" without a matrix.
- Hiding skipped browser, docs, migration, or integration checks.
- Claiming completion when validation failed for environment reasons.
- Inventing package manager, test runner, service, or script names from conventions alone.
