# References

## Authoritative Requirements

- [`../../contract.md`](../../contract.md): root wordstat interface contract. This is authoritative and supplies exact requirements, usage/output/error text, and exit codes. The implementer must use its literals and not relax them.
- [`../../brief.md`](../../brief.md): concise user-facing feature brief; subordinate to `contract.md` where the contract is more specific.

## Design and Plan

- [`feature-specification.md`](feature-specification.md): research synthesis, goals, risks, design constraints and research sources.
- [`implementation-plan.md`](implementation-plan.md): one implementation phase, review gates, and delivery constraints.
- [`draft.md`](draft.md): requirement-to-task coverage matrix; every listed requirement is assigned to T1.

## Task and Tracking

- [`tasks/T1-implement-wordstat-cli.md`](tasks/T1-implement-wordstat-cli.md): frozen task contract, ACs, and exact validation requirements. Implement only its declared in-scope package and tests.
- [`kanban.md`](kanban.md): single source of task status; update after each lane movement and validate integrity.
- [`handoff.md`](handoff.md): decisions, plan review, execution checkpoints and current next action.
- `tasks/T1-implement-wordstat-cli.notes.md`: mutable implementation evidence, coder summary, review and resolution notes (created during implementation).

## Runtime Sources

- Python `utf-8-sig`: https://docs.python.org/3/library/codecs.html#encodings.utf_8_sig
- Python `str.splitlines`: https://docs.python.org/3/library/stdtypes.html#str.splitlines
- Python `re`: https://docs.python.org/3/library/re.html
- Python `open`: https://docs.python.org/3/library/functions.html#open
- Python text stream reconfiguration: https://docs.python.org/3/library/io.html#io.TextIOWrapper.reconfigure
- Python argparse: https://docs.python.org/3/library/argparse.html

## Validation

- From repository root: `python -m pytest -q`, `python -m wordstat --help`, and a JSON example smoke check using the task's exact expected output.
- Plan package gates are executed by the orchestration skill; implementation gates and evidence are recorded in handoff and T1 notes.
