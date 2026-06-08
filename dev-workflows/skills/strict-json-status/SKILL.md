---
name: strict-json-status
description: Use when the user asks to "return only JSON", "match this schema", "emit machine-readable status", "use status ok", or "no prose"; produce an exact JSON contract with no prose, code fences, or extra fields.
---

# Strict JSON Status

## Overview

Produce exactly the JSON shape requested by the user or downstream automation. Treat surrounding prose, Markdown fences, commentary, and extra keys as contract breaks when strict JSON is requested.

## Prerequisites And Clarification

- Identify the required schema, object or array shape, required fields, allowed values, and whether extra fields are forbidden.
- Ask one concise clarification when the schema is missing and downstream automation depends on exact fields.
- If the user provides a schema, do not reinterpret it; preserve field names, casing, nesting, enum values, and required value spellings.
- If no parser can be run, validate the JSON mentally before responding.

## Workflow

1. Extract the output contract from the newest user request, schema, examples, or referenced source.
2. Draft the minimal JSON object or array that satisfies the contract.
3. Check required fields, allowed values, data types, nullability, and whether optional fields should be omitted.
4. Validate syntax with a JSON parser when possible, especially for generated files, copied payloads, or complex nested data.
5. Emit exactly one JSON object or array as requested, with no Markdown, code fences, explanations, greetings, or trailing notes.

Use `contract-shape-extractor` first when the task is to define a reusable schema rather than only emit a strict status response.

## Verification Gates

- G0 Scope gate: schema or required shape is known, or the missing schema has been clarified.
- G2 Shape gate: the response shape is drafted before emission.
- G4 Parse gate: JSON parse validation succeeds when practical; otherwise perform a final syntax check.
- G5 Output gate: the final response contains only the requested JSON value and nothing around it.

## Acceptance Criteria

- Output is syntactically valid JSON.
- Required fields and exact required values are present.
- No extra text surrounds the JSON.
- No unapproved extra keys, renamed fields, casing changes, or prose values are introduced.

## Expected Outcome

A strict machine-readable JSON response that automation can parse without cleanup.

## Common Mistakes

- Wrapping JSON in Markdown fences.
- Adding a sentence before or after the payload.
- Treating `status: "ok"` as equivalent to `status: "success"` when the schema says otherwise.
- Adding helpful but unrequested fields to a strict schema.
- Asking for clarification when the required shape is already clear from the request.
