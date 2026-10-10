# =============================================================================
#  Codermuks in Termux — менеджер переключения агентов v1.1.0
# =============================================================================
#  Что делает этот модуль:
#    • следит за падениями главного агента;
#    • находит альтернативу из fallback_order (в config.json);
#    • фильтрует только тех, у кого есть API-ключ;
#    • опционально спрашивает пользователя через on_switch-колбэк;
#    • помнит, кто уже упал в текущей сессии, чтобы не зацикливаться.
#
#  Пример использования:
#      fb = FallbackManager(current="qwen", on_switch=my_callback)
#      alternative = fb.pick_alternative()
#      if alternative:
#          # переключаемся на alternative
#      else:
#          # альтернатив нет — обрабатываем ошибку
# =============================================================================

from __future__ import annotations

from typing import Callable

from core import config


# =============================================================================
#  МЕНЕДЖЕР
# =============================================================================

class FallbackManager:
    """
    Управляет переключением между агентами при сбоях.

    Логика:
        1. Получает имя текущего лидера.
        2. Читает fallback_order из config.json.
        3. Фильтрует: убирает тех, кто уже упал в этой сессии.
        4. Фильтрует: убирает тех, у кого нет API-ключа.
        5. Возвращает первого из оставшихся или None.

    Менеджер — stateful: он помнит, кто упал. Это защищает от
    бесконечного цикла «A упал → переключились на B → B упал →
    переключились на A → A снова упал».
    """

    def __init__(
        self,
        current: str,
        on_switch: Callable[[str, str], bool] | None = None,
    ) -> None:
        """
        Аргументы:
            current   — имя агента, который только что упал
                        (обычно это текущий главный агент).
            on_switch — колбэк, который спрашивает пользователя,
                        переключаться ли на альтернативу.
                        Сигнатура: on_switch(old, new) -> bool.
                        Если None — переключение происходит молча.
        """
        self.current = (current or "").strip().lower()
        self.on_switch = on_switch

        # Множество упавших агентов в текущей сессии.
        # Изначально содержит текущего лидера — он уже упал.
        self._failed: set[str] = set()
        if self.current:
            self._failed.add(self.current)

    # -------------------------------------------------------------------------
    #  Управление состоянием
    # -------------------------------------------------------------------------

    def mark_failed(self, name: str) -> None:
        """Помечает агента как упавшего — исключаем его из альтернатив."""
        if name:
            self._failed.add(name.strip().lower())

    def reset(self) -> None:
        """
        Сбрасывает список упавших.

        Оставляет только текущего лидера в списке — он всё ещё «упал»
        с точки зрения сессии, но если пользователь перезапустит
        задачу, состояние сбросится вместе с менеджером.
        """
        self._failed.clear()
        if self.current:
            self._failed.add(self.current)

    # -------------------------------------------------------------------------
    #  Цепочка fallback
    # -------------------------------------------------------------------------

    def get_chain(self) -> list[str]:
        """
        Возвращает полный порядок fallback с текущим агентом в начале.

        Порядок берётся из config.get_fallback_order() — там он уже
        нормализован (team_lead первый, дубликатов нет).
        """
        try:
            order = list(config.get_fallback_order())
        except Exception:
            order = []

        # Гарантируем, что текущий агент — первый в списке.
        if self.current:
            if self.current in order:
                order.remove(self.current)
            order.insert(0, self.current)

        return order

    def list_available_alternatives(self) -> list[str]:
        """
        Возвращает список настроенных агентов, кроме уже упавших.

        Настроен = провайдер включён в config.json И имеет API-ключ.
        Порядок — как в fallback_order.
        """
        result: list[str] = []

        for name in self.get_chain():
            # Пропускаем упавших.
            if name in self._failed:
                continue

            # Пропускаем ненастроенных.
            try:
                if not config.is_provider_configured(name):
                    continue
            except Exception:
                continue

            result.append(name)

        return result

    def has_alternatives(self) -> bool:
        """Проверяет, есть ли хоть одна альтернатива."""
        return bool(self.list_available_alternatives())

    # -------------------------------------------------------------------------
    #  Выбор альтернативы
    # -------------------------------------------------------------------------

    def pick_alternative(self) -> str | None:
        """
        Возвращает имя следующего агента или None, если альтернатив нет.

        Если задан on_switch — сначала спрашивает пользователя.
        Если пользователь отказался — возвращает None.
        """
        alternatives = self.list_available_alternatives()

        if not alternatives:
            return None

        next_name = alternatives[0]

        # Спрашиваем пользователя, если задан колбэк.
        if self.on_switch is not None:
            try:
                confirmed = bool(self.on_switch(self.current, next_name))
            except Exception:
                # Ошибка в колбэке — по умолчанию соглашаемся,
                # чтобы не блокировать работу.
                confirmed = True

            if not confirmed:
                return None

        return next_name

    # -------------------------------------------------------------------------
    #  Отладка
    # -------------------------------------------------------------------------

    def state(self) -> dict:
        """
        Возвращает текущее состояние менеджера — для отладки и тестов.

        Формат:
            {
                "current": "qwen",
                "failed": ["qwen"],
                "chain": ["qwen", "mistral", "deepseek", "openrouter"],
                "alternatives": ["mistral", "deepseek"],
            }
        """
        return {
            "current": self.current,
            "failed": sorted(self._failed),
            "chain": self.get_chain(),
            "alternatives": self.list_available_alternatives(),
        }

    def __repr__(self) -> str:
        return (
            f"<FallbackManager current={self.current!r} "
            f"failed={sorted(self._failed)}>"
        )


# =============================================================================
#  ЭКСПОРТ
# =============================================================================

__all__ = ["FallbackManager"]