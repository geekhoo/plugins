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
