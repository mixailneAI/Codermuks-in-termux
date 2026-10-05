# =============================================================================
#  Codermuks in Termux — исполнители кода (расширенный набор)
# =============================================================================
#  Этот модуль добавляет поддержку менее распространённых, но всё ещё
#  актуальных в 2026 году языков программирования:
#
#      Kotlin, Swift, Ruby, PHP, Dart, Elixir, Haskell, Lua, R, SQL, C#
#
#  Как это работает:
#    1. При импорте модуль регистрирует свои LanguageConfig в общем
#       реестре LANG_CONFIG, который живёт в executors/runners.py.
#    2. Функция run_code() из runners.py автоматически подхватывает
#       новые языки — никаких изменений в основном модуле не требуется.
#    3. Перед запуском проверяется наличие компилятора или рантайма.
#       Если инструмент не установлен — возвращается понятная ошибка
#       с подсказкой, что именно нужно поставить.
#
#  Регистрация идемпотентна: повторный импорт не создаёт дубликатов
#  и не перезаписывает уже существующие конфигурации.
# =============================================================================

from __future__ import annotations

import shutil

from executors.runners import (
    LANG_CONFIG,
    LanguageConfig,
)


# =============================================================================
#  ЛОКАЛЬНАЯ ПРОВЕРКА БИНАРНИКОВ
# =============================================================================
#  Не импортируем _check_binary из runners.py (это приватная функция),
#  а держим собственный кэш. Так модуль остаётся самодостаточным и
#  не зависит от внутренних деталей соседнего файла.
# =============================================================================

_BINARY_CACHE: dict[str, bool] = {}


def _has_binary(name: str) -> bool:
    """
    Проверяет, доступен ли указанный бинарник в PATH.

    Результат кэшируется — повторные проверки не бьют по файловой системе.
    """
    if name in _BINARY_CACHE:
        return _BINARY_CACHE[name]
    result = shutil.which(name) is not None
    _BINARY_CACHE[name] = result
    return result


def reset_extended_cache() -> None:
    """
    Сбрасывает локальный кэш проверок.

    Полезно, если пользователь установил новый компилятор без
    перезапуска приложения.
    """
    _BINARY_CACHE.clear()


# =============================================================================
#  РАСШИРЕННЫЕ ЯЗЫКИ
# =============================================================================
#  Каждый язык описан тем же форматом, что и в runners.py.
#
#  Плейсхолдеры в командах:
#      {src} — имя исходного файла
#      {out} — имя выходного бинарника или архива
#
#  Поле check_binary — имя исполняемого файла, наличие которого
#  проверяется перед запуском. Если его нет — раннер вернёт
#  stage="no_binary" с понятным сообщением.
# =============================================================================

EXTENDED_LANG_CONFIG: dict[str, LanguageConfig] = {

    # -------------------------------------------------------------------------
    #  Kotlin
    # -------------------------------------------------------------------------
    #  Компилируется в JVM-байткод. Собираем в self-contained JAR
    #  (флаг -include-runtime) и запускаем через java -jar.
    #  Это самый надёжный способ в Termux, где kotlinc ставят отдельно.
    # -------------------------------------------------------------------------
    "kotlin": LanguageConfig(
        name="kotlin",
        display_name="Kotlin",
        extension=".kt",
        compile_cmd=[
            "kotlinc",
            "{src}",
            "-include-runtime",
            "-d",
            "{out}.jar",
        ],
        run_cmd=["java", "-jar", "{out}.jar"],
        check_binary="kotlinc",
    ),

    # -------------------------------------------------------------------------
    #  Swift
    # -------------------------------------------------------------------------
    #  Компилируется в нативный бинарник через swiftc. В Termux
    #  ставится из сторонних репозиториев (официального пакета нет).
    # -------------------------------------------------------------------------
    "swift": LanguageConfig(
        name="swift",
        display_name="Swift",
        extension=".swift",
        compile_cmd=["swiftc", "{src}", "-o", "{out}"],
        run_cmd=["./{out}"],
        check_binary="swiftc",
    ),

    # -------------------------------------------------------------------------
    #  Ruby
    # -------------------------------------------------------------------------
    #  Интерпретируемый. Запускаем исходник напрямую. Устанавливается
    #  штатно через `pkg install ruby`.
    # -------------------------------------------------------------------------
    "ruby": LanguageConfig(
        name="ruby",
        display_name="Ruby",
        extension=".rb",
        compile_cmd=None,
        run_cmd=["ruby", "{src}"],
        check_binary="ruby",
    ),

    # -------------------------------------------------------------------------
    #  PHP
    # -------------------------------------------------------------------------
    #  Интерпретируемый. Запускаем CLI-версией php (не путать с php-fpm).
    #  Ставится через `pkg install php`.
    # -------------------------------------------------------------------------
    "php": LanguageConfig(
        name="php",
        display_name="PHP",
        extension=".php",
        compile_cmd=None,
        run_cmd=["php", "{src}"],
        check_binary="php",
    ),

    # -------------------------------------------------------------------------
    #  Dart
    # -------------------------------------------------------------------------
    #  Интерпретируемый через `dart run`. Компиляция в AOT-бинарник
    #  тоже возможна (dart compile exe), но в Termux работает нестабильно
    #  из-за ограничений на размер temp. Прямой запуск надёжнее.
    # -------------------------------------------------------------------------
    "dart": LanguageConfig(
        name="dart",
        display_name="Dart",
        extension=".dart",
        compile_cmd=None,
        run_cmd=["dart", "run", "{src}"],
        check_binary="dart",
    ),

    # -------------------------------------------------------------------------
    #  Elixir
    # -------------------------------------------------------------------------
    #  Интерпретируемый через elixir. Используем расширение .exs —
    #  это скриптовый режим Elixir, не требующий проекта mix.
    # -------------------------------------------------------------------------
    "elixir": LanguageConfig(
        name="elixir",
        display_name="Elixir",
        extension=".exs",
        compile_cmd=None,
        run_cmd=["elixir", "{src}"],
        check_binary="elixir",
    ),

    # -------------------------------------------------------------------------
    #  Haskell
    # -------------------------------------------------------------------------
    #  Компилируемый через GHC. Флаг -O2 включает оптимизацию, без него
    #  код на Haskell работает заметно медленнее.
    # -------------------------------------------------------------------------
    "haskell": LanguageConfig(
        name="haskell",
        display_name="Haskell",
        extension=".hs",
        compile_cmd=["ghc", "{src}", "-o", "{out}", "-O2"],
        run_cmd=["./{out}"],
        check_binary="ghc",
    ),

    # -------------------------------------------------------------------------
    #  Lua
    # -------------------------------------------------------------------------
    #  Интерпретируемый. Лёгкий и быстрый, идеально подходит для Termux.
    #  Ставится через `pkg install lua54`.
    # -------------------------------------------------------------------------
    "lua": LanguageConfig(
        name="lua",
        display_name="Lua",
        extension=".lua",
        compile_cmd=None,
        run_cmd=["lua", "{src}"],
        check_binary="lua",
    ),

    # -------------------------------------------------------------------------
    #  R
    # -------------------------------------------------------------------------
    #  Интерпретируемый. Rscript — CLI-обёртка без интерактивной сессии.
    #  Расширение .R (заглавная) — конвенция R-сообщества.
    # -------------------------------------------------------------------------
    "r": LanguageConfig(
        name="r",
        display_name="R",
        extension=".R",
        compile_cmd=None,
        run_cmd=["Rscript", "{src}"],
        check_binary="Rscript",
    ),

    # -------------------------------------------------------------------------
    #  SQL (SQLite)
    # -------------------------------------------------------------------------
    #  Особый случай: пользователь пишет SQL-скрипт, мы выполняем его
    #  в sqlite3. Используем .read — команда sqlite3, которая читает
    #  файл как последовательность SQL-инструкций.
    #
    #  База — в памяти (:memory:), чтобы не оставлять мусорных файлов.
    #  Ставится через `pkg install sqlite`.
    # -------------------------------------------------------------------------
    "sql": LanguageConfig(
        name="sql",
        display_name="SQL (SQLite)",
        extension=".sql",
        compile_cmd=None,
        run_cmd=["sqlite3", ":memory:", ".read", "{src}"],
        check_binary="sqlite3",
    ),

    # -------------------------------------------------------------------------
    #  C# (Mono)
    # -------------------------------------------------------------------------
    #  В Termux официального .NET нет, но есть Mono — это открытая
    #  реализация .NET Framework и C#-компилятор mcs. Работает
    #  стабильно для большинства учебных и прикладных задач.
    #
    #  Компилируем mcs в .exe, запускаем через mono.
    # -------------------------------------------------------------------------
    "csharp": LanguageConfig(
        name="csharp",
        display_name="C#",
        extension=".cs",
        compile_cmd=["mcs", "{src}", "-out:{out}"],
        run_cmd=["mono", "{out}"],
        check_binary="mcs",
    ),
}


# =============================================================================
#  РЕГИСТРАЦИЯ В ОСНОВНОМ РЕЕСТРЕ
# =============================================================================

def register_extended_languages() -> int:
    """
    Регистрирует расширенные языки в основном реестре LANG_CONFIG.

    Возвращает количество фактически добавленных языков.
    Языки, которые уже присутствуют в LANG_CONFIG, не перезаписываются —
    это защищает от случайного затирания пользовательских конфигураций.
    """
    added = 0
    for name, cfg in EXTENDED_LANG_CONFIG.items():
        if name not in LANG_CONFIG:
            LANG_CONFIG[name] = cfg
            added += 1
    return added


# Регистрируем сразу при импорте — чтобы любой код, который сделал
# `import executors.extended_runners`, сразу получил расширенный набор.
register_extended_languages()


# =============================================================================
#  ПУБЛИЧНЫЕ ХЕЛПЕРЫ
# =============================================================================

def extended_supported_languages() -> list[str]:
    """
    Возвращает отсортированный список имён всех расширенных языков,
    которые модуль умеет обрабатывать (независимо от того, установлены
    ли для них инструменты).
    """
    return sorted(EXTENDED_LANG_CONFIG.keys())


def extended_available_languages() -> list[str]:
    """
    Возвращает список расширенных языков, для которых установлен
    компилятор или рантайм. Проверка идёт по check_binary из конфига.
    """
    available: list[str] = []
    for lang, cfg in EXTENDED_LANG_CONFIG.items():
        if _has_binary(cfg.check_binary):
            available.append(lang)
    return sorted(available)


def extended_language_status() -> dict[str, dict]:
    """
    Возвращает полный статус каждого расширенного языка.

    Формат:
        {
            "kotlin": {
                "display_name": "Kotlin",
                "check_binary": "kotlinc",
                "available":    True/False,
                "package":      "kotlin (через sdkman или отдельный репозиторий)",
                "extension":    ".kt",
            },
            ...
        }
    """
    # Подсказки по установке. Для языков, которых нет в штатном pkg,
    # указываем альтернативные способы.
    package_hints: dict[str, str] = {
        "kotlin":   "kotlin (SDKMAN или отдельный репозиторий)",
        "swift":    "swift (сторонний репозиторий, не из pkg)",
        "ruby":     "pkg install ruby",
        "php":      "pkg install php",
        "dart":     "dart (сторонний репозиторий)",
        "elixir":   "pkg install elixir",
        "haskell":  "pkg install ghc",
        "lua":      "pkg install lua54",
        "r":        "pkg install r-base (может отсутствовать в Termux)",
        "sql":      "pkg install sqlite",
        "csharp":   "mono (сторонний репозиторий)",
    }

    status: dict[str, dict] = {}
    for lang, cfg in EXTENDED_LANG_CONFIG.items():
        status[lang] = {
            "display_name": cfg.display_name,
            "check_binary": cfg.check_binary,
            "available": _has_binary(cfg.check_binary),
            "package": package_hints.get(lang, cfg.check_binary),
            "extension": cfg.extension,
        }
    return status


def print_extended_status() -> str:
    """
    Формирует человеко-читаемую таблицу со статусом расширенных языков.

    Возвращает готовую строку — её можно напечатать через rich или
    обычный print в CLI.
    """
    status = extended_language_status()

    # Заголовок таблицы.
    lines: list[str] = []
    lines.append("Расширенные языки программирования:")
    lines.append("")
    lines.append(f"{'Язык':<14} {'Инструмент':<12} {'Статус':<16} Установка")
    lines.append("─" * 78)

    # Сортируем по display_name для стабильного вывода.
    sorted_items = sorted(status.items(), key=lambda kv: kv[1]["display_name"])

    available_count = 0
    for _lang, info in sorted_items:
        display = info["display_name"]
        binary = info["check_binary"]
        if info["available"]:
            available_count += 1
            mark = "✔ доступен"
        else:
            mark = "✘ не найден"
        package = info["package"]
        lines.append(f"{display:<14} {binary:<12} {mark:<16} {package}")

    lines.append("─" * 78)
    lines.append(
        f"Итого: {available_count} из {len(sorted_items)} языков готовы к работе."
    )

    # Если чего-то не хватает — добавим короткую подсказку.
    if available_count < len(sorted_items):
        lines.append("")
        lines.append(
            "Чтобы включить остальные — установи соответствующие пакеты "
            "и перезапусти проверку командой /langs."
        )

    return "\n".join(lines)


def extended_language_info(language: str) -> dict:
    """
    Возвращает детальную информацию об одном расширенном языке.

    Если язык не найден в расширенном наборе — возвращает
    {"supported": False}.
    """
    if not language:
        return {"supported": False}

    key = language.strip().lower()
    cfg = EXTENDED_LANG_CONFIG.get(key)
    if cfg is None:
        return {"supported": False}

    return {
        "supported": True,
        "available": _has_binary(cfg.check_binary),
        "display_name": cfg.display_name,
        "check_binary": cfg.check_binary,
        "extension": cfg.extension,
        "compile_cmd": cfg.compile_cmd,
        "run_cmd": cfg.run_cmd,
    }