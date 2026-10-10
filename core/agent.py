# =============================================================================
#  Codermuks in Termux — оркестратор v1.1.0
# =============================================================================
#  Что изменилось в v1.1.0:
#    • Работает через TeamLead — команду из нескольких агентов.
#    • Главный агент выбирается пользователем (по умолчанию — Mistral).
#    • При падении главного агента — переключение на запасного.
#    • Все служебные сообщения идут через i18n (EN/RU).
#
#  Сохранена обратная совместимость:
#    • Если модуль core/team/ ещё не готов — используется старая логика
#      через core/mistral_client.py (v1.0.x).
#    • Это позволяет запускать проект в процессе миграции.
#
#  Цикл работы остался прежним:
#    1. Планирование задачи.
#    2. Генерация кода.
#    3. Компиляция и запуск.
#    4. Если ошибка — фикс и повтор.
#    5. Возврат результата с таймером рассуждения.
# =============================================================================

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable


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
    used_provider: str = ""                # какой провайдер дал финальный ответ
    used_model: str = ""                   # какая модель дала финальный ответ


# =============================================================================
#  ОРКЕСТРАТОР
# =============================================================================

class Agent:
    """
    Главный агент. Связывает планировщик, кодера, тестировщика и
    файлового менеджера в единый рабочий цикл.

    В v1.1.0 вся реальная работа делегируется в TeamLead, который
    сам решает, какой провайдер использовать для каждой задачи.
    Agent остаётся фасадом для обратной совместимости.
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
        # Флаг: доступен ли новый путь через TeamLead.
        self._team_available: bool | None = None

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

    def _check_team(self) -> bool:
        """
        Проверяет, доступен ли модуль core/team/.

        Результат кэшируется, чтобы не пытаться импортировать
        на каждый запрос. Если модуль ещё не написан — работаем
        по старой схеме через mistral_client.
        """
        if self._team_available is not None:
            return self._team_available

        try:
            from core.team.team_lead import TeamLead  # noqa: F401
            self._team_available = True
        except ImportError:
            self._team_available = False

        return self._team_available

    # -------------------------------------------------------------------------
    #  Точка входа
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
        self.steps = []
        self.notes = []
        self._started_at = time.time()

        # Сбрасываем кэш доступности team при каждом запуске,
        # чтобы пользователь мог установить team-модули без перезапуска.
        self._team_available = None

        if self._check_team():
            # Новый путь — через TeamLead.
            return self._solve_via_team(query, skills or [])
        else:
            # Старый путь — через mistral_client (v1.0.x).
            return self._solve_via_mistral(query, skills or [])

    # -------------------------------------------------------------------------
    #  Новый путь: через TeamLead
    # -------------------------------------------------------------------------

    def _solve_via_team(
        self,
        query: str,
        skills: list[str],
    ) -> AgentResult:
        """
        Решение задачи через мультиагентную команду.

        Делегирует всю работу в TeamLead, который:
            • выбирает главного агента;
            • планирует задачу;
            • зовёт специалистов;
            • собирает финальный ответ.
        """
        from core.team.team_lead import TeamLead

        try:
            lead = TeamLead(on_step=self._begin_step)
            result = lead.solve(query, skills=skills)

            # Дополняем result заметками и шагами из агента.
            result.steps = self.steps + getattr(result, "steps", [])
            result.notes = self.notes + getattr(result, "notes", [])

            # Если TeamLead не заполнил reasoning_time — считаем сами.
            if not getattr(result, "reasoning_time", 0):
                result.reasoning_time = time.time() - self._started_at

            return result

        except Exception as exc:
            # Если TeamLead сломался — падаем обратно на старую логику.
            self._note(f"TeamLead недоступен: {exc}. Использую старую схему.")
            return self._solve_via_mistral(query, skills)

    # -------------------------------------------------------------------------
    #  Старый путь: через mistral_client (v1.0.x, для совместимости)
    # -------------------------------------------------------------------------

    def _solve_via_mistral(
        self,
        query: str,
        skills: list[str],
    ) -> AgentResult:
        """
        Резервная логика для случая, когда team-модули ещё не готовы.

        Полностью повторяет поведение v1.0.x: планирование, генерация,
        компиляция, фикс через mistral_client.
        """
        from core import config
        from core.mistral_client import get_client
        from subagents.coder import CoderSubagent
        from subagents.tester import TesterSubagent
        from subagents.researcher import ResearcherSubagent
        from prompts.templates import SYSTEM_PLANNER, SYSTEM_CODER
        from prompts.subagent_prompts import (
            CODER_TASK_TEMPLATE,
            FIX_TASK_TEMPLATE,
            PLANNER_TASK_TEMPLATE,
        )

        active_skills = skills or []
        client = get_client()

        # --- Шаг 1: планирование ------------------------------------------
        plan_step = self._begin_step("планирование", "разбираю задачу и составляю план")
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
                used_provider="mistral",
                used_model=config.PLANNER_MODEL,
            )
        self._end_step(plan_step)

        # --- Шаг 2: исследование (если включён deep_research) --------------
        research_context = ""
        if "deep_research" in active_skills:
            res_step = self._begin_step("исследование", "ищу информацию в интернете")
            researcher = ResearcherSubagent()
            try:
                research_context = researcher.run(query)
                self._note(f"Собрано контекста: {len(research_context)} символов.")
            except Exception as exc:
                self._note(f"Исследование не удалось: {exc}")
            self._end_step(res_step)

        # --- Шаг 3: генерация кода -----------------------------------------
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
                used_provider="mistral",
                used_model=config.CODING_MODEL,
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
                f"компилирую и запускаю код ({language}) — попытка {iteration + 1}",
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
                    used_provider="mistral",
                    used_model=config.CODING_MODEL,
                )
            self._end_step(test_step)

            final_stdout = run_result.get("stdout", "")
            final_stderr = run_result.get("stderr", "")
            final_exit_code = int(run_result.get("exit_code", -1))

            if final_exit_code == 0 and not final_stderr.strip():
                self._note(f"Успех на итерации {iteration + 1}.")
                break

            if iteration >= config.MAX_FIX_ITERATIONS:
                self._note("Исчерпаны попытки исправления.")
                break

            # --- Фикс: просим кодера исправить ошибку ----------------------
            fix_step = self._begin_step(
                "фикс",
                f"исправляю ошибки компиляции — итерация {iteration + 1}",
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
            used_provider="mistral",
            used_model=config.CODING_MODEL,
        )


# =============================================================================
#  ЭКСПОРТ
# =============================================================================

__all__ = ["Agent", "AgentResult", "Step"]