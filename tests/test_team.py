# =============================================================================
#  Codermuks in Termux — тесты для core/team/ v1.1.0
# =============================================================================
#  Что проверяем:
#    • AgentInfo и AgentRegistry;
#    • ленивое создание провайдеров с кэшем;
#    • get_lead()/set_lead() и дефолт Mistral;
#    • проверку готовности агента (is_configured);
#    • FallbackManager — выбор альтернативы, отказ от зацикливания;
#    • поведение при ошибках в TeamLead.
# =============================================================================

from __future__ import annotations

import pytest


# =============================================================================
#  AGENT INFO
# =============================================================================

class TestAgentInfo:
    """Тесты структуры AgentInfo."""

    def test_create(self):
        """Создание AgentInfo со всеми полями."""
        from core.team.agent_registry import AgentInfo
        info = AgentInfo(
            name="mistral",
            display_name="Mistral AI",
            description_key="agent.mistral.desc",
            default_model="mistral-large-latest",
            order=1,
            is_default_lead=True,
        )
        assert info.name == "mistral"
        assert info.order == 1
        assert info.is_default_lead is True

    def test_default_is_default_lead_false(self):
        """По умолчанию is_default_lead=False."""
        from core.team.agent_registry import AgentInfo
        info = AgentInfo(
            name="qwen",
            display_name="Qwen",
            description_key="agent.qwen.desc",
            default_model="qwen3-coder-plus",
            order=2,
        )
        assert info.is_default_lead is False


# =============================================================================
#  AGENT REGISTRY
# =============================================================================

class TestAgentRegistry:
    """Тесты реестра агентов."""

    def test_registry_has_four_agents(self, reset_registry, clean_config):
        """Реестр содержит 4 агента по умолчанию."""
        from core.team import get_registry
        registry = get_registry()
        assert len(registry.list_all()) == 4

    def test_registry_agent_names(self, reset_registry, clean_config):
        """Имена агентов: mistral, qwen, deepseek, openrouter."""
        from core.team import get_registry
        registry = get_registry()
        names = registry.list_names()
        assert "mistral" in names
        assert "qwen" in names
        assert "deepseek" in names
        assert "openrouter" in names

    def test_agents_sorted_by_order(self, reset_registry, clean_config):
        """Агенты возвращаются в порядке order."""
        from core.team import get_registry
        registry = get_registry()
        agents = registry.list_all()
        orders = [a.order for a in agents]
        assert orders == sorted(orders)

    def test_get_info_existing(self, reset_registry, clean_config):
        """get_info('mistral') возвращает метаданные."""
        from core.team import get_registry
        registry = get_registry()
        info = registry.get_info("mistral")
        assert info is not None
        assert info.name == "mistral"

    def test_get_info_unknown(self, reset_registry, clean_config):
        """get_info('nonexistent') возвращает None."""
        from core.team import get_registry
        registry = get_registry()
        assert registry.get_info("nonexistent") is None

    def test_has_agent(self, reset_registry, clean_config):
        """has() возвращает True/False."""
        from core.team import get_registry
        registry = get_registry()
        assert registry.has("mistral") is True
        assert registry.has("nonexistent") is False

    def test_is_configured_false_without_keys(self, reset_registry, clean_config, clean_keys):
        """Без ключей ни один агент не настроен."""
        from core.team import get_registry
        registry = get_registry()
        for name in registry.list_names():
            assert registry.is_configured(name) is False

    def test_is_configured_true_with_key(self, reset_registry, config_with_mistral_key):
        """С ключом Mistral настроен."""
        from core.team import get_registry
        registry = get_registry()
        assert registry.is_configured("mistral") is True
        assert registry.is_configured("qwen") is False

    def test_list_configured_only_mistral(self, reset_registry, config_with_mistral_key):
        """list_configured() возвращает только настроенных."""
        from core.team import get_registry
        registry = get_registry()
        configured = registry.list_configured()
        names = [a.name for a in configured]
        assert "mistral" in names
        assert "qwen" not in names


# =============================================================================
#  ПРОВАЙДЕРЫ В РЕЕСТРЕ
# =============================================================================

class TestRegistryProviders:
    """Тесты создания провайдеров через реестр."""

    def test_get_provider_mistral(self, reset_registry, clean_config):
        """get_provider('mistral') возвращает MistralProvider."""
        from core.team import get_registry
        from core.llm_providers.mistral_provider import MistralProvider
        registry = get_registry()
        p = registry.get_provider("mistral")
        assert isinstance(p, MistralProvider)

    def test_get_provider_unknown_raises(self, reset_registry, clean_config):
        """get_provider с неизвестным именем выбрасывает ValueError."""
        from core.team import get_registry
        registry = get_registry()
        with pytest.raises(ValueError):
            registry.get_provider("nonexistent")

    def test_provider_cached(self, reset_registry, clean_config):
        """Повторный get_provider возвращает тот же объект."""
        from core.team import get_registry
        registry = get_registry()
        p1 = registry.get_provider("mistral")
        p2 = registry.get_provider("mistral")
        assert p1 is p2

    def test_reset_provider_cache(self, reset_registry, clean_config):
        """reset_provider_cache() пересоздаёт провайдеров."""
        from core.team import get_registry
        registry = get_registry()
        p1 = registry.get_provider("mistral")
        registry.reset_provider_cache()
        p2 = registry.get_provider("mistral")
        assert p1 is not p2


# =============================================================================
#  LEAD
# =============================================================================

class TestRegistryLead:
    """Тесты работы с главным агентом через реестр."""

    def test_default_lead(self, reset_registry, clean_config):
        """По умолчанию главный агент — mistral."""
        from core.team import get_registry
        registry = get_registry()
        assert registry.get_lead() == "mistral"

    def test_set_lead_configured(self, reset_registry, config_with_mistral_key):
        """set_lead работает для настроенного агента."""
        from core.team import get_registry
        registry = get_registry()
        # mistral настроен (есть ключ).
        registry.set_lead("mistral")
        assert registry.get_lead() == "mistral"

    def test_set_lead_not_configured_raises(self, reset_registry, clean_config, clean_keys):
        """set_lead на ненастроенного агента выбрасывает ValueError."""
        from core.team import get_registry
        registry = get_registry()
        with pytest.raises(ValueError):
            registry.set_lead("qwen")

    def test_set_lead_unknown_raises(self, reset_registry, clean_config):
        """set_lead с неизвестным именем — ValueError."""
        from core.team import get_registry
        registry = get_registry()
        with pytest.raises(ValueError):
            registry.set_lead("nonexistent")

    def test_get_lead_info(self, reset_registry, clean_config):
        """get_lead_info() возвращает AgentInfo текущего лидера."""
        from core.team import get_registry
        registry = get_registry()
        info = registry.get_lead_info()
        assert info is not None
        assert info.name == "mistral"


# =============================================================================
#  SUMMARY
# =============================================================================

class TestRegistrySummary:
    """Тесты сводки реестра."""

    def test_summary_has_required_fields(self, reset_registry, clean_config):
        """summary() содержит нужные поля."""
        from core.team import get_registry
        registry = get_registry()
        s = registry.summary()
        assert "total" in s
        assert "configured" in s
        assert "lead" in s
        assert "agents" in s
        assert s["total"] == 4

    def test_summary_configured_count(self, reset_registry, config_with_mistral_key):
        """summary() правильно считает настроенных."""
        from core.team import get_registry
        registry = get_registry()
        s = registry.summary()
        assert s["configured"] == 1  # только mistral

    def test_summary_lead(self, reset_registry, clean_config):
        """summary() показывает текущего лидера."""
        from core.team import get_registry
        registry = get_registry()
        s = registry.summary()
        assert s["lead"] == "mistral"


# =============================================================================
#  SINGLETON
# =============================================================================

class TestSingleton:
    """Тесты singleton-поведения get_registry()."""

    def test_get_registry_returns_same_object(self, reset_registry, clean_config):
        """get_registry() возвращает один и тот же объект."""
        from core.team import get_registry
        r1 = get_registry()
        r2 = get_registry()
        assert r1 is r2

    def test_reset_registry_creates_new(self, reset_registry, clean_config):
        """reset_registry() создаёт новый объект при следующем вызове."""
        from core.team import get_registry, reset_registry
        r1 = get_registry()
        reset_registry()
        r2 = get_registry()
        assert r1 is not r2


# =============================================================================
#  FALLBACK MANAGER
# =============================================================================

class TestFallbackManager:
    """Тесты FallbackManager."""

    def test_init_marks_current_failed(self):
        """При инициализации текущий агент помечается как упавший."""
        from core.team.fallback import FallbackManager
        fb = FallbackManager(current="qwen")
        assert "qwen" in fb._failed

    def test_chain_starts_with_current(self, clean_config):
        """get_chain() начинается с текущего агента."""
        from core.team.fallback import FallbackManager
        fb = FallbackManager(current="qwen")
        chain = fb.get_chain()
        assert chain[0] == "qwen"

    def test_chain_no_duplicates(self, clean_config):
        """get_chain() не содержит дубликатов."""
        from core.team.fallback import FallbackManager
        fb = FallbackManager(current="deepseek")
        chain = fb.get_chain()
        assert len(chain) == len(set(chain))

    def test_alternatives_with_one_key(self, config_with_mistral_key):
        """Если настроен только Mistral и он упал — альтернатив нет."""
        from core.team.fallback import FallbackManager
        fb = FallbackManager(current="mistral")
        # Mistral настроен, но он упал → его исключаем.
        # Остальные (qwen, deepseek, openrouter) — без ключей.
        assert fb.list_available_alternatives() == []
        assert fb.pick_alternative() is None

    def test_alternatives_with_two_keys(self, user_dir):
        """Если настроены 2 агента, один упал — второй предложен."""
        import json
        from core import config

        # Пишем config с двумя ключами.
        config_data = {
            "version": "1.1.0",
            "language": "en",
            "team_lead": "mistral",
            "fallback_order": ["mistral", "qwen"],
            "providers": {
                "mistral": {"enabled": True, "model": "m", "base_url": "u", "api_key": ""},
                "qwen": {"enabled": True, "model": "q", "base_url": "u", "api_key": ""},
            },
        }
        config.CONFIG_FILE.write_text(
            json.dumps(config_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (user_dir / "key.txt").write_text(
            json.dumps({
                "mistral": "sk-test-m",
                "qwen": "sk-test-q",
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        config.reload()

        from core.team.fallback import FallbackManager
        fb = FallbackManager(current="mistral")
        alts = fb.list_available_alternatives()
        assert "qwen" in alts
        assert fb.pick_alternative() == "qwen"

    def test_no_looping(self, user_dir):
        """После двух падений альтернатив нет — не зацикливаемся."""
        import json
        from core import config

        config_data = {
            "version": "1.1.0",
            "team_lead": "mistral",
            "fallback_order": ["mistral", "qwen"],
            "providers": {
                "mistral": {"enabled": True, "model": "m", "base_url": "u", "api_key": ""},
                "qwen": {"enabled": True, "model": "q", "base_url": "u", "api_key": ""},
            },
        }
        config.CONFIG_FILE.write_text(
            json.dumps(config_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (user_dir / "key.txt").write_text(
            json.dumps({"mistral": "k1", "qwen": "k2"}, ensure_ascii=False),
            encoding="utf-8",
        )
        config.reload()

        from core.team.fallback import FallbackManager
        fb = FallbackManager(current="mistral")
        # Первый вызов — qwen.
        assert fb.pick_alternative() == "qwen"
        # Помечаем qwen как упавшего.
        fb.mark_failed("qwen")
        # Теперь альтернатив нет.
        assert fb.pick_alternative() is None

    def test_on_switch_callback_yes(self, user_dir):
        """Если on_switch возвращает True — переключаемся."""
        import json
        from core import config

        config_data = {
            "version": "1.1.0",
            "team_lead": "mistral",
            "fallback_order": ["mistral", "qwen"],
            "providers": {
                "mistral": {"enabled": True, "model": "m", "base_url": "u", "api_key": ""},
                "qwen": {"enabled": True, "model": "q", "base_url": "u", "api_key": ""},
            },
        }
        config.CONFIG_FILE.write_text(
            json.dumps(config_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (user_dir / "key.txt").write_text(
            json.dumps({"mistral": "k1", "qwen": "k2"}, ensure_ascii=False),
            encoding="utf-8",
        )
        config.reload()

        from core.team.fallback import FallbackManager
        calls = []

        def on_switch(old, new):
            calls.append((old, new))
            return True

        fb = FallbackManager(current="mistral", on_switch=on_switch)
        result = fb.pick_alternative()
        assert result == "qwen"
        assert calls == [("mistral", "qwen")]

    def test_on_switch_callback_no(self, user_dir):
        """Если on_switch возвращает False — не переключаемся."""
        import json
        from core import config

        config_data = {
            "version": "1.1.0",
            "team_lead": "mistral",
            "fallback_order": ["mistral", "qwen"],
            "providers": {
                "mistral": {"enabled": True, "model": "m", "base_url": "u", "api_key": ""},
                "qwen": {"enabled": True, "model": "q", "base_url": "u", "api_key": ""},
            },
        }
        config.CONFIG_FILE.write_text(
            json.dumps(config_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (user_dir / "key.txt").write_text(
            json.dumps({"mistral": "k1", "qwen": "k2"}, ensure_ascii=False),
            encoding="utf-8",
        )
        config.reload()

        from core.team.fallback import FallbackManager
        fb = FallbackManager(current="mistral", on_switch=lambda old, new: False)
        assert fb.pick_alternative() is None

    def test_state_dict(self, reset_registry, clean_config):
        """state() возвращает словарь с нужными полями."""
        from core.team.fallback import FallbackManager
        fb = FallbackManager(current="mistral")
        s = fb.state()
        assert "current" in s
        assert "failed" in s
        assert "chain" in s
        assert "alternatives" in s
        assert s["current"] == "mistral"

    def test_reset(self):
        """reset() очищает список упавших, оставляя текущего."""
        from core.team.fallback import FallbackManager
        fb = FallbackManager(current="mistral")
        fb.mark_failed("qwen")
        fb.mark_failed("deepseek")
        assert len(fb._failed) == 3
        fb.reset()
        assert fb._failed == {"mistral"}


# =============================================================================
#  ПАКЕТНЫЙ ЭКСПОРТ
# =============================================================================

class TestPackageExport:
    """Тесты публичного API пакета core.team."""

    def test_imports_from_package(self):
        """Все ключевые классы доступны из core.team."""
        from core.team import (
            AgentInfo,
            AgentRegistry,
            get_registry,
            reset_registry,
            get_team_lead_class,
            get_fallback_manager_class,
        )
        assert AgentInfo is not None
        assert AgentRegistry is not None
        assert callable(get_registry)
        assert callable(reset_registry)
        assert callable(get_team_lead_class)
        assert callable(get_fallback_manager_class)

    def test_team_lead_class_lazy_load(self):
        """get_team_lead_class() возвращает класс TeamLead."""
        from core.team import get_team_lead_class
        cls = get_team_lead_class()
        assert cls.__name__ == "TeamLead"

    def test_fallback_manager_class_lazy_load(self):
        """get_fallback_manager_class() возвращает класс FallbackManager."""
        from core.team import get_fallback_manager_class
        cls = get_fallback_manager_class()
        assert cls.__name__ == "FallbackManager"