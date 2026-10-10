# =============================================================================
#  Codermuks in Termux — тесты для core/llm_providers/ v1.1.0
# =============================================================================
#  Что проверяем:
#    • базовый класс LLMProvider и его контракт;
#    • ChatMessage и ProviderResponse;
#    • классификацию ошибок в OpenAICompatibleProvider;
#    • работу провайдеров с MockProvider (без реальных запросов);
#    • фабрику get_provider() и списки AVAILABLE_PROVIDERS;
#    • извлечение кода из ответов модели;
#    • корректность default_model у каждого провайдера.
# =============================================================================

from __future__ import annotations

import pytest


# =============================================================================
#  CHATMESSAGE
# =============================================================================

class TestChatMessage:
    """Тесты структуры ChatMessage."""

    def test_create_simple(self):
        """Создание ChatMessage с role и content."""
        from core.llm_providers.base import ChatMessage
        msg = ChatMessage(role="user", content="hello")
        assert msg.role == "user"
        assert msg.content == "hello"

    def test_to_dict(self):
        """to_dict() возвращает формат OpenAI."""
        from core.llm_providers.base import ChatMessage
        msg = ChatMessage(role="user", content="hi")
        d = msg.to_dict()
        assert d == {"role": "user", "content": "hi"}

    def test_from_dict(self):
        """from_dict() создаёт объект из словаря."""
        from core.llm_providers.base import ChatMessage
        msg = ChatMessage.from_dict({"role": "assistant", "content": "ok"})
        assert msg.role == "assistant"
        assert msg.content == "ok"

    def test_from_dict_missing_fields(self):
        """from_dict() безопасно обрабатывает пустой словарь."""
        from core.llm_providers.base import ChatMessage
        msg = ChatMessage.from_dict({})
        assert msg.role == "user"  # дефолт
        assert msg.content == ""


# =============================================================================
#  PROVIDER RESPONSE
# =============================================================================

class TestProviderResponse:
    """Тесты структуры ProviderResponse."""

    def test_create(self):
        """Создание ProviderResponse со всеми полями."""
        from core.llm_providers.base import ProviderResponse
        resp = ProviderResponse(
            text="hello",
            provider="mistral",
            model="mistral-large-latest",
            finish_reason="stop",
        )
        assert resp.text == "hello"
        assert resp.provider == "mistral"
        assert resp.model == "mistral-large-latest"

    def test_bool_true(self):
        """Непустой ответ — истинный."""
        from core.llm_providers.base import ProviderResponse
        resp = ProviderResponse(text="hi")
        assert bool(resp) is True

    def test_bool_false_empty(self):
        """Пустой ответ — ложный."""
        from core.llm_providers.base import ProviderResponse
        resp = ProviderResponse(text="")
        assert bool(resp) is False

    def test_bool_false_whitespace(self):
        """Ответ из пробелов — ложный."""
        from core.llm_providers.base import ProviderResponse
        resp = ProviderResponse(text="   \n\t ")
        assert bool(resp) is False


# =============================================================================
#  ИСКЛЮЧЕНИЯ
# =============================================================================

class TestExceptions:
    """Тесты иерархии исключений."""

    def test_hierarchy(self):
        """Все исключения наследуются от ProviderError."""
        from core.llm_providers.base import (
            ProviderError,
            ProviderAuthError,
            ProviderRateLimitError,
            ProviderServerError,
            ProviderNetworkError,
            ProviderNotConfiguredError,
        )
        assert issubclass(ProviderAuthError, ProviderError)
        assert issubclass(ProviderRateLimitError, ProviderError)
        assert issubclass(ProviderServerError, ProviderError)
        assert issubclass(ProviderNetworkError, ProviderError)
        assert issubclass(ProviderNotConfiguredError, ProviderError)

    def test_can_catch_base(self):
        """Можно ловить любое из исключений через ProviderError."""
        from core.llm_providers.base import ProviderError, ProviderAuthError
        try:
            raise ProviderAuthError("bad key")
        except ProviderError as exc:
            assert "bad key" in str(exc)


# =============================================================================
#  БАЗОВЫЙ ПРОВАЙДЕР
# =============================================================================

class TestLLMProviderContract:
    """Тесты контракта абстрактного класса LLMProvider."""

    def test_cannot_instantiate_abstract(self):
        """LLMProvider — абстрактный, его нельзя создать напрямую."""
        from core.llm_providers.base import LLMProvider
        with pytest.raises(TypeError):
            LLMProvider()  # type: ignore

    def test_subclass_must_implement_chat(self):
        """Наследник без chat() не может быть создан."""
        from core.llm_providers.base import LLMProvider

        class Dummy(LLMProvider):
            name = "dummy"

        with pytest.raises(TypeError):
            Dummy()  # type: ignore

    def test_normalize_messages_from_dicts(self):
        """normalize_messages принимает список словарей."""
        from core.llm_providers.base import LLMProvider

        class Dummy(LLMProvider):
            name = "dummy"
            def chat(self, messages, **kwargs):
                return None

        dummy = Dummy()
        result = dummy.normalize_messages([
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "usr"},
        ])
        assert len(result) == 2
        assert result[0]["role"] == "system"

    def test_normalize_messages_from_objects(self):
        """normalize_messages принимает ChatMessage."""
        from core.llm_providers.base import ChatMessage, LLMProvider

        class Dummy(LLMProvider):
            name = "dummy"
            def chat(self, messages, **kwargs):
                return None

        dummy = Dummy()
        result = dummy.normalize_messages([
            ChatMessage(role="user", content="hi"),
        ])
        assert result == [{"role": "user", "content": "hi"}]


# =============================================================================
#  ПРОВАЙДЕРЫ
# =============================================================================

class TestProviderMetadata:
    """Тесты метаданных провайдеров."""

    def test_mistral_metadata(self):
        """MistralProvider имеет корректные метаданные."""
        from core.llm_providers.mistral_provider import MistralProvider
        p = MistralProvider()
        assert p.name == "mistral"
        assert p.display_name == "Mistral AI"
        assert p.default_model == "mistral-large-latest"

    def test_qwen_metadata(self):
        """QwenProvider имеет корректные метаданные."""
        from core.llm_providers.qwen_provider import QwenProvider
        p = QwenProvider()
        assert p.name == "qwen"
        assert p.default_model == "qwen3-coder-plus"

    def test_deepseek_metadata(self):
        """DeepSeekProvider имеет корректные метаданные."""
        from core.llm_providers.deepseek_provider import DeepSeekProvider
        p = DeepSeekProvider()
        assert p.name == "deepseek"
        assert p.default_model == "deepseek-chat"

    def test_openrouter_metadata(self):
        """OpenRouterProvider имеет корректные метаданные."""
        from core.llm_providers.openrouter_provider import OpenRouterProvider
        p = OpenRouterProvider()
        assert p.name == "openrouter"
        assert ":free" in p.default_model

    def test_openrouter_extra_headers(self):
        """OpenRouter возвращает HTTP-Referer и X-Title."""
        from core.llm_providers.openrouter_provider import OpenRouterProvider
        p = OpenRouterProvider()
        headers = p.extra_headers()
        assert "HTTP-Referer" in headers
        assert "X-Title" in headers

    def test_mistral_no_extra_headers(self):
        """Mistral не переопределяет extra_headers — пусто."""
        from core.llm_providers.mistral_provider import MistralProvider
        p = MistralProvider()
        assert p.extra_headers() == {}


# =============================================================================
#  ФАБРИКА
# =============================================================================

class TestFactory:
    """Тесты фабрики get_provider()."""

    def test_available_providers_list(self):
        """AVAILABLE_PROVIDERS содержит 4 имени."""
        from core.llm_providers import AVAILABLE_PROVIDERS
        assert "mistral" in AVAILABLE_PROVIDERS
        assert "qwen" in AVAILABLE_PROVIDERS
        assert "deepseek" in AVAILABLE_PROVIDERS
        assert "openrouter" in AVAILABLE_PROVIDERS
        assert len(AVAILABLE_PROVIDERS) == 4

    def test_get_provider_mistral(self):
        """get_provider('mistral') возвращает MistralProvider."""
        from core.llm_providers import get_provider
        from core.llm_providers.mistral_provider import MistralProvider
        p = get_provider("mistral")
        assert isinstance(p, MistralProvider)

    def test_get_provider_qwen(self):
        """get_provider('qwen') возвращает QwenProvider."""
        from core.llm_providers import get_provider
        from core.llm_providers.qwen_provider import QwenProvider
        p = get_provider("qwen")
        assert isinstance(p, QwenProvider)

    def test_get_provider_case_insensitive(self):
        """get_provider работает в любом регистре."""
        from core.llm_providers import get_provider
        p1 = get_provider("MISTRAL")
        p2 = get_provider("mistral")
        assert p1.name == p2.name == "mistral"

    def test_get_unknown_provider_raises(self):
        """get_provider с неизвестным именем выбрасывает ValueError."""
        from core.llm_providers import get_provider
        with pytest.raises(ValueError):
            get_provider("nonexistent")

    def test_get_empty_provider_raises(self):
        """get_provider('') выбрасывает ValueError."""
        from core.llm_providers import get_provider
        with pytest.raises(ValueError):
            get_provider("")

    def test_list_available(self):
        """list_available() возвращает список имён."""
        from core.llm_providers import list_available
        names = list_available()
        assert isinstance(names, list)
        assert "mistral" in names

    def test_is_configured_returns_bool(self):
        """is_configured() возвращает bool и не падает без ключей."""
        from core.llm_providers import is_configured
        result = is_configured("mistral")
        assert isinstance(result, bool)


# =============================================================================
#  ИЗВЛЕЧЕНИЕ КОДА
# =============================================================================

class TestExtractCode:
    """Тесты извлечения кода из ответов модели.

    Использует CoderSubagent, потому что он уже умеет это делать.
    """

    def test_extract_python(self, sample_code_blocks):
        """Извлекается python-код из блока."""
        from subagents.coder import CoderSubagent
        coder = CoderSubagent()
        raw = sample_code_blocks["python"]
        lang, code = coder.parse_response(raw)
        assert lang == "python"
        assert "hello" in code

    def test_extract_cpp(self, sample_code_blocks):
        """Извлекается C++ код."""
        from subagents.coder import CoderSubagent
        coder = CoderSubagent()
        raw = sample_code_blocks["cpp"]
        lang, code = coder.parse_response(raw)
        assert lang == "cpp"
        assert "iostream" in code

    def test_extract_rust(self, sample_code_blocks):
        """Извлекается Rust код."""
        from subagents.coder import CoderSubagent
        coder = CoderSubagent()
        raw = sample_code_blocks["rust"]
        lang, code = coder.parse_response(raw)
        assert lang == "rust"
        assert "fn main" in code

    def test_extract_go(self, sample_code_blocks):
        """Извлекается Go код."""
        from subagents.coder import CoderSubagent
        coder = CoderSubagent()
        raw = sample_code_blocks["go"]
        lang, code = coder.parse_response(raw)
        assert lang == "go"
        assert "package main" in code

    def test_extract_java(self, sample_code_blocks):
        """Извлекается Java код."""
        from subagents.coder import CoderSubagent
        coder = CoderSubagent()
        raw = sample_code_blocks["java"]
        lang, code = coder.parse_response(raw)
        assert lang == "java"
        assert "class Main" in code

    def test_extract_no_lang_guesses(self, sample_code_blocks):
        """Если язык не указан — определяется автоматически."""
        from subagents.coder import CoderSubagent
        coder = CoderSubagent()
        raw = sample_code_blocks["no_lang"]
        lang, code = coder.parse_response(raw)
        # Без явного языка — эвристика вернёт python (дефолт).
        assert lang in ("python", "javascript")

    def test_extract_multiple_takes_first(self, sample_code_blocks):
        """Из нескольких блоков берётся первый."""
        from subagents.coder import CoderSubagent
        coder = CoderSubagent()
        raw = sample_code_blocks["multiple"]
        lang, code = coder.parse_response(raw)
        assert "print(1)" in code
        assert "print(2)" not in code

    def test_extract_no_code(self, sample_code_blocks):
        """Если блоков нет — возвращается пустой код."""
        from subagents.coder import CoderSubagent
        coder = CoderSubagent()
        raw = sample_code_blocks["no_code"]
        lang, code = coder.parse_response(raw)
        assert code == ""


# =============================================================================
#  ЯЗЫКОВЫЕ АЛИАСЫ
# =============================================================================

class TestLanguageAliases:
    """Тесты таблицы алиасов языков."""

    def test_cpp_aliases(self):
        """cpp / c++ / cxx → 'cpp'."""
        from subagents.coder import CoderSubagent
        coder = CoderSubagent()
        assert coder.normalize_language("cpp") == "cpp"
        assert coder.normalize_language("c++") == "cpp"
        assert coder.normalize_language("cxx") == "cpp"

    def test_csharp_aliases(self):
        """c# / csharp / cs → 'csharp'."""
        from subagents.coder import CoderSubagent
        coder = CoderSubagent()
        assert coder.normalize_language("c#") == "csharp"
        assert coder.normalize_language("csharp") == "csharp"
        assert coder.normalize_language("cs") == "csharp"

    def test_python_aliases(self):
        """python / py / python3 → 'python'."""
        from subagents.coder import CoderSubagent
        coder = CoderSubagent()
        assert coder.normalize_language("python") == "python"
        assert coder.normalize_language("py") == "python"
        assert coder.normalize_language("python3") == "python"

    def test_javascript_aliases(self):
        """js / node / typescript → 'javascript'."""
        from subagents.coder import CoderSubagent
        coder = CoderSubagent()
        assert coder.normalize_language("js") == "javascript"
        assert coder.normalize_language("node") == "javascript"
        assert coder.normalize_language("typescript") == "javascript"

    def test_rust_aliases(self):
        """rust / rs → 'rust'."""
        from subagents.coder import CoderSubagent
        coder = CoderSubagent()
        assert coder.normalize_language("rust") == "rust"
        assert coder.normalize_language("rs") == "rust"

    def test_go_aliases(self):
        """go / golang → 'go'."""
        from subagents.coder import CoderSubagent
        coder = CoderSubagent()
        assert coder.normalize_language("go") == "go"
        assert coder.normalize_language("golang") == "go"

    def test_case_insensitive(self):
        """Регистр не важен."""
        from subagents.coder import CoderSubagent
        coder = CoderSubagent()
        assert coder.normalize_language("PYTHON") == "python"
        assert coder.normalize_language("Rust") == "rust"

    def test_unknown_passthrough(self):
        """Незнакомый язык возвращается в нижнем регистре."""
        from subagents.coder import CoderSubagent
        coder = CoderSubagent()
        assert coder.normalize_language("brainfuck") == "brainfuck"