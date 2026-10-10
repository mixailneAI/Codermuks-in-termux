# =============================================================================
#  Codermuks in Termux — базовые классы LLM-провайдеров v1.1.0
# =============================================================================
#  Этот модуль задаёт общий интерфейс для всех провайдеров (Mistral, Qwen,
#  DeepSeek, OpenRouter). Любой провайдер обязан наследоваться от
#  LLMProvider и реализовать метод chat().
#
#  Что здесь есть:
#    • ChatMessage      — dataclass одного сообщения в диалоге;
#    • ProviderResponse — dataclass ответа от провайдера;
#    • LLMProvider      — абстрактный базовый класс провайдера;
#    • исключения       — ProviderError и его подтипы.
#
#  Никакой конкретной логики обращения к API здесь нет — только контракт.
#  Реальная реализация — в openai_compatible.py и наследниках.
# =============================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Iterator


# =============================================================================
#  ИСКЛЮЧЕНИЯ
# =============================================================================

class ProviderError(Exception):
    """Базовая ошибка провайдера."""
    pass


class ProviderAuthError(ProviderError):
    """Ошибка аутентификации: неверный или отсутствующий API-ключ."""
    pass


class ProviderRateLimitError(ProviderError):
    """Превышен лимит запросов к API провайдера."""
    pass


class ProviderServerError(ProviderError):
    """Сервер провайдера вернул 5xx — временная проблема на его стороне."""
    pass


class ProviderNetworkError(ProviderError):
    """Сетевая ошибка: нет соединения, таймаут, DNS."""
    pass


class ProviderNotConfiguredError(ProviderError):
    """Провайдер не настроен: нет API-ключа или он отключён в конфиге."""
    pass


# =============================================================================
#  СТРУКТУРЫ ДАННЫХ
# =============================================================================

@dataclass
class ChatMessage:
    """
    Одно сообщение в диалоге.

    Поля:
        role    — "system", "user" или "assistant"
        content — текст сообщения

    Пример:
        ChatMessage(role="user", content="Привет!")
    """
    role: str
    content: str

    def to_dict(self) -> dict[str, str]:
        """Преобразует в формат OpenAI: {"role": ..., "content": ...}."""
        return {"role": self.role, "content": self.content}

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "ChatMessage":
        """Создаёт объект из словаря формата OpenAI."""
        return cls(
            role=str(data.get("role", "user")),
            content=str(data.get("content", "")),
        )


@dataclass
class ProviderResponse:
    """
    Ответ от LLM-провайдера.

    Поля:
        text          — текст ответа модели
        provider      — имя провайдера ("mistral", "qwen", ...)
        model         — имя модели, которая сгенерировала ответ
        finish_reason — причина остановки ("stop", "length", "content_filter")
        usage         — статистика токенов (prompt_tokens, completion_tokens, total_tokens)
        raw           — сырой ответ API (для отладки)
    """
    text: str
    provider: str = ""
    model: str = ""
    finish_reason: str = ""
    usage: dict[str, int] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    def __bool__(self) -> bool:
        """Ответ считается «истинным», если в нём есть текст."""
        return bool(self.text and self.text.strip())


# =============================================================================
#  АБСТРАКТНЫЙ ПРОВАЙДЕР
# =============================================================================

class LLMProvider(ABC):
    """
    Базовый класс для всех LLM-провайдеров.

    Наследники обязаны:
        1. Задать атрибут `name` (например, "mistral").
        2. Задать атрибут `display_name` (например, "Mistral AI").
        3. Задать атрибут `default_model`.
        4. Реализовать метод `chat()`.

    Опционально можно переопределить `chat_stream()` и `is_available()`.
    """

    # --- Классовые атрибуты (переопределяются в наследниках) ---------------
    name: str = "base"
    display_name: str = "Base Provider"
    default_model: str = ""

    def __init__(self) -> None:
        """Инициализация по умолчанию. Наследники могут расширить."""
        # Кэш настроек, загружается лениво.
        self._model: str | None = None
        self._base_url: str | None = None
        self._api_key: str | None = None
        self._configured: bool | None = None

    # -------------------------------------------------------------------------
    #  Абстрактный интерфейс
    # -------------------------------------------------------------------------

    @abstractmethod
    def chat(
        self,
        messages: list[ChatMessage] | list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> ProviderResponse:
        """
        Отправляет список сообщений в модель и возвращает ответ.

        Аргументы:
            messages    — список ChatMessage или словарей {"role", "content"}
            model       — имя модели (если None — берётся из конфига)
            temperature — температура генерации
            max_tokens  — лимит токенов в ответе

        Возвращает:
            ProviderResponse с текстом ответа и метаданными.

        Исключения:
            ProviderAuthError       — неверный ключ
            ProviderRateLimitError  — превышен лимит
            ProviderServerError     — 5xx на стороне провайдера
            ProviderNetworkError    — сетевая ошибка
        """
        raise NotImplementedError

    # -------------------------------------------------------------------------
    #  Опциональный потоковый интерфейс
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
        Потоковый вариант chat(). По умолчанию не реализован.

        Наследники могут переопределить, если API поддерживает стриминг.
        Базовая реализация: просто вызывает chat() и отдаёт текст целиком.

        Yields:
            Кусочки текста по мере поступления.
        """
        response = self.chat(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if response.text:
            yield response.text

    # -------------------------------------------------------------------------
    #  Проверка готовности
    # -------------------------------------------------------------------------

    def is_available(self) -> bool:
        """
        Проверяет, готов ли провайдер к работе.

        Провайдер считается готовым, если:
            • он включён в config.json;
            • для него задан API-ключ;
            • задан base_url.

        Кэширует результат, чтобы не читать конфиг на каждый вызов.
        """
        if self._configured is not None:
            return self._configured

        try:
            from core import config
            self._configured = bool(
                config.is_provider_enabled(self.name)
                and config.get_api_key(self.name)
                and config.get_provider_base_url(self.name)
            )
        except Exception:
            self._configured = False

        return self._configured

    def reset_cache(self) -> None:
        """
        Сбрасывает кэш настроек.

        Полезно, если пользователь сменил ключ или модель через CLI,
        и нужно перечитать config.json.
        """
        self._model = None
        self._base_url = None
        self._api_key = None
        self._configured = None

    # -------------------------------------------------------------------------
    #  Геттеры настроек
    # -------------------------------------------------------------------------

    def get_model(self) -> str:
        """
        Возвращает имя модели.

        Сначала ищет в config.json (поле model). Если там пусто —
        возвращает default_model, заданный в наследнике.
        """
        if self._model is not None:
            return self._model

        try:
            from core import config
            configured = config.get_provider_model(self.name)
            self._model = configured or self.default_model
        except Exception:
            self._model = self.default_model

        return self._model

    def get_base_url(self) -> str:
        """Возвращает base_url для OpenAI-совместимого API."""
        if self._base_url is not None:
            return self._base_url

        try:
            from core import config
            self._base_url = config.get_provider_base_url(self.name)
        except Exception:
            self._base_url = ""

        return self._base_url

    def get_api_key(self) -> str:
        """Возвращает API-ключ провайдера."""
        if self._api_key is not None:
            return self._api_key

        try:
            from core import config
            self._api_key = config.get_api_key(self.name)
        except Exception:
            self._api_key = ""

        return self._api_key

    # -------------------------------------------------------------------------
    #  Утилиты для наследников
    # -------------------------------------------------------------------------

    @staticmethod
    def normalize_messages(
        messages: list[ChatMessage] | list[dict[str, str]],
    ) -> list[dict[str, str]]:
        """
        Приводит список сообщений к формату OpenAI.

        Принимает либо список ChatMessage, либо список словарей.
        На выходе — всегда список словарей {"role", "content"}.
        """
        result: list[dict[str, str]] = []
        for msg in messages:
            if isinstance(msg, ChatMessage):
                result.append(msg.to_dict())
            elif isinstance(msg, dict):
                result.append({
                    "role": str(msg.get("role", "user")),
                    "content": str(msg.get("content", "")),
                })
            else:
                # Неизвестный формат — превращаем в строку.
                result.append({"role": "user", "content": str(msg)})
        return result

    # -------------------------------------------------------------------------
    #  Представление
    # -------------------------------------------------------------------------

    def __repr__(self) -> str:
        """Строковое представление для отладки."""
        return (
            f"<{self.__class__.__name__} "
            f"name={self.name!r} "
            f"model={self.get_model()!r} "
            f"available={self.is_available()}>"
        )


# =============================================================================
#  ЭКСПОРТ
# =============================================================================

__all__ = [
    # Данные
    "ChatMessage",
    "ProviderResponse",
    # Провайдеры
    "LLMProvider",
    # Исключения
    "ProviderError",
    "ProviderAuthError",
    "ProviderRateLimitError",
    "ProviderServerError",
    "ProviderNetworkError",
    "ProviderNotConfiguredError",
]