# =============================================================================
#  Codermuks in Termux — запуск проектов v1.4.0
# =============================================================================

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from core.project import Project


console = Console()

COLOR_MAIN = "bright_green"
COLOR_ACCENT = "bright_cyan"
COLOR_WARN = "yellow"
COLOR_ERROR = "bright_red"
COLOR_DIM = "grey62"


# Что запускать для каждого языка.
RUN_COMMANDS = {
    "python":     ["python"],
    "javascript": ["node"],
    "go":         ["go", "run"],
    "rust":       ["sh", "-c", "rustc \"$1\" -o /tmp/_run_bin && /tmp/_run_bin && rm -f /tmp/_run_bin", "sh"],
    "cpp":        ["sh", "-c", "g++ \"$1\" -o /tmp/_run_bin -std=c++17 && /tmp/_run_bin && rm -f /tmp/_run_bin", "sh"],
    "c":          ["sh", "-c", "gcc \"$1\" -o /tmp/_run_bin && /tmp/_run_bin && rm -f /tmp/_run_bin", "sh"],
    "java":       ["java"],
    "ruby":       ["ruby"],
    "php":        ["php"],
    "lua":        ["lua"],
    "r":          ["Rscript"],
    "sql":        ["sqlite3", ":memory:", ".read"],
}


def _find_main_file(proj: Project, language: str) -> Path | None:
    """Ищет главный файл проекта."""
    files = proj.list_files()
    if not files:
        return None

    # Приоритеты по имени.
    preferred = ["main", "app", "start", "run", "index"]

    # Расширения по языку.
    ext_map = {
        "python": [".py"],
        "javascript": [".js"],
        "go": [".go"],
        "rust": [".rs"],
        "cpp": [".cpp", ".cc", ".cxx"],
        "c": [".c"],
        "java": [".java"],
        "ruby": [".rb"],
        "php": [".php"],
        "lua": [".lua"],
        "r": [".r", ".R"],
        "sql": [".sql"],
    }
    exts = ext_map.get(language, [])

    # 1. main.* с нужным расширением.
    for pref in preferred:
        for f in files:
            name = Path(f).stem.lower()
            if name == pref and Path(f).suffix in exts:
                return proj.path / f

    # 2. Первый файл с нужным расширением.
    for f in files:
        if Path(f).suffix in exts:
            return proj.path / f

    return None


def run_project(project_name: str, timeout: int = 30) -> None:
    """Запускает главный файл проекта."""
    console.print()

    proj = Project.open(project_name)
    if proj is None:
        console.print(Text(f"  Проект '{project_name}' не найден.", style=COLOR_WARN))
        console.print()
        return

    language = proj.language or "python"
    main_file = _find_main_file(proj, language)

    if main_file is None:
        console.print(Text(f"  Не нашёл файл для запуска в {project_name}.", style=COLOR_WARN))
        console.print()
        return

    cmd_template = RUN_COMMANDS.get(language)
    if cmd_template is None:
        console.print(Text(f"  Язык '{language}' не поддерживается для запуска.", style=COLOR_WARN))
        console.print()
        return

    # Формируем команду.
    if language in ("rust", "cpp", "c"):
        cmd = cmd_template[:3] + [str(main_file)] + cmd_template[3:]
    elif language == "sql":
        cmd = cmd_template + [str(main_file)]
    elif language == "go":
        cmd = cmd_template + [str(main_file)]
    else:
        cmd = cmd_template + [str(main_file)]

    title = Text()
    title.append("▶ ", style="bold")
    title.append(f"Запускаю {project_name}", style=f"bold {COLOR_ACCENT}")
    console.print(Panel(title, border_style=COLOR_ACCENT, padding=(0, 2)))
    console.print()
    console.print(Text(f"  Файл: {main_file.relative_to(proj.path)}", style=COLOR_DIM))
    console.print(Text(f"  Команда: {' '.join(cmd)}", style=COLOR_DIM))
    console.print()

    try:
        result = subprocess.run(
            cmd,
            cwd=str(proj.path),
            capture_output=True,
            text=True,
            timeout=timeout,
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        console.print(Text(f"  ⏱ Таймаут {timeout} сек.", style=COLOR_ERROR))
        console.print()
        return
    except FileNotFoundError as exc:
        console.print(Text(f"  ✘ Не найден исполняемый файл: {exc}", style=COLOR_ERROR))
        console.print()
        return

    if result.stdout:
        console.print(Text("--- stdout ---", style=COLOR_DIM))
        console.print(Text(result.stdout.rstrip(), style="white"))
        console.print()

    if result.stderr:
        console.print(Text("--- stderr ---", style=COLOR_ERROR))
        console.print(Text(result.stderr.rstrip(), style="white"))
        console.print()

    if result.returncode == 0:
        console.print(Text(f"  ✔ Готово (exit 0)", style=COLOR_MAIN))
    else:
        console.print(Text(f"  ✘ Завершилось с кодом {result.returncode}", style=COLOR_ERROR))
    console.print()


__all__ = ["run_project", "RUN_COMMANDS"]
