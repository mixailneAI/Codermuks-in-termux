# =============================================================================
#  Codermuks in Termux — меню выбора главного агента (/changeagent) v1.1.0
# =============================================================================

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from core.i18n import t
from core.team.agent_registry import get_registry


console = Console()

COLOR_MAIN = "bright_green"
COLOR_ACCENT = "bright_cyan"
COLOR_WARN = "yellow"
COLOR_ERROR = "bright_red"
COLOR_DIM = "grey62"
COLOR_OK = "bright_green"


def _build_agents_table() -> Table:
    """Собирает rich.Table со всеми агентами команды."""
    registry = get_registry()
    agents = registry.list_all()
    current_lead = registry.get_lead()

    table = Table(
        show_header=False,
        box=None,
        padding=(0, 1),
        expand=False,
    )

    table.add_column(justify="right", style=COLOR_ACCENT, no_wrap=True)
    table.add_column(justify="center", no_wrap=True)
    table.add_column(style="white", no_wrap=True)
    table.add_column(style=COLOR_DIM, no_wrap=False)
    table.add_column(style=COLOR_ACCENT, no_wrap=True)

    for idx, info in enumerate(agents, start=1):
        configured = registry.is_configured(info.name)
        is_lead = info.name == current_lead

        marker = "[green]OK[/green]" if configured else "[red]--[/red]"

        name_text = Text(info.display_name)
        if is_lead:
            name_text.stylize(f"bold {COLOR_MAIN}")

        desc = t(info.description_key)

        if is_lead:
            status = f"[bold {COLOR_MAIN}]{t('picker.agent.current')}[/bold {COLOR_MAIN}]"
        elif configured:
            status = f"[{COLOR_OK}]{t('picker.agent.configured')}[/{COLOR_OK}]"
        else:
            status = f"[{COLOR_ERROR}]{t('picker.agent.not_configured')}[/{COLOR_ERROR}]"

        table.add_row(f"[{idx}]", marker, name_text, desc, status)

    return table


def _print_menu() -> None:
    """Печатает заголовок, таблицу агентов и подсказку."""
    title = Text()
    title.append(">> ", style="bold")
    title.append(t("picker.agent.title"), style=f"bold {COLOR_ACCENT}")

    console.print()
    console.print(Panel(title, border_style=COLOR_ACCENT, padding=(0, 2)))

    table = _build_agents_table()
    console.print()
    console.print(table)
    console.print()

    hint = Text()
    hint.append("  i ", style=COLOR_DIM)
    hint.append(t("picker.agent.hint"), style=COLOR_DIM)
    console.print(hint)
    console.print()


def pick_agent(max_attempts: int = 5) -> bool:
    """
    Показывает меню выбора главного агента и меняет его при необходимости.

    Возвращает True, если агент был изменён, и False — если нет.
    """
    registry = get_registry()

    agents = registry.list_all()
    lead_before = registry.get_lead()

    _print_menu()

    for _ in range(max_attempts):
        try:
            answer = console.input(
                f"  [bold {COLOR_ACCENT}]>[/bold {COLOR_ACCENT}] "
                f"[white]{t('picker.agent.prompt')}[/white] "
            ).strip()
        except (KeyboardInterrupt, EOFError):
            console.print()
            console.print(
                Text(f"  {t('picker.agent.cancelled')}", style=COLOR_WARN)
            )
            console.print()
            return False

        if not answer:
            continue

        low = answer.lower()
        if low in ("exit", "quit", "q", "vihod", "выход"):
            console.print()
            console.print(
                Text(f"  {t('picker.agent.cancelled')}", style=COLOR_WARN)
            )
            console.print()
            return False

        try:
            index = int(answer)
        except ValueError:
            console.print(
                Text(f"  {t('picker.agent.invalid')}", style=COLOR_WARN)
            )
            console.print()
            continue

        if index < 1 or index > len(agents):
            console.print(
                Text(f"  {t('picker.agent.invalid')}", style=COLOR_WARN)
            )
            console.print()
            continue

        chosen = agents[index - 1]

        if chosen.name == lead_before:
            console.print()
            console.print(
                Text(
                    f"  i {t('picker.agent.already', name=chosen.display_name)}",
                    style=COLOR_DIM,
                )
            )
            console.print()
            return False

        if not registry.is_configured(chosen.name):
            console.print()
            console.print(
                Text(
                    f"  x {t('picker.agent.cannot_select', name=chosen.display_name)}",
                    style=COLOR_ERROR,
                )
            )
            console.print()
            continue

        try:
            registry.set_lead(chosen.name)
        except Exception as exc:
            console.print()
            console.print(Text(f"  x {exc}", style=COLOR_ERROR))
            console.print()
            continue

        console.print()
        console.print(
            Text(
                f"  OK {t('picker.agent.changed', name=chosen.display_name)}",
                style=COLOR_MAIN,
            )
        )
        console.print()
        return True

    console.print(
        Text(f"  {t('picker.agent.cancelled')}", style=COLOR_WARN)
    )
    console.print()
    return False


__all__ = ["pick_agent"]
