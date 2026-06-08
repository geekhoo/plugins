from __future__ import annotations

from pathlib import Path
from typing import Iterator


SCRIPT_CATEGORIES = {
    "typecheck": ["typecheck", "type-check", "tsc"],
    "lint": ["lint", "eslint", "biome", "check"],
    "unit": ["test", "unit"],
    "integration": ["integration", "e2e"],
    "build": ["build", "compile"],
    "docs": ["docs", "doc"],
}

INSPECTED_CATEGORIES = ["node", "python", "makefile", "dotnet"]
UNSUPPORTED_CATEGORIES = [
    "browser",
    "database/migrations",
    "external services",
    "custom CI-only/domain checks",
]
PYTHON_EVIDENCE_FILES = [
    "pyproject.toml",
    "pytest.ini",
    "tox.ini",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "Pipfile",
    "poetry.lock",
]
SKIP_DIRS = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}


def package_runner(root: Path) -> str:
    if (root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (root / "yarn.lock").exists():
        return "yarn"
    return "npm"


def add(candidates: list[dict], category: str, command: str, evidence: str) -> None:
    candidates.append({"category": category, "command": command, "evidence": evidence})


def iter_files(root: Path, patterns: list[str]) -> Iterator[Path]:
    for pattern in patterns:
        for path in root.rglob(pattern):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            yield path


def relative_evidence(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()
