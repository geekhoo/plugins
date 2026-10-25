import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('langfuse_coverage', Path(__file__).with_name('langfuse-coverage.py'))
cov = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cov)


def obs(id_, type_, name, parent=None, input_=None, output=None, usage=None):
    return {'id': id_, 'type': type_, 'name': name, 'parentObservationId': parent,
            'input': json.dumps(input_) if input_ is not None else None,
            'output': json.dumps(output) if output is not None else None, 'usageDetails': usage or {}}


def hits(points):
    return {p['point'] for p in points if p['hit']}


def test_actor_owned_agent_trace_keeps_subagent_classification():
    root = obs('coder', 'AGENT', 'codex-mxc-win-coder-task')
    root['metadata'] = {'actor_scope': 'subagent', 'agent_role': 'coder'}
    spawn = obs('review', 'TOOL', 'spawn_agent', 'coder', {'agent_type': 'code-reviewer'})
    assert cov.is_subagent_container(root)
    report = cov.coverage([root, spawn])
    assert 'nested_subagents' in hits(report)


def test_same_command_literal_variable_skill_read_counts():
    command = "$r='C:/plugin/skills/impl-review'; Get-Content \"$r/SKILL.md\""
    report = cov.coverage([obs('read', 'TOOL', 'exec_command', input_={'cmd': command})])
    assert 'stage:impl-review' in hits(report)


def test_claude_read_windows_skill_path_counts():
    report = cov.coverage([obs('read', 'TOOL', 'Tool: Read', input_={
        'file_path': r'C:\plugin\skills\geeky-plan\SKILL.md'})])
    assert 'stage:geeky-plan' in hits(report)


def test_ambiguous_variable_skill_read_is_not_guessed():
    command = "$r='C:/plugin/skills/impl-review'; $r='C:/elsewhere'; Get-Content \"$r/SKILL.md\""
    report = cov.coverage([obs('read', 'TOOL', 'exec_command', input_={'cmd': command})])
    assert 'stage:impl-review' not in hits(report)


def test_claude_names_cover_every_required_point():
    o = [obs('turn', 'SPAN', 'Conversational Turn')]
    o += [obs(f's{i}', 'TOOL', 'Tool: Skill', 'turn', {'skill': f'geeky-orchestration:{s}'}) for i, s in enumerate(cov.STAGES)]
    o += [obs('a1', 'TOOL', 'Tool: Agent', 'turn', {'subagent_type': 'geeky-orchestration:geeky-implement-orchestrator'}),
          obs('sub', 'SPAN', 'Subagent: implement', 'turn'),
          obs('a2', 'TOOL', 'Tool: Agent', 'sub', {'subagent_type': 'geeky-orchestration:geeky-coder'}),
          obs('a3', 'TOOL', 'Tool: Agent', 'sub', {'subagent_type': 'geeky-orchestration:code-reviewer'}),
          obs('sh', 'TOOL', 'Tool: PowerShell', 'sub', {'command': 'python scripts/validate-kanban.py; python -m pytest -q; git add -A; git commit -m "x"'}),
          obs('w', 'TOOL', 'Tool: Write', 'sub', {'file_path': 'a.py'}),
          obs('g', 'GENERATION', 'LLM Call', 'turn', output={'content': 'x', 'thinking': [{'content': 'why'}]}, usage={'input': 3})]
    report = cov.coverage(o)
    assert not [p['point'] for p in report if p['required'] and not p['hit']]
    assert 'mcp_tools' not in hits(report)


def test_codex_names_escaped_js_commands_and_encrypted_handoffs():
    o = [obs('turn', 'AGENT', 'Codex Turn')]
    o += [obs(f's{i}', 'TOOL', f'skill:{s}', 'turn', 'x') for i, s in enumerate(cov.STAGES)]
    o += [obs('sp1', 'TOOL', 'spawn_agent', 'turn', {'agent_type': 'geeky-coder', 'message': 'gAAAAABxyz'}),
          obs('child', 'AGENT', 'Codex Subagent Turn', 'sp1'),
          obs('sp2', 'TOOL', 'spawn_agent', 'child', {'agent_type': 'code-reviewer'}),
          obs('ex', 'TOOL', 'exec', 'child', 'tools.exec_command({cmd:"python check-dod.py\\npytest -q\\ngit commit -m $m"})'),
          obs('ap', 'TOOL', 'apply_patch', 'child', '*** Begin Patch'),
          obs('g', 'GENERATION', 'LLM', 'turn', output={'content': 'x', 'reasoning': '{"text": "s"}'}, usage={'output': 2})]
    report = cov.coverage(o)
    assert not [p['point'] for p in report if p['required'] and not p['hit']]
    assert {'gate:check-dod', 'encrypted_handoffs'} <= hits(report)


def test_missing_points_are_reported():
    report = cov.coverage([obs('g', 'GENERATION', 'LLM', usage={'input': 1})])
    missed = {p['point'] for p in report if p['required'] and not p['hit']}
    assert {'stage:geeky-plan', 'git_commit', 'reasoning_summaries'} <= missed
    assert 'nested_subagents' not in missed   # informational: the skill does not require delegation
    assert 'token_usage' not in missed
