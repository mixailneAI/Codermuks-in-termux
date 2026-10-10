# =============================================================================
#  Codermuks in Termux — общие фикстуры pytest v1.1.0
# =============================================================================

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest


# --- Корень проекта в sys.path ---------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
#  ИЗОЛЯЦИЯ ПОЛЬЗОВАТЕЛЬСКОЙ ДИРЕКТОРИИ
# =============================================================================

@pytest.fixture(autouse=True)
def isolated_user_dir(tmp_path, monkeypatch):
    """
    Автоматически подменяет пути core.config на временную папку.

    Вместо подмены HOME (которое ненадёжно из-за кэша импортов)
    мы напрямую меняем атрибуты модуля config: USER_DIR, CONFIG_FILE,
    KEY_FILE, ARTIFACTS_DIR, TEMP_DIR. monkeypatch вернёт их обратно
    после теста автоматически.
    """
    fake_home = tmp_path / "home"
    fake_home.mkdir(parents=True, exist_ok=True)

    fake_user_dir = fake_home / ".codermuks"
    fake_user_dir.mkdir(parents=True, exist_ok=True)
    (fake_user_dir / "artifacts").mkdir(parents=True, exist_ok=True)
    (fake_user_dir / "temp").mkdir(parents=True, exist_ok=True)

    # Импортируем config и подменяем пути.
    from core import config

    monkeypatch.setattr(config, "USER_DIR", fake_user_dir, raising=False)
    monkeypatch.setattr(config, "CONFIG_FILE", fake_user_dir / "config.json", raising=False)
    monkeypatch.setattr(config, "KEY_FILE", fake_user_dir / "key.txt", raising=False)
    monkeypatch.setattr(config, "ARTIFACTS_DIR", fake_user_dir / "artifacts", raising=False)
    monkeypatch.setattr(config, "TEMP_DIR", fake_user_dir / "temp", raising=False)
    monkeypatch.setattr(config, "LOG_FILE", fake_home / ".codermuks.log", raising=False)

    # Сбрасываем кэш, чтобы config перечитал файлы.
    config.reload()

    yield fake_home

    # После теста тоже сброс — чтобы кэш не тянулся в следующий тест.
    config.reload()


# =============================================================================
#  ФИКСТУРЫ ДЛЯ ФАЙЛОВ
# =============================================================================

@pytest.fixture
def user_dir(isolated_user_dir):
    """Возвращает путь к фейковой ~/.codermuks/."""
    path = isolated_user_dir / ".codermuks"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture
def clean_config(user_dir):
    """Создаёт чистый config.json с дефолтами."""
    config_path = user_dir / "config.json"

    default_config = {
        "version": "1.1.0",
        "language": None,
        "team_lead": "mistral",
        "fallback_order": ["mistral", "qwen", "deepseek", "openrouter"],
        "providers": {
            "mistral": {
                "enabled": True,
                "model": "mistral-large-latest",
                "base_url": "https://api.mistral.ai/v1",
                "api_key": "",
            },
            "qwen": {
                "enabled": True,
                "model": "qwen3-coder-plus",
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "api_key": "",
            },
            "deepseek": {
                "enabled": True,
                "model": "deepseek-chat",
                "base_url": "https://api.deepseek.com/v1",
                "api_key": "",
            },
            "openrouter": {
                "enabled": True,
                "model": "qwen/qwen3-coder:free",
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": "",
            },
        },
    }

    config_path.write_text(
        json.dumps(default_config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    from core import config
    config.reload()

    return default_config


@pytest.fixture
def clean_keys(user_dir):
    """Создаёт чистый key.txt с пустыми ключами."""
    key_path = user_dir / "key.txt"

    default_keys = {
        "_readme": "Test fixture",
        "mistral": "",
        "qwen": "",
        "deepseek": "",
        "openrouter": "",
    }

    key_path.write_text(
        json.dumps(default_keys, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    from core import config
    config.reload()

    return default_keys


@pytest.fixture
def config_with_mistral_key(user_dir):
    """Создаёт config.json и key.txt с фейковым ключом Mistral."""
    config_path = user_dir / "config.json"
    key_path = user_dir / "key.txt"

    config_data = {
        "version": "1.1.0",
        "language": "en",
        "team_lead": "mistral",
        "fallback_order": ["mistral", "qwen", "deepseek", "openrouter"],
        "providers": {
            "mistral": {
                "enabled": True,
                "model": "mistral-large-latest",
                "base_url": "https://api.mistral.ai/v1",
                "api_key": "",
            },
            "qwen": {
                "enabled": True,
                "model": "qwen3-coder-plus",
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "api_key": "",
            },
            "deepseek": {
                "enabled": True,
                "model": "deepseek-chat",
                "base_url": "https://api.deepseek.com/v1",
                "api_key": "",
            },
            "openrouter": {
                "enabled": True,
                "model": "qwen/qwen3-coder:free",
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": "",
            },
        },
    }

    keys_data = {
        "mistral": "sk-test-fake-key-for-unit-tests",
        "qwen": "",
        "deepseek": "",
        "openrouter": "",
    }

    config_path.write_text(
        json.dumps(config_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    key_path.write_text(
        json.dumps(keys_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    from core import config
    config.reload()

    return {"config": config_data, "keys": keys_data}


# =============================================================================
#  ФИКСТУРЫ ДЛЯ СИНГЛТОНОВ
# =============================================================================

@pytest.fixture
def reset_registry():
    """Сбрасывает глобальный реестр агентов до и после теста."""
    try:
        from core.team import agent_registry
        agent_registry.reset_registry()
    except Exception:
        pass

    yield

    try:
        from core.team import agent_registry
        agent_registry.reset_registry()
    except Exception:
        pass


@pytest.fixture
def reset_translator():
    """Сбрасывает переводчик до и после теста."""
    try:
        from core.i18n import translator
        translator.init("en")
    except Exception:
        pass

    yield

    try:
        from core.i18n import translator
        translator.init("en")
    except Exception:
        pass


# =============================================================================
#  МОК-ПРОВАЙДЕР
# =============================================================================

class MockProvider:
    """Простой мок-провайдер для тестов. Не ходит в сеть."""

    def __init__(
        self,
        name: str = "mock",
        model: str = "mock-model",
        response_text: str = "```python\nprint('hello')\n```",
        should_raise: Exception | None = None,
    ) -> None:
        self.name = name
        self.display_name = name
        self.default_model = model
        self.response_text = response_text
        self.should_raise = should_raise
        self.calls: list[Any] = []

    def chat(self, messages, **kwargs):
        self.calls.append({"messages": messages, "kwargs": kwargs})
        if self.should_raise is not None:
            raise self.should_raise

        class _Resp:
            pass

        resp = _Resp()
        resp.text = self.response_text
        resp.provider = self.name
        resp.model = self.default_model
        resp.finish_reason = "stop"
        resp.usage = {}
        resp.raw = {}
        return resp

    def chat_stream(self, messages, **kwargs):
        yield self.response_text

    def get_model(self) -> str:
        return self.default_model

    def get_base_url(self) -> str:
        return "https://mock.example/v1"

    def get_api_key(self) -> str:
        return "mock-key"

    def is_available(self) -> bool:
        return True

    def reset_cache(self) -> None:
        pass


@pytest.fixture
def mock_provider():
    return MockProvider()


@pytest.fixture
def mock_provider_factory():
    def _factory(**kwargs) -> MockProvider:
        return MockProvider(**kwargs)
    return _factory


# =============================================================================
#  ХЕЛПЕРЫ
# =============================================================================

@pytest.fixture
def sample_code_blocks():
    return {
        "python": "```python\nprint('hello')\n```",
        "cpp": "```cpp\n#include <iostream>\nint main() { return 0; }\n```",
        "rust": "```rust\nfn main() { println!(\"hi\"); }\n```",
        "go": "```go\npackage main\nfunc main() {}\n```",
        "java": "```java\npublic class Main { public static void main(String[] a) {} }\n```",
        "no_lang": "```\nprint('x')\n```",
        "multiple": "```python\nprint(1)\n```\nSome text\n```python\nprint(2)\n```",
        "no_code": "Just some plain text without any code blocks.",
    }


@pytest.fixture
def temp_project_dir(tmp_path):
    project = tmp_path / "Codermuks-in-termux"
    project.mkdir()
    (project / "core").mkdir()
    (project / "ui").mkdir()
    (project / "tests").mkdir()
    (project / "main.py").write_text("", encoding="utf-8")
    (project / "codermuks").write_text("", encoding="utf-8")
    return project


# =============================================================================
#  НАСТРОЙКИ PYTEST
# =============================================================================

def pytest_configure(config):
    config.addinivalue_line("markers", "slow: медленные тесты")
    config.addinivalue_line("markers", "network: требуют интернета")
    config.addinivalue_line("markers", "integration: требуют компиляторов")
