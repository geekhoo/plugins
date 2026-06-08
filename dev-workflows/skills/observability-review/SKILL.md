---
name: observability-review
description: Use when the user asks about "Langfuse", "OpenTelemetry or OTEL", "traces or spans", "telemetry validation", or "trace export" to review observability instrumentation and separate runtime success from export or instrumentation failure.
---

# Observability Review

## Overview

Review observability from current repo evidence. Keep runtime behavior, instrumentation behavior, and telemetry export behavior distinct throughout the work.

## Prerequisites And Clarification

- Identify the target runtime, observability surfaces, protected paths, and allowed external systems before acting.
- Inspect current runtime code, environment/config contracts, observability docs, and tests before making claims.
- Ask before changing environment enablement boundaries.
- Ask before calling external observability services when credentials, production state, or side effects are unclear.

## Workflow

1. Map the runtime flow from request entry through model calls, pipeline stages, API/UI surfaces, and observability hooks.
2. Inventory tracing signals: traces, spans, metadata, scores, stage names, exported payloads, and documented expectations.
3. Compare source behavior against environment/config enablement rules and preserve explicit boundaries unless the user approves a change.
4. Verify successful runtime behavior separately from instrumentation success and trace/export success.
5. Update or review docs/tests around the observed observability contract when the task calls for changes.
6. Report findings with clear buckets for runtime state, instrumentation state, export state, evidence, validation, and unresolved risks.

Use `contract-shape-extractor` when trace, event, or score schema extraction dominates the task. Use `docs-sync` when observability runbooks or linked docs are the main deliverable. Use `browser-qa` or `browser-probe` for rendered UI, screenshots, console/network, or viewport validation; use `deployment-setup` or `setup-script-forge` for deploying, configuring runtimes, local/cloud setup, dependency fixes, or setup scripts.

## Verification Gates

- G0 Scope: observability surface, runtime flow, external systems, and protected paths are known.
- G1 Evidence: runtime source, env/config contract, docs, manifests, and relevant tests have been inspected.
- G2 Contract: expected span, score, metadata, stage, and export behavior is defined.
- G3 Execution: review, fix, or docs work stayed within the allowed scope.
- G4 Validation: tests, runtime checks, source citations, or safe telemetry checks validate behavior.
- G5 Reporting: final output separates runtime behavior, instrumentation behavior, and export state.

## Acceptance Criteria

- The environment enablement contract is preserved or any requested change is explicit and approved.
- Runtime success is not misreported as trace/export success, and trace/export failure is not misreported as model failure.
- Pipeline stage mapping is explicit, source-backed, and reflected in docs/tests when changed.
- Observability claims cite current evidence rather than memory or assumptions.

## Expected Outcome

Produce an observability review, fix, or validation report that clearly distinguishes runtime behavior, instrumentation behavior, telemetry export behavior, and remaining uncertainty.

## Common Mistakes

- Treating a successful model response as proof that trace export worked.
- Treating an OTEL or Langfuse export error as proof that the app or model call failed.
- Changing observability enablement variables without asking first.
- Inventing stage names, span shapes, score semantics, endpoints, or validation commands.
- Reporting observability status without inspecting current source, docs, and tests.
