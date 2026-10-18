# =============================================================================
#  Codermuks in Termux — просмотр зависимостей проекта v1.4.0
# =============================================================================

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from core.library_manager import LibraryManager
from core.project import Project


console = Console()

COLOR_MAIN = "bright_green"
COLOR_ACCENT = "bright_cyan"
COLOR_WARN = "yellow"
COLOR_ERROR = "bright_red"
COLOR_DIM = "grey62"


def _read_requirements(project_path: Path) -> list[str]:
    """Читает requirements.txt проекта, если есть."""
    req_file = project_path / "requirements.txt"
    if not req_file.exists():
        return []

    result: list[str] = []
    try:
        for line in req_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            result.append(line)
    except OSError:
        pass
    return result


def show_deps(project_name: str = "") -> None:
    """
    Показывает зависимости проекта.

    Если project_name не указан — показывает список всех проектов
    и подсказку, как посмотреть конкретный.
    """
    console.print()

    if not project_name:
        # Список всех проектов с количеством зависимостей.
        from core.workspace import list_projects
        projects = list_projects()
        if not projects:
            console.print(Text("  Проектов пока нет.", style=COLOR_DIM))
            console.print()
            return

        title = Text()
        title.append("📦 ", style="bold")
        title.append("Зависимости по проектам", style=f"bold {COLOR_ACCENT}")
        console.print(Panel(title, border_style=COLOR_ACCENT, padding=(0, 2)))
        console.print()

        for p in projects:
            name = p["name"]
            reqs = _read_requirements(p["path"])
            line = Text()
            line.append(f"  • {name}", style=COLOR_MAIN)
            line.append(f"  — {len(reqs)} завис.", style=COLOR_DIM)
            console.print(line)

        console.print()
        console.print(Text("  Детали: /deps <имя_проекта>", style=COLOR_DIM))
        console.print()
        return

    # Конкретный проект.
    proj = Project.open(project_name)
    if proj is None:
        console.print(Text(f"  Проект '{project_name}' не найден.", style=COLOR_WARN))
        console.print()
        return

    reqs = _read_requirements(proj.path)

    title = Text()
    title.append("📦 ", style="bold")
    title.append(f"Зависимости проекта {project_name}", style=f"bold {COLOR_ACCENT}")
    console.print(Panel(title, border_style=COLOR_ACCENT, padding=(0, 2)))
    console.print()

    if not reqs:
        console.print(Text("  Зависимостей нет.", style=COLOR_DIM))
        console.print()
        return

    lm = LibraryManager()
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column(style="bold", no_wrap=True)
    table.add_column(style="white", no_wrap=True)
    table.add_column(style=COLOR_DIM, no_wrap=False)

    for req in reqs:
        # Для git+ и с версиями — берём только имя пакета.
        import_name = req
        if import_name.startswith("git+"):
            import_name = import_name.rsplit("/", 1)[-1].replace(".git", "")
        else:
            import_name = import_name.split("==")[0].split(">=")[0].split("<=")[0].strip()

        installed = lm.check(import_name)

        if installed:
            icon = "[green]✔[/green]"
            hint = ""
        else:
            icon = "[red]✘[/red]"
            hint = f"pip install {import_name}"

        table.add_row(icon, req, hint)

    console.print(table)
    console.print()

    installed_count = sum(
        1 for r in reqs
        if lm.check(r.rsplit("/", 1)[-1].replace(".git", "").split("==")[0])
    )
    console.print(Text(
        f"  Установлено: {installed_count} из {len(reqs)}",
        style=COLOR_DIM,
    ))
    console.print()


__all__ = ["show_deps"]
