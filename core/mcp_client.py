# =============================================================================
#  Codermuks in Termux — MCP-клиент v1.4.0
# =============================================================================
#  Минимальная реализация MCP (Model Context Protocol) клиента.
#  Говорит по JSON-RPC 2.0 через stdin/stdout с MCP-сервером
#  (например, StudioMCP от Roblox).
#
#  Без внешних зависимостей — только Python stdlib.
# =============================================================================

from __future__ import annotations

import json
import subprocess
import threading
import time
from typing import Any


MCP_PROTOCOL_VERSION = "2024-11-05"
MCP_CLIENT_NAME = "Codermuks"
MCP_CLIENT_VERSION = "1.4.0"


class MCPError(Exception):
    """Ошибка MCP-протокола."""
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"MCP error {code}: {message}")


class MCPClient:
    """
    Клиент для MCP-сервера по stdio-транспорту.

    Использование:
        client = MCPClient(command="путь_к_StudioMCP")
        client.connect()
        tools = client.list_tools()
        result = client.call_tool("script_read", {"path": "game.X.Y"})
        client.disconnect()
    """

    def __init__(self, command: str, args: list[str] | None = None) -> None:
        self.command = command
        self.args = args or []
        self._proc: subprocess.Popen | None = None
        self._next_id = 1
        self._lock = threading.Lock()
        self._server_info: dict[str, Any] = {}

    # -------------------------------------------------------------------------
    #  Подключение
    # -------------------------------------------------------------------------

    def connect(self, timeout: int = 30) -> dict[str, Any]:
        """Запускает MCP-сервер и выполняет handshake."""
        if self._proc is not None:
            raise RuntimeError("Уже подключено")

        try:
            self._proc = subprocess.Popen(
                [self.command] + self.args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except FileNotFoundError as exc:
            raise MCPError(-1, f"Команда не найдена: {self.command}") from exc
        except OSError as exc:
            raise MCPError(-1, f"Не удалось запустить: {exc}") from exc

        # Handshake
        try:
            result = self._request("initialize", {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {
                    "name": MCP_CLIENT_NAME,
                    "version": MCP_CLIENT_VERSION,
                },
            }, timeout=timeout)
            self._server_info = result.get("serverInfo", {})
            self._send_notification("notifications/initialized")
            return result
        except Exception:
            self.disconnect()
            raise

    def disconnect(self) -> None:
        """Закрывает соединение."""
        if self._proc is None:
            return
        try:
            if self._proc.stdin:
                self._proc.stdin.close()
        except Exception:
            pass
        try:
            self._proc.terminate()
            self._proc.wait(timeout=5)
        except Exception:
            try:
                self._proc.kill()
            except Exception:
                pass
        self._proc = None

    # -------------------------------------------------------------------------
    #  JSON-RPC обмен
    # -------------------------------------------------------------------------

    def _send(self, message: dict[str, Any]) -> None:
        if self._proc is None or self._proc.stdin is None:
            raise MCPError(-1, "Нет соединения")
        line = json.dumps(message, ensure_ascii=False)
        self._proc.stdin.write(line + "\n")
        self._proc.stdin.flush()

    def _send_notification(self, method: str, params: Any = None) -> None:
        msg: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        self._send(msg)

    def _recv(self, timeout: float = 30.0) -> dict[str, Any]:
        if self._proc is None or self._proc.stdout is None:
            raise MCPError(-1, "Нет соединения")

        deadline = time.time() + timeout
        while time.time() < deadline:
            line = self._proc.stdout.readline()
            if not line:
                raise MCPError(-1, "MCP-сервер закрыл соединение")
            line = line.strip()
            if not line:
                continue
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
        raise MCPError(-1, f"Таймаут ожидания ответа ({timeout}с)")

    def _request(
        self, method: str, params: Any = None, timeout: float = 30.0,
    ) -> Any:
        """Отправляет запрос и ждёт ответ с тем же id."""
        with self._lock:
            req_id = self._next_id
            self._next_id += 1

            msg: dict[str, Any] = {
                "jsonrpc": "2.0", "id": req_id, "method": method,
            }
            if params is not None:
                msg["params"] = params

            self._send(msg)

            # Ждём ответ с нужным id, пропуская уведомления.
            deadline = time.time() + timeout
            while time.time() < deadline:
                resp = self._recv(timeout=max(0.1, deadline - time.time()))

                # Уведомление без id — пропускаем.
                if "id" not in resp:
                    continue

                if resp["id"] != req_id:
                    continue

                if "error" in resp:
                    err = resp["error"]
                    raise MCPError(
                        err.get("code", -1),
                        err.get("message", "unknown"),
                        err.get("data"),
                    )

                return resp.get("result")

            raise MCPError(-1, f"Таймаут запроса '{method}'")

    # -------------------------------------------------------------------------
    #  MCP-операции
    # -------------------------------------------------------------------------

    def list_tools(self) -> list[dict[str, Any]]:
        """Возвращает список доступных инструментов."""
        result = self._request("tools/list")
        return result.get("tools", []) if result else []

    def call_tool(
        self, name: str, arguments: dict[str, Any] | None = None,
        timeout: float = 60.0,
    ) -> dict[str, Any]:
        """
        Вызывает инструмент MCP.

        Возвращает результат (dict с содержимым). Обычно содержит
        поле 'content' — список блоков (text/image).
        """
        return self._request("tools/call", {
            "name": name,
            "arguments": arguments or {},
        }, timeout=timeout)

    def list_resources(self) -> list[dict[str, Any]]:
        """Список доступных ресурсов (файлы, URI и т.п.)."""
        try:
            result = self._request("resources/list")
            return result.get("resources", []) if result else []
        except MCPError:
            return []

    def list_prompts(self) -> list[dict[str, Any]]:
        """Список предопределённых промптов сервера."""
        try:
            result = self._request("prompts/list")
            return result.get("prompts", []) if result else []
        except MCPError:
            return []

    # -------------------------------------------------------------------------
    #  Свойства
    # -------------------------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    @property
    def server_info(self) -> dict[str, Any]:
        return dict(self._server_info)

    def __repr__(self) -> str:
        status = "connected" if self.is_connected else "disconnected"
        return f"<MCPClient {status} cmd={self.command!r}>"


# =============================================================================
#  ГЛОБАЛЬНЫЙ КЛИЕНТ (SINGLETON)
# =============================================================================

_client: MCPClient | None = None
_client_lock = threading.Lock()


def get_client() -> MCPClient | None:
    """Возвращает глобальный MCP-клиент (или None, если не подключено)."""
    return _client


def set_client(client: MCPClient | None) -> None:
    """Устанавливает глобальный клиент."""
    global _client
    with _client_lock:
        _client = client


def is_connected() -> bool:
    """Проверяет, подключён ли MCP-клиент."""
    return _client is not None and _client.is_connected


__all__ = [
    "MCPClient",
    "MCPError",
    "get_client",
    "set_client",
    "is_connected",
    "MCP_PROTOCOL_VERSION",
]
