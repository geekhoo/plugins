# Baseline c1-csvledger 20261023T104412Z

Approach: canonical prompt, Claude Code isolated in MXC.
Interventions: none.
Oracle verdicts: (fill in for any failure)


Correction (2026-10-23): the runner flagged plugin_modified_during_run because Python wrote scripts/__pycache__/*.pyc into the read-write plugin export. Apart from __pycache__, the export matched the committed plugin at 8ea2ccc file for file (66 files, 0 differences). Set to false; the run is reference-eligible (8.13M tokens, under 12M). The runner now ignores __pycache__ and sets PYTHONDONTWRITEBYTECODE=1.
The main agent delegated geeky-implement to a geeky-orchestration:geeky-implement-orchestrator subagent. Its nested coders and reviewers are recorded only in subagents/ (copied from the MXC session folder).
