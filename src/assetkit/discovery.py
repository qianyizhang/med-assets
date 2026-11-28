"""Find package-owned declarations without descending into excluded directory trees."""

from pathlib import Path

SKIP_DIRS = frozenset({".git", ".artifacts", "node_modules", "__pycache__", ".venv", "src"})


def manifests(repo: Path, name: str) -> list[Path]:
    matches = []
    for directory, subdirs, files in repo.walk():
        subdirs[:] = [child for child in subdirs if child not in SKIP_DIRS]
        if name in files:
            matches.append(directory / name)
    return sorted(matches)
