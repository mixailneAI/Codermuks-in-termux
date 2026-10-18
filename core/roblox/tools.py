# =============================================================================
#  Codermuks in Termux — обёртки над MCP-инструментами Roblox v1.4.0
# =============================================================================
#  Каждая функция — это удобная обёртка над инструментом MCP-сервера
#  Roblox Studio. Внутри вызывает roblox.call_tool() и возвращает
#  человеко-читаемый результат.
#
#  Если Roblox недоступен — функции возвращают пустой результат
#  или явную ошибку, но НЕ падают.
# =============================================================================

from __future__ import annotations

from typing import Any

from core.roblox import (
    call_tool,
    extract_text,
    is_available,
)


# =============================================================================
#  ЧТЕНИЕ
# =============================================================================

def read_script(path: str) -> str:
    """
    Прочитать исходник скрипта по пути Roblox.

    Пример пути:
        "game.ServerScriptService.Main"
        "game.StarterPlayer.StarterPlayerScripts.Movement"
    """
    if not is_available() or not path:
        return ""

    result = call_tool("script_read", {"path": path})
    return extract_text(result)


def search_scripts(query: str, max_results: int = 20) -> str:
    """Поиск по содержимому всех скриптов в проекте."""
    if not is_available() or not query:
        return ""

    result = call_tool("script_grep", {
        "query": query,
        "max_results": max_results,
    })
    return extract_text(result)


def get_game_tree(max_depth: int = 4) -> str:
    """
    Получить иерархию объектов в DataModel.

    Возвращает текстовое дерево (Services → Objects → Children).
    """
    if not is_available():
        return ""

    result = call_tool("get_game_tree", {"max_depth": max_depth})
    return extract_text(result)


def get_console_output(lines: int = 50) -> str:
    """Прочитать последние N строк из Output в Studio."""
    if not is_available():
        return ""

    result = call_tool("get_console_output", {"lines": lines})
    return extract_text(result)


# =============================================================================
#  ЗАПИСЬ
# =============================================================================

def create_or_edit_script(
    path: str,
    source: str,
    script_type: str = "Script",
) -> str:
    """
    Создать или перезаписать скрипт.

    Аргументы:
        path        — полный путь в иерархии Roblox:
                      "game.ServerScriptService.Main"
        source      — содержимое скрипта (Luau).
        script_type — "Script" | "LocalScript" | "ModuleScript".

    Возвращает:
        Текст ответа MCP или пустую строку.
    """
    if not is_available() or not path:
        return ""

    result = call_tool("multi_edit", {
        "edits": [
            {
                "path": path,
                "source": source,
                "type": script_type,
            }
        ]
    })
    return extract_text(result)


def create_or_edit_scripts(edits: list[dict[str, Any]]) -> str:
    """
    Массовое создание/редактирование скриптов.

    Аргументы:
        edits — список словарей:
            [
                {"path": "game.X.Y", "source": "...", "type": "Script"},
                {"path": "game.X.Z", "source": "...", "type": "ModuleScript"},
            ]
    """
    if not is_available() or not edits:
        return ""

    result = call_tool("multi_edit", {"edits": edits})
    return extract_text(result)


def execute_luau(code: str, timeout: float = 30.0) -> str:
    """
    Выполнить произвольный Luau-код в Studio.

    Полезно для:
        • создания объектов (Instance.new(...))
        • настройки свойств
        • операций, которых нет в стандартных MCP-инструментах
    """
    if not is_available() or not code:
        return ""

    result = call_tool("execute_luau", {"code": code}, timeout=timeout)
    return extract_text(result)


# =============================================================================
#  ОБЪЕКТЫ
# =============================================================================

def insert_instance(
    class_name: str,
    parent_path: str,
    properties: dict[str, Any] | None = None,
) -> str:
    """
    Создать новый объект.

    Пример:
        insert_instance("Part", "game.Workspace",
                        {"Position": [0, 5, 0], "Color": [255, 0, 0]})
    """
    if not is_available():
        return ""

    # Проще через execute_luau — надёжнее и гибче.
    props_lines: list[str] = []
    if properties:
        for key, value in properties.items():
            props_lines.append(f"    obj.{key} = {_lua_repr(value)}")

    code = (
        f'local obj = Instance.new("{class_name}")\n'
        f'local parent = {_path_to_lua(parent_path)}\n'
        f'if parent then obj.Parent = parent end\n'
        + "\n".join(props_lines)
        + '\nprint("created: " .. obj:GetFullName())'
    )
    return execute_luau(code)


def delete_instance(path: str) -> str:
    """Удалить объект по пути."""
    if not is_available() or not path:
        return ""

    code = (
        f'local obj = {_path_to_lua(path)}\n'
        f'if obj then obj:Destroy(); print("deleted") '
        f'else print("not found") end'
    )
    return execute_luau(code)


# =============================================================================
#  ТЕСТИРОВАНИЕ
# =============================================================================

def start_playtest() -> str:
    """Запустить playtest в Studio."""
    if not is_available():
        return ""

    result = call_tool("playtest_start")
    return extract_text(result)


def stop_playtest() -> str:
    """Остановить playtest."""
    if not is_available():
        return ""

    result = call_tool("playtest_stop")
    return extract_text(result)


# =============================================================================
#  ВСПОМОГАТЕЛЬНЫЕ
# =============================================================================

def _path_to_lua(path: str) -> str:
    """
    Превращает "game.Workspace.X" в валидное Lua-выражение.

    Например:
        "game.Workspace.Part" → "game:GetService('Workspace').Part"
    """
    if not path:
        return "nil"

    parts = path.split(".")
    if not parts:
        return "nil"

    # Первая часть — game.
    result = "game"

    # Маппинг Services.
    service_map = {
        "Workspace": "Workspace",
        "ServerScriptService": "ServerScriptService",
        "ServerStorage": "ServerStorage",
        "ReplicatedStorage": "ReplicatedStorage",
        "StarterGui": "StarterGui",
        "StarterPack": "StarterPack",
        "StarterPlayer": "StarterPlayer",
        "Players": "Players",
        "Lighting": "Lighting",
        "SoundService": "SoundService",
        "Teams": "Teams",
    }

    for i, part in enumerate(parts[1:], start=1):
        if i == 1 and part in service_map:
            result += f":GetService('{service_map[part]}')"
        else:
            result += f".{part}"

    return result


def _lua_repr(value: Any) -> str:
    """Превращает Python-значение в Lua-литерал."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        # Экранируем кавычки.
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(value, (list, tuple)) and len(value) == 3:
        # Считаем Vector3.
        return f"Vector3.new({value[0]}, {value[1]}, {value[2]})"
    if isinstance(value, (list, tuple)) and len(value) == 4:
        # Считаем Color3.fromRGB.
        return f"Color3.fromRGB({value[0]}, {value[1]}, {value[2]}, {value[3]})"
    if isinstance(value, dict):
        # Считаем словарь свойств.
        inner = ", ".join(f'["{k}"] = {_lua_repr(v)}' for k, v in value.items())
        return "{" + inner + "}"
    return "nil"


__all__ = [
    "read_script",
    "search_scripts",
    "get_game_tree",
    "get_console_output",
    "create_or_edit_script",
    "create_or_edit_scripts",
    "execute_luau",
    "insert_instance",
    "delete_instance",
    "start_playtest",
    "stop_playtest",
]
