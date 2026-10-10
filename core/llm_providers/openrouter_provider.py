# =============================================================================
#  Codermuks in Termux — провайдер OpenRouter v1.1.0
# =============================================================================
#  OpenRouter — агрегатор, дающий доступ к десяткам моделей от разных
#  провайдеров через один API. Особенно полезен для бесплатных моделей,
#  у которых в имени есть суффикс ":free".
#
#  API: https://openrouter.ai/api/v1
#  Модели (бесплатные, работают через :free):
#      • qwen/qwen3-coder:free
#      • meta-llama/llama-3.3-70b-instruct:free
#      • google/gemini-2.0-flash-exp:free
#      • deepseek/deepseek-r1:free
#      • mistralai/mistral-7b-instruct:free
#
#  Документация: https://openrouter.ai/docs
#  Ключи: https://openrouter.ai/keys
#
#  Бесплатно: 50 запросов в день на бесплатные модели.
#  Работает из России: без VPN.
#
#  ОСОБЕННОСТЬ: OpenRouter требует два дополнительных HTTP-заголовка
#  для аналитики — HTTP-Referer и X-Title. Если их не передать,
#  запрос всё равно пройдёт, но мы их добавляем для корректности.
# =============================================================================

from __future__ import annotations

from core.llm_providers.openai_compatible import OpenAICompatibleProvider


# =============================================================================
#  ПРОВАЙДЕР
# =============================================================================

class OpenRouterProvider(OpenAICompatibleProvider):
    """
    Провайдер OpenRouter.

    Наследует всю работу с HTTP от OpenAICompatibleProvider.
    Переопределяет метаданные и добавляет два обязательных заголовка
    для аналитики OpenRouter.
    """

    name: str = "openrouter"
    display_name: str = "OpenRouter"
    default_model: str = "qwen/qwen3-coder:free"

    def extra_headers(self) -> dict[str, str]:
        """
        Дополнительные заголовки, которые требует OpenRouter.

        HTTP-Referer — URL проекта. Используется в аналитике
            OpenRouter, чтобы показать, откуда идут запросы.
        X-Title      — имя приложения. Показывается в дашборде
            OpenRouter как «кто использует мой ключ».

        Оба заголовка необязательны с точки зрения API, но
        рекомендуются документацией, поэтому мы их передаём.
        """
        return {
            "HTTP-Referer": "https://github.com/mixailneAI/Codermuks-in-termux",
            "X-Title": "Codermuks in Termux",
        }


# =============================================================================
#  ЭКСПОРТ
# =============================================================================

__all__ = ["OpenRouterProvider"]