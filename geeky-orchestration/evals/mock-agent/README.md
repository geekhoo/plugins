# Mock actor scenarios

`c0-full` is a SCRIPTED MOCK fixture for `c0-wordstat`. It takes feature requirements from the public case documents, reads each matching workflow `SKILL.md` at stage entry, runs the public Python contract in a fresh disposable Git workspace, and captures successful kanban writes and local command results in each actor's trace format. The positive fixture commits candidate source and required tests together.

Use `-MockAgent -MockScenario c0-full -NoTelemetry` with the existing baseline runner and `-Case c0-wordstat`. The runner copies the helper files into the actor's isolated config directory, avoids Claude User OAuth lookup for mock runs, and denies network egress for this scenario. The fixture makes no provider, model, oracle or telemetry calls.

The regression tests also run one negative history in a fresh candidate repository: source is committed first, required tests later. They exercise the unchanged H1 selector against the real captured In Progress and Done writes, require the selected full SHA to be the source-only commit, then prove its declared test command fails while the later final HEAD passes.

Scripted review text is fixture data, not evidence of model behavior or review quality. The original support checkout and capture remain under `evals/analyses/c0-post-remediation-mock-20261026/support/`.
