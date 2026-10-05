# =============================================================================
#  Codermuks in Termux — оркестратор (главный агент)
# =============================================================================
#  Это ядро всей системы. Оркестратор:
#    1. Принимает запрос пользователя.
#    2. Просит модель-планировщик разобрать задачу.
#    3. Просит субагента-кодера написать код.
#    4. Передаёт код субагенту-тестировщику (компиляция + запуск).
#    5. Если есть ошибки — просит кодера исправить, и так до MAX_FIX_ITERATIONS.
#    6. Когда всё чисто — возвращает финальный результат.
#
#  Также оркестратор ведёт таймер рассуждения: сколько секунд прошло
#  с момента запуска задачи до финального ответа.
# =============================================================================

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable


# =============================================================================
#  СТРУКТУРЫ ДАННЫХ
# =============================================================================

@dataclass
class Step:
    """Один шаг рассуждения агента."""
    name: str          # «планирование», «генерация», «компиляция», «фикс»...
    detail: str        # короткое описание, что именно делает агент
    started_at: float  # время старта шага (unix timestamp)
    duration: float = 0.0  # длительность шага в секундах


@dataclass
class AgentResult:
    """Результат работы оркестратора."""
    success: bool                          # удалось ли решить задачу
    language: str                          # язык, на котором написан код
    code: str                              # финальный код
    stdout: str                            # вывод программы
    stderr: str                            # ошибки программы (пусто при успехе)
    exit_code: int                         # код возврата
    iterations: int                        # сколько было итераций фикса
    reasoning_time: float                  # общее время рассуждения (сек)
    steps: list[Step] = field(default_factory=list)   # все шаги
    plan: str = ""                         # план от планировщика
    notes: list[str] = field(default_factory=list)    # заметки по ходу


# =============================================================================
#  ОРКЕСТРАТОР
# =============================================================================

class Agent:
    """
    Главный агент. Связывает планировщик, кодера, тестировщика и
    файлового менеджера в единый рабочий цикл.
    """

    def __init__(
        self,
        on_step: Callable[[Step], None] | None = None,
    ) -> None:
        """
        Аргументы:
            on_step — колбэк, который вызывается на каждом шаге.
                       CLI использует его, чтобы обновлять таймер.
        """
        self.on_step = on_step
        self.steps: list[Step] = []
        self.notes: list[str] = []
        self._started_at: float = 0.0

    # -------------------------------------------------------------------------
    #  Вспомогательные методы
    # -------------------------------------------------------------------------

    def _begin_step(self, name: str, detail: str) -> Step:
        """
        Открывает новый шаг рассуждения.

        Создаёт объект Step, добавляет его в список и уведомляет
        подписчика (CLI), чтобы тот обновил интерфейс.
        """
        step = Step(name=name, detail=detail, started_at=time.time())
        self.steps.append(step)
        if self.on_step is not None:
            try:
                self.on_step(step)
            except Exception:
                # Ошибки колбэка не должны валить агента.
                pass
        return step

    def _end_step(self, step: Step) -> None:
        """Закрывает шаг и считает его длительность."""
        step.duration = time.time() - step.started_at

    def _note(self, message: str) -> None:
        """Добавляет заметку в общий список."""
        self.notes.append(message)

    # -------------------------------------------------------------------------
    #  Основной цикл
    # -------------------------------------------------------------------------

    def solve(self, query: str, skills: list[str] | None = None) -> AgentResult:
        """
        Решает задачу пользователя.

        Аргументы:
            query  — запрос пользователя (естественный язык).
            skills — список активных скиллов: "deep_research", "reasoning", "analysis".

        Возвращает:
            AgentResult с финальным кодом, выводом и метриками.
        """
        # Импортируем здесь, чтобы избежать циклических зависимостей на уровне модуля.
        from core import config
        from core.mistral_client import get_client
        from subagents.coder import CoderSubagent
        from subagents.tester import TesterSubagent
        from subagents.researcher import ResearcherSubagent
        from prompts.templates import (
            SYSTEM_PLANNER,
            SYSTEM_CODER,
        )
        from prompts.subagent_prompts import (
            CODER_TASK_TEMPLATE,
            FIX_TASK_TEMPLATE,
            PLANNER_TASK_TEMPLATE,
        )

        self.steps = []
        self.notes = []
        self._started_at = time.time()

        active_skills = skills or []

        # --- Шаг 1: планирование --------------------------------------------
        plan_step = self._begin_step("планирование", "разбираю задачу и составляю план")
        client = get_client()

        planner_user_prompt = PLANNER_TASK_TEMPLATE.format(query=query)
        try:
            plan = client.plan(SYSTEM_PLANNER, planner_user_prompt)
            self._note(f"План получен ({len(plan)} символов).")
        except Exception as exc:
            self._end_step(plan_step)
            return AgentResult(
                success=False,
                language="",
                code="",
                stdout="",
                stderr=f"Ошибка планирования: {exc}",
                exit_code=-1,
                iterations=0,
                reasoning_time=time.time() - self._started_at,
                steps=self.steps,
                plan="",
                notes=self.notes,
            )
        self._end_step(plan_step)

        # --- Шаг 2: исследование (если включён deep_research) --------------
        research_context = ""
        if "deep_research" in active_skills:
            res_step = self._begin_step("исследование", "ищу информацию в интернете и на GitHub")
            researcher = ResearcherSubagent()
            try:
                research_context = researcher.run(query)
                self._note(f"Собрано контекста: {len(research_context)} символов.")
            except Exception as exc:
                self._note(f"Исследование не удалось: {exc}")
            self._end_step(res_step)

        # --- Шаг 3: определение языка и генерация кода ---------------------
        coder = CoderSubagent()
        tester = TesterSubagent()

        gen_step = self._begin_step("генерация", "пишу код")
        coder_prompt = CODER_TASK_TEMPLATE.format(
            query=query,
            plan=plan,
            research=research_context or "(исследование не проводилось)",
        )
        try:
            raw_response = client.code(SYSTEM_CODER, coder_prompt)
            language, code = coder.parse_response(raw_response)
        except Exception as exc:
            self._end_step(gen_step)
            return AgentResult(
                success=False,
                language="",
                code="",
                stdout="",
                stderr=f"Ошибка генерации кода: {exc}",
                exit_code=-1,
                iterations=0,
                reasoning_time=time.time() - self._started_at,
                steps=self.steps,
                plan=plan,
                notes=self.notes,
            )
        self._end_step(gen_step)

        # --- Шаг 4: цикл «компиляция → фикс» -------------------------------
        final_stdout = ""
        final_stderr = ""
        final_exit_code = -1
        iterations = 0

        for iteration in range(config.MAX_FIX_ITERATIONS + 1):
            test_step = self._begin_step(
                "компиляция",
                f"компилирую и запускаю код ({language}) — попытка {iteration + 1}"
            )
            try:
                run_result = tester.test(language, code)
            except Exception as exc:
                self._end_step(test_step)
                return AgentResult(
                    success=False,
                    language=language,
                    code=code,
                    stdout="",
                    stderr=f"Ошибка тестирования: {exc}",
                    exit_code=-1,
                    iterations=iteration,
                    reasoning_time=time.time() - self._started_at,
                    steps=self.steps,
                    plan=plan,
                    notes=self.notes,
                )
            self._end_step(test_step)

            final_stdout = run_result.get("stdout", "")
            final_stderr = run_result.get("stderr", "")
            final_exit_code = int(run_result.get("exit_code", -1))

            # Если компиляция и запуск прошли чисто — выходим из цикла.
            if final_exit_code == 0 and not final_stderr.strip():
                self._note(f"Успех на итерации {iteration + 1}.")
                break

            # Если это была последняя разрешённая попытка — прекращаем.
            if iteration >= config.MAX_FIX_ITERATIONS:
                self._note("Исчерпаны попытки исправления.")
                break

            # --- Фикс: просим кодера исправить ошибку ----------------------
            fix_step = self._begin_step(
                "фикс",
                f"исправляю ошибки компиляции — итерация {iteration + 1}"
            )
            fix_prompt = FIX_TASK_TEMPLATE.format(
                language=language,
                code=code,
                stderr=final_stderr,
                stdout=final_stdout,
                iteration=iteration + 1,
            )
            try:
                fix_response = client.code(SYSTEM_CODER, fix_prompt)
                new_language, new_code = coder.parse_response(fix_response)
                if new_code.strip():
                    code = new_code
                    if new_language:
                        language = new_language
                else:
                    self._note("Кодер вернул пустой ответ — оставляем прежний код.")
            except Exception as exc:
                self._note(f"Фикс не удался: {exc}")
            self._end_step(fix_step)
            iterations = iteration + 1

        # --- Финальный результат -------------------------------------------
        success = final_exit_code == 0 and not final_stderr.strip()

        return AgentResult(
            success=success,
            language=language,
            code=code,
            stdout=final_stdout,
            stderr=final_stderr,
            exit_code=final_exit_code,
            iterations=iterations,
            reasoning_time=time.time() - self._started_at,
            steps=self.steps,
            plan=plan,
            notes=self.notes,
        )