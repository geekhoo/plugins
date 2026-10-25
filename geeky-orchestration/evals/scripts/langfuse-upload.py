"""Upload a stored eval run's transcripts to Langfuse, host side (D101).

The contestant never sees Langfuse: after a run, this stages copies of the captured
transcripts (session.jsonl plus subagents/) in a temporary layout and feeds them to
the official Langfuse converters, i.e. the same Stop/SessionEnd hook scripts the
Langfuse Claude Code and Codex integrations run live. Trace ids are seeded from the
run folder, so uploading a run again updates the same traces instead of adding new ones.
The run folder is never modified except for langfuse.json (the outcome record).

  python langfuse-upload.py --install --tools-dir C:\\repos\\.eval-tools\\langfuse
  python langfuse-upload.py <run-folder> [--tools-dir ...]

Needs TRACE_TO_LANGFUSE=true, LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY (LANGFUSE_BASE_URL
optional), uv for the Claude converter and Node 22+ for the Codex converter. Credentials
are read from the environment by the converters only; nothing here prints them. The
upload fails open: the exit code is 0 and the outcome is in langfuse.json.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import urllib.request

# Pinned converters: Langfuse/Claude-Observability-Plugin hook and the Codex plugin package.
CLAUDE_HOOK_COMMIT = 'b5b7cc364996467e856dc17575b5674f4799ad87'
CLAUDE_HOOK_URL = ('https://raw.githubusercontent.com/langfuse/Claude-Observability-Plugin/'
                   f'{CLAUDE_HOOK_COMMIT}/hooks/langfuse_hook.py')
CODEX_PACKAGE = '@langfuse/codex-observability-plugin@0.4.2'


def claude_hook(tools):
    return tools / 'claude' / 'langfuse_hook.py'


def codex_entry(tools):
    return tools / 'codex' / 'node_modules' / '@langfuse' / 'codex-observability-plugin' / 'dist' / 'index.mjs'


def install(tools):
    hook = claude_hook(tools)
    hook.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(CLAUDE_HOOK_URL, timeout=60) as response:
        hook.write_bytes(response.read())
    npm = shutil.which('npm')
    if not npm:
        raise SystemExit('npm not found (Node 22+ is needed for the Codex converter)')
    (tools / 'codex').mkdir(parents=True, exist_ok=True)
    subprocess.run([npm, 'install', '--prefix', str(tools / 'codex'), '--no-fund', '--no-audit',
                    CODEX_PACKAGE], check=True)
    record = {'claude_hook': {'commit': CLAUDE_HOOK_COMMIT,
                              'sha256': hashlib.sha256(hook.read_bytes()).hexdigest()},
              'codex_package': CODEX_PACKAGE, 'codex_entry_exists': codex_entry(tools).is_file()}
    (tools / 'versions.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(record))


def labels(run, folder):
    """Tags and metadata shared by both harnesses; values are run facts, never secrets."""
    harness = run.get('harness')
    tags = ['geeky-eval', str(run.get('case')), str(harness), 'gateway:' + str(run.get('gateway') or 'direct')]
    if str(run.get('approach', '')).startswith('mock-agent'):
        tags.append('mock')
    oracle = run.get('oracle') or {}
    metadata = {'run_folder': folder.name, 'case': run.get('case'), 'harness': harness,
                'model': run.get('model'), 'reasoning': run.get('reasoning'),
                'plugin_sha': run.get('plugin_sha'), 'prompt_sha256': run.get('prompt_sha256'),
                'exit_reason': run.get('exit_reason'),
                'oracle': f"{oracle.get('passed')}/{oracle.get('collected')}" if oracle else None}
    return tags, {k: str(v) for k, v in metadata.items() if v is not None}


def stage_claude(folder, stage, session_id):
    """The hook reads <id>.jsonl and its subagents from the sibling <id>/subagents folder."""
    transcript = stage / f'{session_id}.jsonl'
    shutil.copyfile(folder / 'session.jsonl', transcript)
    if (folder / 'subagents').is_dir():
        shutil.copytree(folder / 'subagents', stage / session_id / 'subagents')
    return transcript


def stage_codex(folder, stage, session_id):
    """The converter finds subagent rollouts by walking <sessions>/YYYY/MM/DD around the main one."""
    day = stage / 'sessions' / '2000' / '01' / '01'
    day.mkdir(parents=True)
    transcript = day / f'rollout-{session_id}.jsonl'
    shutil.copyfile(folder / 'session.jsonl', transcript)
    for sub in sorted((folder / 'subagents').glob('*.jsonl')) if (folder / 'subagents').is_dir() else []:
        shutil.copyfile(sub, day / sub.name)
    return transcript


def converter(run, folder, stage, tools, environ):
    """Command, stdin payload and environment for the run's harness."""
    harness, session_id = run.get('harness'), run.get('session_id')
    tags, metadata = labels(run, folder)
    seed = f'geeky-eval:{folder.parent.name}:{folder.name}'
    env = dict(environ)
    if harness == 'claude-code':
        uv = shutil.which('uv', path=env.get('PATH'))
        if not uv:
            raise RuntimeError('uv not found (runs the Claude converter with its pinned langfuse SDK)')
        transcript = stage_claude(folder, stage, session_id)
        env.update(CC_LANGFUSE_STATE_DIR=str(stage / 'state'), CC_LANGFUSE_TRACE_SEED=seed,
                   CC_LANGFUSE_TRACE_TAGS=','.join(tags))
        # SessionEnd also emits the final turn, which Stop holds open for a later user row.
        payload = {'session_id': session_id, 'transcript_path': str(transcript),
                   'hook_event_name': 'SessionEnd', 'reason': 'other'}
        return [uv, 'run', '--quiet', '--script', str(claude_hook(tools))], payload, env
    if harness == 'codex':
        node = shutil.which('node', path=env.get('PATH'))
        if not node:
            raise RuntimeError('node not found (Node 22+ runs the Codex converter)')
        transcript = stage_codex(folder, stage, session_id)
        # CODEX_HOME points at the stage so no langfuse.json from the owner's homes applies.
        env.update(CODEX_HOME=str(stage), LANGFUSE_CODEX_TRACE_SEED=seed,
                   LANGFUSE_CODEX_TAGS=json.dumps(tags), LANGFUSE_CODEX_METADATA=json.dumps(metadata),
                   LANGFUSE_CODEX_FAIL_ON_ERROR='true')
        payload = {'session_id': session_id, 'transcript_path': str(transcript), 'hook_event_name': 'Stop'}
        return [node, str(codex_entry(tools))], payload, env
    raise RuntimeError(f'unsupported harness: {harness}')


def upload(folder, tools, environ=os.environ):
    run = json.loads((folder / 'run.json').read_text(encoding='utf-8-sig'))
    record = {'uploaded': False, 'harness': run.get('harness'), 'session_id': run.get('session_id'),
              'trace_seed': f'geeky-eval:{folder.parent.name}:{folder.name}',
              'base_url': environ.get('LANGFUSE_BASE_URL') or environ.get('LANGFUSE_CODEX_BASE_URL')}
    missing = [n for n in ('LANGFUSE_PUBLIC_KEY', 'LANGFUSE_SECRET_KEY') if not environ.get(n)]
    if environ.get('TRACE_TO_LANGFUSE') != 'true' or missing:
        record['skipped'] = 'TRACE_TO_LANGFUSE is not true' if environ.get('TRACE_TO_LANGFUSE') != 'true' \
            else 'missing ' + ', '.join(missing)
    elif not run.get('session_id') or not (folder / 'session.jsonl').is_file():
        record['skipped'] = 'run has no captured session.jsonl'
    else:
        with tempfile.TemporaryDirectory(prefix='langfuse-stage-') as temp:
            try:
                command, payload, env = converter(run, folder, Path(temp), tools, environ)
                result = subprocess.run(command, input=json.dumps(payload), env=env, text=True,
                                        capture_output=True, timeout=900, encoding='utf-8')
                record['returncode'] = result.returncode
                record['stderr_tail'] = result.stderr[-2000:]
                state_log = Path(temp) / 'state' / 'langfuse_hook.log'
                if state_log.is_file():
                    record['log_tail'] = [l for l in state_log.read_text(encoding='utf-8', errors='replace')
                                          .splitlines() if '[INFO]' in l or '[ERROR]' in l][-5:]
                sidecar = Path(payload['transcript_path'] + '.langfuse')
                if sidecar.is_file():
                    record['turns_uploaded'] = len(sidecar.read_text(encoding='utf-8').split())
                record['uploaded'] = result.returncode == 0
            except (RuntimeError, OSError, subprocess.SubprocessError) as error:
                record['error'] = f'{type(error).__name__}: {error}'
    (folder / 'langfuse.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('run_folder', nargs='?', type=Path)
    parser.add_argument('--tools-dir', type=Path, default=Path(r'C:\repos\.eval-tools\langfuse'))
    parser.add_argument('--install', action='store_true', help='Install the pinned converters into --tools-dir.')
    args = parser.parse_args()
    if args.install:
        install(args.tools_dir)
        return 0
    if not args.run_folder:
        parser.error('run_folder is required unless --install is given')
    record = upload(args.run_folder.resolve(), args.tools_dir)
    status = 'uploaded' if record['uploaded'] else 'NOT uploaded: ' + str(
        record.get('skipped') or record.get('error') or f"converter exit {record.get('returncode')}")
    print(f'langfuse: {status} ({args.run_folder / "langfuse.json"})', file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
