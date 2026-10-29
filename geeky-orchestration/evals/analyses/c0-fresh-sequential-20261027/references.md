# Sequential C0 evidence references

- [Codex native run](../../baselines/c0-wordstat/20261026T202318Z-fc8f0aa8/run.json)
- [Codex native session](../../baselines/c0-wordstat/20261026T202318Z-fc8f0aa8/session.jsonl)
- [Codex stream](../../baselines/c0-wordstat/20261026T202318Z-fc8f0aa8/stream.jsonl)
- [Codex Langfuse summary](../../baselines/c0-wordstat/20261026T202318Z-fc8f0aa8/langfuse.json)
- [Claude native run](../../baselines/c0-wordstat/20261026T202649Z/run.json)
- [Claude native session](../../baselines/c0-wordstat/20261026T202649Z/session.jsonl)
- [Claude Langfuse summary](../../baselines/c0-wordstat/20261026T202649Z/langfuse.json)
- [Claude coverage](../../baselines/c0-wordstat/20261026T202649Z/langfuse-coverage.json)
- [Mapping implementation context](../codex-v2-litellm-mapping-20261027/README.md)
- Ignored operator evidence: `outputs/c0-fresh-sequential-mapped-20261027/`.
- Preserved pre-contestant setup failure: `outputs/c0-fresh-sequential-20261027/`.

Codex decisive lines: main session93/96 (text wait tool and completion), stream33
(reconnect) and37-38 (message/turn.completed); children own aborts73/70/88.
Claude decisive lines: session169-170 (spec complete/planning starts),269 (PM
review availability),496-497 (planning complete/plan-review starts),518 (alignment
verdict),585 (sequencing reply),586-587 (last evidence pass). Its review-plan.md
ends after phases1-2, with no consolidated overall verdict at timeout.
