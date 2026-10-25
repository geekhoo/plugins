"""Replay pieces of Claude C0 run 3's last request against ant-claude to find the content-filter trigger."""
import json, os, sys, urllib.request, urllib.error
SESSION = '/home/user/plugins/geeky-orchestration/evals/baselines/c0-wordstat/20261025T020134Z/session.jsonl'
BASE = os.environ['LITELLM_PROXY_URL'].rstrip('/')

def messages():
    """Main-thread messages in order, each flattened to (role, text)."""
    out = []
    for line in open(SESSION, encoding='utf-8'):
        r = json.loads(line)
        if r.get('type') not in ('user', 'assistant') or r.get('isSidechain'):
            continue
        c = r['message']['content']
        if isinstance(c, str):
            text = c
        else:
            parts = []
            for b in c:
                t = b.get('type')
                if t == 'text': parts.append(b['text'])
                elif t == 'tool_use': parts.append(f"[tool_use {b['name']}] {json.dumps(b['input'])}")
                elif t == 'tool_result':
                    x = b.get('content'); parts.append('[tool_result] ' + (x if isinstance(x, str) else json.dumps(x)))
                elif t == 'thinking' and b.get('thinking'): parts.append('[thinking] ' + b['thinking'])
            text = '\n'.join(parts)
        if text.strip():
            out.append((r['message']['role'], text))
    return out

def ask(text):
    body = json.dumps({'model': 'ant-claude', 'max_tokens': int(os.environ.get('MAXTOK', '8')),
                       'messages': [{'role': 'user', 'content': text}]}).encode()
    req = urllib.request.Request(BASE + '/v1/messages', body, {'content-type': 'application/json',
        'authorization': 'Bearer ' + os.environ['LITELLM_PROXY_API_KEY'], 'anthropic-version': '2023-06-01'})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=300))
        out = ''.join(b.get('text', '') for b in r.get('content', []))
        return r.get('stop_reason'), out[:120], r.get('usage', {}).get('input_tokens')
    except urllib.error.HTTPError as e:
        return f'HTTP {e.code}', e.read().decode()[:300], None

def render(msgs):
    return '\n\n'.join(f'### {role}\n{text}' for role, text in msgs)

if __name__ == '__main__':
    msgs = messages()
    cmd = sys.argv[1]
    if cmd == 'count':
        for i, (role, text) in enumerate(msgs): print(i, role, len(text), text[:90].replace('\n', ' '))
    elif cmd == 'range':      # probe messages[a:b]
        a, b = int(sys.argv[2]), int(sys.argv[3])
        print(f'[{a}:{b}]', *ask(render(msgs[a:b])))
    elif cmd == 'file':
        print(sys.argv[2], *ask(open(sys.argv[2], encoding='utf-8').read()))
