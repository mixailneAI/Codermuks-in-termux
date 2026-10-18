# =============================================================================
#  Codermuks in Termux — пакет Roblox v1.4.0
# =============================================================================
#  Фасад для работы с Roblox Studio через MCP.
#
#  Автоматически подключается при импорте (если найден StudioMCP).
#  Простой API:
#      from core.roblox import is_available, call_tool, list_tools
#      if is_available():
#          result = call_tool("execute_luau", {"code": "print(1)"})
#
#  Если Roblox не найден — все функции просто возвращают None/False,
#  ничего не ломая.
# =============================================================================

from __future__ import annotations

from typing import Any

from core.mcp_client import (
    MCPClient,
    MCPError,
    get_client,
    is_connected,
    set_client,
)
from core.roblox.discovery import find_studio_mcp, list_all_candidates


# =============================================================================
#  СОСТОЯНИЕ
# =============================================================================

# Кэш доступных инструментов.
_tools_cache: list[dict[str, Any]] | None = None


# =============================================================================
#  ПОДКЛЮЧЕНИЕ
# =============================================================================

def ensure_connected(auto: bool = True) -> bool:
    """
    Убеждается, что MCP-клиент подключён.

    Аргументы:
        auto — если True, при отсутствии пути пытается найти StudioMCP.

    Возвращает:
        True, если подключено.
    """
    if is_connected():
        return True

    if not auto:
        return False

    path = find_studio_mcp()
    if not path:
        return False

    try:
        client = MCPClient(command=path)
        client.connect(timeout=20)
        set_client(client)
        return True
    except (MCPError, OSError, Exception):
        return False


def disconnect() -> None:
    """Отключает текущий MCP-клиент."""
    global _tools_cache
    client = get_client()
    if client is not None:
        try:
            client.disconnect()
        except Exception:
            pass
    set_client(None)
    _tools_cache = None


# =============================================================================
#  ПРОВЕРКИ
# =============================================================================

def is_available() -> bool:
    """Проверяет, доступен ли Roblox через MCP."""
    return is_connected()


def get_server_info() -> dict[str, Any]:
    """Возвращает информацию о MCP-сервере."""
    client = get_client()
    if client is None:
        return {}
    return client.server_info


# =============================================================================
#  ИНСТРУМЕНТЫ
# =============================================================================

def list_tools(use_cache: bool = True) -> list[dict[str, Any]]:
    """
    Возвращает список инструментов MCP-сервера Roblox.

    Если не подключено — пустой список.
    """
    global _tools_cache

    if use_cache and _tools_cache is not None:
        return _tools_cache

    client = get_client()
    if client is None or not client.is_connected:
        return []

    try:
        tools = client.list_tools()
        _tools_cache = tools
        return tools
    except MCPError:
        return []


def get_tool_names() -> list[str]:
    """Возвращает только имена инструментов."""
    return [t.get("name", "") for t in list_tools() if t.get("name")]


def call_tool(
    name: str,
    arguments: dict[str, Any] | None = None,
    timeout: float = 60.0,
) -> dict[str, Any] | None:
    """
    Вызывает MCP-инструмент Roblox.

    Возвращает:
        dict с результатом (содержит 'content') или None при ошибке.
    """
    client = get_client()
    if client is None or not client.is_connected:
        return None

    try:
        return client.call_tool(name, arguments, timeout=timeout)
    except MCPError as exc:
        return {
            "isError": True,
            "error": str(exc),
            "content": [{"type": "text", "text": str(exc)}],
        }


def extract_text(result: dict[str, Any] | None) -> str:
    """
    Извлекает текстовый ответ из результата MCP.

    MCP возвращает content — список блоков вида
    [{"type": "text", "text": "..."}, ...].
    """
    if not result:
        return ""

    if "error" in result and result.get("isError"):
        return str(result.get("error", ""))

    content = result.get("content", [])
    if not isinstance(content, list):
        return ""

    parts: list[str] = []
    for block in content:
        if isinstance(block, dict):
            if block.get("type") == "text":
                parts.append(str(block.get("text", "")))
            elif "text" in block:
                parts.append(str(block["text"]))

    return "\n".join(parts)


# =============================================================================
#  АВТО-ПОДКЛЮЧЕНИЕ ПРИ ИМПОРТЕ
# =============================================================================

def _auto_connect_on_import() -> None:
    """
    Пробует подключиться при импорте.

    Тихо — если Roblox нет, ничего не выводит и не падает.
    """
    try:
        ensure_connected(auto=True)
    except Exception:
        pass


# Пробуем, но не блокируем импорт при неудаче.
_auto_connect_on_import()


# =============================================================================
#  ЭКСПОРТ
# =============================================================================

__all__ = [
    "ensure_connected",
    "disconnect",
    "is_available",
    "get_server_info",
    "list_tools",
    "get_tool_names",
    "call_tool",
    "extract_text",
    "find_studio_mcp",
    "list_all_candidates",
    "MCPError",
]
