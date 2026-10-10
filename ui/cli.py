# =============================================================================
#  Codermuks in Termux — интерфейс командной строки v1.1.0
# =============================================================================
#  Что нового в v1.1.0:
#    • Все строки переведены через core.i18n.t().
#    • Добавлена команда /changeagent — смена главного агента.
#    • Добавлена команда /language — смена языка интерфейса.
#    • Показ провайдера и модели в финальном результате.
#    • Обновлённая памятка (двуязычная через i18n).
#    • Красивое меню выбора агента через rich.Table.
#
#  Как и раньше — вся тяжёлая логика в core/agent.py → TeamLead.
#  Этот файл только вызывает агента и показывает прогресс.
# =============================================================================

from __future__ import annotations

import os
import sys
import time
from typing import Any

from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from core import config
from core.i18n import t, translator
from core.team.agent_registry import get_registry
from skills import modes as skills_mod
from ui.agent_picker import pick_agent
from utils import helpers


# =============================================================================
#  ГЛОБАЛЬНЫЙ КОНСОЛЬНЫЙ ОБЪЕКТ
# =============================================================================

console = Console()


# =============================================================================
#  ЦВЕТА
# =============================================================================

COLOR_MAIN = "bright_green"
COLOR_ACCENT = "bright_cyan"
COLOR_WARN = "yellow"
COLOR_ERROR = "bright_red"
COLOR_DIM = "grey62"
COLOR_HIGHLIGHT = "bright_magenta"


# =============================================================================
#  БАННЕР
# =============================================================================

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

    На узких экранах (< 80 колонок) — компактный вариант.
    """
    width = console.width

    banner = Text()

    if width < 80:
        banner.append("\n")
        banner.append(f"  {t('welcome.banner')}\n", style=f"bold {COLOR_MAIN}")
        banner.append(f"  {t('welcome.version')}\n", style=COLOR_DIM)
        banner.append("\n")
        return banner

    for line in BANNER_LINES:
        banner.append(line + "\n", style=f"bold {COLOR_MAIN}")

    banner.append("\n")
    banner.append(BANNER_SUBTITLE.center(width) + "\n", style=COLOR_ACCENT)
    banner.append(t("welcome.version").center(width) + "\n", style=COLOR_DIM)

    return banner


def print_banner() -> None:
    """Печатает стартовый баннер и краткое приветствие."""
    console.print(_build_banner())
    console.print()

    subtitle = Text()
    subtitle.append(t("welcome.subtitle"), style=f"bold {COLOR_ACCENT}")
    console.print(Align.center(subtitle))
    console.print()


# =============================================================================
#  ПАМЯТКА
# =============================================================================

def print_memo() -> None:
    """
    Печатает памятку с основными командами.

    Строки берутся из i18n — на выбранном пользователем языке.
    """
    console.print(Rule(style=COLOR_DIM))
    console.print()

    header = Text()
    header.append("📖  ", style="bold")
    header.append(t("memo.title"), style=f"bold {COLOR_ACCENT}")
    console.print(Align.center(header))
    console.print()

    # Таблица команд: [название] [описание].
    table = Table(
        show_header=False,
        box=None,
        padding=(0, 2),
        expand=False,
    )
    table.add_column(style=f"bold {COLOR_MAIN}", no_wrap=True)
    table.add_column(style="white", no_wrap=False)

    commands = [
        ("cmd.name.changeagent", "cmd.changeagent"),
        ("cmd.name.language",    "cmd.language"),
        ("cmd.name.research",    "cmd.research"),
        ("cmd.name.reason",      "cmd.reason"),
        ("cmd.name.analyze",     "cmd.analyze"),
        ("cmd.name.langs",       "cmd.langs"),
        ("cmd.name.skills",      "cmd.skills"),
        ("cmd.name.clear",       "cmd.clear"),
        ("cmd.name.help",        "cmd.help"),
        ("cmd.name.exit",        "cmd.exit"),
    ]

    for name_key, desc_key in commands:
        table.add_row(t(name_key), t(desc_key))

    console.print(Align.center(table))
    console.print()

    # Информация о текущем лидере и модели.
    try:
        registry = get_registry()
        lead_name = registry.get_lead()
        lead_info = registry.get_info(lead_name)

        footer = Text()
        footer.append(f"{t('memo.footer.lead')}: ", style=COLOR_DIM)
        footer.append(
            lead_info.display_name if lead_info else lead_name,
            style=COLOR_HIGHLIGHT,
        )
        footer.append("  ·  ", style=COLOR_DIM)
        footer.append(f"{t('memo.footer.model')}: ", style=COLOR_DIM)
        footer.append(
            config.get_provider_model(lead_name) or "—",
            style=COLOR_HIGHLIGHT,
        )
        console.print(Align.center(footer))
    except Exception:
        # Если реестр недоступен — просто пропускаем блок.
        pass

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

    Все строки берутся из i18n.
    """

    def __init__(self) -> None:
        self._started_at: float = 0.0
        self._current_step: str = ""
        self._live: Live | None = None

    def _render(self) -> Panel:
        """Собирает текст текущего состояния в панель."""
        elapsed = time.time() - self._started_at
        timer_text = helpers.format_duration(elapsed)

        content = Text()
        content.append("⏱  ", style=COLOR_ACCENT)
        content.append(timer_text, style=f"bold {COLOR_MAIN}")
        content.append("   ·   ", style=COLOR_DIM)
        content.append(
            self._current_step or t("status.thinking"),
            style=COLOR_WARN,
        )

        return Panel(
            Align.center(content),
            border_style=COLOR_ACCENT,
            padding=(0, 2),
        )

    def start(self) -> None:
        """Запускает живой блок."""
        self._started_at = time.time()
        self._current_step = t("status.thinking")
        self._live = Live(
            self._render(),
            console=console,
            refresh_per_second=4,
            transient=True,
        )
        self._live.start()

    def update(self, step_name: str, detail: str = "") -> None:
        """Обновляет текущий шаг."""
        # Пробуем перевести имя шага (например, "планирование").
        translated = t(f"status.{step_name}") if step_name else ""
        # Если ключа нет — используем как есть.
        if translated == f"status.{step_name}":
            translated = step_name

        self._current_step = translated
        if detail:
            self._current_step += f" — {detail}"

        if self._live is not None:
            self._live.update(self._render())

    def stop(self) -> float:
        """
        Останавливает живой блок и возвращает итоговое время.
        """
        elapsed = time.time() - self._started_at
        if self._live is not None:
            self._live.stop()
            self._live = None
        return elapsed


# =============================================================================
#  ВЫВОД РЕЗУЛЬТАТА
# =============================================================================

def _map_language_to_pygments(language: str) -> str:
    """Приводит внутреннее имя языка к тому, что понимает Pygments."""
    mapping = {
        "c": "c", "cpp": "cpp", "rust": "rust", "python": "python",
        "go": "go", "java": "java", "javascript": "javascript",
        "kotlin": "kotlin", "swift": "swift", "ruby": "ruby",
        "php": "php", "dart": "dart", "elixir": "elixir",
        "haskell": "haskell", "lua": "lua", "r": "r", "sql": "sql",
        "csharp": "csharp",
    }
    return mapping.get(language, "text")


def print_result(result: Any) -> None:
    """
    Печатает финальный результат работы агента.

    Все строки — через i18n.
    """
    console.print()

    # --- Заголовок со статусом --------------------------------------------
    if result.success:
        status_text = Text()
        status_text.append("✔ ", style=f"bold {COLOR_MAIN}")
        status_text.append(t("result.success"), style=f"bold {COLOR_MAIN}")
        border = COLOR_MAIN
    else:
        status_text = Text()
        status_text.append("✘ ", style=f"bold {COLOR_ERROR}")
        status_text.append(t("result.failure"), style=f"bold {COLOR_ERROR}")
        border = COLOR_ERROR

    console.print(Rule(style=border))
    console.print(Align.center(status_text))
    console.print()

    # --- Таблица метаинформации -------------------------------------------
    meta = Table(show_header=False, box=None, padding=(0, 2))
    meta.add_column(style=COLOR_DIM)
    meta.add_column(style="white")

    meta.add_row(f"{t('result.language')}:", result.language or "—")
    meta.add_row(
        f"{t('result.iterations')}:",
        str(result.iterations),
    )
    meta.add_row(
        f"{t('result.reasoning_time')}:",
        helpers.format_duration(result.reasoning_time),
    )

    if result.exit_code >= 0:
        meta.add_row(f"{t('result.exit_code')}:", str(result.exit_code))

    # Провайдер и модель (из AgentResult v1.1.0).
    used_provider = getattr(result, "used_provider", "")
    used_model = getattr(result, "used_model", "")
    if used_provider:
        label = f"{used_provider}"
        if used_model:
            label += f" ({used_model})"
        meta.add_row(f"{t('result.provider')}:", label)

    console.print(Align.center(meta))
    console.print()

    # --- Финальный код ----------------------------------------------------
    if result.code:
        console.print(Rule(f"[bold]{t('result.code')}[/bold]", style=COLOR_DIM))
        console.print()

        syntax = Syntax(
            result.code,
            _map_language_to_pygments(result.language),
            theme="monokai",
            line_numbers=False,
            word_wrap=True,
        )
        console.print(
            Panel(syntax, border_style=COLOR_DIM, padding=(1, 2))
        )
        console.print()

    # --- Вывод программы --------------------------------------------------
    if result.stdout and result.stdout.strip():
        console.print(Rule(f"[bold]{t('result.stdout')}[/bold]", style=COLOR_DIM))
        console.print()
        console.print(
            Panel(
                Text(result.stdout.strip(), style="white"),
                border_style=COLOR_MAIN,
                padding=(1, 2),
            )
        )
        console.print()

    # --- Ошибки -----------------------------------------------------------
    if result.stderr and result.stderr.strip():
        console.print(Rule(f"[bold]{t('result.stderr')}[/bold]", style=COLOR_ERROR))
        console.print()
        console.print(
            Panel(
                Text(result.stderr.strip(), style="white"),
                border_style=COLOR_ERROR,
                padding=(1, 2),
            )
        )
        console.print()

    # --- Заметки ----------------------------------------------------------
    if result.notes:
        console.print(Rule(f"[bold]{t('result.notes')}[/bold]", style=COLOR_DIM))
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
                Text(f"  💾 {t('result.artifact', path=str(path))}", style=COLOR_DIM)
            )
            console.print()
        except Exception:
            pass

    console.print(Rule(style=border))
    console.print()


# =============================================================================
#  СПИСОК ЯЗЫКОВ ПРОГРАММИРОВАНИЯ
# =============================================================================

def print_languages() -> None:
    """Печатает список поддерживаемых языков программирования."""
    # Ленивый импорт — не тянем executors без необходимости.
    from executors import runners
    from executors import extended_runners

    console.print()

    # --- Основные языки ---------------------------------------------------
    console.print(Rule(f"[bold]{t('lang.title.basic')}[/bold]", style=COLOR_DIM))
    console.print()

    basic_table = Table(
        show_header=True,
        header_style=f"bold {COLOR_MAIN}",
        border_style=COLOR_DIM,
        box=None,
    )
    basic_table.add_column(t("lang.column.name"))
    basic_table.add_column(t("lang.column.tool"))
    basic_table.add_column(t("lang.column.status"))

    for lang in runners.supported_languages():
        info = runners.language_info(lang)
        status = (
            f"[green]✔ {t('lang.available')}[/green]"
            if info["available"]
            else f"[red]✘ {t('lang.not_available')}[/red]"
        )
        basic_table.add_row(info["display_name"], info["check_binary"], status)

    console.print(basic_table)
    console.print()

    # --- Расширенные языки -----------------------------------------------
    console.print(Rule(f"[bold]{t('lang.title.extended')}[/bold]", style=COLOR_DIM))
    console.print()

    ext_table = Table(
        show_header=True,
        header_style=f"bold {COLOR_ACCENT}",
        border_style=COLOR_DIM,
        box=None,
    )
    ext_table.add_column(t("lang.column.name"))
    ext_table.add_column(t("lang.column.tool"))
    ext_table.add_column(t("lang.column.status"))
    ext_table.add_column(t("lang.column.install"), style=COLOR_DIM)

    status = extended_runners.extended_language_status()
    for _lang, info in sorted(status.items(), key=lambda kv: kv[1]["display_name"]):
        mark = "[green]✔[/green]" if info["available"] else "[red]✘[/red]"
        ext_table.add_row(
            info["display_name"],
            info["check_binary"],
            mark,
            info["package"],
        )

    console.print(ext_table)
    console.print()


# =============================================================================
#  ОБРАБОТКА КОМАНД
# =============================================================================

def handle_command(
    line: str,
    active_skills: list[str],
) -> tuple[bool, list[str]]:
    """
    Обрабатывает команду (строку, начинающуюся с '/').

    Возвращает кортеж (продолжать_ли_цикл, обновлённый_список_скиллов).
    """
    parts = line.strip().split(maxsplit=1)
    command = parts[0].lower().lstrip("/")

    # --- /exit -----------------------------------------------------------
    if command in ("exit", "quit", "q", "выход"):
        console.print()
        console.print(Text(f"  {t('common.exit')}!", style=COLOR_ACCENT))
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
    if command in ("langs", "languages"):
        print_languages()
        return True, active_skills

    # --- /skills ---------------------------------------------------------
    if command in ("skills", "modes"):
        console.print()
        console.print(skills_mod.format_skills_help())
        console.print()
        return True, active_skills

    # --- /changeagent ----------------------------------------------------
    if command in ("changeagent", "agent", "switch"):
        pick_agent()
        return True, active_skills

    # --- /language -------------------------------------------------------
    if command in ("language", "lang-set"):
        _handle_language_command()
        return True, active_skills

    # --- Скиллы: /research, /reason, /analyze ----------------------------
    skill = skills_mod.get_skill(command)
    if skill is not None:
        if skill.name in active_skills:
            active_skills.remove(skill.name)
            console.print(
                Text(
                    f"  ○ {t('skill.disabled', name=skill.display_name)}",
                    style=COLOR_DIM,
                )
            )
        else:
            active_skills.append(skill.name)
            console.print(
                Text(
                    f"  ● {t('skill.enabled', name=skill.display_name)}",
                    style=COLOR_MAIN,
                )
            )
        return True, active_skills

    # --- Неизвестная команда ---------------------------------------------
    console.print(
        Text(
            f"  ⚠ {t('err.unknown_command', command='/' + command)}",
            style=COLOR_WARN,
        )
    )
    console.print(Text(f"  {t('err.hint_help')}", style=COLOR_DIM))
    return True, active_skills


def _handle_language_command() -> None:
    """
    Обрабатывает команду /language — смену языка интерфейса на лету.

    Показывает мини-меню EN/RU, принимает ввод, сохраняет выбор
    в config.json и переинициализирует переводчик.
    """
    console.print()
    console.print(
        Text(
            "  Select a language · Выберите язык\n"
            "  [1] English\n"
            "  [2] Русский",
            style=COLOR_ACCENT,
        )
    )
    console.print()

    try:
        answer = console.input("  ▸ ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        console.print()
        return

    new_lang = ""
    if answer in ("1", "en", "eng", "english"):
        new_lang = "en"
    elif answer in ("2", "ru", "rus", "russian", "рус", "русский"):
        new_lang = "ru"

    if not new_lang:
        console.print(Text("  ✘ Invalid · Неверно.", style=COLOR_WARN))
        console.print()
        return

    try:
        config.set_language(new_lang)
        translator.init(new_lang)
        console.print(
            Text(f"  ✔ Language changed: {new_lang}", style=COLOR_MAIN)
        )
        console.print()
    except Exception as exc:
        console.print(Text(f"  ✘ {exc}", style=COLOR_ERROR))
        console.print()


# =============================================================================
#  ОБРАБОТКА ЗАПРОСА
# =============================================================================

def run_query(query: str, active_skills: list[str]) -> None:
    """
    Отправляет запрос в агент и показывает результат.
    """
    from core.agent import Agent

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
        console.print(Text(f"  ⚠ {t('err.interrupted')}", style=COLOR_WARN))
        console.print()
        return
    except Exception as exc:
        display.stop()
        console.print()
        console.print(
            Text(f"  ✘ {t('err.unexpected', error=str(exc))}", style=COLOR_ERROR)
        )
        console.print()
        return

    reasoning_time = display.stop()
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
        1 — критическая ошибка
    """
    # --- Создаём директории -----------------------------------------------
    config.ensure_dirs()

    # --- Проверяем, что переводчик инициализирован ------------------------
    # Если main.py уже вызвал init() — здесь ничего не произойдёт.
    # Если run() вызвали напрямую (например, из тестов) — грузим язык из config.
    current_lang = translator.get_language()
    if not current_lang:
        saved_lang = config.get_language() or "en"
        translator.init(saved_lang)

    # --- Проверяем наличие хотя бы одного ключа ---------------------------
    try:
        registry = get_registry()
        configured = registry.list_configured()
        if not configured:
            print_banner()
            console.print()
            console.print(
                Panel(
                    Text(t("err.no_key"), style="white"),
                    title=f"[bold {COLOR_ERROR}]{t('err.provider_not_configured', name='Mistral')}[/bold {COLOR_ERROR}]",
                    border_style=COLOR_ERROR,
                    padding=(1, 2),
                )
            )
            console.print()
            return 1
    except Exception:
        # Если реестр не работает — пропускаем проверку.
        pass

    # --- Приветствие ------------------------------------------------------
    os.system("clear")
    print_banner()
    print_memo()

    # --- Активные скиллы (пусто при старте) ------------------------------
    active_skills: list[str] = []

    # --- Обработка аргументов командной строки ---------------------------
    argv = sys.argv[1:]
    if argv:
        query_parts: list[str] = []
        for arg in argv:
            if arg.startswith("/"):
                low = arg.lower().lstrip("/")
                if low in ("changeagent", "agent"):
                    pick_agent()
                    continue
                if low in ("language", "lang-set"):
                    _handle_language_command()
                    continue
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
            # Формируем приглашение с учётом активных скиллов.
            prompt_text = f"[bold yellow]{t('prompt.main')}[/bold yellow]"
            if active_skills:
                badges = " ".join(f"[{s}]" for s in active_skills)
                prompt_text += f" [dim]{badges}[/dim]"
            prompt_text += f" [bold yellow]{t('prompt.arrow')}[/bold yellow]"

            line = Prompt.ask(prompt_text)

        except (KeyboardInterrupt, EOFError):
            console.print()
            console.print(Text(f"  {t('common.exit')}!", style=COLOR_ACCENT))
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

        # --- Обычный запрос ----------------------------------------------
        run_query(line, active_skills)


# =============================================================================
#  ЭКСПОРТ
# =============================================================================

__all__ = ["run", "console"]