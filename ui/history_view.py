# =============================================================================
#  Codermuks in Termux — просмотр истории проектов v1.3.0
# =============================================================================

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from core.project import Project
from core.workspace import list_projects


console = Console()

COLOR_MAIN = "bright_green"
COLOR_ACCENT = "bright_cyan"
COLOR_WARN = "yellow"
COLOR_DIM = "grey62"


def show_history(project_name: str = "") -> None:
    """
    Показывает историю конкретного проекта или всех проектов.

    Если project_name пуст — показывает список проектов и подсказку.
    """
    console.print()

    if project_name:
        proj = Project.open(project_name)
        if proj is None:
            console.print(Text(f"  Проект '{project_name}' не найден.", style=COLOR_WARN))
            console.print()
            return

        title = Text()
        title.append("📜 ", style="bold")
        title.append(f"История проекта {project_name}", style=f"bold {COLOR_ACCENT}")
        console.print(Panel(title, border_style=COLOR_ACCENT, padding=(0, 2)))
        console.print()

        history_text = proj.format_history(limit=20)
        console.print(Text("  " + history_text.replace("\n", "\n  "), style="white"))
        console.print()

        summary = proj.summary()
        console.print(Text(f"  Всего задач: {summary['tasks_total']}", style=COLOR_DIM))
        console.print(Text(f"  Успешных: {summary['tasks_success']}", style=COLOR_DIM))
        console.print()
        return

    # Список всех проектов.
    projects = list_projects()
    if not projects:
        console.print(Text("  Нет проектов.", style=COLOR_DIM))
        console.print()
        return

    title = Text()
    title.append("📜 ", style="bold")
    title.append("История всех проектов", style=f"bold {COLOR_ACCENT}")
    console.print(Panel(title, border_style=COLOR_ACCENT, padding=(0, 2)))
    console.print()

    for p in projects:
        name = p["name"]
        lang = p.get("language") or "?"
        tasks = 0
        try:
            proj = Project.open(name)
            if proj:
                tasks = proj.summary()["tasks_total"]
        except Exception:
            pass

        line = Text()
        line.append(f"  • {name}", style=COLOR_MAIN)
        line.append(f"  ({lang})", style=COLOR_DIM)
        line.append(f"  — {tasks} задач", style=COLOR_DIM)
        console.print(line)

    console.print()
    console.print(Text("  Для детальной истории: /history <имя>", style=COLOR_DIM))
    console.print()


__all__ = ["show_history"]
