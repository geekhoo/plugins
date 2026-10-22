# Baseline c1-csvledger 20261021T190006Z

Approach: canonical prompt, Claude Code isolated in MXC, plugin c9c8794.
Interventions: none.
Outcome: NOT reference-eligible. The main agent delegated geeky-implement to a background subagent and ended its turn; claude -p stopped the background work after its 10-minute wait ceiling (stderr), with T1-T3 of 10 done. Fixed for later runs by CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0 (D85).


Archived evidence: run.json, analysis.json, stderr.txt (the stop message), stream.jsonl (main-agent trace ending on the background hand-off), solution.bundle (7 commits, T1-T3). Dropped as noise: session.jsonl (duplicate trace) and oracle-output.txt (118 of 118 failed; nothing beyond T1-T3 existed).
