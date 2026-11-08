"""Prepare two scoped C3 session metrics for run 20261108T150341Z-463d8062, without network operations."""
import hashlib, json, re
from pathlib import Path

here = Path(__file__).resolve().parent
run = Path(r'C:\Repos\c3-sol-mapfix-20261107\geeky-orchestration\evals\baselines\c3-minisql\20261108T150341Z-463d8062')
score_path = Path(r'C:\Users\gerald.khoo\geekhoo-plugins\geeky-orchestration\evals\analyses\c3-codex-sol-win-20261108\score.json')
oracle_path = run / 'oracle-output.txt'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


oracle = oracle_path.read_text(encoding='utf-8', errors='replace')
if len(re.findall(r'^182 passed, 1 skipped in ', oracle, re.M)) != 3 or re.search(r'^\d+ failed', oracle, re.M):
    raise ValueError('Unexpected oracle metric')
score = json.loads(score_path.read_text(encoding='utf-8'))
q = score['dimensions']['quality']
if q['P'] != 1.0 or q['D'] != 1.0 or score['scorer'] is None:
    raise ValueError('Unexpected quality evidence')
quality = round(q['score'], 2)

session = 'c3-minisql/codex/20261108T150341Z-463d8062'
scope = 'c3-codex-sol-source-reviewed-20261108-463d8062-v1'
evaluator = 'c3-factual/1'
meta = {'scope_id': scope, 'evaluator': evaluator, 'run_id': '20261108T150341Z-463d8062',
        'workspace_head': 'ef2fe4e9ef82026750d3d758f184c418fc2d5518',
        'oracle_output_sha256': sha(oracle_path), 'quality_evidence_sha256': sha(score_path),
        'plugin_sha': 'eed723042882737fe9789287051d62dd1265e1a4', 'telemetry': 'live 2026-11-08'}


def identifier(name):
    return hashlib.sha256(json.dumps([session, scope, evaluator, name], separators=(',', ':')).encode()).hexdigest()[:32]


defs = [('oracle_pass_rate', 1.0,
         'Independent oracle: 182/182 passed on each of three repetitions; 1 case-insensitive-filesystem test skipped. This measures oracle pass rate only.',
         'fe4ba7b1-73e6-4807-96bc-588fa7b2d25a'),
        ('c3_quality_qact_v1', quality,
         'Frozen score-run.py Quality component: oracle 1.0, size 300/1167 non-test LOC, 7/7 task validation commands pass at task commits (agent-py rerun). Not a composite; QACT and parity composites withheld because the Codex process parsers miss apply-patch board moves and the non-prescribed spec subject breaks parity stage bounds.',
         None)]
scores = []
for name, v, comment, config in defs:
    item = {'id': identifier(name), 'sessionId': session, 'name': name, 'value': v, 'dataType': 'NUMERIC',
            'environment': 'mxc-win', 'source': 'API', 'metadata': meta, 'comment': comment}
    if config:
        item['configId'] = config
    scores.append(item)
for item in scores:
    (here / (item['name'] + '.json')).write_text(json.dumps(item, indent=2) + '\n', encoding='utf-8')
(here / 'expected.json').write_text(json.dumps({'scope': scope, 'scores': scores}, indent=2) + '\n', encoding='utf-8')
print('Prepared', len(scores), 'scoped metrics; quality', quality, '; no network operation.')
