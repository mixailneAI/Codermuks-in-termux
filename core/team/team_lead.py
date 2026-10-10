# =============================================================================
#  Codermuks in Termux — главный агент (TeamLead) v1.1.0
# =============================================================================
#  TeamLead — центральный координатор мультиагентной системы.
#
#  Что делает TeamLead:
#    1. Получает запрос пользователя.
#    2. Читает из реестра, какой агент сейчас лидер.
#    3. Планирует задачу через модель лидера.
#    4. Решает, каких специалистов позвать из команды:
#         • coder   — писать код (обычно Qwen или лидер);
#         • tester  — компилировать и запускать (любой агент);
#         • researcher — искать в интернете (лидер);
#    5. Прогоняет цикл «генерация → компиляция → фикс» до успеха.
#    6. Возвращает финальный AgentResult.
#
#  Отличия от старой логики в core/agent.py:
#    • используется любой провайдер, а не только Mistral;
#    • планировщик — модель лидера, а не всегда Mistral Large;
#    • при падении лидера вызывается fallback (см. fallback.py);
#    • все строки идут через i18n.
# =============================================================================

from __future__ import annotations

import time
from typing import Any, Callable

from core.team.agent_registry import AgentInfo, get_registry
from core.i18n import t


# =============================================================================
#  ИМПОРТЫ ИЗ КОРНЯ (ленивые — внутри методов)
# =============================================================================
#  AgentResult и Step лежат в core/agent.py. Импортируем их лениво,
#  чтобы не создавать циклических зависимостей (agent.py сам зовёт
#  TeamLead в _solve_via_team).
# =============================================================================


# =============================================================================
#  TEAM LEAD
# =============================================================================

class TeamLead:
    """
    Главный агент, координирующий работу команды.

    Экземпляр создаётся на каждый запрос — так проще отслеживать
    состояние конкретной задачи (шаги, заметки, таймер).
    """

    def __init__(
        self,
        on_step: Callable[[Any], None] | None = None,
    ) -> None:
        """
        Аргументы:
            on_step — колбэк, который вызывается на каждом шаге.
                       Используется CLI для обновления таймера.
        """
        self.on_step = on_step
        self.steps: list[Any] = []
        self.notes: list[str] = []
        self._started_at: float = 0.0

        # Реестр агентов (singleton).
        self.registry = get_registry()

        # Имя лидера — заполняется в solve().
        self.lead_name: str = ""

        # Экземпляр провайдера лидера — заполняется в solve().
        self.lead_provider: Any = None

    # -------------------------------------------------------------------------
    #  Вспомогательные методы
    # -------------------------------------------------------------------------

    def _begin_step(self, name: str, detail: str) -> Any:
        """
        Открывает новый шаг рассуждения.

        Создаёт объект Step (из core/agent.py) и уведомляет подписчика.
        Импорт ленивый — чтобы не тянуть core/agent.py сразу.
        """
        from core.agent import Step

        step = Step(name=name, detail=detail, started_at=time.time())
        self.steps.append(step)

        if self.on_step is not None:
            try:
                self.on_step(step)
            except Exception:
                # Ошибки колбэка не должны валить работу.
                pass
        return step

    def _end_step(self, step: Any) -> None:
        """Закрывает шаг и считает его длительность."""
        step.duration = time.time() - step.started_at

    def _note(self, message: str) -> None:
        """Добавляет заметку в список."""
        self.notes.append(message)

    def _build_result(
        self,
        *,
        success: bool,
        language: str = "",
        code: str = "",
        stdout: str = "",
        stderr: str = "",
        exit_code: int = -1,
        iterations: int = 0,
        plan: str = "",
        used_model: str = "",
    ) -> Any:
        """
        Собирает финальный AgentResult.

        Импорт AgentResult ленивый — по той же причине, что и Step.
        """
        from core.agent import AgentResult

        return AgentResult(
            success=success,
            language=language,
            code=code,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            iterations=iterations,
            reasoning_time=time.time() - self._started_at,
            steps=self.steps,
            plan=plan,
            notes=self.notes,
            used_provider=self.lead_name,
            used_model=used_model or self._lead_model(),
        )

    def _lead_model(self) -> str:
        """
        Возвращает имя модели текущего лидера.

        Если провайдер не создан — вернёт пустую строку.
        """
        if self.lead_provider is None:
            return ""
        try:
            return self.lead_provider.get_model()
        except Exception:
            return ""

    def _chat_with_lead(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """
        Отправляет запрос лидеру. При ошибке — срабатывает fallback.

        Возвращает текст ответа. Если ответа нет — пустую строку.

        Исключения:
            Пробрасывает ошибки, если fallback тоже не смог.
        """
        from core.team.fallback import FallbackManager

        try:
            response = self.lead_provider.chat(
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.text or ""

        except Exception as exc:
            # Пробуем fallback на другого агента.
            self._note(f"Лидер {self.lead_name} упал: {exc}. Пробую запасного.")

            fallback = FallbackManager(
                current=self.lead_name,
                on_switch=self._on_fallback_switch,
            )

            alternative = fallback.pick_alternative()
            if alternative is None:
                # Нет альтернативы — пробрасываем исходную ошибку.
                raise

            # Меняем лидера на время выполнения.
            self.lead_name = alternative
            self.lead_provider = self.registry.get_provider(alternative)

            response = self.lead_provider.chat(
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.text or ""

    def _on_fallback_switch(self, old: str, new: str) -> bool:
        """
        Колбэк, вызываемый из FallbackManager при выборе альтернативы.

        Возвращает True, если пользователь подтвердил переключение,
        или если мы работаем в неинтерактивном режиме.
        """
        # В интерактивном режиме — спросим. Если CLI не подключён —
        # всегда говорим «да», чтобы не блокировать работу.
        try:
            from core.i18n import t as tr
            question = tr("fallback.switch", name=old, next=new)
            answer = input(f"{question} ").strip().lower()
            return answer in ("y", "yes", "д", "да")
        except Exception:
            # Нет TTY или ошибка ввода — соглашаемся автоматически.
            return True

    # -------------------------------------------------------------------------
    #  Планирование
    # -------------------------------------------------------------------------

    def _plan_task(self, query: str) -> str:
        """
        Планирует задачу через модель лидера.

        Отправляет запрос планировщику (SYSTEM_PLANNER) и возвращает
        план. Если что-то пошло не так — возвращает заглушку, чтобы
        можно было продолжить генерацию.

        Исключения не выбрасывает — вместо этого возвращает текст-ошибку.
        """
        from prompts.templates import SYSTEM_PLANNER
        from prompts.subagent_prompts import PLANNER_TASK_TEMPLATE

        user_prompt = PLANNER_TASK_TEMPLATE.format(query=query)
        messages = [
            {"role": "system", "content": SYSTEM_PLANNER},
            {"role": "user", "content": user_prompt},
        ]

        try:
            plan = self._chat_with_lead(messages)
            if plan.strip():
                return plan.strip()
        except Exception as exc:
            self._note(f"Планирование не удалось: {exc}")

        # Фолбэк: простой текстовый план без модели.
        return f"Language: auto\nGoal: {query}\nSteps:\n1. Solve the task."

    # -------------------------------------------------------------------------
    #  Определение языка для генерации
    # -------------------------------------------------------------------------

    def _detect_language_from_plan(self, plan: str, query: str) -> str:
        """
        Пытается определить язык программирования из плана или запроса.

        Ищет строку "Language: <lang>" в плане. Если не находит —
        пробует угадать по ключевым словам в запросе.

        Возвращает каноническое имя языка или "python" как дефолт.
        """
        import re

        # 1. Ищем "Language: xxx" в плане.
        match = re.search(r"Language\s*:\s*([A-Za-z0-9#+\-]+)", plan)
        if match:
            return self._normalize_language(match.group(1))

        # 2. Ищем ключевые слова в запросе.
        text = (plan + " " + query).lower()

        aliases = {
            "python": "python", "питон": "python",
            "c++": "cpp", "cpp": "cpp", "плюсы": "cpp",
            "rust": "rust", "раст": "rust",
            "go": "go", "golang": "go", "го": "go",
            "java ": "java", "джава": "java",
            "javascript": "javascript", "js ": "javascript", "нода": "javascript",
            "c#": "csharp", "csharp": "csharp", "си шарп": "csharp",
            "kotlin": "kotlin", "котлин": "kotlin",
            "swift": "swift", "свифт": "swift",
            "ruby": "ruby", "руби": "ruby",
            "php": "php",
            "dart": "dart",
            "elixir": "elixir",
            "haskell": "haskell", "хаскель": "haskell",
            "lua": "lua", "луа": "lua",
            "c ": "c",
        }

        for key, canonical in aliases.items():
            if key in text:
                return canonical

        # 3. Дефолт.
        return "python"

    @staticmethod
    def _normalize_language(raw: str) -> str:
        """
        Приводит произвольное имя языка к каноническому.

        Использует таблицу алиасов из subagents/coder.py, чтобы не
        дублировать логику.
        """
        if not raw:
            return "python"
        try:
            from subagents.coder import LANGUAGE_ALIASES
            return LANGUAGE_ALIASES.get(raw.strip().lower(), raw.strip().lower())
        except Exception:
            return raw.strip().lower()

    # -------------------------------------------------------------------------
    #  Генерация кода
    # -------------------------------------------------------------------------

    def _generate_code(
        self,
        query: str,
        plan: str,
        language: str,
        research: str = "",
    ) -> tuple[str, str]:
        """
        Просит лидера написать код.

        Возвращает кортеж (raw_response, extracted_code).

        Если ответ пустой — возвращает ("", "").
        """
        from prompts.templates import SYSTEM_CODER
        from prompts.subagent_prompts import CODER_TASK_TEMPLATE

        user_prompt = CODER_TASK_TEMPLATE.format(
            query=query,
            plan=plan,
            research=research or "(no research performed)",
        )
        messages = [
            {"role": "system", "content": SYSTEM_CODER},
            {"role": "user", "content": user_prompt},
        ]

        try:
            raw = self._chat_with_lead(messages, temperature=0.2)
        except Exception as exc:
            self._note(f"Генерация кода не удалась: {exc}")
            return "", ""

        # Извлекаем код из ответа.
        code = self._extract_code(raw)
        return raw, code

    def _fix_code(
        self,
        language: str,
        code: str,
        stderr: str,
        stdout: str,
        iteration: int,
    ) -> tuple[str, str]:
        """
        Просит лидера исправить код по ошибке компиляции.

        Возвращает кортеж (raw_response, extracted_code).
        """
        from prompts.templates import SYSTEM_CODER
        from prompts.subagent_prompts import FIX_TASK_TEMPLATE

        user_prompt = FIX_TASK_TEMPLATE.format(
            language=language,
            code=code,
            stderr=stderr,
            stdout=stdout,
            iteration=iteration,
        )
        messages = [
            {"role": "system", "content": SYSTEM_CODER},
            {"role": "user", "content": user_prompt},
        ]

        try:
            raw = self._chat_with_lead(messages, temperature=0.2)
        except Exception as exc:
            self._note(f"Фикс не удался: {exc}")
            return "", ""

        new_code = self._extract_code(raw)
        return raw, new_code

    @staticmethod
    def _extract_code(text: str) -> str:
        """
        Извлекает первый блок кода из ответа модели.

        Поддерживает стандартный markdown-формат с ```язык ... ```.
        """
        if not text:
            return ""

        import re

        pattern = re.compile(
            r"```(?:[a-zA-Z0-9_+\-#]*)\s*\n(.*?)```",
            re.DOTALL,
        )
        match = pattern.search(text)
        if match:
            return match.group(1).rstrip()

        # Если блоков нет — возможно, весь ответ является кодом.
        # Тогда возвращаем как есть (но это редкий случай).
        return ""

    # -------------------------------------------------------------------------
    #  Исследование
    # -------------------------------------------------------------------------

    def _do_research(self, query: str) -> str:
        """
        Запускает исследование через субагента researcher.

        Возвращает текстовый контекст. Если что-то упало — возвращает
        пустую строку (не валим всю задачу).
        """
        try:
            from subagents.researcher import ResearcherSubagent
            researcher = ResearcherSubagent()
            context = researcher.run(query)
            if context:
                self._note(f"Собрано контекста: {len(context)} символов.")
            return context or ""
        except Exception as exc:
            self._note(f"Исследование не удалось: {exc}")
            return ""

    # -------------------------------------------------------------------------
    #  Компиляция и запуск
    # -------------------------------------------------------------------------

    def _compile_and_run(self, language: str, code: str) -> dict[str, Any]:
        """
        Компилирует и запускает код через subagents/tester.py.

        Возвращает словарь с ключами stdout, stderr, exit_code, stage.
        """
        try:
            from subagents.tester import TesterSubagent
            tester = TesterSubagent()
            return tester.test(language, code)
        except Exception as exc:
            return {
                "stdout": "",
                "stderr": f"Ошибка тестирования: {exc}",
                "exit_code": -1,
                "duration": 0.0,
                "language": language,
                "stage": "internal",
            }

    # -------------------------------------------------------------------------
    #  Основной метод
    # -------------------------------------------------------------------------

    def solve(
        self,
        query: str,
        skills: list[str] | None = None,
    ) -> Any:
        """
        Основной цикл работы команды.

        Аргументы:
            query  — запрос пользователя.
            skills — активные скиллы (deep_research, reasoning, analysis).

        Возвращает:
            AgentResult с финальным кодом и метриками.
        """
        from core import config

        self.steps = []
        self.notes = []
        self._started_at = time.time()

        active_skills = skills or []

        # --- Шаг 0: определяем лидера --------------------------------------
        lead_step = self._begin_step("инициализация", "определяю главного агента")
        self.lead_name = self.registry.get_lead()

        try:
            self.lead_provider = self.registry.get_provider(self.lead_name)
        except Exception as exc:
            self._end_step(lead_step)
            return self._build_result(
                success=False,
                stderr=f"Не удалось создать провайдера {self.lead_name}: {exc}",
            )

        if not self.registry.is_configured(self.lead_name):
            self._end_step(lead_step)
            return self._build_result(
                success=False,
                stderr=t(
                    "err.provider_not_configured",
                    name=self.lead_name,
                ),
            )

        self._note(f"Лидер команды: {self.lead_name}")
        self._end_step(lead_step)

        # --- Шаг 1: планирование -------------------------------------------
        plan_step = self._begin_step("планирование", "разбираю задачу")
        plan = self._plan_task(query)
        self._end_step(plan_step)

        # --- Шаг 2: определение языка --------------------------------------
        language = self._detect_language_from_plan(plan, query)
        self._note(f"Язык программирования: {language}")

        # --- Шаг 3: исследование (если включён deep_research) -------------
        research = ""
        if "deep_research" in active_skills:
            res_step = self._begin_step("исследование", "ищу информацию")
            research = self._do_research(query)
            self._end_step(res_step)

        # --- Шаг 4: генерация кода -----------------------------------------
        gen_step = self._begin_step("генерация", "пишу код")
        _, code = self._generate_code(query, plan, language, research)
        self._end_step(gen_step)

        if not code.strip():
            return self._build_result(
                success=False,
                language=language,
                plan=plan,
                stderr=t("result.no_code"),
            )

        # --- Шаг 5: цикл «компиляция → фикс» -------------------------------
        final_stdout = ""
        final_stderr = ""
        final_exit_code = -1
        iterations = 0

        for iteration in range(config.MAX_FIX_ITERATIONS + 1):
            test_step = self._begin_step(
                "компиляция",
                f"{language}, попытка {iteration + 1}",
            )
            run_result = self._compile_and_run(language, code)
            self._end_step(test_step)

            final_stdout = run_result.get("stdout", "") or ""
            final_stderr = run_result.get("stderr", "") or ""
            final_exit_code = int(run_result.get("exit_code", -1))

            # Успех?
            if final_exit_code == 0 and not final_stderr.strip():
                self._note(f"Успех на итерации {iteration + 1}.")
                break

            # Попытки кончились?
            if iteration >= config.MAX_FIX_ITERATIONS:
                self._note("Исчерпаны попытки фикса.")
                break

            # Пробуем исправить.
            fix_step = self._begin_step(
                "фикс",
                f"итерация {iteration + 1}",
            )
            _, new_code = self._fix_code(
                language=language,
                code=code,
                stderr=final_stderr,
                stdout=final_stdout,
                iteration=iteration + 1,
            )
            if new_code.strip():
                code = new_code
            else:
                self._note("Кодер вернул пустой ответ — оставляю прежний код.")
            self._end_step(fix_step)
            iterations = iteration + 1

        # --- Финальный результат -------------------------------------------
        success = final_exit_code == 0 and not final_stderr.strip()

        return self._build_result(
            success=success,
            language=language,
            code=code,
            stdout=final_stdout,
            stderr=final_stderr,
            exit_code=final_exit_code,
            iterations=iterations,
            plan=plan,
        )


# =============================================================================
#  ЭКСПОРТ
# =============================================================================

__all__ = ["TeamLead"]