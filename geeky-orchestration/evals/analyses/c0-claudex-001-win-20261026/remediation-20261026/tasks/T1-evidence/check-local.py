"""Bounded local evidence; instruction/report decisions are walkthroughs, not code tests."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PLUGIN = HERE.parents[5]
REPO = PLUGIN.parent
PIN = '53fb54b5f30ab0397c1fc154e83a6af942797322'
BASELINE = '8fff98b0f087f148d4f416f512dc9988d61a57aa'

def git(*args):
    return subprocess.run(['git', *args], cwd=REPO, capture_output=True, check=True).stdout

def sha(data):
    return hashlib.sha256(data).hexdigest()

assert git('rev-parse', 'HEAD').decode().strip() == PIN
assert git('cat-file', '-t', BASELINE).strip() == b'commit'
prompt_path = 'geeky-orchestration/evals/prompts/end-to-end.md'
old = git('show', f'{PIN}:{prompt_path}')
assert git('show', f'{BASELINE}:{prompt_path}') == old
new = (REPO / prompt_path).read_bytes()
# Git stores LF; compare content with newline normalization and keep the raw copy too.
old_lines = old.replace(b'\r\n', b'\n').splitlines(keepends=True)
new_lines = new.replace(b'\r\n', b'\n').splitlines(keepends=True)
assert old_lines[:-1] == new_lines[:-1] and old_lines[-1] != new_lines[-1]
(HERE / 'historical-prompt.md').write_bytes(old)
assert json.loads((PLUGIN / 'evals/telemetry/langfuse-evaluators/final_report_complete.rule.json').read_text())['enabled'] is False

# Protect all tracked historical/case/scoring material, excluding mutable remediation state.
tracked = git('ls-files', '-z', 'geeky-orchestration').decode().split('\0')
protected = []
head_blobs = {}
gitlinks = {}
for entry in git('ls-tree', '-r', '-z', PIN, 'geeky-orchestration').split(b'\0'):
    if entry:
        metadata, name = entry.split(b'\t', 1)
        if metadata.split()[0] == b'160000':
            gitlinks[name.decode()] = metadata.split()[2].decode()
        else:
            head_blobs[name.decode()] = metadata.split()[2].decode()
frozen_packet = {'implementation-plan.md', 'references.md', 'tasks/T1-streamline-workflow.md',
                 'tasks/T2-bound-runner.md', 'tasks/T3-scope-and-readback.md'}
packet = HERE.parent.parent
for name in filter(None, tracked):
    if name in gitlinks:
        continue
    path = REPO / name
    rel = path.relative_to(PLUGIN).as_posix()
    historical = rel.startswith(('evals/analyses/', 'evals/baselines/', 'evals/cases/')) and not path.is_relative_to(packet)
    unchanged_code = rel.startswith(('evals/scripts/', 'evals/telemetry/')) or rel in {'test_quality_gates.py', 'test_score_run.py'}
    frozen = path.is_relative_to(packet) and path.relative_to(packet).as_posix() in frozen_packet
    if historical or unchanged_code or frozen:
        protected.append({'path': name, 'git_blob': head_blobs[name], 'file_sha256': sha(path.read_bytes())})
# Batch read-only object hashing applies the clean filter (e.g. CRLF); raw file SHA is distinct.
blob_check = subprocess.run(['git', 'hash-object', '--stdin-paths'], cwd=REPO,
                            input='\n'.join(row['path'] for row in protected) + '\n',
                            capture_output=True, text=True, check=True)
actual_blobs = blob_check.stdout.splitlines()
assert len(actual_blobs) == len(protected)
for row, actual_blob in zip(protected, actual_blobs):
    assert row['git_blob'] == actual_blob, row['path']
protected_manifest = HERE / 'protected-files.json'
if protected_manifest.exists():
    assert json.loads(protected_manifest.read_text()) == protected, 'Protected file bytes changed during validation'
protected_manifest.write_text(json.dumps(protected, indent=2) + '\n')

# Local plugin fingerprint deliberately labels working-file bytes separately from committed plugin_sha.
runtime = []
for name in filter(None, tracked):
    if name in gitlinks:
        continue
    rel = (REPO / name).relative_to(PLUGIN).as_posix()
    if not rel.startswith('evals/'):
        runtime.append({'path': rel, 'file_sha256': sha((REPO / name).read_bytes())})
fingerprint = sha(json.dumps(runtime, sort_keys=True, separators=(',', ':')).encode())
manifest = {'kind': 'local-tracked-runtime-file-sha256-manifest', 'base_plugin_commit': PIN,
            'working_tree_fingerprint_sha256': fingerprint, 'entries': runtime}
(HERE / 'plugin-fingerprint.json').write_text(json.dumps(manifest, indent=2) + '\n')

# Isolated synthetic commit-tree manifests: no repository commits or candidate execution.
# Reuse the actual H1 selector, then compare the selected delivery with tested file hashes.
spec = importlib.util.spec_from_file_location('t1_score_run', PLUGIN / 'evals/scripts/score-run.py')
sr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sr)
snapshots = HERE / 'snapshot-fixture'
early = snapshots / 'selected-delivery'
final = snapshots / 'later-final-head'
early.mkdir(parents=True, exist_ok=True)
final.mkdir(parents=True, exist_ok=True)
(early / 'core.py').write_text('VALUE = 1\n')
(final / 'core.py').write_text('VALUE = 1\n')
(final / 'test_core.py').write_text('from core import VALUE\n\ndef test_value():\n    assert VALUE == 1\n')
rows = [{'sha': 'a' * 40, 'ct': 200, 'tasks': ['T1']}, {'sha': 'f' * 40, 'ct': 500, 'tasks': ['T1']}]
selected, basis = sr.task_commit(rows, 'T1', done_ts=250, start_ts=150)
assert selected['sha'] == 'a' * 40
tested = {p.name: sha(p.read_bytes()) for p in final.iterdir() if p.is_file()}
delivered = {p.name: sha(p.read_bytes()) for p in early.iterdir() if p.is_file()}
missing = sorted(set(tested) - set(delivered))
assert missing == ['test_core.py']
assert any(delivered.get(path) != digest for path, digest in tested.items())
fixture_commands = []
for directory, expected_exit in ((early, 4), (final, 0)):
    command = [sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', 'test_core.py']
    result = subprocess.run(command, cwd=directory, capture_output=True, text=True,
                            env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    (HERE / f'{directory.name}-pytest.txt').write_text(result.stdout + result.stderr + f'\nEXIT_CODE={result.returncode}\n')
    assert result.returncode == expected_exit, result.stdout + result.stderr
    fixture_commands.append({'command': command, 'cwd': str(directory), 'exit_code': result.returncode})
snapshot_result = {'synthetic_ids_not_real_commits': True, 'rows': rows, 'selected': selected,
                   'basis': basis, 'tested_final_files': tested, 'selected_delivery_files': delivered,
                   'missing': missing, 'commands': fixture_commands,
                   'decision': 'REJECT selected snapshot; final-HEAD evidence is not applicable'}
(HERE / 'snapshot-result.json').write_text(json.dumps(snapshot_result, indent=2) + '\n')

# Preserve original source labels and emit the precise supported distinction.
erratum = PLUGIN / 'evals/analyses/c0-claudex-001-win-20261026/claude-code/closeout-20261026/review-metadata-erratum.json'
labels = json.loads(erratum.read_text())
for item in labels['files']:
    assert len(item['git_blob']) == 40 and len(item['sha256']) == 64
print(f'PASS: HEAD={PIN}; baseline={BASELINE} exists')
print('PASS: only canonical prompt final paragraph changed; historical prompt bytes saved unchanged')
print(f'PASS: {len(protected)} historical/case/scoring/frozen tracked files match pinned Git blobs; rule remains disabled')
print(f'LIMIT: {len(gitlinks)} tracked Git links excluded from raw file hashing; no traversal into nested repositories')
print(f'PASS: local tracked runtime fingerprint SHA-256={fingerprint}; committed plugin_sha remains {PIN}')
print(f'PASS: H1 synthetic selected {selected["sha"]}; missing={missing}; selected pytest exit=4; later pytest exit=0 (1 passed); reject selected snapshot')
print('PASS: original erratum preserved; Git blob object IDs (40 hex) and file SHA-256 (64 hex) remain distinct labels')
print('LIMIT: no LLM/judge/candidate execution; snapshot uses synthetic immutable file-set manifests, not real commits')
