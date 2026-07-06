# Claude Work Cleaner Pass Guide

Load this reference when a cleanup spans multiple files, generated docs, plugin or skill packages, planning-packet artifacts, frontend surfaces, hooks, or runtime compatibility files.

## Pass 1: Mechanical Clutter

Remove low-risk artifacts that static tools or direct inspection can confirm:

- Unused imports introduced by the recent work.
- Unused locals introduced by the recent work.
- Debug statements such as `console.log`, `debugger`, ad hoc `print`, or temporary `Write-Host`.
- Commented-out code blocks that are not active notes, migration breadcrumbs, or TODOs.
- Placeholder text such as lorem ipsum, "TODO implement", fake sample values, or scaffold instructions left in production paths.

Keep intentional diagnostics, structured logging, examples in docs, and placeholder values inside templates or tests.

## Pass 2: Comment And Documentation Noise

Remove text that restates obvious code or workflow mechanics:

- Comments that explain what a nearby line already says.
- Redundant JSDoc or XML-doc parameter descriptions with no behavior contract.
- Decorative section banners.
- In-app or README narration that describes how obvious UI controls work.
- Skill text that tells the agent generic facts it already knows.

Keep comments that explain why: business rules, migrations, host quirks, validation gaps, compliance, performance, compatibility, or known traps (e.g. DevExtreme `::deep` scoping notes, PostgreSQL/EF Core migration caveats).

## Pass 3: Generated Surface Tightening

Tighten code or docs produced by broad agents:

- Remove duplicated prose across `handoff.md`, `kanban.md`, task notes, and reports when one artifact is the source of truth — but keep them schema-valid for the geeky validators.
- Replace verbose recap with concrete status, evidence, next action, and blocker.
- Collapse repeated command examples into the single working command when variants failed.
- Remove unused helper functions, unused CSS classes, unreachable branches, or frontend state that the UI no longer renders.
- Trim over-specific examples that make validators or link checkers treat placeholders as live broken links.

Do not erase evidence trails. If a report is noisy but contains validation proof, preserve the proof and shorten around it.

## Pass 4: Abstraction Reduction

Simplify only when call sites prove the abstraction is unnecessary:

- Inline private helpers called exactly once when the helper name does not carry important intent.
- Remove factories, strategies, adapters, or wrapper functions with a single implementation and no future requirement in the packet or issue.
- Replace over-generic types with concrete types only when all call sites agree.
- Consolidate duplication only when the shared version is easier to read than the originals.

Leave abstractions in place when they are public API, plugin compatibility surface, skill trigger metadata, framework convention (MediatR handlers, Razor page models, `Markefin.pages.*` registration), test seam, or documented future-extension point.

## Pass 5: Windows And Claude Environment Fit

Clean environment mismatch introduced by generated work:

- Prefer PowerShell-safe commands with quoted paths for anything documented for this host; flag bare-`python`, unquoted-path, or bash-only examples in docs meant for Windows.
- Prefer `git -C <repo>` for multi-repo work.
- Prefer the dedicated Grep/Glob tools (or `rg` with targeted roots in scripts) over broad recursive scans.
- Use `py -3` style PATH-stable launchers in scripts, not bare `python`.
- Keep `~\.claude` runtime-layer changes separate from durable plugin source changes under `C:\Users\gerald.khoo\geekhoo-plugins`; never edit `~\.claude\plugins\cache\`.
- Preserve cross-runtime compatibility files (`.claude-plugin`, `.codex-plugin`, `agents/*.yaml`) when the same skill folder serves multiple agent runtimes.

If host prerequisites block validation, record the missing prerequisite instead of claiming proof.

## Final Report Guidance

Report cleanup in this order:

1. Outcome: what was cleaned and where.
2. Evidence: validation commands and pass/fail/gap.
3. Scope: files touched and protected dirty work left untouched.
4. Skips: passes intentionally skipped and why.
5. Risk: remaining uncertainty or host prerequisites.

Avoid reporting "lines removed" as the main success metric. The goal is clarity per line with preserved proof.
