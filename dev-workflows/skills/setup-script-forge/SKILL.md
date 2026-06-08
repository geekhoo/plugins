---
name: setup-script-forge
description: Use when the user asks for a "setup script", "installer or bootstrapper", "reproducible environment setup", "repair or self-healing setup", or "PowerShell quick start" that should become a self-contained, reusable setup or repair script.
---

# Setup Script Forge

## Overview

Turn repeated manual local setup or repair steps into an idempotent script with clear preflight checks, documented side effects, and verification users can rerun.

Use `repo-validation-runner` instead when the request is to discover, run, or report repository validation checks rather than author setup automation.
Use `deployment-setup` instead when environment setup is tied to deployment, runtime configuration, dry-run deployment checks, or local/remote runtime validation rather than a reusable local setup or repair script.

## Prerequisites And Clarification

Before writing the script, identify:

- Target OS, shell, repo or workspace, dependency managers, and required tools.
- Allowed side effects: created files, modified config, installed packages, network downloads, service starts, or process launches.
- Existing setup docs and scripts that must remain authoritative.

Ask before installing global tools, modifying `PATH`, changing registry or system settings, or downloading dependencies. If the user cannot approve a side effect, design the script to report the missing action and stop.

## Workflow

1. Inventory required tools, repo files, existing setup docs, and current scripts.
2. Define the script contract: command, inputs, outputs, side effects, rerun behavior, and failure behavior.
3. Write idempotent setup steps that check current state before changing it.
4. Include dry-run or verification-only mode when feasible.
5. Make failure messages actionable: name the failed check, expected state, actual state, and next command or decision.
6. Document exact usage in the script header, adjacent docs, or the final answer, matching the real command flags.
7. Run the script or representative checks that prove the contract.

## Verification Gates

- G0: Target OS and side effects are known.
- G1: Dependencies and existing setup docs were inspected.
- G2: Script contract is defined before implementation.
- G4: Script validates preconditions or runs successfully.
- G5: Final report includes limitations and rerun behavior.

Do not claim completion until every applicable gate is satisfied or explicitly reported as blocked.

## Acceptance Criteria

- The script can be rerun safely without duplicating work or corrupting state.
- Failure messages are actionable for the next operator.
- Documentation and final instructions match actual script behavior.
- The verification mode or executed checks demonstrate the intended setup state.

## Expected Outcome

A tested setup or repair script plus concise usage notes that explain command syntax, side effects, verification, limitations, and safe rerun behavior.

## Common Mistakes

- Writing a one-shot script that assumes a clean machine instead of checking current state.
- Installing global tools, changing `PATH`, editing registry/system settings, or downloading dependencies without explicit approval.
- Inventing setup commands instead of deriving them from repo evidence.
- Letting docs drift from the implemented flags or behavior.
- Treating a remote deploy workflow as local setup automation.
