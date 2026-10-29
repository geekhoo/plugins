"""Deterministic, synthetic Responses and pinned Codex V2 probes.

These cases exercise a deliberately small wire subset, not a complete schema.
They do not execute tools or contain captured conversations.
"""
from copy import deepcopy
import json

NONCE = "RESPONSES_CONTRACT_7f3a91c2"
RESULT_NONCE = NONCE + "_RESULT"
ALL = ["responses", "codex-v2-native", "codex-v2-bridge"]
V2 = ["codex-v2-native", "codex-v2-bridge"]

CASES = {
    "message": {"description": "Return an exact text marker", "profiles": ALL, "kind": "message"},
    "function": {"description": "Forced function call with exact arguments", "profiles": ALL, "kind": "function", "name": "record_marker", "args": {"marker": NONCE}},
    "function_roundtrip": {"description": "Return a synthetic function result", "profiles": ALL, "kind": "function", "name": "record_marker", "args": {"marker": NONCE}, "roundtrip": True},
    "v2_spawn": {"description": "Plaintext collaboration spawn", "profiles": V2, "kind": "function", "namespace": "collaboration", "name": "spawn_agent", "args": {"task_name": "contract_probe", "message": NONCE}},
    "v2_parallel_spawn": {"description": "Two parallel plaintext collaboration spawns", "profiles": V2, "kind": "function_calls", "namespace": "collaboration", "name": "spawn_agent", "args": {"task_name": "contract_probe_a", "message": NONCE}},
    "v2_send": {"description": "Plaintext collaboration message", "profiles": V2, "kind": "function", "namespace": "collaboration", "name": "send_message", "args": {"target": "/root/contract_probe", "message": NONCE}},
    "v2_followup": {"description": "Plaintext collaboration followup", "profiles": V2, "kind": "function", "namespace": "collaboration", "name": "followup_task", "args": {"target": "/root/contract_probe", "message": NONCE}},
    "v2_wait": {"description": "Collaboration wait", "profiles": V2, "kind": "function", "namespace": "collaboration", "name": "wait_agent", "args": {"timeout_ms": 10000}},
    "v2_agent_message": {"description": "Receive a plaintext agent message", "profiles": V2, "kind": "message", "input_kind": "agent_message"},
    "v2_named_output": {"description": "Receive a named paired function output", "profiles": V2, "kind": "message", "input_kind": "named_output"},
    "v2_unpaired_output": {"description": "Receive a named unpaired function output", "profiles": V2, "kind": "message", "input_kind": "unpaired_output"},
    "v2_send_roundtrip": {"description": "Return a synthetic collaboration send result", "profiles": V2, "kind": "function", "namespace": "collaboration", "name": "send_message", "args": {"target": "/root/contract_probe", "message": NONCE}, "roundtrip": True},
}


def _function(spec):
    args = spec["args"]
    properties = {key: {"type": "integer" if isinstance(value, int) else "string"} for key, value in args.items()}
    if spec.get("namespace") == "collaboration" and "message" in properties:
        properties["message"]["encrypted"] = True
    return {"type": "function", "name": spec["name"], "description": "Return the requested synthetic arguments exactly.",
            "strict": False, "parameters": {"type": "object", "properties": properties,
                                             "required": list(args), "additionalProperties": False}}


def build_case(case_id, model, stream=False, max_output_tokens=256, reasoning=None):
    spec = deepcopy(CASES[case_id])
    if not isinstance(model, str) or not model.strip():
        raise ValueError("model must be nonempty")
    request = {"model": model, "stream": stream, "max_output_tokens": max_output_tokens, "store": False}
    if reasoning is not None:
        request["reasoning"] = deepcopy(reasoning)
    request["input"] = [{"type": "message", "role": "user", "content": [{"type": "input_text", "text": "Follow the synthetic test instructions exactly."}]}]
    expect = {"kind": "function_call" if spec["kind"] == "function" else spec["kind"], "marker": NONCE}
    if spec["kind"] in ("function", "function_calls"):
        if spec["kind"] == "function_calls":
            second = {**spec["args"], "task_name": "contract_probe_b"}
            expect["calls"] = [{"name": spec["name"], "namespace": spec["namespace"], "arguments": args}
                               for args in (spec["args"], second)]
            request["parallel_tool_calls"] = True
        else:
            expect.update({"name": spec["name"], "arguments": spec["args"]})
        function = _function(spec)
        namespace = spec.get("namespace")
        if namespace and spec["kind"] == "function":
            expect["namespace"] = namespace
        if namespace:
            request["tools"] = [{"type": "namespace", "name": namespace, "description": "Synthetic collaboration tools.", "tools": [function]}]
        else:
            request["tools"] = [function]
        request["tool_choice"] = {"type": "function", "name": spec["name"]}
        if namespace:
            request["tool_choice"]["namespace"] = namespace
        request["input"][0]["content"][0]["text"] = "Call the required function with these exact JSON arguments: " + json.dumps(spec["args"], sort_keys=True)
        if spec["kind"] == "function_calls":
            request["input"][0]["content"][0]["text"] = "Call the required function exactly twice, once for each set of JSON arguments: " + json.dumps([spec["args"], second], sort_keys=True)
    else:
        request["input"][0]["content"][0]["text"] = "Reply with exactly " + NONCE
        kind = spec.get("input_kind")
        if kind:
            request["input"][0]["content"][0]["text"] = "Read the synthetic marker in the following agent message or tool output. Reply with exactly that marker."
        if kind == "agent_message":
            request["input"].append({"type": "agent_message", "author": "/root", "recipient": "/root/contract_probe", "content": [{"type": "input_text", "text": "Message Type: NEW_TASK\nPayload:\n" + NONCE}]})
        elif kind in ("named_output", "unpaired_output"):
            prior = CASES["v2_send"]
            request["tools"] = [{"type": "namespace", "name": "collaboration", "description": "Synthetic collaboration tools.", "tools": [_function(prior)]}]
            request["tool_choice"] = "none"
            if kind == "named_output":
                request["input"].append({"type": "function_call", "name": "send_message", "namespace": "collaboration", "arguments": json.dumps({"target": "/root/contract_probe", "message": "synthetic request"}), "call_id": "call_synthetic", "encrypted_function_args": []})
            output = {"type": "function_call_output", "namespace": "collaboration", "name": "send_message", "output": NONCE}
            if kind == "named_output":
                output["call_id"] = "call_synthetic"
            request["input"].append(output)
    return {"case_id": case_id, "description": spec["description"], "profiles": spec["profiles"],
            "roundtrip": bool(spec.get("roundtrip")), "request": request, "expect": expect}


def build_followup(case, response):
    if not case.get("roundtrip"):
        raise ValueError("case does not support a follow-up")
    try:
        from .contracts import validate_response
    except ImportError:
        from contracts import validate_response
    # A V2 case is already in native form after bridge translation.
    profile = "codex-v2-native" if case["expect"].get("namespace") else "responses"
    problems = validate_response(response, case["expect"], profile)
    if problems:
        raise ValueError("cannot follow up an invalid response: " + problems[0]["code"])
    request = deepcopy(case["request"])
    # Do not carry provider-supplied extensions or unrelated conversation into
    # the next synthetic turn. Preserve only fields of the validated wire subset.
    fields = {
        "reasoning": {"type", "id", "summary", "encrypted_content", "status"},
        "function_call": {"type", "id", "call_id", "name", "namespace", "arguments", "status", "encrypted_function_args"},
    }
    returned = [{key: deepcopy(value) for key, value in item.items() if key in fields[item["type"]]}
                for item in response["output"]]
    calls = [item for item in returned if item.get("type") == "function_call"]
    request["input"].extend(returned)
    request["input"].append({"type": "function_call_output", "call_id": calls[0]["call_id"], "output": RESULT_NONCE})
    request["input"].append({"type": "message", "role": "user", "content": [{"type": "input_text", "text": "Reply with exactly the synthetic function result."}]})
    # Historical calls need their advertised identity for the existing bridge's
    # reversible mapping. Disable fresh calls without removing that mapping.
    request["tool_choice"] = "none"
    return {"request": request, "expect": {"kind": "message", "marker": RESULT_NONCE}}
