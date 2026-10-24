import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('diagnostics', Path(__file__).with_name('diagnostics.py'))
diagnostics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnostics)

ROOT = r'C:\Users\gerald.khoo\.agents\skills'
LINE = ('2026-10-23T16:23:16.797470Z ERROR codex_skills_extension::loader::host: '
        'failed to walk skills root file:///C:/Users/gerald.khoo/.agents/skills: '
        'Access is denied. (os error 5)')


def classify(stages=None, **kwargs):
    options = dict(expected_root=ROOT, cli_version='0.164.0', parity_ok=True,
                   denial_verified=True, skill_invoked=True)
    options.update(kwargs)
    return diagnostics.classify_diagnostics(
        stages if stages is not None else {'plugin-install': '', 'hook-catalogue': '', 'exec': LINE}, **options)


def test_empty_exec_capture_fails_minimum_count():
    result = classify(dict.fromkeys(diagnostics.STAGES, ''))
    assert not result['ok'] and not result['known_diagnostics']
    assert result['unexpected_errors'][0]['stage'] == 'exec'
    assert result['unexpected_errors'][0]['count'] == 0
    assert result['observed_counts'] == {'plugin-install': 0, 'hook-catalogue': 0, 'exec': 0}


def test_stage_count_policy_preserves_raw_and_provenance():
    assert diagnostics.COUNT_POLICY == {'plugin-install': {'exact': 0},
        'hook-catalogue': {'exact': 0}, 'exec': {'minimum': 1}}
    result = classify({'plugin-install': '', 'hook-catalogue': '', 'exec': LINE + '\n'})
    assert result['ok']
    assert len(result['known_diagnostics']) == 1
    assert result['count_policy'] == diagnostics.COUNT_POLICY
    assert result['observed_counts'] == {'plugin-install': 0, 'hook-catalogue': 0, 'exec': 1}
    for record in result['known_diagnostics']:
        assert record['raw'] == LINE and record['count'] == 1
        assert record['version'] == '0.164.0'
        assert record['pattern'] == diagnostics.PATTERN_ID
        assert record['path'] == 'file:///C:/Users/gerald.khoo/.agents/skills'


def test_only_windows_path_case_is_normalized():
    line = LINE.replace('C:/Users/gerald.khoo/.agents/skills', 'c:/USERS/GERALD.KHOO/.AGENTS/SKILLS')
    result = classify({**dict.fromkeys(diagnostics.STAGES, ''), 'exec': line})
    assert result['ok'] and result['known_diagnostics'][0]['raw'] == line


@pytest.mark.parametrize('line', [
    LINE.replace('gerald.khoo', 'other.user'),
    LINE.replace('/.agents/skills:', '/.agents/skills-other:'),
    LINE.replace('os error 5', 'os error 2'),
    LINE.replace('Access is denied.', 'access is denied.'),
    LINE.replace('file:///', 'file://'),
    LINE.replace('/.agents/skills:', '/.agents/../.agents/skills:'),
    LINE.replace('gerald.khoo', 'gerald%2Ekhoo'),
    LINE + ' additional context',
    'prefix ' + LINE,
    'ERROR other_component: unexpected failure',
    'FATAL unknown failure',
    'Traceback (most recent call last):',
])
def test_near_misses_and_unknown_errors_fail_closed(line):
    result = classify({**dict.fromkeys(diagnostics.STAGES, ''), 'exec': line})
    assert not result['ok'] and not result['known_diagnostics']
    assert result['unexpected_errors'][0]['raw'] == line


@pytest.mark.parametrize('count', [1, 2, 37])
def test_exact_exec_recurrences_are_all_retained_without_global_cap(count):
    lines = [LINE.replace('16:23:16.797470Z', f'16:23:16.{index:06d}Z') for index in range(count)]
    result = classify({**dict.fromkeys(diagnostics.STAGES, ''), 'exec': '\n'.join(lines)})
    assert result['ok'] and not result['unexpected_errors']
    assert result['observed_counts'] == {'plugin-install': 0, 'hook-catalogue': 0, 'exec': count}
    assert [record['raw'] for record in result['known_diagnostics']] == lines
    assert [record['count'] for record in result['known_diagnostics']] == list(range(1, count + 1))
    assert all(record['pattern'] == diagnostics.PATTERN_ID for record in result['known_diagnostics'])


@pytest.mark.parametrize('unknown', ['ERROR unrelated failure', 'FATAL unrelated failure',
                                   'Traceback (most recent call last):',
                                   LINE.replace('os error 5', 'os error 2'),
                                   LINE.replace('gerald.khoo', 'other.user')])
def test_mixed_approved_recurrences_and_other_errors_fail(unknown):
    result = classify({**dict.fromkeys(diagnostics.STAGES, ''),
                       'exec': '\n'.join([LINE, unknown, LINE])})
    assert not result['ok']
    assert result['observed_counts']['exec'] == 2
    assert [record['raw'] for record in result['known_diagnostics']] == [LINE, LINE]
    assert any(record['raw'] == unknown for record in result['unexpected_errors'])


@pytest.mark.parametrize('stage', ['plugin-install', 'hook-catalogue'])
def test_known_line_in_wrong_stage_fails_even_with_same_aggregate(stage):
    captures = dict.fromkeys(diagnostics.STAGES, '')
    captures[stage] = LINE
    result = classify(captures)
    assert not result['ok'] and not result['known_diagnostics']
    assert any(e['stage'] == stage and e['count'] == 1 for e in result['unexpected_errors'])
    assert any(e['stage'] == 'exec' and e['count'] == 0 for e in result['unexpected_errors'])


@pytest.mark.parametrize('stage', ['plugin-install', 'hook-catalogue'])
def test_extra_line_in_zero_count_stage_fails(stage):
    captures = {'plugin-install': '', 'hook-catalogue': '', 'exec': LINE}
    captures[stage] = LINE
    result = classify(captures)
    assert not result['ok'] and len(result['known_diagnostics']) == 1


@pytest.mark.parametrize('options', [
    {'cli_version': '0.164.1'}, {'cli_version': 'codex-cli 0.164.0'},
    {'parity_ok': False}, {'denial_verified': False}, {'skill_invoked': False},
    {'parity_ok': 1}, {'expected_root': ''},
])
def test_missing_evidence_or_version_drift_prevents_allowance(options):
    result = classify({'plugin-install': '', 'hook-catalogue': '',
                       'exec': LINE + '\n' + LINE}, **options)
    assert not result['ok'] and not result['known_diagnostics']
    assert any(r['stage'] == 'preflight' for r in result['unexpected_errors'])
    if options.get('expected_root') != '':
        assert result['observed_counts']['exec'] == 2


@pytest.mark.parametrize('stages', [{}, {'exec': ''},
    {**dict.fromkeys(diagnostics.STAGES, ''), 'unrecognized': ''},
    {**dict.fromkeys(diagnostics.STAGES, ''), 'exec': None}])
def test_missing_unknown_or_invalid_stage_capture_fails(stages):
    assert not classify(stages)['ok']


ROUTER = ('2026-10-23T18:39:01.266351Z ERROR codex_core::tools::router: error='
          'apply_patch verification failed: Failed to find expected lines in C:\\repos\\candidate\\tests\\test_cli.py:\n'
          '    assert first == expected')


def verified_patch_record():
    return {**diagnostics.patch_router_blocks(ROUTER)[0], 'stderr_line': 2,
        'verified': True, 'thread_id': 'child', 'call_id': 'failed-call',
        'source_file': 'subagents/child.jsonl', 'source_sha256': 'a' * 64,
        'request_sha256': 'b' * 64, 'response_sha256': 'c' * 64, 'stderr_block_sha256': 'd' * 64,
        'request_ordinal': 10, 'response_ordinal': 12, 'delta_ms': 16.649,
        'failed_tool_record': {'payload': {'call_id': 'failed-call', 'type': 'custom_tool_call_output'}}}


def test_router_error_requires_independent_correlation_and_stays_separate_from_isolation():
    captures = {'plugin-install': '', 'hook-catalogue': '', 'exec': LINE + '\n' + ROUTER}
    assert not classify(captures)['ok']
    evidence = verified_patch_record()
    result = classify(captures, verified_tool_failures=[evidence])
    assert result['ok']
    assert len(result['known_diagnostics']) == 1
    assert result['observed_counts']['exec'] == 1
    assert result['candidate_tool_failures'] == [{**evidence, 'stage': 'exec', 'classification': 'candidate_tool_failure'}]
    assert result['candidate_tool_failures'][0]['failed_tool_record'] == evidence['failed_tool_record']


@pytest.mark.parametrize('options', [{'cli_version': '0.165.0'}, {'parity_ok': False},
    {'denial_verified': False}, {'skill_invoked': False}, {'expected_root': ''}])
def test_correlated_candidate_cannot_bypass_existing_required_proofs(options):
    result = classify({'plugin-install': '', 'hook-catalogue': '', 'exec': LINE + '\n' + ROUTER},
                      verified_tool_failures=[verified_patch_record()], **options)
    assert not result['ok'] and result['candidate_tool_failures'] == []


@pytest.mark.parametrize('failure', ['wrong_raw', 'wrong_path', 'wrong_line', 'duplicate', 'unverified',
    'missing_hash', 'invalid_ordinal', 'outside_time_bound', 'wrong_stage', 'unmatched_error'])
def test_candidate_router_allowance_rejects_incomplete_or_wrong_evidence(failure):
    record = verified_patch_record()
    captures = {'plugin-install': '', 'hook-catalogue': '', 'exec': LINE + '\n' + ROUTER}
    if failure == 'wrong_raw':
        record['raw'] += ' changed'
    elif failure == 'wrong_path':
        record['path'] = r'C:\repos\other\tests\test_cli.py'
    elif failure == 'wrong_line':
        record['stderr_line'] = 3
    elif failure == 'unverified':
        record['verified'] = False
    elif failure == 'missing_hash':
        record.pop('source_sha256')
    elif failure == 'invalid_ordinal':
        record['request_ordinal'] = record['response_ordinal']
    elif failure == 'outside_time_bound':
        record['delta_ms'] = 100.001
    elif failure == 'wrong_stage':
        captures['hook-catalogue'] = ROUTER
    elif failure == 'unmatched_error':
        captures['exec'] += '\nERROR unrelated router failure'
    records = [record, record] if failure == 'duplicate' else [record]
    result = classify(captures, verified_tool_failures=records)
    assert not result['ok']
    if failure not in ('wrong_stage', 'unmatched_error'):
        assert result['candidate_tool_failures'] == []
