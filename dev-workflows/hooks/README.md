# dev-workflows Hooks

This folder holds portable hook assets for the `dev-workflows` plugin.

- `env-canary.sh` is wired through `hooks.json` as a `SessionStart` canary. It emits a warning when Python is missing from PATH.
- `operational-efficiency-guard.ps1` is a Codex/OMX companion guard. The active machine wiring invokes it through `~/.codex/hooks/omx-native-hook-windows-shim.ps1` by passing the hook JSON as `-InputJson`, then delegates to OMX. Keep it warning-only unless an explicit workflow changes that contract.

Do not wire new hook scripts into `hooks.json` until the target runtime contract is validated with a representative payload.
