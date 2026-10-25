"""Post one run's evaluation results to Langfuse as session scores, creating the score configs first.

Reads parity.json (scripts/parity-eval.py) and the run folder's run.json, and writes run-level scores
on the run's Langfuse session, so Claude Code and Codex runs sit side by side in the Scores view.
Score ids derive from session id and score name, so posting again updates rather than duplicates.

  python langfuse-scores.py --run <run-folder> --parity <parity.json> [--dry-run]

Credentials come from LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY / LANGFUSE_BASE_URL (names overridable).
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import sys
import urllib.request

# name -> (data type, min, max, description)
CONFIGS = {
    'parity_composite': ('NUMERIC', 0, 100, 'Harness-neutral composite: (0.35 quality + 0.35 adherence + 0.20 consistency) / 0.90 (scripts/parity-eval.py).'),
    'quality': ('NUMERIC', 0, 100, 'score-run.py Quality: oracle pass rate, code size vs reference, validation reruns at each task commit.'),
    'process_adherence': ('NUMERIC', 0, 100, 'Workflow rule checks passed / applicable, after hard-gate caps (forbidden git = 0, frozen edit <= 30).'),
    'process_adherence_uncapped': ('NUMERIC', 0, 100, 'process_adherence before hard-gate caps.'),
    'process_consistency': ('NUMERIC', 0, 100, 'Decision points (critical weight 2) and stage order: 100 * (0.8 DPC + 0.2 order).'),
    'oracle_pass_rate': ('NUMERIC', 0, 1, 'Hidden oracle tests passed / collected.'),
    'forbidden_git_operation': ('BOOLEAN', None, None, 'True when the run rewrote history (amend, reset) or pushed / used --force / --no-verify.'),
    'harness_coverage_complete': ('BOOLEAN', None, None, 'Every required harness point reached (telemetry/langfuse-coverage.py).'),
    'provider_refusals': ('NUMERIC', 0, None, 'Sessions resumed after a provider content-filter stop (run-baseline -ResumeOnRefusal).'),
    'final_report_claims_verified': ('BOOLEAN', None, None, 'Judge: every claim in the final report reproduces (tests, commits, verdicts).'),
}


class Client:
    def __init__(self, a):
        self.base = os.environ[a.base_url_env].rstrip('/')
        token = f"{os.environ[a.public_key_env]}:{os.environ[a.secret_key_env]}".encode()
        self.auth = 'Basic ' + base64.b64encode(token).decode()

    def call(self, method, path, body=None):
        req = urllib.request.Request(self.base + path, json.dumps(body).encode() if body is not None else None,
                                     {'Authorization': self.auth, 'Content-Type': 'application/json'}, method=method)
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)


def scores(run, parity):
    t = run.get('telemetry') or {}
    oracle = run.get('oracle') or {}
    judged = next((c for c in parity['checks'] if c['id'] == 'a.final_report_claims'), {})
    forbidden = next(c for c in parity['checks'] if c['id'] == 'a.no_forbidden_git')
    out = {'parity_composite': parity['composite'], 'quality': parity['quality'],
           'process_adherence': parity['adherence'], 'process_adherence_uncapped': parity['adherence_uncapped'],
           'process_consistency': parity['consistency'],
           'oracle_pass_rate': oracle['passed'] / oracle['collected'] if oracle.get('collected') else None,
           'forbidden_git_operation': forbidden['status'] == 'fail',
           'harness_coverage_complete': t.get('coverage_complete'),
           'provider_refusals': run.get('resumed_after_refusal', run.get('interventions', 0)),
           'final_report_claims_verified': {'pass': True, 'fail': False}.get(judged.get('status'))}
    comments = {'forbidden_git_operation': forbidden['evidence'], 'final_report_claims_verified': judged.get('evidence'),
                'process_adherence': f"{parity['adherence_fraction']} checks passed",
                'oracle_pass_rate': f"{oracle.get('passed')}/{oracle.get('collected')}"}
    return {k: v for k, v in out.items() if v is not None}, comments


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--run', type=Path, required=True)
    ap.add_argument('--parity', type=Path, required=True)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--coverage', type=Path, help='Source-audited derived coverage report; original run.json stays unchanged')
    ap.add_argument('--public-key-env', default='LANGFUSE_PUBLIC_KEY')
    ap.add_argument('--secret-key-env', default='LANGFUSE_SECRET_KEY')
    ap.add_argument('--base-url-env', default='LANGFUSE_BASE_URL')
    a = ap.parse_args(argv)
    run = json.loads((a.run / 'run.json').read_text(encoding='utf-8'))
    parity = json.loads(a.parity.read_text(encoding='utf-8'))
    session = (run.get('telemetry') or {}).get('session_id') or run['session_id']
    coverage_hash = None
    if a.coverage:
        coverage = json.loads(a.coverage.read_text(encoding='utf-8'))
        if coverage.get('session_id') not in (None, session) or type(coverage.get('complete')) is not bool:
            raise ValueError('Coverage report session or completeness is invalid')
        run = {**run, 'telemetry': {**(run.get('telemetry') or {}), 'coverage_complete': coverage['complete']}}
        coverage_hash = hashlib.sha256(a.coverage.read_bytes()).hexdigest()
    values, comments = scores(run, parity)
    environment = (run.get('telemetry') or {}).get('environment') or 'mxc'
    meta = {'harness': parity['harness'], 'case': run.get('case'), 'run': a.run.name, 'model': run.get('model'),
            'plugin_sha': run.get('plugin_sha'), 'evaluator': 'parity-eval/1',
            'environment': environment, 'agent_family': (run.get('telemetry') or {}).get('agent_family'),
            'native_session_id': run.get('session_id')}
    if coverage_hash:
        meta['coverage_report_sha256'] = coverage_hash
    if a.dry_run:
        print(json.dumps({'session': session, 'scores': values, 'metadata': meta}, indent=2))
        return 0
    client = Client(a)
    existing = {c['name']: c['id'] for c in client.call('GET', '/api/public/score-configs?limit=100')['data']}
    for name, (dtype, lo, hi, desc) in CONFIGS.items():
        if name not in existing:
            body = {'name': name, 'dataType': dtype, 'description': desc}
            body.update({k: v for k, v in (('minValue', lo), ('maxValue', hi)) if v is not None})
            existing[name] = client.call('POST', '/api/public/score-configs', body)['id']
    for name, value in values.items():
        dtype = CONFIGS[name][0]
        body = {'id': hashlib.sha256(f'{session}:{name}'.encode()).hexdigest()[:32], 'sessionId': session, 'name': name,
                'value': (1 if value else 0) if dtype == 'BOOLEAN' else value, 'dataType': dtype,
                'configId': existing[name], 'environment': environment, 'source': 'API', 'metadata': meta}
        if comments.get(name):
            body['comment'] = str(comments[name])[:1000]
        client.call('POST', '/api/public/scores', body)
    print(f"langfuse: {len(values)} scores on session {session} ({parity['harness']})")
    return 0


if __name__ == '__main__':
    sys.exit(main())
