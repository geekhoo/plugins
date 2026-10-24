# Codex C1 run 3 readiness

2026-10-24, Asia/Singapore. Plugin HEAD `bee7b14c3b17b00a6ce0b5643015226a1d7ef963`. [Operator guide](../../../../codex-c1-run3-guide.md).

**Ready for a separately authorized launch; C1 run 3 has not started.** Requested matrix: Sol/high main, Sol/medium coder/task/default workers, Sol/xhigh reviewers. The medium catch-all applies at every depth. No paid API call, scorer/oracle run, repository staging/commit/push or cleanup.

| Check | Evidence |
|---|---|
| Fresh static preparation, 12/12 | [Output](prepare-only-output.txt), [paths](preparation.json), [profile](../../../../baselines/c1-csvledger/20261023T224720Z-e569fde0/parity-preflight.json) |
| Complete Codex 0.164.0 package, 45/45 | [Archive/file hashes](codex-package-check.json) |
| Pinned complete MXC copy, 18 matching entries | [Provenance](../../../../baselines/c1-csvledger/20261023T224720Z-e569fde0/mxc-build-provenance.json) |
| Real CLI/MXC with local scripted provider, two 21/21 checks, zero paid calls | [Reviewer attempt](native-reviewer-attempt.json), [architect reviewer attempt](native-architect-reviewer-attempt.json); raw requests, diagnostics and build hashes are in each attempt folder |
| Combined reviewer-proof gate, 30/30 | [Validation](../../../../baselines/c1-csvledger/20261023T224720Z-e569fde0/native-proof-validation.json); both role proofs retained with hashes |
| Offline adapter checks | [126 tests + 39 subtests](reviewer-matrix-tests.txt); [106 affected tests after final coverage correction](reviewer-proof-gate-tests.txt) |
| Tool/environment/roles/no-contestant state | [Readiness report](readiness.json), [source manifest](source-manifest.json), [bounded adaptation](adaptation-diff.json) |
| Shell setup without workload | [PowerShell helper](prepare-shell.ps1) |

The bounded eight-file adapter/test change adds optional reviewer effort, the architect review alias, role-bound model-free proof and two-reviewer fail-closed launch/audit checks. Canonical skills/agents/prompt, scorer sources, MXC source/binary pins and isolation remain unchanged. Source snapshots before and after preserve prior dirty work. The independently found reviewer-coverage issue was corrected and re-reviewed.

Both uv Python environments passed compatibility checks without installing anything; ordinary `python -m pip check` was unavailable because these environments have no pip module. Exact interpreters and the bundled PowerShell are pinned in the helper. Authentication contents were not read and live provider/auth access was not exercised.

The initial all-medium preparation and its retained-proof validation remain preserved as superseded evidence in `preparation-initial-all-medium.json`; the requested split uses the fresh prepared record above. Two native probes were preparation tests against a loopback-only scripted provider, with denied external egress. No C1 solution execution or paid model inference occurred.

Limits: actual automatic hook invocation during a paid contestant is unverified; the documented shell-write bypass and Codex calibration limits remain. Configuration proof does not establish model capability or support for future unseen trace shapes. Lock availability is rechecked at launch. This evidence grants no launch authorization.
