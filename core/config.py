# =============================================================================
#  Codermuks in Termux — конфигурация v1.1.0
# =============================================================================
#  Этот модуль — единый источник правды о настройках проекта:
#
#    • где лежат конфиги и ключи (config.json, key.txt);
#    • какой язык интерфейса выбран (EN/RU);
#    • какой агент сейчас главный (team_lead);
#    • в каком порядке переключаться при падении (fallback_order);
#    • какие провайдеры включены и как их настроить;
#    • как читать API-ключи для каждого провайдера;
#    • какие таймауты и лимиты применяются к работе агента.
#
#  Все остальные модули импортируют настройки отсюда, чтобы не дублировать
#  пути и константы по всему коду.
# =============================================================================

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


# =============================================================================
#  ПУТИ
# =============================================================================

# --- Корень проекта --------------------------------------------------------
PROJECT_DIR: Path = Path(__file__).resolve().parent.parent

# --- Пользовательская директория -------------------------------------------
USER_DIR: Path = Path.home() / ".codermuks"

# --- Основные файлы --------------------------------------------------------
CONFIG_FILE: Path = USER_DIR / "config.json"      # настройки (язык, team_lead, providers)
KEY_FILE: Path = USER_DIR / "key.txt"             # API-ключи провайдеров
LOG_FILE: Path = Path.home() / ".codermuks.log"   # лог работы

# --- Директории ------------------------------------------------------------
ARTIFACTS_DIR: Path = USER_DIR / "artifacts"      # сохранённые результаты
TEMP_DIR: Path = USER_DIR / "temp"                # временные файлы компиляции


# =============================================================================
#  ПОДДЕРЖИВАЕМЫЕ ПРОВАЙДЕРЫ
# =============================================================================
#  Список провайдеров с их настройками по умолчанию. Используется при
#  создании config.json и при проверке, что пользователь не удалил
#  провайдера из конфига.
# =============================================================================

DEFAULT_PROVIDERS: dict[str, dict[str, Any]] = {
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
}

# Порядок переключения по умолчанию — если главный агент падает,
# пробуем следующего по этому списку.
DEFAULT_FALLBACK_ORDER: list[str] = ["mistral", "qwen", "deepseek", "openrouter"]

# Главный агент по умолчанию.
DEFAULT_TEAM_LEAD: str = "mistral"

# Поддерживаемые языки интерфейса.
SUPPORTED_LANGUAGES: list[str] = ["en", "ru"]


# =============================================================================
#  МОДЕЛИ MISTRAL (оставлены для совместимости с core/mistral_client.py)
# =============================================================================

PLANNER_MODEL: str = "mistral-large-latest"
CODING_MODEL: str = "codestral-latest"
RESEARCH_MODEL: str = "mistral-large-latest"
FAST_MODEL: str = "mistral-small-latest"


# =============================================================================
#  ПАРАМЕТРЫ ГЕНЕРАЦИИ
# =============================================================================

TEMPERATURE_CODING: float = 0.2
TEMPERATURE_PLANNING: float = 0.3
TEMPERATURE_RESEARCH: float = 0.4
MAX_TOKENS: int = 8192
TOP_P: float = 0.95


# =============================================================================
#  ПАРАМЕТРЫ АГЕНТА
# =============================================================================

MAX_FIX_ITERATIONS: int = 5
COMPILE_TIMEOUT: int = 60
RUN_TIMEOUT: int = 30
API_TIMEOUT: int = 120
API_MAX_RETRIES: int = 3
API_RETRY_BACKOFF: float = 1.5


# =============================================================================
#  ВНУТРЕННИЙ КЭШ
# =============================================================================
#  Чтобы не читать config.json и key.txt на каждый запрос, кэшируем
#  их содержимое в памяти. Кэш сбрасывается методом reload().
# =============================================================================

_config_cache: dict[str, Any] | None = None
_keys_cache: dict[str, str] | None = None


# =============================================================================
#  СОЗДАНИЕ ДИРЕКТОРИЙ
# =============================================================================

def ensure_dirs() -> None:
    """
    Создаёт все необходимые директории, если их ещё нет.

    Вызывается один раз при старте приложения и из install.sh,
    чтобы остальной код мог не беспокоиться о существовании путей.
    """
    USER_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
#  РАБОТА С config.json
# =============================================================================

def _default_config() -> dict[str, Any]:
    """Возвращает структуру config.json по умолчанию."""
    return {
        "version": "1.1.0",
        "language": None,
        "team_lead": DEFAULT_TEAM_LEAD,
        "fallback_order": list(DEFAULT_FALLBACK_ORDER),
        "providers": {k: dict(v) for k, v in DEFAULT_PROVIDERS.items()},
    }


def _load_config() -> dict[str, Any]:
    """
    Читает config.json. Если файла нет — создаёт с дефолтами.
    Если файл повреждён — пересоздаёт (сохраняя то, что удалось прочитать).
    """
    global _config_cache

    if _config_cache is not None:
        return _config_cache

    ensure_dirs()

    if not CONFIG_FILE.exists():
        data = _default_config()
        _save_config(data)
        _config_cache = data
        return data

    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # Файл повреждён — пересоздаём.
        data = _default_config()
        _save_config(data)
        _config_cache = data
        return data

    # Убеждаемся, что все ключи верхнего уровня на месте.
    default = _default_config()
    for key, value in default.items():
        if key not in data:
            data[key] = value

    # Убеждаемся, что все провайдеры присутствуют.
    if not isinstance(data.get("providers"), dict):
        data["providers"] = {}
    for name, def_provider in DEFAULT_PROVIDERS.items():
        if name not in data["providers"]:
            data["providers"][name] = dict(def_provider)
        else:
            # Дополняем поля провайдера, если каких-то не хватает.
            for pkey, pval in def_provider.items():
                if pkey not in data["providers"][name]:
                    data["providers"][name][pkey] = pval

    _config_cache = data
    return data


def _save_config(data: dict[str, Any]) -> None:
    """Сохраняет config.json на диск."""
    ensure_dirs()
    CONFIG_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    global _config_cache
    _config_cache = data


def reload() -> None:
    """Сбрасывает кэш конфига и ключей. Полезно при тестировании."""
    global _config_cache, _keys_cache
    _config_cache = None
    _keys_cache = None


def migrate_config_file() -> None:
    """
    Проверяет, что config.json содержит все нужные поля, и дополняет
    его дефолтными значениями. Существующие настройки пользователя
    не трогает.

    Вызывается из update.sh при обновлении проекта.
    """
    data = _load_config()
    _save_config(data)


# =============================================================================
#  ЯЗЫК ИНТЕРФЕЙСА
# =============================================================================

def get_language() -> str | None:
    """
    Возвращает код языка интерфейса ("en" или "ru") или None,
    если язык ещё не выбран.
    """
    data = _load_config()
    lang = data.get("language")
    if lang in SUPPORTED_LANGUAGES:
        return lang
    return None


def set_language(lang: str) -> None:
    """
    Сохраняет выбранный язык интерфейса в config.json.

    Исключения:
        ValueError — если язык не поддерживается.
    """
    if lang not in SUPPORTED_LANGUAGES:
        raise ValueError(
            f"Неподдерживаемый язык: {lang}. "
            f"Доступные: {', '.join(SUPPORTED_LANGUAGES)}"
        )
    data = _load_config()
    data["language"] = lang
    _save_config(data)


# =============================================================================
#  ГЛАВНЫЙ АГЕНТ И FALLBACK
# =============================================================================

def get_team_lead() -> str:
    """
    Возвращает имя текущего главного агента (например, "mistral").

    Если в конфиге указано что-то неизвестное — возвращает дефолт.
    """
    data = _load_config()
    lead = data.get("team_lead", DEFAULT_TEAM_LEAD)
    if lead not in DEFAULT_PROVIDERS:
        return DEFAULT_TEAM_LEAD
    return lead


def set_team_lead(name: str) -> None:
    """
    Меняет главного агента. Сохраняет в config.json.

    Исключения:
        ValueError — если провайдер не поддерживается.
    """
    if name not in DEFAULT_PROVIDERS:
        raise ValueError(
            f"Неизвестный провайдер: {name}. "
            f"Доступные: {', '.join(DEFAULT_PROVIDERS.keys())}"
        )
    data = _load_config()
    data["team_lead"] = name
    _save_config(data)


def get_fallback_order() -> list[str]:
    """
    Возвращает порядок переключения при падении главного агента.

    Гарантирует, что список:
        • содержит только известных провайдеров;
        • начинается с текущего team_lead;
        • не содержит дубликатов.
    """
    data = _load_config()
    order = data.get("fallback_order", list(DEFAULT_FALLBACK_ORDER))

    # Фильтруем незнакомых и дубликаты.
    seen: set[str] = set()
    cleaned: list[str] = []
    for name in order:
        if name in DEFAULT_PROVIDERS and name not in seen:
            cleaned.append(name)
            seen.add(name)

    # Добавляем тех, кого не хватает.
    for name in DEFAULT_PROVIDERS:
        if name not in seen:
            cleaned.append(name)
            seen.add(name)

    # team_lead должен быть первым.
    lead = get_team_lead()
    if lead in cleaned:
        cleaned.remove(lead)
    cleaned.insert(0, lead)

    return cleaned


# =============================================================================
#  ПРОВАЙДЕРЫ
# =============================================================================

def get_all_providers() -> dict[str, dict[str, Any]]:
    """
    Возвращает словарь провайдеров из config.json.
    Каждый провайдер — словарь с полями enabled, model, base_url, api_key.
    """
    data = _load_config()
    return data.get("providers", {})


def get_provider(name: str) -> dict[str, Any] | None:
    """
    Возвращает настройки одного провайдера или None, если такого нет.
    """
    return get_all_providers().get(name)


def is_provider_enabled(name: str) -> bool:
    """Проверяет, включён ли провайдер в config.json (поле enabled)."""
    provider = get_provider(name)
    if provider is None:
        return False
    return bool(provider.get("enabled", False))


def is_provider_configured(name: str) -> bool:
    """
    Проверяет, настроен ли провайдер полностью:
    включён И имеет API-ключ.

    Используется в /changeagent: если False — показываем ❌ не настроен.
    """
    if not is_provider_enabled(name):
        return False
    return bool(get_api_key(name))


# =============================================================================
#  API-КЛЮЧИ
# =============================================================================

def _load_keys() -> dict[str, str]:
    """
    Читает key.txt (JSON с ключами провайдеров).

    Возвращает словарь вида {"mistral": "sk-...", "qwen": "", ...}.
    Если файла нет или он повреждён — возвращает пустой словарь.
    """
    global _keys_cache
    if _keys_cache is not None:
        return _keys_cache

    ensure_dirs()

    if not KEY_FILE.exists():
        _keys_cache = {name: "" for name in DEFAULT_PROVIDERS}
        return _keys_cache

    try:
        raw = json.loads(KEY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        _keys_cache = {name: "" for name in DEFAULT_PROVIDERS}
        return _keys_cache

    # Оставляем только известных провайдеров, всё остальное игнорируем.
    result: dict[str, str] = {}
    for name in DEFAULT_PROVIDERS:
        value = raw.get(name, "")
        result[name] = str(value).strip() if value else ""

    _keys_cache = result
    return result


def get_api_key(provider: str) -> str:
    """
    Возвращает API-ключ для указанного провайдера.

    Порядок поиска:
        1. key.txt (основной источник).
        2. config.json → providers.<name>.api_key (фолбэк).
        3. Переменная окружения вида MISTRAL_API_KEY / QWEN_API_KEY / и т.д.

    Если ключа нигде нет — возвращает пустую строку.
    """
    # 1. key.txt
    keys = _load_keys()
    key = keys.get(provider, "").strip()
    if key:
        return key

    # 2. config.json
    provider_cfg = get_provider(provider)
    if provider_cfg:
        key = str(provider_cfg.get("api_key", "")).strip()
        if key:
            return key

    # 3. Переменные окружения
    env_name = f"{provider.upper()}_API_KEY"
    return os.environ.get(env_name, "").strip()


def get_provider_model(provider: str) -> str:
    """Возвращает имя модели для провайдера."""
    provider_cfg = get_provider(provider)
    if provider_cfg is None:
        return ""
    return str(provider_cfg.get("model", ""))


def get_provider_base_url(provider: str) -> str:
    """Возвращает base_url для провайдера (OpenAI-совместимый API)."""
    provider_cfg = get_provider(provider)
    if provider_cfg is None:
        return ""
    return str(provider_cfg.get("base_url", ""))


# =============================================================================
#  ОКРУЖЕНИЕ
# =============================================================================

def is_termux() -> bool:
    """Проверяет, запущено ли приложение в Termux."""
    prefix = os.environ.get("PREFIX", "")
    return "com.termux" in prefix or Path("/data/data/com.termux").exists()


def get_python_executable() -> str:
    """Возвращает путь к текущему интерпретатору Python."""
    return sys.executable


# =============================================================================
#  ИНИЦИАЛИЗАЦИЯ ПРИ ИМПОРТЕ
# =============================================================================

# Создаём директории сразу при импорте модуля.
ensure_dirs()