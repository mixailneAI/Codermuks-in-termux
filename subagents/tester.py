# =============================================================================
#  Codermuks in Termux — субагент-тестировщик
# =============================================================================
#  Задача тестировщика — запустить код и вернуть результат:
#    • успешно скомпилировалось и отработало;
#    • упало с ошибкой компиляции;
#    • упало с ошибкой исполнения (runtime);
#    • превысило таймаут.
#
#  Тестировщик не «думает» — он просто вызывает executors/runners.py
#  и упаковывает результат в удобную структуру.
# =============================================================================

from __future__ import annotations

from typing import Any

from executors.runners import run_code, is_language_supported, supported_languages
from subagents.base import BaseSubagent


# =============================================================================
#  СУБАГЕНТ
# =============================================================================

class TesterSubagent(BaseSubagent):
    """Субагент, который компилирует и запускает код."""

    name = "tester"
    description = "Компилирует и запускает код на разных языках, возвращает результат."

    # -------------------------------------------------------------------------
    #  Основной интерфейс
    # -------------------------------------------------------------------------

    def test(self, language: str, code: str) -> dict[str, Any]:
        """
        Компилирует и запускает код.

        Аргументы:
            language — каноническое имя языка ("cpp", "rust", "python", ...)
            code     — исходный код

        Возвращает словарь:
            {
                "stdout":     str   — вывод программы (что напечатала),
                "stderr":     str   — ошибки компиляции или исполнения,
                "exit_code":  int   — код возврата (0 — успех),
                "duration":   float — сколько секунд заняла компиляция и запуск,
                "language":   str   — язык, на котором компилировали,
                "stage":      str   — "compile", "run", "ok" или "timeout",
            }

        Никогда не выбрасывает исключения — все ошибки упакованы в словарь.
        """
        # Проверяем, поддерживается ли язык.
        if not is_language_supported(language):
            supported = ", ".join(supported_languages())
            message = (
                f"Язык '{language}' не поддерживается. "
                f"Доступные языки: {supported}"
            )
            self.log(message)
            return {
                "stdout": "",
                "stderr": message,
                "exit_code": -1,
                "duration": 0.0,
                "language": language,
                "stage": "unsupported",
            }

        self.log(f"Запускаю код на '{language}' ({len(code)} символов).")

        try:
            result = run_code(language, code)
        except Exception as exc:
            self.log(f"Раннер выбросил исключение: {exc}")
            return {
                "stdout": "",
                "stderr": f"Внутренняя ошибка раннера: {exc}",
                "exit_code": -1,
                "duration": 0.0,
                "language": language,
                "stage": "runner_error",
            }

        # Раннер уже возвращает словарь с нужными полями — прокидываем его.
        exit_code = int(result.get("exit_code", -1))
        stderr = result.get("stderr", "") or ""

        if exit_code == 0 and not stderr.strip():
            self.log("Код успешно скомпилирован и выполнен.")
        else:
            self.log(
                f"Код завершился с ошибкой (exit={exit_code}, "
                f"stderr={len(stderr)} символов)."
            )

        return result

    def run(self, task: str, **kwargs: Any) -> str:
        """
        Универсальный метод запуска из BaseSubagent.

        Используется, когда менеджер вызывает тестировщика через run().
        Ожидает в kwargs параметры language и code.
        """
        language = kwargs.get("language", "")
        code = kwargs.get("code", "")

        if not language or not code:
            return "Ошибка: не переданы параметры 'language' и 'code'."

        result = self.test(language, code)

        # Формируем человеко-читаемый отчёт.
        parts: list[str] = []
        parts.append(f"Язык: {result.get('language', language)}")
        parts.append(f"Стадия: {result.get('stage', 'unknown')}")
        parts.append(f"Код возврата: {result.get('exit_code', -1)}")
        parts.append(f"Длительность: {result.get('duration', 0.0):.2f} сек")

        stdout = result.get("stdout", "")
        stderr = result.get("stderr", "")

        if stdout:
            parts.append(f"\n--- stdout ---\n{stdout}")
        if stderr:
            parts.append(f"\n--- stderr ---\n{stderr}")

        return "\n".join(parts)