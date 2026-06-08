---
name: contract-shape-extractor
description: Use when the user asks for "JSON schemas", "output contracts", "API shapes", "status schemas", "validation fixtures", or "machine-readable outputs"; extract implicit expectations into explicit contracts with schema, examples, and validation notes.
---

# Contract Shape Extractor

## Overview

Turn implicit input/output expectations into an explicit contract that another agent, test, parser, API client, or validator can consume. Prefer current evidence over memory, and do not silently choose between incompatible shapes.

## Complexity Split

- Use `strict-json-status` for response-only strict status formats.
- Use `repo-validation-runner` or a custom validator for executable validation checks.

## Prerequisites And Clarification

- Identify the contract target and consumers: agent response, API payload, parser input, status object, migration record, fixture set, or validation output.
- Identify the source of truth: code, docs, examples, tests, API responses, user-provided schema, or live behavior.
- Ask before proceeding if multiple incompatible shapes are present, downstream automation needs exact fields, or the source of truth is missing.
- Continue without asking when the target, source evidence, and consumer expectations are clear enough to extract.

## Workflow

1. Map the evidence.
   Inspect the relevant files, tests, docs, responses, examples, or user-supplied schema. Record which sources define the contract and which are only illustrative.

2. Extract the shape.
   Capture fields, nesting, types, optionality, nullable values, arrays, maps, enums, defaults, ordering constraints, identifiers, version fields, and invariants.

3. Define states.
   Include success, partial, blocked, and error states when the workflow or automation can produce them. Do not collapse unknown, blocked, and failed states into one status unless the source requires it.

4. Draft the contract.
   Use JSON Schema when a machine-readable contract is useful or requested. Use a concise prose contract only when the target is not JSON-shaped or schema syntax would add noise.

5. Add examples.
   Provide at least one valid payload and one invalid or edge-case payload when validation behavior matters. Ensure examples match the schema exactly.

6. Link validation.
   Connect the contract to existing validators, tests, parser checks, schema checks, or fixture expectations. If validation is manual, state why and name the manual checks.

7. Report ambiguity.
   List assumptions and unresolved ambiguities separately from the contract so automation consumers do not treat guesses as guarantees.

## Verification Gates

- G0 Scope gate: contract target, consumers, and allowed edit/output surfaces are known.
- G1 Evidence gate: current source examples, code, docs, tests, or responses have been inspected.
- G2 Shape gate: fields, types, states, invariants, examples, and assumptions are drafted.
- G4 Validation gate: sample payloads are validated or manual validation limits are explained.
- G5 Reporting gate: final output includes schema or contract, examples, validation notes, assumptions, and unresolved ambiguities.

## Acceptance Criteria

- Contract is unambiguous enough for another agent, parser, test, or tool to consume.
- Examples conform to the stated schema or explicitly demonstrate invalid behavior.
- Optional, nullable, omitted, blocked, partial, and error states are distinguished when relevant.
- High-risk ambiguity is surfaced instead of silently resolved.
- Validation notes name exact commands, validators, tests, or manual checks when available.

## Expected Outcome

Produce a machine-readable or prose-backed contract with schema, valid and invalid examples, validation notes, source evidence, assumptions, and unresolved ambiguities.

## Common Mistakes

- Inventing fields, enum values, commands, or validators that are not supported by evidence.
- Treating one example payload as the whole contract without checking code or tests.
- Marking fields optional because they are absent in a partial example instead of verifying optionality.
- Mixing response states together, especially success vs partial vs blocked vs error.
- Providing examples that do not parse or do not match the schema.
- Hiding assumptions inside the schema instead of reporting them explicitly.
