import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

HERE = Path(__file__).resolve().parent
PINS = json.loads((HERE / 'pins.json').read_text())
spec = importlib.util.spec_from_file_location('agent_identity', HERE / 'agent_identity.py')
identity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(identity)
sys.path.insert(0, str(HERE))
import process_events  # noqa: E402


@pytest.mark.parametrize('platform', ['win', 'linux', 'mac'])
@pytest.mark.parametrize('harness', ['codex', 'claude-code'])
def test_platform_naming_is_shared_and_sessions_are_unique(platform, harness):
    pwsh = shutil.which('pwsh')
    if not pwsh:
        pytest.skip('PowerShell is required for runner naming')
    script = HERE / 'telemetry.ps1'
    command = (f". '{str(script).replace(chr(39), chr(39)*2)}'; "
               f"Get-EvalTelemetryNaming -Harness {harness} -Platform {platform} "
               "-Case c0-wordstat -Stamp 20261025T000000Z | ConvertTo-Json -Compress")
    result = subprocess.run([pwsh, '-NoProfile', '-Command', command], capture_output=True, text=True, check=True)
    row = json.loads(result.stdout)
    family = f"{'codex' if harness == 'codex' else 'claude'}-mxc-{platform}"
    assert row['Environment'] == f'mxc-{platform}'
    assert row['Family'] == family
    assert row['SessionId'] == f'c0-wordstat/{harness}/20261025T000000Z'


def test_session_naming_rejects_a_slash_inside_a_field():
    pwsh = shutil.which('pwsh')
    if not pwsh:
        pytest.skip('PowerShell is required for runner naming')
    command = (f". '{str(HERE / 'telemetry.ps1').replace(chr(39), chr(39)*2)}'; "
               "Get-EvalTelemetryNaming -Harness codex -Platform win -Case 'c0/wordstat' -Stamp stamp")
    assert subprocess.run([pwsh, '-NoProfile', '-Command', command], capture_output=True, text=True).returncode != 0


@pytest.mark.parametrize('agent_type,role', [
    ('geeky-orchestration:geeky-coder', 'coder'), ('worker', 'coder'), ('code-reviewer', 'reviewer'),
    ('code-architect-reviewer', 'reviewer'), ('geeky-implement-orchestrator', 'orchestrator'),
    ('geeky-orchestration:code-architect', 'planner'),
    ('general-purpose', 'unknown'), ('coder mentioned only in a description', 'unknown')])
def test_native_roles_have_explicit_categories(agent_type, role):
    env = {'GEEKY_AGENT_FAMILY': 'claude-mxc-win', 'GEEKY_SESSION_ID': 'shared-run',
           'GEEKY_RUN_METADATA': '{"mock":"true","plugin_sha":"abc","harness":"claude-code"}'}
    row = identity.actor_identity('native-agent-123', agent_type, parent_agent_id='parent', env=env)
    assert row['metadata']['agent_role'] == role
    assert row['metadata']['actor_scope'] == 'subagent'
    assert row['metadata']['parent_agent_id'] == 'parent'
    assert row['session_id'] == 'shared-run'
    assert row['user_id'] == f'claude-code/{role}'
    assert row['trace_name'] == role


CASES = [('orchestrator', None, True), ('coder', 'geeky-coder', False), ('reviewer', 'code-reviewer', False),
         ('planner', 'code-architect', False), ('unknown', 'general-purpose', False)]


def run_env(harness):
    return {'GEEKY_AGENT_FAMILY': f"{'codex' if harness == 'codex' else 'claude'}-mxc-win",
            'GEEKY_SESSION_ID': f'c2-ds-full/{harness}/20261105T000000Z-abcd1234',
            'GEEKY_RUN_METADATA': json.dumps({'harness': harness, 'run_group_id': f'c2-ds-full/{harness}/20261105T000000Z-abcd1234',
                                              'configured_model': 'model-x', 'provider': 'provider-y'})}


def codex_rows(env):
    node = shutil.which('node')
    if not node:
        pytest.skip('Node is required for the Codex adapter')
    helper = (HERE / 'codex-identity.mjs').resolve().as_uri()
    actors = [{'sessionId': f'thread-{expected}', 'agentNickname': 'Bohr', **({} if root else {'isSubagentThread': True, 'agentRole': agent_type})}
              for expected, agent_type, root in CASES]
    code = f"""import {{agentIdentity}} from {json.dumps(helper)};
console.log(JSON.stringify({json.dumps(actors)}.map(meta => agentIdentity(meta, {{config: {{tags: []}}}}, {json.dumps(env)}))));"""
    return json.loads(subprocess.run([node, '--input-type=module', '-e', code], capture_output=True, text=True, check=True).stdout)


def assert_new_identity(row, harness, role, native):
    assert row['session'] == f'c2-ds-full/{harness}/20261105T000000Z-abcd1234'
    assert row['user'] == f'{harness}/{role}'
    assert row['trace'] == role
    metadata = row['metadata']
    assert metadata['agent_id'] == native and metadata['agent_role'] == role
    assert metadata['agent_family'] == ('codex-mxc-win' if harness == 'codex' else 'claude-mxc-win')
    assert metadata['run_group_id'] == row['session']
    assert metadata['identity_schema'] == 'geeky-eval.agent-identity/2'
    assert metadata['agent_user_id'].endswith(native)
    assert metadata['configured_model'] == 'model-x' and metadata['provider'] == 'provider-y'
    for value in (row['session'], row['user'], row['trace']):
        assert native not in value and 'model-x' not in value and 'provider-y' not in value and 'bohr' not in value.lower()


@pytest.mark.parametrize('role,agent_type,root', CASES)
def test_claude_identity_is_exact(role, agent_type, root):
    row = identity.actor_identity(f'thread-{role}', agent_type, root=root, name='Bohr', env=run_env('claude-code'))
    assert_new_identity({'session': row['session_id'], 'user': row['user_id'], 'trace': row['trace_name'], 'metadata': row['metadata']},
                        'claude-code', role, f'thread-{role}')


def test_codex_identity_is_exact():
    for (role, _, _), row in zip(CASES, codex_rows(run_env('codex'))):
        assert_new_identity({'session': row['sessionId'], 'user': row['userId'], 'trace': row['traceName'], 'metadata': row['metadata']},
                            'codex', role, f'thread-{role}')


def test_harness_defaults_when_run_metadata_omits_it():
    assert identity.actor_identity('a', root=True, env={})['user_id'] == 'claude-code/orchestrator'
    assert codex_rows({})[0]['userId'] == 'codex/orchestrator'


ROLE_TYPES = ['geeky-orchestrator', 'geeky-implement-orchestrator', 'geeky-orchestration:geeky-coder', 'geeky-coder', 'worker',
              'code-reviewer', 'code-architect-reviewer', 'architect-reviewer', 'reviewer', 'plan-reviewer', 'impl-reviewer',
              'code-architect', 'geeky-orchestration:code-architect', 'code-explorer', 'general-purpose', 'default', '', None]


def test_claude_and_codex_role_maps_agree():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node is required for the Codex adapter')
    helper = (HERE / 'codex-identity.mjs').resolve().as_uri()
    code = f"""import {{roleFor}} from {json.dumps(helper)};
console.log(JSON.stringify({json.dumps(ROLE_TYPES)}.map(type => roleFor(type, false))));"""
    roles = json.loads(subprocess.run([node, '--input-type=module', '-e', code], capture_output=True, text=True, check=True).stdout)
    assert roles == [identity.role_for(agent_type) for agent_type in ROLE_TYPES]


def test_tracer_roles_differ_from_the_process_trace_only_for_types_it_calls_planner():
    # Generic types have no planner evidence in native metadata, so the tracers keep them unknown.
    differ = {str(t).rsplit(':', 1)[-1] for t in ROLE_TYPES if identity.role_for(t) != process_events.role_for(t)}
    assert differ == {'code-explorer', 'general-purpose'}


def test_planner_mapping_rests_on_a_real_plugin_agent_type():
    plugin = HERE.parents[1]
    assert (plugin / 'agents/code-architect.md').exists()
    assert 'planner** subagent (`geeky-orchestration:code-architect` type' in (plugin / 'skills/plan-review/SKILL.md').read_text(encoding='utf-8')
    assert not (plugin / 'agents/planner.md').exists()


def test_root_and_agents_share_a_session_and_keep_threads_in_metadata():
    env = {'GEEKY_AGENT_FAMILY': 'claude-mxc-win', 'GEEKY_SESSION_ID': 'run'}
    root = identity.actor_identity('root-id', root=True, env=env)
    coder = identity.actor_identity('coder-id', 'geeky-coder', env=env)
    other = identity.actor_identity('other-id', 'geeky-coder', env=env)
    assert {r['session_id'] for r in [root, coder, other]} == {'run'}
    assert coder['user_id'] == other['user_id'] == 'claude-code/coder'
    assert coder['metadata']['agent_id'] != other['metadata']['agent_id']
    assert root['trace_name'] == 'orchestrator'
    assert root['metadata']['actor_scope'] == 'main'


def test_identity_bounds_are_ascii_safe_and_keep_collision_resistance():
    env = {'GEEKY_AGENT_FAMILY': 'claude-mxc-mac'}
    first = identity.actor_identity('x' * 400, 'geeky-coder', name='a' * 300, env=env)['metadata']
    second = identity.actor_identity('x' * 399 + 'y', 'geeky-coder', name='a' * 300, env=env)['metadata']
    assert len(first['agent_user_id']) < 200 and first['agent_user_id'].isascii()
    assert first['agent_user_id'] != second['agent_user_id'] and first['agent_id'] != second['agent_id']


def resolve_codex(tmp_path, identity_source=None):
    pwsh, node = shutil.which('pwsh'), shutil.which('node')
    if not pwsh or not node:
        pytest.skip('PowerShell and Node are required')
    dist = tmp_path / f"tools/langfuse/codex-tracing/{PINS['codex_plugin']['version']}/dist"
    dist.mkdir(parents=True)
    (dist / 'index.geeky.mjs').write_text('// fixture')
    (dist / 'codex-identity.mjs').write_bytes(identity_source if identity_source is not None else (HERE / 'codex-identity.mjs').read_bytes())
    script = tmp_path / 'resolve.ps1'
    script.write_text("""param($TelemetryPath, $Tools)
$ErrorActionPreference = 'Stop'
. $TelemetryPath
$t = Resolve-EvalTelemetry -Harness codex -ToolsDir $Tools -Case c2-ds-full -Stamp 20261105T000000Z-abcd1234 -PluginSha abcdef1234567 -Model model-x -Provider provider-y
$t | Select-Object SessionId, EnvArgs, Tags, Record | ConvertTo-Json -Depth 6
""", encoding='utf-8')
    env = {k: v for k, v in os.environ.items() if not k.startswith('LANGFUSE_')}
    env.update(TRACE_TO_LANGFUSE='true', LANGFUSE_PUBLIC_KEY='pk-offline', LANGFUSE_SECRET_KEY='sk-offline', LANGFUSE_BASE_URL='http://fixture.invalid')
    return subprocess.run([pwsh, '-NoProfile', '-File', str(script), str(HERE / 'telemetry.ps1'), str(tmp_path / 'tools')],
                          capture_output=True, text=True, encoding='utf-8', env=env)


def test_resolved_run_environment_carries_the_new_identity(tmp_path):
    done = resolve_codex(tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr
    row = json.loads(done.stdout)
    session = 'c2-ds-full/codex/20261105T000000Z-abcd1234'
    assert row['SessionId'] == row['Record']['session_id'] == row['Record']['metadata']['run_group_id'] == session
    assert f'GEEKY_SESSION_ID={session}' in row['EnvArgs']
    assert 'GEEKY_TRACE_NAME=orchestrator' in row['EnvArgs']
    assert 'LANGFUSE_CODEX_USER_ID=codex/orchestrator' in row['EnvArgs']
    assert any(arg.startswith('GEEKY_AGENT_FAMILY=codex-mxc-') for arg in row['EnvArgs'])
    assert row['Record']['user_id'] == 'codex/orchestrator' and row['Record']['user_id_policy'] == 'harness-role'
    assert row['Record']['trace_name'] == 'orchestrator'
    assert row['Record']['agent_family'].startswith('codex-mxc-') and row['Record']['environment'].startswith('mxc-')
    assert {'identity:agent-v2', 'harness:codex', 'model:model-x', 'provider:provider-y'} <= set(row['Tags'])
    assert any(tag.startswith('agent-family:') for tag in row['Tags'])


def test_a_stale_installed_identity_module_fails_closed(tmp_path):
    done = resolve_codex(tmp_path, b'// the module from an older install')
    assert done.returncode != 0
    assert 'Stale' in done.stdout + done.stderr


@pytest.mark.parametrize('telemetry,expected', [
    ("[pscustomobject]@{SessionId='c0/codex/stamp';KeyNames=@('A','B','C');StateDir=$null;Record=[ordered]@{agent_family='codex-mxc-win';user_id='codex/orchestrator';metadata=@{run_group_id='c0/codex/group'}}}",
     ('c0/codex/stamp', 'codex/orchestrator')),
    ("[pscustomobject]@{KeyNames=@('A','B','C');StateDir=$null;Record=[ordered]@{agent_family='codex-mxc-win';user_id='old-user';metadata=@{run_group_id='codex-mxc-win-c0-stamp'}}}",
     ('codex-mxc-win-c0-stamp', 'old-user'))])
def test_save_reads_the_langfuse_session_in_both_forms_and_keeps_the_native_id_apart(tmp_path, telemetry, expected):
    pwsh = shutil.which('pwsh')
    if not pwsh:
        pytest.skip('PowerShell is required')
    fake = tmp_path / 'fake-python.ps1'
    fake.write_text("param([Parameter(ValueFromRemainingArguments)]$Arguments)\n"
                    "Add-Content -LiteralPath $env:T_CALLS -Value $Arguments[[Array]::IndexOf($Arguments, '--session-id') + 1]\n"
                    "$global:LASTEXITCODE = 3\n", encoding='utf-8')
    script = tmp_path / 'save.ps1'
    script.write_text(f"""param($TelemetryPath, $Fake, $OutDir)
$ErrorActionPreference = 'Stop'
. $TelemetryPath
$env:T_CALLS = Join-Path $OutDir 'calls.txt'
$t = {telemetry}
Save-EvalTelemetry -Telemetry $t -SessionId 'native-thread' -OutDir $OutDir -Python $Fake -WaitSec 0
$t.Record | ConvertTo-Json -Depth 5
""", encoding='utf-8')
    done = subprocess.run([pwsh, '-NoProfile', '-File', str(script), str(HERE / 'telemetry.ps1'), str(fake), str(tmp_path)],
                          capture_output=True, text=True, encoding='utf-8')
    assert done.returncode == 0, done.stdout + done.stderr
    record = json.loads(done.stdout)
    assert (tmp_path / 'calls.txt').read_text().splitlines() == [expected[0]]
    assert (record['session_id'], record['user_id']) == expected
    assert record['native_session_id'] == 'native-thread'


def test_codex_adapter_preserves_actor_and_parent_metadata_without_prompt_guessing():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node is required for the Codex adapter')
    helper = (HERE / 'codex-identity.mjs').resolve().as_uri()
    code = f"""import {{agentIdentity}} from {json.dumps(helper)};
const env={{GEEKY_AGENT_FAMILY:'codex-mxc-linux',GEEKY_SESSION_ID:'shared-run',GEEKY_RUN_METADATA:'{{"mock":"true"}}'}};
const root=agentIdentity({{sessionId:'root'}},{{config:{{tags:[]}}}},env);
const child=agentIdentity({{sessionId:'child',isSubagentThread:true,agentRole:'geeky-coder',agentNickname:'Coder A',parentThreadId:'root',agentPath:'/root/coder'}},{{config:{{tags:[]}},parentObservation:{{otelSpan:{{spanContext:()=>({{traceId:'trace',spanId:'dispatch'}})}}}}}},env);
console.log(JSON.stringify({{root,child}}));"""
    rows = json.loads(subprocess.run([node, '--input-type=module', '-e', code], capture_output=True, text=True, check=True).stdout)
    assert (rows['root']['userId'], rows['child']['userId']) == ('codex/orchestrator', 'codex/coder')
    assert rows['child']['metadata']['agent_name'] == 'Coder A'
    assert rows['child']['sessionId'] == rows['root']['sessionId'] == 'shared-run'
    assert rows['child']['metadata']['agent_role'] == 'coder'
    assert rows['child']['metadata']['parent_agent_id'] == 'root'
    assert rows['child']['metadata']['parent_trace_id'] == 'trace'
    assert rows['child']['metadata']['parent_observation_id'] == 'dispatch'


def test_codex_derived_patch_rejects_unknown_upstream_source(tmp_path):
    node = shutil.which('node')
    if not node:
        pytest.skip('Node is required for the Codex adapter')
    source, output = tmp_path / 'original.mjs', tmp_path / 'derived.mjs'
    source.write_text('unexpected upstream source')
    result = subprocess.run([node, str(HERE / 'patch-codex-tracer.mjs'), str(source), str(output)], capture_output=True, text=True)
    assert result.returncode != 0
    assert not output.exists()
    assert source.read_text() == 'unexpected upstream source'


def test_codex_seed_carrier_is_not_reported_as_a_dispatch_parent():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node is required for the Codex adapter')
    helper = (HERE / 'codex-identity.mjs').resolve().as_uri()
    code = f"""import {{agentIdentity}} from {json.dumps(helper)};
const env={{GEEKY_AGENT_FAMILY:'codex-mxc-win'}};
const ctx={{config:{{}},parentSpanContext:{{traceId:'seeded-trace',spanId:'placeholder'}}}};
console.log(JSON.stringify({{seed:agentIdentity({{sessionId:'root'}},ctx,env),external:agentIdentity({{sessionId:'root'}},{{...ctx,attached:true}},env)}}));"""
    rows = json.loads(subprocess.run([node, '--input-type=module', '-e', code], capture_output=True, text=True, check=True).stdout)
    assert 'parent_trace_id' not in rows['seed']['metadata']
    assert rows['external']['metadata']['parent_trace_id'] == 'seeded-trace'
