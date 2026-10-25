# Session archives, 2026-10-24/25

These are binary and bulky files from the cloud session that built the Linux MXC + LiteLLM + Langfuse eval path, checked in because that machine is ephemeral. They live at the repository root, outside every plugin folder, so they are never copied into a plugin install. The evidence and conclusions are in [geeky-orchestration/evals/analyses/session-20261025-evidence/](../../geeky-orchestration/evals/analyses/session-20261025-evidence/README.md) and [the runbook](../../geeky-orchestration/evals/mxc-litellm-runbook.md).

| Archive | Contents |
|---|---|
| `mxc-sdk-1.0.1-decompiled.zip` | ILSpy decompilation of `Microsoft.Mxc.Sdk` 1.0.1 (nuget), MIT-licensed; the license is included as `LICENSE-Microsoft.Mxc.Sdk.md`. Used to trace `MxcContainer.SpawnAsync` -> `Task.Run`, the cause of the exit-255 sandbox kills. |
| `installers.zip` + `installers.z01`, `.z02` (split) | `openai-codex-0.164.0-linux-x64.tgz` (the Codex CLI the runs used) and `pwsh.tgz` (PowerShell for Linux). |
| `build-output.zip` | `mxc-new/`: the MxcClaude host built with the spawn-thread fix (0.2.1). `mxcprobe/` and `gcprobe/`: diagnostic .NET probes. `slirp4netns-1.3.6/`: the source build tried while chasing the kills (it did not help). |
| `venvs.zip` | `lfpy/`: a Python venv with the `langfuse` SDK used for readbacks. `bisect/sdk/`: a venv with the `anthropic` SDK used for the LiteLLM auth check. These venvs point at the session machine's system Python, so they are records, not portable environments; rebuild them with `uv` as in the runbook. |

Extract the split archive by rejoining it first: `zip -s 0 installers.zip --out installers-joined.zip && unzip installers-joined.zip`. Every archive passed `unzip -t`, and the contents were scanned for credential values before commit.

SHA-256:

```
225122a55d14817411875e1abab05313ea8564a2c5e9f92647e4e01f93a866ff  mxc-sdk-1.0.1-decompiled.zip
3077bf53047e421ffeba5241eaa19edb1ec790c14a8bfdf3be40253311f51c9e  installers.zip
6f644f13c2f444ad62c6842930a19b1638c1b0893f7dad8f13a39ea3d06460b1  installers.z01
ce61b1858f8076295605baf71630cd4555b8153599105be1fd51b4d414eee657  installers.z02
4a34c4b9fa9ce70951dbe4a49bdf394f68b898c4d8d9a13ee168377052fbec8b  build-output.zip
34d68bfa7b36fc8eb8a00a2735ea8eba1ed27a74f26610528666252ac5ac0cbc  venvs.zip
```
