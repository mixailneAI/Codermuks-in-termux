# =============================================================================
#  Codermuks in Termux — тесты для core/config.py v1.1.0
# =============================================================================
#  Что проверяем:
#    • создание директорий и файлов по умолчанию;
#    • чтение и сохранение config.json;
#    • работу с языком (get/set language);
#    • работу с главным агентом (get/set team_lead);
#    • порядок fallback (get_fallback_order);
#    • чтение API-ключей из key.txt;
#    • проверку готовности провайдеров (is_provider_configured);
#    • миграцию config.json.
# =============================================================================

from __future__ import annotations

import json
from pathlib import Path

import pytest


# =============================================================================
#  ДИРЕКТОРИИ И ФАЙЛЫ
# =============================================================================

class TestEnsureDirs:
    """Тесты создания директорий."""

    def test_creates_user_dir(self, isolated_user_dir):
        """ensure_dirs() создаёт ~/.codermuks/."""
        from core import config
        config.ensure_dirs()

        assert config.USER_DIR.exists()
        assert config.USER_DIR.is_dir()

    def test_creates_artifacts_dir(self, isolated_user_dir):
        """ensure_dirs() создаёт ~/.codermuks/artifacts/."""
        from core import config
        config.ensure_dirs()

        assert config.ARTIFACTS_DIR.exists()

    def test_creates_temp_dir(self, isolated_user_dir):
        """ensure_dirs() создаёт ~/.codermuks/temp/."""
        from core import config
        config.ensure_dirs()

        assert config.TEMP_DIR.exists()

    def test_idempotent(self, isolated_user_dir):
        """Повторный вызов ensure_dirs() не падает."""
        from core import config
        config.ensure_dirs()
        config.ensure_dirs()
        config.ensure_dirs()

        assert config.USER_DIR.exists()


# =============================================================================
#  ЯЗЫК
# =============================================================================

class TestLanguage:
    """Тесты работы с языком интерфейса."""

    def test_default_language_is_none(self, clean_config):
        """При первом запуске язык не выбран — get_language возвращает None."""
        from core import config
        assert config.get_language() is None

    def test_set_language_en(self, clean_config):
        """set_language('en') сохраняет английский."""
        from core import config
        config.set_language("en")
        assert config.get_language() == "en"

    def test_set_language_ru(self, clean_config):
        """set_language('ru') сохраняет русский."""
        from core import config
        config.set_language("ru")
        assert config.get_language() == "ru"

    def test_set_language_invalid(self, clean_config):
        """set_language('de') выбрасывает ValueError."""
        from core import config
        with pytest.raises(ValueError):
            config.set_language("de")

    def test_set_language_persists(self, clean_config):
        """Язык сохраняется на диск и переживает перезагрузку модуля."""
        from core import config
        config.set_language("ru")

        # Читаем файл напрямую.
        raw = json.loads(config.CONFIG_FILE.read_text(encoding="utf-8"))
        assert raw["language"] == "ru"

    def test_supported_languages_list(self):
        """Список поддерживаемых языков содержит en и ru."""
        from core import config
        assert "en" in config.SUPPORTED_LANGUAGES
        assert "ru" in config.SUPPORTED_LANGUAGES


# =============================================================================
#  ГЛАВНЫЙ АГЕНТ
# =============================================================================

class TestTeamLead:
    """Тесты работы с главным агентом (team_lead)."""

    def test_default_lead_is_mistral(self, clean_config):
        """По умолчанию главный агент — Mistral."""
        from core import config
        assert config.get_team_lead() == "mistral"

    def test_set_lead_qwen(self, clean_config):
        """set_team_lead('qwen') сохраняет Qwen."""
        from core import config
        config.set_team_lead("qwen")
        assert config.get_team_lead() == "qwen"

    def test_set_lead_invalid(self, clean_config):
        """set_team_lead('unknown') выбрасывает ValueError."""
        from core import config
        with pytest.raises(ValueError):
            config.set_team_lead("unknown")

    def test_lead_persists_to_file(self, clean_config):
        """team_lead сохраняется в config.json."""
        from core import config
        config.set_team_lead("deepseek")

        raw = json.loads(config.CONFIG_FILE.read_text(encoding="utf-8"))
        assert raw["team_lead"] == "deepseek"

    def test_lead_unknown_falls_back(self, clean_config):
        """Если в config.json указан незнакомый агент — возвращается дефолт."""
        from core import config

        # Вручную портим config.json.
        data = json.loads(config.CONFIG_FILE.read_text(encoding="utf-8"))
        data["team_lead"] = "nonexistent"
        config.CONFIG_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        config.reload()

        assert config.get_team_lead() == "mistral"


# =============================================================================
#  FALLBACK ORDER
# =============================================================================

class TestFallbackOrder:
    """Тесты порядка fallback."""

    def test_default_order(self, clean_config):
        """Порядок по умолчанию содержит все 4 агента."""
        from core import config
        order = config.get_fallback_order()

        assert order[0] == "mistral"  # текущий lead — первый
        assert "qwen" in order
        assert "deepseek" in order
        assert "openrouter" in order

    def test_lead_is_first(self, clean_config):
        """Главный агент всегда первый в списке fallback."""
        from core import config
        config.set_team_lead("qwen")

        order = config.get_fallback_order()
        assert order[0] == "qwen"

    def test_no_duplicates(self, clean_config):
        """Порядок fallback не содержит дубликатов."""
        from core import config
        order = config.get_fallback_order()
        assert len(order) == len(set(order))

    def test_missing_providers_added(self, clean_config):
        """Если в config.json не хватает агентов — они добавляются."""
        from core import config

        # Убираем часть из fallback_order.
        data = json.loads(config.CONFIG_FILE.read_text(encoding="utf-8"))
        data["fallback_order"] = ["mistral"]
        config.CONFIG_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        config.reload()

        order = config.get_fallback_order()
        assert "qwen" in order
        assert "deepseek" in order
        assert "openrouter" in order


# =============================================================================
#  ПРОВАЙДЕРЫ
# =============================================================================

class TestProviders:
    """Тесты работы с провайдерами."""

    def test_all_providers_present(self, clean_config):
        """Все 4 провайдера присутствуют в config.json."""
        from core import config
        providers = config.get_all_providers()

        assert "mistral" in providers
        assert "qwen" in providers
        assert "deepseek" in providers
        assert "openrouter" in providers

    def test_get_provider(self, clean_config):
        """get_provider('mistral') возвращает словарь с настройками."""
        from core import config
        provider = config.get_provider("mistral")

        assert provider is not None
        assert provider["model"] == "mistral-large-latest"
        assert provider["base_url"] == "https://api.mistral.ai/v1"

    def test_get_unknown_provider(self, clean_config):
        """get_provider('nonexistent') возвращает None."""
        from core import config
        assert config.get_provider("nonexistent") is None

    def test_is_provider_enabled(self, clean_config):
        """Все провайдеры включены по умолчанию."""
        from core import config
        for name in ("mistral", "qwen", "deepseek", "openrouter"):
            assert config.is_provider_enabled(name) is True

    def test_is_provider_enabled_unknown(self, clean_config):
        """Неизвестный провайдер — не enabled."""
        from core import config
        assert config.is_provider_enabled("unknown") is False


# =============================================================================
#  API-КЛЮЧИ
# =============================================================================

class TestApiKeys:
    """Тесты чтения API-ключей."""

    def test_empty_keys_by_default(self, clean_config, clean_keys):
        """По умолчанию все ключи пустые."""
        from core import config
        for name in ("mistral", "qwen", "deepseek", "openrouter"):
            assert config.get_api_key(name) == ""

    def test_reads_mistral_key(self, config_with_mistral_key):
        """Ключ Mistral читается из key.txt."""
        from core import config
        assert config.get_api_key("mistral") == "sk-test-fake-key-for-unit-tests"

    def test_other_keys_empty(self, config_with_mistral_key):
        """Остальные ключи — пустые."""
        from core import config
        assert config.get_api_key("qwen") == ""
        assert config.get_api_key("deepseek") == ""
        assert config.get_api_key("openrouter") == ""

    def test_missing_key_file(self, clean_config):
        """Если key.txt нет — ключи пустые, не падаем."""
        from core import config
        # Не создаём key.txt.
        assert config.get_api_key("mistral") == ""

    def test_broken_key_file(self, clean_config, user_dir):
        """Если key.txt — не JSON, ключи пустые, не падаем."""
        from core import config
        (user_dir / "key.txt").write_text("not a json", encoding="utf-8")
        config.reload()
        assert config.get_api_key("mistral") == ""

    def test_env_var_fallback(self, clean_config, monkeypatch):
        """Если ключа нет в файле — берётся из переменной окружения."""
        from core import config
        monkeypatch.setenv("MISTRAL_API_KEY", "sk-env-var-key")
        config.reload()
        assert config.get_api_key("mistral") == "sk-env-var-key"


# =============================================================================
#  ГОТОВНОСТЬ ПРОВАЙДЕРА
# =============================================================================

class TestProviderConfigured:
    """Тесты проверки готовности провайдера."""

    def test_not_configured_without_key(self, clean_config, clean_keys):
        """Без ключа провайдер не готов."""
        from core import config
        assert config.is_provider_configured("mistral") is False

    def test_configured_with_key(self, config_with_mistral_key):
        """С ключом провайдер готов."""
        from core import config
        assert config.is_provider_configured("mistral") is True

    def test_not_configured_unknown(self, clean_config):
        """Неизвестный провайдер — не готов."""
        from core import config
        assert config.is_provider_configured("unknown") is False

    def test_not_configured_when_disabled(self, config_with_mistral_key):
        """Если enabled=False — провайдер не готов, даже с ключом."""
        from core import config

        data = json.loads(config.CONFIG_FILE.read_text(encoding="utf-8"))
        data["providers"]["mistral"]["enabled"] = False
        config.CONFIG_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        config.reload()

        assert config.is_provider_configured("mistral") is False


# =============================================================================
#  МИГРАЦИЯ
# =============================================================================

class TestMigration:
    """Тесты миграции config.json."""

    def test_migrate_adds_missing_fields(self, clean_config):
        """migrate_config_file() дополняет отсутствующие поля."""
        from core import config

        # Вручную портим config — убираем часть полей.
        data = json.loads(config.CONFIG_FILE.read_text(encoding="utf-8"))
        del data["fallback_order"]
        del data["providers"]["qwen"]
        config.CONFIG_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        config.reload()

        config.migrate_config_file()
        config.reload()

        new_data = json.loads(config.CONFIG_FILE.read_text(encoding="utf-8"))
        assert "fallback_order" in new_data
        assert "qwen" in new_data["providers"]

    def test_migrate_preserves_user_settings(self, config_with_mistral_key):
        """migrate_config_file() не трогает существующие настройки."""
        from core import config

        config.set_language("ru")
        config.migrate_config_file()
        config.reload()

        assert config.get_language() == "ru"

    def test_broken_json_recreated(self, clean_config):
        """Повреждённый JSON пересоздаётся при чтении."""
        from core import config

        config.CONFIG_FILE.write_text("{ broken json", encoding="utf-8")
        config.reload()

        # Первое чтение пересоздаёт файл.
        lead = config.get_team_lead()
        assert lead == "mistral"

        # И файл стал валидным JSON.
        raw = config.CONFIG_FILE.read_text(encoding="utf-8")
        data = json.loads(raw)
        assert data["team_lead"] == "mistral"


# =============================================================================
#  ОКРУЖЕНИЕ
# =============================================================================

class TestEnvironment:
    """Тесты определения окружения."""

    def test_is_termux_returns_bool(self):
        """is_termux() возвращает True или False."""
        from core import config
        result = config.is_termux()
        assert isinstance(result, bool)

    def test_get_python_executable(self):
        """get_python_executable() возвращает путь к Python."""
        from core import config
        path = config.get_python_executable()
        assert isinstance(path, str)
        assert len(path) > 0