# =============================================================================
#  Codermuks in Termux — генерация имён проектов v1.3.0
# =============================================================================
#  Что делает этот модуль:
#    • превращает произвольные названия в безопасные имена папок;
#    • убирает пробелы, кириллицу, спецсимволы;
#    • ищет коллизии в workspace (snake-game, snake-game-2, ...);
#    • умеет искать похожие проекты по fuzzy-сравнению.
#
#  Пример:
#      slugify("Игра Змейка на Python") → "igra-zmeyka-na-python"
#      resolve_collision("snake-game", ["snake-game"]) → "snake-game-2"
# =============================================================================

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from difflib import SequenceMatcher


# =============================================================================
#  ТРАНСЛИТЕРАЦИЯ РУССКОГО → ЛАТИНИЦА
# =============================================================================
#  Простая таблица — если проект называется по-русски, получим читаемое
#  латинское имя вместо мусора.
# =============================================================================

_TRANSLIT_MAP = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d",
    "е": "e", "ё": "yo", "ж": "zh", "з": "z", "и": "i",
    "й": "y", "к": "k", "л": "l", "м": "m", "н": "n",
    "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
    "у": "u", "ф": "f", "х": "h", "ц": "ts", "ч": "ch",
    "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "",
    "э": "e", "ю": "yu", "я": "ya",
}


def _transliterate(text: str) -> str:
    """Транслитерирует русские буквы в латиницу."""
    result: list[str] = []
    for ch in text.lower():
        result.append(_TRANSLIT_MAP.get(ch, ch))
    return "".join(result)


# =============================================================================
#  SLUGIFY
# =============================================================================

# Регулярка: оставляем только a-z, 0-9, дефис, подчёркивание.
_SAFE_CHARS_RE = re.compile(r"[^a-z0-9\-_]+")

# Многократные дефисы → один.
_MULTI_DASH_RE = re.compile(r"-{2,}")

# Слишком длинные имена обрезаем.
MAX_NAME_LENGTH = 50


def slugify(text: str) -> str:
    """
    Превращает произвольный текст в безопасное имя проекта.

    Правила:
        1. Транслитерируем кириллицу.
        2. Убираем всё, кроме a-z, 0-9, дефис, подчёркивание.
        3. Пробелы → дефис.
        4. Сжимаем многократные дефисы.
        5. Обрезаем до MAX_NAME_LENGTH.
        6. Убираем дефисы в начале и конце.

    Примеры:
        slugify("Игра Змейка") → "igra-zmeyka"
        slugify("HTTP Server (Go)") → "http-server-go"
        slugify("   my_awesome   project  ") → "my_awesome-project"
        slugify("!!!") → "project"  (фолбэк)
    """
    if not text:
        return "project"

    # 1. Транслитерация.
    text = _transliterate(text)

    # 2. Пробелы → дефис.
    text = text.replace(" ", "-")

    # 3. Оставляем только безопасные символы.
    text = _SAFE_CHARS_RE.sub("", text)

    # 4. Сжимаем дефисы.
    text = _MULTI_DASH_RE.sub("-", text)

    # 5. Обрезаем.
    if len(text) > MAX_NAME_LENGTH:
        text = text[:MAX_NAME_LENGTH]

    # 6. Убираем лишние символы в начале/конце.
    text = text.strip("-_")

    # 7. Фолбэк.
    if not text:
        return "project"

    return text


# =============================================================================
#  РАЗРЕШЕНИЕ КОЛЛИЗИЙ
# =============================================================================

def resolve_collision(name: str, existing: list[str]) -> str:
    """
    Добавляет суффикс -2, -3, ... если имя уже занято.

    Пример:
        resolve_collision("snake-game", ["snake-game"])
            → "snake-game-2"
        resolve_collision("calculator", ["calculator", "calculator-2"])
            → "calculator-3"
    """
    if name not in existing:
        return name

    counter = 2
    while f"{name}-{counter}" in existing:
        counter += 1
    return f"{name}-{counter}"


# =============================================================================
#  FUZZY-ПОИСК ПОХОЖИХ ПРОЕКТОВ
# =============================================================================

def similarity(a: str, b: str) -> float:
    """
    Возвращает коэффициент схожести двух строк от 0.0 до 1.0.
    Использует SequenceMatcher из стандартной библиотеки.
    """
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def find_similar(
    query: str,
    candidates: list[str],
    threshold: float = 0.6,
) -> list[tuple[str, float]]:
    """
    Ищет проекты, похожие на запрос.

    Аргументы:
        query       — текст запроса (например, «дополни калькулятор»).
        candidates  — список существующих имён проектов.
        threshold   — минимальный коэффициент схожести (0.6 по умолчанию).

    Возвращает:
        Список кортежей (имя, коэффициент), отсортированный по убыванию.

    Пример:
        find_similar("calculator", ["calculator", "snake-game"])
            → [("calculator", 1.0)]
        find_similar("calc", ["calculator", "snake-game"])
            → [("calculator", 0.7)]
    """
    if not query or not candidates:
        return []

    # Транслитерируем и нормализуем запрос.
    normalized_query = slugify(query)

    results: list[tuple[str, float]] = []
    for candidate in candidates:
        score = similarity(normalized_query, candidate)
        if score >= threshold:
            results.append((candidate, score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results


# =============================================================================
#  ГЕНЕРАЦИЯ ИМЕНИ ИЗ ЗАПРОСА (ПРОСТАЯ ЭВРИСТИКА)
# =============================================================================

# Слова, которые не несут смысла в имени проекта.
# Указываем на кириллице — потом автоматически транслитерируем,
# чтобы сравнивать с уже транслитерированным текстом запроса.
_STOP_WORDS_RAW = {
    "напиши", "сделай", "создай", "написать", "сделать", "создать",
    "мне", "нужно", "надо", "пожалуйста", "пожалуста",
    "программа", "программу", "приложение", "приложения",
    "код", "скрипт", "на", "для", "по", "в", "и", "с",
    "write", "make", "create", "the", "a", "an",
    "program", "application", "app", "code", "script",
    "simple", "простой", "простую", "простая", "простое",
    "игра", "игру", "игры",
    "бот", "бота", "боту", "боты",   # разные падежи
}

# Транслитерированные версии — добавляются автоматически ниже.
_STOP_WORDS = set(_STOP_WORDS_RAW) | {_transliterate(w) for w in _STOP_WORDS_RAW}


def guess_project_name_from_query(query: str) -> str:
    """
    Быстрая эвристика: вытаскивает имя проекта из запроса.

    Убирает стоп-слова, берёт 1–3 значимых слова, склеивает через дефис.

    Используется как fallback, если LLM не вернул project_name.
    """
    if not query:
        return "project"

    # Транслитерируем и разбиваем по пробелам.
    text = _transliterate(query.lower())
    words = re.findall(r"[a-z0-9_]+", text)

    # Убираем стоп-слова.
    meaningful = [w for w in words if w not in _STOP_WORDS and len(w) > 1]

    if not meaningful:
        # Всё — стоп-слова. Берём первые 2 слова как есть.
        meaningful = words[:2] if words else ["project"]

    # Берём первые 3 значимых слова.
    name = "-".join(meaningful[:3])

    return slugify(name)


# =============================================================================
#  ЭКСПОРТ
# =============================================================================

__all__ = [
    "slugify",
    "resolve_collision",
    "similarity",
    "find_similar",
    "guess_project_name_from_query",
    "MAX_NAME_LENGTH",
]
