"""Offline regression proof: synthetic payloads and loopback fake upstream only."""

import copy
from contextlib import contextmanager
import http.client
import importlib.util
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

import pytest

from .mapper import (BridgeState, MappingError, digest, map_response_json,
                     map_sse_event, map_sse_frame, translate_request)
from .server import make_server, upstream_target


# Matches the retained failure's 420-character/51-whitespace class, without
# copying any private task or claiming to replay the historical bytes.
TASK = " ".join(["inspect"] * 51 + ["x" * 12])
assert len(TASK) == 420 and sum(char.isspace() for char in TASK) == 51
KEY = "offline-fixture-key"


def request_body(stream=False):
    return {"model": "offline-model", "stream": stream, "max_output_tokens": 256,
            "reasoning": {"effort": "high"}, "store": False,
            "tools": [{"type": "namespace", "name": "collaboration", "description": "Delegate tasks.",
                       "tools": [{"type": "function", "name": "send_message", "description": "Send message.",
                                  "strict": False, "parameters": {"type": "object", "properties": {
                                      "message": {"type": "string", "encrypted": True},
                                      "encrypted": {"type": "boolean", "description": "ordinary named property"}},
                                      "required": ["message"], "additionalProperties": False}}]}],
            "tool_choice": {"type": "function", "namespace": "collaboration", "name": "send_message"},
            "input": [{"type": "message", "role": "developer", "content": [{"type": "input_text", "text": "Do the actual task."}]},
                      {"type": "reasoning", "id": "rs_1", "encrypted_content": "gAAAAA_reasoning", "summary": []},
                      {"type": "agent_message", "author": "/root", "recipient": "/root/test", "content": [
                          {"type": "input_text", "text": "Message Type: NEW_TASK\nPayload:\n"},
                          {"type": "encrypted_content", "encrypted_content": TASK}]}]}


def seeded():
    return BridgeState({digest(TASK): TASK})


def tool_output(wire, arguments=None):
    return {"type": "function_call", "id": "fc_1", "call_id": "call_1", "name": wire,
            "arguments": json.dumps({"target": "/root/test", "message": TASK}) if arguments is None else arguments}


def test_failure_fixture_requires_provenance_and_never_mutates_input():
    source = request_body()
    before = copy.deepcopy(source)
    with pytest.raises(MappingError, match="no plaintext provenance"):
        translate_request(source)
    mapped, context = translate_request(source, seeded())
    assert source == before
    assert mapped["input"][0] == source["input"][0]
    assert mapped["input"][1] == source["input"][1]
    message = mapped["input"][2]
    assert message["role"] == "user" and message["type"] == "message"
    assert json.loads(message["content"][0]["text"].split(": ", 1)[1]) == {"author": "/root", "recipient": "/root/test"}
    assert message["content"][1:] == [{"type": "input_text", "text": "Message Type: NEW_TASK\nPayload:\n"},
                                      {"type": "input_text", "text": TASK}]
    function = mapped["tools"][0]
    assert "encrypted" not in function["parameters"]["properties"]["message"]
    assert function["parameters"]["properties"]["encrypted"]["type"] == "boolean"
    assert function["parameters"]["required"] == ["message"]
    assert function["strict"] is False
    assert function["description"] == "Delegate tasks.\nSend message."
    assert mapped["tool_choice"] == {"type": "function", "name": function["name"]}
    for field in ("model", "stream", "max_output_tokens", "reasoning", "store"):
        assert mapped[field] == source[field]
    result = map_response_json({"id": "resp_1", "output": [tool_output(function["name"])]}, context)
    assert result["output"][0]["namespace"] == "collaboration"
    assert result["output"][0]["encrypted_function_args"] == []
    assert result["output"][0]["call_id"] == "call_1"
    assert result["output"][0]["name"] == "send_message"


@pytest.mark.parametrize("value", ["gAAAAA_opaque", "readable but unproven", "", "eyJjaXBoZXIiOiJvcGFxdWUifQ=="])
def test_unknown_encrypted_content_rejected_even_when_readable(value):
    body = request_body()
    body["input"][2]["content"][1]["encrypted_content"] = value
    with pytest.raises(MappingError):
        translate_request(body, seeded())


def test_hash_binding_and_memory_capacity_fail_closed():
    with pytest.raises(MappingError, match="hash mismatch"):
        BridgeState({"wrong": TASK})
    state = BridgeState(max_entries=1)
    state.remember(["one", "one"])
    with pytest.raises(MappingError, match="capacity"):
        state.remember(["two"])
    assert state.recover("one") == "one"
    with pytest.raises(MappingError):
        state.recover("two")


def test_upstream_plaintext_arguments_provide_cross_request_provenance():
    state = BridgeState()
    body = request_body()
    body["input"] = "Send a task."
    mapped, context = translate_request(body, state)
    wire = mapped["tools"][0]["name"]
    response = {"output": [tool_output(wire)]}
    original = copy.deepcopy(response)
    map_response_json(response, context)
    assert response == original
    mapped2, _ = translate_request(request_body(), state)
    assert mapped2["input"][2]["content"][-1]["text"] == TASK
    assert mapped["tool_choice"]["name"] == wire


def test_collisions_history_choices_and_schema_nodes_are_reversible():
    body = request_body()
    body["input"] = []
    first, _ = translate_request(body)
    wire = first["tools"][0]["name"]
    body["tools"].extend([{"type": "function", "name": wire, "parameters": {"type": "object"}},
                          {"type": "namespace", "name": "other", "tools": [{"type": "function", "name": "send_message"}]}])
    body["input"] = [{"type": "function_call", "id": "fc_h", "call_id": "historic", "namespace": "collaboration",
                      "name": "send_message", "arguments": "{}", "encrypted_function_args": []},
                     {"type": "function_call_output", "call_id": "historic", "namespace": "collaboration",
                      "name": "send_message", "output": [{"type": "input_text", "text": "done"},
                      {"type": "input_image", "image_url": "data:image/png;base64,AAAA"},
                      {"type": "input_audio", "data": "AAAA", "format": "wav"}]}]
    body["tool_choice"] = {"type": "allowed_tools", "mode": "required", "tools": [
        {"type": "function", "name": "send_message", "namespace": "collaboration"}]}
    parameters = body["tools"][0]["tools"][0]["parameters"]
    parameters["$defs"] = {"entry": {"anyOf": [{"type": "string", "encrypted": True}]}}
    parameters["properties"]["arr"] = {"type": "array", "items": {"type": "string", "encrypted": True}}
    mapped, context = translate_request(body)
    names = [tool["name"] for tool in mapped["tools"]]
    assert len(set(names)) == 3 and names[0] != wire and names[1] == wire
    assert mapped["input"][0]["call_id"] == "historic"
    assert "encrypted_function_args" not in mapped["input"][0]
    assert "namespace" not in mapped["input"][1]
    assert mapped["input"][1]["output"] == body["input"][1]["output"]
    assert mapped["tool_choice"]["tools"][0]["name"] == names[0]
    assert "encrypted" not in mapped["tools"][0]["parameters"]["$defs"]["entry"]["anyOf"][0]
    assert "encrypted" not in mapped["tools"][0]["parameters"]["properties"]["arr"]["items"]
    response = map_response_json({"output": [tool_output(name) for name in names]}, context)
    assert [item.get("namespace") for item in response["output"]] == ["collaboration", None, "other"]
    assert "encrypted_function_args" not in response["output"][2]


def test_nested_plaintext_output_recovery_and_opaque_output_failure():
    body = request_body()
    body["input"] = [{"type": "function_call_output", "call_id": "out", "output": [
        {"type": "encrypted_content", "encrypted_content": TASK}]}]
    mapped, _ = translate_request(body, seeded())
    assert mapped["input"][0] == {"type": "function_call_output", "call_id": "out",
                                   "output": [{"type": "input_text", "text": TASK}]}
    with pytest.raises(MappingError):
        translate_request(body)


@pytest.mark.parametrize("event_type", ["response.output_item.added", "response.output_item.done"])
def test_sse_items_and_completion_preserve_order_ids_and_errors(event_type):
    mapped, context = translate_request(request_body(), seeded())
    item = tool_output(mapped["tools"][0]["name"])
    event = {"type": event_type, "sequence_number": 7, "output_index": 2, "item": item}
    result = map_sse_event(event, context)
    assert result["sequence_number"] == 7 and result["output_index"] == 2
    assert result["item"]["id"] == "fc_1" and result["item"]["encrypted_function_args"] == []
    for status in ("completed", "incomplete"):
        completion = map_sse_event({"type": "response." + status, "response": {"status": status, "output": [item]}}, context)
        assert completion["response"]["output"][0]["namespace"] == "collaboration"
    for event in ({"type": "response.function_call_arguments.delta", "delta": "ab", "item_id": "fc_1"},
                  {"type": "error", "code": "provider_error", "message": "synthetic error"}):
        assert map_sse_event(event, context) == event
    frame = b": keepalive\r\nevent: response.output_item.done\r\nid: 17\r\ndata: " + json.dumps(result).encode() + b"\r\n\r\n"
    # The transport sees wire identities, never an already mapped item.
    frame = frame.replace(b'"name": "send_message"', json.dumps("name").encode() + b": " + json.dumps(mapped["tools"][0]["name"]).encode())
    frame = frame.replace(b', "namespace": "collaboration"', b"")
    data = map_sse_frame(frame, context)
    assert b": keepalive\n" in data and b"id: 17\n" in data
    assert b'"encrypted_function_args":[]' in data
    assert map_sse_frame(b"data: [DONE]\n\n", context) == b"data: [DONE]\n\n"


@pytest.mark.parametrize("summary", [[], [{"type": "summary_text", "text": "Keep the summary."}]])
def test_valid_reasoning_summary_content_and_ciphertext_are_unchanged(summary):
    _, context = translate_request({})
    item = {"type": "reasoning", "id": "rs", "summary": summary,
            "content": [{"type": "reasoning_text", "text": "Keep the reasoning."}],
            "encrypted_content": "opaque-reasoning-ciphertext"}
    original = copy.deepcopy(item)
    assert map_response_json({"output": [item]}, context) == {"output": [item]}
    assert map_sse_event({"type": "response.output_item.done", "output_index": 0, "item": item}, context)["item"] == item
    assert item == original


@pytest.mark.parametrize("null_summary", [False, True])
def test_missing_reasoning_summary_json_and_sse_preserve_all_content(null_summary):
    _, context = translate_request({})
    item = {"type": "reasoning", "id": "rs", "encrypted_content": "opaque",
            "content": [{"type": "output_text", "text": "All reasoning text.", "annotations": []}]}
    if null_summary:
        item["summary"] = None
    original = copy.deepcopy(item)
    expected = dict(copy.deepcopy(item), summary=[])
    expected["content"][0]["type"] = "reasoning_text"
    assert map_response_json({"output": [item]}, context)["output"][0] == expected
    for kind in ("response.output_item.added", "response.output_item.done"):
        assert map_sse_event({"type": kind, "output_index": 0, "item": item}, context)["item"] == expected
    assert map_sse_event({"type": "response.completed", "response": {"output": [item]}}, context)["response"]["output"][0] == expected
    assert item == original


def reasoning_drift():
    done = {"type": "reasoning", "id": "rs", "summary": [{"type": "summary_text", "text": "Exact reasoning."}]}
    terminal = {"type": "reasoning", "id": "rs", "role": "assistant", "status": "completed",
                "content": [{"type": "output_text", "text": "Exact reasoning.", "annotations": []}]}
    return done, terminal


def test_exact_reasoning_drift_reconciles_detached_items_and_matching_ciphertext():
    for ciphertext in (None, "opaque"):
        _, context = translate_request({})
        done, terminal = reasoning_drift()
        if ciphertext is not None:
            done["encrypted_content"] = terminal["encrypted_content"] = ciphertext
        original = copy.deepcopy(terminal)
        forwarded = map_sse_event({"type": "response.output_item.done", "output_index": 0, "item": done}, context)
        # Neither caller mutation nor later responses may mutate cached items.
        forwarded["item"]["summary"][0]["text"] = "caller mutation"
        result = map_sse_event({"type": "response.completed", "response": {"output": [terminal]}}, context)
        assert result["response"]["output"] == [done]
        assert terminal == original and context.reasoning_done == {}


@pytest.mark.parametrize("change", ["text", "summary", "empty_summary", "ciphertext", "new_ciphertext", "metadata", "annotations", "role", "status", "id", "index"])
def test_reasoning_drift_conflicts_and_unknown_metadata_are_never_concealed(change):
    _, context = translate_request({})
    done, terminal = reasoning_drift()
    if change == "ciphertext":
        done["encrypted_content"] = "first"
        terminal["encrypted_content"] = "second"
    elif change == "new_ciphertext":
        terminal["encrypted_content"] = "new opaque content"
    elif change == "text":
        terminal["content"][0]["text"] = "Contradictory reasoning."
    elif change == "summary":
        terminal["summary"] = [{"type": "summary_text", "text": "Contradictory summary."}]
    elif change == "empty_summary":
        terminal["summary"] = []
    elif change == "annotations":
        terminal["content"][0]["annotations"] = [{"type": "citation", "value": "retain"}]
    elif change in {"metadata", "role", "status", "id"}:
        terminal[change] = "unexpected"
    map_sse_event({"type": "response.output_item.done", "output_index": 1 if change == "index" else 0, "item": done}, context)
    original = copy.deepcopy(terminal)
    result = map_sse_event({"type": "response.completed", "response": {"output": [terminal]}}, context)["response"]["output"][0]
    assert result != done
    # Only required summary/type repair is allowed; every supplied value stays.
    expected = copy.deepcopy(terminal)
    expected.setdefault("summary", [])
    expected["content"][0]["type"] = "reasoning_text"
    assert result == expected and terminal == original


def test_reasoning_cache_is_request_local_resets_and_commits_after_provenance():
    state = BridgeState(max_entries=0)
    body = request_body()
    body["input"] = []
    mapped, first = translate_request(body, state)
    _, second = translate_request({}, state)
    done, terminal = reasoning_drift()
    event = {"type": "response.output_item.done", "output_index": 0, "item": done}
    map_sse_event(event, first)
    assert second.reasoning_done == {}
    with pytest.raises(MappingError, match="capacity"):
        map_sse_event(dict(event, output_index=1, response={"output": [tool_output(mapped["tools"][0]["name"])]}), first)
    # Failed provenance must not publish the second reasoning cache entry.
    assert first.reasoning_done == {(0, "rs"): done}
    map_sse_event({"type": "response.created", "response": {"output": []}}, first)
    assert first.reasoning_done == {}
    for context in (first, second):
        output = map_sse_event({"type": "response.completed", "response": {"output": [terminal]}}, context)["response"]["output"][0]
        assert output != done and output["content"][0]["text"] == terminal["content"][0]["text"]


@pytest.mark.parametrize("name", ["minimax-bridge-cap192", "deepseek-bridge-cap192", "mimo-bridge-cap768"])
def test_captured_reasoning_drift_replays_through_strict_offline_contract(name):
    root = Path(__file__).resolve().parents[5]
    folder = root / "outputs" / "litellm-bounded-retest-20261027" / name / "result"
    if not folder.is_dir():
        pytest.skip("Retained local provider capture is unavailable")
    modules = []
    for module_name in ("transport", "contracts"):
        path = root / "geeky-orchestration" / "evals" / "tools" / "responses_contract" / (module_name + ".py")
        spec = importlib.util.spec_from_file_location("offline_" + module_name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        modules.append(module)
    transport, contracts = modules
    raw = (folder / "v2_send-sse-turn1.response.raw").read_bytes()
    events, errors = transport.parse_sse(raw)
    assert errors == []
    _, original_errors = transport.reconstruct_response(events)
    assert "item_mismatch" in {error["code"] for error in original_errors}
    request = json.loads((folder / "v2_send-sse-turn1.client-request.json").read_text())
    _, context = translate_request(request)
    before = copy.deepcopy(events)
    mapped = [map_sse_event(event, context) for event in events]
    response, errors = transport.reconstruct_response(mapped)
    assert errors == []
    expected = {"kind": "function_call", "namespace": "collaboration", "name": "send_message",
                "arguments": {"target": "/root/contract_probe", "message": "RESPONSES_CONTRACT_7f3a91c2"}}
    assert contracts.validate_response(response, expected, "codex-v2-bridge") == []
    assert events == before and (folder / "v2_send-sse-turn1.response.raw").read_bytes() == raw


def test_nonempty_encryption_metadata_rejected():
    body = request_body()
    body["input"] = [{"type": "function_call", "namespace": "collaboration", "name": "send_message",
                      "arguments": "{}", "encrypted_function_args": ["message"]}]
    with pytest.raises(MappingError, match="Encrypted function arguments"):
        translate_request(body)
    body["input"] = []
    mapped, context = translate_request(body)
    item = tool_output(mapped["tools"][0]["name"])
    item["encrypted_function_args"] = ["message"]
    with pytest.raises(MappingError, match="Unexpected upstream"):
        map_response_json({"output": [item]}, context)


@pytest.mark.parametrize("opaque", ["opaque-encryption-envelope", "readable envelope", False, 0, [], {}])
def test_separate_function_encryption_envelope_rejected_without_mutation(opaque):
    body = request_body()
    body["input"] = [{"type": "function_call", "namespace": "collaboration", "name": "send_message",
                      "arguments": json.dumps({"message": TASK}), "encrypted_content": opaque}]
    original = copy.deepcopy(body)
    state = BridgeState()
    with pytest.raises(MappingError, match="Encrypted function call content"):
        translate_request(body, state)
    assert body == original and state.known_plaintext == {}
    body["input"] = []
    mapped, context = translate_request(body, state)
    wire = mapped["tools"][0]["name"]
    valid = tool_output(wire)
    encrypted = dict(valid, encrypted_content=opaque)
    response = {"output": [valid, encrypted]}
    original_response = copy.deepcopy(response)
    with pytest.raises(MappingError, match="Encrypted function call content"):
        map_response_json(response, context)
    assert response == original_response and state.known_plaintext == {}
    event = {"type": "response.output_item.done", "item": encrypted}
    with pytest.raises(MappingError, match="Encrypted function call content"):
        map_sse_event(event, context)
    assert state.known_plaintext == {} and "encrypted_function_args" not in event["item"]


@pytest.mark.parametrize("empty", [None, ""])
def test_empty_optional_function_envelope_is_preserved_without_guessing(empty):
    body = request_body()
    body["input"] = [{"type": "function_call", "namespace": "collaboration", "name": "send_message",
                      "arguments": "{}", "encrypted_content": empty}]
    mapped, context = translate_request(body)
    assert mapped["input"][0]["encrypted_content"] == empty
    item = dict(tool_output(mapped["tools"][0]["name"]), encrypted_content=empty)
    result = map_response_json({"output": [item]}, context)
    assert result["output"][0]["encrypted_content"] == empty
    assert result["output"][0]["encrypted_function_args"] == []


@pytest.mark.parametrize("invalid", [None, False, 0, "", {}, ["message"]])
def test_plaintext_metadata_accepts_only_an_actual_empty_list(invalid):
    body = request_body()
    body["input"] = [{"type": "function_call", "namespace": "collaboration", "name": "send_message",
                      "arguments": "{}", "encrypted_function_args": invalid}]
    with pytest.raises(MappingError):
        translate_request(body)
    body["input"] = []
    mapped, context = translate_request(body)
    item = tool_output(mapped["tools"][0]["name"])
    item["encrypted_function_args"] = invalid
    with pytest.raises(MappingError):
        map_response_json({"output": [item]}, context)


@pytest.mark.parametrize("invalid", [None, False, 0, "", {}, ["payload"]])
def test_ordinary_function_opaque_metadata_rejected_with_atomic_provenance(invalid):
    body = request_body()
    body["input"] = []
    body["tools"].append({"type": "function", "name": "ordinary", "parameters": {"type": "object"}})
    state = BridgeState()
    mapped, context = translate_request(body, state)
    valid = tool_output(mapped["tools"][0]["name"])
    opaque = dict(tool_output("ordinary"), encrypted_function_args=invalid)
    response = {"output": [valid, opaque]}
    original = copy.deepcopy(response)
    with pytest.raises(MappingError, match="Unexpected upstream encrypted function arguments"):
        map_response_json(response, context)
    assert response == original and state.known_plaintext == {}
    with pytest.raises(MappingError):
        map_sse_event({"type": "response.output_item.done", "item": opaque}, context)
    assert state.known_plaintext == {}


@pytest.mark.parametrize("explicit", [False, True])
def test_ordinary_function_preserves_absent_or_explicit_empty_metadata(explicit):
    body = {"input": [], "tools": [{"type": "function", "name": "ordinary"}]}
    _, context = translate_request(body)
    item = tool_output("ordinary")
    if explicit:
        item["encrypted_function_args"] = []
    assert map_response_json({"output": [item]}, context) == {"output": [item]}
    assert context.state.known_plaintext == {}


def test_observed_wait_markup_fails_closed_without_inventing_a_call():
    body = {"input": [], "tools": [{"type": "namespace", "name": "collaboration",
            "tools": [{"type": "function", "name": "wait_agent"}]}]}
    _, context = translate_request(body)
    wire = context.reverse[("collaboration", "wait_agent")]
    assert wire == "collaboration__wait_agent_a96e42dcffba0586"
    text = ("All three research agents are now working in parallel. "
            "The repository contains only `brief.md`, `contract.md`, and `.gitignore`, "
            "so the specification will treat the contract as the integration source of truth "
            "and explicitly record that there are no pre-existing package or test conventions "
            "to preserve.<tool_call><function=collaboration__wait_agent_a96e42dcffba0586"
            "</parameter><parameter=timeout_ms>300000</parameter></function></tool_call>")
    message = {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": text}]}
    with pytest.raises(MappingError, match="Tool-call markup"):
        map_response_json({"output": [message]}, context)
    with pytest.raises(MappingError, match="Tool-call markup"):
        map_sse_event({"type": "response.output_item.done", "item": message}, context)
    with pytest.raises(MappingError, match="Tool-call markup"):
        map_sse_event({"type": "response.completed", "response": {"output": [message]}}, context)
    # Splitting at every boundary still fails, without merging unrelated items.
    marker = "<tool_call><function=" + wire
    for split in range(1, len(marker)):
        _, c = translate_request(body)
        map_sse_event({"type": "response.output_text.delta", "item_id": "msg", "content_index": 0, "delta": marker[:split]}, c)
        with pytest.raises(MappingError, match="Tool-call markup"):
            map_sse_event({"type": "response.output_text.delta", "item_id": "msg", "content_index": 0, "delta": marker[split:]}, c)
    _, c = translate_request(body)
    map_sse_event({"type": "response.output_text.delta", "item_id": "one", "delta": marker[:20]}, c)
    map_sse_event({"type": "response.output_text.delta", "item_id": "two", "delta": marker[20:]}, c)
    ordinary = {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "ordinary report"}]}
    assert map_response_json({"output": [ordinary]}, c) == {"output": [ordinary]}
    unknown = {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "<tool_call><function=unadvertised"}]}
    assert map_response_json({"output": [unknown]}, c) == {"output": [unknown]}


@pytest.mark.parametrize("output", ["Report unchanged.", [{"type": "input_text", "text": "Report unchanged."}]])
def test_unpaired_v2_output_becomes_untrusted_message_with_full_envelope(output):
    body = request_body()
    item = {"type": "function_call_output", "id": "notification_1", "name": "background_report",
            "namespace": "collaboration", "metadata": {"source": "worker"}, "output": output}
    body["input"] = [item]
    before = copy.deepcopy(body)
    mapped, _ = translate_request(body)
    assert body == before
    message = mapped["input"][0]
    assert message["type"] == "message" and message["role"] == "user"
    envelope = json.loads(message["content"][0]["text"].split(": ", 1)[1])
    assert envelope == {key: value for key, value in item.items() if key not in {"type", "output"}}
    assert message["content"][1:] == [{"type": "input_text", "text": "Report unchanged."}]


@contextmanager
def fake_upstream(mode="json"):
    captured = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            captured.append((self.path, dict(self.headers), body))
            if mode in {"redirect", "rate_limit"}:
                self.send_response(307 if mode == "redirect" else 429)
                self.send_header("Location", "http://127.0.0.1:1/steal")
                self.end_headers()
                self.wfile.write(b"secret upstream body should never escape")
                return
            item = tool_output(body["tools"][0]["name"])
            if mode == "bad_text_sse":
                wire = body["tools"][0]["name"]
                marker = "<tool_call><function=" + wire
                events = [{"type": "response.output_text.delta", "item_id": "msg", "content_index": 0, "delta": marker[:15]},
                          {"type": "response.output_text.delta", "item_id": "msg", "content_index": 0, "delta": marker[15:]},
                          {"type": "response.completed", "response": {"output": []}}]
                payload = b"".join(b"event: " + event["type"].encode() + b"\ndata: " + json.dumps(event).encode() + b"\n\n" for event in events)
                content_type = "text/event-stream"
            elif mode == "sse":
                events = [{"type": "response.output_item.added", "output_index": 0, "item": dict(item, arguments="")},
                          {"type": "response.function_call_arguments.delta", "item_id": "fc_1", "delta": item["arguments"]},
                          {"type": "response.output_item.done", "output_index": 0, "item": item},
                          {"type": "response.completed", "response": {"id": "resp_1", "output": [item]}}]
                payload = b"".join(b"event: " + event["type"].encode() + b"\ndata: " + json.dumps(event).encode() + b"\n\n" for event in events)
                payload += b"data: [DONE]\n\n"
                content_type = "text/event-stream"
            elif mode == "bad_text_json":
                wire = body["tools"][0]["name"]
                message = {"type": "message", "role": "assistant", "content": [
                    {"type": "output_text", "text": "<tool_call><function=" + wire}]}
                payload = json.dumps({"output": [message]}).encode()
                content_type = "application/json"
            else:
                payload = json.dumps({"id": "resp_1", "output": [item]}).encode()
                content_type = "application/json"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    upstream = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=upstream.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{upstream.server_port}/v1", captured
    finally:
        upstream.shutdown()
        upstream.server_close()
        thread.join(3)


@contextmanager
def running_bridge(base_url, state=None, max_body=100000):
    server = make_server(base_url, KEY, state=state, max_body=max_body, timeout=3)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(3)


def post(server, body, key=KEY, path="/v1/responses", headers=None):
    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
    try:
        connection.request("POST", path, json.dumps(body), {"Authorization": "Bearer " + key,
                           "Content-Type": "application/json", **(headers or {})})
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        connection.close()


def test_http_stream_rejects_text_markup_and_never_emits_completion():
    with fake_upstream("bad_text_sse") as (base, _), running_bridge(base, seeded()) as bridge:
        status, _, raw = post(bridge, request_body(True))
    assert status == 200  # SSE headers precede the invalid event.
    assert b'"code":"bridge_tool_call_as_text"' in raw
    assert b"response.completed" not in raw
    assert b"response.function_call" not in raw


def test_http_json_rejects_text_markup_with_dedicated_sanitized_error():
    with fake_upstream("bad_text_json") as (base, _), running_bridge(base, seeded()) as bridge:
        status, _, raw = post(bridge, request_body())
    assert status == 502
    assert json.loads(raw)["error"]["code"] == "bridge_tool_call_as_text"
    assert b"<tool_call>" not in raw


@pytest.mark.parametrize("stream", [False, True])
def test_http_end_to_end_maps_real_wire_and_auth_without_mutation(stream):
    body = request_body(stream)
    before = copy.deepcopy(body)
    with fake_upstream("sse" if stream else "json") as (base, captured), running_bridge(base, seeded()) as bridge:
        status, headers, raw = post(bridge, body, headers={"X-Upstream-URL": "http://invalid.test", "Connection": "keep-alive", "User-Agent": "codex-mxc-win/offline"})
        assert status == 200
        assert len(captured) == 1
        path, forwarded_headers, forwarded = captured[0]
        assert path == "/v1/responses"
        assert forwarded_headers["Authorization"] == "Bearer " + KEY
        assert "X-Upstream-URL" not in forwarded_headers
        assert forwarded_headers["User-Agent"] == "codex-mxc-win/offline"
        assert forwarded["input"][2]["content"][-1] == {"type": "input_text", "text": TASK}
        assert "namespace" not in forwarded["tool_choice"]
        assert forwarded["tools"][0]["name"] == forwarded["tool_choice"]["name"]
        assert body == before
        if stream:
            assert "Content-Length" not in headers
            events = [json.loads(line[6:]) for line in raw.decode().splitlines() if line.startswith("data: {")]
            assert [event["type"] for event in events] == ["response.output_item.added", "response.function_call_arguments.delta", "response.output_item.done", "response.completed"]
            assert events[0]["item"]["encrypted_function_args"] == []
            assert events[1]["delta"] == json.dumps({"target": "/root/test", "message": TASK})
            assert events[-1]["response"]["output"][0]["namespace"] == "collaboration"
        else:
            result = json.loads(raw)
            assert int(headers["Content-Length"]) == len(raw)
            assert result["output"][0]["encrypted_function_args"] == []
            assert result["output"][0]["namespace"] == "collaboration"


def test_http_rejects_unknown_content_auth_and_bad_path_before_upstream():
    with fake_upstream() as (base, captured), running_bridge(base) as bridge:
        assert post(bridge, request_body())[0] == 400
        assert post(bridge, request_body(), key="wrong")[0] == 401
        assert post(bridge, request_body(), path="/v1/responses?url=http://invalid.test")[0] == 404
        assert captured == []


def test_http_function_encryption_envelope_rejected_before_upstream_and_provenance():
    body = request_body()
    body["input"] = [{"type": "function_call", "namespace": "collaboration", "name": "send_message",
                      "arguments": json.dumps({"message": TASK}), "encrypted_content": "opaque-envelope"}]
    state = BridgeState()
    with fake_upstream() as (base, captured), running_bridge(base, state) as bridge:
        status, _, raw = post(bridge, body)
        assert status == 400 and captured == [] and state.known_plaintext == {}
        assert TASK.encode() not in raw and b"opaque-envelope" not in raw


def test_http_limits_body_and_does_not_forward_redirects_or_error_bodies():
    with fake_upstream("redirect") as (base, captured), running_bridge(base, seeded()) as bridge:
        status, _, raw = post(bridge, request_body())
        assert status == 502 and b"upstream_http_error" in raw and b"secret" not in raw
        assert len(captured) == 1
    with fake_upstream() as (base, captured), running_bridge(base, seeded(), max_body=10) as bridge:
        assert post(bridge, request_body())[0] == 413
        assert captured == []


def test_upstream_rate_limit_status_preserved_with_sanitized_body():
    with fake_upstream("rate_limit") as (base, captured), running_bridge(base, seeded()) as bridge:
        status, _, raw = post(bridge, request_body())
        assert status == 429 and b"secret" not in raw and KEY.encode() not in raw
        assert len(captured) == 1


@pytest.mark.parametrize("url", ["ftp://example.test", "http://user:password@example.test", "http://example.test?token=secret", "http://example.test/#fragment", ""])
def test_invalid_upstream_configuration_rejected(url):
    with pytest.raises(ValueError):
        upstream_target(url)


def test_offline_cli_files_and_invalid_hash(tmp_path):
    folder = Path(__file__).resolve().parent.parent
    source, known, target = [tmp_path / name for name in ("input.json", "known.json", "output.json")]
    source.write_text(json.dumps(request_body()), encoding="utf-8")
    known.write_text(json.dumps({digest(TASK): TASK}), encoding="utf-8")
    command = [sys.executable, "-m", "litellm_bridge", "translate", "--input", str(source), "--output", str(target), "--known-plaintext", str(known)]
    result = subprocess.run(command, cwd=folder, capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert json.loads(target.read_text(encoding="utf-8"))["input"][2]["content"][-1]["text"] == TASK
    known.write_text(json.dumps({"wrong": TASK}), encoding="utf-8")
    result = subprocess.run(command, cwd=folder, capture_output=True, text=True, timeout=10)
    assert result.returncode == 1 and TASK not in result.stderr and KEY not in result.stderr


def test_real_cli_server_readiness_and_fixed_upstream(tmp_path):
    folder = Path(__file__).resolve().parent.parent
    ready = tmp_path / "ready.json"
    known = tmp_path / "known.json"
    known.write_text(json.dumps({digest(TASK): TASK}), encoding="utf-8")
    with fake_upstream() as (base, captured):
        environment = dict(os.environ, LITELLM_PROXY_API_BASE=base, LITELLM_PROXY_API_KEY=KEY,
                           PYTHONDONTWRITEBYTECODE="1")
        process = subprocess.Popen([sys.executable, "-m", "litellm_bridge", "serve", "--port", "0",
                                    "--ready-file", str(ready), "--known-plaintext", str(known)],
                                   cwd=folder, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            deadline = time.monotonic() + 10
            metadata = None
            while time.monotonic() < deadline and process.poll() is None:
                try:
                    metadata = json.loads(ready.read_text(encoding="utf-8"))
                    break
                except (OSError, ValueError):
                    time.sleep(0.02)
            assert metadata is not None, "CLI did not publish valid readiness"
            assert metadata["pid"] == process.pid and KEY not in ready.read_text(encoding="utf-8")
            from urllib.parse import urlsplit
            target = urlsplit(metadata["base_url"])
            assert target.hostname == "127.0.0.1" and target.path == "/v1"
            connection = http.client.HTTPConnection(target.hostname, target.port, timeout=5)
            try:
                connection.request("POST", target.path + "/responses", json.dumps(request_body()),
                                   {"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
                response = connection.getresponse()
                assert response.status == 200
                assert json.loads(response.read())["output"][0]["encrypted_function_args"] == []
            finally:
                connection.close()
            assert len(captured) == 1
        finally:
            process.terminate()
            stdout, stderr = process.communicate(timeout=5)
            assert KEY.encode() not in stdout + stderr and TASK.encode() not in stdout + stderr


def test_cli_graceful_exit_closes_listener_and_removes_readiness(tmp_path, monkeypatch):
    from . import __main__ as cli

    ready = tmp_path / "ready.json"
    seen = []

    def server_factory(*args, **kwargs):
        server = make_server(*args, **kwargs)
        original_close = server.server_close

        def serve(**_kwargs):
            seen.append(json.loads(ready.read_text(encoding="utf-8")))

        def close():
            original_close()
            seen.append("closed")

        server.serve_forever = serve
        server.server_close = close
        return server

    monkeypatch.setattr(cli, "make_server", server_factory)
    monkeypatch.setattr(cli.signal, "signal", lambda *_args: None)
    monkeypatch.setenv("LITELLM_PROXY_API_BASE", "http://127.0.0.1:1/v1")
    monkeypatch.setenv("LITELLM_PROXY_API_KEY", KEY)
    monkeypatch.setattr(sys, "argv", ["litellm_bridge", "serve", "--ready-file", str(ready)])
    assert cli.main() == 0
    assert seen[0]["base_url"].startswith("http://127.0.0.1:") and seen[1] == "closed"
    assert not ready.exists()
