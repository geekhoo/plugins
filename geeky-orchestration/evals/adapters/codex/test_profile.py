"""Offline profile and native patch/guard contract checks; no Codex or MXC launch."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest

HERE = Path(__file__).resolve().parent
PLUGIN = HERE.parents[2]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


P = load('prepare_profile', 'prepare-profile.py')
G = load('guard_bridge', 'guard-bridge.py')


class ProfileTests(unittest.TestCase):
    def test_toml_roundtrip(self):
        value = {'path': 'C:\\dir with spaces\\a.py', 'list': [True, 120],
                 'hooks': {'PreToolUse': [{'matcher': 'Edit|Write'}]}}
        self.assertEqual(tomllib.loads('value=' + P.toml(value))['value'], value)

    def test_contaminated_home_fails_without_reading_auth(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            auth = root / 'signed-in'
            auth.mkdir()
            (auth / 'auth.json').mkdir()  # Any attempt to read this as a file fails.
            (auth / 'AGENTS.md').write_text('unrelated instructions')
            report = P.prepare(PLUGIN, root / 'home', auth, root / 'tools',
                               HERE / 'profile', 'gpt-6.1-sol', 'high')
            self.assertFalse(report['ok'])
            self.assertFalse((root / 'home').exists())
            check = next(c for c in report['checks'] if c['name'] == 'dedicated_codex_home')
            self.assertFalse(check['passed'])

    def test_complete_profile_registers_agents_and_preserves_skills(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            export = root / 'plugin'
            import shutil
            for part in ('agents', 'skills', 'templates', 'scripts', 'hooks', 'mcp'):
                shutil.copytree(PLUGIN / part, export / part,
                                ignore=shutil.ignore_patterns('__pycache__'))
            for part in ('AGENTS.md', 'geeky.manifest.json'):
                shutil.copyfile(PLUGIN / part, export / part)
            tools = root / 'tools'
            # Codex login creates these automatically; disable loading, never delete them.
            signed = root / 'signed-in'
            (signed / 'skills/.system').mkdir(parents=True)
            (signed / 'plugins/cache').mkdir(parents=True)
            (signed / 'config.toml').write_text('[projects]\n')
            (tools / 'agent-py/Scripts').mkdir(parents=True)
            (tools / 'agent-py/Scripts/python.exe').touch()
            (tools / 'geeky-mcp').mkdir()
            (tools / 'geeky-mcp/pyvenv.cfg').write_text('home = C:\\Python314\n')
            report = P.prepare(export, root / 'home', signed, tools,
                               HERE / 'profile', 'gpt-6.1-sol', 'high')
            self.assertTrue(report['ok'], report['checks'])
            self.assertFalse(report['runtime_verified'])
            cfg = tomllib.loads('\n'.join(report['codex_config_overrides']))
            self.assertEqual(cfg['model'], 'gpt-6.1-sol')
            self.assertEqual(cfg['model_reasoning_effort'], 'high')
            self.assertNotIn('model_instructions_file', cfg)
            self.assertFalse(cfg['skills']['bundled']['enabled'])
            self.assertFalse(cfg['plugins']['_default']['enabled'])
            self.assertTrue(cfg['plugins']['geeky-orchestration@geeky-eval']['enabled'])
            shim = root / 'home/marketplace/plugins/geeky-orchestration'
            manifest = json.loads((shim / '.codex-plugin/plugin.json').read_text())
            self.assertEqual(manifest['hooks'], [])
            self.assertEqual(manifest['mcpServers'], {})
            self.assertIn('geeky-coder', cfg['agents'])
            role = tomllib.loads(Path(cfg['agents']['geeky-coder']['config_file']).read_text())
            self.assertEqual(set(role), {'developer_instructions', 'model',
                                         'model_reasoning_effort', 'agents'})
            self.assertEqual(role['model'], 'gpt-6.1-sol')
            self.assertEqual(role['model_reasoning_effort'], 'high')
            self.assertEqual(role['agents'], cfg['agents'])
            self.assertTrue(Path(cfg['mcp_servers']['geeky']['args'][1]).is_file())
            self.assertEqual(report['extra_args'], [])
            self.assertEqual(report['gateway'], 'direct')
            self.assertNotIn('model_provider', cfg)
            routed = P.prepare(export, root / 'home-litellm', signed, tools, HERE / 'profile',
                               'zen/gpt-6.1-sol', 'high', litellm_base_url='https://litellm.example/v1')
            self.assertTrue(routed['ok'], routed['checks'])
            self.assertEqual(routed['gateway'], 'litellm')
            routed_cfg = tomllib.loads('\n'.join(routed['codex_config_overrides']))
            self.assertEqual(routed_cfg['model_provider'], 'litellm')
            self.assertEqual(routed_cfg['model_providers']['litellm'], {'name': 'LiteLLM',
                'base_url': 'https://litellm.example/v1', 'env_key': 'LITELLM_PROXY_API_KEY',
                'wire_api': 'responses'})
            self.assertEqual(routed_cfg['shell_environment_policy'],
                             {'inherit': 'all', 'exclude': ['LITELLM_PROXY_API_KEY']})

    def test_non_system_skill_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            signed = root / 'signed-in'
            (signed / 'skills/unrelated').mkdir(parents=True)
            report = P.prepare(PLUGIN, root / 'home', signed, root / 'tools',
                               HERE / 'profile', 'gpt-6.1-sol', 'high')
            self.assertFalse(report['ok'])
            check = next(c for c in report['checks'] if c['name'] == 'dedicated_codex_home')
            self.assertIn('skills/unrelated', check['detail']['unexpected_non_auth_paths'])


class GuardTests(unittest.TestCase):
    def test_patch_paths_include_moves_and_deletes(self):
        payload = {'tool_input': {'command': '\n'.join([
            '*** Update File: docs/spec/tasks/T1-test.md',
            '*** Move to: docs/spec/tasks/T2-test.md',
            '*** Delete File: docs/spec/draft.md'])}}
        self.assertEqual(len(G.paths(payload)), 3)

    def test_frozen_patch_warns_and_notes_do_not(self):
        for filename, warning in [('draft.md', True), ('tasks/T1-thing.md', True),
                                  ('tasks/T1-thing.notes.md', False), ('kanban.md', False)]:
            result = subprocess.run([sys.executable, str(HERE / 'guard-bridge.py'),
                '--guard', str(PLUGIN / 'hooks/guard-planning-contract.py')],
                input=json.dumps({'tool_name': 'apply_patch', 'tool_input': {
                    'command': '*** Update File: docs/spec/' + filename}}),
                text=True, capture_output=True, check=True)
            self.assertEqual(bool(result.stdout.strip()), warning)
            if warning:
                output = json.loads(result.stdout)['hookSpecificOutput']
                self.assertEqual(output['hookEventName'], 'PreToolUse')
                self.assertIn('frozen', output['additionalContext'])


if __name__ == '__main__':
    unittest.main()
