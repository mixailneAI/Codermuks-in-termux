# =============================================================================
#  Codermuks in Termux — HTTP/SSE MCP-клиент v1.4.0
# =============================================================================
#  Поддерживает подключение к удалённому MCP-серверу по HTTP.
#  Используется для Roblox Studio, когда сервер запущен на другой машине
#  (ПК) в локальной сети или через туннель (Tailscale, ngrok).
#
#  Протокол: JSON-RPC 2.0 over HTTP (Streamable HTTP / SSE).
# =============================================================================

from __future__ import annotations

import json
import time
import uuid
from typing import Any

import requests


class HTTPMCPError(Exception):
    """Ошибка HTTP MCP-клиента."""
    def __init__(self, message: str, status_code: int = 0):
        self.message = message
        self.status_code = status_code
        super().__init__(f"HTTP MCP error ({status_code}): {message}")


class HTTPMCPClient:
    """
    MCP-клиент для удалённого сервера по HTTP.

    Использование:
        client = HTTPMCPClient(url="http://192.168.1.50:3030/mcp")
        client.connect()
        tools = client.list_tools()
        result = client.call_tool("execute_luau", {"code": "print(1)"})
        client.disconnect()
    """

    def __init__(
        self,
        url: str,
        auth_token: str = "",
        timeout: float = 30.0,
    ) -> None:
        self.url = url.rstrip("/")
        self.auth_token = auth_token
        self.timeout = timeout
        self._session_id: str | None = None
        self._next_id = 1
        self._server_info: dict[str, Any] = {}

    # -------------------------------------------------------------------------
    #  Подключение
    # -------------------------------------------------------------------------

    def connect(self) -> dict[str, Any]:
        """Выполняет handshake с удалённым MCP-сервером."""
        try:
            result = self._request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "Codermuks",
                    "version": "1.4.0",
                },
            })
            self._server_info = result.get("serverInfo", {})
            self._notify("notifications/initialized", {})
            return result
        except Exception:
            self.disconnect()
            raise

    def disconnect(self) -> None:
        """Закрывает сессию (если сервер поддерживает)."""
        self._session_id = None

    # -------------------------------------------------------------------------
    #  HTTP-запросы
    # -------------------------------------------------------------------------

    def _build_headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
            headers["X-MCP-Auth"] = self.auth_token
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        return headers

    def _request(self, method: str, params: Any = None) -> Any:
        """Отправляет JSON-RPC запрос и возвращает результат."""
        req_id = str(uuid.uuid4())
        payload: dict[str, Any] = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
        }
        if params is not None:
            payload["params"] = params

        try:
            resp = requests.post(
                self.url,
                json=payload,
                headers=self._build_headers(),
                timeout=self.timeout,
                stream=True,
            )
        except requests.RequestException as exc:
            raise HTTPMCPError(f"Сетевая ошибка: {exc}") from exc

        # Запоминаем session id.
        sid = resp.headers.get("mcp-session-id")
        if sid:
            self._session_id = sid

        if resp.status_code >= 400:
            raise HTTPMCPError(
                f"HTTP {resp.status_code}: {resp.text[:300]}",
                status_code=resp.status_code,
            )

        content_type = resp.headers.get("content-type", "")

        # JSON-ответ.
        if "application/json" in content_type:
            try:
                data = resp.json()
            except json.JSONDecodeError as exc:
                raise HTTPMCPError(f"Невалидный JSON: {exc}") from exc
            if "error" in data:
                raise HTTPMCPError(f"MCP error: {data['error']}")
            return data.get("result")

        # SSE-ответ (text/event-stream).
        if "text/event-stream" in content_type:
            return self._parse_sse(resp)

        # Неизвестный формат — пробуем как JSON.
        try:
            data = resp.json()
            if "error" in data:
                raise HTTPMCPError(f"MCP error: {data['error']}")
            return data.get("result")
        except json.JSONDecodeError:
            raise HTTPMCPError(f"Неизвестный Content-Type: {content_type}")

    def _parse_sse(self, resp: requests.Response) -> Any:
        """Парсит SSE-поток и возвращает последний result."""
        result: Any = None
        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            if line.startswith("data:"):
                data_str = line[len("data:"):].strip()
                if not data_str:
                    continue
                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    continue
                if "error" in data:
                    raise HTTPMCPError(f"MCP error: {data['error']}")
                if "result" in data:
                    result = data["result"]
        if result is None:
            raise HTTPMCPError("SSE-поток завершился без result")
        return result

    def _notify(self, method: str, params: Any = None) -> None:
        """Отправляет notification (без ожидания ответа)."""
        payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        try:
            requests.post(
                self.url,
                json=payload,
                headers=self._build_headers(),
                timeout=5,
            )
        except requests.RequestException:
            pass

    # -------------------------------------------------------------------------
    #  MCP-операции
    # -------------------------------------------------------------------------

    def list_tools(self) -> list[dict[str, Any]]:
        result = self._request("tools/list")
        return result.get("tools", []) if result else []

    def call_tool(
        self, name: str, arguments: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        if timeout:
            old = self.timeout
            self.timeout = timeout
            try:
                return self._request("tools/call", {
                    "name": name,
                    "arguments": arguments or {},
                })
            finally:
                self.timeout = old
        return self._request("tools/call", {
            "name": name,
            "arguments": arguments or {},
        })

    # -------------------------------------------------------------------------
    #  Свойства
    # -------------------------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        return True  # HTTP-клиент не держит соединение, всегда «готов»

    @property
    def server_info(self) -> dict[str, Any]:
        return dict(self._server_info)


__all__ = ["HTTPMCPClient", "HTTPMCPError"]
