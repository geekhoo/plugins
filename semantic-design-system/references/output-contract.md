# Output Contract

Return design-token work using this structure unless the user asks for a different format:

1. Mode Used
2. Assumptions
3. Design System Summary
4. Token Architecture
5. Naming Convention
6. Token Taxonomy
7. Primitive Tokens
8. Semantic Tokens
9. Component Tokens
10. Theme / Mode Strategy
11. CSS Variable Output
12. Usage Examples
13. Accessibility Notes
14. Governance Rules
15. Validation Checklist
16. Migration Plan
17. Open Questions

For codebase-derived work, also include:

18. Styling Source Inventory
19. Extracted Value Inventory
20. Inconsistencies and Risks
21. Confidence Report

## JSON vs JSONC

The DTCG Format Module 2025.10 (first stable release) mandates **strict JSON** for
design-token files, using the `.tokens` or `.tokens.json` extension and the
`application/design-tokens+json` media type. Files written to disk MUST be valid
strict JSON so they interoperate with tools such as Figma, Style Dictionary, and
Tokens Studio. Do not write comments into `.tokens.json` files.

JSONC (JSON with comments) may be used **only** for illustrative inline snippets in
chat responses, where a comment helps explain a decision. When the user asks you to
create files, always emit strict JSON.
