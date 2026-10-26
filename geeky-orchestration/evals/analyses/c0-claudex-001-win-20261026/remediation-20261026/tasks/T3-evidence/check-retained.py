"""Read-only source-bound C0 checks. Never import/execute historical derivation or candidate code."""
import collections
import ast
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PLUGIN = HERE.parents[5]
ANALYSIS = PLUGIN / 'evals/analyses/c0-claudex-001-win-20261026'
LOCAL = Path('C:/repos/.eval-tools/c0-claudex-001/evaluation')
sys.path.insert(0, str(PLUGIN / 'evals/scripts'))
from evaluation_scope import bind_run, load_scope, scoped_efficiency


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def utc(value):
    return dt.datetime.fromisoformat(value.replace('Z', '+00:00'))


manifest_path = ANALYSIS / 'claude-code/closeout-20261026/evaluation-inputs.json'
comparison_path = ANALYSIS / 'comparison-metrics.json'
assert sha(manifest_path) == 'a20b1e8d8099a7d7890b29f3b0b16ba289de7c4f99b4cf09f443929085cd8685'
assert sha(comparison_path) == 'd01e02ad310dfbd96903f9c22b1aa763c5edfb99570cdfa84a2ad41517f215a4'
manifest, comparison = read(manifest_path), read(comparison_path)
original_evaluators = {}
for source in comparison['evaluator_source_hashes']:
    historical = subprocess.run(['git', 'show', 'HEAD:' + source['path'].replace('\\', '/')],
                                cwd=PLUGIN.parent, capture_output=True, check=True).stdout
    candidates = (historical, historical.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n'))
    assert source['sha256'] in {hashlib.sha256(value).hexdigest() for value in candidates}
    original_evaluators[source['path']] = source['sha256']


def formula_tree(text):
    tree = ast.parse(text)
    evaluation = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'Evaluation')
    evaluate = next(node for node in evaluation.body if isinstance(node, ast.FunctionDef) and node.name == 'evaluate')
    start = next(i for i, node in enumerate(evaluate.body) if isinstance(node, ast.FunctionDef) and node.name == 'ratio')
    end = next(i for i, node in enumerate(evaluate.body) if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'composite' for t in node.targets))
    return ast.dump(ast.Module(body=evaluate.body[start:end + 1], type_ignores=[]), include_attributes=False)


old_parity = subprocess.run(['git', 'show', 'HEAD:geeky-orchestration/evals/scripts/parity-eval.py'],
                            cwd=PLUGIN.parent, capture_output=True, check=True).stdout.decode('utf-8')
assert formula_tree(old_parity) == formula_tree((PLUGIN / 'evals/scripts/parity-eval.py').read_text(encoding='utf-8'))
derived = PLUGIN.parent / 'outputs/remediation-20261026/T3-derived'
derived.mkdir(exist_ok=True)
watched = [p for p in ANALYSIS.rglob('*') if p.is_file() and 'remediation-20261026' not in p.parts]
watched += [Path(source['path']) for source in manifest['native_sources']]
watched += [Path(manifest['scoring_input']) / 'session.jsonl', LOCAL / 'closeout/observations-cumulative.json',
            LOCAL / 'closeout/observations-native.json', LOCAL / 'router-fixed/observations.json',
            LOCAL / 'closeout/derive_inputs.py']
before = {str(path): sha(path) for path in watched}
assert sha(LOCAL / 'closeout/derive_inputs.py') == 'a3b64a78481c456fc4586b03afea58c8b3c5048b928f7662e08175587a863f35'
rows, seen, excluded, assignments = [], {}, 0, []
cutoff = utc(manifest['new_event_cutoff'])
raw_current = None
for index, source in enumerate(manifest['native_sources']):
    path = Path(source['path'])
    assert sha(path) == source['sha256']
    owned = []
    native = []
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        try:
            native.append((line, json.loads(line)))
        except ValueError:
            pass # Same explicit malformed-row exclusion as the frozen source derivation.
    if index == 1:
        raw_current = [row for _, row in native]
    for line, row in native:
        if index == 1 and (not row.get('timestamp') or utc(row['timestamp']) < cutoff):
            excluded += 1
            continue
        key = row.get('uuid') or hashlib.sha256(line.encode()).hexdigest()
        if key in seen:
            assert seen[key].get('message') == row.get('message')
            excluded += 1
            continue
        seen[key] = row
        rows.append(line)
        owned.append(key)
    assignments.append({'source_id': f'native-{index}', 'logical_ids': owned})
# Original Windows write_text created CRLF. Preserve that byte representation.
logical = ('\r\n'.join(rows) + '\r\n').encode('utf-8')
(derived / 'session.jsonl').write_bytes(logical)
assert excluded == manifest['forked_historical_rows_excluded'] == 438
assert len(rows) == manifest['rows'] == 1612
assert sha(derived / 'session.jsonl') == manifest['logical_session_sha256'] == sha(Path(manifest['scoring_input']) / 'session.jsonl')
combined, tools, counts, observation_assignments = [], set(), {}, []
for label, path in (('continuation', LOCAL / 'closeout/observations-native.json'),
                    ('previous', LOCAL / 'router-fixed/observations.json')):
    added = []
    observations = read(path)
    assert len(observations) == (1095 if label == 'continuation' else 892)
    for row in observations:
        metadata = row.get('metadata') or {}
        metadata = json.loads(metadata) if isinstance(metadata, str) else metadata
        if row['type'] == 'TOOL':
            key = metadata.get('tool_id')
            if key and key in tools:
                continue
            if key:
                tools.add(key)
        row = {**row, 'id': label + ':' + row['id'],
               'parentObservationId': label + ':' + row['parentObservationId'] if row.get('parentObservationId') else None}
        combined.append(row)
        added.append(row['id'])
    counts[label] = len(added)
    observation_assignments.append({'source_id': label + '-observations', 'logical_ids': ['observation:' + key for key in added]})
(derived / 'observations.json').write_text(json.dumps(combined), encoding='utf-8', newline='')
assert counts == {'continuation': 807, 'previous': 678} and len(combined) == 1485
assert combined == read(LOCAL / 'closeout/observations-cumulative.json')
assert sha(derived / 'observations.json') == '2755c9f7560376c190a1764119cc9681227f7d6e01995d676fa5f91e632243b3'
fresh, historical = set(), set()
for row in raw_current:
    if row.get('type') == 'assistant' and row.get('message', {}).get('id'):
        (fresh if utc(row['timestamp']) >= cutoff else historical).add(row['message']['id'])
assert (len(fresh), len(historical), len(fresh & historical)) == (42, 48, 0)
retained_scores = {}
for key, folder, expected in (('codex_initial', 'codex', 97.46), ('claude_initial', 'claude-code/router-fixed', 90.33),
                              ('claude_cumulative', 'claude-code/closeout-20261026', 98.33)):
    parity = read(ANALYSIS / folder / 'parity.json')
    record = comparison['runs'][key]
    assert parity == record['parity'] and parity['composite'] == expected
    a = [c for c in parity['checks'] if c['dimension'] == 'adherence' and c['status'] in ('pass', 'fail')]
    c = [c for c in parity['checks'] if c['dimension'] == 'consistency' and c['status'] in ('pass', 'fail')]
    critical = {'dp02', 'dp05', 'dp09', 'dp10', 'dp11'}
    adherence = 100 * sum(x['status'] == 'pass' for x in a) / len(a)
    fraction = f"{sum(x['status'] == 'pass' for x in a)}/{len(a)}"
    assert fraction == parity['adherence_fraction']
    dpc = sum((2 if x['id'] in critical else 1) for x in c if x['status'] == 'pass') / sum(2 if x['id'] in critical else 1 for x in c)
    consistency = 100 * (0.8 * dpc + 0.2 * parity['order'])
    quality = record['quality_breakdown']['capped']
    calculated = (0.35 * quality + 0.35 * adherence + 0.20 * consistency) / 0.90
    assert round(calculated, 2) == expected
    retained_scores[key] = {'composite': expected, 'adherence_fraction': fraction, 'quality': quality,
                            'weighted_consistency_denominator': sum(2 if x['id'] in critical else 1 for x in c)}
t1 = comparison['runs']['codex_initial']['task_commit_validation']['T1']
assert [row['exit'] for row in t1['results']] == [4, 0]
assert t1['results'][0]['command'] == 'python -m pytest tests/test_core.py -q'
assert comparison['unknowns']['cumulative_claude_tokens'].startswith('N/A')
assert comparison['unknowns']['backend_identity'].startswith('N/A')
assert comparison['unknowns']['actual_billed_cost'].startswith('N/A')
# Exercise the new sidecar against the same reviewed, retained sources, in isolation.
run_path = Path(manifest['raw_capture']) / 'run.json'
run = read(run_path)
sources = [{'id': f'native-{i}', **source, 'ancestry': []} for i, source in enumerate(manifest['native_sources'])]
for key, path, ancestry in [('review', manifest_path, []), ('run', run_path, []),
                             ('continuation-observations', LOCAL / 'closeout/observations-native.json', ['native-1']),
                             ('previous-observations', LOCAL / 'router-fixed/observations.json', ['native-0']),
                             ('logical', derived / 'session.jsonl', ['native-0', 'native-1']),
                             ('observations', derived / 'observations.json', ['continuation-observations', 'previous-observations'])]:
    sources.append({'id': key, 'path': str(path), 'sha256': sha(path), 'ancestry': ancestry})
scope = {'schema': 'geeky-eval.inputs/1', 'scope_id': 'c0-claude-cumulative-retained-review', 'kind': 'cumulative',
         'parent_scope_id': 'c0-claude-initial-retained',
         'configuration': {key: run[key] for key in ('prompt_sha256', 'plugin_sha')}, 'sources': sources,
         'segments': [{'segment_id': 'retained-closeout', 'authorization_reference': str(ANALYSIS / 'claude-code/closeout-20261026/report.md'),
                       'start': manifest['new_event_cutoff'], 'end': '2026-10-26T06:12:00Z'}],
         'ownership': {'method': 'source-reviewed', 'rule': 'Frozen C0 UUID/message review plus native tool_id precedence; source ancestry retained. Cutoff is not novelty proof.',
                       'cutoff': manifest['new_event_cutoff'], 'evidence_source': 'review',
                       'assignments': assignments + observation_assignments},
         'metric_default': {'scope_id': 'c0-claude-cumulative-retained-review', 'population': 'reviewed cumulative input',
                            'source_ids': ['logical', 'observations', 'run'], 'additive': False, 'complete': True},
         'metrics': {metric: {'scope_id': 'continuation', 'population': 'continuation native parent only; workers not normalized',
                              'complete': False} for metric in ('tokens', 'calls', 'latency_idle', 'backend', 'cost')}}
scope_path = derived / 'evaluation-inputs.json'
scope_path.write_text(json.dumps(scope, indent=2) + '\n', encoding='utf-8')
validated = load_scope(scope_path, [run_path, derived / 'session.jsonl', derived / 'observations.json'])
bind_run(validated, run)
efficiency = scoped_efficiency(comparison['runs']['claude_cumulative']['parity']['efficiency'], validated)
assert all(efficiency[key] is None for key in ('tokens_total', 'calls', 'latency_median_ms', 'backend', 'cost'))
assert efficiency['wall_time_s'] == 7180
after = {str(path): sha(path) for path in watched}
assert before == after
result = {'status': 'retained-invariants-verified', 'scope': 'historical cached evidence, no fresh candidate validation or oracle',
          'excluded_history_rows': excluded, 'logical_rows': len(rows), 'observations': len(combined), 'retained_by_source': counts,
          'parent_requests': {'fresh': 42, 'historical': 48, 'shared': 0, 'population': 'parent assistant message IDs only, not all agents'},
          'scores': retained_scores, 'codex_T1_selected_commit': t1, 'scoped_efficiency': efficiency,
          'unknowns': comparison['unknowns'], 'historical_source_hashes': before,
          'original_evaluator_source_hashes': original_evaluators, 'parity_formula_ast_unchanged': True,
          'full_scorer_replay': 'open: no retained validation-cache.json; candidate commands/oracles prohibited'}
result['isolated_derived_output'] = str(derived)
result['derived_hashes'] = {name: sha(derived / name) for name in ('session.jsonl', 'observations.json', 'evaluation-inputs.json')}
(HERE / 'retained-invariants.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: result[key] for key in ('status', 'excluded_history_rows', 'logical_rows', 'observations', 'retained_by_source', 'parent_requests', 'scores', 'full_scorer_replay')}, indent=2))
