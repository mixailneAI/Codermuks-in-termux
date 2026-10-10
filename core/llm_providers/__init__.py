# =============================================================================
#  Codermuks in Termux — реестр LLM-провайдеров v1.1.0
# =============================================================================
#  Этот модуль — точка входа для всего пакета llm_providers.
#
#  Что здесь есть:
#    • реэкспорт базовых классов (LLMProvider, ChatMessage, ProviderResponse);
#    • функция get_provider(name) — фабрика, возвращающая нужный провайдер
#      по имени (mistral, qwen, deepseek, openrouter);
#    • список AVAILABLE_PROVIDERS — все зарегистрированные провайдеры;
#    • функция list_available() — возвращает список имён провайдеров;
#    • функция get_configured() — только те, у кого есть API-ключ.
#
#  Использование:
#      from core.llm_providers import get_provider
#      provider = get_provider("mistral")
#      response = provider.chat([{"role": "user", "content": "hello"}])
# =============================================================================

from __future__ import annotations

from typing import TYPE_CHECKING

from core.llm_providers.base import (
    ChatMessage,
    LLMProvider,
    ProviderResponse,
)

if TYPE_CHECKING:
    # Импорты только для аннотаций типов — не тянут зависимости в runtime.
    from core.llm_providers.mistral_provider import MistralProvider
    from core.llm_providers.qwen_provider import QwenProvider
    from core.llm_providers.deepseek_provider import DeepSeekProvider
    from core.llm_providers.openrouter_provider import OpenRouterProvider


# =============================================================================
#  СПИСОК ПОДДЕРЖИВАЕМЫХ ПРОВАЙДЕРОВ
# =============================================================================
#  Порядок важен: используется как порядок по умолчанию в меню
#  /changeagent и как fallback_order, если в config.json он не задан.
# =============================================================================

AVAILABLE_PROVIDERS: list[str] = [
    "mistral",
    "qwen",
    "deepseek",
    "openrouter",
]


# =============================================================================
#  ФАБРИКА ПРОВАЙДЕРОВ
# =============================================================================

def get_provider(name: str) -> LLMProvider:
    """
    Возвращает экземпляр провайдера по имени.

    Аргументы:
        name — одно из AVAILABLE_PROVIDERS: "mistral", "qwen",
               "deepseek", "openrouter".

    Возвращает:
        Экземпляр класса-наследника LLMProvider.

    Исключения:
        ValueError — если имя провайдера неизвестно.
        RuntimeError — если не удалось создать провайдер (нет ключа и т. п.).

    Пример:
        >>> p = get_provider("qwen")
        >>> p.name
        'qwen'
    """
    if not name:
        raise ValueError("Имя провайдера не задано.")

    key = name.strip().lower()

    # Импортируем провайдер только в момент обращения — так мы не тянем
    # все зависимости сразу при импорте пакета.
    if key == "mistral":
        from core.llm_providers.mistral_provider import MistralProvider
        return MistralProvider()

    if key == "qwen":
        from core.llm_providers.qwen_provider import QwenProvider
        return QwenProvider()

    if key == "deepseek":
        from core.llm_providers.deepseek_provider import DeepSeekProvider
        return DeepSeekProvider()

    if key == "openrouter":
        from core.llm_providers.openrouter_provider import OpenRouterProvider
        return OpenRouterProvider()

    raise ValueError(
        f"Неизвестный провайдер: {name}. "
        f"Доступные: {', '.join(AVAILABLE_PROVIDERS)}"
    )


# =============================================================================
#  СПИСКИ ДЛЯ UI
# =============================================================================

def list_available() -> list[str]:
    """
    Возвращает список имён всех зарегистрированных провайдеров.

    Используется в /changeagent, чтобы показать полный список.
    """
    return list(AVAILABLE_PROVIDERS)


def get_configured() -> list[str]:
    """
    Возвращает список провайдеров, у которых заполнен API-ключ
    и которые включены в config.json.

    Используется в /changeagent, чтобы помечать доступных агентов.

    При ошибке чтения config (например, до инициализации) — возвращает
    пустой список, чтобы UI просто показал всех как «не настроен».
    """
    try:
        from core import config
    except Exception:
        return []

    result: list[str] = []
    for name in AVAILABLE_PROVIDERS:
        try:
            if config.is_provider_configured(name):
                result.append(name)
        except Exception:
            continue
    return result


def is_configured(name: str) -> bool:
    """
    Проверяет, настроен ли конкретный провайдер.

    Обёртка над config.is_provider_configured() с защитой от исключений.
    """
    if name not in AVAILABLE_PROVIDERS:
        return False

    try:
        from core import config
        return config.is_provider_configured(name)
    except Exception:
        return False


# =============================================================================
#  ЭКСПОРТ
# =============================================================================

__all__ = [
    # Базовые классы
    "LLMProvider",
    "ChatMessage",
    "ProviderResponse",
    # Фабрика и списки
    "get_provider",
    "list_available",
    "get_configured",
    "is_configured",
    # Константы
    "AVAILABLE_PROVIDERS",
]