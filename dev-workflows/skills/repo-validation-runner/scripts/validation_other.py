from __future__ import annotations

from pathlib import Path

from validation_common import add


MAKE_TARGETS = {
    "lint": ["lint"],
    "typecheck": ["typecheck", "type-check"],
    "unit": ["test", "unit"],
    "integration": ["integration", "e2e"],
    "build": ["build"],
    "docs": ["docs"],
}


def detect_makefile(root: Path, candidates: list[dict]) -> None:
    path = root / "Makefile"
    if not path.exists():
        return

    targets = set()
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line or line.startswith(("#", "\t", " ")):
            continue
        target = line.split(":", 1)[0].strip()
        if target:
            targets.add(target)

    for category, names in MAKE_TARGETS.items():
        for name in names:
            if name in targets:
                add(candidates, category, f"make {name}", f"Makefile target {name}")


def detect_dotnet(root: Path, candidates: list[dict]) -> None:
    projects = list(root.glob("*.csproj")) + list(root.glob("*.sln"))
    if not projects:
        return

    evidence = ", ".join(project.name for project in projects[:3])
    add(candidates, "build", "dotnet build", evidence)
    if any("test" in project.name.lower() for project in root.rglob("*.csproj")):
        add(candidates, "unit", "dotnet test", "test *.csproj")
