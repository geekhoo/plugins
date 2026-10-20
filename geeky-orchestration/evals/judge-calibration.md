# Judge Calibration — Judging the Judge

How a human or another agent checks the `/geeky-eval` LLM judge. You score a sample of runs yourself, without looking at the judge's scores, then compare the two. The judge counts as calibrated only if it passes. Repeat the check whenever the rubric, the judge model or the judge prompt changes.

## What you need

| Item | Location |
|---|---|
| Judge rubric: criteria, 0–100 anchors, and the evidence each criterion uses | `evals/rubric/judge-rubric.md` |
| Run evidence bundles | `evals/results/<YYYYMMDDTHHMMSSZ>-<case>-<contestant>/` |
| Case baseline: reference spec, contract, reference solution | `evals/cases/<case>/` |
| Workflow expectations | `evals/expectations/` |

A run bundle contains:

- `trace.jsonl`: the steps taken, as a normalized action trace.
- `diff.patch` and `artifacts/`: the output.
- `validations/`: the oracle and validation-block runs, with their results.
- `results.json`: all scores. Its `judge` key holds the judge's per-criterion scores and citations.

Score only the criteria the rubric marks **judge-scored**. Gates compute everything else, so you don't score it.

## Procedure

1. **Pick the sample.** Choose 6 runs:
   - at least one from each of C1, C2 and C3;
   - at least one from each harness;
   - at least one run with `failed_at` set;
   - at least one with a high composite score and one with a low composite score.

   List the run folder names in your sheet before you start scoring.
2. **Stay blind.** Do not open `results.json` until step 5. Read only `trace.jsonl`, `diff.patch`, `artifacts/`, `validations/` and the case baseline. If you are an agent, do not read any file named `results.json` or `scorecard.md`.
3. **Score each criterion.** Give each judge-scored criterion a value from 0 to 100, using the rubric's anchors. For each score, write one line of evidence: a file path with a line number, or a trace event ID. A score without evidence is invalid.
4. **Check defect claims.** For every defect you claim, give a reproduction or a file:line. You will compare these against the judge's defect list.
5. **Compare.** Now open `results.json`, take the `judge` scores and fill in the comparison columns.
6. **Decide.** Apply the [pass criteria](#pass-criteria) and record the verdict.

## Sheet

Save the sheet to `evals/results/calibration/<YYYYMMDDTHHMMSSZ>-<rater>.md` with one table:

| run | criterion | rater score | rater evidence | judge score | abs diff | within ±10 |
|---|---|---|---|---|---|---|

Below the table, add the defect comparison (judge defects confirmed / not confirmed / missed), the pass-criteria results, and the verdict.

## Pass criteria

The judge is **calibrated** only when all four hold:

1. At least **80%** of (run, criterion) pairs differ by **10 points or less**.
2. No criterion has a mean absolute difference above **15** across the sample.
3. At least **90%** of the judge's claimed defects are confirmed real, meaning the evidence reproduces them.
4. Every judge score cites evidence that exists at the location given.

If any criterion fails, the verdict is **not calibrated**. Name the failing criteria and the runs involved. Fix the rubric anchors or the judge prompt, then repeat on a new sample. While the judge is not calibrated, mark every judge-scored value in reports as provisional.

## Prompt for an agent rater

Paste this into a fresh session. Its working directory must be the geekhoo-plugins repo on the eval branch.

```
You are calibrating the /geeky-eval LLM judge. Follow geeky-orchestration/evals/judge-calibration.md exactly.
Read, in this order: evals/judge-calibration.md, evals/rubric/judge-rubric.md, then for each sampled run its evals/cases/<case>/ baseline and the run bundle files listed under "What you need".
Before scoring, verify with `git log -1` that you are on the commit you were given: <PIN SHA HERE>.
Sample: <LIST 6 RUN FOLDERS, or "choose per step 1">.
Rules:
- Do not open results.json or scorecard.md until step 5.
- Every score needs one line of file:line or trace-event evidence.
- Do not edit anything except your sheet at evals/results/calibration/<timestamp>-<agent-name>.md. Do not commit.
Done when: the sheet exists, every row is filled, the four pass criteria are evaluated with numbers, and the verdict is stated.
Budget: report at most 300 words besides the sheet.
```
