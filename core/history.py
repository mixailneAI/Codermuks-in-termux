# =============================================================================
#  Codermuks in Termux — история проектов v1.2.0
# =============================================================================
#  Что делает этот модуль:
#    • сохраняет историю задач для каждого проекта;
#    • читает историю из .codermuks/history.json;
#    • позволяет агенту «помнить», что уже было сделано;
#    • форматирует историю для показа пользователю.
#
#  Структура history.json:
#      {
#        "project_name": "calculator",
#        "language": "python",
#        "created_at": "2026-10-15T14:32:00",
#        "tasks": [
#          {
#            "date": "2026-10-15T14:32:00",
#            "query": "напиши простой калькулятор",
#            "result": "success",
#            "provider": "mistral",
#            "model": "codestral-latest",
#            "reasoning_time": 8.3,
#            "files_created": ["calculator.py", "README.md"],
#            "files_modified": []
#          },
#          {
#            "date": "2026-10-16T09:15:00",
#            "query": "добавь возведение в степень",
#            "result": "success",
#            "files_modified": ["calculator.py"]
#          }
#        ]
#      }
# =============================================================================

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


# =============================================================================
#  КОНСТАНТЫ
# =============================================================================

# Имя скрытой папки внутри проекта.
PROJECT_META_DIR = ".codermuks"

# Имя файла истории.
HISTORY_FILE = "history.json"

# Сколько последних задач показывать по умолчанию.
DEFAULT_RECENT_LIMIT = 10


# =============================================================================
#  ПУТИ
# =============================================================================

def get_history_path(project_path: Path) -> Path:
    """Возвращает путь к history.json проекта."""
    return project_path / PROJECT_META_DIR / HISTORY_FILE


# =============================================================================
#  ЧТЕНИЕ И ЗАПИСЬ
# =============================================================================

def load_history(project_path: Path) -> dict[str, Any]:
    """
    Читает history.json проекта.

    Если файла нет или он повреждён — возвращает пустую структуру.
    Никогда не выбрасывает исключение — безопасно для вызова где угодно.
    """
    path = get_history_path(project_path)

    if not path.exists():
        return _empty_history(project_path)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return _empty_history(project_path)

    # Гарантируем наличие всех ключей.
    if "tasks" not in data or not isinstance(data["tasks"], list):
        data["tasks"] = []

    data.setdefault("project_name", project_path.name)
    data.setdefault("language", "")
    data.setdefault("created_at", datetime.now().isoformat(timespec="seconds"))

    return data


def save_history(project_path: Path, history: dict[str, Any]) -> None:
    """
    Сохраняет history.json на диск.

    Создаёт служебную папку .codermuks/, если её нет.
    """
    path = get_history_path(project_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _empty_history(project_path: Path) -> dict[str, Any]:
    """Возвращает пустую структуру истории для нового проекта."""
    return {
        "project_name": project_path.name,
        "language": "",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "tasks": [],
    }


# =============================================================================
#  ДОБАВЛЕНИЕ ЗАПИСЕЙ
# =============================================================================

def add_task(
    project_path: Path,
    query: str,
    result: str,
    *,
    provider: str = "",
    model: str = "",
    reasoning_time: float = 0.0,
    files_created: list[str] | None = None,
    files_modified: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """
    Добавляет запись о задаче в историю проекта.

    Аргументы:
        project_path      — путь к папке проекта.
        query             — исходный запрос пользователя.
        result            — "success" или "failure".
        provider          — имя провайдера ("mistral", "qwen", ...).
        model             — имя модели.
        reasoning_time    — сколько секунд думал агент.
        files_created     — список созданных файлов.
        files_modified    — список изменённых файлов.
        extra             — любые дополнительные поля.

    Пример:
        add_task(
            project_path,
            "напиши калькулятор",
            "success",
            provider="mistral",
            model="codestral-latest",
            reasoning_time=8.3,
            files_created=["calculator.py", "README.md"],
        )
    """
    history = load_history(project_path)

    entry: dict[str, Any] = {
        "date": datetime.now().isoformat(timespec="seconds"),
        "query": query,
        "result": result,
    }

    if provider:
        entry["provider"] = provider
    if model:
        entry["model"] = model
    if reasoning_time > 0:
        entry["reasoning_time"] = round(reasoning_time, 2)
    if files_created:
        entry["files_created"] = files_created
    if files_modified:
        entry["files_modified"] = files_modified
    if extra:
        entry.update(extra)

    history["tasks"].append(entry)
    save_history(project_path, history)


def update_language(project_path: Path, language: str) -> None:
    """
    Обновляет язык проекта в history.json.
    Вызывается при первом определении языка.
    """
    history = load_history(project_path)
    history["language"] = language
    save_history(project_path, history)


# =============================================================================
#  ЧТЕНИЕ ИСТОРИИ
# =============================================================================

def get_tasks(project_path: Path) -> list[dict[str, Any]]:
    """Возвращает полный список задач проекта."""
    return load_history(project_path).get("tasks", [])


def get_recent(
    project_path: Path,
    limit: int = DEFAULT_RECENT_LIMIT,
) -> list[dict[str, Any]]:
    """
    Возвращает последние N задач (свежие первыми).
    """
    tasks = get_tasks(project_path)
    return list(reversed(tasks[-limit:]))


def get_summary(project_path: Path) -> dict[str, Any]:
    """
    Возвращает сводку по проекту:
        {
            "total_tasks": 5,
            "success": 4,
            "failure": 1,
            "first_task_date": "...",
            "last_task_date": "...",
            "language": "python",
        }
    """
    history = load_history(project_path)
    tasks = history.get("tasks", [])

    if not tasks:
        return {
            "total_tasks": 0,
            "success": 0,
            "failure": 0,
            "first_task_date": "",
            "last_task_date": "",
            "language": history.get("language", ""),
        }

    success = sum(1 for t in tasks if t.get("result") == "success")
    failure = len(tasks) - success

    return {
        "total_tasks": len(tasks),
        "success": success,
        "failure": failure,
        "first_task_date": tasks[0].get("date", ""),
        "last_task_date": tasks[-1].get("date", ""),
        "language": history.get("language", ""),
    }


# =============================================================================
#  КОНТЕКСТ ДЛЯ LLM
# =============================================================================

def get_context_for_llm(
    project_path: Path,
    limit: int = 5,
) -> str:
    """
    Формирует текст-контекст о предыдущих задачах — для передачи
    в промпт планировщику.

    Планировщик видит, что уже было сделано, и не дублирует работу.

    Пример вывода:
        Previous tasks in this project:
        1. [2026-10-15] напиши простой калькулятор → success
        2. [2026-10-16] добавь возведение в степень → success
    """
    tasks = get_recent(project_path, limit=limit)

    if not tasks:
        return ""

    lines = ["Previous tasks in this project:"]
    # Показываем в хронологическом порядке (старые сверху).
    for i, task in enumerate(reversed(tasks), start=1):
        date = task.get("date", "")[:10]  # только дата
        query = task.get("query", "").strip()
        result = task.get("result", "unknown")
        lines.append(f"{i}. [{date}] {query} → {result}")

    return "\n".join(lines)


# =============================================================================
#  ФОРМАТИРОВАНИЕ ДЛЯ ПОКАЗА
# =============================================================================

def format_history(project_path: Path, limit: int = DEFAULT_RECENT_LIMIT) -> str:
    """
    Формирует красивый текст истории для показа пользователю.

    Пример:
        История проекта calculator (Python):

        [16.10 09:15] добавь возведение в степень — успех (6.1 сек)
        [15.10 14:32] напиши простой калькулятор — успех (8.3 сек)
    """
    history = load_history(project_path)
    tasks = get_recent(project_path, limit=limit)

    if not tasks:
        return f"Проект {project_path.name}: задач пока не было."

    language = history.get("language", "")
    header = f"История проекта {project_path.name}"
    if language:
        header += f" ({language})"
    header += ":"

    lines = [header, ""]

    for task in tasks:
        date_full = task.get("date", "")
        try:
            dt = datetime.fromisoformat(date_full)
            date_str = dt.strftime("%d.%m %H:%M")
        except (ValueError, TypeError):
            date_str = date_full[:16]

        query = task.get("query", "—").strip()
        result = task.get("result", "unknown")

        if result == "success":
            result_str = "успех"
        elif result == "failure":
            result_str = "ошибка"
        else:
            result_str = result

        rt = task.get("reasoning_time")
        time_str = f" ({rt} сек)" if rt else ""

        lines.append(f"[{date_str}] {query} — {result_str}{time_str}")

    return "\n".join(lines)


# =============================================================================
#  ЭКСПОРТ
# =============================================================================

__all__ = [
    "PROJECT_META_DIR",
    "HISTORY_FILE",
    "DEFAULT_RECENT_LIMIT",
    "get_history_path",
    "load_history",
    "save_history",
    "add_task",
    "update_language",
    "get_tasks",
    "get_recent",
    "get_summary",
    "get_context_for_llm",
    "format_history",
]
