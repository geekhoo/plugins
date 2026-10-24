"""Conservative process facts from captured Codex own-history records.

Supports delegated planning/review and implementation, literal PowerShell board
insertions and native commit results. Does not execute shell text, decrypt prompts,
or infer task verdicts from a generic PASS. Unsupported mappings remain missing.
"""
import hashlib
import json
import re


def lane_insertions(command):
    """Literal lane-header replacements, in execution order (including Ready)."""
    pattern = r"\.Replace\('## (Backlog|Ready|In Progress|In Review|Done|Blocked)',\s*\"## \1`n([^\"]+)\"\)"
    result = []
    for match in re.finditer(pattern, command):
        for task, phase in re.findall(r'- \[[ x]\] (T\d+)\b[^`\n]*?\(phase (\d+)\)', match[2], re.I):
            result.append((task, match[1], 'P' + phase))
    return result


def review_result(message):
    clean = message.replace('**', '')
    verdicts = re.findall(r'\b(T\d+):\s*(PASS|FAIL|NEEDS FIXES)\b', clean)
    phases = set(re.findall(r'\bPhase[ -]+(\d+)\b', clean, re.I))
    if not verdicts or len(phases) != 1:
        raise ValueError('Review requires per-task verdicts and one explicit phase')
    tasks = {}
    for task, verdict in verdicts:
        if task in tasks and tasks[task] != verdict:
            raise ValueError('Conflicting task verdicts')
        tasks[task] = verdict
    if len(set(tasks.values())) != 1:
        raise ValueError('Mixed per-task review verdicts require separate mapping')
    passed = all(v == 'PASS' for v in tasks.values())
    if passed and re.search(r'NEEDS FIXES|\bFAIL\b', clean):
        raise ValueError('Conflicting overall review verdict')
    return sorted(tasks, key=lambda t: int(t[1:])), 'P' + phases.pop(), 'pass' if passed else 'fail', passed and 'READY TO ADVANCE' in clean


def task_commit_bindings(command, committed, done):
    """Bind native commit subjects to literal -m variables with Tasks trailers.

    Equal list lengths or commit order never establishes task identity. Only the
    last literal assignment to the actual -m variable is supported here.
    """
    messages = {}
    for call in re.finditer(r'\bgit\s+commit\s+-m\s+\$(\w+)\b', command):
        assignments = list(re.finditer(r'\$' + re.escape(call[1]) + r'\s*=\s*', command[:call.start()]))
        value = re.match(r'"([^"$]*)"\s*;', command[assignments[-1].end():]) if assignments else None
        if not value:
            raise ValueError('Task commit requires a literal commit-message assignment')
        message = value[1].replace('`n', '\n').replace('`r', '\r')
        subject = message.splitlines()[0]
        trailers = re.findall(r'^Tasks:\s*(T\d+)\s*$', message, re.M)
        if len(trailers) != 1 or subject in messages:
            raise ValueError('Task commit requires one unique subject and single-task trailer')
        messages[subject] = trailers[0]
    bindings = {}
    for prefix, subject in committed:
        task = messages.get(subject.strip())
        if task not in done or task in bindings:
            raise ValueError('Ambiguous task to commit mapping')
        bindings[task] = (prefix, subject.strip())
    if set(bindings) != set(done) or len(messages) != len(committed):
        raise ValueError('Ambiguous task to commit mapping')
    return bindings


def dispatched_task(thread, dispatch):
    """Visible dispatch name plus own notes write and product FileChange."""
    args = json.loads(dispatch['payload']['arguments'])
    named = set(re.findall(r'(?:^|_)(T\d+)(?=_|$)', args.get('task_name', ''), re.I))
    named = {t.upper() for t in named}
    notes, product, proofs = set(), False, []
    for row in thread['rows']:
        p = row.get('payload', {}); item = p.get('item', {})
        if p.get('type') != 'item_completed' or item.get('status') != 'completed':
            continue
        paths = []
        if item.get('type') == 'FileChange':
            changes = item.get('changes', {})
            if not isinstance(changes, dict):
                continue
            paths = [path.replace('\\', '/') for path, change in changes.items() if change.get('type') not in ('delete', 'remove')]
            product |= any('/docs/' not in path and path.endswith('.py') for path in paths)
        elif item.get('type') == 'CommandExecution' and item.get('exit_code') == 0:
            cmd = item.get('command', '')
            cmd = cmd[-1] if isinstance(cmd, list) else cmd
            paths = re.findall(r'(?:Set-Content|Add-Content)\s+(?:-Encoding\s+\w+\s+)?([^;\s]+\.notes\.md)', cmd)
        for path in paths:
            match = re.search(r'/tasks/(T\d+)-[^/]+\.notes\.md$', path)
            if match:
                notes.add(match[1]); proofs.append(row)
    if len(named) != 1 or notes != named or not product:
        raise ValueError('Ambiguous coder dispatch/own notes/product mapping')
    return sorted(named), proofs


def extract(run_dir, threads, root_id, ownership):
    data = {'schema': 'geeky-eval.process-evidence/1', 'origin': 'automatic-raw-trace',
            'sources': {}, 'contexts': [], 'stage_intervals': [], 'reviews': [],
            'lane_moves': [], 'handoff_calls': [], 'critical_findings': [],
            'implementation_commits': {}, 'expected_implementation_commits': [], 'missing': []}
    # Activate only for the supported delegated implementation shape. Legacy traces
    # retain their existing route; strict scoring still checks their completeness.
    impls = [sid for sid, t in threads.items() if t['role'] == 'geeky-implement-orchestrator']
    if not impls:
        return None
    if len(impls) != 1:
        raise ValueError('Automatic process mapping requires one implementation delegate')
    impl = impls[0]
    refs, by_call, commands, completions, reads = {}, {}, {}, {}, {}
    for sid, thread in threads.items():
        path = thread['path'].relative_to(run_dir).as_posix()
        raw = thread['path'].read_bytes()
        all_rows = [json.loads(line) for line in raw.decode('utf-8-sig').splitlines() if line.strip()]
        indices = {json.dumps(row, sort_keys=True): i for i, row in enumerate(all_rows)}
        data['sources'][path] = hashlib.sha256(raw).hexdigest()
        commands[sid], completions[sid], reads[sid] = [], [], set()
        for row in thread['rows']:
            p = row.get('payload') or {}; item = p.get('item') or {}
            cid = p.get('call_id') or item.get('id')
            snippet = cid or p.get('type') or row['timestamp']
            ref = {'path': path, 'record_index': indices[json.dumps(row, sort_keys=True)],
                   'timestamp': row['timestamp'], 'source_text': snippet,
                   'record_sha256': hashlib.sha256(json.dumps(row, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()}
            refs[id(row)] = ref
            if p.get('type') == 'function_call' and p.get('name') == 'spawn_agent':
                by_call[sid + ':' + cid] = row
            if p.get('type') == 'task_complete':
                completions[sid].append(row)
            if p.get('type') == 'item_completed' and item.get('type') == 'CommandExecution':
                cmd = item.get('command') or ''; cmd = cmd[-1] if isinstance(cmd, list) else cmd
                out = item.get('aggregated_output') or item.get('stdout') or ''
                commands[sid].append((row, cmd, out, item.get('exit_code') == 0 and item.get('status') == 'completed'))
                if item.get('exit_code') == 0 and re.search(r'\bGet-Content\b', cmd):
                    reads[sid].update(re.findall(r'/skills/([\w-]+)/SKILL\.md', cmd.replace('\\', '/')))

    def ref(row):
        return refs[id(row)]

    def context(cid, stage, role=None, tasks=None, phase=None, proofs=()):
        result = {'call_id': cid, 'stage': stage, 'refs': [ref(by_call[cid]), *proofs]}
        result.update({k: v for k, v in [('role', role), ('tasks', tasks), ('phase', phase)] if v is not None})
        data['contexts'].append(result)

    def interval(stage, start, end, scope=None):
        data['stage_intervals'].append({'stage': stage, 'scope_call_id': scope, 'start': ref(start), 'end': ref(end)})

    impl_call = threads[impl].get('dispatch')
    if impl_call not in by_call or not completions[impl]:
        raise ValueError('Implementation delegate lacks bound dispatch/completion')
    context(impl_call, 'geeky-implement', 'orchestrator')
    interval('geeky-implement', by_call[impl_call], completions[impl][-1], impl_call)
    planners = [sid for sid in threads if threads[sid].get('parent') == root_id
                and {'geeky-plan', 'plan-review'} <= reads[sid]]
    if len(planners) != 1:
        raise ValueError('Ambiguous delegated planning stage')
    planner = planners[0]; plan_call = threads[planner].get('dispatch')
    context(plan_call, 'geeky-plan', 'orchestrator')
    # A successful plan commit followed by a reviewer dispatch is the transition;
    # reading both skill files in preflight is not two workflow executions.
    plan_commits = [r for r, cmd, out, ok in commands[planner] if ok and 'git commit' in cmd
                    and re.search(r'^\[[^\n]+ [0-9a-f]{7,40}\] .*plan', out, re.M | re.I)]
    if not plan_commits:
        raise ValueError('Missing successful planning commit')
    first_commit = plan_commits[0]['timestamp']
    plan_reviews = [t['dispatch'] for t in threads.values() if t.get('parent') == planner
                    and t.get('dispatch') in by_call and by_call[t['dispatch']]['timestamp'] > first_commit]
    if not plan_reviews:
        raise ValueError('Missing delegated plan review after plan commit')
    review_start = min((by_call[c] for c in plan_reviews), key=lambda r: r['timestamp'])
    for cid in plan_reviews:
        context(cid, 'plan-review', 'reviewer')
    interval('geeky-plan', by_call[plan_call], review_start, plan_call)
    interval('plan-review', review_start, completions[planner][-1], plan_call)
    root_rows = threads[root_id]['rows']
    announcements = [r for r in root_rows if r.get('type') == 'response_item'
                     and r.get('payload', {}).get('type') == 'message'
                     and r['payload'].get('role') == 'assistant'
                     and re.search(r'I[’\x27]m now using `?impl-review`?', json.dumps(r['payload'].get('content'), ensure_ascii=False))]
    if len(announcements) != 1 or not completions[root_id]:
        raise ValueError('Missing or ambiguous final-review announcement')
    research = [r for r in root_rows if r.get('type') == 'response_item'
                and r.get('payload', {}).get('type') == 'message' and r['payload'].get('role') == 'assistant']
    boundaries = [('spec-research', research[0]), ('geeky-plan', by_call[plan_call]),
                  ('plan-review', review_start), ('geeky-implement', by_call[impl_call]),
                  ('impl-review', announcements[0])]
    for (stage, start), (_, end) in zip(boundaries, boundaries[1:] + [('end', completions[root_id][-1])]):
        if start['timestamp'] >= end['timestamp']:
            raise ValueError('Automatic stages are not ordered')
        interval(stage, start, end)

    phases = {}
    for row, cmd, out, ok in commands[impl]:
        if not ok:
            continue
        cid = impl + ':' + row['payload']['item']['id']
        moves = lane_insertions(cmd) if 'kanban.md' in cmd and 'Set-Content' in cmd else []
        for task, lane, phase in moves:
            if task in phases and phases[task] != phase:
                raise ValueError('Conflicting task phase')
            phases[task] = phase
            data['lane_moves'].append({'call_id': cid, 'task': task, 'lane': lane, 'refs': [ref(row)]})
        done = [task for task, lane, _ in moves if lane == 'Done']
        if done and 'handoff.md' in cmd and re.search(r'Add-Content|Set-Content', cmd):
            data['handoff_calls'].append({'call_id': cid, 'tasks': done, 'refs': [ref(row)]})
        if 'git commit' in cmd:
            committed = re.findall(r'^\[[^\]\n]+ ([0-9a-f]{7,40})\] (.+)$', out, re.M)
            if not committed:
                data['missing'].append('implementation commit output: ' + cid)
            for prefix, subject in committed:
                # Keep the captured prefix; the scorer must resolve it uniquely in
                # the immutable solution history, never invent the missing digits.
                entry = {'sha': prefix, 'subject': subject.strip(), 'refs': [ref(row)]}
                data['expected_implementation_commits'].append(entry)
            if done:
                for task, (prefix, subject) in task_commit_bindings(cmd, committed, done).items():
                    data['implementation_commits'][task] = {'sha': prefix, 'subject': subject.strip(), 'refs': [ref(row)]}

    for sid, thread in threads.items():
        if thread.get('parent') != impl:
            continue
        cid = thread.get('dispatch')
        if 'coder' in thread['role']:
            own = ownership(thread)
            tasks, proofs = (own['tasks'], []) if own else dispatched_task(thread, by_call[cid])
            if any(t not in phases for t in tasks):
                raise ValueError('Coder lacks explicit phase mapping')
            context(cid, 'geeky-implement', 'coder', tasks, phases[tasks[0]], [ref(r) for r in proofs])
        elif 'reviewer' in thread['role']:
            if not completions[sid]:
                raise ValueError('Reviewer lacks own completion')
            for row in completions[sid]:
                tasks, phase, verdict, ready = review_result(row['payload'].get('last_agent_message', ''))
                if any(phases.get(t) != phase for t in tasks):
                    raise ValueError('Review phase disagrees with task lane evidence')
                data['reviews'].append({'call_id': cid, 'tasks': tasks, 'phase': phase, 'verdict': verdict,
                                        'ready': ready, 'result_ref': ref(row), 'refs': [ref(by_call[cid]), ref(row)]})
            context(cid, 'geeky-implement', 'reviewer', tasks, phase)
    return data
