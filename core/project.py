# =============================================================================
#  Codermuks in Termux — класс Project v1.2.0
# =============================================================================
#  Что это:
#    Высокоуровневая обёртка вокруг одной папки проекта в workspace.
#    Объединяет работу с файлами, историей и метаданными.
#
#  Что умеет:
#    • создавать и открывать проекты;
#    • читать, писать, удалять и искать файлы внутри проекта;
#    • вести историю задач;
#    • автоматически выбирать «релевантные» файлы по запросу;
#    • хранить и обновлять метаданные (язык, даты).
#
#  Пример:
#      project = Project.create("snake game", language="python")
#      project.write_file("snake.py", code)
#      project.add_task("напиши змейку", "success", ...)
#      project.set_language("python")
# =============================================================================

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from core import history as history_mod
from core import workspace as ws_mod
from utils.naming import find_similar


# =============================================================================
#  КЛАСС
# =============================================================================

class Project:
    """
    Один проект в workspace.

    Создаётся через classmethod'ы:
        • Project.create(name, language)  — новый проект;
        • Project.open(name)              — открыть существующий;
        • Project.find(query)             — найти похожий.
    """

    def __init__(self, path: Path) -> None:
        """
        Обычно не вызывается напрямую — используй Project.create/open/find.
        """
        self._path = path.resolve()

    # -------------------------------------------------------------------------
    #  СВОЙСТВА
    # -------------------------------------------------------------------------

    @property
    def path(self) -> Path:
        """Путь к папке проекта."""
        return self._path

    @property
    def name(self) -> str:
        """Имя проекта (имя папки)."""
        return self._path.name

    @property
    def meta_dir(self) -> Path:
        """Путь к .codermuks/ внутри проекта."""
        return self._path / ws_mod.PROJECT_META_DIR

    @property
    def metadata(self) -> dict[str, Any]:
        """Читает и возвращает metadata.json."""
        return ws_mod.read_metadata(self._path)

    @property
    def language(self) -> str:
        """Язык проекта (из metadata.json, или пустая строка)."""
        return self.metadata.get("language", "")

    @property
    def exists(self) -> bool:
        """Существует ли папка проекта."""
        return self._path.is_dir()

    def __repr__(self) -> str:
        return f"<Project {self.name!r} path={self._path}>"

    # -------------------------------------------------------------------------
    #  СОЗДАНИЕ И ОТКРЫТИЕ
    # -------------------------------------------------------------------------

    @classmethod
    def create(cls, raw_name: str, language: str = "") -> "Project":
        """
        Создаёт новый проект в workspace.

        Имя нормализуется через slugify, при коллизии добавляется -2, -3.
        """
        path = ws_mod.create_project(raw_name, language)
        project = cls(path)

        # Сразу создаём пустую историю.
        history_mod.save_history(project.path, history_mod.load_history(project.path))

        return project

    @classmethod
    def open(cls, name: str) -> "Project | None":
        """
        Открывает существующий проект по имени.

        Возвращает None, если проекта нет.
        """
        if not ws_mod.project_exists(name):
            return None
        return cls(ws_mod.get_workspace_dir() / name)

    @classmethod
    def find(cls, query: str, threshold: float = 0.6) -> "Project | None":
        """
        Ищет существующий проект, похожий на запрос пользователя.

        Использует fuzzy-сравнение имён через utils.naming.find_similar.

        Пример:
            Project.find("дополни калькулятор")
            → Project(name='calculator')
        """
        names = ws_mod.get_project_names()
        if not names:
            return None

        matches = find_similar(query, names, threshold=threshold)
        if not matches:
            return None

        best_name, _score = matches[0]
        return cls.open(best_name)

    # -------------------------------------------------------------------------
    #  ФАЙЛЫ
    # -------------------------------------------------------------------------

    def _safe_path(self, rel_path: str) -> Path:
        """
        Превращает относительный путь в абсолютный и проверяет,
        что он внутри проекта (защита от ../).

        Исключения:
            ValueError — если путь выходит за пределы проекта.
        """
        if not rel_path:
            raise ValueError("Пустой путь к файлу.")

        # Абсолютный путь внутри проекта.
        target = (self._path / rel_path).resolve()

        # Проверяем, что путь внутри корня проекта.
        try:
            target.relative_to(self._path)
        except ValueError:
            raise ValueError(
                f"Путь '{rel_path}' выходит за пределы проекта '{self.name}'."
            )

        return target

    def write_file(self, rel_path: str, content: str) -> Path:
        """
        Записывает файл в проект.

        Создаёт родительские директории при необходимости.
        Возвращает абсолютный путь к записанному файлу.
        """
        target = self._safe_path(rel_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def read_file(self, rel_path: str) -> str:
        """
        Читает файл проекта.

        Возвращает содержимое или пустую строку, если файла нет.
        """
        target = self._safe_path(rel_path)
        if not target.exists() or not target.is_file():
            return ""
        try:
            return target.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return ""

    def delete_file(self, rel_path: str) -> bool:
        """
        Удаляет файл проекта.

        Возвращает True, если файл удалён, False — если его не было.
        """
        target = self._safe_path(rel_path)
        if not target.exists():
            return False
        try:
            target.unlink()
            return True
        except OSError:
            return False

    def file_exists(self, rel_path: str) -> bool:
        """Проверяет существование файла в проекте."""
        target = self._safe_path(rel_path)
        return target.is_file()

    def list_files(self, include_hidden: bool = False) -> list[str]:
        """
        Возвращает список файлов проекта (относительные пути).

        Скрытые файлы (.codermuks/ и т.п.) по умолчанию не включаются.
        """
        if not self._path.exists():
            return []

        result: list[str] = []
        for entry in self._path.rglob("*"):
            if not entry.is_file():
                continue
            rel = entry.relative_to(self._path)
            # Пропускаем служебные и скрытые.
            if not include_hidden:
                if any(part.startswith(".") for part in rel.parts):
                    continue
            result.append(str(rel).replace("\\", "/"))

        return sorted(result)

    def read_relevant_files(
        self,
        query: str,
        max_files: int = 5,
        max_chars_per_file: int = 4000,
    ) -> dict[str, str]:
        """
        Читает файлы, релевантные запросу пользователя.

        Логика:
            1. Берём список файлов проекта.
            2. Ищем в запросе упоминания файлов (по имени без расширения).
            3. Если ничего не нашли — возвращаем самые свежие файлы.
            4. Обрезаем слишком большие файлы.

        Возвращает:
            { "snake.py": "код...", "README.md": "..." }
        """
        all_files = self.list_files(include_hidden=False)
        if not all_files:
            return {}

        query_lower = query.lower()

        # Файлы, чьё имя встречается в запросе.
        matched: list[str] = []
        for f in all_files:
            stem = Path(f).stem.lower()
            if stem and stem in query_lower:
                matched.append(f)

        # Если ничего явно не нашли — берём последние изменённые файлы.
        if not matched:
            files_with_mtime = []
            for f in all_files:
                full = self._path / f
                try:
                    mtime = full.stat().st_mtime
                except OSError:
                    mtime = 0
                files_with_mtime.append((f, mtime))
            files_with_mtime.sort(key=lambda x: x[1], reverse=True)
            matched = [f for f, _ in files_with_mtime[:max_files]]

        # Ограничиваем количество.
        matched = matched[:max_files]

        # Читаем.
        result: dict[str, str] = {}
        for rel in matched:
            content = self.read_file(rel)
            if content:
                if len(content) > max_chars_per_file:
                    content = content[:max_chars_per_file] + "\n... (truncated)"
                result[rel] = content

        return result

    # -------------------------------------------------------------------------
    #  ИСТОРИЯ
    # -------------------------------------------------------------------------

    def add_task(
        self,
        query: str,
        result: str,
        *,
        provider: str = "",
        model: str = "",
        reasoning_time: float = 0.0,
        files_created: list[str] | None = None,
        files_modified: list[str] | None = None,
    ) -> None:
        """Добавляет запись о задаче в историю проекта."""
        history_mod.add_task(
            self._path,
            query,
            result,
            provider=provider,
            model=model,
            reasoning_time=reasoning_time,
            files_created=files_created,
            files_modified=files_modified,
        )

    def get_recent_tasks(self, limit: int = 10) -> list[dict[str, Any]]:
        """Возвращает последние задачи проекта."""
        return history_mod.get_recent(self._path, limit=limit)

    def get_history(self) -> dict[str, Any]:
        """Возвращает полную историю проекта."""
        return history_mod.load_history(self._path)

    def get_context_for_llm(self, limit: int = 5) -> str:
        """
        Формирует контекст о предыдущих задачах — для передачи
        в промпт планировщику.
        """
        return history_mod.get_context_for_llm(self._path, limit=limit)

    def format_history(self, limit: int = 10) -> str:
        """Форматирует историю для показа пользователю."""
        return history_mod.format_history(self._path, limit=limit)

    # -------------------------------------------------------------------------
    #  МЕТАДАННЫЕ
    # -------------------------------------------------------------------------

    def set_language(self, language: str) -> None:
        """Устанавливает язык проекта (в metadata.json и history.json)."""
        ws_mod.update_metadata(self._path, language=language)
        history_mod.update_language(self._path, language)

    def update_meta(self, **fields: Any) -> None:
        """Обновляет произвольные поля metadata.json."""
        ws_mod.update_metadata(self._path, **fields)

    # -------------------------------------------------------------------------
    #  СВОДКА
    # -------------------------------------------------------------------------

    def summary(self) -> dict[str, Any]:
        """
        Возвращает краткую сводку по проекту.

        Пример:
            {
                "name": "calculator",
                "language": "python",
                "files_count": 3,
                "tasks_total": 5,
                "tasks_success": 4,
                "created_at": "2026-10-15T...",
            }
        """
        hist_summary = history_mod.get_summary(self._path)

        return {
            "name": self.name,
            "language": self.language,
            "files_count": len(self.list_files()),
            "tasks_total": hist_summary["total_tasks"],
            "tasks_success": hist_summary["success"],
            "created_at": self.metadata.get("created_at", ""),
        }

    def format_summary(self) -> str:
        """
        Красивая однострочная сводка для показа в списке.

        Пример:
            calculator (Python) — 3 файла, 5 задач, 2 успешные
        """
        s = self.summary()
        parts: list[str] = []

        name = s["name"]
        if s["language"]:
            name += f" ({s['language']})"
        parts.append(name)

        if s["files_count"]:
            parts.append(f"{s['files_count']} файл(ов)")

        if s["tasks_total"]:
            parts.append(
                f"{s['tasks_total']} задач, "
                f"{s['tasks_success']} успешных"
            )

        return " — ".join(parts)


# =============================================================================
#  ЭКСПОРТ
# =============================================================================

__all__ = ["Project"]
