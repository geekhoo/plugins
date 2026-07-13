---
name: figma-create-design-system-rules
description: Generates custom design system rules for the user's codebase. Use when user says "create design system rules", "generate rules for my project", "set up design rules", "customize design system guidelines", or wants to establish project-specific conventions for Figma-to-code workflows. Requires Figma MCP server connection.
disable-model-invocation: false
---

# Create Design System Rules

## Overview

This skill helps you generate custom design system rules tailored to your project's specific needs. These rules guide AI coding agents to produce consistent, high-quality code when implementing Figma designs, ensuring that your team's conventions, component patterns, and architectural decisions are followed automatically.

### Supported Rule Files

| Agent | Rule File |
|-------|-----------|
| Claude Code | `CLAUDE.md` |
| Codex CLI | `AGENTS.md` |
| Cursor | `.cursor/rules/figma-design-system.mdc` |

## What Are Design System Rules?

Project-level instructions that encode the "unwritten knowledge" of your codebase (component locations, naming, token rules, architectural patterns) so agents implement Figma designs consistently. Full explainer in `references/rule-templates.md`.

## Prerequisites

- Figma MCP server must be connected and accessible
- Access to the project codebase for analysis
- Understanding of your team's component conventions (or willingness to establish them)

## When to Use This Skill

Use this skill when:

- Starting a new project that will use Figma designs
- Onboarding an AI coding agent to an existing project with established patterns
- Standardizing Figma-to-code workflows across your team
- Updating or refining existing design system conventions
- Users explicitly request: "create design system rules", "set up Figma guidelines", "customize rules for my project"

## Required Workflow

**Follow these steps in order. Do not skip steps.**

### Step 1: Run the Create Design System Rules Tool

Call the Figma MCP server's `create_design_system_rules` tool to get the foundational prompt and template.

**Parameters:**

- `clientLanguages`: Comma-separated list of languages used in the project (e.g., "typescript,javascript", "python", "javascript")
- `clientFrameworks`: Framework being used (e.g., "react", "vue", "svelte", "angular", "unknown")

This tool returns guidance and a template for creating design system rules.

Structure your design system rules following the template format provided in the tool's response.

### Step 2: Analyze the Codebase

Before finalizing rules, analyze the project to understand existing patterns:

**Component Organization:**

- Where are UI components located? (e.g., `src/components/`, `app/ui/`, `lib/components/`)
- Is there a dedicated design system directory?
- How are components organized? (by feature, by type, flat structure)

**Styling Approach:**

- What CSS framework or approach is used? (Tailwind, CSS Modules, styled-components, etc.)
- Where are design tokens defined? (CSS variables, theme files, config files)
- Are there existing color, typography, or spacing tokens?

**Component Patterns:**

- What naming conventions are used? (PascalCase, kebab-case, prefixes)
- How are component props typically structured?
- Are there common composition patterns?

**Architecture Decisions:**

- How is state management handled?
- What routing system is used?
- Are there specific import patterns or path aliases?

### Step 3: Generate Project-Specific Rules

Based on your codebase analysis, create a comprehensive set of rules covering five sections: General Component Rules, Styling Rules, Figma MCP Integration Rules (required fetch flow + implementation rules), Asset Handling Rules, and Project-Specific Conventions. Load `references/rule-templates.md` and adapt its verbatim templates for each section — do not write these from memory.

### Step 4: Save Rules to the Appropriate Rule File

Detect which AI coding agent the user is working with and save the generated rules to the corresponding file:

| Agent | Rule File | Notes |
|-------|-----------|-------|
| Claude Code | `CLAUDE.md` in project root | Markdown format. Can also use `.claude/rules/figma-design-system.md` for modular organization. |
| Codex CLI | `AGENTS.md` in project root | Markdown format. Append as a new section if file already exists. 32 KiB combined size limit. |
| Cursor | `.cursor/rules/figma-design-system.mdc` | Markdown with YAML frontmatter (`description`, `globs`, `alwaysApply`). |

If unsure which agent the user is working with, check for existing rule files in the project or ask the user.

For Cursor, wrap the rules with YAML frontmatter:

```markdown
---
description: Rules for implementing Figma designs using the Figma MCP server. Covers component organization, styling conventions, design tokens, asset handling, and the required Figma-to-code workflow.
globs: "src/components/**"
alwaysApply: false
---

[Generated rules here]
```

Customize the `globs` pattern to match the directories where Figma-derived code will live in the project (e.g., `"src/**/*.tsx"` or `["src/components/**", "src/pages/**"]`).

After saving, the rules will be automatically loaded by the agent and applied to all Figma implementation tasks.

### Step 5: Validate and Iterate

After creating rules:

1. Test with a simple Figma component implementation
2. Verify the agent follows the rules correctly
3. Refine any rules that aren't working as expected
4. Share with team members for feedback
5. Update rules as the project evolves

## Examples, rule catalog & troubleshooting

For the example rule catalog (essential / recommended / optional rules), three
full worked examples (React + Tailwind, Vue + custom CSS, design-system monorepo),
best practices, and common issues & solutions, see
[references/examples-and-patterns.md](references/examples-and-patterns.md).

## Additional Resources

- [Figma MCP Server Documentation](https://developers.figma.com/docs/figma-mcp-server/)
- [Figma Variables and Design Tokens](https://help.figma.com/hc/en-us/articles/15339657135383-Guide-to-variables-in-Figma)
