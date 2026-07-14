---
name: figma-batch-analyzer
description: >
  Use when the user wants a compact, structured spec table from Figma (a table, not
  a long prose plan) — says "analyze figma", "figma specs", "what does figma say
  about", "batch analyze", invokes /figma-batch-analyzer, mentions a Figma node ID
  or URL and wants to know what to implement, asks how a component should look, or
  wants a checklist of visual fixes to make.
---

# Figma Batch Analyzer

The goal of this skill is to replace the typical "verbose prose plan" Figma workflow with a fast,
scannable structured spec. Gerald works against the Markefin UI Figma file and needs to go from
"here's a node ID" directly to "here's what to change in code", with no manual filtering step.

## Default context

- **Default Figma file key**: `f23wB7B5Sq16GncjfLNEYL`
- **Figma MCP tools** (the connector prefix varies with how it's mounted — `mcp__Figma__*`, `mcp__claude_ai_Figma__*`, etc.; resolve the live prefix via tool discovery, don't hardcode it):
  - `get_design_context` — primary source of truth for layout, colors, type, spacing
  - `get_screenshot` — optional visual confirmation
  - `get_variable_defs` — if the component uses design tokens/variables

## Invocation forms

```
/figma-batch-analyzer
/figma-batch-analyzer [node-id-1] [node-id-2]
/figma-batch-analyzer https://www.figma.com/design/f23wB7B5Sq16GncjfLNEYL/...?node-id=xxx&...
```

When called with no arguments, ask the user which node(s) to analyze.

## Step 1 — Resolve node IDs

If the user passes a full Figma URL, extract the `node-id` query parameter (URL-decode `%3A` → `:`).
If the user passes a bare node ID (e.g. `123:456`), use it directly with the default file key.
If multiple nodes are given, resolve all of them.

## Step 2 — Fetch design context (parallel)

Call the resolved `…get_design_context` tool for each node. If multiple nodes, call them in parallel.

Pass:
- `file_key`: the file key extracted from the URL, or `f23wB7B5Sq16GncjfLNEYL` if not present
- `node_id`: the resolved node ID

If any node uses Figma variables/tokens, also call the resolved `…get_variable_defs` tool for that file.

## Step 3 — Extract spec values

From the response, extract these properties (only include rows where there is a real value):

| Category | Properties to extract |
|----------|----------------------|
| Layout | width, height, min/max width, display mode (auto-layout direction, wrap) |
| Color | background color, border color, text color — as hex (#RRGGBB) |
| Typography | font family, font size (px), font weight, line height (px or %), letter spacing |
| Spacing | padding (top/right/bottom/left or shorthand), gap between children |
| Border | border width, border radius (per-corner if varied) |
| States | any named variants: hover, active, disabled, selected |

Normalize values to CSS-friendly units (px, %, hex). If a value is a Figma variable, show both the variable name and its resolved value.

## Step 4 — Diff against current code (optional but valuable)

If you know or can find the corresponding code file for this component (search for `.cshtml`, `.css`, `.js` files in the repo that match the component name), read the current values and add a "Current Code" column and a "Match?" column to the table.

To find the file: look for filenames containing the component name (derived from the node's name in Figma). The project root is typically the workspace directory.

If no code file is identifiable, omit those two columns.

## Step 5 — Output the structured spec

Output this exact format. Keep it concise — the table replaces prose.

```
## Figma Analysis: {Component Name}
Node: {node-id}  |  File: {file-key}

| Property | Figma Spec | Current Code | Match? |
|----------|-----------|--------------|--------|
| Width | 240px | 220px | ❌ |
| Height | auto | — | — |
| Background | #F2F2F5 | #FFFFFF | ❌ |
| Border radius | 8px | 8px | ✓ |
| Border | 1px solid #D0D0D5 | none | ❌ |
| Font | Inter 13px / 400 | Inter 13px / 400 | ✓ |
| Line height | 20px | — | — |
| Padding | 12px 16px | 10px 16px | ❌ |
| Gap | 8px | — | — |
| Hover state | background #E8E8EF | — | — |
```

If no code file was found, omit the last two columns entirely (see `references/output-example.md` for the variant and a full worked example).

If multiple nodes were analyzed, output one section per node, separated by a horizontal rule (`---`).

## Step 6 — Implementation checklist

After the table(s), output a numbered checklist of concrete code changes. Maximum 8 items. Each item should name the file and the exact change. Omit anything that already matches.

```
## Implementation Checklist
1. Set width to 240px in `programs-v2.cshtml.css` (.program-card)
2. Set background-color: #F2F2F5 (was #FFFFFF)
3. Add border: 1px solid #D0D0D5
4. Update padding from 10px 16px → 12px 16px
5. Add :hover { background: #E8E8EF }
```

If everything matches, say: "No changes needed — code matches Figma spec."

## What NOT to do

- Do not write 200-line prose explanations of the design
- Do not include "considerations", "suggestions", or open-ended commentary
- Do not explain what the component is for or how it was designed
- Do not ask clarifying questions if you have enough to proceed (node ID + file key = enough)
- Do not include checklist items for properties that already match

## Example

For a full worked single-node example with code diff, load `references/output-example.md`.
