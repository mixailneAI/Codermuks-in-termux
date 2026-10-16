# =============================================================================
#  Codermuks in Termux — экспорт проектов в ZIP v1.3.0
# =============================================================================

from __future__ import annotations

import zipfile
from datetime import datetime
from pathlib import Path

from core.project import Project


def _default_export_dir() -> Path:
    """Куда сохранять ZIP по умолчанию — общая память телефона."""
    shared = Path.home() / "storage" / "shared"
    if shared.exists():
        return shared
    return Path.home()


def export_project(project_name: str, output_path: Path | None = None) -> Path | None:
    """
    Экспортирует проект в ZIP-архив.

    Аргументы:
        project_name — имя проекта.
        output_path  — куда сохранить (по умолчанию ~/storage/shared/<name>.zip).

    Возвращает путь к созданному файлу или None при ошибке.
    """
    proj = Project.open(project_name)
    if proj is None or not proj.exists:
        return None

    if output_path is None:
        date = datetime.now().strftime("%Y-%m-%d")
        output_path = _default_export_dir() / f"{project_name}-{date}.zip"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in proj.path.rglob("*"):
                if not file_path.is_file():
                    continue
                # Пропускаем служебные .codermuks/ и __pycache__.
                rel = file_path.relative_to(proj.path)
                if any(part.startswith(".") and part != ".codermuks"
                       for part in rel.parts):
                    continue
                if "__pycache__" in rel.parts:
                    continue
                if file_path.suffix == ".pyc":
                    continue
                zf.write(file_path, arcname=str(rel))
        return output_path
    except (OSError, zipfile.BadZipFile):
        return None


def export_info(project_name: str) -> dict:
    """Возвращает инфо о проекте перед экспортом (для UI)."""
    proj = Project.open(project_name)
    if proj is None:
        return {}

    files = proj.list_files(include_hidden=False)
    total_size = 0
    for rel in files:
        try:
            total_size += (proj.path / rel).stat().st_size
        except OSError:
            pass

    return {
        "name": project_name,
        "files_count": len(files),
        "total_size": total_size,
        "path": proj.path,
    }


__all__ = ["export_project", "export_info"]
