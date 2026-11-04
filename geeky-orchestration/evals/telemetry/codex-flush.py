"""Replay a Codex rollout through the Langfuse tracer after the run.

Usage: <python> codex-flush.py <node> <tracer .mjs> <payload.json>
The tracer reads its Stop payload from stdin; the MXC host closes the workload's stdin, so the payload
travels as a file. Without a turn_id the tracer skips a turn that never completed (a run killed or timed
out mid-turn), so the last started turn is named as the one that stopped. The rollout's .langfuse sidecar
keeps already-delivered turns from being re-sent.

A Stop hook whose flush timed out can still deliver every span while leaving no sidecar, and a replay
then stores the same ids a second time. So before replaying, each unmarked flush attempt in the rollout's
.langfuse-attempts ledger is checked against Langfuse: a turn is marked delivered only if every span id
that attempt recorded is readable. Anything less, including an unreachable Langfuse, replays as before:
a late duplicate is recoverable (langfuse-run.py counts unique ids), a lost turn is not.
"""
import base64
import http.client
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request

SETTLE_SECONDS = 120
POLL_SECONDS = 10


def log(message):
    print(f'codex-flush: {message}', flush=True)


def last_started_turn(transcript_path):
    turn_id = None
    with open(transcript_path, encoding='utf-8') as f:
        for line in f:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            item = row.get('payload') or {}
            if row.get('type') == 'event_msg' and item.get('type') == 'task_started' and item.get('turn_id'):
                turn_id = item['turn_id']
    return turn_id


def unmarked_attempts(transcript_path):
    """Attempts whose turns the sidecar does not record yet; flush outcomes go to the log for evidence."""
    try:
        with open(f'{transcript_path}.langfuse', encoding='utf-8') as f:
            marked = set(f.read().split())
    except FileNotFoundError:
        marked = set()
    try:
        with open(f'{transcript_path}.langfuse-attempts', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        return []
    attempts = []
    for line in lines:
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if entry.get('event') == 'flush':
            log(f"hook flush ok={entry.get('ok')} elapsed_ms={entry.get('elapsed_ms')} error={entry.get('error')}")
        elif entry.get('event') == 'attempt' and entry.get('span_ids'):
            turns = [t for t in entry.get('turn_ids') or [] if t and t not in marked]
            if turns:
                attempts.append({'turns': turns, 'span_ids': set(entry['span_ids'])})
    return attempts


def reader_from_environment(env):
    """Reads the session's observation ids over the exporter's route (direct, no proxy), or None if unconfigured."""
    session_id = env.get('GEEKY_SESSION_ID')
    keys = [env.get(f'LANGFUSE_CODEX_{suffix}') or env.get(f'LANGFUSE_{suffix}')
            for suffix in ('PUBLIC_KEY', 'SECRET_KEY', 'BASE_URL')]
    if not session_id or not all(keys):
        return None
    public_key, secret_key, base_url = keys
    auth = base64.b64encode(f'{public_key}:{secret_key}'.encode()).decode()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def read_ids():
        ids, cursor = set(), None
        while True:
            query = {'sessionId': session_id, 'limit': 1000, 'fields': 'core'}
            if cursor:
                query['cursor'] = cursor
            request = urllib.request.Request(
                f"{base_url.rstrip('/')}/api/public/v2/observations?{urllib.parse.urlencode(query)}",
                headers={'Authorization': 'Basic ' + auth})
            with opener.open(request, timeout=60) as response:
                page = json.load(response)
            ids.update(row['id'] for row in page.get('data', []) if row.get('id'))
            cursor = (page.get('meta') or {}).get('cursor')
            if not cursor or not page.get('data'):
                return ids

    return read_ids


def mark_delivered_turns(transcript_path, read_ids, settle_seconds=SETTLE_SECONDS, poll_seconds=POLL_SECONDS,
                         sleep=time.sleep, clock=time.monotonic):
    """Append turns that Langfuse holds in full to the sidecar. Ingestion is asynchronous, so unconfirmed
    attempts are polled until settle_seconds; whatever is still unconfirmed is left for the tracer to replay."""
    attempts = unmarked_attempts(transcript_path)
    if not attempts:
        return []
    if read_ids is None:
        log('unmarked flush attempt, but no session id or Langfuse credentials to check it; replaying')
        return []
    deadline = clock() + settle_seconds
    delivered = []
    while True:
        try:
            ids = read_ids()
        except (OSError, ValueError, http.client.HTTPException) as error:
            log(f'Langfuse read failed ({type(error).__name__})')
            ids = set()
        for attempt in [a for a in attempts if a['span_ids'] <= ids]:
            attempts.remove(attempt)
            delivered.extend(attempt['turns'])
        if not attempts or clock() >= deadline:
            break
        sleep(poll_seconds)
    if delivered:
        # The tracer splits this file on a bare \n; a \r\n would hide the mark from it.
        with open(f'{transcript_path}.langfuse', 'a', encoding='utf-8', newline='\n') as f:
            f.writelines(f'{turn}\n' for turn in delivered)
        log(f'{len(delivered)} turn(s) already delivered by the hook; not replayed')
    if attempts:
        log(f'{sum(len(a["turns"]) for a in attempts)} turn(s) not fully readable after {settle_seconds}s; replaying')
    return delivered


def main(argv, settle_seconds=SETTLE_SECONDS):
    node, tracer, payload_path = argv[1:4]
    with open(payload_path, encoding='utf-8') as f:
        payload = json.load(f)
    if not payload.get('turn_id'):
        turn_id = last_started_turn(payload['transcript_path'])
        if turn_id:
            payload['turn_id'] = turn_id
    mark_delivered_turns(payload['transcript_path'], reader_from_environment(os.environ), settle_seconds)
    node_options = ['--preserve-symlinks-main', '--preserve-symlinks'] if sys.platform == 'win32' else []
    return subprocess.run([node, *node_options, tracer], input=json.dumps(payload).encode()).returncode


if __name__ == '__main__':
    sys.exit(main(sys.argv))
