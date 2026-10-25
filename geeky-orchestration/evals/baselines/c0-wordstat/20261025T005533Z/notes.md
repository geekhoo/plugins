# Baseline c0-wordstat 20261025T005533Z

Approach: canonical prompt, Claude Code isolated in MXC.
Interventions: none.
Oracle verdicts: (fill in for any failure)

# Claude C0 run 1 (ant-claude via LiteLLM, Linux MXC)

Timed out at the 2700 s case ceiling during geeky-implement: spec-research 00:55-01:03 (3 researchers),
PM review 01:13-01:18, plan review 01:23-01:29, architect 01:30-01:33, first geeky-coder 01:37-01:39.
Median model latency 4.5 s; subagents used 23-48 calls each. 3 commits, oracle 0/13.
No Langfuse data: the Stop hook only fires when the single -p turn ends, and it never ended (one
mid-run firing processed 0 turns). Started before the mxc environment and trace-name changes.
Not reference-eligible.
