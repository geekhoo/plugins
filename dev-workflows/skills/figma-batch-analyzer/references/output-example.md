# Output variants and worked example

## No-code-file variant

If no code file was found, omit the last two columns entirely:

```
| Property | Figma Spec |
|----------|-----------|
| Width | 240px |
...
```

## Example (single node, with code diff)

User: `/figma-batch-analyzer 847:2301`

You call: `mcp__claude_ai_Figma__get_design_context(file_key="f23wB7B5Sq16GncjfLNEYL", node_id="847:2301")`

You search the workspace for a CSS file matching "ProgramCard" or "program-card", read the current values, then output:

```
## Figma Analysis: Program Card
Node: 847:2301  |  File: f23wB7B5Sq16GncjfLNEYL

| Property | Figma Spec | Current Code | Match? |
|----------|-----------|--------------|--------|
| Width | 240px | 220px | ❌ |
| Background | #F2F2F5 | #FFFFFF | ❌ |
| Border radius | 8px | 8px | ✓ |
| Font | Inter 13px / 400 | Inter 13px / 400 | ✓ |
| Padding | 12px 16px | 10px 16px | ❌ |

## Implementation Checklist
1. Set width: 240px in programs-v2.cshtml.css (.program-card)
2. Set background-color: #F2F2F5
3. Update padding: 12px 16px
```
