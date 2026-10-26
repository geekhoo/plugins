# C0 post-remediation non-chargeable MXC mocks

The original capture contains twelve actual MXC attempts, including both full scripted fixtures passing 13/13 oracle tests over 3 repetitions. Its F1 terminal-state defect and F2 measured deadline overhead are preserved as historical observations. Scripted reviews are not model compliance.

The separately authorized [follow-up implementation](follow-up-implementation.md) fixes F1, defines F2's supported boundary, and maintains guarded fixtures with recognized H1 Done evidence. Fresh verification is 147 passed / 1 optional skip plus three bounded real-MXC checks. [Machine evidence](follow-up-evidence.json) and current [handoff](handoff.md) distinguish current results from the original capture and retain the historical replay/live-behavior limits.

Read [report](report.md), [metrics](metrics.json), [manifest](evidence-manifest.json), [source fingerprints](source-fingerprints.json), then [handoff](handoff.md).

Current [operator readiness](../../c0-readiness.md) records installed local tools and 28 passing mock checks. Live telemetry and paid canaries remain held.

## Publication status

The mock evidence is committed in grouped history. [Follow-up plan](follow-up-plan.md)
records the bounded F1/F2/H1 remediation and validation scope; it authorizes no
implementation or additional evaluation by itself. See the capture-time caveats in
[report](report.md) and [handoff](handoff.md) for unresolved findings and limits.

The source changes are published in commits `ebcbacd` and `6462c6d`; the subsequent
commit reconciles current handoff/evidence pointers. The implementation note records
LF normalization mappings for five tested CRLF files. Its earlier no-commit wording
describes the review-time state.
