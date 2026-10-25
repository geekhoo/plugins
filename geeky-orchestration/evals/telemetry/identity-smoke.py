"""Model-free, three-agent fixture for the installed Langfuse converters.

This writes synthetic native-shaped rollouts, invokes only the telemetry hook,
and performs no inference or tool execution. Run with a resolved mock telemetry
environment. Use the Langfuse CLI to audit the resulting shared run session.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid


def create_fixture(home, unannounced=False):
    home = Path(home)
    folder = home / 'sessions'
    folder.mkdir(parents=True, exist_ok=False)
    actors = {role: str(uuid.uuid4()) for role in ('orchestrator', 'coder', 'reviewer')}
    roles = {'coder': 'geeky-coder', 'reviewer': 'code-reviewer'}
    base = dt.datetime.now(dt.timezone.utc)
    files = {}
    for offset, role in enumerate(actors):
        agent_id = actors[role]
        parent = None if role == 'orchestrator' else actors['orchestrator' if role == 'coder' else 'coder']
        meta = {'id': agent_id, 'timestamp': base.isoformat(), 'cwd': str(home),
                'cli_version': '0.164.0', 'model_provider': 'mock'}
        if parent:
            fields = dict(parent_thread_id=parent, agent_role=roles[role],
                          agent_path=f'/root/{role}', agent_nickname=f'{role}-smoke')
            if unannounced:
                meta.update(thread_source='subagent', source={'subagent': {'thread_spawn': fields}})
            else:
                meta.update(thread_source='subagent', **fields)
        rows = []

        def row(kind, payload):
            timestamp = base + dt.timedelta(milliseconds=offset * 100 + len(rows))
            rows.append({'timestamp': timestamp.isoformat(), 'type': kind, 'payload': payload})

        row('session_meta', meta)
        row('event_msg', {'type': 'task_started', 'turn_id': f'turn-{role}'})
        row('turn_context', {'model': 'identity-smoke-no-inference', 'effort': 'mock'})
        row('event_msg', {'type': 'user_message', 'message': f'Synthetic {role} telemetry fixture; no model call.'})
        child = 'coder' if role == 'orchestrator' else 'reviewer' if role == 'coder' else None
        if child and not unannounced:
            row('response_item', {'type': 'function_call', 'name': 'spawn_agent',
                                 'call_id': f'spawn-{child}', 'arguments': json.dumps({
                                     'agent_type': roles[child], 'task_name': child, 'message': 'Synthetic fixture'})})
            row('response_item', {'type': 'function_call_output', 'call_id': f'spawn-{child}',
                                 'output': json.dumps({'agent_id': actors[child], 'nickname': f'{child}-smoke'})})
        row('response_item', {'type': 'message', 'role': 'assistant',
                             'content': [{'type': 'output_text', 'text': f'Synthetic {role} finished.'}]})
        row('event_msg', {'type': 'token_count', 'info': {
            'last_token_usage': {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0},
            'total_token_usage': {'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}}})
        row('event_msg', {'type': 'task_complete', 'turn_id': f'turn-{role}'})
        file = folder / f'rollout-{agent_id}.jsonl'
        file.write_text(''.join(json.dumps(item) + '\n' for item in rows), encoding='utf-8')
        files[role] = file
    return actors, files


def create_claude_fixture(home):
    home = Path(home)
    home.mkdir(parents=True, exist_ok=False)
    actors = {role: str(uuid.uuid4()) for role in ('orchestrator', 'coder', 'reviewer')}
    subagents = home / actors['orchestrator'] / 'subagents'
    subagents.mkdir(parents=True)
    base = dt.datetime.now(dt.timezone.utc)
    files = {}
    for role in actors:
        rows = []

        def row(kind, content):
            rows.append({'type': kind, 'uuid': str(uuid.uuid4()), 'sessionId': actors['orchestrator'],
                         'timestamp': (base + dt.timedelta(milliseconds=len(rows))).isoformat(),
                         'cwd': str(home), 'isSidechain': False, 'message': {'role': kind, 'content': content,
                         **({'id': str(uuid.uuid4()), 'model': 'identity-smoke-no-inference',
                             'usage': {'input_tokens': 0, 'output_tokens': 0}, 'stop_reason': 'end_turn'}
                            if kind == 'assistant' else {})}})

        row('user', f'Synthetic {role}; no inference or tool execution.')
        child = 'coder' if role == 'orchestrator' else 'reviewer' if role == 'coder' else None
        if child:
            agent_type = 'geeky-coder' if child == 'coder' else 'code-reviewer'
            tool_id = f'dispatch-{child}'
            row('assistant', [{'type': 'tool_use', 'id': tool_id, 'name': 'Agent',
                               'input': {'subagent_type': agent_type, 'name': f'{child}-smoke',
                                         'description': f'Synthetic {child}', 'prompt': 'Synthetic fixture'}}])
            row('user', [{'type': 'tool_result', 'tool_use_id': tool_id, 'content': f'Synthetic {child} finished.'}])
            (subagents / f'agent-{actors[child]}.meta.json').write_text(json.dumps({
                'toolUseId': tool_id, 'agentType': agent_type, 'name': f'{child}-smoke',
                'description': f'Synthetic {child}'}), encoding='utf-8')
        row('assistant', [{'type': 'text', 'text': f'Synthetic {role} complete.'}])
        file = home / f'{actors[role]}.jsonl' if role == 'orchestrator' else subagents / f'agent-{actors[role]}.jsonl'
        file.write_text(''.join(json.dumps(item) + '\n' for item in rows), encoding='utf-8')
        files[role] = file
    return actors, files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home', type=Path, required=True)
    parser.add_argument('--harness', choices=['codex', 'claude-code'], default='codex')
    parser.add_argument('--node')
    parser.add_argument('--tracer')
    parser.add_argument('--hook-command', help='Claude bootstrap argv as JSON, with no credentials')
    parser.add_argument('--unannounced', action='store_true', help='Codex: recover children using nested parent metadata only')
    args = parser.parse_args()
    if not os.environ.get('GEEKY_SESSION_ID') or not os.environ.get('GEEKY_AGENT_FAMILY'):
        parser.error('Resolve a mock telemetry identity before running this fixture')
    metadata = json.loads(os.environ.get('GEEKY_RUN_METADATA', '{}'))
    if metadata.get('mock') != 'true':
        parser.error('This fixture requires mock=true metadata')
    if args.harness == 'codex' and (not args.node or not args.tracer):
        parser.error('Codex requires --node and --tracer')
    if args.harness == 'claude-code' and not args.hook_command:
        parser.error('Claude requires --hook-command')
    actors, files = create_fixture(args.home, args.unannounced) if args.harness == 'codex' else create_claude_fixture(args.home)
    payload = {'session_id': actors['orchestrator'], 'transcript_path': str(files['orchestrator']),
               'hook_event_name': 'SessionEnd' if args.harness == 'claude-code' else 'Stop',
               'turn_id': 'turn-orchestrator', 'cwd': str(args.home)}
    env = {**os.environ, 'CODEX_HOME': str(args.home), 'LANGFUSE_CODEX_FAIL_ON_ERROR': 'true'}
    options = ['--preserve-symlinks-main', '--preserve-symlinks'] if sys.platform == 'win32' else []
    command = [args.node, *options, args.tracer] if args.harness == 'codex' else json.loads(args.hook_command)
    subprocess.run(command, input=json.dumps(payload), text=True,
                   env=env, check=True, timeout=300)
    report = {'session_id': os.environ['GEEKY_SESSION_ID'], 'actors': actors, 'paid_model_calls': 0,
              'environment': os.environ.get('LANGFUSE_TRACING_ENVIRONMENT')}
    (args.home / 'identity-smoke.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
