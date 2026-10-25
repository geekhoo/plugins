# Codex C0 attempt 3 (ant-claude via LiteLLM, Linux MXC, SIGHUP ignored)

Exit 255 after 150 s, like attempts 1-2, and launch-evidence/codex-exit.json was never written: the
whole sandbox was killed, not just Codex. MXC reports in-sandbox signal deaths as 128+n (129/137/143
verified), so a bare 255 means MXC killed bwrap from outside (provider monitor; TimedOut was false).
An unrelated curl load test died the same way once in three tries. Attempt 4 runs with a slirp4netns
and supervisor watcher. Not reference-eligible; kept as evidence.
