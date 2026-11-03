# Documentation refresh handoff

Target machine: Windows; workdir `C:\Users\gerald.khoo\geekhoo-plugins`. Review date: 3 November 2026, Asia/Singapore.

Read in order: [README.md](README.md), [findings.md](findings.md), [inventory.csv](inventory.csv), [registrations.csv](registrations.csv), [references.md](references.md), then [kanban.md](kanban.md).

The reviewed base was `ea94635d2f76918f4a01699aea3e356f90954033`; verify it remains an ancestor with `git merge-base --is-ancestor ea94635d2f76918f4a01699aea3e356f90954033 HEAD` before using this snapshot. Subsequent documentation commits do not change that review pin. Verify the MXC source boundary `554c50acb90ecf15f161dc8f88e9ad12c8f015eb` and its parent `c957a431e4e1144b4280cee92d15bb90646e21ee` through Git. The first retained C1 run used `24c4e6daa6199be8196970ece35c79d6f184e8a4`. This is a dirty checkout; the pinned source does not describe all local source and evidence.

Eight Terra 6.1 batches completed their assigned history inventories. Sandbox, Codex, operations, scoring, workflow and agent documents were checked against owning source; repository/plugin guides were checked against manifests and current files. Historical captures were inventoried with selective packet-index inspection. No original capture, frozen case requirement or score was refreshed in place.

The parent applied reviewed replacements serially and regenerated all 30 registrations after fixing the canonical phase-review summary and portable terminology source locators. The inventory includes two older canonical documents needed for that linked correction. Existing Python/PowerShell/bridge modifications and untracked preflight/C1 work belong to earlier work and must be preserved. Detailed agent reports, the original status, document backup and source hashes are retained locally in `outputs/docs-refresh-20261103/`.

Validation completed:

- Local relative links resolve in the 62 refreshed existing Markdown documents and five new Markdown records. The index explicitly labels ignored local evidence links that will be absent in a fresh clone.
- Hash comparison preserves all 359 historical documents and all 12 frozen case documents. Existing non-document edits and untracked source work match the initial backup.
- Of 272 source/config paths hashed before integration, only six generated Codex TOML instruction bodies changed. An independent Terra check parsed all six TOMLs and verified unchanged non-instruction metadata against HEAD.
- All 30 harness projections match their six canonical agent bodies. The phase-review summary matches the existing execution protocol.
- `git diff --check` passed with `cr-at-eol` handling for the Windows checkout. HEAD was unchanged at the end of the source review; the owner subsequently authorized the documentation commits below. No contestant, oracle, provider, scoring or publication command was run.

The final operational review identified three wording issues: a historical credential source presented as future policy, an undated 2026-10-27 stopped-state claim, and a historical C1 reference labelled current. All three were corrected. Validation artifacts and both independent integration reviews are retained under `outputs/docs-refresh-20261103/`.

The owner subsequently authorized small local documentation commits and explicitly prohibited pushing. Mixed documents use refresh-only staged content: pre-existing preflight/scoring paragraphs, smoke/run drafts and sandbox additions remain in the worktree. The refreshed credential wording and smoke clarification inside those pre-existing draft sections also remain uncommitted because they cannot stand alone against the reviewed HEAD. The current-state index records the later campaign evidence separately.

Any later takeover is limited to maintaining this documentation record against verified new source changes. Do not launch contestants, contact providers, publish scores, overwrite historical results or treat these pins as fresh launch authority. Use a concise handback of at most 500 words, with changed paths, validation evidence and unresolved discrepancies.

## Local documentation commits

The owner authorized documentation-only commits on 3 November 2026 and prohibited push. Each group passed the commit-message gate and staged whitespace checks.

| Commit | Group |
|---|---|
| `4251e23a16be2af9a0448304e6998120f9830309` | docs(workflow): align gates and agent guides |
| `bc942910785e90adad4c7734734aa414faa30280` | docs(mxc): clarify sandbox behavior |
| `717b5c651a771c6eba18b197ae5cc25552cb4041` | docs(evals): refresh operator references |
| `ec7879a89ddf46b34620ce8a94011e8f8324dd8b` | docs(packaging): correct dependency notes |

The final `docs: record MXC documentation refresh` commit contains this handoff, the inventory and root navigation. Resolve its SHA with `git log -1 --format=%H -- docs/mxc-documentation-refresh-20261103/handoff.md`; a commit cannot contain its own hash.

Nine pre-existing hunks across seven mixed documents were excluded from staging. All original code and untracked work remain outside these commits. Final byte/hash and index checks are recorded in the local `outputs/docs-refresh-20261103/publication/` folder.

## Post-commit review corrections

A review of the five commits on 3 November found remaining drift. The owner authorized these text corrections and committed them locally as one group, `docs: correct workflow, MXC and eval doc drift`, resolved with `git log -1 --format=%H -- docs/mxc-documentation-refresh-20261103/handoff.md`. Earlier unrelated hunks in `mxc-sandbox/README.md` and `mxc-troubleshooting/SKILL.md` stay in the worktree:

- `mxc-troubleshooting/evals/evals.json`: expected outputs for the hook and `--isolated` prompts now match the skill.
- `scripts/check-dod.py`: docstring states the gate runs with the Done move. Behavior is unchanged.
- `geeky-implement/SKILL.md`, `execution-protocol.md`, `docs/end-to-end-workflow.md`: a split phase review records every dispatch's agent ID and marks the verdict issuer. `SKILL.md` also gains the last-dispatch rule.
- `dev-workflows/PACKAGING.md`, `langfuse-evaluators/README.md`, `adapters/codex/README.md`: Figma heading, `provider_refusals` fallback and retry wording corrected. `langfuse-scores.py` is unchanged.
- `mxc-sandbox` README, `mxc-run`, recipes and `mxc-troubleshooting`: removed the unsupported "later" ordering and hook exit 66 claim, and qualified system-drive enumeration. The troubleshooting symptom row still quotes `exit=66`, since no artifact confirms or refutes it for hooks.
- This packet: `findings.md` marks the two worktree-only corrections, and `README.md` and `kanban.md` state 459 inventory paths.

- `mcp/server.py:276`, `mcp/wire_baseline.json:335` and `geeky.manifest.json:59`: the `check-dod` wording now places the gate in the Done step, on the owner's ruling. Regenerate the baseline with `uv run --frozen --with "mcp==1.29.0" python wire_baseline.py --out wire_baseline.json` from `mcp/`; the unpinned command picks up an untracked local `uv.lock` and adds an unrelated line.

`framework-agnostic-quality-gates.md:125` is left as it describes proposed gates. They were committed as one group because each commit gives later runs a new `plugin_sha`, which D60 treats as a different contestant.
