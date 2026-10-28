"""Pure request/response transformations; no transport, credentials or inference.

Encryption is never inferred from prefixes. A tagged encrypted collaboration
value needs exact hash-bound plaintext provenance, even if it looks readable.
Reasoning encrypted_content is an independent Responses feature and is retained.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import threading
from dataclasses import dataclass, field


class MappingError(ValueError):
    """The request cannot be translated without losing or guessing content."""


class ToolCallAsText(MappingError):
    """An advertised tool-call signature appeared in assistant output text."""


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class BridgeState:
    """Process-local provenance. Explicit entries must bind their exact SHA256.

    Keep one state per trusted client/run; never share it across unrelated users.
    Nothing is persisted. Overflow fails rather than evicting needed provenance.
    """

    known_plaintext: dict[str, str] = field(default_factory=dict)
    max_entries: int = 10000
    _lock: threading.RLock = field(default_factory=threading.RLock, repr=False)

    def __post_init__(self):
        self.known_plaintext = dict(self.known_plaintext)
        if any(not isinstance(v, str) or digest(v) != k for k, v in self.known_plaintext.items()):
            raise MappingError("Known plaintext hash mismatch")
        if len(self.known_plaintext) > self.max_entries:
            raise MappingError("Plaintext provenance capacity exceeded")

    def remember(self, values):
        entries = {digest(value): value for value in values}
        with self._lock:
            if len(set(self.known_plaintext) | set(entries)) > self.max_entries:
                raise MappingError("Plaintext provenance capacity exceeded")
            self.known_plaintext.update(entries)

    def recover(self, value):
        if not isinstance(value, str):
            raise MappingError("Invalid encrypted collaboration value")
        with self._lock:
            known = self.known_plaintext.get(digest(value))
        if known != value:
            raise MappingError("Encrypted collaboration content has no plaintext provenance")
        return value


@dataclass
class MappingContext:
    state: BridgeState
    names: dict[str, tuple[str | None, str]]
    reverse: dict[tuple[str | None, str], str]
    text_tails: dict[tuple, str] = field(default_factory=dict)
    reasoning_done: dict[tuple[int, str], dict] = field(default_factory=dict)

    def check_text(self, text, key=None):
        # This is an error guard, never a tool-call parser. Only match names
        # actually advertised in this request, and retain a bounded suffix so
        # an SSE delta boundary cannot hide the exact signature.
        if not isinstance(text, str):
            return
        markers = ["<tool_call><function=" + name for name in self.names]
        if not markers:
            return
        combined = self.text_tails.get(key, "") + text if key is not None else text
        if any(marker in combined for marker in markers):
            raise ToolCallAsText("Tool-call markup in assistant output text")
        if key is not None:
            self.text_tails[key] = combined[-(max(map(len, markers)) - 1):]


COLLABORATION_CALLS = {"spawn_agent", "send_message", "followup_task"}


def _strip_schema(value):
    if not isinstance(value, dict):
        return value
    result = copy.deepcopy(value)
    result.pop("encrypted", None)
    for key in ("properties", "$defs", "definitions", "patternProperties"):
        if isinstance(result.get(key), dict):
            result[key] = {name: _strip_schema(schema) for name, schema in result[key].items()}
    for key in ("items", "additionalProperties", "contains", "not", "if", "then", "else", "propertyNames"):
        if key in result:
            result[key] = _strip_schema(result[key])
    for key in ("anyOf", "oneOf", "allOf", "prefixItems"):
        if isinstance(result.get(key), list):
            result[key] = [_strip_schema(schema) for schema in result[key]]
    return result


def _content(content, state, *, multimodal=False):
    if not isinstance(content, list):
        raise MappingError("Collaboration content must be a list")
    result = []
    for part in content:
        if not isinstance(part, dict):
            raise MappingError("Invalid collaboration content part")
        kind = part.get("type")
        if kind == "encrypted_content":
            result.append({"type": "input_text", "text": state.recover(part.get("encrypted_content"))})
        elif kind == "input_text" and isinstance(part.get("text"), str):
            result.append(copy.deepcopy(part))
        elif multimodal and kind in {"input_image", "input_audio"}:
            result.append(copy.deepcopy(part))
        else:
            raise MappingError("Unsupported collaboration content part")
    return result


def _flatten_tools(tools, state):
    if not isinstance(tools, list):
        raise MappingError("Tools must be a list")
    reserved = {t.get("name") for t in tools if isinstance(t, dict) and t.get("type") != "namespace"}
    flattened, names, reverse = [], {}, {}
    for tool in tools:
        if not isinstance(tool, dict):
            raise MappingError("Invalid tool definition")
        if tool.get("type") == "namespace" and not isinstance(tool.get("name"), str):
            raise MappingError("Namespace name is required")
        namespace = tool.get("name") if tool.get("type") == "namespace" else None
        children = tool.get("tools") if namespace is not None else [tool]
        if not isinstance(children, list):
            raise MappingError("Namespace tools must be a list")
        for child in children:
            child = copy.deepcopy(child)
            if not isinstance(child, dict):
                raise MappingError("Invalid namespace tool")
            name = child.get("name")
            if child.get("type") != "function":
                if namespace is not None:
                    raise MappingError("Only function namespace tools are supported")
                flattened.append(child)
                continue
            if not isinstance(name, str) or not name or (namespace is not None and not isinstance(namespace, str)):
                raise MappingError("Invalid function identity")
            identity = (namespace, name)
            if identity in reverse:
                raise MappingError("Duplicate function identity")
            wire = name
            if namespace is not None:
                label = re.sub(r"[^a-zA-Z0-9_-]", "_", namespace + "__" + name)[:38]
                base = label + "_" + digest(json.dumps(identity))[:16]
                wire, suffix = base, 0
                while wire in reserved or wire in names:
                    suffix += 1
                    wire = base + "_" + str(suffix)
            if wire in names:
                raise MappingError("Function wire name collision")
            child["name"] = wire
            if namespace is not None and tool.get("description"):
                child["description"] = str(tool["description"]) + "\n" + child.get("description", "")
            child.pop("namespace", None)
            if "parameters" in child:
                child["parameters"] = _strip_schema(child["parameters"])
            flattened.append(child)
            names[wire], reverse[identity] = identity, wire
    return flattened, MappingContext(state, names, reverse)


def _check_function_content(item):
    # Pinned FunctionCall carries a separate optional encryption envelope.
    # Absent/null/empty-string carry no opaque value; reject every nonempty
    # envelope and malformed type, irrespective of readable argument strings.
    content = item.get("encrypted_content")
    if content is not None and (not isinstance(content, str) or content != ""):
        raise MappingError("Encrypted function call content is unsupported")


def _request_function(item, context):
    _check_function_content(item)
    identity = (item.get("namespace"), item.get("name"))
    if identity not in context.reverse:
        raise MappingError("Function identity missing from request tools")
    if "encrypted_function_args" in item and item["encrypted_function_args"] != []:
        raise MappingError("Encrypted function arguments are unsupported")
    item["name"] = context.reverse[identity]
    item.pop("namespace", None)
    item.pop("encrypted_function_args", None)


def translate_request(body: dict, state: BridgeState | None = None):
    """Return a detached ordinary Responses request and its reversible context."""
    if not isinstance(body, dict):
        raise MappingError("Request must be an object")
    mapped = copy.deepcopy(body)
    state = state if state is not None else BridgeState()
    mapped["tools"], context = _flatten_tools(mapped.get("tools", []), state)
    inputs = mapped.get("input", [])
    if isinstance(inputs, str):
        inputs = []
    if not isinstance(inputs, list):
        raise MappingError("Request input must be text or a list")
    for index, item in enumerate(inputs):
        if not isinstance(item, dict):
            raise MappingError("Invalid input item")
        if item.get("type") == "agent_message":
            # JSON framing avoids delimiter ambiguity in untrusted agent names.
            envelope = {key: item[key] for key in item if key not in {"type", "content"}}
            inputs[index] = {"type": "message", "role": "user", "content": [
                {"type": "input_text", "text": "Agent message envelope: " + json.dumps(envelope, sort_keys=True, ensure_ascii=False) + "\n"},
                *_content(item.get("content"), state)]}
        elif item.get("type") == "function_call":
            _request_function(item, context)
        elif item.get("type") == "function_call_output":
            if isinstance(item.get("output"), list):
                item["output"] = _content(item["output"], state, multimodal=True)
            elif not isinstance(item.get("output"), str):
                raise MappingError("Unsupported function output")
            if not item.get("call_id"):
                envelope = {key: value for key, value in item.items() if key not in {"type", "output"}}
                output = item["output"]
                content = output if isinstance(output, list) else [{"type": "input_text", "text": output}]
                inputs[index] = {"type": "message", "role": "user", "content": [
                    {"type": "input_text", "text": "Unpaired tool output envelope: " + json.dumps(envelope, sort_keys=True, ensure_ascii=False) + "\n"},
                    *content]}
            elif item.get("name") is not None:
                _request_function(item, context)
    choice = mapped.get("tool_choice")
    if isinstance(choice, dict):
        if choice.get("type") == "function":
            _request_function(choice, context)
        elif choice.get("type") == "allowed_tools":
            for tool in choice.get("tools", []):
                if tool.get("type") == "function":
                    _request_function(tool, context)
    return mapped, context


def _response_item(item, context, pending_plaintext):
    if isinstance(item, dict) and item.get("type") == "reasoning":
        # Codex requires a summary array, even when no summary was supplied.
        if item.get("summary") is None:
            item["summary"] = []
        # Pinned ReasoningItemContent accepts reasoning_text/text, not the
        # output_text emitted by some Responses providers. Keep all payloads.
        if isinstance(item.get("content"), list):
            for part in item["content"]:
                if isinstance(part, dict) and part.get("type") == "output_text" and isinstance(part.get("text"), str):
                    part["type"] = "reasoning_text"
    if isinstance(item, dict) and item.get("type") == "message" and item.get("role") == "assistant":
        for part in item.get("content", []):
            if isinstance(part, dict) and part.get("type") == "output_text":
                context.check_text(part.get("text"))
    if not isinstance(item, dict) or item.get("type") != "function_call":
        return
    _check_function_content(item)
    if "encrypted_function_args" in item and item["encrypted_function_args"] != []:
        raise MappingError("Unexpected upstream encrypted function arguments")
    identity = context.names.get(item.get("name"))
    if identity is None:
        raise MappingError("Upstream returned an unknown function")
    namespace, name = identity
    item["name"] = name
    if namespace is not None:
        item["namespace"] = namespace
    if namespace == "collaboration" and name in COLLABORATION_CALLS:
        item["encrypted_function_args"] = []
        arguments = item.get("arguments", "")
        # added events may contain empty/partial arguments. Only completed JSON
        # gets recorded, and only the documented collaboration message fields.
        try:
            parsed = json.loads(arguments)
        except (ValueError, TypeError):
            return
        if isinstance(parsed, dict):
            pending_plaintext.extend(parsed[key] for key in ("message", "prompt")
                                     if isinstance(parsed.get(key), str))


def _map_response_json(body, context, pending_plaintext):
    mapped = copy.deepcopy(body)
    if not isinstance(mapped, dict):
        raise MappingError("Upstream response must be an object")
    if not isinstance(mapped.get("output", []), list):
        raise MappingError("Upstream output must be a list")
    for item in mapped.get("output", []):
        _response_item(item, context, pending_plaintext)
    return mapped


def map_response_json(body: dict, context: MappingContext):
    pending_plaintext = []
    mapped = _map_response_json(body, context, pending_plaintext)
    context.state.remember(pending_plaintext)
    return mapped


def _terminal_reasoning(item, index, completed):
    """Reconcile only the captured summary-as-message duplicate representation."""
    if not isinstance(item, dict) or item.get("type") != "reasoning":
        return item
    previous = completed.get((index, item.get("id"))) if isinstance(item.get("id"), str) else None
    if previous is None or set(previous) - {"type", "id", "summary", "encrypted_content"}:
        return item
    if (set(item) - {"type", "id", "status", "role", "content", "summary", "encrypted_content"}
            or item.get("summary") is not None
            or item.get("status") != "completed" or item.get("role") != "assistant"
            or ("encrypted_content" in item) != ("encrypted_content" in previous)
            or item.get("encrypted_content") != previous.get("encrypted_content")):
        return item
    summary, content = previous.get("summary"), item.get("content")
    if (not isinstance(summary, list) or len(summary) != 1
            or not isinstance(summary[0], dict) or set(summary[0]) != {"type", "text"}
            or summary[0].get("type") != "summary_text" or not isinstance(summary[0].get("text"), str)
            or not isinstance(content, list) or len(content) != 1 or not isinstance(content[0], dict)
            or set(content[0]) - {"type", "text", "annotations"}
            or content[0].get("type") != "output_text"
            or content[0].get("annotations", []) != []
            or content[0].get("text") != summary[0]["text"]):
        return item
    return copy.deepcopy(previous)


def map_sse_event(event: dict, context: MappingContext):
    """Map a decoded SSE data object, preserving event IDs and delta ordering."""
    mapped = copy.deepcopy(event)
    if not isinstance(mapped, dict):
        raise MappingError("Upstream SSE data must be an object")
    pending_plaintext = []
    kind = mapped.get("type")
    # Context is request-local. Also discard completed items on response start
    # and terminal events so a reused context cannot reuse another response.
    completed = {} if kind == "response.created" else context.reasoning_done
    if mapped.get("type") == "response.output_text.delta":
        context.check_text(mapped.get("delta"), (mapped.get("item_id"), mapped.get("content_index")))
    elif mapped.get("type") == "response.output_text.done":
        context.check_text(mapped.get("text"))
    if mapped.get("type") in {"response.output_item.added", "response.output_item.done"}:
        _response_item(mapped.get("item"), context, pending_plaintext)
    if isinstance(mapped.get("response"), dict):
        if kind in {"response.completed", "response.incomplete"} and isinstance(mapped["response"].get("output"), list):
            mapped["response"]["output"] = [
                _terminal_reasoning(item, index, completed)
                for index, item in enumerate(mapped["response"]["output"])]
        mapped["response"] = _map_response_json(mapped["response"], context, pending_plaintext)
    context.state.remember(pending_plaintext)
    # Commit the detached cache only after the event and provenance succeed.
    if kind in {"response.created", "response.completed", "response.incomplete", "response.failed", "error"}:
        context.reasoning_done.clear()
    elif kind == "response.output_item.done":
        item, index = mapped.get("item"), mapped.get("output_index")
        if (isinstance(item, dict) and item.get("type") == "reasoning"
                and type(index) is int and index >= 0 and isinstance(item.get("id"), str) and item["id"]):
            context.reasoning_done.setdefault((index, item["id"]), copy.deepcopy(item))
    return mapped


def map_sse_frame(frame: bytes, context: MappingContext) -> bytes:
    """Map complete UTF-8 SSE frames; preserve comments/event/id/retry fields."""
    text = frame.decode("utf-8")
    lines = text.splitlines()
    data = [line[5:].lstrip(" ") for line in lines if line.startswith("data:")]
    if not data or "\n".join(data) == "[DONE]":
        return frame
    try:
        mapped = map_sse_event(json.loads("\n".join(data)), context)
    except ToolCallAsText:
        raise
    except (ValueError, TypeError) as error:
        raise MappingError("Invalid upstream SSE data") from error
    kept = [line for line in lines if not line.startswith("data:")]
    return ("\n".join(kept + ["data: " + json.dumps(mapped, separators=(",", ":"), ensure_ascii=False)]) + "\n\n").encode("utf-8")
