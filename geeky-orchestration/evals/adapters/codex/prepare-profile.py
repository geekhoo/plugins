"""Prepare a Codex eval profile without starting Codex or reading credentials.

The report is a static access/configuration inventory. MXC runtime proof is CP2.
Only run-scoped HOME is written; CODEX_HOME remains the owner's signed-in home.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tomllib

WINDOWS = os.name == 'nt'


def venv_python(venv):
    return venv / ('Scripts/python.exe' if WINDOWS else 'bin/python')


def site_packages(venv):
    if WINDOWS:
        return venv / 'Lib/site-packages'
    return next(iter(sorted(venv.glob('lib/python*/site-packages'))), venv / 'lib/site-packages')


def cmdline(args):
    # Codex runs hook commands through the platform shell.
    return subprocess.list2cmdline(args) if WINDOWS else shlex.join(args)


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


def provider_catalog(base_catalog, slugs, context_window):
    """Catalog entries for models Codex does not know (a LiteLLM route).

    Built from the legacy gpt-5.5 entry, the one catalog shape without code mode: every tool is a
    JSON function (no freeform `exec` or `apply_patch`, whose input LiteLLM's bridges drop), and
    multi-agent v2 keeps the collaboration tools the workflows dispatch subagents with.
    """
    base = next(m for m in base_catalog['models'] if m.get('slug') == 'gpt-5.5')
    entries = []
    for slug in dict.fromkeys(slugs):
        entry = dict(base, slug=slug, display_name=slug, description='Eval model routed through LiteLLM',
                     apply_patch_tool_type=None, multi_agent_version='v2', upgrade=None, availability_nux=None,
                     additional_speed_tiers=[], service_tiers=[], priority=0,
                     context_window=context_window, max_context_window=context_window)
        entries.append(entry)
    return {'models': entries}


def prepare(plugin, home, codex_home, tools, profile, model, reasoning,
            worker_model=None, worker_reasoning=None, reviewer_reasoning=None,
            telemetry_node=None, telemetry_hook=None, provider=None):
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
    check('python', venv_python(tools / 'agent-py').is_file(), 'agent-py interpreter')
    if telemetry_hook:
        check('telemetry_hook', Path(telemetry_node).is_file() and Path(telemetry_hook).is_file(),
              {'node': str(telemetry_node), 'hook': str(telemetry_hook)})
    check('mcp_venv', (tools / 'geeky-mcp/pyvenv.cfg').is_file(), 'geeky-mcp bootstrap venv')
    report = {'ok': False, 'runtime_verified': False, 'checks': checks,
              'codex_config_overrides': [], 'extra_args': [], 'model': model,
              'reasoning': reasoning, 'worker_model': worker_model,
              'worker_reasoning': worker_reasoning,
              'model_matrix': {
                  'orchestrator': {'model': model, 'reasoning': reasoning},
                  'workers': {'model': worker_model, 'reasoning': worker_reasoning,
                              'scope': 'all-descendants'}},
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
    if telemetry_hook:
        # Plaintext reasoning summaries for the trace; the raw reasoning stays provider-encrypted.
        config['model_reasoning_summary'] = 'detailed'
    if provider:
        config['model_provider'] = 'litellm'
        config['model_providers'] = {'litellm': {
            'name': 'LiteLLM', 'base_url': provider['base_url'], 'env_key': provider['env_key'],
            'wire_api': 'responses', 'requires_openai_auth': False, 'supports_websockets': False}}
        # Hosted web search is an OpenAI server tool; a LiteLLM route cannot serve it.
        config['web_search'] = 'disabled'
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
    # The skills name Claude Code's built-in `general-purpose` type (web researchers, the PM review,
    # the planner fallback). Codex has no such role, so those dispatches failed; register one.
    general = role_dir / 'general-purpose.toml'
    agents['general-purpose'] = {'description': 'General-purpose subagent for research, review and other briefs (the Claude Code built-in type the skills name).',
                                 'config_file': str(general)}
    projections.append((general, {'name': 'general-purpose', 'developer_instructions':
        'You are a general-purpose subagent. Complete the brief you are given with the tools available and report the result precisely.'}))
    for role, data in projections:
        # Each child gets explicit worker settings and the complete registry/defaults
        # for its own descendants, independent of the orchestrator config layer.
        effort = reviewer_reasoning if reviewer_reasoning and role.stem in reviewer_roles else worker_reasoning
        layer = {'model': worker_model, 'model_reasoning_effort': effort,
                 'developer_instructions': data['developer_instructions'] + review_policy, 'agents': agents}
        if telemetry_hook:
            layer['model_reasoning_summary'] = 'detailed'
        rendered_role = '\n'.join(f'{k}={toml(v)}' for k, v in layer.items()) + '\n'
        tomllib.loads(rendered_role)
        role.write_text(rendered_role, encoding='utf-8')
    if WINDOWS:
        # The venv launcher cannot start inside MXC; use the venv's base interpreter.
        pyvenv = (tools / 'geeky-mcp/pyvenv.cfg').read_text()
        base = next(line.partition('=')[2].strip() for line in pyvenv.splitlines()
                    if line.partition('=')[0].strip() == 'home')
        interpreter = str(Path(base) / 'python.exe')
    else:
        interpreter = str(venv_python(tools / 'geeky-mcp'))
    bootstrap = home / 'mcp-bootstrap.py'
    shutil.copyfile(profile / 'mcp-bootstrap.py', bootstrap)
    # The bootstrap lives in granted run HOME and processes the venv's .pth files.
    config['mcp_servers'] = {'geeky': {'command': interpreter,
        'args': ['-u', str(bootstrap),
                 '--site-packages', str(site_packages(tools / 'geeky-mcp')),
                 '--server', str(plugin / 'mcp/server.py')], 'startup_timeout_sec': 120}}
    bridge = home / 'guard-bridge.py'
    shutil.copyfile(Path(__file__).with_name('guard-bridge.py'), bridge)
    command = cmdline([str(venv_python(tools / 'agent-py')),
        str(bridge), '--guard', str(plugin / 'hooks/guard-planning-contract.py')])
    config['hooks'] = {'PreToolUse': [{'matcher': 'Edit|Write|NotebookEdit|apply_patch',
        'hooks': [{'type': 'command', 'command': command, 'timeout': 5}]}]}
    telemetry = None
    if telemetry_hook:
        # Langfuse's Codex Stop hook; it uploads the rollout (and child threads) after each turn.
        tracer = home / 'langfuse-tracer.py'
        shutil.copyfile(Path(__file__).with_name('langfuse-tracer.py'), tracer)
        tracer.with_suffix('.json').write_text(json.dumps({'node': str(telemetry_node), 'hook': str(telemetry_hook)}),
                                               encoding='utf-8')
        telemetry_command = cmdline([str(venv_python(tools / 'agent-py')), str(tracer)])
        config['hooks']['Stop'] = [{'hooks': [{'type': 'command', 'command': telemetry_command, 'timeout': 600}]}]
        telemetry = {'hook_command': telemetry_command, 'reasoning_summary': 'detailed'}
    if provider:
        catalog = home / 'model-catalog.json'
        catalog.write_text(json.dumps(provider_catalog(json.loads(Path(provider['catalog_base']).read_text(encoding='utf-8')),
                                                       [model, worker_model], provider['context_window'])), encoding='utf-8')
        config['model_catalog_json'] = str(catalog)
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
    check('agent_registration', len(roles) == len(list((plugin / 'agents').glob('*.md'))) + 1 + bool(reviewer_reasoning), roles)
    check('hook_configuration', True, 'Warn guard bridge configured; runtime proof pending CP2.')
    report.update(ok=all(c['passed'] for c in checks), codex_config_overrides=overrides,
        extra_args=[], telemetry=telemetry,
        provider=({'name': 'litellm', 'base_url': provider['base_url'], 'env_key': provider['env_key'],
                   'context_window': provider['context_window'], 'tool_shape': 'classic-functions, multi-agent v2'}
                  if provider else None),
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
    p.add_argument('--reviewer-reasoning', choices=('minimal', 'low', 'medium', 'high', 'xhigh', 'max', 'ultra'),
                   help='Optional effort for reviewer roles; ordinary worker defaults remain independent.')
    p.add_argument('--telemetry-node', type=Path, help='Node.js 22+ that runs the Langfuse Stop hook.')
    p.add_argument('--telemetry-hook', type=Path, help="Langfuse Codex plugin's dist/index.mjs.")
    p.add_argument('--provider-base-url', help='Route models through this Responses endpoint (LiteLLM).')
    p.add_argument('--provider-env-key', help='Environment variable holding the endpoint key.')
    p.add_argument('--catalog-base', type=Path, help='`codex debug models` output to derive catalog entries from.')
    p.add_argument('--context-window', type=int, default=200000)
    a = p.parse_args()
    if a.provider_base_url and not (a.provider_env_key and a.catalog_base):
        p.error('--provider-base-url needs --provider-env-key and --catalog-base')
    if bool(a.telemetry_node) != bool(a.telemetry_hook):
        p.error('--telemetry-node and --telemetry-hook go together')
    result = prepare(a.plugin, a.home, a.codex_home, a.tools_dir, a.profile, a.model, a.reasoning,
                     a.worker_model, a.worker_reasoning, a.reviewer_reasoning,
                     a.telemetry_node, a.telemetry_hook,
                     {'base_url': a.provider_base_url, 'env_key': a.provider_env_key,
                      'catalog_base': a.catalog_base, 'context_window': a.context_window} if a.provider_base_url else None)
    a.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'ok': result['ok'], 'report': str(a.output)}))
    return 0 if result['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())
