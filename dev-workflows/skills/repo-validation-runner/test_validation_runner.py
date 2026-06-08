from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent
SCRIPT = SKILL_ROOT / "scripts" / "detect_validation_commands.py"


class ValidationRunnerEntrypointTests(unittest.TestCase):
    def test_cli_reports_candidate_detector_role(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "README.md").write_text("# Empty\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(root)],
                check=True,
                capture_output=True,
                text=True,
            )

        output = json.loads(result.stdout)
        self.assertEqual("candidate_detector", output["role"])
        self.assertEqual([], output["candidates"])


if __name__ == "__main__":
    unittest.main()
