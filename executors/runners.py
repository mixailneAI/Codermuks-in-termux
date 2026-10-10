# =============================================================================
#  Codermuks in Termux — исполнители кода (основной набор)
# =============================================================================
#  Этот модуль отвечает за компиляцию и запуск кода на основных языках,
#  которые чаще всего используются в Termux:
#
#      C, C++, Rust, Python, Go, Java, JavaScript
#
#  Расширенный набор (Kotlin, Swift, Ruby, PHP, Dart, Elixir, Haskell,
#  Lua, R, SQL, C#) живёт в extended_runners.py.
#
#  Что делает модуль:
#    1. Проверяет, что язык поддерживается и компилятор установлен.
#    2. Создаёт изолированную временную директорию под каждую задачу.
#    3. Записывает исходник в файл.
#    4. Компилирует (если язык компилируемый) с таймаутом.
#    5. Запускает бинарник или интерпретатор с таймаутом.
#    6. Возвращает stdout / stderr / код возврата / длительность.
#    7. Всегда чистит временную директорию после работы.
# =============================================================================

from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from core import config


# =============================================================================
#  КОНФИГУРАЦИЯ ЯЗЫКА
# =============================================================================

@dataclass
class LanguageConfig:
    """
    Описание одного языка программирования.

    Поля:
        name          — каноническое имя ("cpp", "rust", ...)
        display_name  — человеко-читаемое имя ("C++", "Rust", ...)
        extension     — расширение исходного файла (".cpp", ".rs", ...)
        compile_cmd   — команда компиляции или None для интерпретируемых
                        Плейсхолдеры: {src} — исходник, {out} — бинарник
        run_cmd       — команда запуска
                        Плейсхолдеры: {src} — исходник, {out} — бинарник
        check_binary  — имя бинарника для проверки установки
        source_base   — базовое имя исходника без расширения (обычно "main")
    """
    name: str
    display_name: str
    extension: str
    compile_cmd: list[str] | None
    run_cmd: list[str]
    check_binary: str
    source_base: str = "main"


# =============================================================================
#  РЕЕСТР ЯЗЫКОВ
# =============================================================================
#  Здесь описаны все основные языки. Если нужно добавить язык —
#  достаточно дописать сюда запись, и он автоматически появится
#  в supported_languages().
# =============================================================================

LANG_CONFIG: dict[str, LanguageConfig] = {
    # --- C -------------------------------------------------------------------
    "c": LanguageConfig(
        name="c",
        display_name="C",
        extension=".c",
        compile_cmd=["gcc", "{src}", "-o", "{out}", "-lm", "-O2", "-std=c11"],
        run_cmd=["./{out}"],
        check_binary="gcc",
    ),

    # --- C++ -----------------------------------------------------------------
    "cpp": LanguageConfig(
        name="cpp",
        display_name="C++",
        extension=".cpp",
        compile_cmd=["g++", "{src}", "-o", "{out}", "-std=c++17", "-O2"],
        run_cmd=["./{out}"],
        check_binary="g++",
    ),

    # --- Rust ----------------------------------------------------------------
    "rust": LanguageConfig(
        name="rust",
        display_name="Rust",
        extension=".rs",
        compile_cmd=["rustc", "{src}", "-o", "{out}", "-O"],
        run_cmd=["./{out}"],
        check_binary="rustc",
    ),

    # --- Python --------------------------------------------------------------
    "python": LanguageConfig(
        name="python",
        display_name="Python",
        extension=".py",
        compile_cmd=None,   # интерпретируемый
        run_cmd=["python", "{src}"],
        check_binary="python",
    ),

    # --- Go ------------------------------------------------------------------
    "go": LanguageConfig(
        name="go",
        display_name="Go",
        extension=".go",
        compile_cmd=["go", "build", "-o", "{out}", "{src}"],
        run_cmd=["./{out}"],
        check_binary="go",
    ),

    # --- Java ----------------------------------------------------------------
    #  Используем single-file source-code mode (Java 11+), который
    #  компилирует файл «на лету». Так не нужно отдельно вызывать javac
    #  и вручную следить за соответствием имени класса и файла.
    "java": LanguageConfig(
        name="java",
        display_name="Java",
        extension=".java",
        compile_cmd=None,
        run_cmd=["java", "{src}"],
        check_binary="java",
    ),

    # --- JavaScript (Node.js) ------------------------------------------------
    "javascript": LanguageConfig(
        name="javascript",
        display_name="JavaScript",
        extension=".js",
        compile_cmd=None,
        run_cmd=["node", "{src}"],
        check_binary="node",
    ),
}


# =============================================================================
#  ПРОВЕРКА ДОСТУПНОСТИ КОМПИЛЯТОРА
# =============================================================================

#  Кэш проверок: чтобы не вызывать shutil.which() на каждый запуск.
_BINARY_CACHE: dict[str, bool] = {}


def _check_binary(name: str) -> bool:
    """
    Проверяет, доступен ли указанный бинарник в PATH.

    Результат кэшируется, чтобы не проверять одно и то же много раз.
    """
    if name in _BINARY_CACHE:
        return _BINARY_CACHE[name]

    result = shutil.which(name) is not None
    _BINARY_CACHE[name] = result
    return result


def reset_binary_cache() -> None:
    """Сбрасывает кэш проверок бинарников (полезно при тестировании)."""
    _BINARY_CACHE.clear()


# =============================================================================
#  ОПРЕДЕЛЕНИЕ ИМЕНИ ИСХОДНОГО ФАЙЛА
# =============================================================================

def _build_source_filename(language: str, cfg: LanguageConfig, code: str) -> str:
    """
    Возвращает имя исходного файла для заданного языка и кода.

    Для большинства языков это просто <source_base><extension>.
    Исключение — Java: имя файла обязано совпадать с именем
    публичного класса (или класса с точкой входа).
    """
    if language == "java":
        # Ищем имя публичного класса, иначе — первого класса в файле.
        match = re.search(r"public\s+(?:final\s+|abstract\s+)?class\s+(\w+)", code)
        if match:
            return f"{match.group(1)}.java"

        match = re.search(r"\bclass\s+(\w+)", code)
        if match:
            return f"{match.group(1)}.java"

        # Ничего не нашли — используем дефолтное имя.
        return "Main.java"

    return f"{cfg.source_base}{cfg.extension}"


# =============================================================================
#  ЗАПУСК ПОДПРОЦЕССА
# =============================================================================

def _run_subprocess(
    cmd: list[str],
    cwd: Path,
    timeout: int,
) -> tuple[str, str, int, bool]:
    """
    Запускает подпроцесс и возвращает результат.

    Возвращает кортеж:
        (stdout, stderr, exit_code, timed_out)

    Никогда не выбрасывает исключения — все проблемы упаковываются
    в возвращаемые значения. Это упрощает обработку на уровне run_code.
    """
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return (
            proc.stdout or "",
            proc.stderr or "",
            proc.returncode if proc.returncode is not None else -1,
            False,
        )
    except subprocess.TimeoutExpired as exc:
        # Процесс не уложился в таймаут — собираем то, что успел выдать.
        out = ""
        err = ""
        if exc.stdout:
            out = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else exc.stdout
        if exc.stderr:
            err = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else exc.stderr
        err = (err + f"\n[Таймаут: {timeout} сек]").strip()
        return out, err, -1, True
    except FileNotFoundError as exc:
        return "", f"Бинарник не найден: {exc}", 127, False
    except Exception as exc:
        return "", f"Ошибка запуска подпроцесса: {exc}", -1, False


# =============================================================================
#  ОСНОВНАЯ ФУНКЦИЯ
# =============================================================================

def run_code(language: str, code: str) -> dict:
    """
    Компилирует и запускает код на указанном языке.

    Аргументы:
        language — каноническое имя языка ("cpp", "rust", ...)
        code     — исходный код строкой

    Возвращает словарь:
        {
            "stdout":       str    — что напечатала программа,
            "stderr":       str    — ошибки компиляции или исполнения,
            "exit_code":    int    — код возврата (0 — успех),
            "duration":     float  — сколько секунд заняло всё,
            "language":     str    — язык,
            "stage":        str    — стадия, на которой остановились:
                                      "ok"          — всё хорошо
                                      "compile"     — упало на компиляции
                                      "run"         — упало при исполнении
                                      "timeout"     — превышен таймаут
                                      "unsupported" — язык не поддерживается
                                      "no_binary"   — нет компилятора/рантайма
                                      "internal"    — внутренняя ошибка
        }
    """
    started_at = time.time()

    # --- Шаг 1: проверяем поддержку языка ---------------------------------
    if language not in LANG_CONFIG:
        supported = ", ".join(sorted(LANG_CONFIG.keys()))
        return {
            "stdout": "",
            "stderr": (
                f"Язык '{language}' не поддерживается. "
                f"Доступные: {supported}."
            ),
            "exit_code": -1,
            "duration": time.time() - started_at,
            "language": language,
            "stage": "unsupported",
        }

    cfg = LANG_CONFIG[language]

    # --- Шаг 2: проверяем наличие компилятора/рантайма --------------------
    if not _check_binary(cfg.check_binary):
        return {
            "stdout": "",
            "stderr": (
                f"Не найден '{cfg.check_binary}' — не установлен компилятор "
                f"или рантайм для языка {cfg.display_name}. "
                f"Установи его через pkg install."
            ),
            "exit_code": -1,
            "duration": time.time() - started_at,
            "language": language,
            "stage": "no_binary",
        }

    # --- Шаг 3: создаём изолированную временную директорию ---------------
    #  Каждый запуск получает свой уникальный подкаталог в TEMP_DIR.
    #  Это исключает конфликты при параллельных задачах и гарантирует,
    #  что после работы мы удалим ровно то, что создали.
    run_id = uuid.uuid4().hex[:12]
    workdir = config.TEMP_DIR / f"{language}_{run_id}"

    try:
        workdir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return {
            "stdout": "",
            "stderr": f"Не удалось создать рабочую директорию: {exc}",
            "exit_code": -1,
            "duration": time.time() - started_at,
            "language": language,
            "stage": "internal",
        }

    try:
        # --- Шаг 4: записываем исходник ------------------------------------
        source_name = _build_source_filename(language, cfg, code)
        source_path = workdir / source_name

        try:
            source_path.write_text(code, encoding="utf-8")
        except Exception as exc:
            return {
                "stdout": "",
                "stderr": f"Не удалось записать исходный файл: {exc}",
                "exit_code": -1,
                "duration": time.time() - started_at,
                "language": language,
                "stage": "internal",
            }

        #  Имя выходного бинарника — фиксированное, чтобы не завязываться
        #  на имя исходника.
        output_name = "program"

        # --- Шаг 5: компиляция (если нужна) --------------------------------
        if cfg.compile_cmd is not None:
            compile_argv = [
                arg.replace("{src}", source_name).replace("{out}", output_name)
                for arg in cfg.compile_cmd
            ]
            comp_out, comp_err, comp_code, comp_timeout = _run_subprocess(
                compile_argv,
                cwd=workdir,
                timeout=config.COMPILE_TIMEOUT,
            )

            if comp_timeout:
                return {
                    "stdout": comp_out,
                    "stderr": (
                        f"Компиляция превысила таймаут "
                        f"({config.COMPILE_TIMEOUT} сек).\n{comp_err}"
                    ),
                    "exit_code": -1,
                    "duration": time.time() - started_at,
                    "language": language,
                    "stage": "timeout",
                }

            if comp_code != 0:
                #  Компилятор вернул ненулевой код — это ошибка сборки.
                #  Отдаём stderr как есть, чтобы кодер увидел сообщения.
                return {
                    "stdout": comp_out,
                    "stderr": comp_err or "Компиляция завершилась с ошибкой.",
                    "exit_code": comp_code,
                    "duration": time.time() - started_at,
                    "language": language,
                    "stage": "compile",
                }

        # --- Шаг 6: запуск -------------------------------------------------
        run_argv = [
            arg.replace("{src}", source_name).replace("{out}", output_name)
            for arg in cfg.run_cmd
        ]
        run_out, run_err, run_code_exit, run_timeout = _run_subprocess(
            run_argv,
            cwd=workdir,
            timeout=config.RUN_TIMEOUT,
        )

        if run_timeout:
            return {
                "stdout": run_out,
                "stderr": (
                    f"Программа превысила таймаут "
                    f"({config.RUN_TIMEOUT} сек).\n{run_err}"
                ),
                "exit_code": -1,
                "duration": time.time() - started_at,
                "language": language,
                "stage": "timeout",
            }

        # --- Шаг 7: определяем финальную стадию ----------------------------
        if run_code_exit == 0 and not run_err.strip():
            stage = "ok"
        else:
            stage = "run"

        return {
            "stdout": run_out,
            "stderr": run_err,
            "exit_code": run_code_exit,
            "duration": time.time() - started_at,
            "language": language,
            "stage": stage,
        }

    except Exception as exc:
        #  Любая непредвиденная ошибка — упаковываем в стандартный ответ.
        return {
            "stdout": "",
            "stderr": f"Внутренняя ошибка раннера: {exc}",
            "exit_code": -1,
            "duration": time.time() - started_at,
            "language": language,
            "stage": "internal",
        }
    finally:
        # --- Шаг 8: чистим временную директорию ----------------------------
        #  Удаляем всё, что создали, чтобы не засорять хранилище.
        #  Ошибки удаления игнорируем — это не критично для работы.
        try:
            shutil.rmtree(workdir, ignore_errors=True)
        except Exception:
            pass


# =============================================================================
#  ПУБЛИЧНЫЕ ХЕЛПЕРЫ
# =============================================================================

def is_language_supported(language: str) -> bool:
    """
    Проверяет, поддерживается ли указанный язык.

    Регистр не важен: "Cpp" и "cpp" — одно и то же.
    """
    if not language:
        return False
    return language.strip().lower() in LANG_CONFIG


def supported_languages() -> list[str]:
    """
    Возвращает отсортированный список канонических имён всех
    поддерживаемых языков.
    """
    return sorted(LANG_CONFIG.keys())


def get_language_config(language: str) -> LanguageConfig | None:
    """
    Возвращает конфигурацию языка или None, если язык не поддерживается.
    """
    if not language:
        return None
    return LANG_CONFIG.get(language.strip().lower())


def available_languages() -> list[str]:
    """
    Возвращает список языков, для которых реально установлен
    компилятор или рантайм в системе.
    """
    available: list[str] = []
    for lang, cfg in LANG_CONFIG.items():
        if _check_binary(cfg.check_binary):
            available.append(lang)
    return sorted(available)


def language_info(language: str) -> dict:
    """
    Возвращает информацию о языке для отображения в CLI.

    Формат:
        {
            "supported":    bool,
            "available":    bool,
            "display_name": str,
            "check_binary": str,
        }
    """
    cfg = get_language_config(language)
    if cfg is None:
        return {
            "supported": False,
            "available": False,
            "display_name": language,
            "check_binary": "",
        }

    return {
        "supported": True,
        "available": _check_binary(cfg.check_binary),
        "display_name": cfg.display_name,
        "check_binary": cfg.check_binary,
    }