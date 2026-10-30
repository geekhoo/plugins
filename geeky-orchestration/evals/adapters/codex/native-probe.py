"""Run the native Codex harness against a loopback-only deterministic Responses fixture.

No external model is contacted. Tool execution, discovery, MCP and hooks are real.
Only disposable fixture files may be written in the supplied eval workspace.
"""
import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
import queue
import subprocess
import threading
import time
import tomllib
import uuid
from diagnostics import classify_diagnostics

EXPECTED_SKILLS = ('archive', 'geeky-implement', 'geeky-plan', 'geeky-resume',
                   'geeky-status', 'impl-review', 'plan-review', 'spec-research')
THREADS = {
    'main': ('/root', 'CP2_NATIVE_MAIN'),
    'child': ('/root/cp2_native_child', 'CP2_NATIVE_CHILD_ONLY'),
    'grandchild': ('/root/cp2_native_child/cp2_native_grandchild', 'CP2_NATIVE_GRANDCHILD_ONLY'),
    'default': ('/root/cp2_native_child/cp2_native_default', 'CP2_NATIVE_DEFAULT_ONLY'),
}
ROLES = {'child': 'geeky-coder', 'grandchild': 'geeky-orchestrator'}
VARIANTS = ('default', 'paid-roles-defaultfork', 'paid-roles-forkall', 'cold-workers')
MAX_WAITS = 6


def profile_tool_shape(profile):
    provider = profile.get('provider') or {}
    return ('classic-functions' if str(provider.get('tool_shape', '')).startswith('classic-functions')
            else 'code-mode')


def declared_functions(data):
    """Use declarations from the request, including native deferred search results."""
    declarations = list(data.get('tools', []))
    for row in data.get('input', []):
        if row.get('type') == 'tool_search_output':
            declarations.extend(row.get('tools', []))
    result = []
    for tool in declarations:
        namespace = tool.get('name') if tool.get('type') == 'namespace' else None
        for child in tool.get('tools', []) if namespace else [tool]:
            if child.get('type') == 'function':
                result.append((namespace, child))
    return result


def declared_call(data, name, arguments, call_id):
    matches = [(namespace, tool) for namespace, tool in declared_functions(data)
               if tool.get('name') == name or tool.get('name', '').endswith('__' + name)]
    if len(matches) != 1:
        raise ValueError('Fixture requires one declared function: ' + name)
    namespace, tool = matches[0]
    return item(tool['name'], arguments, call_id, namespace)


def history_protocol_evidence(requests):
    """Redacted shape checks only; never decode, replace or authenticate ciphertext."""
    errors, searches, opaque = [], 0, 0
    for request_index, request in enumerate(requests):
        for index, row in enumerate(request.get('input', [])):
            if row.get('type') in ('tool_search_call', 'tool_search_output'):
                searches += 1
                prefix = 'tsc_' if row['type'] == 'tool_search_call' else 'tso_'
                if not isinstance(row.get('id'), str) or not row['id'].startswith(prefix):
                    errors.append({'request_index': request_index, 'item_index': index,
                                   'code': 'tool_search_item_id_prefix', 'type': row['type']})
            # Only count opaque content. Presence/shape cannot prove decryptability.
            opaque += bool(row.get('encrypted_content'))
            for field in ('content', 'output'):
                value = row.get(field)
                if isinstance(value, list):
                    opaque += sum(isinstance(part, dict) and part.get('type') == 'encrypted_content'
                                  for part in value)
    return {'ok': not errors, 'errors': errors, 'tool_search_items': searches,
            'opaque_items': opaque, 'cryptographic_compatibility_verified': False}


def worker_routing_errors(data, own_path, spawned_paths=()):
    """Inspect structured calls, not assistant prose, for the observed self/wait defects."""
    errors = []
    for row in data.get('input', []):
        if row.get('type') != 'function_call' or row.get('namespace') != 'collaboration':
            continue
        arguments = json.loads(row['arguments'])
        if row.get('name') in ('send_message', 'followup_task') and arguments.get('target') == own_path:
            errors.append('self_target')
        if row.get('name') == 'wait_agent' and not spawned_paths:
            errors.append('wait_without_child')
    return errors


def native_plaintext_contract_evidence(requests):
    """Check only handoff encryption and unsupported search; reasoning is independent."""
    encrypted_schemas = tagged_handoffs = search_items = 0
    for request in requests:
        search_items += sum(tool.get('type') == 'tool_search' for tool in request.get('tools', []))
        for namespace in request.get('tools', []):
            if namespace.get('type') != 'namespace' or namespace.get('name') != 'collaboration':
                continue
            for tool in namespace.get('tools', []):
                properties = tool.get('parameters', {}).get('properties', {})
                encrypted_schemas += sum(properties.get(field, {}).get('encrypted') is True
                                         for field in ('message', 'prompt'))
        for row in request.get('input', []):
            search_items += row.get('type') in ('tool_search_call', 'tool_search_output')
            field = ('content' if agent_envelope(row) is not None else
                     'output' if row.get('type') == 'function_call_output' else None)
            if field and isinstance(row.get(field), list):
                tagged_handoffs += sum(part.get('type') == 'encrypted_content'
                                       for part in row[field] if isinstance(part, dict))
    return {'encrypted_message_schemas': encrypted_schemas,
            'tagged_encrypted_handoffs': tagged_handoffs, 'search_items': search_items}


def fixture_file_write(workspace, marker='CP2 disposable guard fixture'):
    # Single quoted PowerShell literals preserve $, quotes, spaces and Unicode.
    path = str(workspace / 'docs/spec-001-feature/draft.md').replace("'", "''")
    content = marker.replace("'", "''")
    return ("$ErrorActionPreference='Stop'; $fixturePath='" + path + "'; "
            "[System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($fixturePath)) | Out-Null; "
            "[System.IO.File]::WriteAllText($fixturePath, '" + content + "', "
            "[System.Text.UTF8Encoding]::new($false)); Get-Content -LiteralPath $fixturePath")


def classic_write_evidence(workspace, marker, events):
    """A prior attempt's file cannot stand in for this attempt's successful write."""
    try:
        exact_bytes = (workspace / 'docs/spec-001-feature/draft.md').read_bytes() == marker.encode('utf-8')
    except OSError:
        return False
    return bool(marker) and exact_bytes and any(
        event.get('type') == 'item.completed'
        and (event.get('item') or {}).get('type') == 'command_execution'
        and event['item'].get('exit_code') == 0
        and marker in (event['item'].get('command') or '')
        and marker in (event['item'].get('aggregated_output') or '')
        for event in events)


def variant_roles(variant):
    if variant not in VARIANTS:
        raise ValueError('Unknown native probe variant: ' + variant)
    return dict(ROLES) if variant in ('default', 'cold-workers') else {
        'child': 'geeky-orchestrator', 'grandchild': 'code-explorer'}


def spawn_item(arguments, call_id, variant):
    if variant == 'paid-roles-forkall':
        arguments = {**arguments, 'fork_turns': 'all'}
    elif variant == 'cold-workers':
        arguments = {**arguments, 'fork_turns': 'none'}
    return item('spawn_agent', arguments, call_id, 'collaboration')


def request_spawn_calls(requests):
    """Record the native request's echoed tool calls, excluding duplicate history."""
    calls = {}
    for index, request in enumerate(requests):
        for row in request.get('input', []):
            if row.get('type') == 'function_call' and row.get('name') == 'spawn_agent':
                calls.setdefault(row['call_id'], {'call_id': row['call_id'],
                    'request_index': index, 'arguments': json.loads(row['arguments'])})
    return list(calls.values())


ENVELOPE_PREFIX = 'Agent message envelope: '


def agent_envelope(row):
    """Author/recipient of a native agent_message or of one the bridge lowered to a user message."""
    if row.get('type') == 'agent_message':
        return {key: row.get(key) for key in ('author', 'recipient')}
    parts = row.get('content') if row.get('type') == 'message' and row.get('role') == 'user' else None
    first = parts[0] if isinstance(parts, list) and parts and isinstance(parts[0], dict) else {}
    text = first.get('text', '')
    if not isinstance(text, str) or not text.startswith(ENVELOPE_PREFIX):
        return None
    try:
        envelope = json.loads(text[len(ENVELOPE_PREFIX):])
    except ValueError:
        return None
    return envelope if isinstance(envelope, dict) else None


def content_text(row):
    parts = [c for c in row.get('content', []) if isinstance(c, dict)]
    if row.get('type') == 'message' and agent_envelope(row) is not None:
        parts = parts[1:]
    return '\n'.join(c.get('text', c.get('encrypted_content', '')) for c in parts)


def request_thread(data):
    """Prefer the newest addressed task; inherited tasks and call arguments are history."""
    inputs = data.get('input', [])
    for row in reversed(inputs):
        envelope = agent_envelope(row)
        if envelope is None:
            continue
        text = content_text(row)
        if not text.startswith('Message Type: NEW_TASK\n'):
            continue
        for name, (recipient, marker) in THREADS.items():
            if name != 'main' and envelope.get('recipient') == recipient and marker in text:
                return name
    for row in inputs:
        if row.get('type') == 'message' and row.get('role') == 'user' and agent_envelope(row) is None:
            if content_text(row).startswith(THREADS['main'][1] + '.'):
                return 'main'
            for name, (_, marker) in THREADS.items():
                if name != 'main' and content_text(row).startswith(marker + '.'):
                    return name
    return None


def child_completed(data, parent, child, marker):
    return any((agent_envelope(row) or {}).get('author') == THREADS[child][0]
               and (agent_envelope(row) or {}).get('recipient') == THREADS[parent][0]
               and content_text(row).startswith('Message Type: FINAL_ANSWER\n')
               and marker in content_text(row)
               for row in data.get('input', []))


def probe_roles(profile, variant='default', reviewer_role=None):
    roles = variant_roles(variant)
    reviewers = profile.get('model_matrix', {}).get('reviewers', {})
    if reviewer_role and (variant not in ('default', 'cold-workers') or reviewer_role not in reviewers.get('roles', [])):
        raise ValueError('Reviewer probe requires a registered reviewer role and default or cold-workers variant')
    if reviewers and variant in ('default', 'cold-workers'):
        roles['grandchild'] = reviewer_role or 'code-reviewer'
    return roles


def model_expectations(profile, variant='default', reviewer_role=None):
    config = tomllib.loads('\n'.join(profile['codex_config_overrides']))
    main = {'model': profile.get('model', config.get('model')),
            'reasoning': profile.get('reasoning', config.get('model_reasoning_effort'))}
    worker = {'model': profile.get('worker_model', main['model']),
              'reasoning': profile.get('worker_reasoning', main['reasoning'])}
    matrix = profile.get('model_matrix', {'orchestrator': main, 'workers': worker})
    if (matrix.get('orchestrator') != main
            or {k: matrix.get('workers', {}).get(k) for k in worker} != worker):
        raise ValueError('Profile model matrix disagrees with explicit model/reasoning fields')
    reviewers = matrix.get('reviewers')
    if bool(reviewers) != bool(profile.get('reviewer_reasoning')) or reviewers and (reviewers != {'model': worker['model'], 'reasoning': profile.get('reviewer_reasoning'),
            'roles': ['code-reviewer', 'code-architect-reviewer'], 'scope': 'review-assignments'}
            or matrix['workers'].get('scope') != 'all-descendants-except-reviewers'):
        raise ValueError('Profile reviewer matrix disagrees with explicit reviewer settings')
    instructions = {'main': config.get('developer_instructions', '')}
    expected = {'main': main, 'child': worker, 'grandchild': worker, 'default': worker}
    for thread, role in probe_roles(profile, variant, reviewer_role).items():
        role_file = config.get('agents', {}).get(role, {}).get('config_file')
        instructions[thread] = (tomllib.loads(Path(role_file).read_text(encoding='utf-8'))
                                .get('developer_instructions', '') if role_file else '')
        if reviewers and role in reviewers['roles']:
            expected[thread] = {key: reviewers[key] for key in ('model', 'reasoning')}
    return expected, instructions


def request_evidence(requests, expected, instructions):
    evidence = {}
    for thread in THREADS:
        indices = [i for i, request in enumerate(requests) if request_thread(request) == thread]
        observed = []
        for index in indices:
            request = requests[index]
            developer = '\n'.join(content_text(row) for row in request.get('input', [])
                                  if row.get('role') == 'developer')
            # A descendant inherits ancestors' instructions. The last complete registered
            # role body identifies its own applied layer, not merely inherited text.
            positions = {name: developer.rfind(body.strip()) for name, body in instructions.items()
                         if body.strip() and body.strip() in developer}
            own = positions.get(thread, -1)
            role_ok = own >= 0 and own == max(positions.values(), default=-1)
            observed.append({'request_index': index, 'model': request.get('model'),
                             'reasoning': (request.get('reasoning') or {}).get('effort'),
                             'registered_instructions': role_ok})
        evidence[thread] = {'expected': expected[thread], 'requests': observed,
            'model_reasoning_ok': bool(observed) and all(
                all(row[key] == value and value is not None for key, value in expected[thread].items())
                for row in observed),
            'instructions_ok': bool(observed) and all(row['registered_instructions'] for row in observed)}
    return evidence


def fixture_output(data, state, workspace):
    variant = state['variant']
    roles = state.get('roles', variant_roles(variant))
    thread = request_thread(data)
    if thread is None:
        state['errors'].append('Unroutable fixture request')
        return message('CP2_NATIVE_UNROUTABLE')
    state[thread + '_requests'] += 1
    if thread in ('grandchild', 'default'):
        return message('CP2_NATIVE_' + thread.upper() + '_OK')
    if thread == 'child':
        if state['child_requests'] == 1:
            return spawn_item({'agent_type': roles['grandchild'],
                'task_name': 'cp2_native_grandchild',
                'message': 'CP2_NATIVE_GRANDCHILD_ONLY. Return CP2_NATIVE_GRANDCHILD_OK.'},
                'cp2_nested_spawn', variant)
        if child_completed(data, 'child', 'grandchild', 'CP2_NATIVE_GRANDCHILD_OK'):
            if not state['default_spawned']:
                state['default_spawned'] = True
                # Baseline/cold variants omit agent_type; paid variants use explicit default.
                arguments = {'task_name': 'cp2_native_default',
                             'message': 'CP2_NATIVE_DEFAULT_ONLY. Return CP2_NATIVE_DEFAULT_OK.'}
                if variant not in ('default', 'cold-workers'):
                    arguments['agent_type'] = 'default'
                return spawn_item(arguments, 'cp2_default_spawn', variant)
            if child_completed(data, 'child', 'default', 'CP2_NATIVE_DEFAULT_OK'):
                return message('CP2_NATIVE_CHILD_OK')
        waiting = 'child'
    else:
        step = state['main_step']
        classic = state.get('tool_shape') == 'classic-functions'
        prior_mcp = [x for x in data.get('input', []) if str(x.get('call_id', '')).startswith('cp2_mcp')
                     and x.get('type') == 'custom_tool_call_output']
        if step == 3 and prior_mcp and 'CP2_MCP_PENDING' in str(prior_mcp[-1].get('output')) and state['mcp_attempts'] < 20:
            step = state['main_step'] = 2
        if step < 4:
            state['main_step'] += 1
        if step == 0:
            if classic:
                python = state['guard_python'].replace("'", "''")
                guard = ("; '{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"docs/spec-001-feature/draft.md\"}}' | "
                         "& '" + python + "' (Join-Path $env:CLAUDE_PLUGIN_ROOT 'hooks/guard-planning-contract.py') --mode warn; "
                         "if($LASTEXITCODE -ne 0){throw 'CP2_EXPLICIT_GUARD_FAILED'}")
                return declared_call(data, 'exec_command', {'cmd': fixture_file_write(workspace, state.get(
                    'file_marker', 'CP2 disposable guard fixture')) + guard,
                    'workdir': str(workspace), 'login': False}, 'cp2_write')
            return item('apply_patch', '*** Begin Patch\n*** Add File: docs/spec-001-feature/draft.md\n+CP2 disposable guard fixture\n*** End Patch', 'cp2_patch')
        if step == 1:
            call = declared_call if classic else lambda data, *args: item(*args)
            return call(data, 'exec_command', {'cmd': "$ErrorActionPreference='Stop'; Get-Content -Raw -LiteralPath (Join-Path $env:CLAUDE_PLUGIN_ROOT 'skills/geeky-plan/SKILL.md'); Write-Output 'CP2_NATIVE_SKILL_OK'; Write-Output 'CP2_NATIVE_EXEC_OK'",
                'workdir': str(workspace), 'login': False}, 'cp2_exec')
        if step == 2:
            state['mcp_attempts'] += 1
            if classic:
                if any(tool.get('name', '').endswith('geeky_check_commit')
                       for _, tool in declared_functions(data)):
                    return declared_call(data, 'geeky_check_commit', {'params': {
                        'message': 'chore(mock): probe native MCP\n\nTasks: T0'}}, 'cp2_mcp_call')
                # Deferred discovery is a native client operation, not a JSON function.
                state['main_step'] = 2
                if state['mcp_attempts'] > 20:
                    state['errors'].append('classic MCP discovery exhausted')
                    return message('CP2_NATIVE_MCP_FAILED')
                if not any(tool.get('type') == 'tool_search' for tool in data.get('tools', [])):
                    if any(tool.get('name') == 'exec_command' for _, tool in declared_functions(data)):
                        # Native MCP startup is asynchronous. Recheck its next request's
                        # catalog without emitting an unsupported search operation.
                        return declared_call(data, 'exec_command', {
                            'cmd': "Start-Sleep -Milliseconds 500; Write-Output 'CP2_MCP_PENDING'",
                            'workdir': str(workspace), 'login': False},
                            'cp2_mcp_pending_' + str(state['mcp_attempts']))
                    state['errors'].append('classic MCP unavailable: no declared gate, tool_search or exec_command')
                    return message('CP2_NATIVE_MCP_UNAVAILABLE')
                return {'type': 'tool_search_call', 'id': 'tsc_cp2_' + str(state['mcp_attempts']),
                        'call_id': 'call_cp2_search_' + str(state['mcp_attempts']),
                        'execution': 'client', 'arguments': {'query': 'geeky_check_commit'}}
            script = ('const t=ALL_TOOLS.find(x=>x.name.endsWith("geeky_check_commit"));'
                      'if(!t){await new Promise(r=>setTimeout(r,500));text("CP2_MCP_PENDING");}else{'
                      'const r=await tools[t.name]({params:{message:"chore(mock): probe native MCP\\n\\nTasks: T0"}});'
                      'const g=r.structuredContent||JSON.parse(r.content.find(c=>c.type==="text").text);'
                      'if(g.ok!==true||g.exit_code!==0)throw Error("CP2_MCP_GATE_FAILED");'
                      'text(r);}')
            return item('exec', script, 'cp2_mcp_' + str(state['mcp_attempts']), 'functions')
        if step == 3:
            return spawn_item({'agent_type': roles['child'],
                'task_name': 'cp2_native_child',
                'message': 'CP2_NATIVE_CHILD_ONLY. Spawn the scripted grandchild, wait for its final answer, then return CP2_NATIVE_CHILD_OK.'},
                'cp2_spawn', variant)
        if child_completed(data, 'main', 'child', 'CP2_NATIVE_CHILD_OK'):
            return message('CP2_NATIVE_OK')
        waiting = 'main'
    state[waiting + '_waits'] += 1
    if state[waiting + '_waits'] > MAX_WAITS:
        state['errors'].append(waiting + ' exhausted bounded descendant waits')
        return message('CP2_NATIVE_WAIT_FAILED')
    return item('wait_agent', {'timeout_ms': 10000},
                'cp2_' + waiting + '_wait_' + str(state[waiting + '_waits']), 'collaboration')


def fixture_state(variant='default'):
    variant_roles(variant)  # Reject unknown variants before any process is launched.
    return {'variant': variant, 'main_step': 0, 'main_requests': 0, 'child_requests': 0, 'grandchild_requests': 0,
            'default_requests': 0, 'default_spawned': False,
            'main_waits': 0, 'child_waits': 0, 'mcp_attempts': 0, 'errors': []}


def missing_skill_paths(inputs):
    catalogue = '\n'.join(c.get('text', '') for row in inputs
                          for c in row.get('content', []) if isinstance(c, dict))
    catalogue = re.sub('/+', '/', catalogue.replace('\\', '/'))
    return [name for name in EXPECTED_SKILLS if name + '/SKILL.md' not in catalogue]


def install_local_plugin(codex, overrides, output):
    """Materialize only the pinned local export; enabling a config entry is insufficient."""
    command = [codex, '--no-daemon', 'plugin', 'add', 'geeky-orchestration@geeky-eval', '--json']
    for override in overrides:
        command += ['-c', override]
    result = subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True,
                            text=True, encoding='utf-8', timeout=45)
    (output / 'native-plugin-install.json').write_text(result.stdout, encoding='utf-8')
    (output / 'native-plugin-install-stderr.txt').write_text(result.stderr, encoding='utf-8')
    if result.returncode:
        raise RuntimeError('Pinned local plugin installation failed; see native-plugin-install evidence')


def resolve_hook_trust(codex, overrides, workspace, output, telemetry_command=None):
    """Ask the native hook catalogue for exact IDs/hashes; no thread or model turn."""
    auth_free_home = output / 'hook-catalog-home'
    auth_free_home.mkdir()
    command = [codex, '--no-daemon', 'app-server', '--stdio', '--strict-config']
    for override in overrides:
        command += ['-c', override]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, encoding='utf-8',
        env={**os.environ, 'CODEX_HOME': str(auth_free_home)})
    lines = queue.Queue()
    errors = []
    reader_errors = []
    def read_pipe(stream, append):
        try:
            for line in stream:
                append(line)
        except Exception as exc:
            reader_errors.append(str(exc))
    readers = [
        threading.Thread(target=read_pipe, args=(process.stdout, lines.put), daemon=True),
        threading.Thread(target=read_pipe, args=(process.stderr, errors.append), daemon=True),
    ]
    for reader in readers:
        reader.start()
    def send(value):
        process.stdin.write(json.dumps(value) + '\n')
        process.stdin.flush()
    def response(mid):
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            try:
                value = json.loads(lines.get(timeout=.5))
            except queue.Empty:
                continue
            if value.get('id') == mid:
                if 'error' in value:
                    raise RuntimeError('Native hook catalogue RPC failed: ' + str(value['error']))
                return value['result']
        raise TimeoutError('Native hook catalogue did not respond')
    try:
        send({'id': 1, 'method': 'initialize', 'params': {'clientInfo': {
            'name': 'cp2-hook-catalog', 'version': '1.0'}, 'capabilities': {'experimentalApi': True}}})
        response(1)
        send({'method': 'initialized'})
        send({'id': 2, 'method': 'hooks/list', 'params': {'cwds': [str(workspace)]}})
        result = response(2)
        (output / 'native-hook-catalog.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        states = {}
        for group in result.get('data', []):
            for hook in group.get('hooks', []):
                # This profile declares exactly the vetted warn bridge and no other hook.
                if str(hook.get('eventName', '')).lower() == 'pretooluse' and 'guard-bridge.py' in str(hook.get('command')):
                    states[hook['key']] = {'trusted_hash': hook['currentHash'], 'enabled': True}
                # The optional Langfuse Stop hook is trusted only by its exact generated command.
                elif (telemetry_command and str(hook.get('eventName', '')).lower() == 'stop'
                      and str(hook.get('command')) == telemetry_command):
                    states[hook['key']] = {'trusted_hash': hook['currentHash'], 'enabled': True}
        if len(states) != 1 + bool(telemetry_command):
            raise RuntimeError('Expected exactly one vetted native guard hook'
                               + (' and one Langfuse Stop hook' if telemetry_command else ''))
        return 'hooks.state={' + ','.join(json.dumps(k) + '={trusted_hash=' +
            json.dumps(v['trusted_hash']) + ',enabled=true}' for k, v in states.items()) + '}'
    finally:
        process.stdin.close()
        try:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        finally:
            for reader in readers:
                reader.join(timeout=5)
            (output / 'native-hook-catalog-stderr.txt').write_text(''.join(errors), encoding='utf-8')
            if any(reader.is_alive() for reader in readers):
                raise RuntimeError('Native hook catalogue pipe readers did not drain')
            if reader_errors:
                raise RuntimeError('Native hook catalogue pipe read failed: ' + '; '.join(reader_errors))


def item(name, arguments, call_id, namespace=None):
    if name in ('apply_patch', 'exec'):
        result = {'type': 'custom_tool_call', 'call_id': call_id, 'name': name, 'input': arguments}
    else:
        result = {'type': 'function_call', 'call_id': call_id, 'name': name,
                  'arguments': json.dumps(arguments)}
    if namespace:
        result['namespace'] = namespace
    return result


def message(text):
    return {'type': 'message', 'role': 'assistant', 'id': 'msg_fixture',
            'content': [{'type': 'output_text', 'text': text}]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--codex', required=True)
    p.add_argument('--profile', type=Path, required=True)
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--forbidden-skill-root', type=Path)
    p.add_argument('--variant', choices=VARIANTS, default='default')
    p.add_argument('--reviewer-role', choices=('code-reviewer', 'code-architect-reviewer'))
    p.add_argument('--native-plaintext-proxy', action='store_true',
                   help='Exercise the native-preserving compatibility proxy against this local fixture only')
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=True)
    profile = json.loads(a.profile.read_text(encoding='utf-8-sig'))
    expected_models, expected_instructions = model_expectations(profile, a.variant, a.reviewer_role)
    roles = probe_roles(profile, a.variant, a.reviewer_role)
    version_result = subprocess.run([a.codex, '--version'], stdin=subprocess.DEVNULL,
        capture_output=True, text=True, encoding='utf-8', timeout=15)
    cli_version = version_result.stdout.strip().removeprefix('codex-cli ')
    denial_verified = False
    denial_detail = {'path': str(a.forbidden_skill_root), 'winerror': None}
    if a.forbidden_skill_root is not None:
        try:
            list(a.forbidden_skill_root.iterdir())
        except PermissionError as exc:
            denial_detail['winerror'] = getattr(exc, 'winerror', None)
            denial_verified = getattr(exc, 'winerror', None) == 5
        except OSError as exc:
            denial_detail['other_error'] = str(exc)
    install_local_plugin(a.codex, profile['codex_config_overrides'], a.output)
    trust_override = resolve_hook_trust(a.codex, profile['codex_config_overrides'], a.workspace, a.output)
    requests = []
    state = fixture_state(a.variant)
    state['roles'] = roles
    state['file_marker'] = 'CP2 disposable guard fixture ' + uuid.uuid4().hex
    state['tool_shape'] = profile_tool_shape(profile)
    config = tomllib.loads('\n'.join(profile['codex_config_overrides']))
    state['guard_python'] = config.get('mcp_servers', {}).get('geeky', {}).get('command', '')
    if state['tool_shape'] == 'classic-functions' and not state['guard_python']:
        raise ValueError('Classic fixture requires the prepared MCP Python interpreter for explicit guard proof')
    lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Never log HTTP headers or credentials.

        def do_GET(self):
            # Native model discovery stays on the same local fixture too.
            body = json.dumps({'models': []}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            if self.path not in ('/v1/responses', '/responses'):
                self.send_error(404)
                return
            data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            with lock:
                requests.append(data)
                output = fixture_output(data, state, a.workspace)
                rid = 'resp_cp2_' + str(len(requests))
            events = [
                {'type': 'response.created', 'response': {'id': rid}},
                {'type': 'response.output_item.done', 'item': output},
                {'type': 'response.completed', 'response': {'id': rid, 'usage': {
                    'input_tokens': 0, 'output_tokens': 0, 'total_tokens': 0}}}]
            if a.native_plaintext_proxy and output.get('type') == 'function_call':
                # Exercise real streaming initialization, not only completed items.
                # The proxy must declare plaintext before arguments arrive.
                output['id'] = 'fc_cp2_' + str(len(requests))
                added = {**output, 'arguments': '', 'status': 'in_progress'}
                events = [events[0],
                    {'type': 'response.output_item.added', 'output_index': 0, 'item': added},
                    {'type': 'response.function_call_arguments.delta', 'output_index': 0,
                     'item_id': output['id'], 'delta': output['arguments']},
                    {'type': 'response.function_call_arguments.done', 'output_index': 0,
                     'item_id': output['id'], 'arguments': output['arguments']},
                    {'type': 'response.output_item.done', 'output_index': 0, 'item': output},
                    events[-1]]
            body = ''.join('event: ' + e['type'] + '\ndata: ' + json.dumps(e) + '\n\n'
                           for e in events).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Connection', 'close')
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    compatibility_proxy = None
    fixture_env = os.environ.copy()
    fixture_url = f'http://127.0.0.1:{server.server_port}/v1'
    if a.native_plaintext_proxy:
        from litellm_bridge.server import make_server
        fixture_key = 'cp2-native-plaintext-local-fixture'
        compatibility_proxy = make_server(fixture_url, fixture_key, wire_mode='native-plaintext')
        threading.Thread(target=compatibility_proxy.serve_forever, daemon=True).start()
        fixture_url = f'http://127.0.0.1:{compatibility_proxy.server_port}/v1'
        fixture_env['CP2_PLAINTEXT_FIXTURE_KEY'] = fixture_key
    provider = {'name': 'CP2 loopback fixture',
                'base_url': fixture_url,
                'wire_api': 'responses', 'requires_openai_auth': False,
                'supports_websockets': False, 'request_max_retries': 0,
                'stream_max_retries': 0}
    if compatibility_proxy:
        provider['env_key'] = 'CP2_PLAINTEXT_FIXTURE_KEY'
    # TOML inline table uses JSON string values and TOML booleans.
    def value(v):
        return str(v).lower() if isinstance(v, bool) else json.dumps(v)
    provider_toml = '{' + ','.join(json.dumps(k) + '=' + value(v) for k, v in provider.items()) + '}'
    command = [a.codex, '--no-daemon', 'exec', '--json', '--sandbox', 'danger-full-access',
               '--ignore-user-config', '--ignore-rules', '--strict-config', '--cd', str(a.workspace)]
    for override in profile['codex_config_overrides']:
        command += ['-c', override]
    command += ['-c', 'model_provider="cp2_fixture"', '-c', 'model_providers.cp2_fixture=' + provider_toml]
    command += ['-c', trust_override]
    command += ['CP2_NATIVE_MAIN. Follow only the deterministic local fixture responses; no external services.']
    started = time.monotonic()
    try:
        result = subprocess.run(command, stdin=subprocess.DEVNULL, text=True, capture_output=True,
                                timeout=180, env=fixture_env)
    finally:
        if compatibility_proxy:
            compatibility_proxy.shutdown()
            compatibility_proxy.server_close()
        server.shutdown()
        server.server_close()
    a.output.mkdir(parents=True, exist_ok=True)
    (a.output / 'native-stream.jsonl').write_text(result.stdout, encoding='utf-8')
    (a.output / 'native-stderr.txt').write_text(result.stderr, encoding='utf-8')
    # Request bodies contain this fixture's prompt/config/tools only. Headers are never stored.
    (a.output / 'native-fixture-requests.json').write_text(json.dumps(requests, indent=2), encoding='utf-8')
    text = json.dumps(requests)
    checks = []
    def check(name, passed, detail=''):
        checks.append({'name': name, 'passed': bool(passed), 'detail': detail})
    check('native_exit', result.returncode == 0, str(result.returncode))
    check('native_version', cli_version == '0.164.0' and version_result.returncode == 0
          and not version_result.stderr.strip(), cli_version)
    check('native_user_skills_denied', denial_verified, denial_detail)
    check('local_responses_only', len(requests) >= 5, f'{len(requests)} loopback fixture requests; no forwarding')
    missing_skills = missing_skill_paths(requests[0].get('input', []) if requests else [])
    check('native_skill_discovery', not missing_skills,
          {'expected_skill_paths': EXPECTED_SKILLS, 'missing': missing_skills})
    classic = state['tool_shape'] == 'classic-functions'
    native_events = [json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
    check('native_file_write' if classic else 'native_patch',
          classic_write_evidence(a.workspace, state['file_marker'], native_events) if classic
          else (a.workspace / 'docs/spec-001-feature/draft.md').is_file(),
          'Exact per-attempt UTF-8 bytes and matching successful command evidence' if classic else '')
    check('native_explicit_guard' if classic else 'native_guard_context',
          'is a frozen geeky-plan planning artifact' in text,
          'Explicit guard invocation; shell writes bypass native hook' if classic else '')
    check('native_shell', 'CP2_NATIVE_EXEC_OK' in text)
    skill_invoked = any(e.get('type') == 'item.completed'
                        and (e.get('item') or {}).get('type') == 'command_execution'
                        and (e.get('item') or {}).get('exit_code') == 0
                        and 'CP2_NATIVE_SKILL_OK' in (e['item'].get('aggregated_output') or '')
                        and 'geeky-plan' in (e['item'].get('aggregated_output') or '')
                        for e in native_events)
    check('native_skill_invoked', skill_invoked, 'Native shell read complete pinned geeky-plan SKILL.md')
    check('native_mcp', any(e.get('type') == 'item.completed'
          and (e.get('item') or {}).get('type') == 'mcp_tool_call'
          and (e.get('item') or {}).get('tool') == 'geeky_check_commit'
          and ((e['item'].get('result') or {}).get('structured_content') or {}).get('ok') is True
          and ((e['item'].get('result') or {}).get('structured_content') or {}).get('exit_code') == 0
          for e in native_events), f'{state["mcp_attempts"]} bounded discovery attempts')
    check('native_subagent', state['child_requests'] > 0, str(state['child_requests']))
    check('native_completed', 'CP2_NATIVE_OK' in result.stdout)
    evidence = request_evidence(requests, expected_models, expected_instructions)
    for thread in THREADS:
        check('native_' + thread + '_model_reasoning', evidence[thread]['model_reasoning_ok'],
              evidence[thread])
        if thread != 'default':
            check('native_' + thread + '_registered_instructions', evidence[thread]['instructions_ok'],
                  {'role': roles.get(thread, 'orchestrator'), 'request_indices': [
                      row['request_index'] for row in evidence[thread]['requests']]})
    check('native_nested_subagent', state['grandchild_requests'] > 0 and not state['errors'],
          {'grandchild_requests': state['grandchild_requests'], 'errors': state['errors']})
    stream_errors = [e for e in native_events
                     if e.get('type') == 'error' or (e.get('item') or {}).get('type') == 'error']
    plaintext_contract = native_plaintext_contract_evidence(requests)
    if a.native_plaintext_proxy:
        check('native_plaintext_handoff_contract',
              not plaintext_contract['encrypted_message_schemas']
              and not plaintext_contract['tagged_encrypted_handoffs'], plaintext_contract)
        check('native_eager_mcp', not plaintext_contract['search_items'], plaintext_contract)
    functional_ok = all(c['passed'] for c in checks)
    raw_diagnostics = {
        'plugin-install': (a.output / 'native-plugin-install-stderr.txt').read_text(encoding='utf-8'),
        'hook-catalogue': (a.output / 'native-hook-catalog-stderr.txt').read_text(encoding='utf-8'),
        'exec': result.stderr}
    diagnostics = classify_diagnostics(raw_diagnostics, str(a.forbidden_skill_root), cli_version,
        functional_ok, denial_verified, skill_invoked)
    history_protocol = history_protocol_evidence(requests)
    check('native_clean_diagnostics', diagnostics['ok'] and not stream_errors and history_protocol['ok'],
          {'known': diagnostics['known_diagnostics'], 'unexpected': diagnostics['unexpected_errors'],
           'stream_errors': len(stream_errors), 'history_protocol_errors': history_protocol['errors']})
    report = {'ok': all(c['passed'] for c in checks), 'functional_ok': functional_ok, 'checks': checks,
              'elapsed_s': round(time.monotonic() - started, 2),
              'paid_model_calls': 0, 'local_fixture_requests': len(requests),
              'child_requests': state['child_requests'], 'grandchild_requests': state['grandchild_requests'],
              'default_requests': state['default_requests'],
              'variant': a.variant, 'roles': roles, 'tool_shape': state['tool_shape'],
              'guard_hook_exercised': not classic and 'is a frozen geeky-plan planning artifact' in text,
              'history_protocol': history_protocol,
              'spawn_calls': request_spawn_calls(requests), 'raw_diagnostics': raw_diagnostics,
              'model_matrix': profile.get('model_matrix'), 'request_evidence': evidence,
              'model_capability_verified': False}
    report['native_plaintext_proxy'] = a.native_plaintext_proxy
    report['native_plaintext_contract'] = plaintext_contract
    report.update(cli_version=cli_version, known_diagnostics=diagnostics['known_diagnostics'],
                  unexpected_errors=diagnostics['unexpected_errors'],
                  count_policy=diagnostics['count_policy'], observed_counts=diagnostics['observed_counts'],
                  process_starts=['version', 'plugin-install', 'hook-catalogue', 'exec'])
    (a.output / 'native-summary.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report))
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
