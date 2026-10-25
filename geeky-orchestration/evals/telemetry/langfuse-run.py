"""Fetch one eval session's observations from Langfuse and summarize them.

Uses the v2 observations API (the only read path on Langfuse v4 events-only deployments), so it
works against both v3 and v4 servers. Credentials come from environment variables named on the
command line, never from arguments. Waits for asynchronous ingestion until the observation count
is stable. Exit 0 when the session has observations, 3 when none arrived before --wait ran out.

  python langfuse-run.py --session-id <id> --output <run>/langfuse.json [--full <run>/langfuse-observations.json]
"""
import argparse
import base64
import collections
import json
import os
from pathlib import Path
import sys
import time
import urllib.parse
import urllib.request

SUMMARY_FIELDS = 'core,basic,usage,metadata'
FULL_FIELDS = 'core,basic,usage,metadata,io,model'


def fetch_observations(base_url, auth, session_id, fields, limit=1000):
    observations, cursor = [], None
    while True:
        query = {'sessionId': session_id, 'limit': limit, 'fields': fields}
        if cursor:
            query['cursor'] = cursor
        request = urllib.request.Request(
            f"{base_url.rstrip('/')}/api/public/v2/observations?{urllib.parse.urlencode(query)}",
            headers={'Authorization': 'Basic ' + auth})
        with urllib.request.urlopen(request, timeout=60) as response:
            page = json.load(response)
        observations.extend(page.get('data', []))
        cursor = (page.get('meta') or {}).get('cursor')
        if not cursor or not page.get('data'):
            return observations


def truncated(metadata):
    """The Claude hook records {'truncated': true, ...} for any text it cut; scan nested metadata."""
    if isinstance(metadata, dict):
        return metadata.get('truncated') is True or any(truncated(v) for v in metadata.values())
    if isinstance(metadata, list):
        return any(truncated(v) for v in metadata)
    if isinstance(metadata, str) and metadata.startswith(('{', '[')):
        try:
            return truncated(json.loads(metadata))
        except ValueError:
            return False
    return False


def summarize(session_id, observations):
    types = collections.Counter(o.get('type') for o in observations)
    names = collections.Counter(o.get('name') for o in observations)
    usage = collections.Counter()
    for o in observations:
        for key, value in (o.get('usageDetails') or {}).items():
            if isinstance(value, (int, float)):
                usage[key] += value
    starts = sorted(o['startTime'] for o in observations if o.get('startTime'))
    return {
        'schema': 'geeky-eval.langfuse-session/1', 'session_id': session_id,
        'traces': len({o.get('traceId') for o in observations}),
        'observations': len(observations), 'by_type': dict(types),
        'generations': types.get('GENERATION', 0),
        'tool_calls': sum(n for name, n in names.items() if str(name).startswith('Tool:')) or types.get('TOOL', 0),
        'subagents': sum(n for name, n in names.items() if str(name).startswith(('Subagent:', 'Agent:'))),
        'environments': sorted({o.get('environment') for o in observations if o.get('environment')}),
        'usage_details': dict(usage),
        'truncated_observations': sum(1 for o in observations if truncated(o.get('metadata'))),
        'first_start': starts[0] if starts else None, 'last_start': starts[-1] if starts else None,
        'top_names': names.most_common(25),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--session-id', required=True)
    p.add_argument('--output', type=Path, help='summary JSON (stdout when omitted)')
    p.add_argument('--full', type=Path, help='also write every observation with input/output')
    p.add_argument('--wait', type=int, default=0, help='seconds to wait for ingestion to settle')
    p.add_argument('--public-key-env', default='LANGFUSE_PUBLIC_KEY')
    p.add_argument('--secret-key-env', default='LANGFUSE_SECRET_KEY')
    p.add_argument('--base-url-env', default='LANGFUSE_BASE_URL')
    a = p.parse_args()
    missing = [n for n in (a.public_key_env, a.secret_key_env, a.base_url_env) if not os.environ.get(n)]
    if missing:
        print(f'langfuse-run: missing environment variables: {", ".join(missing)}', file=sys.stderr)
        return 2
    base_url = os.environ[a.base_url_env]
    auth = base64.b64encode(f'{os.environ[a.public_key_env]}:{os.environ[a.secret_key_env]}'.encode()).decode()

    deadline = time.monotonic() + a.wait
    observations, previous = [], -1
    while True:
        observations = fetch_observations(base_url, auth, a.session_id, SUMMARY_FIELDS)
        # Settled: something arrived and two polls agree, or time is up.
        if (observations and len(observations) == previous) or time.monotonic() >= deadline:
            break
        previous = len(observations)
        time.sleep(10)
    summary = summarize(a.session_id, observations)
    text = json.dumps(summary, indent=2)
    if a.output:
        a.output.write_text(text + '\n', encoding='utf-8')
    print(text if not a.output else
          f"langfuse: session {a.session_id}: {summary['traces']} traces, {summary['observations']} observations "
          f"({summary['generations']} generations, {summary['tool_calls']} tool calls), "
          f"{summary['truncated_observations']} truncated")
    if a.full and observations:
        full = fetch_observations(base_url, auth, a.session_id, FULL_FIELDS)
        a.full.write_text(json.dumps(full, indent=1) + '\n', encoding='utf-8')
    return 0 if observations else 3


if __name__ == '__main__':
    sys.exit(main())
