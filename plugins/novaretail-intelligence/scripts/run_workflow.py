"""Locate the course repository and delegate to the shared session 7 CLI."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


def find_repository(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "pyproject.toml").exists() and (candidate / "apps" / "sesion7_workflow_cli.py").exists():
            return candidate
    raise RuntimeError("No se encontro el repositorio del curso.")


def main() -> int:
    repository = find_repository(Path(__file__).resolve())
    command = [sys.executable, str(repository / "apps" / "sesion7_workflow_cli.py"), *sys.argv[1:]]
    return subprocess.call(command, cwd=repository)


if __name__ == "__main__":
    raise SystemExit(main())
