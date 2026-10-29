# References

- [Diagnostic tool](../../tools/responses_contract/README.md), [pinned sources](../../tools/responses_contract/sources.json).
- [Original decryption fix](../codex-v2-litellm-mapping-20261027/README.md), [subsequent root-cause analysis](../c0-root-causes-20261027/README.md).
- [Terminal evaluations](../c0-fresh-sequential-20261027/README.md).
- Fresh source: `4228c3f73fc3894c86725cf42900406c1d2d981f`; local tool hashes in probe authorization.json.
- `outputs/litellm-six-models-20261027/authorization.json`: exact model/cap/mode/request limits.
- `outputs/litellm-six-models-20261027/results.json`: raw diagnostic verdicts and report hashes.
- `outputs/litellm-six-models-20261027/interpreted-results.json`: outcome classification without conflating cap exhaustion/native encryption with incompatibility.
- `outputs/litellm-six-models-20261027/verification.json`: client request count, redaction/preservation and stopped-process proof.
