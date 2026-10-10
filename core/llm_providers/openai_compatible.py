# =============================================================================
#  Codermuks in Termux — OpenAI-совместимый провайдер v1.1.0
# =============================================================================
#  Общая реализация для всех провайдеров, работающих через стандартный
#  OpenAI API (/chat/completions). Именно так работают:
#
#      • Mistral   — https://api.mistral.ai/v1
#      • Qwen      — https://dashscope.aliyuncs.com/compatible-mode/v1
#      • DeepSeek  — https://api.deepseek.com/v1
#      • OpenRouter — https://openrouter.ai/api/v1
#
#  Этот класс делает всю тяжёлую работу: HTTP-запросы, retry с backoff,
#  классификацию ошибок, разбор ответа, поддержку стриминга.
#
#  Конкретные провайдеры (mistral_provider.py и т.д.) — это тонкие
#  обёртки, которые задают name, display_name, default_model и при
#  необходимости переопределяют поведение.
# =============================================================================

from __future__ import annotations

import json
import time
from typing import Any, Iterator

import requests

from core.llm_providers.base import (
    ChatMessage,
    LLMProvider,
    ProviderAuthError,
    ProviderError,
    ProviderNetworkError,
    ProviderNotConfiguredError,
    ProviderRateLimitError,
    ProviderResponse,
    ProviderServerError,
)


# =============================================================================
#  КОНСТАНТЫ
# =============================================================================

# Таймаут одного HTTP-запроса (сек). Значение по умолчанию — если
# config не задан или недоступен.
DEFAULT_HTTP_TIMEOUT: int = 120

# Количество попыток при временных ошибках.
DEFAULT_MAX_RETRIES: int = 3

# Базовая задержка между попытками (сек). Экспоненциальный backoff:
# delay = BACKOFF * (2 ** attempt)
DEFAULT_RETRY_BACKOFF: float = 1.5

# Заголовки для всех запросов.
USER_AGENT: str = "Codermuks/1.1.0 (+https://github.com/mixailneAI/Codermuks-in-termux)"


# =============================================================================
#  БАЗОВЫЙ КЛАСС
# =============================================================================

class OpenAICompatibleProvider(LLMProvider):
    """
    Провайдер для любого OpenAI-совместимого API.

    Наследники переопределяют:
        • name           — короткое имя ("mistral", "qwen", ...)
        • display_name   — красивое имя для UI ("Mistral AI", "Qwen", ...)
        • default_model  — модель по умолчанию

    Если у провайдера особые заголовки (например, OpenRouter требует
    HTTP-Referer и X-Title) — их можно добавить в `extra_headers()`.
    """

    # --- Классовые атрибуты, переопределяются в наследниках ---------------
    name: str = "openai_compatible"
    display_name: str = "OpenAI-Compatible Provider"
    default_model: str = ""

    # -------------------------------------------------------------------------
    #  Настройки
    # -------------------------------------------------------------------------

    def _http_timeout(self) -> int:
        """Возвращает таймаут HTTP-запроса из config или дефолт."""
        try:
            from core import config
            return int(getattr(config, "API_TIMEOUT", DEFAULT_HTTP_TIMEOUT))
        except Exception:
            return DEFAULT_HTTP_TIMEOUT

    def _max_retries(self) -> int:
        """Количество попыток при временных ошибках."""
        try:
            from core import config
            return int(getattr(config, "API_MAX_RETRIES", DEFAULT_MAX_RETRIES))
        except Exception:
            return DEFAULT_MAX_RETRIES

    def _retry_backoff(self) -> float:
        """Базовая задержка между попытками."""
        try:
            from core import config
            return float(getattr(config, "API_RETRY_BACKOFF", DEFAULT_RETRY_BACKOFF))
        except Exception:
            return DEFAULT_RETRY_BACKOFF

    def extra_headers(self) -> dict[str, str]:
        """
        Дополнительные HTTP-заголовки.

        Наследники могут переопределить. Например, OpenRouter требует
        HTTP-Referer и X-Title для аналитики.
        """
        return {}

    # -------------------------------------------------------------------------
    #  Формирование HTTP-запроса
    # -------------------------------------------------------------------------

    def _build_url(self) -> str:
        """
        Собирает полный URL до эндпоинта /chat/completions.

        Убирает лишний слэш в конце base_url, если он есть.
        """
        base = self.get_base_url().rstrip("/")
        if not base:
            raise ProviderNotConfiguredError(
                f"Провайдер {self.name}: не задан base_url в config.json."
            )
        return f"{base}/chat/completions"

    def _build_headers(self) -> dict[str, str]:
        """
        Собирает заголовки для HTTP-запроса.

        Включает:
            • Authorization: Bearer <api_key>
            • Content-Type: application/json
            • User-Agent
            • дополнительные заголовки от наследника
        """
        api_key = self.get_api_key()
        if not api_key:
            raise ProviderAuthError(
                f"Провайдер {self.name}: отсутствует API-ключ. "
                f"Вставь ключ в ~/.codermuks/key.txt"
            )

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }
        headers.update(self.extra_headers())
        return headers

    def _build_payload(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float | None,
        max_tokens: int | None,
        stream: bool,
    ) -> dict[str, Any]:
        """
        Собирает тело запроса.

        Значения temperature и max_tokens берутся из config, если
        пользователь их не задал явно.
        """
        # Дефолты из config.
        if temperature is None:
            try:
                from core import config
                temperature = float(getattr(config, "TEMPERATURE_PLANNING", 0.3))
            except Exception:
                temperature = 0.3

        if max_tokens is None:
            try:
                from core import config
                max_tokens = int(getattr(config, "MAX_TOKENS", 8192))
            except Exception:
                max_tokens = 8192

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if stream:
            payload["stream"] = True

        return payload

    # -------------------------------------------------------------------------
    #  Классификация ошибок
    # -------------------------------------------------------------------------

    def _classify_http_error(self, status_code: int, body: str) -> Exception:
        """
        Превращает HTTP-статус в понятное исключение.

        Коды:
            401, 403     → ProviderAuthError
            429          → ProviderRateLimitError
            500, 502,
            503, 504     → ProviderServerError
            остальные    → ProviderNetworkError
        """
        snippet = (body or "")[:300]

        if status_code in (401, 403):
            return ProviderAuthError(
                f"Провайдер {self.name}: неверный API-ключ "
                f"(HTTP {status_code}). Проверь ~/.codermuks/key.txt"
            )

        if status_code == 429:
            return ProviderRateLimitError(
                f"Провайдер {self.name}: превышен лимит запросов "
                f"(HTTP 429). Подожди немного."
            )

        if status_code in (500, 502, 503, 504):
            return ProviderServerError(
                f"Провайдер {self.name}: сервер временно недоступен "
                f"(HTTP {status_code}). Попробую позже."
            )

        return ProviderNetworkError(
            f"Провайдер {self.name}: HTTP {status_code}. Ответ: {snippet}"
        )

    def _classify_exception(self, exc: Exception) -> Exception:
        """
        Превращает сетевое исключение requests в наш тип ошибки.
        """
        text = str(exc).lower()

        if "timeout" in text or "timed out" in text:
            return ProviderNetworkError(
                f"Провайдер {self.name}: таймаут запроса."
            )

        if "connection" in text or "network" in text or "resolve" in text:
            return ProviderNetworkError(
                f"Провайдер {self.name}: нет соединения с сервером."
            )

        return ProviderNetworkError(
            f"Провайдер {self.name}: ошибка запроса: {exc}"
        )

    # -------------------------------------------------------------------------
    #  Разбор успешного ответа
    # -------------------------------------------------------------------------

    def _parse_response(self, data: dict[str, Any], model: str) -> ProviderResponse:
        """
        Превращает JSON-ответ API в объект ProviderResponse.

        Ожидаемый формат (OpenAI-совместимый):
            {
              "choices": [
                {"message": {"role": "assistant", "content": "..."},
                 "finish_reason": "stop"}
              ],
              "usage": {"prompt_tokens": 10, "completion_tokens": 20, ...},
              "model": "mistral-large-latest"
            }
        """
        text = ""

        choices = data.get("choices") or []
        if choices:
            first = choices[0]
            message = first.get("message") or {}
            content = message.get("content", "")

            # content может быть строкой или списком блоков (некоторые API).
            if isinstance(content, str):
                text = content
            elif isinstance(content, list):
                parts: list[str] = []
                for part in content:
                    if isinstance(part, dict) and part.get("text"):
                        parts.append(str(part["text"]))
                    elif isinstance(part, str):
                        parts.append(part)
                text = "".join(parts)

            finish_reason = str(first.get("finish_reason", ""))
        else:
            finish_reason = ""

        # Метаданные.
        usage_raw = data.get("usage") or {}
        usage: dict[str, int] = {}
        if isinstance(usage_raw, dict):
            for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
                value = usage_raw.get(key)
                if isinstance(value, int):
                    usage[key] = value

        served_model = str(data.get("model", model))

        return ProviderResponse(
            text=text,
            provider=self.name,
            model=served_model,
            finish_reason=finish_reason,
            usage=usage,
            raw=data,
        )

    # -------------------------------------------------------------------------
    #  Основной метод — chat
    # -------------------------------------------------------------------------

    def chat(
        self,
        messages: list[ChatMessage] | list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> ProviderResponse:
        """
        Отправляет запрос к API и возвращает ответ.

        Реализует retry с экспоненциальным backoff при временных
        ошибках (сеть, 5xx, rate limit). При auth error — падает сразу.
        """
        # Проверяем, что провайдер настроен.
        if not self.get_api_key():
            raise ProviderAuthError(
                f"Провайдер {self.name}: API-ключ не задан."
            )

        chosen_model = model or self.get_model()
        if not chosen_model:
            raise ProviderNotConfiguredError(
                f"Провайдер {self.name}: не задана модель."
            )

        normalized = self.normalize_messages(messages)
        url = self._build_url()
        headers = self._build_headers()
        payload = self._build_payload(
            normalized, chosen_model, temperature, max_tokens, stream=False
        )

        timeout = self._http_timeout()
        max_retries = self._max_retries()
        backoff = self._retry_backoff()

        last_exc: Exception | None = None

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=timeout,
                )

                # Успех.
                if 200 <= response.status_code < 300:
                    try:
                        data = response.json()
                    except json.JSONDecodeError:
                        raise ProviderNetworkError(
                            f"Провайдер {self.name}: не удалось разобрать JSON-ответ."
                        )
                    return self._parse_response(data, chosen_model)

                # Ошибка HTTP — классифицируем.
                error = self._classify_http_error(
                    response.status_code, response.text
                )
                last_exc = error

                # Auth — повторять бессмысленно.
                if isinstance(error, ProviderAuthError):
                    raise error

                # Остальные ошибки — повторяем, если есть попытки.
                if attempt < max_retries - 1:
                    time.sleep(backoff * (2 ** attempt))
                    continue
                raise error

            except ProviderAuthError:
                raise
            except ProviderError:
                raise
            except requests.RequestException as exc:
                last_exc = self._classify_exception(exc)

                if attempt < max_retries - 1:
                    time.sleep(backoff * (2 ** attempt))
                    continue
                raise last_exc

            except Exception as exc:
                last_exc = ProviderNetworkError(
                    f"Провайдер {self.name}: неожиданная ошибка: {exc}"
                )

                if attempt < max_retries - 1:
                    time.sleep(backoff * (2 ** attempt))
                    continue
                raise last_exc

        # Сюда не должны попасть, но на всякий случай.
        raise last_exc or ProviderNetworkError(
            f"Провайдер {self.name}: все попытки исчерпаны."
        )

    # -------------------------------------------------------------------------
    #  Потоковый режим
    # -------------------------------------------------------------------------

    def chat_stream(
        self,
        messages: list[ChatMessage] | list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> Iterator[str]:
        """
        Потоковый режим: отдаёт кусочки текста по мере поступления.

        Использует SSE (Server-Sent Events), который поддерживает
        любой OpenAI-совместимый API. Формат каждой строки:

            data: {"choices":[{"delta":{"content":"..."}}]}

        Завершение: строка `data: [DONE]`.

        Если стриминг не поддерживается — наследник может
        воспользоваться базовой реализацией из LLMProvider (вернёт
        ответ одним куском).
        """
        if not self.get_api_key():
            raise ProviderAuthError(
                f"Провайдер {self.name}: API-ключ не задан."
            )

        chosen_model = model or self.get_model()
        if not chosen_model:
            raise ProviderNotConfiguredError(
                f"Провайдер {self.name}: не задана модель."
            )

        normalized = self.normalize_messages(messages)
        url = self._build_url()
        headers = self._build_headers()
        payload = self._build_payload(
            normalized, chosen_model, temperature, max_tokens, stream=True
        )

        timeout = self._http_timeout()

        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=timeout,
                stream=True,
            )
        except requests.RequestException as exc:
            raise self._classify_exception(exc)

        if response.status_code >= 400:
            raise self._classify_http_error(
                response.status_code,
                response.text if hasattr(response, "text") else "",
            )

        # Парсим SSE-поток.
        try:
            for raw_line in response.iter_lines(decode_unicode=True):
                if not raw_line:
                    continue

                line = raw_line.strip()

                # Пропускаем служебные строки.
                if line.startswith(":"):
                    continue
                if not line.startswith("data:"):
                    continue

                data_str = line[len("data:"):].strip()

                # Конец потока.
                if data_str == "[DONE]":
                    break

                try:
                    chunk = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                choices = chunk.get("choices") or []
                if not choices:
                    continue

                delta = choices[0].get("delta") or {}
                content = delta.get("content")

                if isinstance(content, str) and content:
                    yield content
                elif isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and part.get("text"):
                            yield str(part["text"])
                        elif isinstance(part, str):
                            yield part

        except requests.RequestException as exc:
            raise self._classify_exception(exc)


# =============================================================================
#  ЭКСПОРТ
# =============================================================================

__all__ = ["OpenAICompatibleProvider"]