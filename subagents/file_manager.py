# =============================================================================
#  Codermuks in Termux — субагент файловый менеджер
# =============================================================================
#  Задача файлового менеджера — работать с файлами проекта:
#    • читать содержимое файлов;
#    • создавать новые файлы;
#    • перезаписывать существующие;
#    • применять патчи (замена фрагмента);
#    • удалять файлы;
#    • перечислять содержимое директории.
#
#  Все операции ограничены рабочей директорией (по умолчанию —
#  текущая директория пользователя), чтобы агент не мог случайно
#  изменить что-то в системных папках.
# =============================================================================

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from subagents.base import BaseSubagent


# =============================================================================
#  СУБАГЕНТ
# =============================================================================

class FileManagerSubagent(BaseSubagent):
    """Субагент, который безопасно управляет файлами проекта."""

    name = "file_manager"
    description = "Читает, создаёт, изменяет и удаляет файлы проекта."

    # -------------------------------------------------------------------------
    #  Публичный интерфейс
    # -------------------------------------------------------------------------

    def run(self, task: str, **kwargs: Any) -> str:
        """
        Универсальный метод запуска.

        Поддерживает команды через kwargs:
            action="read"   — прочитать файл (path)
            action="write"  — записать файл (path, content)
            action="patch"  — заменить фрагмент (path, old, new)
            action="delete" — удалить файл (path)
            action="list"   — список файлов (path)
            action="mkdir"  — создать директорию (path)
            action="exists" — проверить существование (path)

        Возвращает строку-отчёт о результате.
        """
        action = kwargs.get("action", "").lower()

        handlers = {
            "read": self.read_file,
            "write": self.write_file,
            "patch": self.patch_file,
            "delete": self.delete_file,
            "list": self.list_dir,
            "mkdir": self.make_dir,
            "exists": self.file_exists,
        }

        if action not in handlers:
            available = ", ".join(sorted(handlers.keys()))
            return (
                f"Неизвестное действие '{action}'. "
                f"Доступные действия: {available}."
            )

        try:
            return handlers[action](**kwargs)
        except Exception as exc:
            self.log(f"Действие '{action}' не удалось: {exc}")
            return f"Ошибка: {exc}"

    # -------------------------------------------------------------------------
    #  Работа с путями
    # -------------------------------------------------------------------------

    def _resolve(self, path: str | None, base: str | None = None) -> Path:
        """
        Превращает строку пути в абсолютный Path и проверяет,
        что он находится внутри разрешённой рабочей директории.

        Если base передан — используется как корень. Иначе — берётся
        текущая рабочая директория процесса.

        Исключения:
            ValueError — если путь пытается выйти за пределы рабочей директории.
        """
        if not path:
            raise ValueError("Пустой путь.")

        root = Path(base).expanduser().resolve() if base else Path.cwd().resolve()
        target = (root / path).expanduser().resolve() if not Path(path).is_absolute() else Path(path).resolve()

        # Проверяем, что цель внутри корня.
        try:
            target.relative_to(root)
        except ValueError:
            raise ValueError(
                f"Путь '{path}' выходит за пределы рабочей директории '{root}'."
            )

        return target

    # -------------------------------------------------------------------------
    #  Действия
    # -------------------------------------------------------------------------

    def read_file(self, **kwargs: Any) -> str:
        """
        Читает файл и возвращает его содержимое.

        Параметры:
            path — путь к файлу (обязательно)
            base — корневая директория (опционально)
        """
        target = self._resolve(kwargs.get("path"), kwargs.get("base"))

        if not target.exists():
            return f"Файл не найден: {target}"
        if not target.is_file():
            return f"Это не файл: {target}"

        try:
            content = target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return f"Файл '{target}' не является текстовым."

        self.log(f"Прочитан файл {target} ({len(content)} символов).")
        return content

    def write_file(self, **kwargs: Any) -> str:
        """
        Записывает содержимое в файл. Создаёт директории по пути при
        необходимости. Если файл существует — перезаписывает.

        Параметры:
            path    — путь к файлу (обязательно)
            content — содержимое (обязательно)
            base    — корневая директория (опционально)
        """
        target = self._resolve(kwargs.get("path"), kwargs.get("base"))
        content = kwargs.get("content", "")
        if content is None:
            content = ""

        # Создаём родительские директории.
        target.parent.mkdir(parents=True, exist_ok=True)

        target.write_text(str(content), encoding="utf-8")
        self.log(f"Записан файл {target} ({len(str(content))} символов).")
        return f"Файл записан: {target}"

    def patch_file(self, **kwargs: Any) -> str:
        """
        Заменяет один фрагмент в файле на другой.

        Параметры:
            path — путь к файлу (обязательно)
            old  — заменяемый фрагмент (обязательно)
            new  — новый фрагмент (обязательно)
            base — корневая директория (опционально)

        Заменяется первое вхождение. Если old не найден — ошибка.
        """
        target = self._resolve(kwargs.get("path"), kwargs.get("base"))
        old = kwargs.get("old", "")
        new = kwargs.get("new", "")

        if not old:
            return "Не указан фрагмент для замены (old)."
        if not target.exists():
            return f"Файл не найден: {target}"

        content = target.read_text(encoding="utf-8")
        if old not in content:
            return f"Фрагмент для замены не найден в файле: {target}"

        updated = content.replace(old, str(new), 1)
        target.write_text(updated, encoding="utf-8")
        self.log(f"Патч применён к {target}.")
        return f"Патч применён: {target}"

    def delete_file(self, **kwargs: Any) -> str:
        """
        Удаляет файл или директорию.

        Параметры:
            path — путь к цели (обязательно)
            base — корневая директория (опционально)
        """
        target = self._resolve(kwargs.get("path"), kwargs.get("base"))

        if not target.exists():
            return f"Не найдено: {target}"

        if target.is_dir():
            shutil.rmtree(target)
            self.log(f"Удалена директория {target}.")
            return f"Директория удалена: {target}"

        target.unlink()
        self.log(f"Удалён файл {target}.")
        return f"Файл удалён: {target}"

    def list_dir(self, **kwargs: Any) -> str:
        """
        Возвращает список файлов и директорий.

        Параметры:
            path — директория (опционально, по умолчанию текущая)
            base — корневая директория (опционально)
        """
        rel_path = kwargs.get("path") or "."
        target = self._resolve(rel_path, kwargs.get("base"))

        if not target.exists():
            return f"Директория не найдена: {target}"
        if not target.is_dir():
            return f"Это не директория: {target}"

        entries = sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        lines: list[str] = []
        for entry in entries:
            if entry.is_dir():
                lines.append(f"📁 {entry.name}/")
            else:
                size = entry.stat().st_size
                lines.append(f"📄 {entry.name} ({size} байт)")

        if not lines:
            return f"Директория пуста: {target}"

        header = f"Содержимое {target}:"
        return header + "\n" + "\n".join(lines)

    def make_dir(self, **kwargs: Any) -> str:
        """
        Создаёт директорию (вместе с родительскими).

        Параметры:
            path — путь к директории (обязательно)
            base — корневая директория (опционально)
        """
        target = self._resolve(kwargs.get("path"), kwargs.get("base"))
        target.mkdir(parents=True, exist_ok=True)
        self.log(f"Создана директория {target}.")
        return f"Директория создана: {target}"

    def file_exists(self, **kwargs: Any) -> str:
        """
        Проверяет существование файла или директории.

        Параметры:
            path — путь (обязательно)
            base — корневая директория (опционально)
        """
        target = self._resolve(kwargs.get("path"), kwargs.get("base"))

        if not target.exists():
            return "нет"
        if target.is_dir():
            return "директория"
        if target.is_file():
            return "файл"
        return "существует"