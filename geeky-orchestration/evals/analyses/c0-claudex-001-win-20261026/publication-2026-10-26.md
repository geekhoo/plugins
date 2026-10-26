# Repository publication, 2026-10-26

Historical record of the first publication, through the Claude timeout.
The later [closeout publication](publication-closeout-2026-10-26.md) records the
completed continuation and supersedes current-state claims below.

The owner requested grouped commits, aligned documents, a writing refresh, and a
push to origin. These publication task IDs describe repository work. They do not
refer to either contestant's implementation tasks.

| Publication task | Commit group |
|---|---|
| T1 | Agent-specific telemetry identities and named sessions, `ce9c3d1` |
| T2 | Windows MXC preparation, launch options, mock adapter, and verified build pin, `d1923e0` |
| T3 | Native trace parsing, task validation, phase boundaries, and score publication, `3e15536` |
| T4 | Immutable C0 captures, setup evidence, score records, and runtime exclusions, `49d00be` |
| T5 | Current documentation, historical scope notices, and writing refresh |

The source baseline is `c83d4b941341b4094b6e7d2f4ac125e5c1b74154` on `main`.
The initial fetch found no divergence from `origin/main`. The publication uses
ordinary commits and a normal push. It does not amend or replace prior history.

## Retained evidence

The artifact audit inspected 250 new evidence files, about 40 MB. It found no
live credential values and no file near GitHub's 100 MiB limit. Apparent key
matches inside a provider signature were false positives. All five solution
bundles passed the credential-content scan.

The copied `launch-evidence/hook-catalog-home` directory under the Codex run
remains local. Its 19 files contain runtime databases, sidecars, temporary state,
and an installation identifier. A narrow ignore rule excludes that directory.
No evaluated file or raw transcript was deleted or redacted.

Git attributes preserve the new baseline and analysis records without line-ending
normalization. This keeps the captured bytes and recorded hashes intact across
checkouts. Full API exports and private environment files remain outside Git.

## Document alignment

The [alignment report](alignment-report-2026-10-26.md) lists the drift and each
correction. Preparation and provider-failure records retain their dated scope.
Current entry points link the final Codex result and the Claude timeout. The
writing refresh preserves scores, identifiers, verdicts, and candidate artifacts.

Codex remains at parity 97.46. Claude remains at parity 90.33 with an unfinished
final closeout. Publishing these records does not authorize another paid run.

## Validation

The first targeted batch passed 117 tests with one skip. PowerShell syntax checks
passed for four changed scripts, and Node syntax checks passed for both new
JavaScript helpers. The broader batch exposed a stale native-qualification test;
the publication retains the default proof requirement and tests the explicit
owner-waiver path separately. The corrected full suite passed 374 tests and
45 subtests, with three skips. Three historical integration tests were excluded.

Run the same offline checks from the repository root with the evaluation Python:

```powershell
python -m pytest -q -p no:cacheprovider `
  geeky-orchestration/evals/scripts `
  geeky-orchestration/evals/telemetry `
  geeky-orchestration/evals/adapters/codex `
  geeky-orchestration/test_score_run.py -k 'not Run3IntegrationTest'
```

The final documentation check covered 37 Markdown files. Every file decoded as
UTF-8, with no remaining encoding-corruption markers or broken relative file
links. The staged evidence check confirmed byte-for-byte equality for all 202
evidence files in that commit. Stream and session SHA-256 values still match the
recorded originals in all five runs. No paid test, provider probe, or judge ran
during publication.

Before using the new telemetry configuration on another installation, run
`evals/telemetry/install-telemetry-tools.ps1` to regenerate the derived Codex
converter. An old installed converter may still emit native session IDs.
