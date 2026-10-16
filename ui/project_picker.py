# =============================================================================
#  Codermuks in Termux — меню выбора проектов v1.2.0
# =============================================================================

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from core.project import Project
from core.workspace import delete_project, list_projects


console = Console()

COLOR_MAIN = "bright_green"
COLOR_ACCENT = "bright_cyan"
COLOR_WARN = "yellow"
COLOR_ERROR = "bright_red"
COLOR_DIM = "grey62"


def _build_table() -> Table:
    projects = list_projects()
    table = Table(show_header=False, box=None, padding=(0, 1))

    table.add_column(justify="right", style=COLOR_ACCENT, no_wrap=True)
    table.add_column(style="white", no_wrap=True)
    table.add_column(style=COLOR_DIM, no_wrap=False)
    table.add_column(style=COLOR_ACCENT, no_wrap=True)

    if not projects:
        table.add_row("", "[dim]пока нет проектов[/dim]", "", "")
        return table

    for idx, p in enumerate(projects, start=1):
        name = p["name"]
        lang = p.get("language") or "?"
        files = p.get("files_count", 0)
        info = f"{lang}, {files} файл(ов)"
        table.add_row(f"[{idx}]", name, info, "")

    return table


def print_projects() -> None:
    """Печатает список проектов пользователя."""
    projects = list_projects()

    title = Text()
    title.append("📁 ", style="bold")
    title.append("Мои проекты", style=f"bold {COLOR_ACCENT}")

    console.print()
    console.print(Panel(title, border_style=COLOR_ACCENT, padding=(0, 2)))
    console.print()

    if not projects:
        console.print(Text("  Проектов пока нет.", style=COLOR_DIM))
        console.print(Text("  Задай первую задачу — codermuks создаст проект сам.", style=COLOR_DIM))
        console.print()
        return

    console.print(_build_table())
    console.print()
    console.print(Text(f"  Всего: {len(projects)}", style=COLOR_DIM))
    console.print(Text(f"  Путь: ~/codermuks-workspace/", style=COLOR_DIM))
    console.print()


def pick_project() -> Project | None:
    """Простое меню выбора проекта для удаления."""
    projects = list_projects()
    if not projects:
        console.print()
        console.print(Text("  Нет проектов.", style=COLOR_WARN))
        console.print()
        return None

    print_projects()
    console.print(Text("  Введи номер проекта для удаления или 'exit':", style=COLOR_ACCENT))

    try:
        answer = console.input("  ▸ ").strip()
    except (KeyboardInterrupt, EOFError):
        console.print()
        return None

    if answer.lower() in ("exit", "q", "quit", "выход"):
        return None

    try:
        idx = int(answer)
    except ValueError:
        console.print(Text("  Неверный ввод.", style=COLOR_WARN))
        return None

    if idx < 1 or idx > len(projects):
        console.print(Text("  Такого номера нет.", style=COLOR_WARN))
        return None

    chosen = projects[idx - 1]
    name = chosen["name"]

    console.print()
    console.print(Text(f"  Удалить проект '{name}'? [y/N]:", style=COLOR_ERROR))
    try:
        confirm = console.input("  ▸ ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        return None

    if confirm in ("y", "yes", "д", "да"):
        if delete_project(name):
            console.print(Text(f"  ✔ Проект '{name}' удалён.", style=COLOR_MAIN))
        else:
            console.print(Text("  ✘ Не удалось удалить.", style=COLOR_ERROR))
    else:
        console.print(Text("  Отменено.", style=COLOR_DIM))

    console.print()
    return None


__all__ = ["print_projects", "pick_project"]
