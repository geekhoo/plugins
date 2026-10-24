"""Classify only the owner's approved Codex 0.164.0 denied-root diagnostic.

This classifier supplies no isolation/discovery proof itself. Callers must provide
independent evidence and the complete stderr capture for every process stage.
"""
import re

STAGES = ('plugin-install', 'hook-catalogue', 'exec')
# Accounting policy v2: the paid capture repeats the same exact exec diagnostic.
# Installation/catalogue remain exact zero; no unverified global count cap.
COUNT_POLICY = {'plugin-install': {'exact': 0}, 'hook-catalogue': {'exact': 0},
                'exec': {'minimum': 1}}
PATTERN_ID = 'codex-0.164.0-denied-user-skills-root-v1'
DENIED_ROOT = re.compile(
    r'^(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?Z) '
    r'ERROR codex_skills_extension::loader::host: failed to walk skills root '
    r'(?P<path>file:///[A-Za-z]:/[^\r\n]+): Access is denied\. \(os error 5\)$')
ERROR_LINE = re.compile(r'\b(?:ERROR|FATAL)\b|Traceback')
PATCH_ROUTER_HEAD = re.compile(
    r'^(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?Z) '
    r'ERROR codex_core::tools::router: error=(?P<failure>apply_patch verification failed: '
    r'Failed to find expected lines in (?P<path>[A-Za-z]:[\\/][^\r\n]+):)$')


def patch_router_blocks(stderr):
    """Only the exact expected-lines failure with indented context is eligible."""
    lines = stderr.splitlines()
    blocks = []
    for index, line in enumerate(lines):
        match = PATCH_ROUTER_HEAD.fullmatch(line)
        if match is None:
            continue
        stop = index + 1
        while stop < len(lines) and lines[stop].startswith((' ', '\t')):
            stop += 1
        if stop > index + 1:
            blocks.append({**match.groupdict(), 'stderr_line': index + 1,
                'raw': '\n'.join(lines[index:stop]),
                'failure': match['failure'] + '\n' + '\n'.join(lines[index + 1:stop])})
    return blocks


def classify_diagnostics(stage_stderr, expected_root, cli_version, parity_ok,
                         denial_verified, skill_invoked, verified_tool_failures=()):
    """Return known lines and fail-closed errors without discarding source text.

    All three stage keys must be explicitly supplied, including empty captures.
    Install/catalogue require zero matches; exec requires at least one. Every
    accepted recurrence retains its raw line and ordinal. Observed counts cover
    exact signature/root matches even when required proof fails (never accepted).
    The only path normalization is Windows separators and case; aliases, URI
    escapes, dot segments, trailing separators and different roots do not match.
    """
    known = []
    unexpected = []
    candidate_failures = []
    observed_counts = dict.fromkeys(STAGES)
    expected_uri = None
    if isinstance(expected_root, str):
        normalized = expected_root.replace('\\', '/')
        if (re.fullmatch(r'[A-Za-z]:/[^\r\n]+', normalized)
                and not normalized.endswith('/')
                and not any(p in ('', '.', '..') for p in normalized.split('/')[1:])):
            expected_uri = 'file:///' + normalized

    def failure(reason, stage='preflight', raw=None, path=None, count=0):
        unexpected.append({'stage': stage, 'raw': raw, 'path': path, 'count': count,
                           'version': cli_version, 'pattern': PATTERN_ID, 'reason': reason})

    def result():
        return {'ok': not unexpected, 'known_diagnostics': known,
                'unexpected_errors': unexpected, 'count_policy': COUNT_POLICY,
                'observed_counts': observed_counts, 'candidate_tool_failures': candidate_failures}

    proofs = {'version': cli_version == '0.164.0', 'parity_ok': parity_ok is True,
              'denial_verified': denial_verified is True, 'skill_invoked': skill_invoked is True,
              'expected_root': expected_uri is not None}
    for name, passed in proofs.items():
        if not passed:
            failure('Required evidence failed: ' + name)
    if not isinstance(stage_stderr, dict):
        failure('stage_stderr must be a dictionary of explicit stage captures')
        return result()
    for stage in STAGES:
        if stage not in stage_stderr:
            failure('Missing process-stage stderr capture', stage)
    for stage, stderr in stage_stderr.items():
        recognized = stage in STAGES
        if not recognized:
            failure('Unknown process stage', stage)
        if not isinstance(stderr, str):
            failure('Stage stderr must be a string', stage)
            continue
        count = 0
        blocks = {block['stderr_line']: block for block in patch_router_blocks(stderr)} if stage == 'exec' else {}
        for number, raw in enumerate(stderr.splitlines(), 1):
            match = DENIED_ROOT.fullmatch(raw)
            matching_root = (match is not None and expected_uri is not None
                             and match['path'].lower() == expected_uri.lower())
            if matching_root:
                count += 1
            approved = recognized and all(proofs.values()) and matching_root
            if approved:
                if stage == 'exec':
                    known.append({'stage': stage, 'raw': raw, 'path': match['path'],
                        'count': count, 'version': cli_version, 'pattern': PATTERN_ID})
                else:
                    failure('Approved diagnostic is forbidden in this process stage', stage,
                            raw, match['path'], count)
            elif ERROR_LINE.search(raw):
                block = blocks.get(number)
                verified = [record for record in verified_tool_failures
                            if isinstance(record, dict) and record.get('verified') is True
                            and all(isinstance(record.get(key), str) and record[key]
                                    for key in ('thread_id', 'call_id', 'source_file'))
                            and all(isinstance(record.get(key), str) and re.fullmatch(r'[0-9a-fA-F]{64}', record[key])
                                    for key in ('source_sha256', 'request_sha256', 'response_sha256', 'stderr_block_sha256'))
                            and type(record.get('request_ordinal')) is int
                            and type(record.get('response_ordinal')) is int
                            and record['request_ordinal'] < record['response_ordinal']
                            and isinstance(record.get('delta_ms'), (float, int)) and 0 <= record['delta_ms'] <= 100
                            and record.get('stderr_line') == number and block is not None
                            and all(record.get(key) == block[key] for key in ('raw', 'failure', 'path', 'timestamp'))]
                unique_call = len(verified) == 1 and sum(
                    record.get('thread_id') == verified[0].get('thread_id')
                    and record.get('call_id') == verified[0].get('call_id')
                    for record in verified_tool_failures if isinstance(record, dict)) == 1
                if stage == 'exec' and all(proofs.values()) and unique_call:
                    candidate_failures.append({**verified[0], 'stage': 'exec',
                                               'classification': 'candidate_tool_failure'})
                else:
                    failure('Unapproved diagnostic', stage, raw,
                            match['path'] if match else None, count)
        observed_counts[stage] = count
        if recognized:
            policy = COUNT_POLICY[stage]
            if ('exact' in policy and count != policy['exact']) or ('minimum' in policy and count < policy['minimum']):
                failure(f'Process-stage count mismatch: required {policy}',
                        stage, stderr, expected_uri, count)
    return result()
