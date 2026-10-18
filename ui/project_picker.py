# =============================================================================
#  Codermuks in Termux — меню проектов v1.4.0
# =============================================================================

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from core.project import Project
from core.workspace import delete_project, list_projects
from utils.exporter import export_project, export_info


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

    if not projects:
        table.add_row("", "[dim]пока нет проектов[/dim]", "")
        return table

    for idx, p in enumerate(projects, start=1):
        name = p["name"]
        lang = p.get("language") or "?"
        files = p.get("files_count", 0)
        info = f"{lang}, {files} файл(ов)"
        table.add_row(f"[{idx}]", name, info)
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
    console.print(Text("  Действия:", style=COLOR_ACCENT))
    console.print(Text("    /open <имя>    — продолжить работу с проектом", style=COLOR_DIM))
    console.print(Text("    /delete <имя>  — удалить проект", style=COLOR_DIM))
    console.print(Text("    /export <имя>  — сохранить ZIP в память телефона", style=COLOR_DIM))
    console.print(Text("    /deps <имя>    — зависимости проекта", style=COLOR_DIM))
    console.print(Text("    /run <имя>     — запустить проект", style=COLOR_DIM))
    console.print()


# -----------------------------------------------------------------------------
#  /open
# -----------------------------------------------------------------------------

def open_project(name: str) -> str:
    """
    Проверяет, что проект существует, и возвращает его имя.

    Возвращает пустую строку, если проекта нет.
    """
    console.print()
    if not name:
        console.print(Text("  Укажи имя проекта: /open <имя>", style=COLOR_WARN))
        console.print()
        return ""

    proj = Project.open(name)
    if proj is None:
        console.print(Text(f"  Проект '{name}' не найден.", style=COLOR_WARN))
        console.print()
        return ""

    files = proj.list_files()
    lang = proj.language or "?"

    console.print(
        Text(f"  ✔ Открыт проект: ", style=COLOR_MAIN)
        + Text(f"{name} ", style=f"bold {COLOR_ACCENT}")
        + Text(f"({lang}, {len(files)} файл(ов))", style=COLOR_DIM)
    )
    console.print(Text(f"    Дальше все задачи пойдут в него.", style=COLOR_DIM))
    console.print()
    return name


# -----------------------------------------------------------------------------
#  /delete
# -----------------------------------------------------------------------------

def delete_project_interactive(name: str) -> bool:
    """Спрашивает подтверждение и удаляет проект."""
    console.print()
    if not name:
        console.print(Text("  Укажи имя проекта: /delete <имя>", style=COLOR_WARN))
        console.print()
        return False

    proj = Project.open(name)
    if proj is None:
        console.print(Text(f"  Проект '{name}' не найден.", style=COLOR_WARN))
        console.print()
        return False

    try:
        answer = console.input(
            f"  Удалить проект '{name}'? [y/N]: "
        ).strip().lower()
    except (KeyboardInterrupt, EOFError):
        console.print()
        return False

    if answer not in ("y", "yes", "д", "да"):
        console.print(Text("  Отменено.", style=COLOR_DIM))
        console.print()
        return False

    if delete_project(name):
        console.print(Text(f"  ✔ Проект '{name}' удалён.", style=COLOR_MAIN))
    else:
        console.print(Text("  ✘ Не удалось удалить.", style=COLOR_ERROR))
    console.print()
    return True


# -----------------------------------------------------------------------------
#  /export
# -----------------------------------------------------------------------------

def export_project_interactive(name: str) -> None:
    """Экспортирует проект в ZIP."""
    console.print()
    if not name:
        console.print(Text("  Укажи имя проекта: /export <имя>", style=COLOR_WARN))
        console.print()
        return

    info = export_info(name)
    if not info:
        console.print(Text(f"  Проект '{name}' не найден.", style=COLOR_WARN))
        console.print()
        return

    console.print(Text(f"  📦 Экспорт проекта {name}...", style=COLOR_ACCENT))
    result = export_project(name)

    if result is None:
        console.print(Text("  ✘ Не удалось создать ZIP.", style=COLOR_ERROR))
        console.print()
        return

    size_kb = result.stat().st_size / 1024
    console.print(Text(f"  ✔ Готово: {result}", style=COLOR_MAIN))
    console.print(Text(f"    Файлов: {info['files_count']}, {size_kb:.1f} КБ", style=COLOR_DIM))
    console.print()


# -----------------------------------------------------------------------------
#  Старый pick_project (для совместимости)
# -----------------------------------------------------------------------------

def pick_project() -> Project | None:
    """Совместимость со старым API."""
    projects = list_projects()
    if not projects:
        console.print()
        console.print(Text("  Нет проектов.", style=COLOR_WARN))
        console.print()
        return None
    print_projects()
    return None


__all__ = [
    "print_projects",
    "pick_project",
    "open_project",
    "delete_project_interactive",
    "export_project_interactive",
]
