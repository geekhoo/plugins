"""Reproduce source-reviewed C1 parity scores using the existing C0 evaluator.

Inputs are an explicitly pinned local campaign and its retained Langfuse
observations, quality scores, review decisions and workspaces. No model calls,
telemetry uploads, score publication, or task validation commands are performed.
The result is deterministic for the same verified inputs; human judgments and
trace completeness remain separately disclosed rather than inferred.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
SCHEMA = 'geeky-eval.c1-normalized-campaign/1'
STAGES = ('spec-research', 'geeky-plan', 'plan-review', 'geeky-implement', 'impl-review')
ENGINE_PATHS = (HERE / 'c1-normalized-score.py', HERE / 'parity-eval.py', HERE / 'evaluation_scope.py', HERE / 'codex-trace.py',
                HERE.parent / 'telemetry/langfuse-coverage.py',
                HERE.parents[1] / 'scripts/check-commit.py', HERE.parents[1] / 'scripts/check-dod.py',
                HERE.parents[1] / 'scripts/validate-kanban.py', HERE.parents[1] / 'scripts/validate-planning-folder.py',
                HERE.parents[1] / 'scripts/validate-task-schema.py')


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def file_input(item):
    path = Path(item['path'])
    if not path.is_file() or sha256(path) != item['sha256']:
        raise ValueError(f"Missing or changed source: {path}")
    return path


def json_input(item):
    return json.loads(file_input(item).read_text(encoding='utf-8-sig'))


def git(workspace, *args):
    # A contestant workspace can contain local Git configuration. Avoid
    # executing a configured fsmonitor or hook while inspecting its history.
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith('GIT_')}
    env.update({'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull,
                'GIT_CONFIG_SYSTEM': os.devnull, 'GIT_OPTIONAL_LOCKS': '0',
                'GIT_TERMINAL_PROMPT': '0', 'GIT_PAGER': 'cat'})
    result = subprocess.run(['git', '-c', 'core.fsmonitor=false', '-c', f'core.hooksPath={os.devnull}',
                             '-C', str(workspace), *args], capture_output=True, env=env,
                            text=True, encoding='utf-8')
    if result.returncode:
        raise ValueError(f'Git inspection failed: {args[0]}')
    return result.stdout


def workspace_state(workspace):
    workspace = Path(workspace)
    heartbeat = workspace / 'docs/spec-001-feature/.heartbeat'
    status = git(workspace, 'status', '--porcelain=v1', '--untracked-files=all')
    allowed = {'?? docs/spec-001-feature/.heartbeat'}
    if any(line not in allowed for line in status.splitlines()):
        raise ValueError('Workspace has unbound changes or untracked files')
    reflog = git(workspace, 'reflog', '--date=iso-strict', '--format=%H%x1f%gd%x1f%gs')
    return {'head': git(workspace, 'rev-parse', 'HEAD').strip(),
            'status_sha256': hashlib.sha256(status.encode('utf-8')).hexdigest(),
            'reflog_sha256': hashlib.sha256(reflog.encode('utf-8')).hexdigest(),
            'heartbeat_sha256': sha256(heartbeat) if heartbeat.is_file() else None}


def module_from(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_manual(manual):
    if not isinstance(manual, dict):
        raise ValueError('Manual evidence must be an object')
    for key, value in manual.items():
        if (not isinstance(key, str) or not isinstance(value, dict) or
                type(value.get('pass')) is not bool or not str(value.get('note', '')).strip()):
            raise ValueError(f'Invalid or unsupported manual judgment: {key}')
    required = {'hg.false_completion_claim', 'a.no_orchestrator_code_edits'}
    if not required.issubset(manual):
        raise ValueError('False-completion and generic C1 code-edit checks require explicit reviewed evidence')


def verify_engine(campaign):
    if campaign.get('schema') != SCHEMA:
        raise ValueError('Unsupported C1 campaign schema')
    supplied = {str(file_input(item).resolve()).casefold() for item in campaign.get('engine_sources', [])}
    required = {str(path.resolve()).casefold() for path in ENGINE_PATHS}
    if not required.issubset(supplied):
        raise ValueError('Campaign does not pin every evaluator and gate source')


def apply_stage_review(evaluation, mode, process, parity):
    kind = mode['kind']
    if kind == 'existing':
        pass
    elif kind == 'specification-commit':
        if evaluation.bounds['spec-research'][1] is not None or evaluation.bounds['geeky-plan'][0] is not None:
            raise ValueError('Unexpected automatic specification boundary')
        matches = [c for c in evaluation.moves if any(f.endswith('/feature-specification.md') for f in c['files'])]
        if not matches or matches[0]['sha'] != mode['commit']:
            raise ValueError('Specification commit does not match the pinned reflog')
        start, boundary, end = evaluation.bounds['spec-research'][0], matches[0]['time'], evaluation.bounds['geeky-plan'][1]
        if not (start and boundary and end and start < boundary < end):
            raise ValueError('Specification boundary is not ordered')
        evaluation.bounds['spec-research'] = (start, boundary)
        evaluation.bounds['geeky-plan'] = (boundary, end)
    elif kind == 'reviewed-process':
        if not process:
            raise ValueError('Reviewed stage intervals require validated native process evidence')
        intervals = [x for x in process.get('stage_intervals', []) if x.get('scope_call_id') is None]
        if len(intervals) != len(STAGES) or {x['stage'] for x in intervals} != set(STAGES):
            raise ValueError('Reviewed global stage intervals are incomplete or duplicated')
        for interval in intervals:
            start = parity.utc_time(interval['start']['timestamp'])
            end = parity.utc_time(interval['end']['timestamp'])
            if start >= end:
                raise ValueError('Reviewed stage interval is empty or reversed')
            evaluation.bounds[interval['stage']] = (start, '9999' if interval['stage'] == 'impl-review' else end)
    else:
        raise ValueError('Unknown stage-evidence mode')
    starts = [evaluation.bounds[s][0] for s in STAGES]
    if not all(starts) or starts != sorted(starts):
        raise ValueError('Stage boundaries are incomplete or out of order')
    for stage in STAGES[:-1]:
        lo, hi = evaluation.bounds[stage]
        if not hi or lo >= hi:
            raise ValueError('Stage has no measurable interval: ' + stage)
    for earlier, later in zip(STAGES, STAGES[1:]):
        if evaluation.bounds[earlier][1] > evaluation.bounds[later][0]:
            raise ValueError('Stage intervals overlap: ' + earlier + ' / ' + later)


def evaluate_campaign(campaign, parity, trace_module):
    verify_engine(campaign)
    results, seen = [], set()
    for entry in campaign.get('runs', []):
        run_id = entry['id']
        if not run_id or run_id in seen:
            raise ValueError('Missing or duplicate run identity')
        seen.add(run_id)
        inputs = entry['inputs']
        for extra in entry.get('supporting_sources', []):
            file_input(extra)
        run_path = file_input(inputs['run'])
        run = json.loads(run_path.read_text(encoding='utf-8-sig'))
        if run.get('case') != 'c1-csvledger':
            raise ValueError('This scoring campaign requires C1 csvledger')
        run_session = (run.get('telemetry') or {}).get('session_id') or run.get('session_id')
        if run_session != entry['langfuse_session_id']:
            raise ValueError('Langfuse session is not bound to the run record')
        if run.get('plugin_sha') != entry['plugin_sha'] or run.get('prompt_sha256') != entry['prompt_sha256']:
            raise ValueError('Run configuration does not match campaign pins')
        if str(Path(run['workspace']).resolve()).casefold() != str(Path(entry['workspace']).resolve()).casefold():
            raise ValueError('Run workspace differs from campaign pin')
        if workspace_state(entry['workspace']) != entry['workspace_state']:
            raise ValueError('Workspace, reflog or heartbeat changed since campaign freeze')
        observations = json_input(inputs['observations'])
        if not isinstance(observations, list) or not observations:
            raise ValueError('Missing normalized Langfuse observations')
        ids = [x.get('id') for x in observations]
        if not all(ids) or len(ids) != len(set(ids)):
            raise ValueError('Ambiguous Langfuse observation identities')
        sessions = {x.get('sessionId') for x in observations}
        if sessions != {entry['langfuse_session_id']}:
            raise ValueError('Observation session differs from the campaign pin')
        quality = json_input(inputs['quality_score'])
        if (quality.get('case') != 'c1-csvledger' or quality.get('plugin_sha') != run.get('plugin_sha') or
                quality.get('run') != Path(entry['native_run_dir']).name or
                quality.get('harness') != run.get('harness') or quality.get('model') != run.get('model')):
            raise ValueError('Quality score is not bound to the candidate')
        if (quality.get('process_completeness', {}).get('complete') is not True or
                not isinstance(quality.get('needs_judge'), list) or quality['needs_judge']):
            raise ValueError('Quality input lacks strict process evidence or judgments')
        if not 0 <= quality['dimensions']['quality']['capped'] <= 100:
            raise ValueError('Quality component is outside 0–100')
        manual = json_input(inputs['manual'])
        validate_manual(manual)
        scope_path = file_input(inputs['scope'])
        scope = parity.load_scope(scope_path, [run_path, file_input(inputs['observations']),
                                               file_input(inputs['quality_score']), file_input(inputs['manual'])])
        if scope['missing_sources']:
            raise ValueError('Evaluation scope has missing source evidence')
        process = None
        if 'process_evidence' in inputs:
            native_dir = Path(entry['native_run_dir'])
            reviewed_path = file_input(inputs['process_evidence'])
            trace = trace_module.load(native_dir, reviewed_path)
            if not trace.get('trace_complete') or not trace.get('process_evidence'):
                raise ValueError(f"Native process evidence failed validation: {trace.get('trace_errors')}")
            process = trace['process_evidence']
        evaluation = parity.Evaluation(run_path.parent, observations, quality, manual, scope)
        apply_stage_review(evaluation, entry['stage_evidence'], process, parity)
        evaluated = evaluation.evaluate()
        if evaluated.get('needs_judge'):
            raise ValueError('Required scoring judgments are missing: ' + ', '.join(evaluated['needs_judge']))
        eligible = {x['id'] for x in evaluated['checks']} | {'hg.false_completion_claim'}
        if set(manual) - eligible:
            raise ValueError('Manual evidence contains an unused or unrecognized check')
        expected = (0.35 * evaluated['quality'] + 0.35 * evaluated['adherence'] + 0.20 * evaluated['consistency']) / 0.90
        if not math.isfinite(expected) or abs(evaluated['composite'] - round(expected, 2)) > 0.01:
            raise ValueError('Composite does not reproduce the C0 parity formula')
        after = workspace_state(entry['workspace'])
        if after != entry['workspace_state']:
            raise ValueError('Workspace changed during evaluation')
        # Post-run replay latencies, cost and aggregate populations are not
        # automatically comparable; retain only the source-recorded wall time.
        evaluated['efficiency'] = {'wall_time_s': run.get('wall_time_s'), 'tokens_total': None,
                                   'latency_median_ms': None, 'commits': None, 'interventions': run.get('interventions'),
                                   'calls': None, 'backend': None, 'cost': None}
        results.append({'id': run_id, 'langfuse_session_id': entry['langfuse_session_id'],
                        'plugin_sha': run['plugin_sha'], 'prompt_sha256': run['prompt_sha256'],
                        'harness': run['harness'], 'model': run['model'],
                        'provenance': entry['provenance'], 'review_mode': 'operator-reviewed',
                        'trace_delivery_complete': 'unverified', 'score': evaluated})
    if not results:
        raise ValueError('Campaign has no runs')
    return {'schema': 'geeky-eval.c1-normalized-score/1', 'case': 'c1-csvledger',
            'formula': '(0.35 * Quality + 0.35 * Adherence + 0.20 * Consistency) / 0.90',
            'task_tier_included': False, 'scoring_mode': 'source-reviewed; deterministic for frozen inputs',
            'limitations': ['Judgments and source corrections are reviewed inputs, not automatic ground truth.',
                            'Complete Langfuse ingestion and controlled model equivalence are not established.',
                            'The existing parity code-edit detector is wordstat/tests-specific; source-reviewed QACT evidence is used for C1.'],
            'runs': results}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args(argv)
    if args.out.exists():
        raise ValueError('Output exists; refusing overwrite')
    campaign = json.loads(args.campaign.read_text(encoding='utf-8-sig'))
    verify_engine(campaign)
    parity = module_from(HERE / 'parity-eval.py', 'c1_existing_parity')
    parity.git = git
    trace = module_from(HERE / 'codex-trace.py', 'c1_existing_codex_trace')
    result = evaluate_campaign(campaign, parity, trace)
    result['campaign_sha256'] = sha256(args.campaign)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x', encoding='utf-8', newline='\n') as out:
        json.dump(result, out, ensure_ascii=False, indent=2, sort_keys=True)
        out.write('\n')
    print(json.dumps({'runs': [{'id': r['id'], 'score': r['score']['composite']} for r in result['runs']],
                      'campaign_sha256': result['campaign_sha256']}))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
        print('c1-normalized-score: ' + str(exc), file=sys.stderr)
        sys.exit(1)
