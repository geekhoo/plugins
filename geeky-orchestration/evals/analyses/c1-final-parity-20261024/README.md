# Final-pair scoring parity: Claude 6 and Codex 2

2026-10-24. Scope is the final pair only; no historical Codex expansion, rubric changes, skills/agents changes, paid execution or MXC launches.

## Result

| Run | Quality | Adherence | Consistency | Task tier | Raw composite |
|---|---:|---:|---:|---:|---:|
| Claude 6 | 98.595166 | 100 | 100 | 87.635011 | 98.27180923451854 |
| Codex 2 | 100 | 97.058824 | 100 | 90.694168 | 98.04000506482035 |

Both strict scores are complete, with no unresolved judgments. Codex 2 now derives process facts automatically from raw session/descendant rollouts, without an operator process-evidence input. Legitimate manual judgments and exact previously saved own-commit validation remain inputs for both. This is automatic process normalization, not automated subjective judgment or fresh contestant validation.

[Verification](verification.json), [Codex score](run2-automatic/score.md), [fact comparison](run2-automatic/normalization-comparison.json), [automatic evidence](run2-automatic/automatic-process.json), [Claude regression](claude6-regression/score.md).

## Bounded implementation

- `codex-process.py` derives delegated stages, coder task ownership, explicit phase/task reviews, literal PowerShell lane insertions and commit identity from visible own-history records. No run-specific IDs, ordinals or expected score constants are used in extraction.
- `codex-trace.py` uses that route for the supported delegated implementation shape when no operator process artifact is supplied. Explicit historical annotations remain supported and labeled separately.
- The shared scorer counts completed native Codex validation commands rather than duplicate JS/poll wrappers, resolves captured commit prefixes/subjects uniquely, and propagates missing extraction facts. A strict withheld composite now returns exit 1 after writing its diagnostic reports; invalid input retains its existing error path.
- Ambiguous coder mappings, mixed task review verdicts and unbound multi-task commit identities reject. Commit ownership requires the actual commit-message variable's literal assignment and one Tasks trailer; matching counts/order alone are insufficient. Unsupported syntax is not guessed.

The automatic and annotated run-2 facts match for coder ownership, review verdicts/timestamps, eleven lane moves, handoff task sets and four implementation commits. Only two scoped stage starts differ: native dispatch is 0.501s earlier for planning and 7.319s earlier for implementation than the annotation's child task-start. Neither changes a score. Validation attempts remain 1/1/2.

## Verification and preservation

Focused parser/process/trace/stage tests: **68 passed, 2 optional proof tests skipped**. The retained raw run-2 tests ran; the skips concern optional environment-provided fixture proofs, not run-2 acceptance. Strict CLI missing-composite behavior was observed failing before correction. Raw extraction tests failed before implementation; negative ownership/review/commit identity cases now pass. Independent source review's two ambiguity findings were corrected and re-reviewed.

Guard/profile/trust offline tests: **64 passed**. No guard implementation changed. The retained run-2 native summary already records successful native patch and guard-context checks. Catalog trustStatus=untrusted is observed before applying the exact current-hash trust override; it does not demonstrate an untrusted paid launch. The shipped warn guard and Codex bridge cover corresponding edit/patch paths, including move/delete paths. Shell writes bypass both; expanding shell coverage is outside this parity match. Actual automatic hook invocation during the paid run remains unverified.

Claude 6 was scored once from an isolated bundle clone with its saved cache and judgments; all raw dimensions match its previous complete derivation exactly. The final Codex source was rechecked after the ambiguity fixes, reusing cached results. No contestant validation commands ran. The new automatic score artifacts contain the final verification; interim timestamped outputs from this work were superseded, not retained as a separate historical run.

All 206 original four-run evidence files still match their preserved hashes. Previous analysis folders and original scores remain unchanged. `sources/` snapshots and verification hashes identify this implementation. The earlier six-Claude proof remains valid for its earlier frozen source; this change intentionally verifies only the requested final Claude/Codex pair.

## Use and limits

For the supported Codex shape, omit `--process-evidence`; retain `--harness codex`, source-backed `--manual`, exact `--validation-cache`, `--no-rerun`, `--require-complete` and a fresh `--out`. Never target a historical run folder for output. A nonzero result or withheld composite is an incomplete result, not permission to invent mappings. New workflow shapes need evidence and tests before support is claimed.

The supported final-pair measurement goal is met. Broad extractor generality, shell hardening, paid-session hook proof, model-effect claims and new contestant runs remain outside this closeout. No staging, commits or pushes.
