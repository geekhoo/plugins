"""Preserve only the selected Codex rollout and its proven descendant threads."""
import argparse
import json
from pathlib import Path
import shutil


def capture(sessions, thread_id, destination):
    index = {}
    for path in sorted(Path(sessions).rglob('rollout-*.jsonl')):
        try:
            with path.open(encoding='utf-8-sig') as stream:
                row = json.loads(stream.readline())
            if row.get('type') != 'session_meta':
                continue
            meta = row['payload']
            identity = meta.get('id') or meta.get('session_id')
            if identity:
                index.setdefault(identity, []).append((path, meta))
        except (OSError, ValueError, KeyError):
            continue
    if len(index.get(thread_id, [])) != 1:
        raise ValueError('Missing or ambiguous main rollout: ' + thread_id)
    selected = {thread_id}
    while True:
        before = len(selected)
        for identity, records in index.items():
            for _, meta in records:
                source = meta.get('source')
                spawn = source.get('subagent', {}).get('thread_spawn', {}) if isinstance(source, dict) else {}
                parent = meta.get('parent_thread_id') or spawn.get('parent_thread_id')
                if parent in selected:
                    selected.add(identity)
        if len(selected) == before:
            break
    if any(len(index[identity]) != 1 for identity in selected):
        raise ValueError('Ambiguous descendant rollout')
    destination = Path(destination)
    if (destination / 'subagents').exists() or (destination / 'rollout-manifest.json').exists():
        raise ValueError('Refusing to mix rollout captures from different attempts')
    destination.mkdir(parents=True, exist_ok=True)
    records = []
    for identity in sorted(selected):
        source, meta = index[identity][0]
        target = destination / ('session.jsonl' if identity == thread_id else f'subagents/rollout-{identity}.jsonl')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        records.append({'thread_id': identity, 'parent_thread_id': meta.get('parent_thread_id'),
                        'file': target.relative_to(destination).as_posix()})
    report = {'main_thread_id': thread_id, 'threads': records}
    (destination / 'rollout-manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sessions', required=True, type=Path)
    parser.add_argument('--thread-id', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(capture(args.sessions, args.thread_id, args.output)))
