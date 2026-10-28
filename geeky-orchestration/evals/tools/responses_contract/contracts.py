"""Offline checks for the specific synthetic probes, not a full JSON Schema."""
import json
import math
import re
from collections import Counter

PROFILES = {"responses", "codex-v2-native", "codex-v2-bridge"}
COLLAB_PLAINTEXT = {"spawn_agent", "send_message", "followup_task"}


def _error(errors, code, path, message):
    errors.append({"code": code, "path": path, "message": message})


def _string(value):
    return isinstance(value, str) and bool(value.strip())


def _strict_json_object(text):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError("duplicate JSON object key")
            result[key] = value
        return result

    def constant(value):
        raise ValueError("non-finite JSON constant")

    def number(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("non-finite JSON number")
        return result

    result = json.loads(text, object_pairs_hook=pairs, parse_constant=constant, parse_float=number)
    if not isinstance(result, dict):
        raise ValueError("not an object")
    return result


def _parts(content, path, errors, allowed):
    if not isinstance(content, list) or not content:
        _error(errors, "content", path, "Expected a nonempty content array")
        return
    for i, part in enumerate(content):
        p = f"{path}[{i}]"
        if not isinstance(part, dict) or not isinstance(part.get("type"), str) or part.get("type") not in allowed:
            _error(errors, "content_type", p, "Unexpected content type")
            continue
        key = "encrypted_content" if part["type"] == "encrypted_content" else "text"
        if not isinstance(part.get(key), str):
            _error(errors, "content_value", p, "Content value must be a string")


def _call(item, path, errors, profile):
    if not _string(item.get("name")) or not _string(item.get("call_id")):
        _error(errors, "call_identity", path, "Function call requires name and call_id")
    namespace = item.get("namespace")
    if namespace is not None and not _string(namespace):
        _error(errors, "namespace", path + ".namespace", "Namespace must be nonempty")
    if namespace is not None and profile == "responses":
        _error(errors, "native_extension", path + ".namespace", "Namespaced calls require a Codex V2 profile")
    try:
        args = _strict_json_object(item.get("arguments"))
    except (TypeError, ValueError):
        _error(errors, "arguments_json", path + ".arguments", "Function arguments must be a JSON object encoded as a string")
        args = None
    metadata = item.get("encrypted_function_args")
    if profile == "responses" and ("encrypted_function_args" in item or item.get("encrypted_content") not in (None, "")):
        _error(errors, "native_extension", path, "Function encryption fields require Codex V2")
    plaintext = namespace == "collaboration" and isinstance(item.get("name"), str) and item.get("name") in COLLAB_PLAINTEXT
    if plaintext and profile != "responses" and (not isinstance(metadata, list) or metadata):
        _error(errors, "plaintext_metadata", path + ".encrypted_function_args", "Plaintext collaboration calls require an explicit empty list")
    elif "encrypted_function_args" in item and (not isinstance(metadata, list) or any(not isinstance(x, str) for x in metadata)):
        _error(errors, "encryption_metadata", path + ".encrypted_function_args", "Encryption metadata must be an array of strings")
    if isinstance(metadata, list) and metadata:
        _error(errors, "unsupported_encryption", path + ".encrypted_function_args", "Opaque encrypted function arguments are outside this probe")
    if item.get("encrypted_content") not in (None, ""):
        _error(errors, "encrypted_envelope", path + ".encrypted_content", "Opaque encrypted function envelopes are outside this probe")
    if item.get("status") not in (None, "completed"):
        _error(errors, "item_status", path + ".status", "Function call is not complete")
    return args


def validate_request(request, profile):
    errors = []
    if profile not in PROFILES:
        return [{"code": "profile", "path": "$", "message": "Unknown profile"}]
    if not isinstance(request, dict):
        return [{"code": "request", "path": "$", "message": "Expected an object"}]
    if not _string(request.get("model")):
        _error(errors, "model", "$.model", "Model must be nonempty")
    if "stream" in request and not isinstance(request["stream"], bool):
        _error(errors, "stream", "$.stream", "Stream must be boolean")
    if "parallel_tool_calls" in request and not isinstance(request["parallel_tool_calls"], bool):
        _error(errors, "parallel_tool_calls", "$.parallel_tool_calls", "Parallel tool calls must be boolean")
    if "max_output_tokens" in request and (type(request["max_output_tokens"]) is not int or request["max_output_tokens"] <= 0):
        _error(errors, "max_output_tokens", "$.max_output_tokens", "Maximum output tokens must be a positive integer")
    if "reasoning" in request and not isinstance(request["reasoning"], dict):
        _error(errors, "reasoning", "$.reasoning", "Reasoning must be an object")
    identities = set()
    tools = request.get("tools", [])
    if not isinstance(tools, list):
        _error(errors, "tools", "$.tools", "Tools must be an array")
        tools = []

    def declaration(tool, namespace, path):
        if not isinstance(tool, dict) or tool.get("type") != "function" or not _string(tool.get("name")):
            _error(errors, "tool_declaration", path, "Expected a named function declaration")
            return
        identity = (namespace, tool["name"])
        if identity in identities:
            _error(errors, "duplicate_tool", path, "Duplicate function identity")
        identities.add(identity)
        schema = tool.get("parameters")
        if not isinstance(schema, dict) or schema.get("type") != "object":
            _error(errors, "tool_schema", path + ".parameters", "Function parameters must be an object schema")
        if profile == "responses" and isinstance(schema, dict):
            def has_encrypted(value):
                if isinstance(value, dict):
                    if "encrypted" in value:
                        return True
                    for key, child in value.items():
                        if key in ("properties", "$defs", "definitions", "patternProperties") and isinstance(child, dict):
                            if any(has_encrypted(v) for v in child.values()):
                                return True
                        elif has_encrypted(child):
                            return True
                    return False
                return isinstance(value, list) and any(has_encrypted(x) for x in value)
            if has_encrypted(schema):
                _error(errors, "native_extension", path + ".parameters", "Encrypted schema fields require Codex V2")

    for i, tool in enumerate(tools):
        path = f"$.tools[{i}]"
        if isinstance(tool, dict) and tool.get("type") == "namespace":
            if profile == "responses":
                _error(errors, "native_extension", path, "Tool namespaces require Codex V2")
            if not _string(tool.get("name")) or not isinstance(tool.get("tools"), list):
                _error(errors, "tool_namespace", path, "Namespace requires name and tools array")
                continue
            for j, child in enumerate(tool["tools"]):
                declaration(child, tool["name"], f"{path}.tools[{j}]")
        else:
            declaration(tool, None, path)
    choice = request.get("tool_choice")
    if isinstance(choice, dict):
        name, namespace = choice.get("name"), choice.get("namespace")
        if choice.get("type") != "function" or not _string(name) or (namespace is not None and not _string(namespace)):
            _error(errors, "tool_choice", "$.tool_choice", "Expected a named forced function choice")
        elif (namespace, name) not in identities:
            _error(errors, "tool_choice", "$.tool_choice", "Forced function must be declared")
    elif choice is not None and choice not in ("none", "auto", "required"):
        _error(errors, "tool_choice", "$.tool_choice", "Unsupported tool choice")
    rows = request.get("input")
    if isinstance(rows, str):
        return errors
    if not isinstance(rows, list) or not rows:
        _error(errors, "input", "$.input", "Expected a nonempty input array or string")
        return errors
    calls = {}
    for i, item in enumerate(rows):
        path = f"$.input[{i}]"
        if not isinstance(item, dict):
            _error(errors, "item", path, "Expected an object")
            continue
        kind = item.get("type")
        if kind == "message":
            if item.get("role") not in ("system", "developer", "user", "assistant"):
                _error(errors, "role", path + ".role", "Unexpected message role")
            if not isinstance(item.get("content"), str):
                _parts(item.get("content"), path + ".content", errors, {"input_text", "output_text"})
        elif kind == "agent_message":
            if profile == "responses":
                _error(errors, "native_extension", path, "Agent messages require a Codex V2 profile")
            if not _string(item.get("author")) or not _string(item.get("recipient")):
                _error(errors, "agent_identity", path, "Agent message requires author and recipient")
            _parts(item.get("content"), path + ".content", errors, {"input_text", "encrypted_content"})
        elif kind == "reasoning":
            if not isinstance(item.get("summary"), list):
                _error(errors, "reasoning_summary", path + ".summary", "Reasoning summary must be an array")
            if item.get("encrypted_content") is not None and not isinstance(item["encrypted_content"], str):
                _error(errors, "reasoning_content", path + ".encrypted_content", "Reasoning encrypted content must be a string or null")
        elif kind == "function_call":
            _call(item, path, errors, profile)
            call_id = item.get("call_id")
            if _string(call_id):
                if call_id in calls:
                    _error(errors, "duplicate_call_id", path + ".call_id", "Duplicate call ID")
                calls[call_id] = item
        elif kind == "function_call_output":
            if profile == "responses" and item.get("namespace") is not None:
                _error(errors, "native_extension", path + ".namespace", "Output namespaces require Codex V2")
            call_id = item.get("call_id")
            if call_id is not None:
                if not _string(call_id) or call_id not in calls:
                    _error(errors, "output_call_id", path + ".call_id", "Output must refer to a preceding call")
                elif ((item.get("name") is not None and item["name"] != calls[call_id].get("name")) or
                      (item.get("namespace") is not None and item["namespace"] != calls[call_id].get("namespace"))):
                    _error(errors, "output_identity", path, "Output identity differs from its call")
            elif profile == "responses" or not _string(item.get("name")):
                _error(errors, "output_identity", path, "Unpaired output requires a named Codex V2 output")
            if not isinstance(item.get("output"), (str, list)):
                _error(errors, "output_value", path + ".output", "Output must be text or an array")
            elif isinstance(item["output"], list):
                _parts(item["output"], path + ".output", errors, {"input_text", "encrypted_content"})
                if profile == "responses" and any(isinstance(part, dict) and part.get("type") == "encrypted_content" for part in item["output"]):
                    _error(errors, "native_extension", path + ".output", "Encrypted tool output requires Codex V2")
        else:
            _error(errors, "input_type", path + ".type", "Item type is outside the supported probe subset")
    return errors


def _looks_like_call(text):
    if re.search(r"<\s*(?:tool_call|function(?:=|\s))", text, re.I):
        return True
    try:
        obj = json.loads(text)
    except (ValueError, TypeError):
        return False
    return isinstance(obj, dict) and ("name" in obj and ("arguments" in obj or "parameters" in obj) or "tool_calls" in obj)


def validate_response(response, expect, profile):
    errors = []
    if profile not in PROFILES:
        return [{"code": "profile", "path": "$", "message": "Unknown profile"}]
    if not isinstance(response, dict) or not isinstance(expect, dict):
        return [{"code": "response", "path": "$", "message": "Expected response and expectation objects"}]
    if not _string(response.get("id")) or response.get("object") != "response":
        _error(errors, "response_identity", "$", "Expected a Responses object with a nonempty ID")
    if response.get("error") is not None:
        _error(errors, "response_error", "$.error", "Response contains an error")
    if response.get("status") != "completed":
        _error(errors, "response_status", "$.status", "Response must complete successfully")
    output = response.get("output")
    if not isinstance(output, list):
        _error(errors, "output", "$.output", "Expected an output array")
        return errors
    calls, texts = [], []
    messages = 0
    ids = set()
    for i, item in enumerate(output):
        path = f"$.output[{i}]"
        if not isinstance(item, dict):
            _error(errors, "item", path, "Expected an object")
            continue
        kind = item.get("type")
        if kind == "reasoning":
            if not isinstance(item.get("summary"), list):
                _error(errors, "reasoning_summary", path + ".summary", "Reasoning summary must be an array")
            if item.get("encrypted_content") is not None and not isinstance(item["encrypted_content"], str):
                _error(errors, "reasoning_content", path + ".encrypted_content", "Reasoning encrypted content must be a string or null")
        elif kind == "function_call":
            if not _string(item.get("id")):
                _error(errors, "item_id", path + ".id", "Function call requires an item ID in this Responses probe")
            args = _call(item, path, errors, profile)
            call_id = item.get("call_id")
            if _string(call_id):
                if call_id in ids:
                    _error(errors, "duplicate_call_id", path + ".call_id", "Duplicate call ID")
                ids.add(call_id)
            calls.append((item, args, path))
        elif kind == "message":
            messages += 1
            if not _string(item.get("id")):
                _error(errors, "item_id", path + ".id", "Assistant message requires an item ID in this Responses probe")
            if item.get("role") != "assistant" or item.get("status") not in (None, "completed"):
                _error(errors, "message_status", path, "Expected a completed assistant message")
            parts = item.get("content")
            if not isinstance(parts, list) or not parts:
                _error(errors, "content", path + ".content", "Expected a nonempty content array")
                continue
            for j, part in enumerate(parts):
                pp = f"{path}.content[{j}]"
                if not isinstance(part, dict):
                    _error(errors, "content_type", pp, "Expected a content object")
                elif part.get("type") == "refusal":
                    _error(errors, "refusal", pp, "Response refused the probe")
                elif part.get("type") != "output_text" or not isinstance(part.get("text"), str):
                    _error(errors, "content_type", pp, "Expected output_text")
                else:
                    texts.append(part["text"])
                    if _looks_like_call(part["text"]):
                        _error(errors, "tool_call_as_text", pp, "Tool call must be a structured item")
        else:
            _error(errors, "output_type", path + ".type", "Item type is outside the supported probe subset")
    kind = expect.get("kind")
    if kind == "function_call":
        if messages:
            _error(errors, "unexpected_message", "$.output", "Function call probe cannot contain assistant messages")
        if len(calls) != 1:
            _error(errors, "expected_call", "$.output", "Expected exactly one structured function call")
        else:
            item, args, path = calls[0]
            if item.get("name") != expect.get("name") or item.get("namespace") != expect.get("namespace"):
                _error(errors, "tool_identity", path, "Unexpected tool name or namespace")
            if args != expect.get("arguments"):
                _error(errors, "arguments_mismatch", path + ".arguments", "Arguments differ from the requested synthetic values")
    elif kind == "function_calls":
        if messages:
            _error(errors, "unexpected_message", "$.output", "Function call probe cannot contain assistant messages")
        expected = expect.get("calls")
        if not isinstance(expected, list) or not expected or any(not isinstance(row, dict) for row in expected):
            _error(errors, "expectation", "$", "Expected a nonempty list of call expectations")
        else:
            try:
                def identity(name, namespace, arguments):
                    return json.dumps([name, namespace, arguments], sort_keys=True, separators=(",", ":"), allow_nan=False)
                actual_set = Counter(identity(item.get("name"), item.get("namespace"), args) for item, args, _ in calls)
                expected_set = Counter(identity(row.get("name"), row.get("namespace"), row.get("arguments")) for row in expected)
                if len(calls) != len(expected) or actual_set != expected_set:
                    _error(errors, "calls_mismatch", "$.output", "Structured calls do not match the expected identities and arguments")
            except (TypeError, ValueError):
                _error(errors, "expectation", "$", "Call expectations must contain JSON values")
    elif kind == "message":
        if calls or "".join(texts).strip() != expect.get("marker"):
            _error(errors, "message_mismatch", "$.output", "Expected the exact synthetic text marker and no function call")
    else:
        _error(errors, "expectation", "$", "Unknown expectation kind")
    return errors
