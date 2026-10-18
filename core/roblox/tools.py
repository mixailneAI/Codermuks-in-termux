# =============================================================================
#  Codermuks in Termux — обёртки над MCP-инструментами Roblox v1.4.0
# =============================================================================

from __future__ import annotations

from typing import Any

from core.roblox import call_tool, extract_text, is_available


def read_script(path: str) -> str:
    if not is_available() or not path:
        return ""
    return extract_text(call_tool("script_read", {"path": path}))


def search_scripts(query: str, max_results: int = 20) -> str:
    if not is_available() or not query:
        return ""
    return extract_text(call_tool("script_grep", {"query": query, "max_results": max_results}))


def get_game_tree(max_depth: int = 4) -> str:
    if not is_available():
        return ""
    return extract_text(call_tool("get_game_tree", {"max_depth": max_depth}))


def get_console_output(lines: int = 50) -> str:
    if not is_available():
        return ""
    return extract_text(call_tool("get_console_output", {"lines": lines}))


def create_or_edit_script(path: str, source: str, script_type: str = "Script") -> str:
    if not is_available() or not path:
        return ""
    return extract_text(call_tool("multi_edit", {
        "edits": [{"path": path, "source": source, "type": script_type}]
    }))


def create_or_edit_scripts(edits: list[dict[str, Any]]) -> str:
    if not is_available() or not edits:
        return ""
    return extract_text(call_tool("multi_edit", {"edits": edits}))


def execute_luau(code: str, timeout: float = 30.0) -> str:
    if not is_available() or not code:
        return ""
    return extract_text(call_tool("execute_luau", {"code": code}, timeout=timeout))


def insert_instance(class_name: str, parent_path: str, properties: dict[str, Any] | None = None) -> str:
    if not is_available():
        return ""
    props = properties or {}
    lines = [f"local obj = Instance.new('{class_name}')"]
    for key, val in props.items():
        lines.append(f"obj.{key} = {_lua_repr(val)}")
    lines.append(f"obj.Parent = {_path_to_lua(parent_path)}")
    lines.append('print("created: " .. obj:GetFullName())')
    return execute_luau("\n".join(lines))


def start_playtest() -> str:
    if not is_available():
        return ""
    return extract_text(call_tool("playtest_start"))


def stop_playtest() -> str:
    if not is_available():
        return ""
    return extract_text(call_tool("playtest_stop"))


def _path_to_lua(path: str) -> str:
    if not path:
        return "nil"
    parts = path.split(".")
    result = "game"
    service_map = {"Workspace": "Workspace", "ServerScriptService": "ServerScriptService",
                   "ReplicatedStorage": "ReplicatedStorage", "StarterGui": "StarterGui",
                   "StarterPlayer": "StarterPlayer", "Players": "Players", "Lighting": "Lighting"}
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
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(value, (list, tuple)) and len(value) == 3:
        return f"Vector3.new({value[0]}, {value[1]}, {value[2]})"
    if isinstance(value, (list, tuple)) and len(value) == 4:
        return f"Color3.fromRGB({value[0]}, {value[1]}, {value[2]}, {value[3]})"
    if isinstance(value, dict):
        inner = ", ".join(f'["{k}"] = {_lua_repr(v)}' for k, v in value.items())
        return "{" + inner + "}"
    return "nil"


__all__ = [
    "read_script", "search_scripts", "get_game_tree", "get_console_output",
    "create_or_edit_script", "create_or_edit_scripts", "execute_luau",
    "insert_instance", "start_playtest", "stop_playtest",
]
