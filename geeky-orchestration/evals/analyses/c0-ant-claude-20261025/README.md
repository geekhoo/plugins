# C0 on ant-claude, both harnesses (2026-10-25)

First complete end-to-end C0 runs in Linux MXC (mxc-sandbox 0.2.1), both through LiteLLM `ant-claude` (`mimo-v2.6-flash`), telemetry on (Langfuse env `mxc`).

| | Codex run 6 | Claude run 4 |
|---|---|---|
| Run folder | `baselines/c0-wordstat/20261025T030302Z-a037e8ab` | `baselines/c0-wordstat/20261025T030323Z` |
| Exit | completed, 0 | completed, 0 (1 provider refusal, auto-resumed: `interventions = 1`) |
| Wall time | 3383 s | 4175 s |
| Commits | 9 | 12 |
| Oracle | 13/13, stable over 3 | 13/13, stable over 3 |
| Langfuse | 659 observations, coverage complete | 828 observations, coverage complete |
| Tokens (input / cached / output) | 20.8M / 20.1M / 187k | 16.7M / 15.3M / 425k |

Notes:
- Both exceed the C0 token ceiling (6M); nearly all of it is cached input. The ceiling was set before any real run and needs recalibrating.
- Claude's `cost_usd_estimate` ($25.20) is Claude Code's guess for an unknown model, not the LiteLLM price.
- Claude run 4 used `ANTHROPIC_AUTH_TOKEN`; it started before the runner switched to `ANTHROPIC_API_KEY`.
- No sandbox kills on either run (the old spawn-thread bug killed earlier runs within 1-3 minutes).
- Neither run is scored yet: `score-run.py` needs reviewed manual verdicts.
