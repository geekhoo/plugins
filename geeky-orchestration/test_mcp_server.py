from __future__ import annotations

import ast
import unittest
from pathlib import Path


SERVER = Path(__file__).resolve().parent / "mcp" / "server.py"


def _server_tree() -> ast.Module:
    return ast.parse(SERVER.read_text(encoding="utf-8"), filename=str(SERVER))


def _spawn_calls(tree: ast.Module) -> list[ast.Call]:
    """Every asyncio.create_subprocess_exec call in the server."""
    calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "create_subprocess_exec":
            calls.append(node)
    return calls


def _keyword(call: ast.Call, name: str) -> ast.expr | None:
    for kw in call.keywords:
        if kw.arg == name:
            return kw.value
    return None


def _result_exprs(expr: ast.expr) -> list[ast.expr]:
    """The expressions that could actually become the argument's value.

    A plain walk would flag the `None` in `stdin_text is not None`, which is a
    test of the *caller's* argument and says nothing about what the child gets.
    Only the branches of a conditional can be the value.
    """
    if isinstance(expr, ast.IfExp):
        return _result_exprs(expr.body) + _result_exprs(expr.orelse)
    return [expr]


class StdioTransportGuardTests(unittest.TestCase):
    """A subprocess of a stdio MCP server must never be handed the transport.

    On stdio the server's own stdin is the pipe the host talks to it on. A child
    that inherits it stalls before it runs any code, and the tool call never
    returns -- four of the six tools hung this way until 0.2.15. `stdin=None`
    means *inherit*, so the spawn site must always name a real target.

    These are source assertions on purpose: they cost no `uv` resolve and no
    server launch, so unlike wire_baseline.py they can run on every commit.
    """

    def test_server_has_a_spawn_site(self) -> None:
        self.assertTrue(_spawn_calls(_server_tree()),
                        "no create_subprocess_exec call found -- this guard has gone stale")

    def test_every_spawn_passes_stdin_explicitly(self) -> None:
        for call in _spawn_calls(_server_tree()):
            with self.subTest(line=call.lineno):
                self.assertIsNotNone(
                    _keyword(call, "stdin"),
                    "create_subprocess_exec at line %d passes no stdin=; the child would "
                    "inherit the server's stdio transport" % call.lineno)

    def test_no_spawn_can_inherit_stdin(self) -> None:
        for call in _spawn_calls(_server_tree()):
            stdin = _keyword(call, "stdin")
            if stdin is None:
                continue                      # reported by the test above
            with self.subTest(line=call.lineno):
                inherits = any(isinstance(node, ast.Constant) and node.value is None
                               for node in _result_exprs(stdin))
                self.assertFalse(
                    inherits,
                    "create_subprocess_exec at line %d can pass stdin=None, which makes "
                    "the validator inherit the host's stdio pipe and hang" % call.lineno)

    def test_stdinless_spawns_use_devnull(self) -> None:
        for call in _spawn_calls(_server_tree()):
            stdin = _keyword(call, "stdin")
            if stdin is None:
                continue
            with self.subTest(line=call.lineno):
                names = {node.attr for node in ast.walk(stdin) if isinstance(node, ast.Attribute)}
                names |= {node.id for node in ast.walk(stdin) if isinstance(node, ast.Name)}
                self.assertIn(
                    "DEVNULL", names,
                    "create_subprocess_exec at line %d never routes stdin to DEVNULL; a "
                    "validator that is fed nothing needs a real empty stdin" % call.lineno)


if __name__ == "__main__":
    unittest.main()
