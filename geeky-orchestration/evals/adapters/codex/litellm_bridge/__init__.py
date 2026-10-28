"""Local, fail-closed compatibility bridge for Codex V2 and Responses proxies."""

from .mapper import BridgeState, MappingError, map_response_json, map_sse_event, translate_request

__all__ = ["BridgeState", "MappingError", "translate_request", "map_response_json", "map_sse_event"]
