# =============================================================================
#  Codermuks in Termux — управление workspace v1.4.0
# =============================================================================
#  Что делает этот модуль:
#    • создаёт и обслуживает ~/codermuks-workspace/;
#    • хранит список существующих проектов;
#    • создаёт новые проекты с правильными именами (без коллизий);
#    • перечисляет, ищет и удаляет проекты.
#
#  Структура workspace:
#      ~/codermuks-workspace/
#      ├── snake-game/
#      │   ├── snake.py
#      │   ├── README.md
#      │   └── .codermuks/
#      │       ├── metadata.json
#      │       └── history.json
#      └── calculator/
#          └── ...
# =============================================================================

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

from utils.naming import resolve_collision, slugify


# =============================================================================
#  КОНСТАНТЫ
# =============================================================================

# Имя корневой папки в домашней директории пользователя.
WORKSPACE_NAME = "codermuks-workspace"

# Имя скрытой папки внутри каждого проекта — там метаданные и история.
PROJECT_META_DIR = ".codermuks"

# Имя файла метаданных проекта.
METADATA_FILE = "metadata.json"


# =============================================================================
#  ПУТИ
# =============================================================================

def get_workspace_dir() -> Path:
    """
    Возвращает путь к корневой папке workspace.
    По умолчанию — ~/codermuks-workspace/.
    """
    return Path.home() / WORKSPACE_NAME


def ensure_workspace() -> Path:
    """
    Создаёт workspace, если его нет. Возвращает путь.
    """
    ws = get_workspace_dir()
    ws.mkdir(parents=True, exist_ok=True)
    return ws


# =============================================================================
#  СПИСОК ПРОЕКТОВ
# =============================================================================

def list_projects() -> list[dict]:
    """
    Возвращает список всех проектов в workspace.

    Каждый проект — словарь:
        {
            "name": "snake-game",
            "path": Path("..."),
            "language": "python",       # из metadata.json (если есть)
            "created_at": "2026-10-16T...",  # из metadata.json
            "modified_at": "2026-10-16T...",  # mtime папки
            "files_count": 3,
        }

    Сортировка — по дате последнего изменения (свежие сверху).
    """
    ws = ensure_workspace()
    projects: list[dict] = []

    for entry in ws.iterdir():
        if not entry.is_dir():
            continue
        if entry.name.startswith("."):
            continue

        meta = read_metadata(entry)
        files = [f for f in entry.rglob("*") if f.is_file()
                 and ".codermuks" not in f.parts]
        mtime = datetime.fromtimestamp(entry.stat().st_mtime).isoformat()

        projects.append({
            "name": entry.name,
            "path": entry,
            "language": meta.get("language", ""),
            "created_at": meta.get("created_at", mtime),
            "modified_at": mtime,
            "files_count": len(files),
        })

    projects.sort(key=lambda p: p["modified_at"], reverse=True)
    return projects


def get_project_names() -> list[str]:
    """Возвращает список имён всех проектов (для авто-дополнения)."""
    return [p["name"] for p in list_projects()]


def project_exists(name: str) -> bool:
    """Проверяет, есть ли проект с таким именем."""
    ws = get_workspace_dir()
    return (ws / name).is_dir()


# =============================================================================
#  СОЗДАНИЕ ПРОЕКТА
# =============================================================================

def create_project(raw_name: str, language: str = "") -> Path:
    """
    Создаёт новый проект в workspace.

    Аргументы:
        raw_name — имя проекта (может содержать пробелы, кириллицу).
        language — язык программирования (сохраняется в метаданные).

    Возвращает:
        Путь к созданной папке проекта.

    Логика:
        1. Нормализует имя через slugify().
        2. Проверяет коллизии и добавляет -2, -3, если нужно.
        3. Создаёт папку проекта и служебную папку .codermuks/.
        4. Создаёт metadata.json с базовой информацией.
    """
    ensure_workspace()

    # 1. Нормализуем имя.
    safe_name = slugify(raw_name)

    # 2. Разрешаем коллизии.
    existing = get_project_names()
    final_name = resolve_collision(safe_name, existing)

    # 3. Создаём папки.
    project_path = get_workspace_dir() / final_name
    project_path.mkdir(parents=True, exist_ok=True)
    (project_path / PROJECT_META_DIR).mkdir(exist_ok=True)

    # 4. Метаданные.
    metadata = {
        "name": final_name,
        "language": language,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "modified_at": datetime.now().isoformat(timespec="seconds"),
        "version": "1.4.0",
    }
    write_metadata(project_path, metadata)

    return project_path


# =============================================================================
#  УДАЛЕНИЕ ПРОЕКТА
# =============================================================================

def delete_project(name: str) -> bool:
    """
    Удаляет проект вместе с содержимым.

    Возвращает True, если удалил, False — если проекта нет.
    """
    if not project_exists(name):
        return False

    project_path = get_workspace_dir() / name

    # Защита от удаления системных папок.
    if name.startswith(".") or "/" in name or "\\" in name:
        return False

    shutil.rmtree(project_path, ignore_errors=True)
    return True


# =============================================================================
#  МЕТАДАННЫЕ ПРОЕКТА
# =============================================================================

def get_metadata_path(project_path: Path) -> Path:
    """Возвращает путь к metadata.json проекта."""
    return project_path / PROJECT_META_DIR / METADATA_FILE


def read_metadata(project_path: Path) -> dict:
    """
    Читает metadata.json проекта.

    Если файла нет или он повреждён — возвращает пустой словарь.
    """
    meta_path = get_metadata_path(project_path)
    if not meta_path.exists():
        return {}
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def write_metadata(project_path: Path, metadata: dict) -> None:
    """
    Записывает metadata.json проекта.

    Всегда обновляет поле modified_at.
    """
    metadata["modified_at"] = datetime.now().isoformat(timespec="seconds")
    meta_path = get_metadata_path(project_path)
    meta_path.parent.mkdir(exist_ok=True)
    meta_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def update_metadata(project_path: Path, **fields) -> None:
    """
    Обновляет отдельные поля metadata.json.

    Пример:
        update_metadata(project_path, language="python", last_task="add feature")
    """
    meta = read_metadata(project_path)
    meta.update(fields)
    write_metadata(project_path, meta)


# =============================================================================
#  ЭКСПОРТ
# =============================================================================

__all__ = [
    "WORKSPACE_NAME",
    "PROJECT_META_DIR",
    "METADATA_FILE",
    "get_workspace_dir",
    "ensure_workspace",
    "list_projects",
    "get_project_names",
    "project_exists",
    "create_project",
    "delete_project",
    "get_metadata_path",
    "read_metadata",
    "write_metadata",
    "update_metadata",
]
