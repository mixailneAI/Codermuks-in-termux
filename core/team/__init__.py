# =============================================================================
#  Codermuks in Termux — пакет команды агентов v1.1.0
# =============================================================================
#  Этот пакет отвечает за мультиагентную систему Codermuks.
#
#  Что здесь есть:
#    • agent_registry.py — реестр всех агентов команды (Mistral, Qwen,
#                          DeepSeek, OpenRouter);
#    • team_lead.py      — главный агент, координирующий работу;
#    • fallback.py       — переключение между агентами при сбоях.
#
#  Как это работает:
#    1. Пользователь запускает codermuks.
#    2. TeamLead читает из config.json, какой агент сейчас главный.
#    3. На каждый запрос TeamLead выбирает нужного специалиста из реестра.
#    4. Если главный агент падает — срабатывает fallback.
#
#  Пример:
#      from core.team import TeamLead, get_registry
#      lead = TeamLead()
#      result = lead.solve("напиши HTTP-сервер на Go")
# =============================================================================

from __future__ import annotations

from core.team.agent_registry import (
    AgentInfo,
    AgentRegistry,
    get_registry,
    reset_registry,
)


# =============================================================================
#  ЛЕНИВЫЙ ИМПОРТ TeamLead И FallbackManager
# =============================================================================
#  Импортируем их не сразу, а через обёртки — чтобы избежать циклических
#  зависимостей: team_lead.py импортирует agent_registry, а agent_registry
#  не должен импортировать team_lead.
# =============================================================================

def get_team_lead_class():
    """
    Возвращает класс TeamLead. Загружает его лениво.

    Такой подход нужен для избежания циклического импорта:
    team_lead.py импортирует agent_registry.py, поэтому agent_registry
    не может импортировать team_lead на уровне модуля.
    """
    from core.team.team_lead import TeamLead
    return TeamLead


def get_fallback_manager_class():
    """
    Возвращает класс FallbackManager. Загружает его лениво.
    """
    from core.team.fallback import FallbackManager
    return FallbackManager


# =============================================================================
#  ЭКСПОРТ
# =============================================================================

__all__ = [
    # Данные
    "AgentInfo",
    # Реестр
    "AgentRegistry",
    "get_registry",
    "reset_registry",
    # Ленивые геттеры классов
    "get_team_lead_class",
    "get_fallback_manager_class",
]