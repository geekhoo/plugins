"""Resolve the vetted native guard's exact trust hash, then launch Codex.

The runner calls this only under its separately authorized -Launch path. Importing
the catalogue helper does not run the native probe's HTTP fixture or main().
"""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess


def capture_runtime_proof(codex, forbidden_root):
    version = subprocess.run([codex, '--version'], stdin=subprocess.DEVNULL,
        capture_output=True, text=True, encoding='utf-8', timeout=15)
    proof = {'root': str(forbidden_root), 'denial_verified': False,
             'error_type': None, 'winerror': None,
             'cli_version': version.stdout.strip().removeprefix('codex-cli '),
             'version_returncode': version.returncode, 'version_stderr': version.stderr,
             'version_stdout': version.stdout}
    try:
        list(forbidden_root.iterdir())
    except OSError as exc:
        proof.update(error_type=type(exc).__name__, winerror=getattr(exc, 'winerror', None))
        proof['denial_verified'] = isinstance(exc, PermissionError) and proof['winerror'] == 5
    return proof


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--codex', required=True)
    p.add_argument('--profile', type=Path, required=True)
    p.add_argument('--workspace', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--prompt-file', type=Path, required=True)
    p.add_argument('--forbidden-skill-root', type=Path, required=True)
    a = p.parse_args()
    profile = json.loads(a.profile.read_text(encoding='utf-8-sig'))
    spec = importlib.util.spec_from_file_location('native_catalogue', Path(__file__).with_name('native-probe.py'))
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    a.output.mkdir(parents=True, exist_ok=False)
    proof = capture_runtime_proof(a.codex, a.forbidden_skill_root)
    (a.output / 'runtime-denial-proof.json').write_text(json.dumps(proof, indent=2), encoding='utf-8')
    if (not proof['denial_verified'] or proof['cli_version'] != '0.164.0'
            or proof['version_returncode'] != 0 or proof['version_stderr'].strip()):
        raise RuntimeError('Runtime denial/version proof failed; no contestant launched')
    helper.install_local_plugin(a.codex, profile['codex_config_overrides'], a.output)
    telemetry_command = (profile.get('telemetry') or {}).get('hook_command')
    trust = helper.resolve_hook_trust(a.codex, profile['codex_config_overrides'], a.workspace, a.output,
                                      *([telemetry_command] if telemetry_command else []))
    command = [a.codex, '--no-daemon', 'exec', '--json', '--sandbox', 'danger-full-access',
               '--ignore-user-config', '--ignore-rules', '--strict-config', '--cd', str(a.workspace)]
    for override in profile['codex_config_overrides']:
        command += ['-c', override]
    command += ['-c', trust, a.prompt_file.read_text(encoding='utf-8-sig')]
    return subprocess.run(command, stdin=subprocess.DEVNULL).returncode


if __name__ == '__main__':
    raise SystemExit(main())
