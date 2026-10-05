# =============================================================================
#  Codermuks in Termux — субагент-кодер
# =============================================================================
#  Задача кодера — писать код через модель Codestral. Он получает задачу
#  на естественном языке, отправляет её в Mistral и возвращает готовый
#  блок кода с указанием языка.
#
#  Что умеет:
#    • генерировать код по описанию задачи;
#    • определять язык программирования из ответа модели;
#    • нормализовать имена языков (cpp → c++, csharp → c# и т. д.);
#    • исправлять код по сообщению об ошибке от тестировщика.
# =============================================================================

from __future__ import annotations

from typing import Any

from core.mistral_client import get_client
from prompts.templates import SYSTEM_CODER
from subagents.base import BaseSubagent


# =============================================================================
#  ТАБЛИЦА НОРМАЛИЗАЦИИ ЯЗЫКОВ
# =============================================================================
#  Codestral иногда возвращает нестандартные обозначения. Приводим их
#  к каноническим именам, которые понимает executors/runners.py.
# =============================================================================

LANGUAGE_ALIASES: dict[str, str] = {
    # C и производные
    "c": "c",
    "c99": "c",
    "c11": "c",
    "c17": "c",
    "cpp": "cpp",
    "c++": "cpp",
    "cplusplus": "cpp",
    "cxx": "cpp",
    "cc": "cpp",
    "c#": "csharp",
    "csharp": "csharp",
    "cs": "csharp",
    "dotnet": "csharp",

    # Rust
    "rust": "rust",
    "rs": "rust",
    "rustlang": "rust",

    # Go
    "go": "go",
    "golang": "go",

    # Python
    "python": "python",
    "py": "python",
    "python3": "python",
    "py3": "python",

    # Java
    "java": "java",

    # JavaScript / Node.js
    "javascript": "javascript",
    "js": "javascript",
    "node": "javascript",
    "nodejs": "javascript",
    "typescript": "javascript",
    "ts": "javascript",

    # Расширенные языки
    "kotlin": "kotlin",
    "kt": "kotlin",
    "swift": "swift",
    "ruby": "ruby",
    "rb": "ruby",
    "php": "php",
    "dart": "dart",
    "elixir": "elixir",
    "ex": "elixir",
    "haskell": "haskell",
    "hs": "haskell",
    "lua": "lua",
    "r": "r",
    "sql": "sql",
    "sqlite": "sql",
}


# =============================================================================
#  СУБАГЕНТ
# =============================================================================

class CoderSubagent(BaseSubagent):
    """Субагент, который пишет код через Codestral."""

    name = "coder"
    description = "Генерирует и исправляет код на любом языке программирования."

    # -------------------------------------------------------------------------
    #  Публичные методы
    # -------------------------------------------------------------------------

    def run(self, task: str, **kwargs: Any) -> str:
        """
        Универсальный метод запуска.

        В простом случае используется для генерации кода по текстовой
        задаче. Если в kwargs передан параметр `system_prompt`, он
        подменяет системный промпт по умолчанию.
        """
        system_prompt = kwargs.get("system_prompt", SYSTEM_CODER)
        temperature = kwargs.get("temperature", None)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task},
        ]

        self.log(f"Отправляю задачу в Codestral: {task[:80]}...")
        response = self.client.chat(
            messages=messages,
            model=kwargs.get("model"),
            temperature=temperature,
        )
        self.log(f"Получен ответ длиной {len(response)} символов.")
        return response

    def parse_response(self, response: str) -> tuple[str, str]:
        """
        Разбирает ответ Codestral и извлекает язык и код.

        Возвращает кортеж (language, code):
            language — каноническое имя языка ("cpp", "rust", ...)
            code     — готовый к компиляции исходник

        Если блоков кода несколько, берётся первый. Если блоков нет —
        возвращается ("", "") и записывается предупреждение в лог.
        """
        lang_raw, code = self.extract_first_code(response)

        if not code:
            self.log("Не удалось найти блок кода в ответе модели.")
            return "", ""

        # Нормализуем имя языка.
        language = self.normalize_language(lang_raw)

        # Если язык не указан в блоке — пробуем угадать по содержимому.
        if not language:
            language = self.guess_language_from_code(code)
            self.log(f"Язык не указан в блоке — определил как '{language}'.")

        self.log(f"Извлечён код: язык={language}, {len(code)} символов.")
        return language, code

    def normalize_language(self, raw: str) -> str:
        """
        Приводит название языка к каноническому виду.

        Если язык неизвестен — возвращает исходную строку в нижнем регистре.
        Если raw пустой — возвращает пустую строку.
        """
        if not raw:
            return ""
        key = raw.strip().lower()
        return LANGUAGE_ALIASES.get(key, key)

    def guess_language_from_code(self, code: str) -> str:
        """
        Пытается определить язык по характерным признакам кода.

        Это эвристика — она не идеальна, но помогает, когда модель
        забыла указать язык в блоке. Если ничего не найдено —
        возвращается 'python' как самый безопасный вариант для Termux.
        """
        text = code

        # C++ — есть #include и std:: или cout.
        if "#include" in text and ("std::" in text or "cout" in text or "template" in text):
            return "cpp"

        # C — есть #include и printf, но нет плюсовых признаков.
        if "#include" in text and ("printf" in text or "malloc" in text or "int main" in text):
            return "c"

        # Rust — fn main или let mut.
        if "fn main" in text or "let mut" in text or "println!" in text:
            return "rust"

        # Go — package main и func main.
        if "package main" in text or ("func " in text and "package " in text):
            return "go"

        # Java — public class и public static void main.
        if "public class" in text and "public static void main" in text:
            return "java"

        # C# — using System и namespace.
        if "using System" in text or ("namespace " in text and "Console.WriteLine" in text):
            return "csharp"

        # JavaScript / TypeScript — function, const, let, =>.
        if "console.log" in text or "function " in text or "const " in text or "=>" in text:
            return "javascript"

        # Kotlin — fun main и val/var.
        if "fun main" in text or ("val " in text and "package " in text):
            return "kotlin"

        # Swift — import Swift/Foundation и func.
        if "import Swift" in text or "import Foundation" in text:
            return "swift"

        # Ruby — puts и def ... end.
        if "puts " in text or ("def " in text and "end" in text):
            return "ruby"

        # PHP — <?php.
        if "<?php" in text:
            return "php"

        # Lua — local и print.
        if "local " in text and "print(" in text:
            return "lua"

        # Haskell — module и main :: IO.
        if "module Main" in text or "main :: IO" in text:
            return "haskell"

        # Elixir — defmodule.
        if "defmodule " in text:
            return "elixir"

        # Python — по умолчанию.
        return "python"