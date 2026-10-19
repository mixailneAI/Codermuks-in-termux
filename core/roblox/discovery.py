# =============================================================================
#  Codermuks in Termux — авто-обнаружение и ручная настройка StudioMCP v1.4.0
# =============================================================================
#  Что изменилось:
#    • Добавлен метод save_manual_path() для ручного ввода.
#    • Улучшен поиск на Windows (ищет в %LOCALAPPDATA%).
#    • Если ничего не найдено — возвращает пустую строку.
# =============================================================================

from __future__ import annotations

import json
import os
import platform
import shutil
from pathlib import Path

ROBLOX_CONFIG_FILE = Path.home() / ".codermuks" / "roblox.json"


def _find_windows() -> list[str]:
    candidates: list[str] = []
    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        versions_dir = Path(local) / "Roblox" / "Versions"
        if versions_dir.is_dir():
            for version_dir in versions_dir.iterdir():
                for name in ("StudioMCP.exe", "StudioMCP"):
                    candidate = version_dir / name
                    if candidate.is_file():
                        candidates.append(str(candidate))
                for sub in version_dir.rglob("StudioMCP.exe"):
                    candidates.append(str(sub))
    which = shutil.which("StudioMCP")
    if which:
        candidates.append(which)
    return candidates


def _find_macos() -> list[str]:
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
    which = shutil.which("StudioMCP")
    if which:
        candidates.append(which)
    return candidates


def _find_linux() -> list[str]:
    candidates: list[str] = []
    which = shutil.which("StudioMCP")
    if which:
        candidates.append(which)
    return candidates


def _find_all() -> list[str]:
    system = platform.system().lower()
    if system == "windows":
        return _find_windows()
    if system == "darwin":
        return _find_macos()
    return _find_linux()


def load_saved_path() -> str:
    if not ROBLOX_CONFIG_FILE.exists():
        return ""
    try:
        data = json.loads(ROBLOX_CONFIG_FILE.read_text(encoding="utf-8"))
        return str(data.get("studio_mcp_path", "")).strip()
    except (json.JSONDecodeError, OSError):
        return ""


def save_path(path: str) -> None:
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


def save_manual_path(path: str) -> None:
    """Сохраняет путь, введённый пользователем вручную."""
    if path and Path(path).is_file():
        save_path(path)


def clear_saved_path() -> None:
    if ROBLOX_CONFIG_FILE.exists():
        try:
            ROBLOX_CONFIG_FILE.unlink()
        except OSError:
            pass


def find_studio_mcp_url() -> str:
    """Возвращает сохранённый URL удалённого MCP-сервера."""
    from core import config
    return config.get_roblox_mcp_url()


def find_studio_mcp() -> str:
    """Ищет MCP-сервер. Сначала сохранённый, потом авто-поиск."""
    saved = load_saved_path()
    if saved and Path(saved).is_file():
        return saved

    found = _find_all()
    if found:
        save_path(found[0])
        return found[0]

    return ""


def list_all_candidates() -> list[str]:
    return _find_all()


__all__ = [
    "ROBLOX_CONFIG_FILE",
    "find_studio_mcp",
    "list_all_candidates",
    "load_saved_path",
    "save_path",
    "save_manual_path",
    "clear_saved_path",
]
