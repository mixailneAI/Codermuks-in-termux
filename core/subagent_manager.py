# =============================================================================
#  Codermuks in Termux — менеджер субагентов
# =============================================================================
#  Управляет жизненным циклом субагентов: регистрация, получение по имени,
#  запуск задач и сбор результатов.
#
#  Зачем это нужно:
#    • Оркестратор не должен создавать субагентов вручную каждый раз.
#    • Легко добавить нового субагента — достаточно зарегистрировать его здесь.
#    • Единая точка логирования и обработки ошибок при запуске задач.
# =============================================================================

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable


# =============================================================================
#  СТРУКТУРЫ ДАННЫХ
# =============================================================================

@dataclass
class TaskResult:
    """Результат выполнения задачи субагентом."""
    subagent: str              # имя субагента
    task: str                  # исходная задача
    success: bool              # выполнено ли успешно
    output: str                # результат работы (текст)
    error: str = ""            # сообщение об ошибке (пусто, если успех)
    duration: float = 0.0      # длительность в секундах
    metadata: dict[str, Any] = field(default_factory=dict)  # доп. данные


# =============================================================================
#  МЕНЕДЖЕР
# =============================================================================

class SubagentManager:
    """
    Реестр субагентов и диспетчер задач.

    Использование:
        manager = SubagentManager()
        manager.register("coder", CoderSubagent())
        manager.register("tester", TesterSubagent())
        ...
        result = manager.run("coder", "напиши функцию сортировки")
    """

    def __init__(self) -> None:
        # Словарь зарегистрированных субагентов: имя → экземпляр.
        self._subagents: dict[str, Any] = {}
        # История выполненных задач — для отладки и анализа.
        self._history: list[TaskResult] = []
        # Колбэк для уведомления о старте задачи (используется CLI).
        self.on_task_start: Callable[[str, str], None] | None = None
        # Колбэк для уведомления о завершении задачи.
        self.on_task_end: Callable[[TaskResult], None] | None = None

    # -------------------------------------------------------------------------
    #  Регистрация
    # -------------------------------------------------------------------------

    def register(self, name: str, subagent: Any) -> None:
        """
        Регистрирует субагента под указанным именем.

        Аргументы:
            name     — короткое имя ("coder", "tester", ...)
            subagent — экземпляр субагента (наследник BaseSubagent)
        """
        self._subagents[name] = subagent

    def unregister(self, name: str) -> None:
        """Удаляет субагента из реестра."""
        self._subagents.pop(name, None)

    def get(self, name: str) -> Any:
        """
        Возвращает субагента по имени.

        Исключения:
            KeyError — если субагент не зарегистрирован.
        """
        if name not in self._subagents:
            available = ", ".join(self._subagents.keys()) or "(пусто)"
            raise KeyError(
                f"Субагент '{name}' не найден. Доступные: {available}"
            )
        return self._subagents[name]

    def list_subagents(self) -> list[str]:
        """Возвращает список имён зарегистрированных субагентов."""
        return list(self._subagents.keys())

    def has(self, name: str) -> bool:
        """Проверяет, зарегистрирован ли субагент с таким именем."""
        return name in self._subagents

    # -------------------------------------------------------------------------
    #  Запуск задач
    # -------------------------------------------------------------------------

    def run(self, name: str, task: str, **kwargs) -> TaskResult:
        """
        Запускает задачу у субагента.

        Аргументы:
            name — имя субагента
            task — текстовая задача
            **kwargs — дополнительные аргументы для субагента

        Возвращает:
            TaskResult с результатом работы.

        Никогда не выбрасывает исключение наружу — все ошибки упакованы
        в TaskResult, чтобы оркестратор мог их обработать единообразно.
        """
        started = time.time()

        if self.on_task_start is not None:
            try:
                self.on_task_start(name, task)
            except Exception:
                pass

        # Проверяем, что субагент существует.
        if name not in self._subagents:
            result = TaskResult(
                subagent=name,
                task=task,
                success=False,
                output="",
                error=f"Субагент '{name}' не зарегистрирован.",
                duration=time.time() - started,
            )
            self._history.append(result)
            if self.on_task_end is not None:
                try:
                    self.on_task_end(result)
                except Exception:
                    pass
            return result

        subagent = self._subagents[name]

        # Пытаемся запустить задачу.
        try:
            output = subagent.run(task, **kwargs)
            result = TaskResult(
                subagent=name,
                task=task,
                success=True,
                output=str(output) if output is not None else "",
                error="",
                duration=time.time() - started,
            )
        except Exception as exc:
            result = TaskResult(
                subagent=name,
                task=task,
                success=False,
                output="",
                error=str(exc),
                duration=time.time() - started,
            )

        self._history.append(result)
        if self.on_task_end is not None:
            try:
                self.on_task_end(result)
            except Exception:
                pass

        return result

    # -------------------------------------------------------------------------
    #  История
    # -------------------------------------------------------------------------

    def history(self) -> list[TaskResult]:
        """Возвращает копию истории выполненных задач."""
        return list(self._history)

    def clear_history(self) -> None:
        """Очищает историю задач."""
        self._history.clear()

    def stats(self) -> dict[str, int]:
        """
        Возвращает агрегированную статистику по задачам.

        Полезно для отладки и для отчёта в конце сессии.
        """
        total = len(self._history)
        ok = sum(1 for r in self._history if r.success)
        failed = total - ok
        return {
            "total": total,
            "success": ok,
            "failed": failed,
        }


# =============================================================================
#  ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР
# =============================================================================

_manager_instance: SubagentManager | None = None


def get_manager() -> SubagentManager:
    """
    Возвращает глобальный менеджер субагентов.

    Создаёт его при первом обращении и автоматически регистрирует
    все стандартные субагенты (coder, tester, researcher, file_manager).
    """
    global _manager_instance
    if _manager_instance is not None:
        return _manager_instance

    manager = SubagentManager()

    # Регистрируем стандартные субагенты. Импортируем здесь, чтобы
    # избежать циклических зависимостей на уровне модуля.
    try:
        from subagents.coder import CoderSubagent
        manager.register("coder", CoderSubagent())
    except Exception:
        pass

    try:
        from subagents.tester import TesterSubagent
        manager.register("tester", TesterSubagent())
    except Exception:
        pass

    try:
        from subagents.researcher import ResearcherSubagent
        manager.register("researcher", ResearcherSubagent())
    except Exception:
        pass

    try:
        from subagents.file_manager import FileManagerSubagent
        manager.register("file_manager", FileManagerSubagent())
    except Exception:
        pass

    _manager_instance = manager
    return manager


def reset_manager() -> None:
    """
    Сбрасывает глобальный экземпляр менеджера.

    Полезно при тестировании или перезапуске сессии.
    """
    global _manager_instance
    _manager_instance = None