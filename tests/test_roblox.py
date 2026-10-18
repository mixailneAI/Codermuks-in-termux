# =============================================================================
#  Codermuks in Termux — тесты для Roblox-модуля v1.4.1
# =============================================================================

from __future__ import annotations

import sys
from pathlib import Path

# Корень проекта в sys.path.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
#  MCP CLIENT
# =============================================================================

class TestMCPClientImports:
    """Тесты импорта и базовых свойств MCP-клиента."""

    def test_import(self):
        from core.mcp_client import MCPClient, MCPError
        assert MCPClient is not None
        assert MCPError is not None

    def test_protocol_version(self):
        from core.mcp_client import MCP_PROTOCOL_VERSION
        assert MCP_PROTOCOL_VERSION == "2024-11-05"

    def test_client_version(self):
        from core.mcp_client import MCP_CLIENT_VERSION
        assert MCP_CLIENT_VERSION.startswith("1.")

    def test_error_attributes(self):
        from core.mcp_client import MCPError
        err = MCPError(404, "Not found", {"detail": "x"})
        assert err.code == 404
        assert err.message == "Not found"
        assert err.data == {"detail": "x"}

    def test_client_not_connected_by_default(self):
        from core.mcp_client import MCPClient
        client = MCPClient(command="nonexistent_binary_xyz")
        assert client.is_connected is False

    def test_client_repr(self):
        from core.mcp_client import MCPClient
        client = MCPClient(command="test")
        assert "disconnected" in repr(client)
        assert "test" in repr(client)

    def test_global_singleton(self):
        from core.mcp_client import get_client, set_client, is_connected
        # По умолчанию — не подключено.
        set_client(None)
        assert get_client() is None
        assert is_connected() is False

    def test_connect_nonexistent_raises(self):
        """Подключение к несуществующему бинарю → MCPError."""
        from core.mcp_client import MCPClient, MCPError
        client = MCPClient(command="definitely_not_a_real_binary_xyz123")
        try:
            client.connect(timeout=2)
            assert False, "Должно было упасть"
        except MCPError:
            pass  # Ожидаемо
        finally:
            client.disconnect()


# =============================================================================
#  ROBLOX DISCOVERY
# =============================================================================

class TestRobloxDiscovery:
    """Тесты поиска StudioMCP."""

    def test_import(self):
        from core.roblox.discovery import find_studio_mcp, list_all_candidates
        assert callable(find_studio_mcp)
        assert callable(list_all_candidates)

    def test_find_returns_string(self):
        from core.roblox.discovery import find_studio_mcp
        result = find_studio_mcp()
        assert isinstance(result, str)

    def test_list_candidates_returns_list(self):
        from core.roblox.discovery import list_all_candidates
        result = list_all_candidates()
        assert isinstance(result, list)

    def test_save_load_clear(self, tmp_path, monkeypatch):
        """Проверяем сохранение/загрузку пути."""
        from core.roblox import discovery
        # Подменяем ROBLOX_CONFIG_FILE на временный.
        test_file = tmp_path / "roblox.json"
        monkeypatch.setattr(discovery, "ROBLOX_CONFIG_FILE", test_file)

        # Изначально пусто.
        assert discovery.load_saved_path() == ""

        # Сохраняем.
        discovery.save_path("/tmp/fake_studiomcp")
        assert discovery.load_saved_path() == "/tmp/fake_studiomcp"

        # Очищаем.
        discovery.clear_saved_path()
        assert discovery.load_saved_path() == ""


# =============================================================================
#  ROBLOX PACKAGE (facade)
# =============================================================================

class TestRobloxPackage:
    """Тесты фасада core.roblox."""

    def test_import(self):
        from core.roblox import (
            is_available, list_tools, get_tool_names,
            call_tool, extract_text, find_studio_mcp,
        )
        assert callable(is_available)
        assert callable(list_tools)
        assert callable(get_tool_names)
        assert callable(call_tool)
        assert callable(extract_text)
        assert callable(find_studio_mcp)

    def test_is_available_false_on_termux(self):
        """На Termux Studio нет → False."""
        from core.roblox import is_available, disconnect
        disconnect()
        assert is_available() is False

    def test_list_tools_empty_without_connection(self):
        from core.roblox import list_tools, disconnect
        disconnect()
        assert list_tools() == []

    def test_get_tool_names_empty(self):
        from core.roblox import get_tool_names, disconnect
        disconnect()
        assert get_tool_names() == []

    def test_call_tool_returns_none_without_connection(self):
        from core.roblox import call_tool, disconnect
        disconnect()
        assert call_tool("execute_luau", {"code": "print(1)"}) is None

    def test_extract_text_empty(self):
        from core.roblox import extract_text
        assert extract_text(None) == ""
        assert extract_text({}) == ""

    def test_extract_text_from_content(self):
        from core.roblox import extract_text
        result = {
            "content": [
                {"type": "text", "text": "hello"},
                {"type": "text", "text": "world"},
            ]
        }
        assert extract_text(result) == "hello\nworld"

    def test_extract_text_error(self):
        from core.roblox import extract_text
        result = {
            "isError": True,
            "error": "something failed",
            "content": [{"type": "text", "text": "something failed"}],
        }
        assert "something failed" in extract_text(result)


# =============================================================================
#  ROBLOX TOOLS
# =============================================================================

class TestRobloxTools:
    """Тесты обёрток tools.py — без подключения всё возвращает пусто."""

    def test_read_script_empty(self):
        from core.roblox.tools import read_script
        from core.roblox import disconnect
        disconnect()
        assert read_script("game.Workspace") == ""

    def test_search_scripts_empty(self):
        from core.roblox.tools import search_scripts
        from core.roblox import disconnect
        disconnect()
        assert search_scripts("test") == ""

    def test_get_game_tree_empty(self):
        from core.roblox.tools import get_game_tree
        from core.roblox import disconnect
        disconnect()
        assert get_game_tree() == ""

    def test_execute_luau_empty(self):
        from core.roblox.tools import execute_luau
        from core.roblox import disconnect
        disconnect()
        assert execute_luau("print(1)") == ""

    def test_create_or_edit_empty(self):
        from core.roblox.tools import create_or_edit_script
        from core.roblox import disconnect
        disconnect()
        assert create_or_edit_script("game.X", "code") == ""

    def test_insert_instance_empty(self):
        from core.roblox.tools import insert_instance
        from core.roblox import disconnect
        disconnect()
        assert insert_instance("Part", "game.Workspace") == ""

    def test_path_to_lua_service(self):
        """game.Workspace.X → game:GetService('Workspace').X."""
        from core.roblox.tools import _path_to_lua
        result = _path_to_lua("game.Workspace.Part")
        assert "GetService('Workspace')" in result
        assert ".Part" in result

    def test_path_to_lua_nested(self):
        """Nested path работает."""
        from core.roblox.tools import _path_to_lua
        result = _path_to_lua("game.ServerScriptService.Modules.Utils")
        assert "GetService('ServerScriptService')" in result
        assert ".Modules.Utils" in result

    def test_path_to_lua_empty(self):
        from core.roblox.tools import _path_to_lua
        assert _path_to_lua("") == "nil"

    def test_lua_repr_number(self):
        from core.roblox.tools import _lua_repr
        assert _lua_repr(42) == "42"
        assert _lua_repr(3.14) == "3.14"

    def test_lua_repr_bool(self):
        from core.roblox.tools import _lua_repr
        assert _lua_repr(True) == "true"
        assert _lua_repr(False) == "false"

    def test_lua_repr_string(self):
        from core.roblox.tools import _lua_repr
        assert _lua_repr("hello") == '"hello"'
        assert _lua_repr('he said "hi"') == '"he said \\"hi\\""'

    def test_lua_repr_vector3(self):
        from core.roblox.tools import _lua_repr
        result = _lua_repr([1, 2, 3])
        assert result == "Vector3.new(1, 2, 3)"

    def test_lua_repr_color3(self):
        from core.roblox.tools import _lua_repr
        result = _lua_repr([255, 0, 0, 0])
        assert "Color3.fromRGB" in result

    def test_lua_repr_dict(self):
        from core.roblox.tools import _lua_repr
        result = _lua_repr({"A": 1, "B": "x"})
        assert '["A"] = 1' in result
        assert '["B"] = "x"' in result


# =============================================================================
#  ROBLOX SUBAGENTS
# =============================================================================

class TestRobloxSubagents:
    """Тесты субагентов — без провайдера и без Studio."""

    def test_import(self):
        from core.roblox.subagents import (
            RobloxScriptAgent, RobloxWorldAgent, RobloxTestAgent,
        )
        assert RobloxScriptAgent is not None
        assert RobloxWorldAgent is not None
        assert RobloxTestAgent is not None

    def test_list_names(self):
        from core.roblox.subagents import list_subagent_names
        names = list_subagent_names()
        assert "script" in names
        assert "world" in names
        assert "test" in names

    def test_create_subagent_valid(self):
        from core.roblox.subagents import create_subagent, RobloxScriptAgent
        agent = create_subagent("script", None)
        assert isinstance(agent, RobloxScriptAgent)

    def test_create_subagent_invalid(self):
        from core.roblox.subagents import create_subagent
        agent = create_subagent("nonexistent", None)
        assert agent is None

    def test_script_agent_not_ready(self):
        """Без Studio run() возвращает ошибку."""
        from core.roblox.subagents import RobloxScriptAgent
        from core.roblox import disconnect
        disconnect()
        agent = RobloxScriptAgent(provider=None)
        assert agent.is_ready() is False
        result = agent.run("test")
        assert "не подключён" in result.lower() or "❌" in result

    def test_world_agent_not_ready(self):
        from core.roblox.subagents import RobloxWorldAgent
        from core.roblox import disconnect
        disconnect()
        agent = RobloxWorldAgent(provider=None)
        result = agent.run("test")
        assert "не подключён" in result.lower() or "❌" in result

    def test_test_agent_not_ready(self):
        from core.roblox.subagents import RobloxTestAgent
        from core.roblox import disconnect
        disconnect()
        agent = RobloxTestAgent(provider=None)
        result = agent.run("test")
        assert "не подключён" in result.lower() or "❌" in result


# =============================================================================
#  ПАРСИНГ JSON В СУБАГЕНТАХ
# =============================================================================

class TestParseJson:
    """Тесты парсинга JSON из ответов LLM."""

    def test_parse_clean_json(self):
        from core.roblox.subagents import BaseRobloxSubagent
        text = '{"action": "test", "value": 42}'
        result = BaseRobloxSubagent._parse_json(text)
        assert result is not None
        assert result["action"] == "test"
        assert result["value"] == 42

    def test_parse_with_markdown(self):
        from core.roblox.subagents import BaseRobloxSubagent
        text = '```json\n{"a": 1}\n```'
        result = BaseRobloxSubagent._parse_json(text)
        assert result == {"a": 1}

    def test_parse_with_text_around(self):
        from core.roblox.subagents import BaseRobloxSubagent
        text = 'Here is the plan:\n{"b": 2}\nEnd.'
        result = BaseRobloxSubagent._parse_json(text)
        assert result == {"b": 2}

    def test_parse_invalid(self):
        from core.roblox.subagents import BaseRobloxSubagent
        assert BaseRobloxSubagent._parse_json("not json at all") is None
        assert BaseRobloxSubagent._parse_json("") is None
        assert BaseRobloxSubagent._parse_json(None) is None

    def test_parse_nested(self):
        from core.roblox.subagents import BaseRobloxSubagent
        text = '{"actions": [{"tool": "x"}], "summary": "done"}'
        result = BaseRobloxSubagent._parse_json(text)
        assert result["actions"][0]["tool"] == "x"
        assert result["summary"] == "done"


# =============================================================================
#  ROBLOX PROMPTS
# =============================================================================

class TestRobloxPrompts:
    """Тесты промптов для субагентов."""

    def test_system_prompts_exist(self):
        from core.roblox.prompts import (
            SCRIPT_AGENT_SYSTEM, WORLD_AGENT_SYSTEM, TEST_AGENT_SYSTEM,
        )
        assert "Roblox" in SCRIPT_AGENT_SYSTEM
        assert "Roblox" in WORLD_AGENT_SYSTEM
        assert "Roblox" in TEST_AGENT_SYSTEM

    def test_task_templates_exist(self):
        from core.roblox.prompts import (
            SCRIPT_AGENT_TASK, WORLD_AGENT_TASK, TEST_AGENT_TASK,
        )
        assert "{query}" in SCRIPT_AGENT_TASK
        assert "{query}" in WORLD_AGENT_TASK
        assert "{query}" in TEST_AGENT_TASK

    def test_format_script_task(self):
        from core.roblox.prompts import SCRIPT_AGENT_TASK
        result = SCRIPT_AGENT_TASK.format(
            query="test query",
            project_name="my-project",
            scripts_list="(none)",
            console_errors="(none)",
            plan="{}",
        )
        assert "test query" in result
        assert "my-project" in result
