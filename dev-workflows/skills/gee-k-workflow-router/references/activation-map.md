# Activation Map

| Trigger | Activate |
|---|---|
| review, audit, evidence, line refs | `dev-workflows:evidence-review` |
| fix findings, address review | `dev-workflows:review-remediation` |
| validate, tests, complete set | `dev-workflows:repo-validation-runner` |
| browser, UI, SPA, Playwright | `browser-verify`, `playwright-testing`, `dev-workflows:browser-qa` |
| read-only, do not edit | `dev-workflows:scope-guard` |
| resume, continue, status | `dev-workflows:resume-inventory`, `dev-workflows:status-interrupt` |
| AGENTS, README, docs refresh | `dev-workflows:align-docs`, `dev-workflows:docs-sync` |
| plan, spec, kanban, handoff | `dev-workflows:planning-packet`, `geeky-orchestration:geeky-plan` |
| plugin, skill, marketplace, benchmark | `dev-workflows:plugin-skill-lifecycle`, `skill-creator`, `skill-review` |
| web search, official docs, current docs | `dev-workflows:research-gated-spec` |
| large corpus, all documents, PDFs | `dev-workflows:corpus-sharder`, `dev-workflows:document-corpus-pipeline`, `pdf` |
| Langfuse, observability, traces, scores | `dev-workflows:observability-review`, `langfuse` |
| deploy, runtime setup, local env | `dev-workflows:deployment-setup`, `dev-workflows:env-check` |

If multiple triggers apply, use the narrowest safety skill first:

1. `scope-guard`
2. `resume-inventory`
3. `evidence-review`
4. `repo-validation-runner`
5. domain-specific skill
