# =============================================================================
#  Codermuks in Termux — live-панель рассуждений v1.2.0
# =============================================================================
#  Что делает:
#    • подписывается на EventBus и собирает историю событий;
#    • рисует красивую панель с деревом шагов агента;
#    • работает в фоновом потоке, обновляет экран 4 раза в секунду.
# =============================================================================

from __future__ import annotations

import threading
import time
from typing import Any

from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from core.events import Event, get_bus


# Цвета
COLOR_MAIN = "bright_green"
COLOR_ACCENT = "bright_cyan"
COLOR_WARN = "yellow"
COLOR_ERROR = "bright_red"
COLOR_DIM = "grey62"
COLOR_STEP = "bright_white"


class LivePanel:
    """Живая панель с цепочкой рассуждений агента."""

    def __init__(self, console: Console) -> None:
        self.console = console
        self._started_at = time.time()
        self._steps: list[tuple[str, str, str]] = []  # (icon, name, detail)
        self._current = ""
        self._live: Live | None = None
        self._thread = None
        self._stop = None
        self._unsubscribe = None

    # -------------------------------------------------------------------------
    #  Обработка событий
    # -------------------------------------------------------------------------

    def _on_event(self, event: Event) -> None:
        """Реакция на событие из EventBus."""
        name = event.name

        # Начало этапа.
        if name.endswith(".start") or name in (
            "planning.start", "codegen.start", "compile.start",
            "run.start", "fix.start", "research.start", "task.done",
        ):
            stage = name.split(".")[0]
            label = {
                "planning": "планирую",
                "codegen": "пишу код",
                "compile": "компилирую",
                "run": "запускаю",
                "fix": "исправляю",
                "research": "исследую",
                "task": "финал",
                "project": "проект",
            }.get(stage, stage)
            self._current = label
            self._steps.append(("⋯", label, ""))

        # Прогресс.
        elif name.endswith(".step") or name.endswith(".file") or \
             name.endswith(".source"):
            detail = event.get("message") or event.get("file") or ""
            if self._steps:
                icon, label, _ = self._steps[-1]
                self._steps[-1] = (icon, label, str(detail))

        # Успех.
        elif name.endswith(".done") or name.endswith(".success"):
            if self._steps:
                icon, label, detail = self._steps[-1]
                self._steps[-1] = ("✔", label, detail)

        # Ошибка.
        elif name.endswith(".error"):
            if self._steps:
                icon, label, detail = self._steps[-1]
                err = event.get("error", "ошибка")
                self._steps[-1] = ("✘", label, f"{detail} — {err}")

        # Создан/открыт проект.
        elif name in ("project.created", "project.opened"):
            pname = event.get("name", "")
            self._steps.insert(0, ("•", "проект", pname))

    # -------------------------------------------------------------------------
    #  Отрисовка
    # -------------------------------------------------------------------------

    def _render(self) -> Panel:
        elapsed = time.time() - self._started_at
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)

        content = Text()
        content.append("⏱  ", style=COLOR_ACCENT)
        content.append(f"{minutes:02d}:{seconds:02d}", style=f"bold {COLOR_MAIN}")
        content.append("   ·   ", style=COLOR_DIM)
        content.append(self._current or "думаю", style=COLOR_WARN)
        content.append("\n\n")

        # Дерево шагов.
        for icon, label, detail in self._steps[-8:]:
            color = COLOR_STEP
            if icon == "✔":
                color = COLOR_MAIN
            elif icon == "✘":
                color = COLOR_ERROR

            content.append(f"  {icon}  ", style=color)
            content.append(f"{label}", style=f"bold {color}")
            if detail:
                content.append(f"  ·  {detail}", style=COLOR_DIM)
            content.append("\n")

        return Panel(
            content,
            border_style=COLOR_ACCENT,
            padding=(0, 2),
            title="[bold]Codermuks[/bold]",
            subtitle="[dim]рассуждение[/dim]",
        )

    # -------------------------------------------------------------------------
    #  Управление
    # -------------------------------------------------------------------------

    def _auto_refresh(self) -> None:
        while not self._stop.is_set():
            try:
                if self._live is not None:
                    self._live.update(self._render())
            except Exception:
                pass
            time.sleep(0.25)

    def start(self) -> None:
        self._started_at = time.time()
        self._steps = []
        self._current = "инициализация"
        self._live = Live(
            self._render(),
            console=self.console,
            refresh_per_second=4,
            transient=True,
        )
        self._live.start()

        # Подписываемся на EventBus.
        self._unsubscribe = get_bus().subscribe(self._on_event)

        # Запускаем поток обновления.
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._auto_refresh, daemon=True)
        self._thread.start()

    def stop(self) -> float:
        elapsed = time.time() - self._started_at
        if self._stop is not None:
            self._stop.set()
        if self._thread is not None:
            try:
                self._thread.join(timeout=1.0)
            except Exception:
                pass
            self._thread = None
        if self._unsubscribe is not None:
            try:
                self._unsubscribe()
            except Exception:
                pass
            self._unsubscribe = None
        if self._live is not None:
            try:
                self._live.stop()
            except Exception:
                pass
            self._live = None
        return elapsed


__all__ = ["LivePanel"]
