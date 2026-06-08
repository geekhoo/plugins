---
name: deployment-setup
description: Use when the user asks to "deploy", "configure local or cloud runtime", "diagnose remote dependency failures", "set up Scrapy Cloud or Zyte", or "run dry-run deployment checks" while setting up or validating deployment and runtime state.
---

# Deployment Setup

## Overview

Make deployment and environment setup evidence-backed and reproducible. Derive commands from current manifests, dependency declarations, config files, and docs; do not invent deploy commands or validation results.

## Complexity Split

- Use `setup-script-forge` when the deliverable is an idempotent, reusable local setup or repair script.
- Keep `deployment-setup` for remote deploys, runtime config, dependency mismatch diagnosis, dry-run deploy checks, and external runtime validation.

## Prerequisites And Clarification

- Discover deployment manifests, config files, dependency files, scripts, and docs before planning commands.
- Ask before deploying, installing global tools, changing remote state, using credentials, or modifying production-like environments unless the user explicitly requested that action.
- Ask when the target environment, allowed side effects, credential source, or deployment action is ambiguous.
- Treat remote failures as evidence to reconcile against local imports, runtime versions, manifests, and dependency declarations.

## Workflow

1. Identify the target environment, requested action, protected paths, credentials needed, and allowed side effects.
2. Inventory manifests and dependency declarations such as `requirements.txt`, lockfiles, runtime config, deployment YAML/TOML/JSON, CI files, platform docs, and existing setup scripts.
3. Compare local imports, runtime assumptions, and build steps with remote requirements; record mismatches before changing files.
4. Write or update only the setup/deploy artifacts needed for the requested action.
5. Run deploy, setup, or dry-run commands only when explicitly requested or approved; otherwise produce an exact runbook.
6. Validate local or remote state with commands, logs, health checks, platform status, or source citations.
7. Report commands run, files changed, dependency findings, validation evidence, and unresolved risks.

## Verification Gates

- G0 Scope: target environment, action, credentials boundary, and side effects are known.
- G1 Evidence: config, manifests, dependency declarations, scripts, and relevant docs are inspected.
- G2 Plan: deploy/setup plan and expected outputs are explicit.
- G3 Execution: remote-changing or credential-using actions run only with approval or explicit request.
- G4 Validation: local or remote state is validated with concrete evidence.
- G5 Reporting: final response includes commands, dependency findings, validation results, assumptions, and risks.

## Acceptance Criteria

- Commands are derived from repo or environment evidence.
- Remote side effects are intentional and scoped.
- Missing dependencies are documented with reproducible fixes.
- The result is either a deployed/validated environment or a clear setup/remediation runbook.

## Expected Outcome

Deliver a deployed or validated environment when action is allowed. If action is not allowed or information is missing, deliver a runbook with exact commands, prerequisites, validation steps, and the reason live execution was not performed.

## Common Mistakes

- Running a real deployment when the user only asked for setup instructions or diagnosis.
- Using credentials, changing remote state, or installing global tools without explicit permission.
- Copying commands from memory instead of current manifests, scripts, or platform docs.
- Treating local success as remote validation when the target is a cloud/runtime platform.
- Fixing remote dependency failures without comparing imports, dependency files, and platform runtime constraints.
- Omitting failed commands, partial validation, or unresolved credential/environment limitations from the final report.
