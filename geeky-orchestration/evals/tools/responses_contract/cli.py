"""Prepare offline, replay saved wire evidence, or explicitly probe an endpoint.

No Codex process, MXC, actual collaboration tool, judge, or telemetry exporter is
started. All messages and tool outputs are synthetic contract fixtures.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit, urlunsplit

from .cases import CASES, build_case, build_followup
from .contracts import validate_request, validate_response
from . import transport

PROFILES = ('responses', 'codex-v2-native', 'codex-v2-bridge')
HERE = Path(__file__).resolve().parent
ADAPTER = HERE.parents[1] / 'adapters/codex'
MAX_PLAN_BYTES = 4 * 1024 * 1024


class DiagnosticError(ValueError):
    """A fixed, operator-safe configuration message; never include payloads."""


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    raw = Path(path).read_bytes()
    if len(raw) > MAX_PLAN_BYTES:
        raise DiagnosticError('Input document exceeds diagnostic size limit')
    return json.loads(raw.decode('utf-8-sig'))


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def source_pins():
    paths = [HERE / name for name in
             ('cli.py', 'contracts.py', 'cases.py', 'transport.py', 'sources.json')]
    paths += [ADAPTER / 'litellm_bridge' / name for name in ('mapper.py', 'server.py')]
    return {str(path.relative_to(HERE.parents[1])).replace('\\', '/'): digest(path.read_bytes())
            for path in paths}


def bridge_module():
    adapter = str(ADAPTER)
    if adapter not in sys.path:
        sys.path.insert(0, adapter)
    from litellm_bridge import mapper
    return mapper


def positive(value):
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise argparse.ArgumentTypeError('Value must be finite and positive')
    return result


def fresh(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=False)
    return path


def make_plan(args):
    selected = [name for name, case in CASES.items() if args.profile in case['profiles']] if args.cases == 'all' else args.cases.split(',')
    if not selected or len(selected) != len(set(selected)) or any(x not in CASES for x in selected):
        raise DiagnosticError('Select distinct known case IDs from catalog')
    if any(args.profile not in CASES[x]['profiles'] for x in selected):
        raise DiagnosticError('Selected case is not available in the chosen profile')
    modes = ('json', 'sse') if args.stream == 'both' else (args.stream,)
    items = []
    for name in selected:
        for mode in modes:
            case = build_case(name, args.model, stream=mode == 'sse',
                              max_output_tokens=args.max_output_tokens,
                              reasoning={'effort': args.reasoning} if args.reasoning else None)
            errors = validate_request(case['request'], args.profile)
            if errors:
                raise DiagnosticError('Generated case failed request contract validation')
            items.append({'id': f'{name}-{mode}', 'case_id': name, 'mode': mode,
                          'roundtrip': bool(CASES[name].get('roundtrip', False)), **case})
    required = sum(2 if item['roundtrip'] else 1 for item in items)
    if required > args.max_requests:
        raise DiagnosticError('Selected cases exceed max-requests; narrow the selection or explicitly raise the cap')
    plan = {'schema': 'responses-contract.plan/1', 'created_utc': datetime.now(timezone.utc).isoformat(),
            'profile': args.profile, 'model': args.model, 'items': items,
            'limits': {'max_requests': args.max_requests, 'planned_max_requests': required,
                       'max_output_tokens': args.max_output_tokens, 'timeout_s': args.timeout,
                       'max_response_bytes': args.max_response_bytes},
            'source_sha256': source_pins(), 'synthetic_only': True,
            'actual_tools_executed': False, 'network_executed': False}
    out = fresh(args.output)
    save_json(out / 'plan.json', plan)
    for item in items:
        save_json(out / f"{item['id']}.request.json", item['request'])
    return {'outcome': 'prepared', 'plan': str(out / 'plan.json'),
            'profile': args.profile, 'cases': len(items), 'maximum_requests': required,
            'network_executed': False}


def load_plan(path):
    plan = read_json(path)
    if not isinstance(plan, dict) or plan.get('schema') != 'responses-contract.plan/1':
        raise DiagnosticError('Unsupported diagnostic plan')
    if plan.get('source_sha256') != source_pins():
        raise DiagnosticError('Plan source pins are stale; prepare a new plan')
    profile = plan.get('profile')
    if profile not in PROFILES or plan.get('synthetic_only') is not True:
        raise DiagnosticError('Invalid diagnostic plan profile')
    limits = plan.get('limits', {})
    for key in ('max_requests', 'planned_max_requests', 'max_output_tokens', 'max_response_bytes'):
        if type(limits.get(key)) is not int or limits[key] < 1:
            raise DiagnosticError('Invalid diagnostic plan limits')
    positive(limits.get('timeout_s'))
    if limits['planned_max_requests'] > limits['max_requests']:
        raise DiagnosticError('Invalid diagnostic request budget')
    if not isinstance(plan.get('model'), str) or not plan['model']:
        raise DiagnosticError('Missing diagnostic model')
    items = plan.get('items')
    if not isinstance(items, list) or not items:
        raise DiagnosticError('Empty diagnostic plan')
    identities = set()
    for item in items:
        if not isinstance(item, dict) or item.get('case_id') not in CASES or item.get('mode') not in ('json', 'sse'):
            raise DiagnosticError('Invalid diagnostic case')
        name = item['case_id']
        mode = item['mode']
        if profile not in CASES[name]['profiles'] or item.get('id') != f'{name}-{mode}' or item['id'] in identities:
            raise DiagnosticError('Invalid or duplicate diagnostic case')
        identities.add(item['id'])
        # Rebuild requests rather than trusting a file labelled synthetic_only.
        # No arbitrary prompts, tools or uploaded conversation can enter a probe.
        request = item.get('request')
        if not isinstance(request, dict):
            raise DiagnosticError('Invalid diagnostic request')
        reasoning = request.get('reasoning')
        if reasoning is not None and (not isinstance(reasoning, dict) or
                set(reasoning) != {'effort'} or not isinstance(reasoning['effort'], str)):
            raise DiagnosticError('Invalid diagnostic reasoning')
        expected = build_case(name, plan['model'], stream=mode == 'sse',
                              max_output_tokens=limits['max_output_tokens'], reasoning=reasoning)
        if any(item.get(key) != expected[key] for key in ('request', 'expect')):
            raise DiagnosticError('Plan request differs from the pinned synthetic fixture')
        if item.get('roundtrip') != bool(CASES[name].get('roundtrip', False)):
            raise DiagnosticError('Invalid roundtrip declaration')
    required = sum(2 if item['roundtrip'] else 1 for item in items)
    if required != limits['planned_max_requests'] or required > limits['max_requests']:
        raise DiagnosticError('Invalid diagnostic request budget')
    return plan


def endpoint_label(endpoint):
    parsed = urlsplit(endpoint)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, '', ''))


def scrub(raw, secrets):
    for value in sorted({x for x in secrets if x}, key=len, reverse=True):
        # Match mixed literal/JSON-escaped spellings too: a provider can echo a
        # key as "\\u0073ecret", not just JSON's usual canonical serialization.
        pieces = []
        for char in value:
            escaped = json.dumps(char, ensure_ascii=True)[1:-1]
            utf16 = char.encode('utf-16-be')
            unicode_escape = ''.join('\\u' + utf16[i:i + 2].hex() for i in range(0, len(utf16), 2))
            variants = {re.escape(char.encode('utf-8')), re.escape(escaped.encode('ascii')),
                        re.escape(unicode_escape.encode('ascii'))}
            if char == '/':
                variants.add(re.escape(b'\\/'))
            # Hex digits in JSON Unicode escapes are case insensitive.
            for variant in list(variants):
                if b'\\\\u' in variant:
                    variants.remove(variant)
                    variants.add(re.sub(rb'[a-f]', lambda m: b'[' + m[0] + m[0].upper() + b']', variant))
            pieces.append(b'(?:' + b'|'.join(sorted(variants)) + b')')
        raw = re.sub(b''.join(pieces), b'[REDACTED]', raw)
    return raw


def scrub_values(value, secrets):
    if isinstance(value, str):
        return scrub(value.encode('utf-8'), secrets).decode('utf-8')
    if isinstance(value, list):
        return [scrub_values(item, secrets) for item in value]
    if isinstance(value, dict):
        return {scrub_values(key, secrets): scrub_values(item, secrets) for key, item in value.items()}
    return value


def credentials(args):
    headers = {}
    secrets = []
    if args.auth != 'none':
        value = os.environ.get(args.api_key_env, '')
        if not value or '\r' in value or '\n' in value:
            raise DiagnosticError('Selected API-key environment variable is missing or invalid')
        if args.auth == 'bearer':
            headers['Authorization'] = 'Bearer ' + value
        else:
            headers['api-key'] = value
        secrets += [value, headers.get('Authorization', '')]
    if args.headers_env:
        extra = json.loads(os.environ.get(args.headers_env, '{}'))
        if not isinstance(extra, dict):
            raise DiagnosticError('Extra headers environment must be a JSON object')
        for key, value in extra.items():
            if (not isinstance(key, str) or not isinstance(value, str) or
                not key or any(c in key + value for c in '\r\n') or
                key.lower() in ('host', 'content-length', 'transfer-encoding', 'connection', 'authorization', 'api-key')):
                raise DiagnosticError('Invalid or conflicting extra header')
            headers[key] = value
            secrets.append(value)
    return headers, secrets


def wire_request(case, profile, state):
    if profile != 'codex-v2-bridge':
        return copy.deepcopy(case['request']), None, copy.deepcopy(case['expect'])
    mapper = bridge_module()
    request, context = mapper.translate_request(case['request'], state)
    expect = copy.deepcopy(case['expect'])
    expected_calls = ([expect] if expect.get('kind') == 'function_call' else
                      expect.get('calls', []) if expect.get('kind') == 'function_calls' else [])
    for expected_call in expected_calls:
        identity = (expected_call.get('namespace'), expected_call['name'])
        expected_call['name'] = context.reverse[identity]
        expected_call.pop('namespace', None)
    return request, context, expect


def check_exchange(result, expect, profile, context, stream=None):
    # The bridge may repair an upstream reasoning-item representation. Keep
    # parsing/transport failures fatal; recheck item equality on mapped events.
    errors = [error for error in result.get('errors', [])
              if not (context is not None and result.get('events') and error.get('code') == 'item_mismatch')]
    if stream is not None:
        expected_content_type = 'text/event-stream' if stream else 'application/json'
        if result.get('content_type') != expected_content_type:
            errors.append({'code': 'response_mode', 'path': '$',
                           'message': 'Response format differs from the requested JSON/SSE mode'})
    if result.get('http_status') != 200:
        errors.append({'code': 'http_status', 'path': '$', 'message': 'Endpoint did not return HTTP 200'})
    response = result.get('response')
    if not isinstance(response, dict):
        errors.append({'code': 'missing_response', 'path': '$', 'message': 'No complete Responses object'})
        return None, errors, []
    wire_errors = validate_response(response, expect, 'responses' if context is not None else profile)
    if context is None:
        errors += wire_errors
    client = response
    if context is not None:
        try:
            mapper = bridge_module()
            if result.get('events'):
                events = [mapper.map_sse_event(event, context) for event in result['events']]
                client, stream_errors = transport.reconstruct_response(events)
                errors += stream_errors
            else:
                client = mapper.map_response_json(response, context)
        except (ValueError, TypeError, KeyError):
            errors.append({'code': 'bridge_mapping', 'path': '$', 'message': 'Bridge rejected the endpoint response'})
            client = None
    return client, errors, wire_errors


def summary(plan, outcome, results, count, network, endpoint=None):
    return {'schema': 'responses-contract.report/1', 'profile': plan['profile'],
            'validation_scope': 'selected_synthetic_cases',
            'mapping_mode': 'in_process_mapper' if plan['profile'] == 'codex-v2-bridge' else 'none',
            'outcome': outcome, 'requested_model': plan['model'],
            'network_executed': network, 'request_count': count,
            'automatic_retries': 0, 'actual_tools_executed': False,
            'evaluation_started': False, 'native_v2_support': (
                'not_tested' if plan['profile'] != 'codex-v2-native' else
                'selected_cases_passed' if outcome == 'passed' else 'not_established'),
            'endpoint': endpoint, 'results': results, 'source_sha256': plan['source_sha256'],
            'limitations': ['Selected synthetic contracts only; no full Codex/MXC workflow qualification.',
                            'Alias/model response fields do not establish backend identity.',
                            'Tool calls are validated, never executed. Opaque encryption is not decrypted.',
                            'A passing bridge profile does not prove native V2 endpoint support.']}


def replay(args):
    plan = load_plan(args.plan)
    selected = [item for item in plan['items'] if item['id'] == args.item]
    if len(selected) != 1:
        raise DiagnosticError('Select an item ID present in the plan')
    item = selected[0]
    raw = args.response.read_bytes()
    if len(raw) > plan['limits']['max_response_bytes']:
        raise DiagnosticError('Saved response exceeds planned size limit')
    state = bridge_module().BridgeState() if plan['profile'] == 'codex-v2-bridge' else None
    _, context, expect = wire_request(item, plan['profile'], state)
    if item['mode'] == 'sse':
        events, errors = transport.parse_sse(raw)
        response, reconstruction = transport.reconstruct_response(events)
        result = {'http_status': 200, 'response': response, 'events': events,
                  'errors': errors + reconstruction}
    else:
        response, errors = transport.decode_json(raw)
        result = {'http_status': 200, 'response': response, 'events': [], 'errors': errors}
    client, errors, wire_errors = check_exchange(result, expect, plan['profile'], context)
    if context is not None and isinstance(client, dict):
        errors += validate_response(client, item['expect'], plan['profile'])
    outcome = 'failed' if errors else 'passed'
    row = {'item': item['id'], 'outcome': outcome, 'errors': errors,
           'wire_errors': wire_errors, 'wire_stream_errors': result.get('errors', []),
           'saved_body_sha256': digest(raw), 'roundtrip': 'not_executed' if item['roundtrip'] else 'not_requested'}
    report = summary(plan, outcome, [row], 0, False)
    report['validation_scope'] = 'single_saved_response'
    report['native_v2_support'] = 'not_established_by_replay'
    out = fresh(args.output)
    save_json(out / 'report.json', report)
    return {'outcome': outcome, 'report': str(out / 'report.json'), 'network_executed': False}


def validate_saved_request(args):
    request = read_json(args.input)
    errors = validate_request(request, args.profile)
    out = fresh(args.output)
    outcome = 'failed' if errors else 'passed'
    save_json(out / 'report.json', {'schema': 'responses-contract.request-report/1',
              'validation_scope': 'selected_request_shapes_only', 'profile': args.profile,
              'outcome': outcome, 'errors': errors, 'input_sha256': digest(args.input.read_bytes()),
              'network_executed': False, 'request_count': 0, 'source_sha256': source_pins(),
              'limitations': ['Structural subset only; no endpoint, decryption or model behavior proof.',
                              'Input content is not copied into this report.']})
    return {'outcome': outcome, 'report': str(out / 'report.json'), 'network_executed': False}


def probe(args):
    if not args.allow_network:
        raise DiagnosticError('Endpoint probing requires the explicit --allow-network flag; prepare/replay are offline')
    plan = load_plan(args.plan)
    endpoint = transport.normalize_endpoint(args.endpoint)
    headers, secrets = credentials(args)
    out = fresh(args.output)
    save_json(out / 'attempt.json', scrub_values({'schema': 'responses-contract.attempt/1',
              'started_utc': datetime.now(timezone.utc).isoformat(),
              'plan_sha256': digest(args.plan.read_bytes()), 'endpoint': endpoint_label(endpoint),
              'endpoint_url_sha256': digest(endpoint.encode('utf-8')),
              'maximum_requests': plan['limits']['max_requests'], 'automatic_retries': 0}, secrets))
    rows, count = [], 0
    limits = plan['limits']
    for item in plan['items']:
        state = bridge_module().BridgeState() if plan['profile'] == 'codex-v2-bridge' else None
        case = copy.deepcopy(item)
        row = {'item': item['id'], 'outcome': 'not_run', 'exchanges': [], 'errors': []}
        rows.append(row)
        for turn in range(2 if item['roundtrip'] else 1):
            if count >= limits['max_requests']:
                row['errors'].append({'code': 'request_budget', 'path': '$', 'message': 'Request budget exhausted'})
                break
            request_errors = validate_request(case['request'], plan['profile'])
            if request_errors:
                row['errors'] += request_errors
                break
            try:
                request, context, expect = wire_request(case, plan['profile'], state)
            except (ValueError, TypeError, KeyError):
                row['errors'].append({'code': 'bridge_request', 'path': '$', 'message': 'Bridge rejected synthetic request'})
                break
            count += 1
            prefix = f"{item['id']}-turn{turn + 1}"
            # Match transport.exchange's actual body serialization exactly.
            request_bytes = json.dumps(request, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
            stored_request = scrub(request_bytes, secrets)
            (out / f'{prefix}.request.json').write_bytes(stored_request)
            if context is not None:
                native_request = json.dumps(case['request'], ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
                (out / f'{prefix}.client-request.json').write_bytes(scrub(native_request, secrets))
            # Persist the attempt count before issuing the single HTTP request.
            save_json(out / 'progress.json', scrub_values({'requests_started': count, 'item': item['id'], 'turn': turn + 1}, secrets))
            result = transport.exchange(endpoint, request, headers, timeout=limits['timeout_s'],
                                        max_bytes=limits['max_response_bytes'])
            raw = result.get('body', b'')
            stored = scrub(raw, secrets)
            (out / f'{prefix}.response.raw').write_bytes(stored)
            client, errors, wire_errors = check_exchange(result, expect, plan['profile'], context,
                                                         stream=case['request'].get('stream', False))
            if context is not None and isinstance(client, dict):
                errors += validate_response(client, case['expect'], plan['profile'])
                client_bytes = json.dumps(client, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
                (out / f'{prefix}.client-response.json').write_bytes(scrub(client_bytes, secrets))
            row['exchanges'].append({'turn': turn + 1, 'http_status': result.get('http_status'),
                'content_type': result.get('content_type'), 'elapsed_s': result.get('elapsed_s'),
                'request_body_sha256': digest(request_bytes),
                'wire_request_sha256': digest(request_bytes) if result.get('request_sent') or result.get('http_status') is not None else None,
                'wire_response_sha256': digest(raw) if result.get('body_complete') else None,
                'captured_body_sha256': digest(raw), 'response_body_complete': bool(result.get('body_complete')),
                'stored_request_sha256': digest(stored_request), 'request_redacted': stored_request != request_bytes,
                'stored_response_sha256': digest(stored), 'response_redacted': stored != raw,
                'wire_errors': wire_errors, 'wire_stream_errors': result.get('errors', []), 'errors': errors,
                'reported_model': client.get('model') if isinstance(client, dict) else None})
            row['errors'] += errors
            if errors:
                break
            if turn == 0 and item['roundtrip']:
                try:
                    case = build_followup(case, client)
                except (ValueError, TypeError, KeyError):
                    row['errors'].append({'code': 'followup_build', 'path': '$', 'message': 'Cannot build correlated synthetic followup'})
                    break
        row['outcome'] = 'failed' if row['errors'] else 'passed'
        # Sanitize all derived strings too, even if a hostile endpoint echoes a key.
        save_json(out / 'report.json', scrub_values(summary(plan, 'in_progress', rows, count,
                  True, endpoint_label(endpoint)), secrets))
        if row['errors'] and not args.continue_on_failure:
            break
    done = {row['item'] for row in rows}
    rows += [{'item': item['id'], 'outcome': 'not_run', 'errors': []} for item in plan['items'] if item['id'] not in done]
    outcome = 'passed' if all(row['outcome'] == 'passed' for row in rows) else 'failed'
    report = summary(plan, outcome, rows, count, count > 0, endpoint_label(endpoint))
    report['endpoint_url_sha256'] = digest(endpoint.encode('utf-8'))
    report = scrub_values(report, secrets)
    save_json(out / 'report.json', report)
    return scrub_values({'outcome': outcome, 'request_count': count, 'report': str(out / 'report.json'),
                         'network_executed': count > 0}, secrets)


def parser():
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest='command', required=True)
    sub.add_parser('catalog', help='List cases and profiles without network or credentials')
    prepare = sub.add_parser('prepare', help='Create a pinned synthetic plan; no network')
    prepare.add_argument('--model', required=True)
    prepare.add_argument('--profile', choices=PROFILES, default='responses')
    prepare.add_argument('--cases', required=True, help='Comma-separated case IDs, or all')
    prepare.add_argument('--stream', choices=('json', 'sse', 'both'), default='both')
    prepare.add_argument('--max-requests', type=int, default=16)
    prepare.add_argument('--max-output-tokens', type=int, default=256)
    prepare.add_argument('--timeout', type=positive, default=30)
    prepare.add_argument('--max-response-bytes', type=int, default=2 * 1024 * 1024)
    prepare.add_argument('--reasoning', help='Optional effort; omitted by default, endpoint-specific support')
    prepare.add_argument('--output', type=Path, required=True, help='New directory; never overwrite evidence')
    replay_parser = sub.add_parser('replay', help='Validate one saved response against a pinned plan; no network')
    replay_parser.add_argument('--plan', type=Path, required=True)
    replay_parser.add_argument('--item', required=True)
    replay_parser.add_argument('--response', type=Path, required=True)
    replay_parser.add_argument('--output', type=Path, required=True)
    saved = sub.add_parser('validate-request', help='Check a saved request structure; no network or payload copy')
    saved.add_argument('--input', type=Path, required=True)
    saved.add_argument('--profile', choices=PROFILES, default='codex-v2-native')
    saved.add_argument('--output', type=Path, required=True)
    live = sub.add_parser('probe', help='Explicit endpoint calls using only prepared synthetic fixtures')
    live.add_argument('--plan', type=Path, required=True)
    live.add_argument('--endpoint', required=True, help='Responses URL or base URL ending /v1')
    live.add_argument('--auth', choices=('bearer', 'api-key', 'none'), default='bearer')
    live.add_argument('--api-key-env', default='RESPONSES_API_KEY')
    live.add_argument('--headers-env', help='Environment variable containing extra headers as JSON')
    live.add_argument('--allow-network', action='store_true')
    live.add_argument('--continue-on-failure', action='store_true', help='Continue other cases; never retry a failure')
    live.add_argument('--output', type=Path, required=True)
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == 'catalog':
            result = {'profiles': PROFILES, 'cases': CASES, 'network_executed': False}
        elif args.command == 'prepare':
            if (args.max_requests < 1 or args.max_output_tokens < 1 or args.max_response_bytes < 1 or not args.model):
                raise DiagnosticError('Diagnostic limits and model must be positive/nonempty')
            result = make_plan(args)
        elif args.command == 'replay':
            result = replay(args)
        elif args.command == 'validate-request':
            result = validate_saved_request(args)
        else:
            result = probe(args)
        print(json.dumps(result, ensure_ascii=False))
        return 1 if result.get('outcome') == 'failed' else 0
    except DiagnosticError as error:
        print(json.dumps({'outcome': 'invalid', 'error': str(error)}))
        return 2
    except (ValueError, TypeError, KeyError, OSError, argparse.ArgumentTypeError, RecursionError, OverflowError):
        # Never print arbitrary exceptions: input or endpoint errors can contain secrets.
        print(json.dumps({'outcome': 'invalid', 'error': 'Invalid configuration, input, stale pins, or I/O; inspect the local plan and command arguments.'}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
