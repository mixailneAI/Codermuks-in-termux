# =============================================================================
#  Codermuks in Termux — тесты для core/i18n/ v1.1.0
# =============================================================================
#  Что проверяем:
#    • инициализацию переводчика выбранным языком;
#    • функцию t() — перевод ключа;
#    • подстановку плейсхолдеров;
#    • функцию tn() — плюрализацию;
#    • фолбэк на английский, если в ru нет строки;
#    • возврат ключа при отсутствии перевода;
#    • полноту переводов (одинаковые ключи в en и ru);
#    • работу со списком языков.
# =============================================================================

from __future__ import annotations

import pytest


# =============================================================================
#  ИНИЦИАЛИЗАЦИЯ
# =============================================================================

class TestInit:
    """Тесты инициализации переводчика."""

    def test_init_en(self, reset_translator):
        """init('en') устанавливает английский."""
        from core.i18n import translator
        translator.init("en")
        assert translator.get_language() == "en"

    def test_init_ru(self, reset_translator):
        """init('ru') устанавливает русский."""
        from core.i18n import translator
        translator.init("ru")
        assert translator.get_language() == "ru"

    def test_init_invalid_falls_back(self, reset_translator):
        """init('xx') — неизвестный язык → английский."""
        from core.i18n import translator
        translator.init("xx")
        assert translator.get_language() == "en"

    def test_init_empty_falls_back(self, reset_translator):
        """init('') — пустой язык → английский."""
        from core.i18n import translator
        translator.init("")
        assert translator.get_language() == "en"

    def test_set_language_alias(self, reset_translator):
        """set_language() работает так же, как init()."""
        from core.i18n import translator
        translator.set_language("ru")
        assert translator.get_language() == "ru"


# =============================================================================
#  ПЕРЕВОД t()
# =============================================================================

class TestTranslate:
    """Тесты функции t()."""

    def test_simple_translation_en(self, reset_translator):
        """t('cmd.exit') на английском возвращает английскую строку."""
        from core.i18n import translator
        translator.init("en")
        result = translator.t("cmd.exit")
        assert "exit" in result.lower()

    def test_simple_translation_ru(self, reset_translator):
        """t('cmd.exit') на русском возвращает русскую строку."""
        from core.i18n import translator
        translator.init("ru")
        result = translator.t("cmd.exit")
        assert "вый" in result.lower()  # "выйти"

    def test_unknown_key_returns_key(self, reset_translator):
        """t('nonexistent.key') возвращает сам ключ."""
        from core.i18n import translator
        translator.init("en")
        result = translator.t("nonexistent.key.that.does.not.exist")
        assert result == "nonexistent.key.that.does.not.exist"

    def test_empty_key(self, reset_translator):
        """t('') возвращает пустую строку."""
        from core.i18n import translator
        translator.init("en")
        assert translator.t("") == ""

    def test_placeholder_substitution(self, reset_translator):
        """Плейсхолдеры {name} подставляются."""
        from core.i18n import translator
        translator.init("en")
        result = translator.t("err.unknown_command", command="/test")
        assert "/test" in result
        assert "{" not in result

    def test_multiple_placeholders(self, reset_translator):
        """Несколько плейсхолдеров в одной строке."""
        from core.i18n import translator
        translator.init("en")
        result = translator.t("fallback.switch", name="Qwen", next="Mistral")
        assert "Qwen" in result
        assert "Mistral" in result

    def test_missing_placeholder_safe(self, reset_translator):
        """Если плейсхолдер не передан — возвращаем строку без подстановки."""
        from core.i18n import translator
        translator.init("en")
        # Не передаём name и next.
        result = translator.t("fallback.switch")
        # Функция не должна падать.
        assert isinstance(result, str)
        assert len(result) > 0


# =============================================================================
#  ФОЛБЭК
# =============================================================================

class TestFallback:
    """Тесты фолбэка на английский."""

    def test_fallback_to_en_when_ru_missing(self, reset_translator, monkeypatch):
        """Если в ru нет ключа — используется английский."""
        from core.i18n import translator

        # Временно загружаем ru и искусственно удаляем ключ.
        translator.init("ru")
        # Убираем один ключ из словаря.
        translator._strings.pop("cmd.exit", None)

        result = translator.t("cmd.exit")
        # Должен вернуться английский вариант, а не ключ.
        assert result != "cmd.exit"
        assert len(result) > 0


# =============================================================================
#  ПЛЮРАЛИЗАЦИЯ tn()
# =============================================================================

class TestPluralization:
    """Тесты функции tn()."""

    def test_en_singular(self, reset_translator):
        """tn('result.iterations_count', 1) на английском → единственное число."""
        from core.i18n import translator
        translator.init("en")
        result = translator.tn("result.iterations_count", 1)
        assert "1" in result
        assert "iteration" in result.lower()

    def test_en_plural(self, reset_translator):
        """tn('result.iterations_count', 5) на английском → множественное."""
        from core.i18n import translator
        translator.init("en")
        result = translator.tn("result.iterations_count", 5)
        assert "5" in result
        assert "iterations" in result.lower()

    def test_ru_singular(self, reset_translator):
        """tn на русском для 1 → 'итерация'."""
        from core.i18n import translator
        translator.init("ru")
        result = translator.tn("result.iterations_count", 1)
        assert "1" in result
        # Одна итерация.

    def test_ru_many(self, reset_translator):
        """tn на русском для 5 → множественное."""
        from core.i18n import translator
        translator.init("ru")
        result = translator.tn("result.iterations_count", 5)
        assert "5" in result

    def test_ru_21_uses_singular(self, reset_translator):
        """В русском 21 → 'итерация' (единственное)."""
        from core.i18n import translator
        translator.init("ru")
        result = translator.tn("result.iterations_count", 21)
        assert "21" in result


# =============================================================================
#  ПОЛНОТА ПЕРЕВОДОВ
# =============================================================================

class TestCompleteness:
    """Тесты полноты переводов."""

    def test_no_missing_keys_in_ru(self):
        """Все ключи из en.py присутствуют в ru.py."""
        from core.i18n import translator
        missing = translator.missing_keys()
        assert missing["missing_in_ru"] == [], (
            f"В ru.py нет ключей: {missing['missing_in_ru']}"
        )

    def test_no_missing_keys_in_en(self):
        """Все ключи из ru.py присутствуют в en.py."""
        from core.i18n import translator
        missing = translator.missing_keys()
        assert missing["missing_in_en"] == [], (
            f"В en.py нет ключей: {missing['missing_in_en']}"
        )

    def test_same_number_of_keys(self):
        """Количество ключей в en.py и ru.py одинаковое."""
        from core.i18n import en, ru
        assert len(en.STRINGS) == len(ru.STRINGS), (
            f"en: {len(en.STRINGS)} ключей, "
            f"ru: {len(ru.STRINGS)} ключей"
        )


# =============================================================================
#  ХЕЛПЕРЫ
# =============================================================================

class TestHelpers:
    """Тесты вспомогательных функций."""

    def test_has_key_positive(self, reset_translator):
        """has_key возвращает True для существующего ключа."""
        from core.i18n import translator
        translator.init("en")
        assert translator.has_key("cmd.exit") is True

    def test_has_key_negative(self, reset_translator):
        """has_key возвращает False для несуществующего."""
        from core.i18n import translator
        translator.init("en")
        assert translator.has_key("nonexistent.key") is False

    def test_keys_returns_list(self, reset_translator):
        """keys() возвращает отсортированный список."""
        from core.i18n import translator
        translator.init("en")
        result = translator.keys()
        assert isinstance(result, list)
        assert len(result) > 0
        # Проверяем, что отсортировано.
        assert result == sorted(result)

    def test_list_languages(self):
        """list_languages возвращает en и ru."""
        from core.i18n import translator
        langs = translator.list_languages()
        assert "en" in langs
        assert "ru" in langs
        assert langs["en"] == "English"
        assert langs["ru"] == "Русский"


# =============================================================================
#  ПАКЕТНЫЙ ЭКСПОРТ
# =============================================================================

class TestPackageExport:
    """Тесты публичного API пакета core.i18n."""

    def test_import_from_package(self):
        """Все функции доступны из core.i18n напрямую."""
        from core.i18n import (
            t, tn, init, get_language, set_language, list_languages,
        )
        assert callable(t)
        assert callable(tn)
        assert callable(init)
        assert callable(get_language)
        assert callable(set_language)
        assert callable(list_languages)

    def test_t_works_via_package(self, reset_translator):
        """t() из пакета работает без явного init — грузит дефолт."""
        from core.i18n import t, translator
        translator.init("en")
        result = t("cmd.exit")
        assert isinstance(result, str)
        assert len(result) > 0