"""Offline worker matrix generation and CLI wiring; never starts Codex or MXC."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest

HERE = Path(__file__).resolve().parent
PLUGIN = HERE.parents[2]
spec = importlib.util.spec_from_file_location('worker_prepare_profile', HERE / 'prepare-profile.py')
profile = importlib.util.module_from_spec(spec)
spec.loader.exec_module(profile)


class WorkerConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.export = self.root / 'plugin'
        for part in ('agents', 'skills', 'templates', 'scripts', 'hooks', 'mcp'):
            shutil.copytree(PLUGIN / part, self.export / part,
                            ignore=shutil.ignore_patterns('__pycache__'))
        for part in ('AGENTS.md', 'geeky.manifest.json'):
            shutil.copyfile(PLUGIN / part, self.export / part)
        self.tools = self.root / 'tools'
        agent_python = self.tools / ('agent-py/Scripts/python.exe' if os.name == 'nt' else 'agent-py/bin/python')
        agent_python.parent.mkdir(parents=True)
        agent_python.touch()
        (self.tools / 'geeky-mcp').mkdir()
        (self.tools / 'geeky-mcp/pyvenv.cfg').write_text('home = C:\\Python314\n')
        self.signed = self.root / 'signed-in'
        self.signed.mkdir()
        # No credentials are read; this intentionally cannot be opened as a file.
        (self.signed / 'auth.json').mkdir()

    def assert_matrix(self, report, worker_model, worker_reasoning):
        self.assertTrue(report['ok'], report['checks'])
        self.assertFalse(report['runtime_verified'])
        self.assertEqual(report['worker_model'], worker_model)
        self.assertEqual(report['worker_reasoning'], worker_reasoning)
        self.assertEqual(report['model_matrix'], {
            'orchestrator': {'model': 'gpt-6.1-sol', 'reasoning': 'medium'},
            'workers': {'model': worker_model, 'reasoning': worker_reasoning,
                        'scope': 'all-descendants'}})
        config = tomllib.loads('\n'.join(report['codex_config_overrides']))
        self.assertEqual(config['model'], 'gpt-6.1-sol')
        self.assertEqual(config['model_reasoning_effort'], 'medium')
        agents = config['agents']
        self.assertEqual(agents['default_subagent_model'], worker_model)
        self.assertEqual(agents['default_subagent_reasoning_effort'], worker_reasoning)
        roles = {name: row for name, row in agents.items() if isinstance(row, dict)}
        self.assertEqual(set(roles), {p.stem for p in (self.export / 'agents').glob('*.md')})
        self.assertEqual(len(roles), 6)
        for name, row in roles.items():
            with self.subTest(role=name):
                layer = tomllib.loads(Path(row['config_file']).read_text(encoding='utf-8'))
                self.assertEqual(layer['model'], worker_model)
                self.assertEqual(layer['model_reasoning_effort'], worker_reasoning)
                # Every nested role retains exactly the same registry and defaults.
                self.assertEqual(layer['agents'], agents)
                projection = Path(row['config_file']).parents[1] / '.codex/agents' / (name + '.toml')
                projected = tomllib.loads(projection.read_text(encoding='utf-8'))
                self.assertEqual(layer['developer_instructions'], projected['developer_instructions'])

    def test_independent_workers_at_every_registered_depth(self):
        before = profile.digest(self.export)
        report = profile.prepare(self.export, self.root / 'home', self.signed, self.tools,
            HERE / 'profile', 'gpt-6.1-sol', 'medium', 'gpt-6-luna', 'max')
        self.assert_matrix(report, 'gpt-6-luna', 'max')
        self.assertEqual(profile.digest(self.export), before)

    def test_omitted_worker_settings_preserve_previous_matrix(self):
        report = profile.prepare(self.export, self.root / 'home', self.signed, self.tools,
            HERE / 'profile', 'gpt-6.1-sol', 'medium')
        self.assert_matrix(report, 'gpt-6.1-sol', 'medium')

    def test_worker_settings_default_independently(self):
        for i, (model, effort, expected_model, expected_effort) in enumerate([
                ('gpt-6-luna', None, 'gpt-6-luna', 'medium'),
                (None, 'max', 'gpt-6.1-sol', 'max')]):
            with self.subTest(worker_model=model, worker_reasoning=effort):
                report = profile.prepare(self.export, self.root / f'home-{i}', self.signed,
                    self.tools, HERE / 'profile', 'gpt-6.1-sol', 'medium', model, effort)
                self.assert_matrix(report, expected_model, expected_effort)

    def test_cli_records_requested_matrix(self):
        output = self.root / 'report.json'
        command = [sys.executable, str(HERE / 'prepare-profile.py'),
            '--plugin', str(self.export), '--home', str(self.root / 'home'),
            '--codex-home', str(self.signed), '--tools-dir', str(self.tools),
            '--profile', str(HERE / 'profile'), '--output', str(output),
            '--model', 'gpt-6.1-sol', '--reasoning', 'medium',
            '--worker-model', 'gpt-6-luna', '--worker-reasoning', 'max']
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        self.assertTrue(json.loads(result.stdout)['ok'])
        self.assert_matrix(json.loads(output.read_text(encoding='utf-8')), 'gpt-6-luna', 'max')

    def test_reviewers_have_independent_effort_and_architect_review_alias(self):
        before = profile.digest(self.export)
        report = profile.prepare(self.export, self.root / 'home', self.signed, self.tools,
            HERE / 'profile', 'gpt-6.1-sol', 'high', 'gpt-6.1-sol', 'medium', 'xhigh')
        self.assertTrue(report['ok'], report['checks'])
        self.assertEqual(report['model_matrix'], {
            'orchestrator': {'model': 'gpt-6.1-sol', 'reasoning': 'high'},
            'workers': {'model': 'gpt-6.1-sol', 'reasoning': 'medium', 'scope': 'all-descendants-except-reviewers'},
            'reviewers': {'model': 'gpt-6.1-sol', 'reasoning': 'xhigh',
                         'roles': ['code-reviewer', 'code-architect-reviewer'], 'scope': 'review-assignments'}})
        config = tomllib.loads('\n'.join(report['codex_config_overrides']))
        self.assertEqual(config['model_reasoning_effort'], 'high')
        agents = config['agents']
        self.assertEqual(agents['default_subagent_reasoning_effort'], 'medium')
        self.assertEqual(agents['default_subagent_model'], 'gpt-6.1-sol')
        self.assertIn('For plan sequencing review use code-architect-reviewer', config['developer_instructions'])
        for name, row in agents.items():
            if not isinstance(row, dict):
                continue
            with self.subTest(role=name):
                layer = tomllib.loads(Path(row['config_file']).read_text(encoding='utf-8'))
                effort = 'xhigh' if name in ('code-reviewer', 'code-architect-reviewer') else 'medium'
                self.assertEqual(layer['model_reasoning_effort'], effort)
                self.assertEqual(layer['model'], 'gpt-6.1-sol')
                self.assertEqual(layer['agents'], agents)
                self.assertIn('All plan semantic, task/phase and final domain review', layer['developer_instructions'])
        architect = tomllib.loads(Path(agents['code-architect']['config_file']).read_text())
        reviewer = tomllib.loads(Path(agents['code-architect-reviewer']['config_file']).read_text())
        self.assertEqual(architect['developer_instructions'], reviewer['developer_instructions'])
        self.assertEqual(profile.digest(self.export), before)

    def test_cli_accepts_reviewer_effort(self):
        output = self.root / 'review-report.json'
        command = [sys.executable, str(HERE / 'prepare-profile.py'),
            '--plugin', str(self.export), '--home', str(self.root / 'home'),
            '--codex-home', str(self.signed), '--tools-dir', str(self.tools),
            '--profile', str(HERE / 'profile'), '--output', str(output),
            '--model', 'gpt-6.1-sol', '--reasoning', 'high',
            '--worker-model', 'gpt-6.1-sol', '--worker-reasoning', 'medium',
            '--reviewer-reasoning', 'xhigh']
        subprocess.run(command, capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(output.read_text())['reviewer_reasoning'], 'xhigh')


if __name__ == '__main__':
    unittest.main()
