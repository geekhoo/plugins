# Luna/high C0 preparation — live held

Owner request: prepare both C0 MXC runners through LiteLLM using
`vercel/gpt-6-luna` at high; do not run. The misspelled `verce/` was normalized to
the previously tested alias. All main, worker and reviewer settings request high.
Retained settings are 6000 seconds, 60-second advisory closeout reserve, one
attempt per harness and zero recoveries. Sequence remains Codex then Claude.

Required runner/workflow fixes are committed in
`b74536ada16656b2c28e0183c5e279047b001766`. The owner then explicitly waived
qualification for this Luna pair; [the recorded waiver](qualification-waiver.json)
retains the exact authorization, model, harnesses, settings and hold boundary.
It supplies no qualification proof and changes no isolation requirement.

Official preparation, source/prompt manifests, role readback, unexecuted launch
commands and separate 18-file MXC build copies are recorded under local
`outputs/c0-luna-final-preparation-20261028/` (ignored evidence). The machine
record is `preparation.json`; `verification.json` binds final checks. Both runners
materialize fresh seed repositories and committed plugin exports. Claude uses
`-PrepareOnly`; Codex omits both `-Launch` and `-MockAgent`. Neither path runs
the seed oracle or a contestant/MXC workload. Codex dumps the installed local
model catalog and generates its static profile; no provider probe is included.

Codex uses its existing V2-to-V1 LiteLLM bridge at launch; no listener was started.
Its eight role registrations explicitly use Luna/high. Claude's optional new
`-Effort high` sets main CLI effort, descendant environment effort and recorded
runner/telemetry effort. Omitted effort retains previous behavior. Configured
high remains distinct from observed provider behavior.

Langfuse hooks are configured during preparation using `codex-mxc-win` and
`claude-mxc-win` identities. Credentials are read only into the isolated operator
process from the external env file; no values are stored in artifacts. There is
no live telemetry operation or delivery claim. Future launch requires tracing
enabled from startup and a fresh explicit owner instruction.

The committed-export gate remains enforced. The new Luna waiver resolves the
qualification prerequisite for this prepared pair only; the `claudex-001` waiver
remains historical. Selected previous endpoint/tool checks do not establish
full workflow or all-role/high behavior. Both evaluations are stopped.

The prepared absolute deadline expires during a hold. Later launch must invoke
the saved official runner command afresh to establish a new deadline and fresh
runtime directories. Do not replay `prepared-launch.json.host_args` or reuse the
materialized static profile as a live attempt. This preparation grants no run,
provider/telemetry probe, judge or push authority. The source commits are local.

Verification: 118 focused tests and 45 subtests passed; the unchanged runner suite
has saved 60-pass proof. Current fresh inventory and existing valid mock evidence
are bound in `verification.json`; 115 historical captures remain hash-pinned.

Stale records: the first `outputs/c0-luna-preparation-20261028/` drafts and prior
`claudex-001` commands remain preserved and are superseded by the final prepared
manifest. Historical captures/scores remain unchanged. Current readiness and
root/plugin READMEs point here; earlier dated investigation reports retain their
capture-time uncommitted/hold statements as history.
