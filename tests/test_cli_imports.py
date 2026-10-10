# =============================================================================
#  Codermuks in Termux — тесты импортов и базовых функций ui/cli.py v1.1.0
# =============================================================================
#  Что проверяем:
#    • ui/cli.py импортируется без ошибок;
#    • все публичные функции доступны;
#    • вспомогательные функции работают корректно;
#    • маппинг языков на Pygments корректен;
#    • ReasoningDisplay создаётся и управляется;
#    • handle_command корректно реагирует на базовые команды.
#
#  ВАЖНО: мы НЕ запускаем интерактивный цикл run() — он ждёт ввода
#  пользователя. Тестируем только импорты и вспомогательные функции.
# =============================================================================

from __future__ import annotations

import pytest


# =============================================================================
#  ИМПОРТЫ
# =============================================================================

class TestImports:
    """Тесты успешного импорта ui/cli.py и его зависимостей."""

    def test_cli_imports(self):
        """ui/cli.py импортируется без ошибок."""
        import ui.cli  # noqa: F401

    def test_console_object_exists(self):
        """Глобальный console — объект rich.Console."""
        from ui.cli import console
        from rich.console import Console
        assert isinstance(console, Console)

    def test_run_function_exists(self):
        """Функция run() доступна и вызывается."""
        from ui.cli import run
        assert callable(run)

    def test_print_banner_exists(self):
        """Функция print_banner() доступна."""
        from ui.cli import print_banner
        assert callable(print_banner)

    def test_print_memo_exists(self):
        """Функция print_memo() доступна."""
        from ui.cli import print_memo
        assert callable(print_memo)

    def test_print_result_exists(self):
        """Функция print_result() доступна."""
        from ui.cli import print_result
        assert callable(print_result)

    def test_print_languages_exists(self):
        """Функция print_languages() доступна."""
        from ui.cli import print_languages
        assert callable(print_languages)

    def test_handle_command_exists(self):
        """Функция handle_command() доступна."""
        from ui.cli import handle_command
        assert callable(handle_command)

    def test_run_query_exists(self):
        """Функция run_query() доступна."""
        from ui.cli import run_query
        assert callable(run_query)

    def test_reasoning_display_class_exists(self):
        """Класс ReasoningDisplay доступен."""
        from ui.cli import ReasoningDisplay
        assert ReasoningDisplay is not None


# =============================================================================
#  КОНСТАНТЫ
# =============================================================================

class TestConstants:
    """Тесты констант модуля."""

    def test_banner_lines_not_empty(self):
        """BANNER_LINES — непустой список строк."""
        from ui.cli import BANNER_LINES
        assert isinstance(BANNER_LINES, list)
        assert len(BANNER_LINES) > 0
        for line in BANNER_LINES:
            assert isinstance(line, str)

    def test_banner_subtitle(self):
        """BANNER_SUBTITLE содержит 'TERMUX'."""
        from ui.cli import BANNER_SUBTITLE
        assert "TERMUX" in BANNER_SUBTITLE.replace(" ", "")

    def test_colors_defined(self):
        """Все цветовые константы определены."""
        from ui.cli import (
            COLOR_MAIN, COLOR_ACCENT, COLOR_WARN,
            COLOR_ERROR, COLOR_DIM, COLOR_HIGHLIGHT,
        )
        for color in (
            COLOR_MAIN, COLOR_ACCENT, COLOR_WARN,
            COLOR_ERROR, COLOR_DIM, COLOR_HIGHLIGHT,
        ):
            assert isinstance(color, str)
            assert len(color) > 0


# =============================================================================
#  МАППИНГ ЯЗЫКОВ
# =============================================================================

class TestLanguageMapping:
    """Тесты функции _map_language_to_pygments()."""

    def test_python(self):
        """python → python."""
        from ui.cli import _map_language_to_pygments
        assert _map_language_to_pygments("python") == "python"

    def test_cpp(self):
        """cpp → cpp."""
        from ui.cli import _map_language_to_pygments
        assert _map_language_to_pygments("cpp") == "cpp"

    def test_rust(self):
        """rust → rust."""
        from ui.cli import _map_language_to_pygments
        assert _map_language_to_pygments("rust") == "rust"

    def test_go(self):
        """go → go."""
        from ui.cli import _map_language_to_pygments
        assert _map_language_to_pygments("go") == "go"

    def test_java(self):
        """java → java."""
        from ui.cli import _map_language_to_pygments
        assert _map_language_to_pygments("java") == "java"

    def test_javascript(self):
        """javascript → javascript."""
        from ui.cli import _map_language_to_pygments
        assert _map_language_to_pygments("javascript") == "javascript"

    def test_csharp(self):
        """csharp → csharp."""
        from ui.cli import _map_language_to_pygments
        assert _map_language_to_pygments("csharp") == "csharp"

    def test_unknown_returns_text(self):
        """Неизвестный язык → 'text'."""
        from ui.cli import _map_language_to_pygments
        assert _map_language_to_pygments("brainfuck") == "text"

    def test_empty_returns_text(self):
        """Пустой язык → 'text'."""
        from ui.cli import _map_language_to_pygments
        assert _map_language_to_pygments("") == "text"

    def test_all_known_languages(self):
        """Все поддерживаемые языки отображаются без 'text'."""
        from ui.cli import _map_language_to_pygments
        known = [
            "c", "cpp", "rust", "python", "go", "java", "javascript",
            "kotlin", "swift", "ruby", "php", "dart", "elixir",
            "haskell", "lua", "r", "sql", "csharp",
        ]
        for lang in known:
            result = _map_language_to_pygments(lang)
            assert result != "text", f"Язык {lang} не имеет маппинга"


# =============================================================================
#  REASONING DISPLAY
# =============================================================================

class TestReasoningDisplay:
    """Тесты класса ReasoningDisplay."""

    def test_create(self):
        """ReasoningDisplay создаётся без ошибок."""
        from ui.cli import ReasoningDisplay
        display = ReasoningDisplay()
        assert display is not None

    def test_start_and_stop(self):
        """start() и stop() работают без ошибок."""
        from ui.cli import ReasoningDisplay
        display = ReasoningDisplay()
        display.start()
        # Дадим немного времени на один refresh.
        import time
        time.sleep(0.1)
        elapsed = display.stop()
        assert isinstance(elapsed, float)
        assert elapsed >= 0

    def test_update_step(self):
        """update() меняет текущий шаг."""
        from ui.cli import ReasoningDisplay
        display = ReasoningDisplay()
        display.start()
        display.update("планирование", "разбираю задачу")
        display.stop()
        # Главное — не упало.

    def test_stop_returns_elapsed(self):
        """stop() возвращает положительное время после старта."""
        from ui.cli import ReasoningDisplay
        import time
        display = ReasoningDisplay()
        display.start()
        time.sleep(0.15)
        elapsed = display.stop()
        assert elapsed >= 0.1


# =============================================================================
#  HANDLE COMMAND
# =============================================================================

class TestHandleCommand:
    """Тесты обработки команд."""

    def test_exit_command(self, reset_translator, clean_config):
        """/exit возвращает (False, ...)."""
        from ui.cli import handle_command
        from core.i18n import translator
        translator.init("en")

        keep_going, skills = handle_command("/exit", [])
        assert keep_going is False

    def test_help_command(self, reset_translator, clean_config):
        """/help возвращает (True, ...) и не меняет скиллы."""
        from ui.cli import handle_command
        from core.i18n import translator
        translator.init("en")

        keep_going, skills = handle_command("/help", [])
        assert keep_going is True
        assert skills == []

    def test_clear_command(self, reset_translator, clean_config):
        """/clear возвращает (True, ...)."""
        from ui.cli import handle_command
        from core.i18n import translator
        translator.init("en")

        keep_going, skills = handle_command("/clear", [])
        assert keep_going is True

    def test_research_skill_toggles_on(self, reset_translator, clean_config):
        """/research включает скилл."""
        from ui.cli import handle_command
        from core.i18n import translator
        translator.init("en")

        keep_going, skills = handle_command("/research", [])
        assert keep_going is True
        assert "research" in skills

    def test_research_skill_toggles_off(self, reset_translator, clean_config):
        """/research выключает скилл, если он уже включён."""
        from ui.cli import handle_command
        from core.i18n import translator
        translator.init("en")

        keep_going, skills = handle_command("/research", ["research"])
        assert keep_going is True
        assert "research" not in skills

    def test_reason_skill(self, reset_translator, clean_config):
        """/reason включает скилл рассуждений."""
        from ui.cli import handle_command
        from core.i18n import translator
        translator.init("en")

        keep_going, skills = handle_command("/reason", [])
        assert keep_going is True
        assert "reason" in skills

    def test_analyze_skill(self, reset_translator, clean_config):
        """/analyze включает скилл анализа."""
        from ui.cli import handle_command
        from core.i18n import translator
        translator.init("en")

        keep_going, skills = handle_command("/analyze", [])
        assert keep_going is True
        assert "analyze" in skills

    def test_unknown_command(self, reset_translator, clean_config):
        """Неизвестная команда не ломает цикл и не меняет скиллы."""
        from ui.cli import handle_command
        from core.i18n import translator
        translator.init("en")

        keep_going, skills = handle_command("/nonexistent", ["research"])
        assert keep_going is True
        assert skills == ["research"]

    def test_skill_toggle_preserves_others(self, reset_translator, clean_config):
        """Toggle одного скилла не сбрасывает остальные."""
        from ui.cli import handle_command
        from core.i18n import translator
        translator.init("en")

        keep_going, skills = handle_command("/reason", ["research"])
        assert keep_going is True
        assert "research" in skills
        assert "reason" in skills


# =============================================================================
#  ЗАВИСИМОСТИ МОДУЛЯ
# =============================================================================

class TestDependencies:
    """Тесты зависимостей ui/cli.py."""

    def test_imports_rich(self):
        """rich доступен."""
        import rich
        assert rich is not None

    def test_imports_translator(self):
        """core.i18n.translator доступен."""
        from core.i18n import translator  # noqa: F401

    def test_imports_agent_picker(self):
        """ui.agent_picker доступен."""
        from ui import agent_picker  # noqa: F401

    def test_imports_agent_registry(self):
        """core.team.agent_registry доступен."""
        from core.team import agent_registry  # noqa: F401

    def test_imports_config(self):
        """core.config доступен."""
        from core import config  # noqa: F401

    def test_imports_helpers(self):
        """utils.helpers доступен."""
        from utils import helpers  # noqa: F401

    def test_imports_skills(self):
        """skills.modes доступен."""
        from skills import modes  # noqa: F401


# =============================================================================
#  ПРОВЕРКА t() В КОНТЕКСТЕ CLI
# =============================================================================

class TestTranslationIntegration:
    """Проверка, что все ключи, используемые в cli.py, есть в переводах."""

    def test_all_cli_keys_exist_in_en(self, reset_translator):
        """Все ключи, которые CLI берёт из i18n, есть в en.py."""
        from core.i18n import translator
        translator.init("en")

        # Ключи, которые cli.py запрашивает через t().
        used_keys = [
            "welcome.banner",
            "welcome.version",
            "welcome.subtitle",
            "memo.title",
            "memo.footer.lead",
            "memo.footer.model",
            "cmd.name.changeagent",
            "cmd.name.language",
            "cmd.name.research",
            "cmd.name.reason",
            "cmd.name.analyze",
            "cmd.name.langs",
            "cmd.name.skills",
            "cmd.name.clear",
            "cmd.name.help",
            "cmd.name.exit",
            "cmd.changeagent",
            "cmd.language",
            "cmd.research",
            "cmd.reason",
            "cmd.analyze",
            "cmd.langs",
            "cmd.skills",
            "cmd.clear",
            "cmd.help",
            "cmd.exit",
            "status.thinking",
            "result.success",
            "result.failure",
            "result.language",
            "result.iterations",
            "result.reasoning_time",
            "result.exit_code",
            "result.code",
            "result.stdout",
            "result.stderr",
            "result.notes",
            "result.provider",
            "result.artifact",
            "err.interrupted",
            "err.unexpected",
            "err.unknown_command",
            "err.hint_help",
            "err.no_key",
            "err.provider_not_configured",
            "lang.title.basic",
            "lang.title.extended",
            "lang.column.name",
            "lang.column.tool",
            "lang.column.status",
            "lang.column.install",
            "lang.available",
            "lang.not_available",
            "skill.enabled",
            "skill.disabled",
            "common.exit",
            "prompt.main",
            "prompt.arrow",
        ]

        for key in used_keys:
            assert translator.has_key(key), f"Ключ '{key}' отсутствует в en.py"

    def test_all_cli_keys_exist_in_ru(self, reset_translator):
        """Все ключи CLI есть в ru.py."""
        from core.i18n import translator
        translator.init("ru")

        used_keys = [
            "welcome.banner",
            "cmd.name.changeagent",
            "cmd.name.language",
            "status.thinking",
            "result.success",
            "err.interrupted",
            "skill.enabled",
            "prompt.main",
        ]

        for key in used_keys:
            assert translator.has_key(key), f"Ключ '{key}' отсутствует в ru.py"


# =============================================================================
#  ПАКЕТНЫЙ ЭКСПОРТ
# =============================================================================

class TestPackageExport:
    """Тесты __all__ в cli.py."""

    def test_all_contains_run(self):
        """__all__ содержит 'run'."""
        from ui import cli
        assert "run" in cli.__all__

    def test_all_contains_console(self):
        """__all__ содержит 'console'."""
        from ui import cli
        assert "console" in cli.__all__