# =============================================================================
#  Codermuks in Termux — вспомогательные утилиты
# =============================================================================
#  Мелкие функции, которые используются в разных модулях:
#    • форматирование времени в «1 мин 23 сек»;
#    • безопасное создание временных директорий;
#    • сохранение артефактов (готового кода) в ~/.codermuks/artifacts/;
#    • настройка логгера с записью в файл;
#    • проверка поддержки эмодзи и цветов в терминале.
# =============================================================================

from __future__ import annotations

import logging
import os
import re
import shutil
import time
from datetime import datetime
from pathlib import Path

from core import config


# =============================================================================
#  ФОРМАТИРОВАНИЕ ВРЕМЕНИ
# =============================================================================

def format_duration(seconds: float) -> str:
    """
    Превращает число секунд в человеко-читаемую строку.

    Примеры:
        0.5     → "0.5 сек"
        12      → "12 сек"
        65      → "1 мин 5 сек"
        3725    → "1 ч 2 мин 5 сек"
    """
    if seconds < 1:
        return f"{seconds:.1f} сек"

    total = int(round(seconds))
    hours = total // 3600
    minutes = (total % 3600) // 60
    secs = total % 60

    parts: list[str] = []
    if hours:
        parts.append(f"{hours} ч")
    if minutes:
        parts.append(f"{minutes} мин")
    if secs or not parts:
        parts.append(f"{secs} сек")

    return " ".join(parts)


def format_bytes(num_bytes: int) -> str:
    """
    Превращает число байт в человеко-читаемый размер: "12.4 КБ", "1.2 МБ".
    """
    size = float(num_bytes)
    for unit in ("Б", "КБ", "МБ", "ГБ", "ТБ"):
        if size < 1024:
            if unit == "Б":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} ПБ"


# =============================================================================
#  ВРЕМЕННЫЕ ДИРЕКТОРИИ
# =============================================================================

def make_tempdir(prefix: str = "codermuks_") -> Path:
    """
    Создаёт уникальную временную директорию внутри ~/.codermuks/temp/.

    Возвращает путь. Директория сразу готова к использованию.
    """
    # Убеждаемся, что корень TEMP_DIR существует.
    config.TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # Формируем уникальное имя: префикс + timestamp + счётчик.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = str(int(time.time() * 1000) % 10000).zfill(4)
    name = f"{prefix}{timestamp}_{suffix}"

    path = config.TEMP_DIR / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def cleanup_tempdir(path: Path) -> None:
    """
    Удаляет временную директорию, если она внутри TEMP_DIR.

    Защита от случайного удаления чего-то важного: удаляем только
    то, что лежит в ~/.codermuks/temp/.
    """
    try:
        resolved = path.resolve()
        root = config.TEMP_DIR.resolve()
        resolved.relative_to(root)
    except (ValueError, OSError):
        return

    shutil.rmtree(path, ignore_errors=True)


def cleanup_all_temp() -> int:
    """
    Удаляет всю папку TEMP_DIR и создаёт заново.

    Возвращает количество удалённых элементов верхнего уровня.
    Вызывается при старте, чтобы подчистить хвосты предыдущих сессий.
    """
    if not config.TEMP_DIR.exists():
        config.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        return 0

    count = 0
    try:
        for entry in config.TEMP_DIR.iterdir():
            count += 1
            if entry.is_dir():
                shutil.rmtree(entry, ignore_errors=True)
            else:
                try:
                    entry.unlink()
                except OSError:
                    pass
    except OSError:
        pass

    return count


# =============================================================================
#  СОХРАНЕНИЕ АРТЕФАКТОВ
# =============================================================================

# Расширения для разных языков — используется при сохранении артефакта.
_LANG_EXTENSIONS: dict[str, str] = {
    "c": ".c",
    "cpp": ".cpp",
    "rust": ".rs",
    "python": ".py",
    "go": ".go",
    "java": ".java",
    "javascript": ".js",
    "kotlin": ".kt",
    "swift": ".swift",
    "ruby": ".rb",
    "php": ".php",
    "dart": ".dart",
    "elixir": ".exs",
    "haskell": ".hs",
    "lua": ".lua",
    "r": ".R",
    "sql": ".sql",
    "csharp": ".cs",
}


def save_artifact(
    code: str,
    language: str = "",
    success: bool = True,
) -> Path:
    """
    Сохраняет сгенерированный код в ~/.codermuks/artifacts/.

    Аргументы:
        code     — исходный код
        language — каноническое имя языка (для выбора расширения)
        success  — успешно ли завершилась задача; помечается в имени файла

    Возвращает путь к сохранённому файлу.

    Имя файла формируется как:
        YYYY-MM-DD_HH-MM-SS_<lang>_<ok|fail>.<ext>
    """
    config.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    # Определяем расширение по языку.
    ext = _LANG_EXTENSIONS.get(language, ".txt")

    # Формируем имя файла.
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    status = "ok" if success else "fail"
    lang_part = language or "unknown"
    filename = f"{timestamp}_{lang_part}_{status}{ext}"

    path = config.ARTIFACTS_DIR / filename
    path.write_text(code, encoding="utf-8")
    return path


def list_artifacts() -> list[Path]:
    """
    Возвращает список сохранённых артефактов, отсортированный
    по времени изменения (сначала новые).
    """
    if not config.ARTIFACTS_DIR.exists():
        return []

    files = [
        p for p in config.ARTIFACTS_DIR.iterdir()
        if p.is_file()
    ]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files


# =============================================================================
#  ЛОГИРОВАНИЕ
# =============================================================================

_logger_configured: bool = False


def get_logger(name: str = "codermuks") -> logging.Logger:
    """
    Возвращает настроенный логгер.

    Логгер пишет в файл ~/.codermuks.log в формате:
        [YYYY-MM-DD HH:MM:SS] [LEVEL] [name] сообщение

    При первом вызове создаёт файл и добавляет обработчик.
    Повторные вызовы возвращают тот же логгер без дублирования
    обработчиков.
    """
    global _logger_configured

    logger = logging.getLogger(name)

    if _logger_configured:
        return logger

    logger.setLevel(logging.INFO)

    try:
        handler = logging.FileHandler(config.LOG_FILE, encoding="utf-8")
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    except OSError:
        # Не можем открыть файл — молча работаем без логирования.
        logger.addHandler(logging.NullHandler())

    _logger_configured = True
    return logger


def log_exception(logger: logging.Logger, exc: Exception, context: str = "") -> None:
    """
    Записывает исключение в лог с трассировкой.
    """
    if context:
        logger.error("%s: %s", context, exc, exc_info=True)
    else:
        logger.error("Исключение: %s", exc, exc_info=True)


# =============================================================================
#  ПРОВЕРКИ ОКРУЖЕНИЯ
# =============================================================================

def terminal_width() -> int:
    """
    Возвращает ширину терминала в колонках.

    Fallback — 80, если определить не удалось.
    """
    try:
        return shutil.get_terminal_size((80, 24)).columns
    except Exception:
        return 80


def supports_emoji() -> bool:
    """
    Проверяет, поддерживает ли терминал эмодзи.

    Смотрит на переменные окружения: если LANG или LC_ALL содержат
    UTF-8, эмодзи скорее всего работают.
    """
    lang = os.environ.get("LANG", "") + os.environ.get("LC_ALL", "")
    return "utf" in lang.lower()


def supports_colors() -> bool:
    """
    Проверяет, поддерживает ли терминал ANSI-цвета.

    Termux поддерживает всегда; проверка нужна для запуска
    на других платформах.
    """
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM") in (None, "", "dumb"):
        return False
    return True


def humanize_query(query: str) -> str:
    """
    Приводит запрос к «одной строке»: убирает лишние пробелы и
    переносы строк.

    Полезно, когда пользователь вставил многострочный текст.
    """
    if not query:
        return ""
    return re.sub(r"\s+", " ", query).strip()


# =============================================================================
#  РАБОТА С ИМЕНАМИ ФАЙЛОВ
# =============================================================================

def safe_filename(name: str) -> str:
    """
    Превращает произвольную строку в безопасное имя файла.

    Убирает спецсимволы, оставляя буквы, цифры, дефисы, точки
    и подчёркивания.
    """
    if not name:
        return "unnamed"
    cleaned = re.sub(r"[^\w\-.]+", "_", name, flags=re.UNICODE)
    cleaned = cleaned.strip("._") or "unnamed"
    return cleaned[:120]


def ensure_extension(filename: str, extension: str) -> str:
    """
    Добавляет расширение к имени файла, если его ещё нет.
    """
    if not extension.startswith("."):
        extension = "." + extension
    if filename.endswith(extension):
        return filename
    return filename + extension


# =============================================================================
#  ФОРМАТИРОВАНИЕ СТАТУСОВ
# =============================================================================

def status_icon(success: bool) -> str:
    """Возвращает галочку или крестик в зависимости от статуса."""
    return "✔" if success else "✘"


def progress_bar(current: int, total: int, width: int = 20) -> str:
    """
    Рисует текстовый прогресс-бар.

    Пример: [████████░░░░░░░░░░░░] 40%
    """
    if total <= 0:
        total = 1
    ratio = min(max(current / total, 0.0), 1.0)
    filled = int(round(width * ratio))
    bar = "█" * filled + "░" * (width - filled)
    percent = int(round(ratio * 100))
    return f"[{bar}] {percent}%"