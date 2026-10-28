import copy
import importlib.util
import json
from pathlib import Path

import pytest

from .cases import CASES, NONCE, RESULT_NONCE, build_case, build_followup
from .contracts import validate_request, validate_response


def response(case):
    expect = case["expect"]
    if expect["kind"] == "message":
        output = [{"type": "message", "id": "msg_1", "role": "assistant", "status": "completed", "content": [{"type": "output_text", "text": NONCE}]}]
    else:
        output = []
        for index, call in enumerate(expect["calls"] if expect["kind"] == "function_calls" else [expect], 1):
            item = {"type": "function_call", "id": f"fc_{index}", "name": call["name"], "call_id": f"call_{index}", "arguments": json.dumps(call["arguments"])}
            if "namespace" in call:
                item["namespace"] = call["namespace"]
                if item["name"] != "wait_agent":
                    item["encrypted_function_args"] = []
            output.append(item)
    return {"id": "resp_1", "object": "response", "status": "completed", "output": output}


@pytest.mark.parametrize("case_id", CASES)
def test_all_synthetic_cases_validate(case_id):
    case = build_case(case_id, "offline-model")
    for profile in case["profiles"]:
        assert validate_request(case["request"], profile) == []
        assert validate_response(response(case), case["expect"], profile) == []


@pytest.mark.parametrize("case_id", ["function_roundtrip", "v2_send_roundtrip"])
def test_roundtrip_preserves_actual_reasoning_and_call_and_correlates_output(case_id):
    case = build_case(case_id, "offline-model")
    original = response(case)
    original["output"].insert(0, {"type": "reasoning", "id": "rs_1", "summary": [], "encrypted_content": "opaque-reasoning"})
    before = copy.deepcopy(original)
    followup = build_followup(case, original)
    assert original == before
    assert followup["request"]["input"][1:3] == original["output"]
    assert RESULT_NONCE not in json.dumps(case["request"])
    assert followup["request"]["input"][3] == {"type": "function_call_output", "call_id": "call_1", "output": RESULT_NONCE}
    assert followup["expect"]["marker"] == RESULT_NONCE
    assert RESULT_NONCE not in json.dumps(followup["request"]["input"][-1])
    assert validate_request(followup["request"], case["profiles"][0]) == []
    followup["request"]["input"][3]["call_id"] = "wrong"
    assert "output_call_id" in codes(validate_request(followup["request"], case["profiles"][0]))


def codes(errors):
    return {error["code"] for error in errors}


@pytest.mark.parametrize("value", [None, False, "", {}, ["message"]])
def test_plaintext_v2_metadata_must_be_explicit_empty_list(value):
    case = build_case("v2_send", "offline-model")
    result = response(case)
    result["output"][0]["encrypted_function_args"] = value
    for profile in ("codex-v2-native", "codex-v2-bridge"):
        assert "plaintext_metadata" in codes(validate_response(result, case["expect"], profile))
    del result["output"][0]["encrypted_function_args"]
    assert "plaintext_metadata" in codes(validate_response(result, case["expect"], "codex-v2-native"))


def test_wait_does_not_require_plaintext_metadata_and_reasoning_is_independent():
    case = build_case("v2_wait", "offline-model")
    result = response(case)
    result["output"].insert(0, {"type": "reasoning", "summary": [], "encrypted_content": "opaque"})
    assert validate_response(result, case["expect"], "codex-v2-native") == []


def test_opaque_function_encryption_is_unsupported_for_wait_and_ordinary_tools():
    for case_id in ("v2_wait", "function"):
        case = build_case(case_id, "offline-model")
        result = response(case)
        result["output"][0]["encrypted_function_args"] = ["message"]
        result["output"][0]["encrypted_content"] = "opaque"
        assert {"unsupported_encryption", "encrypted_envelope"} <= codes(validate_response(result, case["expect"], "codex-v2-native"))


@pytest.mark.parametrize("text", ['<tool_call><function=record_marker>{}</function></tool_call>', '{"name":"record_marker","arguments":{}}'])
def test_tool_calls_as_text_are_rejected(text):
    case = build_case("function", "offline-model")
    result = {"status": "completed", "output": [{"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": text}]}]}
    assert {"tool_call_as_text", "expected_call"} <= codes(validate_response(result, case["expect"], "responses"))


def test_wrong_identity_arguments_and_call_id_fail():
    case = build_case("v2_spawn", "offline-model")
    result = response(case)
    result["output"][0].update({"name": "send_message", "namespace": "wrong", "call_id": "", "arguments": "{"})
    assert {"tool_identity", "call_identity", "arguments_json"} <= codes(validate_response(result, case["expect"], "codex-v2-native"))


@pytest.mark.parametrize("arguments", [
    '{"marker":"wrong","marker":"' + NONCE + '"}',
    '{"marker":NaN}', '{"marker":Infinity}', '{"marker":1e999}',
    '{"marker":{"nested":-1e999}}',
])
def test_function_arguments_reject_ambiguous_or_nonfinite_json(arguments):
    case = build_case("function", "offline-model")
    result = response(case)
    result["output"][0]["arguments"] = arguments
    assert "arguments_json" in codes(validate_response(result, case["expect"], "responses"))


@pytest.mark.parametrize("case_id", ["function_roundtrip", "v2_parallel_spawn"])
def test_function_probes_reject_unexpected_assistant_message(case_id):
    case = build_case(case_id, "offline-model")
    result = response(case)
    result["output"].append({"type": "message", "id": "msg_extra", "role": "assistant", "content": [{"type": "output_text", "text": "extra"}]})
    assert "unexpected_message" in codes(validate_response(result, case["expect"], case["profiles"][0]))


def test_followup_filters_unknown_provider_fields():
    case = build_case("function_roundtrip", "offline-model")
    result = response(case)
    result["output"].insert(0, {"type": "reasoning", "id": "rs_1", "summary": [], "encrypted_content": "opaque", "extra": "discard"})
    result["output"][1]["extra"] = "discard"
    followup = build_followup(case, result)
    assert followup["request"]["input"][1] == {"type": "reasoning", "id": "rs_1", "summary": [], "encrypted_content": "opaque"}
    assert "extra" not in followup["request"]["input"][2]


@pytest.mark.parametrize("status", ["incomplete", "failed", None])
def test_incomplete_response_and_refusal_fail(status):
    case = build_case("message", "offline-model")
    result = {"status": status, "output": [{"type": "message", "role": "assistant", "content": [{"type": "refusal", "refusal": "no"}]}]}
    assert {"response_status", "refusal", "message_mismatch"} <= codes(validate_response(result, case["expect"], "responses"))


def test_native_input_shapes_and_unpaired_identity():
    case = build_case("v2_agent_message", "offline-model")
    agent = case["request"]["input"][-1]
    assert "native_extension" in codes(validate_request(case["request"], "responses"))
    agent["recipient"] = ""
    agent["content"] = [{"type": "encrypted_content", "encrypted_content": 3}]
    assert {"agent_identity", "content_value"} <= codes(validate_request(case["request"], "codex-v2-native"))
    unpaired = build_case("v2_unpaired_output", "offline-model")["request"]
    assert validate_request(unpaired, "codex-v2-native") == []
    del unpaired["input"][-1]["name"]
    assert "output_identity" in codes(validate_request(unpaired, "codex-v2-native"))


@pytest.mark.parametrize("case_id", ["v2_agent_message", "v2_named_output", "v2_unpaired_output"])
def test_handoff_marker_appears_only_in_handoff(case_id):
    request = build_case(case_id, "offline-model")["request"]
    assert NONCE not in json.dumps(request["input"][:-1])
    assert NONCE in json.dumps(request["input"][-1])


def test_named_pair_must_match_call():
    req = build_case("v2_named_output", "offline-model")["request"]
    req["input"][-1]["name"] = "wrong"
    assert "output_identity" in codes(validate_request(req, "codex-v2-native"))


def test_followup_rejects_invalid_response_and_non_roundtrip():
    case = build_case("function_roundtrip", "offline-model")
    with pytest.raises(ValueError):
        build_followup(case, {"status": "incomplete", "output": []})
    with pytest.raises(ValueError):
        build_followup(build_case("message", "offline-model"), response(build_case("message", "offline-model")))


@pytest.mark.parametrize("field,value", [("model", []), ("stream", "yes"), ("max_output_tokens", True), ("max_output_tokens", 0), ("reasoning", "high"), ("tools", {}), ("tool_choice", [])])
def test_malformed_request_values_return_errors(field, value):
    request = build_case("function", "offline-model")["request"]
    request[field] = value
    assert validate_request(request, "responses")


def test_declarations_choice_and_extension_fail_closed():
    request = build_case("function", "offline-model")["request"]
    request["tools"].append(copy.deepcopy(request["tools"][0]))
    request["tool_choice"]["name"] = "different"
    request["tools"][0]["parameters"] = []
    assert {"duplicate_tool", "tool_choice", "tool_schema"} <= codes(validate_request(request, "responses"))
    v2 = build_case("v2_send", "offline-model")["request"]
    assert "native_extension" in codes(validate_request(v2, "responses"))


def test_ordinary_property_named_encrypted_is_not_encryption_metadata():
    request = build_case("function", "offline-model")["request"]
    request["tools"][0]["parameters"]["properties"]["encrypted"] = {"type": "boolean"}
    assert validate_request(request, "responses") == []
    request["tools"][0]["parameters"]["properties"]["marker"]["encrypted"] = True
    assert "native_extension" in codes(validate_request(request, "responses"))


def test_response_identity_item_id_and_error_checked():
    case = build_case("message", "offline-model")
    result = response(case)
    del result["id"]
    del result["output"][0]["id"]
    result["error"] = {"message": "synthetic"}
    assert {"response_identity", "response_error", "item_id"} <= codes(validate_response(result, case["expect"], "responses"))


def test_invalid_nested_types_do_not_raise():
    request = build_case("v2_agent_message", "offline-model")["request"]
    request["input"][-1]["content"] = [{"type": []}]
    assert validate_request(request, "codex-v2-native")
    result = response(build_case("v2_send", "offline-model"))
    result["output"][0]["name"] = []
    assert validate_response(result, build_case("v2_send", "offline-model")["expect"], "codex-v2-native")


def test_existing_bridge_maps_named_unpaired_and_roundtrip_history():
    path = Path(__file__).resolve().parents[2] / "adapters" / "codex" / "litellm_bridge" / "mapper.py"
    spec = importlib.util.spec_from_file_location("contract_bridge_mapper", path)
    mapper = importlib.util.module_from_spec(spec)
    # dataclasses resolve their defining module during import.
    import sys
    sys.modules[spec.name] = mapper
    spec.loader.exec_module(mapper)
    for case_id in ("v2_named_output", "v2_unpaired_output", "function_roundtrip", "v2_send_roundtrip", "v2_parallel_spawn"):
        case = build_case(case_id, "offline-model")
        _, context = mapper.translate_request(case["request"])
        if case_id == "v2_parallel_spawn":
            wire_name = context.reverse[("collaboration", "spawn_agent")]
            wire = response(case)
            for item in wire["output"]:
                item["name"] = wire_name
                item.pop("namespace")
                item.pop("encrypted_function_args")
            native = mapper.map_response_json(wire, context)
            assert validate_response(native, case["expect"], "codex-v2-bridge") == []
        if not case["roundtrip"]:
            continue
        exp = case["expect"]
        wire_name = context.reverse[(exp.get("namespace"), exp["name"])]
        wire = {"id": "resp_1", "object": "response", "status": "completed", "output": [{"type": "function_call", "id": "fc_1", "call_id": "call_1", "name": wire_name, "arguments": json.dumps(exp["arguments"])}]}
        native = mapper.map_response_json(wire, context)
        followup = build_followup(case, native)
        mapper.translate_request(followup["request"], context.state)


def test_parallel_spawns_validate_unordered_and_reject_invalid_calls():
    case = build_case("v2_parallel_spawn", "offline-model")
    result = response(case)
    assert case["request"]["parallel_tool_calls"] is True
    assert case["request"]["tool_choice"] == {"type": "function", "namespace": "collaboration", "name": "spawn_agent"}
    result["output"].reverse()
    for profile in case["profiles"]:
        assert validate_response(result, case["expect"], profile) == []
        dropped = copy.deepcopy(result)
        dropped["output"].pop()
        assert "calls_mismatch" in codes(validate_response(dropped, case["expect"], profile))
        duplicate = copy.deepcopy(result)
        duplicate["output"][1]["call_id"] = duplicate["output"][0]["call_id"]
        assert "duplicate_call_id" in codes(validate_response(duplicate, case["expect"], profile))
        bad_args = copy.deepcopy(result)
        bad_args["output"][0]["arguments"] = json.dumps({"task_name": "wrong", "message": NONCE})
        assert "calls_mismatch" in codes(validate_response(bad_args, case["expect"], profile))
        missing = copy.deepcopy(result)
        del missing["output"][0]["encrypted_function_args"]
        assert "plaintext_metadata" in codes(validate_response(missing, case["expect"], profile))
