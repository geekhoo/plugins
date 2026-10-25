"""Prepare a Codex eval profile without starting Codex or reading credentials.

The report is a static access/configuration inventory. MXC runtime proof is CP2.
Only run-scoped HOME is written; CODEX_HOME remains the owner's signed-in home.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib


def toml(value):
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return '[' + ', '.join(toml(v) for v in value) + ']'
    if isinstance(value, dict):
        return '{' + ', '.join(f'{toml(k)} = {toml(v)}' for k, v in value.items()) + '}'
    raise TypeError(type(value).__name__)


def digest(root):
    h = hashlib.sha256()
    for p in sorted(root.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts:
            h.update(p.relative_to(root).as_posix().encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def prepare(plugin, home, codex_home, tools, profile, model, reasoning,
            worker_model=None, worker_reasoning=None, reviewer_reasoning=None, litellm_base_url=None):
    worker_model = model if worker_model is None else worker_model
    worker_reasoning = reasoning if worker_reasoning is None else worker_reasoning
    reviewer_roles = ['code-reviewer', 'code-architect-reviewer']
    review_policy = (
        '\n\nEvaluation role routing: ordinary task workers use the configured worker settings. '
        'All plan semantic, task/phase and final domain review assignments must use code-reviewer. '
        'For plan sequencing review use code-architect-reviewer, which preserves the canonical '
        'code-architect instructions with reviewer effort; use code-architect for architecture '
        'production tasks. Give each reviewer its concrete scope and required verdict. '
        'Do not use default/task roles for review assignments or override these registered settings.'
        if reviewer_reasoning else '')
    checks = []
    def check(name, passed, detail):
        checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

    check('home_separate', home.resolve() != codex_home.resolve(),
          'Run HOME and signed-in CODEX_HOME must differ.')
    # Inspect only named non-secret contamination paths, never auth or home listings.
    contaminants = [name for name in ('AGENTS.md', 'AGENTS.override.md', 'hooks.json',
        'agents', 'memories', 'rules')
        if (codex_home / name).exists()]
    skill_root = codex_home / 'skills'
    if skill_root.exists():
        contaminants.extend('skills/' + p.name for p in skill_root.iterdir()
                            if p.name not in ('.system', '.codex-system-skills.marker'))
    defaults = tomllib.loads((profile / 'config.toml').read_text(encoding='utf-8-sig'))
    check('cached_context_disabled',
          defaults.get('skills', {}).get('bundled', {}).get('enabled') is False
          and defaults.get('plugins', {}).get('_default', {}).get('enabled') is False
          and set(defaults.get('plugins', {})) == {'_default'},
          'Bundled skills and cached plugins disabled; user config ignored by runner.')
    check('dedicated_codex_home', not contaminants,
          {'unexpected_non_auth_paths': contaminants, 'config_ignored': True})
    leaks = [p.relative_to(plugin).as_posix() for p in plugin.rglob('*')
             if p.is_file() and (p.name == 'spec.md' or p.match('oracle_*.py')
                                 or 'evals' in p.relative_to(plugin).parts)]
    check('no_oracle_export', not leaks, leaks)
    required = ['AGENTS.md', 'geeky.manifest.json', 'skills', 'agents', 'templates',
                'scripts/sync-agents.py', 'hooks/guard-planning-contract.py', 'mcp/server.py']
    check('export_components', all((plugin / p).exists() for p in required), required)
    check('fresh_home', not home.exists(), str(home))
    check('python', (tools / 'agent-py/Scripts/python.exe').is_file(), 'agent-py interpreter')
    check('mcp_venv', (tools / 'geeky-mcp/pyvenv.cfg').is_file(), 'geeky-mcp bootstrap venv')
    report = {'ok': False, 'runtime_verified': False, 'checks': checks,
              'codex_config_overrides': [], 'extra_args': [], 'model': model,
              'reasoning': reasoning, 'worker_model': worker_model,
              'worker_reasoning': worker_reasoning,
              'model_matrix': {
                  'orchestrator': {'model': model, 'reasoning': reasoning},
                  'workers': {'model': worker_model, 'reasoning': worker_reasoning,
                              'scope': 'all-descendants'}},
              'gateway': 'litellm' if litellm_base_url else 'direct',
              'profile_sha256': digest(profile)}
    if reviewer_reasoning:
        report['reviewer_reasoning'] = reviewer_reasoning
        report['model_matrix']['workers']['scope'] = 'all-descendants-except-reviewers'
        report['model_matrix']['reviewers'] = {
            'model': worker_model, 'reasoning': reviewer_reasoning,
            'roles': reviewer_roles, 'scope': 'review-assignments'}
    if not all(c['passed'] for c in checks):
        return report

    home.mkdir(parents=True)
    skills = home / '.agents/skills'
    skills.mkdir(parents=True)
    # Copy complete skill trees with references/assets, preserving relative paths.
    for skill in sorted((plugin / 'skills').iterdir()):
        if skill.is_dir():
            shutil.copytree(skill, skills / skill.name)
    sync = plugin / 'scripts/sync-agents.py'
    result = subprocess.run([sys.executable, str(sync), '--project-root', str(home),
                             '--targets', 'codex', '--json'], text=True, capture_output=True)
    check('agent_projection', result.returncode == 0, result.stdout.strip())
    if result.returncode:
        return report
    config = defaults
    config['model'] = model
    config['model_reasoning_effort'] = reasoning
    if litellm_base_url:
        # Route every thread through the owner's LiteLLM proxy. Only the variable name is
        # configured; Codex reads the key from the environment. inherit=all would pass it to
        # the agent's shell (verified on 0.164.0), so exclude it there explicitly.
        config['model_provider'] = 'litellm'
        config['model_providers'] = {'litellm': {'name': 'LiteLLM', 'base_url': litellm_base_url,
            'env_key': 'LITELLM_PROXY_API_KEY', 'wire_api': 'responses'}}
        config['shell_environment_policy']['exclude'] = ['LITELLM_PROXY_API_KEY']
    shutil.copyfile(plugin / 'AGENTS.md', home / 'AGENTS.md')
    config['developer_instructions'] = (plugin / 'AGENTS.md').read_text(encoding='utf-8') + review_policy
    # Windows native skill discovery uses KnownFolder HOME, ignoring env HOME.
    # A local marketplace is the supported alternate discovery route. Only this
    # pinned export is enabled; native runtime may cache it in dedicated CODEX_HOME.
    market = home / 'marketplace'
    market_manifest = market / '.claude-plugin/marketplace.json'
    market_manifest.parent.mkdir(parents=True)
    shim = market / 'plugins/geeky-orchestration'
    shutil.copytree(plugin, shim)
    native_manifest = shim / '.codex-plugin/plugin.json'
    native_manifest.parent.mkdir(exist_ok=True)
    native_manifest.write_text(json.dumps({'name': 'geeky-orchestration',
        'version': '0.3.0-eval.' + digest(plugin)[:12], 'skills': './skills/',
        'mcpServers': {}, 'hooks': []}), encoding='utf-8')
    market_manifest.write_text(json.dumps({'name': 'geeky-eval', 'plugins': [
        {'name': 'geeky-orchestration', 'source': './plugins/geeky-orchestration'}]}), encoding='utf-8')
    config['marketplaces'] = {'geeky-eval': {'source_type': 'local', 'source': str(market)}}
    config['plugins']['geeky-orchestration@geeky-eval'] = {'enabled': True}
    agents = config.setdefault('agents', {})
    agents.update(enabled=True, default_subagent_model=worker_model,
                  default_subagent_reasoning_effort=worker_reasoning,
                  max_depth=3, max_concurrent_threads_per_session=8)
    role_dir = home / 'roles'
    role_dir.mkdir()
    projections = []
    for projection in sorted((home / '.codex/agents').glob('*.toml')):
        data = tomllib.loads(projection.read_text(encoding='utf-8'))
        # A config_file is a config layer, not a standalone agent definition.
        # name/description from sync-agents belong in the registry, not that layer.
        role = role_dir / projection.name
        agents[data['name']] = {'description': data['description'], 'config_file': str(role)}
        projections.append((role, data))
    if reviewer_reasoning:
        architect = next(data for _, data in projections if data['name'] == 'code-architect')
        review_role = role_dir / 'code-architect-reviewer.toml'
        agents['code-architect-reviewer'] = {
            'description': 'Plan sequencing reviewer using the canonical code-architect instructions.',
            'config_file': str(review_role)}
        projections.append((review_role, architect))
    for role, data in projections:
        # Each child gets explicit worker settings and the complete registry/defaults
        # for its own descendants, independent of the orchestrator config layer.
        effort = reviewer_reasoning if reviewer_reasoning and role.stem in reviewer_roles else worker_reasoning
        layer = {'model': worker_model, 'model_reasoning_effort': effort,
                 'developer_instructions': data['developer_instructions'] + review_policy, 'agents': agents}
        rendered_role = '\n'.join(f'{k}={toml(v)}' for k, v in layer.items()) + '\n'
        tomllib.loads(rendered_role)
        role.write_text(rendered_role, encoding='utf-8')
    pyvenv = (tools / 'geeky-mcp/pyvenv.cfg').read_text()
    base = next(line.partition('=')[2].strip() for line in pyvenv.splitlines()
                if line.partition('=')[0].strip() == 'home')
    interpreter = str(Path(base) / 'python.exe')
    bootstrap = home / 'mcp-bootstrap.py'
    shutil.copyfile(profile / 'mcp-bootstrap.py', bootstrap)
    # The bootstrap lives in granted run HOME and processes the venv's .pth files.
    config['mcp_servers'] = {'geeky': {'command': interpreter,
        'args': ['-u', str(bootstrap),
                 '--site-packages', str(tools / 'geeky-mcp/Lib/site-packages'),
                 '--server', str(plugin / 'mcp/server.py')], 'startup_timeout_sec': 120}}
    bridge = home / 'guard-bridge.py'
    shutil.copyfile(Path(__file__).with_name('guard-bridge.py'), bridge)
    command = subprocess.list2cmdline([str(tools / 'agent-py/Scripts/python.exe'),
        str(bridge), '--guard', str(plugin / 'hooks/guard-planning-contract.py')])
    config['hooks'] = {'PreToolUse': [{'matcher': 'Edit|Write|NotebookEdit|apply_patch',
        'hooks': [{'type': 'command', 'command': command, 'timeout': 5}]}]}
    # Parent CLI overrides register all roles explicitly; projection folders alone do not.
    overrides = [f'{k}={toml(v)}' for k, v in config.items()]
    rendered = '\n'.join(overrides) + '\n'
    tomllib.loads(rendered)
    (home / 'eval.config.toml').write_text(rendered, encoding='utf-8')
    copied = {p.relative_to(skills).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in skills.rglob('*') if p.is_file()}
    source = {p.relative_to(plugin / 'skills').as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in (plugin / 'skills').rglob('*') if p.is_file()}
    check('full_skills', copied == source, sorted(p.name for p in skills.iterdir()))
    roles = sorted(k for k, v in agents.items() if isinstance(v, dict))
    check('agent_registration', len(roles) == len(list((plugin / 'agents').glob('*.md'))) + bool(reviewer_reasoning), roles)
    check('hook_configuration', True, 'Warn guard bridge configured; runtime proof pending CP2.')
    report.update(ok=all(c['passed'] for c in checks), codex_config_overrides=overrides,
        extra_args=[],
        profile_sha256=hashlib.sha256((digest(profile) + digest(home)).encode()).hexdigest(),
        reachability={'claude': required, 'codex': required,
                      'runtime_proof': 'UNVERIFIED until checkpoint 2'},
        capability_notes=['sync-agents omits canonical model/tool restrictions for Codex; generated role layers apply the worker model/reasoning and preserve nested defaults/registrations. Runtime inheritance requires native probe evidence.',
            'Windows KnownFolder ignores HOME for skills; run-home local marketplace enables only pinned export. Its native cache is in dedicated CODEX_HOME.',
            'Shell edits bypass guard as in Claude.',
            'Codex patch warnings are wrapped as additionalContext; Claude plain stdout warnings may be invisible (O19).'])
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('plugin', 'home', 'codex-home', 'tools-dir', 'profile', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--model', required=True)
    p.add_argument('--reasoning', required=True)
    p.add_argument('--worker-model', help='Subagent model at every depth; defaults to --model.')
    p.add_argument('--worker-reasoning', help='Subagent effort at every depth; defaults to --reasoning.')
    p.add_argument('--litellm-base-url', help='OpenAI-compatible LiteLLM base URL (ending /v1); omit for direct auth.')
    p.add_argument('--reviewer-reasoning', choices=('minimal', 'low', 'medium', 'high', 'xhigh', 'max', 'ultra'),
                   help='Optional effort for reviewer roles; ordinary worker defaults remain independent.')
    a = p.parse_args()
    result = prepare(a.plugin, a.home, a.codex_home, a.tools_dir, a.profile, a.model, a.reasoning,
                     a.worker_model, a.worker_reasoning, a.reviewer_reasoning, a.litellm_base_url)
    a.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'ok': result['ok'], 'report': str(a.output)}))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
