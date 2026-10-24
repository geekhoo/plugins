"""Reproduce six committed Claude C1 scores using isolated, retained fixtures.

No model or judge is invoked. Existing manual verdicts supply judgement checks.
Default: test current analyzer/scorer. --committed-tools tests their HEAD versions.
All scorer writes, bundle clones, and task validation reruns use scratch storage.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
PLUGIN = REPO / 'geeky-orchestration'
BASE = 'geeky-orchestration/evals/baselines/c1-csvledger'
EXPECTED = {
    '20261020T114232Z': 77.2,
    '20261020T155628Z': 77.0,
    '20261022T065938Z': 86.7,
    '20261022T125647Z': 97.9,
    '20261023T062603Z': 93.8,
    '20261023T104412Z': 98.3,
}
TOOL_PATHS = [
    'geeky-orchestration/evals/scripts/analyze-run.py',
    'geeky-orchestration/evals/scripts/score-run.py',
]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command, *, cwd=None, env=None):
    result = subprocess.run(command, cwd=cwd, env=env, capture_output=True,
                            text=True, encoding='utf-8', errors='replace')
    if result.returncode:
        raise RuntimeError(f'Command failed ({result.returncode}): {command!r}\n'
                           f'{result.stdout}\n{result.stderr}')
    return result


def dimensions(score):
    d = score['dimensions']
    return {'quality': d['quality']['capped'], 'adherence': d['adherence']['capped'],
            'consistency': d['consistency']['score'], 'task_tier': d['task_tier']['score'],
            'composite': score['composite']}


def verify_claude_scope(path):
    """Recheck retained proof when only the lazily unused Codex helper changed."""
    report = json.loads(path.read_text(encoding='utf-8'))
    original_report_hash = sha256(path)
    rows = report.get('runs', [])
    exact = (len(rows) == len(EXPECTED) and {r['run'] for r in rows} == set(EXPECTED)
             and all(r['passed'] and round(r['actual']['composite'], 1) == EXPECTED[r['run']]
                     and all(abs(r['actual'][k] - r['expected'][k]) < 1e-9
                             for k in r['expected']) for r in rows))
    tool_hashes = report['tool_sha256']
    tools_unchanged = all(sha256(REPO / p) == tool_hashes[p] for p in TOOL_PATHS)
    fixtures_unchanged = all(sha256(REPO / p) == digest
                             for p, digest in report['original_worktree_sha256'].items())
    supplementary_unchanged = all(sha256(Path(row['source'])) == row['sha256']
        for row in report.get('supplementary_runtime_evidence', []))
    helper = 'geeky-orchestration/evals/scripts/codex-trace.py'
    report.update(source_report=str(path), source_report_sha256=original_report_hash,
        claude_reachable_tools_unchanged=tools_unchanged,
        original_fixtures_unchanged=fixtures_unchanged,
        supplementary_sources_unchanged=supplementary_unchanged,
        codex_helper_initial_sha256=tool_hashes.get(helper),
        codex_helper_final_sha256=sha256(REPO / helper),
        scope_note='Claude mode does not import the lazy Codex trace helper; analyzer/scorer hashes must match.',
        ok=exact and tools_unchanged and fixtures_unchanged and supplementary_unchanged
           and not report.get('error') and report['tools_source'] == 'working-tree')
    output = path.with_name('claude-scope-report.json')
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'ok': report['ok'], 'report': str(output)}))
    return 0 if report['ok'] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--committed-tools', action='store_true')
    parser.add_argument('--verify-claude-scope', type=Path,
                        help='Revalidate a retained current-tool report; preserves original report')
    args = parser.parse_args()
    if args.verify_claude_scope:
        return verify_claude_scope(args.verify_claude_scope)
    head = run(['git', '-C', str(REPO), 'rev-parse', 'HEAD']).stdout.strip()
    started = time.monotonic()
    scratch = Path(tempfile.mkdtemp(prefix='claude-c1-regression-')).resolve()
    snapshot = scratch / 'snapshot'
    snapshot.mkdir()
    report = {'ok': False, 'head': head, 'scratch': str(scratch),
              'tools_source': 'HEAD' if args.committed_tools else 'working-tree',
              'model_calls': 0, 'judge_calls': 0, 'runs': [], 'fixture_sha256': {},
              'supplementary_runtime_evidence': []}
    originals = {}
    current_tool_paths = TOOL_PATHS + [
        'geeky-orchestration/evals/scripts/codex-trace.py']
    current_tool_paths = [p for p in current_tool_paths if (REPO / p).is_file()]
    tool_hashes = {p: sha256(REPO / p) for p in current_tool_paths}
    paths = [f'{BASE}/{stamp}' for stamp in EXPECTED] + TOOL_PATHS + [
        'geeky-orchestration/scripts',
        'geeky-orchestration/evals/cases/c1-csvledger/case.json',
        'geeky-orchestration/evals/cases/c1-csvledger/spec.md',
    ]
    archive = subprocess.run(['git', '-C', str(REPO), 'archive', '--format=tar', head,
                              '--', *paths], capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:') as tar:
        for member in tar:
            if member.isdir():
                continue
            if not member.isfile():
                raise RuntimeError(f'Non-regular committed fixture: {member.name}')
            destination = (snapshot / member.name).resolve()
            if not destination.is_relative_to(snapshot):
                raise RuntimeError(f'Archive escapes scratch directory: {member.name}')
            data = tar.extractfile(member).read()
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            if member.name.startswith(BASE + '/'):
                digest = hashlib.sha256(data).hexdigest()
                originals[member.name] = sha256(REPO / member.name)
                # Checkout line endings may differ from Git blobs. Fixtures come
                # exclusively from Git; raw checkout hashes prove no original writes.
                report['fixture_sha256'][member.name] = digest
    report['original_worktree_sha256'] = originals
    tools_root = snapshot if args.committed_tools else REPO
    report['tool_sha256'] = ({p: sha256(tools_root / p) for p in TOOL_PATHS}
                            if args.committed_tools else tool_hashes)
    env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1',
           'PATH': str(Path(sys.executable).parent) + os.pathsep + os.environ.get('PATH', '')}
    try:
        for stamp, expected in EXPECTED.items():
            fixture = snapshot / BASE / stamp
            recorded = json.loads((fixture / 'score.json').read_text(encoding='utf-8-sig'))
            metadata = json.loads((fixture / 'run.json').read_text(encoding='utf-8-sig'))
            if metadata.get('harness') != 'claude-code':
                raise RuntimeError(f'Expected committed Claude fixture: {stamp}')
            if round(recorded['composite'], 1) != expected:
                raise RuntimeError(f'Committed score disagrees with fixed reference: {stamp}')
            workspace = scratch / 'workspaces' / stamp
            workspace.parent.mkdir(exist_ok=True)
            run(['git', 'clone', '--quiet', str(fixture / 'solution.bundle'), str(workspace)])
            heartbeat = Path(recorded['planning_folder']) / '.heartbeat'
            if not (workspace / heartbeat).exists():
                # Untracked final heartbeats are absent from solution.bundle.
                # Preserve actual historical bytes, never infer a status from scores.
                original_workspace = Path(metadata['workspace'])
                source = original_workspace / heartbeat
                if source.is_file():
                    clone_head = run(['git', '-C', str(workspace), 'rev-parse', 'HEAD']).stdout.strip()
                    source_head = run(['git', '-C', str(original_workspace), 'rev-parse', 'HEAD']).stdout.strip()
                    if clone_head != source_head:
                        raise RuntimeError(f'Historical workspace HEAD differs from bundle: {stamp}')
                    data = source.read_bytes()
                    evidence = scratch / 'supplementary' / stamp / '.heartbeat'
                    evidence.parent.mkdir(parents=True)
                    evidence.write_bytes(data)
                    (workspace / heartbeat).write_bytes(data)
                    digest = hashlib.sha256(data).hexdigest()
                    if sha256(source) != digest:
                        raise RuntimeError(f'Heartbeat changed while copying: {stamp}')
                    report['supplementary_runtime_evidence'].append({
                        'run': stamp, 'source': str(source), 'sha256': digest,
                        'historical_head': source_head, 'bundle_head': clone_head,
                        'saved_copy': str(evidence), 'git_pinned': False})
            commands = [
                [sys.executable, '-B', str(tools_root / TOOL_PATHS[0]), str(fixture), '--analysis-only'],
                [sys.executable, '-B', str(tools_root / TOOL_PATHS[1]), str(fixture),
                 '--manual', str(fixture / 'manual-verdicts.json'), '--workspace', str(workspace)],
            ]
            for label, command in zip(('analyzer', 'scorer'), commands):
                result = run(command, env=env)
                (fixture / f'regression-{label}-stdout.txt').write_text(result.stdout, encoding='utf-8')
                (fixture / f'regression-{label}-stderr.txt').write_text(result.stderr, encoding='utf-8')
            actual = json.loads((fixture / 'score.json').read_text(encoding='utf-8-sig'))
            reference, reproduced = dimensions(recorded), dimensions(actual)
            matches = all(abs(reproduced[k] - reference[k]) < 1e-9 for k in reference)
            matches = matches and round(reproduced['composite'], 1) == expected
            entry = {'run': stamp, 'expected_composite': expected, 'passed': matches,
                     'expected': reference, 'actual': reproduced, 'commands': commands}
            report['runs'].append(entry)
            print(json.dumps(entry), flush=True)
        report['original_fixtures_unchanged'] = all(
            sha256(REPO / p) == digest for p, digest in originals.items())
        report['current_tools_unchanged'] = all(
            sha256(REPO / p) == digest for p, digest in tool_hashes.items())
        report['supplementary_sources_unchanged'] = all(
            sha256(Path(row['source'])) == row['sha256']
            for row in report['supplementary_runtime_evidence'])
        report['ok'] = (all(row['passed'] for row in report['runs'])
                        and len(report['runs']) == len(EXPECTED)
                        and report['original_fixtures_unchanged']
                        and report['supplementary_sources_unchanged']
                        and (args.committed_tools or report['current_tools_unchanged']))
    except Exception as exc:
        report['error'] = str(exc)
    finally:
        report['elapsed_s'] = round(time.monotonic() - started, 2)
        output = scratch / 'regression-report.json'
        output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'ok': report['ok'], 'report': str(output)}), flush=True)
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
