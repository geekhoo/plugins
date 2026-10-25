import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pe = module(HERE / 'parity-eval.py', 'parity_eval')
ls = module(HERE.parent / 'telemetry/langfuse-scores.py', 'langfuse_scores')


def obs(oid, name, inp, parent=None, t='2026-10-25T03:00:00Z', kind='TOOL'):
    return {'id': oid, 'type': kind, 'name': name, 'input': json.dumps(inp) if not isinstance(inp, str) else inp,
            'output': '', 'parentObservationId': parent, 'startTime': t}


def test_events_normalise_both_tracers():
    o = [obs('s1', 'Subagent: coder', '', kind='SPAN'),
         obs('a', 'Tool: Agent', {'subagent_type': 'geeky-orchestration:geeky-coder', 'prompt': 'Implement T1'}),
         obs('b', 'Tool: Write', {'file_path': '/ws/wordstat/cli.py', 'content': 'x'}, parent='s1'),
         obs('c', 'spawn_agent', {'agent_type': 'code-reviewer', 'message': 'Review phase 1'}),
         obs('d', 'exec_command', {'cmd': "cat > tests/test_cli.py <<'EOF'\nx\nEOF"}),
         obs('e', 'skill:plan-review', {'cmd': 'cat SKILL.md'})]
    ev = {e['name']: e for e in pe.events(o)}
    assert ev['Tool: Agent']['kind'] == 'spawn' and 'geeky-coder' in ev['Tool: Agent']['role']
    assert ev['spawn_agent']['role'] == 'code-reviewer'
    assert ev['Tool: Write']['thread'] == 'sub' and ev['Tool: Write']['paths'] == ['/ws/wordstat/cli.py']
    assert ev['exec_command']['thread'] == 'main' and 'tests/test_cli.py' in ev['exec_command']['paths']
    assert ev['skill:plan-review']['kind'] == 'skill'


def test_final_review_marker_matches_both_harnesses():
    assert pe.REVIEW_FINAL.search('{"task_name":"impl_cli_review","agent_type":"code-reviewer"}')
    assert pe.REVIEW_FINAL.search('{"description": "Impl review: CLI core"}')
    assert pe.REVIEW_FINAL.search("a CLI expert reviewing wordstat's implementation")
    assert not pe.REVIEW_FINAL.search('{"description": "Phase 1 review of T1"}')


def test_stage_time_comparison_normalizes_git_and_observation_offsets():
    assert pe.utc_time('2026-10-26T00:19:16+08:00') == pe.utc_time('2026-10-25T16:19:16Z')
    evaluation = pe.Evaluation.__new__(pe.Evaluation)
    evaluation.bounds = {'geeky-implement': (pe.utc_time('2026-10-26T00:19:16+08:00'),
                                          pe.utc_time('2026-10-26T00:34:00+08:00'))}
    evaluation.events = [{'t': '2026-10-25T16:25:00.123Z', 'kind': 'spawn'}]
    assert evaluation.within('geeky-implement') == evaluation.events


def test_batched_commit_helper_counts_each_recorded_gate_pass():
    event = {'text': 'function C { python check-commit.py --message $msg }; C a; C b; C c',
             'output': 'OK: commit message valid.\r\nOK: commit message valid.\r\nOK: commit message valid.\r\n'}
    assert pe.commit_gate_runs(event) == 3
    assert pe.commit_gate_runs({'text': 'python check-commit.py --message x', 'output': ''}) == 1
    assert pe.commit_gate_runs({'text': 'Get-Content x', 'output': event['output']}) == 0


def test_stage_boundaries_use_explicit_review_dispatch_and_skill():
    evaluation = pe.Evaluation.__new__(pe.Evaluation)
    times = [pe.utc_time(f'2026-10-25T03:{minute}:00Z') for minute in ('00', '05', '10', '20', '30')]
    evaluation.moves = [
        {'subject': 'docs: author feature specification in docs/spec', 'time': times[1], 'files': []},
        {'subject': pe.PLAN_REVIEW_SUBJECT, 'time': times[3], 'files': ['implementation-plan.md']}]
    evaluation.events = [
        {'t': times[0], 'kind': 'shell', 'name': 'Tool: PowerShell', 'text': 'read'},
        {'t': times[2], 'kind': 'spawn', 'name': 'Tool: Agent', 'text': 'plan-review Phase 1 document audit'},
        {'t': times[4], 'kind': 'skill', 'name': 'Tool: Skill', 'text': 'geeky-orchestration:impl-review'}]
    bounds = evaluation.stage_bounds()
    assert bounds['plan-review'] == (times[2], times[3])
    assert bounds['impl-review'][0] == times[4]


def test_named_actor_trace_does_not_turn_coder_edits_into_orchestrator_edits():
    root = obs('actor', 'codex-mxc-win-coder-worker', '', kind='AGENT')
    root['metadata'] = {'actor_scope': 'subagent', 'agent_role': 'coder'}
    edit = obs('edit', 'apply_patch', '*** Begin Patch\n*** Add File: app.py\n+x\n*** End Patch', parent='actor')
    assert pe.events([root, edit])[0]['thread'] == 'sub'


def test_scores_map_parity_results():
    parity = {'harness': 'codex', 'composite': 98.75, 'quality': 96.8, 'adherence': 0.0, 'adherence_uncapped': 96.97,
              'adherence_fraction': '32/33', 'consistency': 100.0,
              'checks': [{'id': 'a.no_forbidden_git', 'status': 'fail', 'evidence': 'reflog: reset'},
                         {'id': 'a.final_report_claims', 'status': 'pass', 'evidence': 'judge: ok'}]}
    run = {'oracle': {'passed': 13, 'collected': 13}, 'telemetry': {'coverage_complete': True}, 'interventions': 1}
    values, comments = ls.scores(run, parity)
    assert values['oracle_pass_rate'] == 1.0 and values['forbidden_git_operation'] is True
    assert values['final_report_claims_verified'] is True and values['provider_refusals'] == 1
    assert set(values) <= set(ls.CONFIGS) and comments['process_adherence'] == '32/33 checks passed'


def test_score_publication_uses_named_session_and_retains_native_id(tmp_path, capsys):
    run_dir = tmp_path / 'run'
    run_dir.mkdir()
    (run_dir / 'run.json').write_text(json.dumps({
        'session_id': 'native-thread', 'telemetry': {
            'session_id': 'codex-mxc-win-c0-wordstat-stamp', 'environment': 'mxc-win',
            'agent_family': 'codex-mxc-win', 'coverage_complete': False}}))
    parity = tmp_path / 'parity.json'
    parity.write_text(json.dumps({
        'harness': 'codex', 'composite': 100, 'quality': 100, 'adherence': 100,
        'adherence_uncapped': 100, 'adherence_fraction': '1/1', 'consistency': 100,
        'checks': [{'id': 'a.no_forbidden_git', 'status': 'pass', 'evidence': 'fixture'}]}))
    coverage = tmp_path / 'coverage.json'
    coverage.write_text(json.dumps({'session_id': 'codex-mxc-win-c0-wordstat-stamp', 'complete': True}))
    assert ls.main(['--run', str(run_dir), '--parity', str(parity), '--coverage', str(coverage), '--dry-run']) == 0
    published = json.loads(capsys.readouterr().out)
    assert published['session'] == 'codex-mxc-win-c0-wordstat-stamp'
    assert published['metadata']['native_session_id'] == 'native-thread'
    assert published['metadata']['environment'] == 'mxc-win'
    assert published['scores']['harness_coverage_complete'] is True
    assert len(published['metadata']['coverage_report_sha256']) == 64
    assert json.loads((run_dir / 'run.json').read_text())['telemetry']['coverage_complete'] is False
