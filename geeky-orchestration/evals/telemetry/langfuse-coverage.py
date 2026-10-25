"""Check which harness points one eval session reached, from its Langfuse observations.

Works on both tracers' output: the Claude hook ("Tool: <name>", "Subagent: ...", "LLM Call") and
the Codex tracer ("<tool name>", "skill:<name>", "Codex Subagent Turn", "LLM"). Each point is
required or informational; exit 0 when every required point is hit, 1 otherwise, 3 when the
session has no observations. See cases/c0-wordstat/spec.md for why each point matters.

  python langfuse-coverage.py --session-id <id> [--output coverage.json]
  python langfuse-coverage.py --observations langfuse-observations.json
"""
import argparse
import base64
import importlib.util
import json
import os
from pathlib import Path
import re
import sys

STAGES = ('spec-research', 'geeky-plan', 'plan-review', 'geeky-implement', 'impl-review')
GATES = ('validate-planning-folder', 'validate-task-schema', 'validate-kanban', 'check-dod', 'check-commit')
SPAWN_TOOLS = {'Tool: Agent', 'Tool: Task', 'spawn_agent'}
SHELL_TOOLS = {'Tool: Bash', 'Tool: PowerShell', 'exec', 'exec_command', 'shell', 'local_shell'}
EDIT_TOOLS = {'Tool: Write', 'Tool: Edit', 'Tool: MultiEdit', 'Tool: NotebookEdit', 'apply_patch'}


def decoded(value):
    """Tracers store input/output as JSON text; decode once so nested keys are reachable."""
    if isinstance(value, str) and value[:1] in '{["':
        try:
            return json.loads(value)
        except ValueError:
            return value
    return value


def text(value):
    value = decoded(value)
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)


def is_subagent_container(o):
    metadata = decoded(o.get('metadata')) or {}
    return ((o.get('type') == 'AGENT' and isinstance(metadata, dict) and metadata.get('actor_scope') == 'subagent')
            or (o.get('type') == 'SPAN' and str(o.get('name', '')).startswith('Subagent:'))
            or o.get('name') == 'Codex Subagent Turn')


def skill_read_text(observation):
    raw = decoded(observation.get('input'))
    if observation.get('name') == 'Tool: Read' and isinstance(raw, dict):
        return str(raw.get('file_path', ''))
    source = (raw.get('cmd') or raw.get('command')) if isinstance(raw, dict) else raw
    if not isinstance(source, str) or not re.search(r'\b(?:Get-Content|cat|type)\b', source, re.I):
        return text(raw)
    # Resolve only one literal, non-interpolated binding from this same command.
    # This is evidence normalization, never shell execution or cross-call guessing.
    bindings = {}
    for match in re.finditer(r'''\$(\w+)\s*=\s*(['"])([^'"\r\n$]+)\2''', source):
        bindings.setdefault(match.group(1).lower(), []).append(match.group(3))
    expanded = source
    for name, values in bindings.items():
        if len(values) == 1:
            expanded = re.sub(r'\$' + re.escape(name) + r'(?=[/\\]SKILL\.md)',
                              lambda _: values[0], expanded, flags=re.I)
    return expanded


def coverage(observations):
    by_id = {o['id']: o for o in observations}

    def inside_subagent(o):
        seen, parent = set(), by_id.get(o.get('parentObservationId'))
        while parent and parent['id'] not in seen:
            if is_subagent_container(parent):
                return True
            seen.add(parent['id'])
            parent = by_id.get(parent.get('parentObservationId'))
        return False

    tools = [o for o in observations if o.get('type') == 'TOOL']
    spawns = [o for o in tools if o.get('name') in SPAWN_TOOLS]
    shells = [o for o in tools if o.get('name') in SHELL_TOOLS or str(o.get('name', '')).startswith('skill:')]
    # Codex's exec input is JavaScript; commands sit in string literals with escaped newlines.
    shell_text = [(o, re.sub(r'\\[nrt]', '\n', text(o.get('input')))) for o in shells]
    generations = [o for o in observations if o.get('type') == 'GENERATION']
    points = []

    def point(name, hits, required=True, detail=''):
        hits = list(hits)
        points.append({'point': name, 'required': required, 'hit': bool(hits), 'count': len(hits),
                       'example': hits[0]['id'] if hits else None, 'detail': detail})

    for stage in STAGES:
        # Claude: the Skill tool; Codex: the tracer's skill:<name> tool, or any read of the skill file.
        pattern = re.compile(r'(?:^|[:"/\\])%s(?:"|[/\\]SKILL\.md)' % re.escape(stage))
        point(f'stage:{stage}', (o for o in tools if o.get('name') == f'skill:{stage}'
                                 or (o.get('name') == 'Tool: Skill' and pattern.search(text(o.get('input'))))
                                 or pattern.search(skill_read_text(o)) and f'skills/{stage}/SKILL.md' in skill_read_text(o).replace('\\\\', '/').replace('\\', '/')))
    point('subagents', spawns)
    # geeky-implement makes the main thread the orchestrator; delegating it to geeky-implement-orchestrator
    # is the agent's choice (Claude usually does, Codex C0 attempt 5 did not), so nesting is informational.
    point('nested_subagents', (o for o in spawns if inside_subagent(o)), required=False,
          detail='a subagent dispatched another (implement orchestrator -> coder/reviewer)')
    point('role:geeky-coder', (o for o in spawns if 'geeky-coder' in text(o.get('input'))))
    point('role:code-reviewer', (o for o in spawns if 'code-reviewer' in text(o.get('input'))))
    mcp = [o for o in tools if re.search(r'mcp__geeky|geeky__|^mcp[_.:]', str(o.get('name', '')))]
    gate_hits = {g: [o for o, t in shell_text if g in t or g.replace('-', '_') in t]
                    + [o for o in mcp if g.replace('-', '_') in str(o.get('name', '')) or g in str(o.get('name', ''))]
                 for g in GATES}
    point('gates', (o for hits in gate_hits.values() for o in hits),
          detail=', '.join(f'{g}={len(h)}' for g, h in gate_hits.items()))
    for gate, hits in gate_hits.items():
        point(f'gate:{gate}', hits, required=False)
    point('mcp_tools', mcp, required=False, detail='gates may run as scripts instead')
    point('pytest', (o for o, t in shell_text if re.search(r'\bpytest\b', t)))
    point('git_commit', (o for o, t in shell_text if re.search(r'\bgit\b[^\n;|]{0,80}?\bcommit\b', t)))
    point('file_edits', (o for o in tools if o.get('name') in EDIT_TOOLS or '*** Begin Patch' in text(o.get('input'))))

    def has_reasoning(o):
        out = decoded(o.get('output'))
        return isinstance(out, dict) and bool(out.get('thinking') or out.get('reasoning'))
    point('reasoning_summaries', (o for o in generations if has_reasoning(o)),
          detail='thinking (Claude) or reasoning summary (Codex) on generations')
    point('token_usage', (o for o in generations if any(isinstance(v, (int, float)) and v > 0
                                                       for v in (o.get('usageDetails') or {}).values())))
    encrypted = [o for o in spawns + [t for t in tools if t.get('name') in ('send_message', 'followup_task')]
                 if 'gAAAAA' in text(o.get('input'))]
    point('encrypted_handoffs', encrypted, required=False,
          detail='Codex inter-agent payloads the provider encrypted (no plaintext exists)')
    return points


def load_fetcher():
    spec = importlib.util.spec_from_file_location('langfuse_run', Path(__file__).with_name('langfuse-run.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument('--session-id')
    source.add_argument('--observations', type=Path, help='observations saved by langfuse-run.py --full')
    p.add_argument('--output', type=Path)
    p.add_argument('--public-key-env', default='LANGFUSE_PUBLIC_KEY')
    p.add_argument('--secret-key-env', default='LANGFUSE_SECRET_KEY')
    p.add_argument('--base-url-env', default='LANGFUSE_BASE_URL')
    a = p.parse_args()
    if a.observations:
        observations = json.loads(a.observations.read_text(encoding='utf-8'))
    else:
        missing = [n for n in (a.public_key_env, a.secret_key_env, a.base_url_env) if not os.environ.get(n)]
        if missing:
            print(f'langfuse-coverage: missing environment variables: {", ".join(missing)}', file=sys.stderr)
            return 2
        auth = base64.b64encode(f'{os.environ[a.public_key_env]}:{os.environ[a.secret_key_env]}'.encode()).decode()
        fetcher = load_fetcher()
        observations = fetcher.fetch_observations(os.environ[a.base_url_env], auth, a.session_id, fetcher.FULL_FIELDS)
    if not observations:
        print('langfuse-coverage: no observations', file=sys.stderr)
        return 3
    points = coverage(observations)
    missed = [x['point'] for x in points if x['required'] and not x['hit']]
    report = {'schema': 'geeky-eval.harness-coverage/1', 'session_id': a.session_id,
              'observations': len(observations), 'complete': not missed, 'missed': missed, 'points': points}
    if a.output:
        a.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    width = max(len(x['point']) for x in points)
    for x in points:
        mark = 'HIT ' if x['hit'] else ('MISS' if x['required'] else '--  ')
        print(f"{mark} {x['point']:<{width}} {x['count']:>5}{'' if x['required'] else '  (info)'}"
              + (f"  {x['detail']}" if x['detail'] else ''))
    print(f"coverage: {'complete' if not missed else 'missing ' + ', '.join(missed)} ({len(observations)} observations)")
    return 0 if not missed else 1


if __name__ == '__main__':
    sys.exit(main())
