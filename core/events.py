# =============================================================================
#  Codermuks in Termux — шина событий v1.3.0
# =============================================================================
#  Что делает этот модуль:
#    • позволяет компонентам агента публиковать события;
#    • подписчики (UI) получают их и рисуют в реальном времени;
#    • работает в одном потоке — простой синхронный event bus.
#
#  Как это работает:
#      1. Агент вызывает events.emit("planning.step", {...}).
#      2. EventBus проходит по всем подписчикам.
#      3. Каждый подписчик получает объект Event.
#      4. CLI обновляет панель в реальном времени.
#
#  Пример:
#      bus = get_bus()
#      bus.subscribe(my_callback)
#      bus.emit("planning.start", {"query": "напиши змейку"})
#      bus.emit("planning.step", {"detail": "определил язык: Python"})
#      bus.emit("planning.done", {})
# =============================================================================

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable


# =============================================================================
#  СОБЫТИЕ
# =============================================================================

@dataclass
class Event:
    """
    Одно событие от агента.

    Поля:
        name      — имя события ("planning.start", "codegen.file", ...).
        data      — словарь с полезной нагрузкой.
        timestamp — unix-время возникновения события.
        level     — "info" / "success" / "warning" / "error" / "progress".
        step      — опциональное имя текущего шага (для группировки).
    """
    name: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    level: str = "info"
    step: str = ""

    # --- Удобные геттеры ---------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """Достаёт значение из data."""
        return self.data.get(key, default)

    @property
    def message(self) -> str:
        """Короткое текстовое описание события."""
        return str(self.data.get("message", ""))


# =============================================================================
#  УРОВНИ
# =============================================================================

LEVEL_INFO = "info"
LEVEL_SUCCESS = "success"
LEVEL_WARNING = "warning"
LEVEL_ERROR = "error"
LEVEL_PROGRESS = "progress"


# =============================================================================
#  ШИНА
# =============================================================================

class EventBus:
    """
    Простая синхронная шина событий.

    Все подписчики вызываются в том порядке, в котором подписались.
    Ошибка в одном подписчике НЕ ломает других — обёрнуто в try/except.
    """

    def __init__(self) -> None:
        # Список подписчиков: (callback, filter_name_or_None)
        self._subscribers: list[tuple[Callable[[Event], None], str | None]] = []
        # История событий — для отладки и повторного воспроизведения.
        self._history: list[Event] = []
        # Максимум сохраняемых событий, чтобы не есть память.
        self._history_limit: int = 1000

    # -------------------------------------------------------------------------
    #  ПОДПИСКА
    # -------------------------------------------------------------------------

    def subscribe(
        self,
        callback: Callable[[Event], None],
        filter_prefix: str | None = None,
    ) -> Callable[[], None]:
        """
        Подписывает callback на события.

        Аргументы:
            callback      — функция, принимающая Event.
            filter_prefix — если задан, callback вызывается только для
                            событий, чьё имя начинается с этого префикса.
                            Пример: "planning" — только планирование.

        Возвращает:
            Функцию unsubscribe(), которая отписывает callback.
        """
        entry = (callback, filter_prefix)
        self._subscribers.append(entry)

        def unsubscribe() -> None:
            try:
                self._subscribers.remove(entry)
            except ValueError:
                pass

        return unsubscribe

    def unsubscribe_all(self) -> None:
        """Убирает всех подписчиков."""
        self._subscribers.clear()

    # -------------------------------------------------------------------------
    #  ПУБЛИКАЦИЯ
    # -------------------------------------------------------------------------

    def emit(
        self,
        name: str,
        data: dict[str, Any] | None = None,
        *,
        level: str = LEVEL_INFO,
        step: str = "",
    ) -> Event:
        """
        Публикует событие.

        Возвращает сам объект Event — удобно для логирования.

        Пример:
            bus.emit("codegen.file", {"file": "snake.py"}, level="success")
        """
        event = Event(
            name=name,
            data=data or {},
            level=level,
            step=step,
        )

        # Сохраняем в историю.
        self._history.append(event)
        if len(self._history) > self._history_limit:
            self._history = self._history[-self._history_limit:]

        # Уведомляем подписчиков.
        for callback, filter_prefix in list(self._subscribers):
            if filter_prefix is not None:
                if not name.startswith(filter_prefix):
                    continue
            try:
                callback(event)
            except Exception:
                # Ошибка подписчика не должна ломать публикацию.
                pass

        return event

    # -------------------------------------------------------------------------
    #  ИСТОРИЯ
    # -------------------------------------------------------------------------

    def get_history(self, limit: int = 100) -> list[Event]:
        """Возвращает последние N событий."""
        return list(self._history[-limit:])

    def clear_history(self) -> None:
        """Очищает историю."""
        self._history.clear()

    def count(self) -> int:
        """Сколько событий было опубликовано."""
        return len(self._history)


# =============================================================================
#  ГЛОБАЛЬНАЯ ШИНА (SINGLETON)
# =============================================================================

_bus_instance: EventBus | None = None


def get_bus() -> EventBus:
    """Возвращает глобальную шину событий."""
    global _bus_instance
    if _bus_instance is None:
        _bus_instance = EventBus()
    return _bus_instance


def reset_bus() -> None:
    """Сбрасывает глобальную шину (для тестов)."""
    global _bus_instance
    _bus_instance = None


# =============================================================================
#  УДОБНЫЕ ОБЁРТКИ
# =============================================================================

def emit(name: str, data: dict[str, Any] | None = None, **kwargs: Any) -> Event:
    """Короткая обёртка над get_bus().emit()."""
    return get_bus().emit(name, data, **kwargs)


def subscribe(
    callback: Callable[[Event], None],
    filter_prefix: str | None = None,
) -> Callable[[], None]:
    """Короткая обёртка над get_bus().subscribe()."""
    return get_bus().subscribe(callback, filter_prefix)


# =============================================================================
#  ПРЕДОПРЕДЕЛЁННЫЕ СОБЫТИЯ (СПРАВОЧНИК)
# =============================================================================
#  Мы не ограничиваем имена событий, но эти — стандартные.
#  Компоненты агента используют их, чтобы UI знал, что рисовать.
#
#  Формат: "namespace.action"
#
#    planning.start          — начало планирования
#    planning.step           — промежуточный шаг планирования
#    planning.done           — план готов
#
#    codegen.start           — начало генерации кода
#    codegen.file            — начали писать файл
#    codegen.file.done       — файл записан
#    codegen.done            — генерация завершена
#
#    compile.start           — начало компиляции
#    compile.success         — успех
#    compile.error           — ошибка компиляции
#
#    run.start               — запуск программы
#    run.success             — программа отработала
#    run.error               — программа упала
#
#    fix.start               — начало фикса
#    fix.done                — фикс завершён
#
#    research.start          — начало исследования
#    research.source         — найден источник
#    research.done           — исследование завершено
#
#    project.created         — создан проект
#    project.opened          — открыт проект
#    project.saved           — сохранён проект
#
#    token.usage             — использовано N токенов
#    task.done               — задача завершена
# =============================================================================


# =============================================================================
#  ЭКСПОРТ
# =============================================================================

__all__ = [
    "Event",
    "EventBus",
    "get_bus",
    "reset_bus",
    "emit",
    "subscribe",
    "LEVEL_INFO",
    "LEVEL_SUCCESS",
    "LEVEL_WARNING",
    "LEVEL_ERROR",
    "LEVEL_PROGRESS",
]
