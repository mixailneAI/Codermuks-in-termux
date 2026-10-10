# =============================================================================
#  Codermuks in Termux — менеджер переводов v1.1.0
# =============================================================================
#  Центральный модуль системы интернационализации. Отвечает за:
#    • загрузку строк выбранного языка (en / ru);
#    • функцию перевода t("ключ") → строка;
#    • подстановку плейсхолдеров вида {name} в строки;
#    • плюрализацию через tn("ключ", n) — если понадобится;
#    • смену языка на лету через set_language().
#
#  ВАЖНО: модуль работает даже без вызова init(). Если пользователь
#  обратится к t() до инициализации, будет использован английский
#  как безопасный дефолт.
# =============================================================================

from __future__ import annotations

from typing import Any


# =============================================================================
#  ВНУТРЕННЕЕ СОСТОЯНИЕ
# =============================================================================

# Текущий язык. None означает «ещё не выбран» — используем дефолт.
_current_language: str | None = None

# Кэш загруженных словарей. Заполняется при init() и set_language().
_strings: dict[str, str] = {}

# Список поддерживаемых языков и их «человеческие» названия.
SUPPORTED_LANGUAGES: dict[str, str] = {
    "en": "English",
    "ru": "Русский",
}

# Язык по умолчанию — используется, пока пользователь не выбрал свой.
DEFAULT_LANGUAGE: str = "en"


# =============================================================================
#  ЗАГРУЗКА СЛОВАРЕЙ
# =============================================================================

def _load_strings(language: str) -> dict[str, str]:
    """
    Загружает словарь строк для указанного языка.

    Импортирует соответствующий модуль (en.py или ru.py) и берёт
    из него константу STRINGS. Если модуль не найден или словарь
    пуст — возвращает пустой словарь (все ключи будут отдаваться
    как есть, это безопасное поведение).

    Аргументы:
        language — код языка: "en" или "ru".

    Возвращает:
        Словарь вида {"ключ": "строка"}.
    """
    if language == "en":
        try:
            from core.i18n import en
            return dict(getattr(en, "STRINGS", {}))
        except Exception:
            return {}

    if language == "ru":
        try:
            from core.i18n import ru
            return dict(getattr(ru, "STRINGS", {}))
        except Exception:
            return {}

    return {}


# =============================================================================
#  ИНИЦИАЛИЗАЦИЯ
# =============================================================================

def init(language: str) -> None:
    """
    Инициализирует переводчик выбранным языком.

    Загружает словарь строк и сохраняет его в памяти. Вызывается
    из main.py сразу после того, как пользователь выбрал язык
    (или язык был прочитан из config.json).

    Аргументы:
        language — код языка: "en" или "ru".
                   Если язык не поддерживается — молча ставит дефолт.

    Пример:
        from core.i18n import translator
        translator.init("ru")
        print(translator.t("cmd.exit"))   # → "выйти из программы"
    """
    global _current_language, _strings

    lang = (language or "").strip().lower()

    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE

    _current_language = lang
    _strings = _load_strings(lang)

    # На случай, если словарь языка пуст — подгружаем дефолт.
    if not _strings and lang != DEFAULT_LANGUAGE:
        _strings = _load_strings(DEFAULT_LANGUAGE)


def set_language(language: str) -> None:
    """
    Меняет язык на лету. Обёртка над init() — оставлена для
    семантики (например, вызов из CLI по команде /language).

    Аргументы:
        language — код языка: "en" или "ru".
    """
    init(language)


def get_language() -> str:
    """
    Возвращает текущий код языка.

    Если init() ещё не вызывался — вернёт DEFAULT_LANGUAGE.
    """
    return _current_language or DEFAULT_LANGUAGE


def list_languages() -> dict[str, str]:
    """
    Возвращает словарь поддерживаемых языков:
        {"en": "English", "ru": "Русский"}
    """
    return dict(SUPPORTED_LANGUAGES)


# =============================================================================
#  ПЕРЕВОД
# =============================================================================

def t(key: str, **kwargs: Any) -> str:
    """
    Переводит ключ на текущий язык.

    Аргументы:
        key    — ключ строки, например "cmd.exit".
        kwargs — плейсхолдеры для подстановки, например name="Qwen".

    Возвращает:
        Переведённую строку. Если ключ не найден — возвращает сам ключ
        (чтобы сразу видеть забытые переводы).

    Примеры:
        t("cmd.exit")                    # → "выйти из программы"
        t("fallback.switch", name="Qwen")  # → "Переключиться на Qwen? [y/n]:"
    """
    if not key:
        return ""

    # Если словарь пуст (init не вызывался) — грузим дефолт.
    if not _strings:
        init(_current_language or DEFAULT_LANGUAGE)

    # Ищем строку в текущем языке.
    template = _strings.get(key)

    # Если строки нет — попробуем английский как фолбэк.
    if template is None and _current_language != DEFAULT_LANGUAGE:
        fallback = _load_strings(DEFAULT_LANGUAGE)
        template = fallback.get(key)

    # Если строки нет нигде — возвращаем сам ключ.
    if template is None:
        template = key

    # Подставляем плейсхолдеры, если они были переданы.
    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            # Если что-то не так с плейсхолдерами — возвращаем
            # строку как есть, без подстановки.
            return template

    return template


def tn(key: str, count: int, **kwargs: Any) -> str:
    """
    Перевод с учётом числа (плюрализация).

    Ищет ключ с суффиксом _one или _many в зависимости от count,
    и подставляет в него {count} и остальные плейсхолдеры.

    Для русского языка правила такие:
        • count % 10 == 1, но count % 100 != 11  → _one
        • всё остальное                            → _many

    Для английского:
        • count == 1    → _one
        • иначе         → _many

    Аргументы:
        key    — базовый ключ без суффикса, например "step.iterations".
        count  — число.
        kwargs — дополнительные плейсхолдеры.

    Пример:
        tn("step.iterations", 1)   # → "1 итерация"
        tn("step.iterations", 5)   # → "5 итераций"
    """
    lang = get_language()

    # Выбираем суффикс по правилам языка.
    if lang == "ru":
        if count % 10 == 1 and count % 100 != 11:
            suffix = "_one"
        else:
            suffix = "_many"
    else:
        suffix = "_one" if count == 1 else "_many"

    # Сначала пробуем ключ с суффиксом, если нет — базовый.
    full_key = f"{key}{suffix}"
    result = t(full_key, count=count, **kwargs)

    # Если вернулся сам ключ (нет перевода) — пробуем базовый.
    if result == full_key:
        result = t(key, count=count, **kwargs)

    return result


# =============================================================================
#  УТИЛИТЫ
# =============================================================================

def has_key(key: str) -> bool:
    """
    Проверяет, есть ли перевод для данного ключа в текущем языке.
    Полезно для тестов и отладки.
    """
    if not _strings:
        init(_current_language or DEFAULT_LANGUAGE)
    return key in _strings


def keys() -> list[str]:
    """
    Возвращает отсортированный список всех ключей текущего языка.
    Полезно для отладки: если чего-то не хватает в ru.py, это сразу
    видно при сравнении keys() для en и ru.
    """
    if not _strings:
        init(_current_language or DEFAULT_LANGUAGE)
    return sorted(_strings.keys())


def missing_keys() -> dict[str, list[str]]:
    """
    Сравнивает два словаря (en и ru) и возвращает ключи, которых
    не хватает в каждом из них. Используется в тестах.

    Возвращает:
        {
            "missing_in_ru": [...],
            "missing_in_en": [...]
        }
    """
    en = _load_strings("en")
    ru = _load_strings("ru")

    en_keys = set(en.keys())
    ru_keys = set(ru.keys())

    return {
        "missing_in_ru": sorted(en_keys - ru_keys),
        "missing_in_en": sorted(ru_keys - en_keys),
    }


# =============================================================================
#  ЭКСПОРТ
# =============================================================================

__all__ = [
    "init",
    "set_language",
    "get_language",
    "list_languages",
    "t",
    "tn",
    "has_key",
    "keys",
    "missing_keys",
    "SUPPORTED_LANGUAGES",
    "DEFAULT_LANGUAGE",
]