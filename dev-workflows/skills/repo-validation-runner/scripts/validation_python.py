from __future__ import annotations

from pathlib import Path

from validation_common import PYTHON_EVIDENCE_FILES, add, iter_files, relative_evidence


def python_evidence(root: Path, pyproject_text: str) -> list[str]:
    evidence = []
    for name in PYTHON_EVIDENCE_FILES:
        if not (root / name).exists():
            continue
        if name == "pyproject.toml" and pyproject_text and "[tool.pytest" in pyproject_text:
            evidence.append("pyproject.toml [tool.pytest]")
        else:
            evidence.append(name)

    test_file = next(iter_files(root, ["test_*.py", "*_test.py"]), None)
    if test_file:
        evidence.append(relative_evidence(root, test_file))

    src_file = next(iter_files(root / "src", ["*.py"]), None) if (root / "src").is_dir() else None
    if src_file:
        evidence.append(relative_evidence(root, src_file))

    package_init = next(iter_files(root, ["__init__.py"]), None)
    if package_init:
        evidence.append(relative_evidence(root, package_init))

    return evidence


def detect_python(root: Path, candidates: list[dict]) -> None:
    pyproject = root / "pyproject.toml"
    pyproject_text = pyproject.read_text(encoding="utf-8", errors="ignore") if pyproject.exists() else ""
    pytest_evidence = python_evidence(root, pyproject_text)
    if pytest_evidence:
        add(candidates, "unit", "python -m pytest", ", ".join(pytest_evidence))

    if pyproject_text and "[tool.ruff" in pyproject_text:
        add(candidates, "lint", "python -m ruff check .", "pyproject.toml [tool.ruff]")
    if pyproject_text and "[tool.mypy" in pyproject_text:
        add(candidates, "typecheck", "python -m mypy .", "pyproject.toml [tool.mypy]")
