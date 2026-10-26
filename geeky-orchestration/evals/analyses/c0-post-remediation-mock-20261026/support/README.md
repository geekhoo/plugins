# C0 fixture support evidence

Checkout: C:/repos/c0-remediation-mock-20261026/full-harness
Pinned HEAD: d90bbd352d5722784180100bf5e431e91bc55210 (unchanged).
Initial sparse checkout clean; final changes limited to the seven fixture support files in fixture-support-manifest.json.
No fixture-checkout commits, pushes, provider calls, sign-ins, telemetry hooks, network requests, oracle invocation or MXC execution performed.
Candidate Git commits are disposable test artifacts produced by the scripted actor.

## Validation

1. C:/Python314/python.exe -m pytest -q -p no:cacheprovider geeky-orchestration/evals/mock-agent/test_c0_fixture.py geeky-orchestration/evals/adapters/codex/test_mock_codex.py --basetemp=outputs/c0-full-fixture/verified-pytest-temp
   Exit 0; 25 passed in 33.99s; stdout/stderr: verified-tests.log.
2. pwsh -NoProfile -File outputs/c0-full-fixture/validate-scripts.ps1
   Exit 0; both modified runner PowerShell AST parses and git diff --check pass; script-validation.log.
3. C:/Python314/python.exe outputs/c0-full-fixture/save-evidence.py
   Exit 0; seven source hashes and support diff saved; manifest.log, fixture-support-manifest.json, fixture-support.diff.

Python: 3.14.7, pytest 9.1.1, Windows PowerShell 7.
The complete first focused check (23 passed) remains in focused-tests.log. An additional legacy regression test initially failed because inherited PATH selected Python 3.13 without pytest (final-tests.log); only the test environment PATH was corrected, then all 25 passed. No runtime bypass was added.

## Acceptance mapping

- Both copied actor payload shapes run explicit c0-full: verified-pytest-temp/test_full_scripted_fixture_bot0 (Claude) and bot1 (Codex).
- Each actual candidate runs 17 public-contract subprocess tests, including CRLF+optional BOM, Unicode and splitlines counts, tie ordering, UTF-8 LF exact output, large top (5000 digits), usage and file errors. Source and tests committed together.
- Planning-folder, task-schema, kanban at transitions, DoD per task and commit gates all run with exit 0; .git/c0-full-commands.json gives exact argv/stdout/stderr/exits.
- One phase review artifact READY TO ADVANCE, T1/T2 Done, three saved current domain replies consolidated Overall PASS, Run Summary and done heartbeat asserted by focused tests.
- Candidate .git/c0-full-summary.json maps paths, three candidate commits and source/test hashes; deadline/reserve fields exactly match injected child values.
- SCRIPTED MOCK labels and zero model/token/cost usage asserted; all child Python processes had denied socket connections via test sitecustomize. Only git and current Python are dispatched by the helper.
- Existing Codex mock tests pass; existing Claude happy and gate-fail subprocess behavior remains separate, unchanged stub semantics; Codex bounded slow and crash negative subprocess scenarios pass.
- Runner checks require -NoTelemetry and c0-wordstat for c0-full; --deny-net is appended only for that mock scenario; existing lifecycle/deadline logic unchanged.

## Scope limits

Reviews are deterministic scripted judgments, not actual agents or LLM compliance evidence. Source came only from public brief/contract, never oracle or historical candidate implementations. Parent owns actual pinned MXC executions, oracle results, and final analysis. Main source checkout was never edited. No additional product fixes or packet execution were performed.
