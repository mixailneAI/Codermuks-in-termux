# =============================================================================
#  Codermuks in Termux — провайдер Qwen (Alibaba Cloud) v1.1.0
# =============================================================================
#  Qwen — второй агент команды. Специализируется на генерации кода:
#  модель qwen3-coder-plus показывает одни из лучших результатов
#  в задачах программирования.
#
#  API: https://dashscope.aliyuncs.com/compatible-mode/v1
#  Модели:
#      • qwen3-coder-plus   — специализированная модель для кода
#      • qwen3-coder-flash  — быстрая версия
#      • qwen-plus          — универсальная модель
#      • qwen-turbo         — самая быстрая
#
#  Документация: https://help.aliyun.com/zh/dashscope/
#  Ключи: https://dashscope.console.aliyun.com/apiKey
#
#  Бесплатно: 1000 запросов в день.
#  Работает из России: без VPN и без карты.
#
#  Вся логика HTTP-запросов — в OpenAICompatibleProvider.
# =============================================================================

from __future__ import annotations

from core.llm_providers.openai_compatible import OpenAICompatibleProvider


# =============================================================================
#  ПРОВАЙДЕР
# =============================================================================

class QwenProvider(OpenAICompatibleProvider):
    """
    Провайдер Qwen Code (Alibaba Cloud DashScope).

    Наследует всю работу с HTTP от OpenAICompatibleProvider.
    Переопределяет только метаданные.

    Особенность Qwen: DashScope предоставляет OpenAI-совместимый
    эндпоинт через префикс /compatible-mode. Именно его мы и указываем
    в config.json.
    """

    name: str = "qwen"
    display_name: str = "Qwen Code (Alibaba)"
    default_model: str = "qwen3-coder-plus"


# =============================================================================
#  ЭКСПОРТ
# =============================================================================

__all__ = ["QwenProvider"]