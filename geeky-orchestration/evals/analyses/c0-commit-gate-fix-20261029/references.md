# Evidence references

- User's 29 October 2026 instruction: prepare and run one native Codex C0 MXC
  attempt, rotated keys, literal credential scans and conditional public push.
- Initial clean source: `9a031e607464d003b7960cf3cf390b96562ef30c`.
- Gate fix: `629ae3f31dd230b859abaa2e9a2152ce1f3de5d5`.
- [Original procedure](../c0-codex-native-run-20261029/handoff.md), W1-W5.
- [Original native failure](../c0-codex-native-run-20261029/README.md).
- [Claude reference](../c0-luna-overtime-20261028/README.md), Luna/high,
  6000-second initial budget; overtime is a separate historical authorization.
- Local `outputs/c0-codex-native-fix-20261029/gate-tests.log`: 10 tests and
  12 subprocess subtests passed.
- Local `readiness/20261029T061819Z-1244138b/readiness.json`: inventory-ready,
  errors empty; records precommit dirty scope honestly.
- Local `scan-before-code-commit.json`: six staged files, zero literal hits.
- Local `rotated-langfuse-auth.json`: one existing-session read, exit 0,
  four traces and 100 observations. No credential values recorded.
- Preparation baseline plugin: `0b1f5fbc0e84b110ea0f9fa59ddfa711b46cf53a`.
  Before the fix the exported plugin delta was README-only; preparation will
  record the exact final exported delta and source/tool hashes.
- [Consumed attempt and terminal analysis](../c0-codex-native-fixed-run-20261029/README.md):
  preparation at 183aead passed; one launch crashed during T1; oracle 0/13 x3,
  Langfuse 23 traces / 920 observations, parity unavailable.
