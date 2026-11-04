# bridge-scout

Two throwaway probes used while designing `mxc-sandbox/bridge`. Neither needs the sandbox.

- `capture.mjs <out.jsonl> [port]`: a fake Anthropic endpoint on 127.0.0.1 (default port 8790). It records every
  request Claude Code sends (method, URL, headers with `authorization`/`x-api-key` replaced by their length, and
  the body) and answers each `/v1/messages` call with a one-word SSE stream. Point a Claude Code session at it
  with `ANTHROPIC_BASE_URL=http://127.0.0.1:8790` to see the request shapes the bridge has to map.
- `sweep.mjs`: sends one short reasoning question to the gateway at each effort level, three times, on both
  `/v1/messages` and `/v1/responses`, and prints output and reasoning token counts. It reads
  `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN` from the environment. This is how we measured that effort is
  applied on `/v1/messages` while reasoning tokens are only visible on the Responses route.
  Paid: 24 small calls.
