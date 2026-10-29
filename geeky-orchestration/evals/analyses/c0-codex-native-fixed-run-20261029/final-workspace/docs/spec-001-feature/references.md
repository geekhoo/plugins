# References and Implementation Guide

## Authoritative Requirements

- [`../../contract.md`](../../contract.md) — authoritative interface, package, counting, output, encoding, and error requirements. Resolve any apparent conflict in favor of this file; its specific argparse-default usage-error row governs that case.
- [`../../brief.md`](../../brief.md) — concise user outcome and pytest requirement. It is subordinate to the more precise contract.
- [`feature-specification.md`](feature-specification.md) — researched scope, architecture, acceptance criteria, sources, and documented decisions. Frozen for implementation.
- [`draft.md`](draft.md) — requirement-to-task coverage matrix; every listed requirement is covered by T1 or T2.

## Frozen Implementation Contract

- [`implementation-plan.md`](implementation-plan.md) — two-phase architecture, phase gates, validation commands, and decisions. Do not edit during implementation.
- [`tasks/T1-counting-core.md`](tasks/T1-counting-core.md) — Phase 1 contract for `wordstat/core.py`, `analyze_text(text, top)`, and `tests/test_core.py`; no dependencies.
- [`tasks/T2-cli-contract.md`](tasks/T2-cli-contract.md) — Phase 2 contract for `wordstat/__main__.py`, consumption of T1's API, and `tests/test_cli.py`; depends on T1.
- [`review-development-project-manager.md`](review-development-project-manager.md) — semantic and sequencing reviews, resolved findings, and ACCEPT verdict.

## Tracking and Implementation Evidence

- [`kanban.md`](kanban.md) — task lane source of truth. T1 starts Ready; T2 stays in Backlog until T1 is Done because it depends on T1. Validate the kanban after every lane move.
- [`handoff.md`](handoff.md) — running decisions and workflow checkpoint. Append task/phase findings and exact validation evidence here; do not change frozen task bodies to handle discovered contract issues.
- Planned tests: `tests/test_core.py` for pure R3/R4 calculations and `tests/test_cli.py` for the subprocess-level interface, exact stdout/stderr bytes, and exit status. T2 also requires a deterministic monkeypatched `OSError` test for unreadable input.

## Required Commands

- Phase 1: `python -m compileall -q wordstat`; `pytest tests/test_core.py -q`.
- Phase 2 and final suite: `python -m compileall -q wordstat`; `pytest -q`; from the repository root, `python -m wordstat --help`.
- Capture subprocess results as bytes. Do not claim other operating systems were tested unless they were actually run.

## Workflow Notes

- Keep `implementation-plan.md`, `feature-specification.md`, `draft.md`, `references.md`, and task bodies frozen. `kanban.md`, `handoff.md`, and `tasks/Tx-*.notes.md` are mutable tracking artifacts.
- Complete T1's task review and Phase 1 review before moving T2 from Backlog to Ready. Each phase needs a task verdict for each member and a reviewer-agent verdict of READY TO ADVANCE before the next phase begins.
- The final implementation review must use `impl-review`; acceptance in this package does not authorize release or deployment.
