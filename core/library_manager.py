# =============================================================================
#  Codermuks in Termux — управление библиотеками v1.3.0
# =============================================================================
#  Что делает:
#    • проверяет, установлена ли библиотека;
#    • пытается поставить через pip;
#    • если pip не смог — пробует pkg (для системных пакетов Termux);
#    • если и это не вышло — пробует pip install git+<github_url>;
#    • если всё упало — сообщает пользователю, что нужно поставить вручную;
#    • записывает requirements.txt в проект.
# =============================================================================

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

from core.events import emit, LEVEL_INFO, LEVEL_SUCCESS, LEVEL_ERROR


# Системные пакеты Termux, которых нет в pip, но есть в pkg.
PKG_FALLBACK = {
    "pygame": "python-pygame",
    "sqlite3": "sqlite",
    "tkinter": "python-tkinter",
    "lua": "lua54",
    "gcc": "clang",
    "zlib": "zlib",
    "openssl": "openssl",
    "PIL": "python-pillow",
    "cv2": "opencv-python",
}

# Репозитории на GitHub — для установки напрямую, если нет в PyPI.
GITHUB_FALLBACK = {
    "pygame": "https://github.com/pygame/pygame.git",
    "numpy": "https://github.com/numpy/numpy.git",
    "pandas": "https://github.com/pandas-dev/pandas.git",
    "requests": "https://github.com/psf/requests.git",
    "flask": "https://github.com/pallets/flask.git",
    "fastapi": "https://github.com/tiangolo/fastapi.git",
    "aiohttp": "https://github.com/aio-libs/aiohttp.git",
    "Pillow": "https://github.com/python-pillow/Pillow.git",
    "beautifulsoup4": "https://github.com/wention/BeautifulSoup4.git",
    "scipy": "https://github.com/scipy/scipy.git",
    "matplotlib": "https://github.com/matplotlib/matplotlib.git",
}


class LibraryManager:
    """Проверка и установка Python-библиотек."""

    @staticmethod
    def check(name: str) -> bool:
        if not name:
            return False
        try:
            return importlib.util.find_spec(name) is not None
        except (ImportError, ValueError):
            return False

    @staticmethod
    def _run(cmd: list[str], timeout: int) -> bool:
        try:
            r = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=timeout, stdin=subprocess.DEVNULL,
            )
            return r.returncode == 0
        except Exception:
            return False

    def _pip_install(self, target: str, timeout: int = 180) -> bool:
        return self._run(
            [sys.executable, "-m", "pip", "install", "--no-input", target],
            timeout,
        )

    def _pkg_install(self, pkg_name: str, timeout: int = 180) -> bool:
        return self._run(["pkg", "install", "-y", pkg_name], timeout)

    def ensure(self, name: str, github_url: str = "") -> tuple[str, str, str]:
        """
        Гарантирует, что библиотека доступна.

        Возвращает (status, message, method):
            ("ok", "...", "")              — уже стоит
            ("installed", "...", "pip")    — поставили через pip
            ("installed", "...", "pkg")    — поставили через pkg
            ("installed", "...", "github") — поставили с GitHub
            ("failed", name, "")           — не удалось
        """
        if not name:
            return ("ok", "", "")

        if self.check(name):
            return ("ok", f"{name} уже установлена", "")

        # 1. pip
        emit("library.installing", {"name": name, "method": "pip"}, level=LEVEL_INFO)
        if self._pip_install(name):
            emit("library.installed", {"name": name, "method": "pip"}, level=LEVEL_SUCCESS)
            return ("installed", f"{name} установлена через pip", "pip")

        # 2. pkg (для системных пакетов Termux)
        pkg_name = PKG_FALLBACK.get(name, "")
        if pkg_name:
            emit("library.installing", {"name": name, "method": "pkg"}, level=LEVEL_INFO)
            if self._pkg_install(pkg_name):
                emit("library.installed", {"name": name, "method": "pkg"}, level=LEVEL_SUCCESS)
                return ("installed", f"{name} установлена через pkg", "pkg")

        # 3. GitHub
        url = github_url or GITHUB_FALLBACK.get(name, "")
        if url:
            emit("library.installing", {"name": name, "method": "github"}, level=LEVEL_INFO)
            if self._pip_install(f"git+{url}", timeout=300):
                emit("library.installed", {"name": name, "method": "github"}, level=LEVEL_SUCCESS)
                return ("installed", f"{name} установлена с GitHub", "github")

        # 4. Провал
        emit("library.failed", {"name": name}, level=LEVEL_ERROR)
        return ("failed", name, "")

    def ensure_all(self, requirements: list) -> dict:
        """
        Проверяет и ставит все библиотеки из плана.

        Возвращает:
            {
                "ok": bool,
                "installed": [{"name": ..., "method": ...}, ...],
                "missing": ["name", ...],
                "already": ["name", ...],
            }
        """
        result = {"ok": True, "installed": [], "missing": [], "already": []}
        if not requirements:
            return result

        for req in requirements:
            if isinstance(req, dict):
                name = str(req.get("name", "")).strip()
                url = str(req.get("github_url", "")).strip()
            else:
                name = str(req).strip()
                url = ""

            if not name:
                continue

            status, _msg, method = self.ensure(name, url)
            if status == "installed":
                result["installed"].append({"name": name, "method": method})
            elif status == "failed":
                result["missing"].append(name)
            else:
                result["already"].append(name)

        result["ok"] = len(result["missing"]) == 0
        return result

    # -------------------------------------------------------------------------
    #  requirements.txt
    # -------------------------------------------------------------------------

    @staticmethod
    def write_requirements(
        project_path: Path,
        requirements: list,
        installed: list | None = None,
    ) -> Path | None:
        """
        Записывает requirements.txt в проект.

        Аргументы:
            project_path — путь к папке проекта.
            requirements — список требований из плана.
            installed    — список уже установленных (для пометки в комментарии).

        Возвращает путь к файлу или None, если требований нет.
        """
        if not requirements:
            return None

        installed_names = set()
        if installed:
            for item in installed:
                if isinstance(item, dict):
                    installed_names.add(item.get("name", ""))
                else:
                    installed_names.add(str(item))

        lines = ["# Автоматически сгенерировано Codermuks v1.3.0", ""]

        for req in requirements:
            if isinstance(req, dict):
                name = str(req.get("name", "")).strip()
                url = str(req.get("github_url", "")).strip()
            else:
                name = str(req).strip()
                url = ""

            if not name:
                continue

            if url:
                lines.append(f"git+{url}")
            else:
                lines.append(name)

        content = "\n".join(lines) + "\n"
        target = project_path / "requirements.txt"
        try:
            target.write_text(content, encoding="utf-8")
            return target
        except OSError:
            return None


__all__ = ["LibraryManager", "PKG_FALLBACK", "GITHUB_FALLBACK"]
