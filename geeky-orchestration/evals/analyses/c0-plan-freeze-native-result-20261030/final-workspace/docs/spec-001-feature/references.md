# References

## Requirements and design

- [`../../brief.md`](../../brief.md): concise outcome and test expectation; consult for user intent, subordinate to the contract.
- [`../../contract.md`](../../contract.md): authoritative package, CLI, computation, formatting, encoding, and error requirements. Implement exactly; don't paraphrase expected literals.
- [`feature-specification.md`](feature-specification.md): approved scope, risks, and acceptance criteria.
- [`implementation-plan.md`](implementation-plan.md): task/phase and design sequencing for the implementation.
- [`draft.md`](draft.md): requirement-to-task coverage matrix; update only during plan-review if a correction is required.

## Execution and tracking

- [`tasks/T1-wordstat-cli.md`](tasks/T1-wordstat-cli.md): frozen task contract; validation requirements must run before the task is accepted.
- [`kanban.md`](kanban.md): authoritative task lane. Move each task once and run `validate-kanban.py` after every move.
- [`handoff.md`](handoff.md): running decisions/evidence log and next-step instructions.
- `tests/`: planned process-level pytest tests, to be created as part of T1; verify outputs as bytes where newline/encoding determinism matters.

## Supporting technical references

- [Python 3.11 argparse](https://docs.python.org/3.11/library/argparse.html): `prog`, parsing, and usage error behavior.
- [Python 3.11 codecs](https://docs.python.org/3.11/library/codecs.html#encodings-and-unicode): `utf-8-sig` BOM handling.
- [Python 3.11 string methods](https://docs.python.org/3.11/library/stdtypes.html#str.splitlines): contract's line counting primitive.
- [Python 3.11 `re`](https://docs.python.org/3.11/library/re.html): explicit token matching.
- [Python 3.11 JSON](https://docs.python.org/3.11/library/json.html#json.dumps): serialization defaults.
- [Python 3.11 text stream reconfiguration](https://docs.python.org/3.11/library/io.html#io.TextIOBase.reconfigure): explicit encoding and newline.
