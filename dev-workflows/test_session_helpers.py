from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SCAN_SESSIONS = ROOT / "skills" / "list-sessions" / "scripts" / "scan_sessions.py"
SCAN_FRICTION = ROOT / "skills" / "session-friction-review" / "scripts" / "scan_friction.py"


class SessionHelperTests(unittest.TestCase):
    def test_scan_sessions_groups_real_and_background_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            claude_dir = Path(temp_dir) / ".claude"
            project = claude_dir / "projects" / "example-project"
            project.mkdir(parents=True)
            (project / "real-session.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "type": "user",
                                "timestamp": "2026-06-01T00:00:00Z",
                                "cwd": "C:/repo/example",
                                "gitBranch": "main",
                                "message": {"content": "Build the report"},
                            }
                        ),
                        json.dumps({"type": "assistant", "timestamp": "2026-06-01T00:01:00Z"}),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (project / "background-session.jsonl").write_text(
                json.dumps(
                    {
                        "type": "user",
                        "timestamp": "2026-06-01T01:00:00Z",
                        "cwd": "C:/repo/example",
                        "message": {"content": "You are a memory consolidation agent"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCAN_SESSIONS),
                    "--claude-dir",
                    str(claude_dir),
                    "--format",
                    "json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        output = json.loads(result.stdout)
        self.assertEqual(output["totals"]["projects"], 1)
        self.assertEqual(output["totals"]["real"], 1)
        self.assertEqual(output["totals"]["background"], 1)
        self.assertEqual(output["groups"][0]["displayPath"], "C:/repo/example")
        self.assertEqual(output["groups"][0]["real"][0]["firstPrompt"], "Build the report")

    def test_scan_friction_counts_signature_hits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            claude_dir = Path(temp_dir) / ".claude"
            project = claude_dir / "projects" / "example-project"
            project.mkdir(parents=True)
            (project / "session-123456789.jsonl").write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "timestamp": "2026-06-01T00:00:00Z",
                                "cwd": "C:/repo/example",
                            }
                        ),
                        "Failed with non-blocking status code: python3: command not found",
                        "no, i said use the local file",
                        "missing-tool: command not found",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCAN_FRICTION),
                    "--claude-dir",
                    str(claude_dir),
                    "--format",
                    "json",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        rows = json.loads(result.stdout)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["project"], "example")
        self.assertEqual(row["silent_hook"], 1)
        self.assertEqual(row["python"], 1)
        self.assertGreaterEqual(row["cmd"], 1)
        self.assertEqual(row["correction"], 1)


if __name__ == "__main__":
    unittest.main()
