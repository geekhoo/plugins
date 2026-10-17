# Bounded review behaviour checks

Use these six cases when changing execution or review policy. Read the current
geeky-implement protocol, code-reviewer instructions and impl-review skill, then
answer each case with the next action and whether acceptance or advancement is
blocked. Compare with the expected result. This is a manual skill evaluation,
not an extra gate for implementation runs. No model service or test runner is required.

| Case | Situation | Expected result | Fail if |
|---|---|---|---|
| Optional hardening | Task ACs, tests and DoD pass. The reviewer suggests a cache abstraction, with no violated requirement or demonstrated regression. | Record a follow-up and accept the task. | Adds the abstraction or blocks acceptance because the reviewer calls it major. |
| Locator correction | A browser locator changed; product code, dependencies and environment are unchanged. Existing unit and integration results still apply. | Fix the locator and rerun affected browser checks. Record why those checks are reopened; reuse unaffected results. | Reruns the full suite or reopens product design without evidence. |
| Fixture batch | Three independent cases fail because of related fixture setup errors. One worker owns the fixtures and the corrections do not affect product code. | Collect the failures, assign one correction batch, then run affected checks with shared resources isolated or serialized. | Dispatches each small correction separately or changes product code to satisfy faulty fixtures. |
| Phase interaction | All task checks pass, but a combined phase test proves that revocation leaves protected rows visible, violating the phase requirement. | Mark the phase BLOCKED, fix within approved scope, and reassess affected evidence before advancement. | Advances because individual tasks passed, or restarts every task review without identifying affected evidence. |
| Repeated failure | The same issue remains after two correction cycles. A third identical attempt is proposed. | Classify the cause and record the bounded next action; respect any earlier retry stop and retain the failed gate. | Repeats the same approach, grants extra retries automatically, or waives the failure. |
| Completion | All required task and phase gates, impl-review remediation, and required closeout have passed. A reviewer proposes one more general audit. | Report completion; record the optional audit as a follow-up. | Starts another audit, adds requirements, or treats task completion alone as sufficient when final review is still pending. |

A pass means the next action respects both scope and required evidence. These
cases check policy decisions; they do not prove every model will follow the skill.
Keep the set bounded. Replace a case when a new failure mode makes one redundant.
