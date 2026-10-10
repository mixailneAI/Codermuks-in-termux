# =============================================================================
#  Codermuks in Termux — реестр агентов команды v1.1.0
# =============================================================================
#  Что делает этот модуль:
#    • хранит информацию о всех агентах команды (Mistral, Qwen,
#      DeepSeek, OpenRouter);
#    • умеет выдавать агента по имени;
#    • лениво создаёт и кэширует экземпляры провайдеров;
#    • проверяет, настроен ли агент (есть ли API-ключ);
#    • хранит текущего главного агента (team_lead);
#    • предоставляет списки для UI (/changeagent).
#
#  Ключевая идея: AgentInfo — это «паспорт» агента (имя, описание,
#  модель). Реальный провайдер создаётся лениво, только когда его
#  действительно позвали работать.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# =============================================================================
#  ОПИСАНИЕ АГЕНТА
# =============================================================================

@dataclass
class AgentInfo:
    """
    Метаданные одного агента команды.

    Поля:
        name            — короткое имя (ключ в config.json): "mistral"
        display_name    — красивое имя для UI: "Mistral AI"
        description_key — i18n-ключ описания: "agent.mistral.desc"
        default_model   — модель по умолчанию: "mistral-large-latest"
        order           — порядок в меню /changeagent (1, 2, 3, 4)
        is_default_lead — является ли агентом по умолчанию
    """
    name: str
    display_name: str
    description_key: str
    default_model: str
    order: int
    is_default_lead: bool = False


# =============================================================================
#  РЕЕСТР
# =============================================================================

class AgentRegistry:
    """
    Реестр всех агентов команды.

    Экземпляр создаётся один раз и живёт всё время работы приложения.
    Кэширует как метаданные (AgentInfo), так и реальных провайдеров
    (LLMProvider), чтобы не создавать их при каждом запросе.
    """

    def __init__(self) -> None:
        """Создаёт пустой реестр и регистрирует стандартных агентов."""
        # Метаданные агентов: имя → AgentInfo.
        self._agents: dict[str, AgentInfo] = {}

        # Кэш реальных провайдеров: имя → LLMProvider.
        # Заполняется лениво при первом обращении через get_provider().
        self._provider_cache: dict[str, Any] = {}

        # Регистрируем стандартных агентов.
        self._register_defaults()

    # -------------------------------------------------------------------------
    #  Регистрация
    # -------------------------------------------------------------------------

    def _register_defaults(self) -> None:
        """
        Регистрирует 4 стандартных агента команды.

        Порядок важен: он определяет, как агенты будут показаны
        в меню /changeagent.
        """
        defaults = [
            AgentInfo(
                name="mistral",
                display_name="Mistral AI",
                description_key="agent.mistral.desc",
                default_model="mistral-large-latest",
                order=1,
                is_default_lead=True,
            ),
            AgentInfo(
                name="qwen",
                display_name="Qwen Code",
                description_key="agent.qwen.desc",
                default_model="qwen3-coder-plus",
                order=2,
            ),
            AgentInfo(
                name="deepseek",
                display_name="DeepSeek",
                description_key="agent.deepseek.desc",
                default_model="deepseek-chat",
                order=3,
            ),
            AgentInfo(
                name="openrouter",
                display_name="OpenRouter",
                description_key="agent.openrouter.desc",
                default_model="qwen/qwen3-coder:free",
                order=4,
            ),
        ]

        for info in defaults:
            self._agents[info.name] = info

    def register(self, info: AgentInfo) -> None:
        """
        Регистрирует нового агента. Если агент с таким именем уже
        есть — перезаписывает его метаданные.
        """
        self._agents[info.name] = info

    # -------------------------------------------------------------------------
    #  Доступ к агентам
    # -------------------------------------------------------------------------

    def get_info(self, name: str) -> AgentInfo | None:
        """
        Возвращает метаданные агента по имени или None, если такого нет.
        """
        if not name:
            return None
        return self._agents.get(name.strip().lower())

    def list_all(self) -> list[AgentInfo]:
        """
        Возвращает список всех зарегистрированных агентов,
        отсортированный по полю order.
        """
        return sorted(self._agents.values(), key=lambda a: a.order)

    def list_configured(self) -> list[AgentInfo]:
        """
        Возвращает только тех агентов, у которых заполнен API-ключ.
        Именно их можно выбрать через /changeagent.
        """
        return [info for info in self.list_all() if self.is_configured(info.name)]

    def list_names(self) -> list[str]:
        """Возвращает список имён всех агентов в порядке order."""
        return [info.name for info in self.list_all()]

    def has(self, name: str) -> bool:
        """Проверяет, зарегистрирован ли агент с таким именем."""
        return bool(name) and name.strip().lower() in self._agents

    # -------------------------------------------------------------------------
    #  Проверка готовности
    # -------------------------------------------------------------------------

    def is_configured(self, name: str) -> bool:
        """
        Проверяет, настроен ли агент — есть ли у него API-ключ
        и включён ли он в config.json.
        """
        if not self.has(name):
            return False

        try:
            from core import config
            return bool(config.is_provider_configured(name.strip().lower()))
        except Exception:
            return False

    # -------------------------------------------------------------------------
    #  Провайдеры (ленивое создание)
    # -------------------------------------------------------------------------

    def get_provider(self, name: str) -> Any:
        """
        Возвращает экземпляр провайдера для указанного агента.

        Провайдер создаётся лениво при первом обращении и кэшируется.
        Если провайдер не зарегистрирован — поднимает ValueError.

        Исключения:
            ValueError — если агент с таким именем не зарегистрирован.
        """
        if not self.has(name):
            raise ValueError(
                f"Агент '{name}' не зарегистрирован. "
                f"Доступные: {', '.join(self.list_names())}"
            )

        key = name.strip().lower()

        # Если уже в кэше — возвращаем.
        if key in self._provider_cache:
            return self._provider_cache[key]

        # Создаём через фабрику llm_providers.
        from core.llm_providers import get_provider

        provider = get_provider(key)
        self._provider_cache[key] = provider
        return provider

    def reset_provider_cache(self) -> None:
        """
        Сбрасывает кэш провайдеров.

        Полезно, если пользователь сменил API-ключ или модель
        в config.json — тогда нужно пересоздать провайдеров,
        чтобы они перечитали настройки.
        """
        self._provider_cache.clear()

    # -------------------------------------------------------------------------
    #  Главный агент (team_lead)
    # -------------------------------------------------------------------------

    def get_lead(self) -> str:
        """
        Возвращает имя текущего главного агента.

        Читает из config.json (поле team_lead). Если там указан
        неизвестный агент — возвращает дефолт (Mistral).
        """
        try:
            from core import config
            lead = config.get_team_lead()
        except Exception:
            lead = ""

        if self.has(lead):
            return lead.strip().lower()

        # Фолбэк: первый агент с флагом is_default_lead.
        for info in self.list_all():
            if info.is_default_lead:
                return info.name

        # Совсем крайний случай — первый из списка.
        names = self.list_names()
        return names[0] if names else "mistral"

    def set_lead(self, name: str) -> None:
        """
        Устанавливает главного агента. Сохраняет выбор в config.json.

        Исключения:
            ValueError — если агент не зарегистрирован или не настроен.
        """
        if not self.has(name):
            raise ValueError(f"Агент '{name}' не зарегистрирован.")

        if not self.is_configured(name):
            raise ValueError(
                f"Агент '{name}' не настроен. "
                f"Добавь API-ключ в ~/.codermuks/key.txt."
            )

        from core import config
        config.set_team_lead(name.strip().lower())

    def get_lead_info(self) -> AgentInfo | None:
        """Возвращает метаданные текущего главного агента."""
        return self.get_info(self.get_lead())

    # -------------------------------------------------------------------------
    #  Служебные методы
    # -------------------------------------------------------------------------

    def summary(self) -> dict[str, Any]:
        """
        Возвращает сводку по реестру — удобно для отладки и логов.

        Формат:
            {
                "total": 4,
                "configured": 2,
                "lead": "mistral",
                "agents": [
                    {"name": "mistral", "configured": True, "is_lead": True},
                    ...
                ]
            }
        """
        agents = self.list_all()
        lead = self.get_lead()

        return {
            "total": len(agents),
            "configured": len(self.list_configured()),
            "lead": lead,
            "agents": [
                {
                    "name": info.name,
                    "display_name": info.display_name,
                    "configured": self.is_configured(info.name),
                    "is_lead": info.name == lead,
                }
                for info in agents
            ],
        }


# =============================================================================
#  ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР
# =============================================================================

_registry_instance: AgentRegistry | None = None


def get_registry() -> AgentRegistry:
    """
    Возвращает глобальный экземпляр реестра агентов.

    Создаётся при первом обращении и живёт всё время работы
    приложения. Все модули должны использовать именно эту функцию.
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = AgentRegistry()
    return _registry_instance


def reset_registry() -> None:
    """
    Сбрасывает глобальный реестр.

    Полезно при тестировании или если пользователь изменил
    config.json и хочет, чтобы изменения вступили в силу
    без перезапуска приложения.
    """
    global _registry_instance
    _registry_instance = None


# =============================================================================
#  ЭКСПОРТ
# =============================================================================

__all__ = [
    "AgentInfo",
    "AgentRegistry",
    "get_registry",
    "reset_registry",
]