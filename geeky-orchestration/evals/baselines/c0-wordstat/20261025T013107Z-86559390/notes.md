# Codex C0 attempt 4 (ant-claude via LiteLLM, Linux MXC, watcher on)

Exit 255 at 01:33:42 like attempts 1-3. The sandbox slirp4netns (pid 12950) disappeared in the same
second the bwrap processes were torn down (slirp-watch/liveness.log, 1 s resolution); its supervisor
log shows no error. Forced .NET GC in a scratch host did not kill a sandbox (ruled out). Next test:
whether ending a Claude Code turn (stop hook) coincides with the kill. Not reference-eligible.
