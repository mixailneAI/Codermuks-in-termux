# =============================================================================
#  Codermuks in Termux — авто-обнаружение StudioMCP v1.4.0
# =============================================================================
#  Ищет исполняемый файл StudioMCP (MCP-сервер Roblox Studio)
#  в стандартных местах установки Roblox.
#
#  На Termux/Android ничего не найдёт — это нормально.
#  На Windows/Mac/Linux находит и возвращает путь.
# =============================================================================

from __future__ import annotations

import json
import os
import platform
import shutil
from pathlib import Path


# Где хранится сохранённый путь (если пользователь указал вручную).
ROBLOX_CONFIG_FILE = Path.home() / ".codermuks" / "roblox.json"


# =============================================================================
#  ПОИСК ПО ОС
# =============================================================================

def _find_windows() -> list[str]:
    """Ищет StudioMCP на Windows."""
    candidates: list[str] = []
    local = os.environ.get("LOCALAPPDATA", "")
    appdata = os.environ.get("APPDATA", "")
    program_files = os.environ.get("PROGRAMFILES", "C:\\Program Files")
    program_files_x86 = os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)")

    # Roblox Studio кладёт версии в %LOCALAPPDATA%\Roblox\Versions\<version>\
    if local:
        versions_dir = Path(local) / "Roblox" / "Versions"
        if versions_dir.is_dir():
            for version_dir in versions_dir.iterdir():
                for name in ("StudioMCP.exe", "StudioMCP"):
                    candidate = version_dir / name
                    if candidate.is_file():
                        candidates.append(str(candidate))
                # StudioMCP может лежать в подпапке
                for sub in version_dir.rglob("StudioMCP.exe"):
                    candidates.append(str(sub))

    # Стандартные пути установки
    for base in (program_files, program_files_x86, appdata):
        if not base:
            continue
        for sub in ("Roblox", "Roblox Studio"):
            path = Path(base) / sub
            if path.is_dir():
                for exe in path.rglob("StudioMCP.exe"):
                    candidates.append(str(exe))

    # Через PATH
    which = shutil.which("StudioMCP")
    if which:
        candidates.append(which)

    return candidates


def _find_macos() -> list[str]:
    """Ищет StudioMCP на macOS."""
    candidates: list[str] = []

    app_paths = [
        "/Applications/RobloxStudio.app",
        str(Path.home() / "Applications" / "RobloxStudio.app"),
    ]
    for app in app_paths:
        app_path = Path(app)
        if app_path.is_dir():
            for exe in app_path.rglob("StudioMCP"):
                candidates.append(str(exe))

    # Через PATH
    which = shutil.which("StudioMCP")
    if which:
        candidates.append(which)

    return candidates


def _find_linux() -> list[str]:
    """Ищет StudioMCP на Linux (обычно через Wine или нативный)."""
    candidates: list[str] = []

    # Нативный бинарь в PATH
    which = shutil.which("StudioMCP")
    if which:
        candidates.append(which)

    # Через Wine: путь имитирует Windows
    wine_prefix = os.environ.get("WINEPREFIX")
    if wine_prefix:
        wine_local = Path(wine_prefix) / "drive_c" / "users"
        if wine_local.is_dir():
            for user_dir in wine_local.iterdir():
                versions = user_dir / "AppData" / "Local" / "Roblox" / "Versions"
                if versions.is_dir():
                    for exe in versions.rglob("StudioMCP.exe"):
                        candidates.append(str(exe))

    return candidates


def _find_all() -> list[str]:
    """Возвращает все найденные пути для текущей ОС."""
    system = platform.system().lower()
    if system == "windows":
        return _find_windows()
    if system == "darwin":
        return _find_macos()
    return _find_linux()


# =============================================================================
#  СОХРАНЁННЫЙ ПУТЬ
# =============================================================================

def load_saved_path() -> str:
    """Читает сохранённый путь из ~/.codermuks/roblox.json."""
    if not ROBLOX_CONFIG_FILE.exists():
        return ""
    try:
        data = json.loads(ROBLOX_CONFIG_FILE.read_text(encoding="utf-8"))
        return str(data.get("studio_mcp_path", "")).strip()
    except (json.JSONDecodeError, OSError):
        return ""


def save_path(path: str) -> None:
    """Сохраняет путь к StudioMCP."""
    ROBLOX_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    data: dict = {}
    if ROBLOX_CONFIG_FILE.exists():
        try:
            data = json.loads(ROBLOX_CONFIG_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    data["studio_mcp_path"] = path
    ROBLOX_CONFIG_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def clear_saved_path() -> None:
    """Удаляет сохранённый путь."""
    if ROBLOX_CONFIG_FILE.exists():
        try:
            ROBLOX_CONFIG_FILE.unlink()
        except OSError:
            pass


# =============================================================================
#  ГЛАВНАЯ ФУНКЦИЯ
# =============================================================================

def find_studio_mcp() -> str:
    """
    Возвращает путь к StudioMCP или пустую строку.

    Порядок поиска:
        1. Сохранённый путь (~/.codermuks/roblox.json).
        2. Авто-обнаружение по стандартным местам ОС.

    Если нашёл в процессе обнаружения — сохраняет в конфиг.
    """
    # 1. Уже сохранён?
    saved = load_saved_path()
    if saved and Path(saved).is_file():
        return saved

    # 2. Авто-обнаружение.
    found = _find_all()
    if found:
        # Берём первый найденный.
        path = found[0]
        save_path(path)
        return path

    return ""


def list_all_candidates() -> list[str]:
    """Возвращает все найденные пути (для отладки)."""
    return _find_all()


__all__ = [
    "ROBLOX_CONFIG_FILE",
    "find_studio_mcp",
    "list_all_candidates",
    "load_saved_path",
    "save_path",
    "clear_saved_path",
]
