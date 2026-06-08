---
name: capability-inventory
description: Use when the user asks "what tools are available", "which MCP servers, connectors, plugins, or skills", "is X capability available", or "what are the fallbacks" — inventory currently available capabilities and substitutes.
---

# Capability Inventory

## Overview

Build a current capability inventory before naming tools as callable. Treat tool names, plugin cache IDs, browser availability, connector state, and skill paths as drift-prone until inspected in the current session.

## Prerequisites And Clarification

- Identify the capability domain first: tools, MCP servers, connectors, plugins, skills, browser automation, Figma, CLI commands, or substitutes.
- Ask only when the user wants installation or enablement rather than inventory, or when the requested domain is ambiguous enough to change the result.
- Do not install, enable, update, or call external systems merely to answer an inventory request.
- Prefer current session tool metadata and live discovery over memory, old cache paths, stale plugin names, or prior run summaries.

## Workflow

1. Set the inventory scope.
   Record the requested domain, target repo or machine context, any no-edit constraints, and whether the user needs a report only or also wants fallback validation.

2. Inspect current capabilities.
   Use the active tool list already in context, `tool_search` for deferred plugin/MCP tools when relevant, available skill metadata, plugin lists or local manifests when they are in scope, and CLI probes only when the user asks about command availability.

3. Map requested names to current reality.
   For each requested or implied capability, classify it as:
   - `available`: callable or discoverable now.
   - `missing`: no current callable capability found.
   - `stale`: old name, old cache ID, or historical command that does not match current discovery.
   - `substitute`: different current capability can satisfy the same need.
   - `untested`: plausible fallback that was not validated.

4. Validate substitutes when practical.
   Run harmless probes such as help/version commands, tool discovery, manifest reads, or local dry checks. Do not validate by causing external side effects unless the user explicitly asked for that action.

5. Report the inventory.
   Include the current callable name, evidence source, substitute or fallback, validation status, and drift notes. Separate confirmed facts from assumptions.

## Verification Gates

- G0 Scope gate: capability domain and requested output are known.
- G1 Evidence gate: current tools, plugins, skills, connectors, or CLI state have been inspected.
- G4 Validation gate: substitute commands or fallbacks are tested when practical, or marked untested with the reason.
- G5 Reporting gate: final report distinguishes available, missing, stale, substitute, and untested capabilities.

## Acceptance Criteria

- Do not present stale exact tool names, cache IDs, or command names as callable.
- Fallbacks are source-backed or clearly marked unverified.
- Drift-prone assumptions are flagged.
- Installation and enablement are separated from inventory unless explicitly requested.
- The report gives enough evidence for another agent to use the current capability safely.

## Expected Outcome

A current capability inventory and fallback map that names what can be used now, what is missing, what looks stale, and what substitute has been validated or left untested.

## Common Mistakes

- Treating a remembered plugin cache path or old MCP name as current without discovery.
- Calling an install or enablement flow when the user only asked what is available.
- Reporting a fallback without saying whether it was tested.
- Collapsing missing capability and stale command name into the same status.
- Omitting the source of evidence for a claimed callable tool.
