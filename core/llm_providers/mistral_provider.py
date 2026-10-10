# =============================================================================
#  Codermuks in Termux — провайдер Mistral v1.1.0
# =============================================================================
#  Mistral — главный агент команды по умолчанию.
#
#  API: https://api.mistral.ai/v1
#  Модели:
#      • mistral-large-latest  — самая умная, для планирования и анализа
#      • codestral-latest      — специально для кода
#      • mistral-small-latest  — быстрая, для простых задач
#
#  Документация: https://docs.mistral.ai/
#  Ключи: https://console.mistral.ai/api-keys
#
#  Вся логика HTTP-запросов — в OpenAICompatibleProvider. Здесь только
#  метаданные провайдера.
# =============================================================================

from __future__ import annotations

from core.llm_providers.openai_compatible import OpenAICompatibleProvider


# =============================================================================
#  ПРОВАЙДЕР
# =============================================================================

class MistralProvider(OpenAICompatibleProvider):
    """
    Провайдер Mistral AI.

    Наследует всю работу с HTTP от OpenAICompatibleProvider.
    Переопределяет только метаданные — имя, отображаемое имя
    и модель по умолчанию.
    """

    name: str = "mistral"
    display_name: str = "Mistral AI"
    default_model: str = "mistral-large-latest"


# =============================================================================
#  ЭКСПОРТ
# =============================================================================

__all__ = ["MistralProvider"]