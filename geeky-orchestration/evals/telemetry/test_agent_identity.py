import importlib.util
import json
from pathlib import Path
import shutil
import subprocess

import pytest

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location('agent_identity', HERE / 'agent_identity.py')
identity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(identity)


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
    assert row['SessionId'] == f'{family}-c0-wordstat-20261025T000000Z'


@pytest.mark.parametrize('agent_type,role', [
    ('geeky-orchestration:geeky-coder', 'coder'), ('code-reviewer', 'reviewer'),
    ('code-architect-reviewer', 'reviewer'), ('geeky-implement-orchestrator', 'orchestrator'),
    ('general-purpose', 'unknown'), ('coder mentioned only in a description', 'unknown')])
def test_native_roles_have_explicit_categories(agent_type, role):
    env = {'GEEKY_AGENT_FAMILY': 'claude-mxc-win', 'GEEKY_SESSION_ID': 'shared-run',
           'GEEKY_RUN_METADATA': '{"mock":"true","plugin_sha":"abc"}'}
    row = identity.actor_identity('native-agent-123', agent_type, parent_agent_id='parent', env=env)
    assert row['metadata']['agent_role'] == role
    assert row['metadata']['actor_scope'] == 'subagent'
    assert row['metadata']['parent_agent_id'] == 'parent'
    assert row['session_id'] == 'shared-run'
    assert row['user_id'].startswith('claude-mxc-win-')
    assert row['user_id'].endswith('-native-agent-123')


def test_root_and_agents_have_distinct_users_in_the_same_run_session():
    env = {'GEEKY_AGENT_FAMILY': 'claude-mxc-win', 'GEEKY_SESSION_ID': 'run'}
    root = identity.actor_identity('root-id', root=True, env=env)
    coder = identity.actor_identity('coder-id', 'geeky-coder', env=env)
    reviewer = identity.actor_identity('reviewer-id', 'code-reviewer', env=env)
    assert {r['session_id'] for r in [root, coder, reviewer]} == {'run'}
    assert len({r['user_id'] for r in [root, coder, reviewer]}) == 3
    assert root['trace_name'] == 'claude-mxc-win-orchestrator'
    assert root['metadata']['actor_scope'] == 'main'


def test_identity_bounds_are_ascii_safe_and_keep_collision_resistance():
    env = {'GEEKY_AGENT_FAMILY': 'claude-mxc-mac'}
    first = identity.actor_identity('x' * 400, 'geeky-coder', name='a' * 300, env=env)
    second = identity.actor_identity('x' * 399 + 'y', 'geeky-coder', name='a' * 300, env=env)
    assert len(first['user_id']) < 200 and first['user_id'].isascii()
    assert first['user_id'] != second['user_id']


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
    assert rows['root']['userId'] != rows['child']['userId']
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
