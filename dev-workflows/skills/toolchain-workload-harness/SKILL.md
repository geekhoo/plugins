---
name: toolchain-workload-harness
description: Use when the user asks to simulate coding-agent workloads, benchmark tools through repeated workload harnesses, run ToolForge-like experiments, or test toolchain behavior with reproducible synthetic tasks.
---

# Toolchain Workload Harness

## Overview

Build repeatable workload evaluations for tools, skills, and coding-agent toolchains. Prefer bounded fixtures and reproducible commands over anecdotal judgments.

## Prerequisites And Clarification

- Confirm workload domain, duration, toolchain under test, success metrics, and allowed side effects from the request; ask only when missing scope changes risk, duration, target system, output shape, or side effects.
- Ask before running long, expensive, destructive, or external-service workloads.
- Keep fixtures isolated from user work unless the user explicitly selects live project state.
- If the task is specifically plugin or skill evaluation, use `plugin-skill-lifecycle`; use this skill only for the workload harness layer.
- Use `capability-inventory` for tool availability or fallback inventory, and `repo-validation-runner` for repo-grounded validation or check execution.
- If workload ideas should come from prior sessions, use `codex-session-request-mining` first.

## Workflow

1. Define workload cases with clear task prompts, initial state, allowed tools, expected outputs, and stop conditions.
2. Prepare isolated fixtures, reset steps, and any seeded files needed to rerun the same cases.
3. Choose metrics before running: completion rate, elapsed time, command count, error rate, output quality checks, side effects, and reproducibility notes.
4. Run the toolchain tasks within the agreed scope and capture commands, outputs, failures, and deviations.
5. Separate tool failures from fixture, setup, environment, or unclear-prompt failures.
6. Summarize results with reproducible commands, fixture paths, limits, observed issues, and recommended next changes.

## Verification Gates

- G0: Workload scope, limits, side effects, and success metrics are known.
- G1: Fixtures, reset steps, workload cases, and metrics are defined.
- G3: Workload run completed, or stopped with the concrete reason recorded.
- G4: Results include commands, outputs, failures, and reproducibility notes.

## Acceptance Criteria

- Workloads are repeatable from the reported fixture setup and commands.
- Results distinguish toolchain failures from fixture or setup problems.
- Side effects are bounded to the approved scope.
- The final report gives enough evidence for another agent to rerun or extend the harness.

## Expected Outcome

A workload evaluation report plus reusable harness fixtures, metrics, and commands for repeated toolchain behavior testing.

## Common Mistakes

- Starting runs before scope, limits, metrics, or side effects are explicit.
- Treating one successful or failed anecdote as a benchmark.
- Mixing fixture bugs, setup gaps, and toolchain failures in one undifferentiated result.
- Running long or external-service workloads without asking first.
- Reporting conclusions without the commands, outputs, failures, and reproducibility notes needed to rerun the workload.
