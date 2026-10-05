# =============================================================================
#  Codermuks in Termux — интерфейс командной строки
# =============================================================================
#  Это «лицо» программы — всё, что видит пользователь:
#    • стартовый баннер с большим зелёным названием;
#    • двуязычную памятку (RU/EN);
#    • приглашение ввода с поддержкой команд;
#    • живой таймер рассуждения во время работы агента;
#    • красивый вывод финального кода с подсветкой синтаксиса;
#    • сообщения об ошибках и подсказки.
#
#  Вся тяжёлая логика (обращения к Mistral, компиляция, фиксы) живёт
#  в core/agent.py. Этот файл только вызывает агента и показывает
#  прогресс.
# =============================================================================

from __future__ import annotations

import os
import sys
import time
from typing import Any

from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from core import config
from skills import modes as skills_mod
from utils import helpers


# =============================================================================
#  ГЛОБАЛЬНЫЙ КОНСОЛЬНЫЙ ОБЪЕКТ
# =============================================================================

# Один Console на всё приложение — так rich корректно управляет
# позиционированием, цветами и живыми блоками.
console = Console()


# =============================================================================
#  ЦВЕТОВАЯ СХЕМА
# =============================================================================

COLOR_MAIN = "bright_green"
COLOR_ACCENT = "bright_cyan"
COLOR_WARN = "yellow"
COLOR_ERROR = "bright_red"
COLOR_DIM = "grey62"
COLOR_HIGHLIGHT = "bright_magenta"


# =============================================================================
#  СТАРТОВЫЙ БАННЕР
# =============================================================================

# Большое название проекта. Рисуется вручную символами Unicode,
# чтобы не тянуть внешние зависимости вроде pyfiglet на каждый запуск.
BANNER_LINES = [
    "  ██████╗ ██████╗ ██████╗ ███████╗██████╗ ███╗   ███╗██╗   ██╗██╗  ██╗███████╗",
    " ██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔══██╗████╗ ████║██║   ██║██║ ██╔╝██╔════╝",
    " ██║     ██║   ██║██║  ██║█████╗  ██████╔╝██╔████╔██║██║   ██║█████╔╝ ███████╗",
    " ██║     ██║   ██║██║  ██║██╔══╝  ██╔══██╗██║╚██╔╝██║██║   ██║██╔═██╗ ╚════██║",
    " ╚██████╗╚██████╔╝██████╔╝███████╗██║  ██║██║ ╚═╝ ██║╚██████╔╝██║  ██╗███████║",
    "  ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝",
]

BANNER_SUBTITLE = "▸  I N   T E R M U X  ◂"


def _build_banner() -> Text:
    """
    Собирает объект Text с большим зелёным названием CODERMUKS.

    Если терминал слишком узкий (< 80 колонок) — используется
    компактный вариант, чтобы буквы не «разъезжались».
    """
    width = console.width

    banner = Text()

    # Компактный режим для мобильных экранов.
    if width < 80:
        banner.append("\n")
        banner.append("  CODERMUKS in TERMUX\n", style=f"bold {COLOR_MAIN}")
        banner.append("  v1.0.0\n", style=COLOR_DIM)
        banner.append("\n")
        return banner

    # Полноразмерный режим — ASCII-art.
    for line in BANNER_LINES:
        banner.append(line + "\n", style=f"bold {COLOR_MAIN}")

    banner.append("\n")
    banner.append(BANNER_SUBTITLE.center(width) + "\n", style=COLOR_ACCENT)
    banner.append("v1.0.0".center(width) + "\n", style=COLOR_DIM)

    return banner


def print_banner() -> None:
    """Печатает стартовый баннер и краткое приветствие."""
    console.print(_build_banner())
    console.print()

    subtitle = Text()
    subtitle.append("AI coding agent", style=f"bold {COLOR_ACCENT}")
    subtitle.append(" · powered by ", style=COLOR_DIM)
    subtitle.append("Mistral", style=f"bold {COLOR_HIGHLIGHT}")
    console.print(Align.center(subtitle))
    console.print()


# =============================================================================
#  ДВУЯЗЫЧНАЯ ПАМЯТКА
# =============================================================================

def print_memo() -> None:
    """
    Печатает двуязычную памятку с основными командами.

    Использует rich.Table с двумя колонками — русский и английский.
    """
    console.print(Rule(style=COLOR_DIM))
    console.print()

    header = Text()
    header.append("📖  ", style="bold")
    header.append("ПАМЯТКА / HELP MEMO", style=f"bold {COLOR_ACCENT}")
    console.print(Align.center(header))
    console.print()

    table = Table(
        show_header=True,
        header_style=f"bold {COLOR_MAIN}",
        border_style=COLOR_DIM,
        box=None,
        padding=(0, 2),
        expand=False,
    )
    table.add_column("🇷🇺 Русский", style="white", no_wrap=False)
    table.add_column("🇬🇧 English", style="white", no_wrap=False)

    rows = [
        (
            "[bold cyan]codermuks[/bold cyan] — запуск в интерактивном режиме",
            "[bold cyan]codermuks[/bold cyan] — start interactive mode",
        ),
        (
            '[bold cyan]codermuks "задача"[/bold cyan] — сразу выполнить запрос',
            '[bold cyan]codermuks "task"[/bold cyan] — run a request immediately',
        ),
        (
            "[bold green]/research[/bold green] — глубокое исследование (web, GitHub)",
            "[bold green]/research[/bold green] — deep research (web, GitHub)",
        ),
        (
            "[bold green]/reason[/bold green] — показать цепочку рассуждений",
            "[bold green]/reason[/bold green] — show reasoning chain",
        ),
        (
            "[bold green]/analyze[/bold green] — анализ существующего кода",
            "[bold green]/analyze[/bold green] — analyze existing code",
        ),
        (
            "[bold green]/langs[/bold green] — список поддерживаемых языков",
            "[bold green]/langs[/bold green] — list supported languages",
        ),
        (
            "[bold green]/clear[/bold green] — очистить экран",
            "[bold green]/clear[/bold green] — clear the screen",
        ),
        (
            "[bold green]/help[/bold green] — показать эту памятку",
            "[bold green]/help[/bold green] — show this memo",
        ),
        (
            "[bold red]/exit[/bold red] — выйти из программы",
            "[bold red]/exit[/bold red] — exit the program",
        ),
    ]

    for ru, en in rows:
        table.add_row(ru, en)

    console.print(Align.center(table))
    console.print()

    footer = Text()
    footer.append("Модель: ", style=COLOR_DIM)
    footer.append(config.CODING_MODEL, style=COLOR_HIGHLIGHT)
    footer.append("  ·  ", style=COLOR_DIM)
    footer.append("Планировщик: ", style=COLOR_DIM)
    footer.append(config.PLANNER_MODEL, style=COLOR_HIGHLIGHT)
    console.print(Align.center(footer))

    console.print()
    console.print(Rule(style=COLOR_DIM))
    console.print()


# =============================================================================
#  ТАЙМЕР РАССУЖДЕНИЯ
# =============================================================================

class ReasoningDisplay:
    """
    Живой блок с таймером рассуждения.

    Показывает:
        ⏱ 00:42  ·  текущий шаг агента

    Обновляется на каждом шаге через колбэк on_step из Agent.
    """

    def __init__(self) -> None:
        self._started_at: float = 0.0
        self._current_step: str = "инициализация"
        self._live: Live | None = None

    def _render(self) -> Panel:
        """
        Собирает текст текущего состояния в красивую панель.
        """
        elapsed = time.time() - self._started_at
        timer_text = helpers.format_duration(elapsed)

        content = Text()
        content.append("⏱  ", style=COLOR_ACCENT)
        content.append(timer_text, style=f"bold {COLOR_MAIN}")
        content.append("   ·   ", style=COLOR_DIM)
        content.append(self._current_step, style=COLOR_WARN)

        return Panel(
            Align.center(content),
            border_style=COLOR_ACCENT,
            padding=(0, 2),
        )

    def start(self) -> None:
        """Запускает живой блок."""
        self._started_at = time.time()
        self._current_step = "инициализация"
        self._live = Live(
            self._render(),
            console=console,
            refresh_per_second=4,
            transient=True,
        )
        self._live.start()

    def update(self, step_name: str, detail: str = "") -> None:
        """Обновляет текущий шаг."""
        self._current_step = f"{step_name}" + (f" — {detail}" if detail else "")
        if self._live is not None:
            self._live.update(self._render())

    def stop(self) -> float:
        """
        Останавливает живой блок и возвращает итоговое время
        рассуждения в секундах.
        """
        elapsed = time.time() - self._started_at
        if self._live is not None:
            self._live.stop()
            self._live = None
        return elapsed


# =============================================================================
#  ВЫВОД РЕЗУЛЬТАТА
# =============================================================================

def print_result(result: Any) -> None:
    """
    Печатает финальный результат работы агента.

    Аргументы:
        result — объект AgentResult из core/agent.py

    Что показываем:
        • статус (успех / ошибка);
        • метаинформацию (язык, итерации, время рассуждения);
        • финальный код с подсветкой синтаксиса;
        • вывод программы (stdout);
        • ошибки, если остались (stderr).
    """
    console.print()

    # --- Заголовок со статусом --------------------------------------------
    if result.success:
        status_text = Text()
        status_text.append("✔ ", style=f"bold {COLOR_MAIN}")
        status_text.append("Задача выполнена", style=f"bold {COLOR_MAIN}")
        border = COLOR_MAIN
    else:
        status_text = Text()
        status_text.append("✘ ", style=f"bold {COLOR_ERROR}")
        status_text.append("Задача не выполнена", style=f"bold {COLOR_ERROR}")
        border = COLOR_ERROR

    console.print(Rule(style=border))
    console.print(Align.center(status_text))
    console.print()

    # --- Таблица метаинформации -------------------------------------------
    meta = Table(show_header=False, box=None, padding=(0, 2))
    meta.add_column(style=COLOR_DIM)
    meta.add_column(style="white")

    meta.add_row("Язык:", result.language or "—")
    meta.add_row("Итераций фикса:", str(result.iterations))
    meta.add_row("Время рассуждения:", helpers.format_duration(result.reasoning_time))

    if result.exit_code >= 0:
        meta.add_row("Код возврата:", str(result.exit_code))

    console.print(Align.center(meta))
    console.print()

    # --- Финальный код с подсветкой ---------------------------------------
    if result.code:
        lang_for_syntax = _map_language_to_pygments(result.language)

        console.print(Rule("[bold]Код[/bold]", style=COLOR_DIM))
        console.print()

        syntax = Syntax(
            result.code,
            lang_for_syntax,
            theme="monokai",
            line_numbers=False,
            word_wrap=True,
        )
        console.print(
            Panel(
                syntax,
                border_style=COLOR_DIM,
                padding=(1, 2),
            )
        )
        console.print()

    # --- Вывод программы --------------------------------------------------
    if result.stdout and result.stdout.strip():
        console.print(Rule("[bold]Вывод программы[/bold]", style=COLOR_DIM))
        console.print()
        console.print(
            Panel(
                Text(result.stdout.strip(), style="white"),
                border_style=COLOR_MAIN,
                padding=(1, 2),
            )
        )
        console.print()

    # --- Ошибки (если остались) -------------------------------------------
    if result.stderr and result.stderr.strip():
        console.print(Rule("[bold]Ошибки[/bold]", style=COLOR_ERROR))
        console.print()
        console.print(
            Panel(
                Text(result.stderr.strip(), style="white"),
                border_style=COLOR_ERROR,
                padding=(1, 2),
            )
        )
        console.print()

    # --- Заметки агента ---------------------------------------------------
    if result.notes:
        console.print(Rule("[bold]Заметки[/bold]", style=COLOR_DIM))
        console.print()
        for note in result.notes:
            bullet = Text()
            bullet.append("  • ", style=COLOR_ACCENT)
            bullet.append(note, style=COLOR_DIM)
            console.print(bullet)
        console.print()

    # --- Сохранение артефакта --------------------------------------------
    if result.code:
        try:
            path = helpers.save_artifact(
                result.code,
                language=result.language,
                success=result.success,
            )
            console.print(
                Text(f"  💾 Код сохранён: {path}", style=COLOR_DIM)
            )
            console.print()
        except Exception:
            pass

    console.print(Rule(style=border))
    console.print()


def _map_language_to_pygments(language: str) -> str:
    """
    Приводит внутреннее имя языка к тому, что понимает Pygments
    (библиотека подсветки, которую использует rich.Syntax).
    """
    mapping = {
        "c": "c",
        "cpp": "cpp",
        "rust": "rust",
        "python": "python",
        "go": "go",
        "java": "java",
        "javascript": "javascript",
        "kotlin": "kotlin",
        "swift": "swift",
        "ruby": "ruby",
        "php": "php",
        "dart": "dart",
        "elixir": "elixir",
        "haskell": "haskell",
        "lua": "lua",
        "r": "r",
        "sql": "sql",
        "csharp": "csharp",
    }
    return mapping.get(language, "text")


# =============================================================================
#  КОМАНДЫ
# =============================================================================

def handle_command(line: str, active_skills: list[str]) -> tuple[bool, list[str]]:
    """
    Обрабатывает команду (строку, начинающуюся с '/').

    Возвращает кортеж:
        (продолжать_ли_цикл, обновлённый_список_скиллов)

    Если команда не команда, а обычный текст — возвращает (True, skills)
    и оставляет решение за вызывающим кодом.
    """
    parts = line.strip().split(maxsplit=1)
    command = parts[0].lower().lstrip("/")

    # --- /exit -----------------------------------------------------------
    if command in ("exit", "quit", "q"):
        console.print()
        console.print(Text("  До встречи! · See you!", style=COLOR_ACCENT))
        console.print()
        return False, active_skills

    # --- /help -----------------------------------------------------------
    if command in ("help", "h", "?"):
        print_memo()
        return True, active_skills

    # --- /clear ----------------------------------------------------------
    if command in ("clear", "cls"):
        os.system("clear")
        print_banner()
        return True, active_skills

    # --- /langs ----------------------------------------------------------
    if command in ("langs", "languages", "lang"):
        print_languages()
        return True, active_skills

    # --- /skills ---------------------------------------------------------
    if command in ("skills", "modes"):
        console.print()
        console.print(skills_mod.format_skills_help())
        console.print()
        return True, active_skills

    # --- Скиллы: /research, /reason, /analyze ----------------------------
    skill = skills_mod.get_skill(command)
    if skill is not None:
        if skill.name in active_skills:
            active_skills.remove(skill.name)
            console.print(
                Text(f"  ○ Скилл выключен: {skill.display_name}", style=COLOR_DIM)
            )
        else:
            active_skills.append(skill.name)
            console.print(
                Text(f"  ● Скилл включён: {skill.display_name}", style=COLOR_MAIN)
            )
        return True, active_skills

    # --- Неизвестная команда ---------------------------------------------
    console.print(
        Text(f"  ⚠ Неизвестная команда: /{command}", style=COLOR_WARN)
    )
    console.print(
        Text("  Введи /help, чтобы увидеть список команд.", style=COLOR_DIM)
    )
    return True, active_skills


def print_languages() -> None:
    """
    Печатает список поддерживаемых языков: основные и расширенные.
    """
    # Импортируем здесь, чтобы не тянуть executors на каждом старте CLI.
    from executors import runners
    from executors import extended_runners

    console.print()

    # --- Основные языки ---------------------------------------------------
    console.print(Rule("[bold]Основные языки[/bold]", style=COLOR_DIM))
    console.print()

    basic_table = Table(
        show_header=True,
        header_style=f"bold {COLOR_MAIN}",
        border_style=COLOR_DIM,
        box=None,
    )
    basic_table.add_column("Язык")
    basic_table.add_column("Инструмент")
    basic_table.add_column("Статус")

    for lang in runners.supported_languages():
        info = runners.language_info(lang)
        status = "[green]✔ доступен[/green]" if info["available"] else "[red]✘ нет[/red]"
        basic_table.add_row(
            info["display_name"],
            info["check_binary"],
            status,
        )

    console.print(basic_table)
    console.print()

    # --- Расширенные языки -----------------------------------------------
    console.print(Rule("[bold]Расширенные языки[/bold]", style=COLOR_DIM))
    console.print()

    extended_table = Table(
        show_header=True,
        header_style=f"bold {COLOR_ACCENT}",
        border_style=COLOR_DIM,
        box=None,
    )
    extended_table.add_column("Язык")
    extended_table.add_column("Инструмент")
    extended_table.add_column("Статус")
    extended_table.add_column("Установка", style=COLOR_DIM)

    status = extended_runners.extended_language_status()
    for _lang, info in sorted(status.items(), key=lambda kv: kv[1]["display_name"]):
        mark = "[green]✔[/green]" if info["available"] else "[red]✘[/red]"
        extended_table.add_row(
            info["display_name"],
            info["check_binary"],
            mark,
            info["package"],
        )

    console.print(extended_table)
    console.print()


# =============================================================================
#  ОБРАБОТКА ЗАПРОСА
# =============================================================================

def run_query(query: str, active_skills: list[str]) -> None:
    """
    Отправляет запрос в агент и показывает результат.

    Аргументы:
        query         — текст запроса пользователя
        active_skills — список активных скиллов
    """
    from core.agent import Agent

    # --- Живой таймер рассуждения ----------------------------------------
    display = ReasoningDisplay()
    display.start()

    # Колбэк, который агент вызывает на каждом шаге.
    def on_step(step: Any) -> None:
        display.update(step.name, step.detail)

    agent = Agent(on_step=on_step)

    try:
        result = agent.solve(query, skills=active_skills)
    except KeyboardInterrupt:
        display.stop()
        console.print()
        console.print(Text("  ⚠ Прервано пользователем.", style=COLOR_WARN))
        console.print()
        return
    except Exception as exc:
        display.stop()
        console.print()
        console.print(Text(f"  ✘ Ошибка: {exc}", style=COLOR_ERROR))
        console.print()
        return

    reasoning_time = display.stop()

    # Синхронизируем время: агент считает своё, но показываем мы.
    # Это позволяет таймеру учитывать и время вывода тоже.
    result.reasoning_time = reasoning_time

    print_result(result)


# =============================================================================
#  ГЛАВНЫЙ ЦИКЛ
# =============================================================================

def run() -> int:
    """
    Точка входа CLI. Запускает интерактивный цикл.

    Возвращает код выхода:
        0 — успешное завершение
        1 — критическая ошибка (например, нет ключа Mistral)
    """
    # --- Создаём пользовательские директории ------------------------------
    config.ensure_dirs()

    # --- Проверяем наличие ключа Mistral ---------------------------------
    try:
        config.get_api_key()
    except (FileNotFoundError, ValueError) as exc:
        print_banner()
        console.print()
        console.print(
            Panel(
                Text(str(exc), style="white"),
                title="[bold red]Требуется API-ключ Mistral[/bold red]",
                border_style=COLOR_ERROR,
                padding=(1, 2),
            )
        )
        console.print()
        return 1

    # --- Приветствие ------------------------------------------------------
    os.system("clear")
    print_banner()
    print_memo()

    # --- Активные скиллы (пусто при старте) ------------------------------
    active_skills: list[str] = []

    # --- Обработка аргументов командной строки ---------------------------
    #  Если пользователь запустил `codermuks "задача"` — сразу выполняем
    #  её и выходим, не заходя в интерактивный режим.
    argv = sys.argv[1:]
    if argv:
        query_parts: list[str] = []
        for arg in argv:
            if arg.startswith("/"):
                skill = skills_mod.get_skill(arg)
                if skill is not None:
                    active_skills.append(skill.name)
                    continue
            query_parts.append(arg)

        query = " ".join(query_parts).strip()
        if query:
            run_query(query, active_skills)
            return 0

    # --- Интерактивный цикл ----------------------------------------------
    while True:
        try:
            # Формируем строку приглашения с учётом активных скиллов.
            prompt_text = "[bold yellow]codermuks[/bold yellow]"
            if active_skills:
                badges = " ".join(f"[{s}]" for s in active_skills)
                prompt_text += f" [dim]{badges}[/dim]"
            prompt_text += " [bold yellow]▸[/bold yellow]"

            line = Prompt.ask(prompt_text)

        except (KeyboardInterrupt, EOFError):
            console.print()
            console.print(Text("  До встречи! · See you!", style=COLOR_ACCENT))
            console.print()
            return 0

        line = line.strip()
        if not line:
            continue

        # --- Команда или обычный запрос? ---------------------------------
        if line.startswith("/"):
            keep_going, active_skills = handle_command(line, active_skills)
            if not keep_going:
                return 0
            continue

        # --- Обычный запрос → агент --------------------------------------
        run_query(line, active_skills)


# =============================================================================
#  ЭКСПОРТ
# =============================================================================

__all__ = ["run", "console"]