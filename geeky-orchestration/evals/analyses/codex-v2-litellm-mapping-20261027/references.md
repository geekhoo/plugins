# Mapping fix references

## Implementation and current evidence

- [Pure mapper](../../adapters/codex/litellm_bridge/mapper.py)
- [Authenticated transport](../../adapters/codex/litellm_bridge/server.py)
- [CLI](../../adapters/codex/litellm_bridge/__main__.py)
- [Offline mapper/transport tests](../../adapters/codex/litellm_bridge/test_bridge.py)
- [Host lifecycle](../../adapters/codex/litellm-bridge.ps1)
- [Lifecycle tests](../../adapters/codex/test_litellm_bridge_lifecycle.py)
- [Future runner integration](../../scripts/run-codex-baseline.ps1)
- [Source inventory](../../scripts/check-c0-readiness.py)
- Repository-local ignored evidence: `outputs/codex-v2-bridge-verification-20261027/`.
- Prior source-bound investigation: `outputs/codex-decryption-investigation-20261027/`.
- Prior held/reset record: `outputs/c0-clean-live-20261027/reset-held.json`.

## Pinned protocol contract

Codex 0.164.0 source commit `6aaac694803004a63c6f393d153c96d22521a6b9`:

- [Plaintext metadata selection](https://github.com/openai/codex/blob/6aaac694803004a63c6f393d153c96d22521a6b9/codex-rs/core/src/tools/router.rs#L54)
- [V2 message construction](https://github.com/openai/codex/blob/6aaac694803004a63c6f393d153c96d22521a6b9/codex-rs/core/src/tools/handlers/multi_agents_v2.rs#L54)
- [Schema encryption annotation](https://github.com/openai/codex/blob/6aaac694803004a63c6f393d153c96d22521a6b9/codex-rs/tools/src/json_schema/types.rs)
- [Namespace/function declarations](https://github.com/openai/codex/blob/6aaac694803004a63c6f393d153c96d22521a6b9/codex-rs/tools/src/responses_api.rs)
- [Response item variants](https://github.com/openai/codex/blob/6aaac694803004a63c6f393d153c96d22521a6b9/codex-rs/protocol/src/models.rs)
- [SSE event handling](https://github.com/openai/codex/blob/6aaac694803004a63c6f393d153c96d22521a6b9/codex-rs/codex-api/src/sse/responses.rs)

Upstream reports corroborate the compatibility issue but are not evidence that
this particular local fix has full workflow qualification:
[33267](https://github.com/openai/codex/issues/33267),
[33551](https://github.com/openai/codex/issues/33551).
