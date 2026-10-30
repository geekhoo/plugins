# References

## Authoritative inputs

- `../../brief.md` (repository root): short feature request. Use as context; it defers the full behavior contract to `contract.md`.
- `../../contract.md` (repository root): authoritative interface and behavior requirements. Preserve exact semantics, output bytes, wording, streams, and exit codes; do not change it during implementation.
- `feature-specification.md`: researched feature scope and accepted interpretation. Read alongside the root contract; it does not supersede it.

## Planning and task contracts

- `implementation-plan.md`: design, phase order, validation strategy, and scope decisions.
- `draft.md`: requirement coverage matrix linking B1-B6 and R1-R6/contract clauses to tasks.
- `tasks/T1-core-cli.md`: task contract for module entry point and successful interface tests.
- `tasks/T2-contract-edge-cases.md`: task contract for error paths and boundary semantics; depends on T1.
- `kanban.md`: single source of truth for task lane state and package-level validation checklist.
- `review-development-project-manager.md`: PM review of coverage, ordering, and per-task evidence.
- `handoff.md`: decisions, workflow state, reviewer/gate outcomes, and next steps.

## Tests and implementation locations

- `../../wordstat/__main__.py` (repository root; to be created by T1): `python -m wordstat` entry point, using only the Python standard library.
- `../../tests/test_wordstat.py` (repository root; to be created/extended by T1 and T2): black-box pytest subprocess suite. Run `python -m pytest -q` from repository root.

## Research sources

- Python 3.11 codecs, `utf-8-sig`: https://docs.python.org/3.11/library/codecs.html#encodings-and-unicode
- Python argparse `ArgumentParser.error`: https://docs.python.org/3.11/library/argparse.html#argparse.ArgumentParser.error
- Python `TextIOWrapper.reconfigure`: https://docs.python.org/3.11/library/io.html#io.TextIOWrapper.reconfigure
- Python `str.splitlines` and `str.lower`: https://docs.python.org/3.11/library/stdtypes.html#str.splitlines, https://docs.python.org/3.11/library/stdtypes.html#str.lower
- Python regular expressions and string sequence semantics: https://docs.python.org/3.11/library/re.html#regular-expression-syntax, https://docs.python.org/3.11/library/stdtypes.html#text-sequence-type-str
- Python subprocess and pytest parametrization: https://docs.python.org/3/library/subprocess.html#subprocess.run, https://docs.pytest.org/en/stable/how-to/parametrize.html
