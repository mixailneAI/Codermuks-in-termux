# =============================================================================
#  Codermuks in Termux — главный агент (TeamLead) v1.4.0
# =============================================================================
#  Что нового:
#    • Работа через Project (создание/открытие реальных папок).
#    • EventBus — real-time события для UI.
#    • JSON-планирование (action, project_name, plan).
#    • Формат ### FILE: для многофайловых проектов.
#    • История задач проекта.
# =============================================================================

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Callable

from core.events import emit, LEVEL_INFO, LEVEL_SUCCESS, LEVEL_ERROR, LEVEL_PROGRESS
from core.project import Project
from core.team.agent_registry import get_registry
from core.workspace import list_projects


# Регулярка для парсинга ### FILE: <path> + ```lang\n...```
FILE_BLOCK_RE = re.compile(
    r"###\s*FILE:\s*(?P<path>[^\s]+)\s*\n"
    r"```[a-zA-Z0-9_+\-#]*\s*\n"
    r"(?P<content>.*?)"
    r"\n```",
    re.DOTALL,
)


class TeamLead:
    """Главный агент, координирующий работу команды."""

    def __init__(self, on_step: Callable[[Any], None] | None = None) -> None:
        self.on_step = on_step
        self.steps: list[Any] = []
        self.notes: list[str] = []
        self._started_at: float = 0.0
        self.registry = get_registry()
        self.lead_name: str = ""
        self.lead_provider: Any = None
        self.project: Project | None = None
        self.forced_project: str = ""  # имя проекта, открытого через /open
        self._last_error: str = ""  # текст последней ошибки провайдера

    # --- Шаги ------------------------------------------------------------

    def _begin_step(self, name: str, detail: str) -> Any:
        from core.agent import Step
        step = Step(name=name, detail=detail, started_at=time.time())
        self.steps.append(step)
        if self.on_step is not None:
            try:
                self.on_step(step)
            except Exception:
                pass
        return step

    def _end_step(self, step: Any) -> None:
        step.duration = time.time() - step.started_at

    def _note(self, message: str) -> None:
        self.notes.append(message)

    # --- Результат -------------------------------------------------------

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
        if self.lead_provider is None:
            return ""
        try:
            return self.lead_provider.get_model()
        except Exception:
            return ""

    # --- Общение с лидером ----------------------------------------------

    # --- Общение с лидером с fallback ------------------------------------

    def _is_permanent_error(self, error_text: str) -> bool:
        """Permanent — ошибка аккаунта (не деньги, не временно)."""
        low = error_text.lower()
        return any(kw in low for kw in (
            "402", "insufficient", "balance", "payment required",
            "401", "403", "unauthorized", "invalid api key",
            "forbidden", "no permission", "quota",
        ))

    def _chat(self, messages: list[dict], temperature: float | None = None) -> str:
        """
        Отправляет запрос лидеру. При падении — fallback на следующего.

        Логика:
            1. Пробуем текущего лидера.
            2. Если permanent error (402/401/403) — молча переключаемся.
            3. Если временная ошибка — спрашиваем пользователя.
            4. Если альтернатив нет — возвращаем "".
        """
        from core.team.fallback import FallbackManager
        from core.events import emit

        try:
            resp = self.lead_provider.chat(messages, temperature=temperature)
            return resp.text or ""
        except Exception as exc:
            error_text = str(exc)
            self._note(f"Лидер {self.lead_name} упал: {error_text}")
            self._last_error = error_text

        # Fallback
        fallback = FallbackManager(
            current=self.lead_name,
            on_switch=self._on_fallback_switch,
        )
        alternative = fallback.pick_alternative()

        if alternative is None:
            self._note("Нет доступных альтернатив.")
            return ""

        # Переключаемся.
        old_lead = self.lead_name
        self._note(f"Переключаюсь {old_lead} → {alternative}")
        self.lead_name = alternative
        try:
            self.lead_provider = self.registry.get_provider(alternative)
        except Exception as exc:
            self._note(f"Не удалось создать провайдер {alternative}: {exc}")
            return ""

        # Пробуем на новом.
        try:
            resp = self.lead_provider.chat(messages, temperature=temperature)
            return resp.text or ""
        except Exception as exc:
            self._note(f"Альтернатива {alternative} тоже упала: {exc}")
            return ""

    def _on_fallback_switch(self, old: str, new: str) -> bool:
        """
        Колбэк FallbackManager при переключении.

        Для permanent ошибок (402/401/403) — автода.
        Иначе — спрашиваем с pause LivePanel.
        """
        from core.events import emit

        err = getattr(self, "_last_error", "").lower()

        # Permanent — соглашаемся молча, чтобы не мучить пользователя.
        if self._is_permanent_error(err):
            self._note(f"Авто-переключение {old} → {new} (permanent error)")
            return True

        # Временная ошибка — спрашиваем.
        emit("ui.pause", {})
        try:
            try:
                question = (
                    f"Провайдер {old} недоступен. "
                    f"Переключиться на {new}? [y/n]:"
                )
                answer = input(f"  {question} ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                return False
            return answer in ("y", "yes", "д", "да")
        finally:
            emit("ui.resume", {})


    # --- Парсинг JSON от LLM --------------------------------------------

    @staticmethod
    def _parse_json(text: str) -> dict | None:
        if not text:
            return None
        text = text.strip()
        # Убираем markdown-обёртку, если есть.
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
            text = re.sub(r"\s*```\s*$", "", text)
        # Ищем первый {...}
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _parse_files(text: str) -> dict[str, str]:
        result: dict[str, str] = {}
        for match in FILE_BLOCK_RE.finditer(text):
            path = match.group("path").strip()
            content = match.group("content").rstrip()
            if path and content:
                result[path] = content
        return result


    # --- Шаг: определить проект -----------------------------------------

    def _detect_project(self, query: str) -> tuple[str, str]:
        """Возвращает (action, project_name)."""
        # Если пользователь открыл проект через /open — используем его.
        if self.forced_project:
            return ("continue", self.forced_project)

        from prompts.templates import SYSTEM_PROJECT_DECIDER
        from prompts.subagent_prompts import PROJECT_DECIDER_TASK_TEMPLATE

        projects = list_projects()
        if projects:
            lines = []
            for p in projects[:20]:
                lang = p.get("language") or "?"
                lines.append(f"- {p['name']} ({lang})")
            projects_list = "\n".join(lines)
        else:
            projects_list = "(нет проектов)"

        prompt = PROJECT_DECIDER_TASK_TEMPLATE.format(
            query=query,
            projects_list=projects_list,
        )
        messages = [
            {"role": "system", "content": SYSTEM_PROJECT_DECIDER},
            {"role": "user", "content": prompt},
        ]
        raw = self._chat(messages, temperature=0.1)
        parsed = self._parse_json(raw)

        if not parsed:
            from utils.naming import guess_project_name_from_query
            return ("new", guess_project_name_from_query(query))

        action = str(parsed.get("action", "new")).lower()
        if action not in ("continue", "create", "new"):
            action = "new"

        name = str(parsed.get("project_name", "")).strip()
        if not name:
            from utils.naming import guess_project_name_from_query
            name = guess_project_name_from_query(query)

        return (action, name)

    def _open_or_create_project(self, action: str, name: str) -> Project:
        if action == "continue":
            proj = Project.open(name)
            if proj is not None:
                emit("project.opened", {"name": proj.name})
                self._note(f"Открыт проект: {proj.name}")
                return proj

        proj = Project.create(name)
        emit("project.created", {"name": proj.name})
        self._note(f"Создан проект: {proj.name}")
        return proj

    # --- Шаг: планирование ----------------------------------------------

    def _plan(self, query: str, project: Project) -> dict:
        from prompts.templates import SYSTEM_PLANNER
        from prompts.subagent_prompts import PLANNER_TASK_TEMPLATE

        files = project.list_files()
        files_list = "\n".join(f"- {f}" for f in files) if files else "(пусто)"

        history_ctx = project.get_context_for_llm(limit=5) or "(нет истории)"

        prompt = PLANNER_TASK_TEMPLATE.format(
            query=query,
            project_name=project.name,
            language=project.language or "(не определён)",
            files_list=files_list,
            history_context=history_ctx,
        )
        messages = [
            {"role": "system", "content": SYSTEM_PLANNER},
            {"role": "user", "content": prompt},
        ]
        raw = self._chat(messages, temperature=0.3)
        parsed = self._parse_json(raw)

        if not parsed:
            return {
                "language": "python",
                "goal": query,
                "steps": ["реализовать задачу"],
                "requirements": [],
                "edge_cases": [],
                "files_to_modify": [],
                "files_to_create": [],
            }

        return parsed


    # --- Шаг: генерация кода --------------------------------------------

    def _generate(self, query: str, project: Project, plan: dict) -> dict[str, str]:
        from prompts.templates import SYSTEM_CODER
        from prompts.subagent_prompts import CODER_TASK_TEMPLATE

        # Собираем содержимое файлов, которые надо изменить.
        to_modify = plan.get("files_to_modify", []) or []
        existing_parts = []
        for rel in to_modify:
            content = project.read_file(rel)
            if content:
                existing_parts.append(f"### {rel}\n{content}")
        existing_files = "\n\n".join(existing_parts) if existing_parts else "(нет)"

        plan_str = json.dumps(plan, ensure_ascii=False, indent=2)

        prompt = CODER_TASK_TEMPLATE.format(
            query=query,
            project_name=project.name,
            language=plan.get("language", ""),
            plan=plan_str,
            existing_files=existing_files,
        )
        messages = [
            {"role": "system", "content": SYSTEM_CODER},
            {"role": "user", "content": prompt},
        ]
        raw = self._chat(messages, temperature=0.2)
        files = self._parse_files(raw)

        if not files:
            # Фолбэк: пробуем как один блок ```lang ... ```
            block = re.search(r"```[a-zA-Z0-9_+\-#]*\s*\n(.*?)```", raw, re.DOTALL)
            if block:
                lang = plan.get("language", "python")
                ext = {"python": ".py", "go": ".go", "rust": ".rs",
                       "cpp": ".cpp", "c": ".c", "java": ".java",
                       "javascript": ".js"}.get(lang, ".txt")
                files = {f"main{ext}": block.group(1).rstrip()}

        return files

    # --- Шаг: компиляция/запуск -----------------------------------------

    def _run(self, project: Project, files: dict[str, str], language: str) -> dict:
        # Пока используем существующий TesterSubagent для компиляции/запуска
        # во временной папке. Проект сохраняется отдельно.
        if not files:
            return {"stdout": "", "stderr": "нет файлов", "exit_code": -1,
                    "stage": "no_files", "duration": 0.0, "language": language}

        # Берём первый файл как основной.
        first_path = next(iter(files))
        code = files[first_path]

        try:
            from subagents.tester import TesterSubagent
            tester = TesterSubagent()
            return tester.test(language, code)
        except Exception as exc:
            return {"stdout": "", "stderr": f"Ошибка теста: {exc}",
                    "exit_code": -1, "stage": "internal",
                    "duration": 0.0, "language": language}

    def _fix(self, project: Project, files: dict[str, str], language: str,
             stderr: str, stdout: str, iteration: int) -> dict[str, str]:
        from prompts.templates import SYSTEM_FIXER
        from prompts.subagent_prompts import FIXER_TASK_TEMPLATE

        parts = []
        for path, content in files.items():
            parts.append(f"### {path}\n{content}")
        current = "\n\n".join(parts)

        prompt = FIXER_TASK_TEMPLATE.format(
            iteration=iteration,
            project_name=project.name,
            language=language,
            current_files=current,
            stdout=stdout,
            stderr=stderr,
        )
        messages = [
            {"role": "system", "content": SYSTEM_FIXER},
            {"role": "user", "content": prompt},
        ]
        raw = self._chat(messages, temperature=0.2)
        new_files = self._parse_files(raw)
        return new_files or files

    # --- Roblox ----------------------------------------------------------

    def _ask_roblox_path(self) -> str:
        """Спрашивает путь к StudioMCP. Live-панель на время ввода замирает."""
        from core.events import emit
        from pathlib import Path

        emit("ui.pause", {})

        try:
            print()
            print("  \u23f8  Рассуждение приостановлено для ввода.")
            print()
            print("  \u26a0\ufe0f  Roblox Studio не найден автоматически.")
            print()
            print("  ВАЖНО: Roblox Studio должен быть на той же машине,")
            print("         что и Codermuks.")
            print("         Если ты в Termux (Android), а Studio на ПК —")
            print("         запусти Codermuks на ПК, а не на телефоне.")
            print()
            print("  Как подключить MCP в Roblox Studio:")
            print("    1. Открой Roblox Studio.")
            print("    2. Assistant → \u22ef → Manage MCP Servers → Enable.")
            print("    3. Studio покажет готовую команду запуска StudioMCP.")
            print("    4. Скопируй путь к исполняемому файлу.")
            print()
            print("  Примеры:")
            print("    Windows: C:\\Users\\you\\AppData\\Local\\Roblox\\Versions\\...\\StudioMCP.exe")
            print("    macOS:   /Applications/RobloxStudio.app/Contents/MacOS/StudioMCP")
            print()
            print("  Введи путь к StudioMCP (или Enter для отмены):")

            try:
                answer = input("  \u25b8 ").strip()
            except KeyboardInterrupt:
                print()
                raise
            except EOFError:
                print()
                return ""

            if not answer:
                return ""

            if not Path(answer).is_file():
                print(f"  \u2718 Файл не найден: {answer}")
                return ""

            from core.roblox.discovery import save_manual_path
            save_manual_path(answer)
            print(f"  \u2714 Путь сохранён: {answer}")
            return answer
        finally:
            emit("ui.resume", {})


    def _ensure_roblox_connected(self) -> bool:
        """
        Убеждается, что Roblox подключён.

        Если MCP не найден автоматически — спрашивает путь.
        Возвращает True, если подключение удалось.
        """
        from core.roblox import is_available, ensure_connected, disconnect
        from core.roblox.discovery import find_studio_mcp, clear_saved_path

        # Уже подключено?
        if is_available():
            return True

        # Пробуем найти и подключиться.
        if ensure_connected(auto=True):
            return True

        # Не нашли. Спрашиваем у пользователя.
        print()
        print("  ⚠️  Для Roblox-задач нужен MCP-сервер Roblox Studio.")
        path = self._ask_roblox_path()

        if not path:
            return False

        # Пробуем подключиться с новым путём.
        disconnect()
        clear_saved_path()
        if ensure_connected(auto=True):
            return True

        print(f"  ✘ Не удалось подключиться к {path}")
        return False

    def _solve_roblox(self, query: str, plan: dict, language: str) -> Any:
        """
        Решает задачу через Roblox-субагентов с итеративным циклом.

        Схема:
            1. ScriptAgent — создаёт скрипты
            2. WorldAgent  — создаёт объекты
            3. TestAgent   — запускает playtest, читает консоль
            4. Если есть ошибки → FixAgent исправляет → повтор
            5. Максимум 3 итерации.
        """
        from core.roblox.subagents import (
            RobloxScriptAgent, RobloxWorldAgent,
            RobloxTestAgent, RobloxFixAgent,
        )

        if not self._ensure_roblox_connected():
            return self._build_result(
                success=False,
                language="luau",
                plan=json.dumps(plan, ensure_ascii=False),
                stderr=(
                    "Roblox Studio не подключён.\n"
                    "Включи MCP в Studio (Assistant → ⋯ → Manage MCP Servers) "
                    "и снова вызови задачу."
                ),
            )

        project_name = self.project.name if self.project else "roblox"

        # === Итерации ===
        max_iterations = 3
        previous_errors = ""
        all_reports: list[str] = []
        final_success = False

        for iteration in range(max_iterations):
            iter_label = f"итерация {iteration + 1}/{max_iterations}"
            self._note(f"Roblox {iter_label}")

            # 1. ScriptAgent
            script_step = self._begin_step("roblox-script", f"пишу скрипты ({iter_label})")
            try:
                script_agent = RobloxScriptAgent(provider=self.lead_provider)
                script_result = script_agent.run(
                    query, project_name=project_name, plan=plan,
                    console_errors=previous_errors or "(нет)",
                )
                all_reports.append(script_result)
                self._note(f"Script: {script_result[:150]}")
            except Exception as exc:
                all_reports.append(f"❌ ScriptAgent: {exc}")
            self._end_step(script_step)

            # 2. WorldAgent (только на первой итерации — объекты создаются один раз)
            if iteration == 0:
                world_step = self._begin_step("roblox-world", "создаю объекты")
                try:
                    world_agent = RobloxWorldAgent(provider=self.lead_provider)
                    world_result = world_agent.run(
                        query, project_name=project_name, plan=plan,
                        console_errors="(нет)",
                    )
                    all_reports.append(world_result)
                    self._note(f"World: {world_result[:150]}")
                except Exception as exc:
                    all_reports.append(f"❌ WorldAgent: {exc}")
                self._end_step(world_step)

            # 3. TestAgent
            test_step = self._begin_step("roblox-test", f"тестирую ({iter_label})")
            test_result = ""
            try:
                test_agent = RobloxTestAgent(provider=self.lead_provider)
                test_result = test_agent.run(
                    query, project_name=project_name,
                    changes_summary="\n".join(all_reports[-2:]),
                )
                all_reports.append(test_result)
                self._note(f"Test: {test_result[:150]}")
            except Exception as exc:
                all_reports.append(f"❌ TestAgent: {exc}")
            self._end_step(test_step)

            # 4. Проверяем — есть ли ошибки?
            has_errors = (
                "❌" in test_result
                or "errors" in test_result.lower()
                or "обнаружены ошибки" in test_result.lower()
                or "stack traceback" in test_result.lower()
            )

            if not has_errors:
                final_success = True
                self._note(f"Успех на итерации {iteration + 1}")
                break

            # 5. FixAgent
            self._note(f"Ошибки — фикшу (итерация {iteration + 1})")
            fix_step = self._begin_step("roblox-fix", f"исправляю ({iter_label})")
            try:
                fix_agent = RobloxFixAgent(provider=self.lead_provider)
                fix_result = fix_agent.run(
                    query,
                    errors=test_result,
                    scripts_state="(см. выше)",
                )
                all_reports.append(fix_result)
                self._note(f"Fix: {fix_result[:150]}")
            except Exception as exc:
                all_reports.append(f"❌ FixAgent: {exc}")
            self._end_step(fix_step)

            previous_errors = test_result

        # === Финальный отчёт ===
        full_report = "\n\n".join(all_reports)

        # Записываем в историю.
        try:
            if self.project:
                self.project.add_task(
                    query,
                    "success" if final_success else "failure",
                    provider=self.lead_name,
                    model=self._lead_model(),
                    reasoning_time=time.time() - self._started_at,
                )
        except Exception:
            pass

        emit(
            "task.done",
            {"success": final_success},
            level=LEVEL_SUCCESS if final_success else LEVEL_ERROR,
        )

        return self._build_result(
            success=final_success,
            language="luau",
            code=full_report,
            stdout=full_report,
            exit_code=0 if final_success else 1,
            plan=json.dumps(plan, ensure_ascii=False),
        )

    # --- Главный метод ---------------------------------------------------

    def solve(self, query: str, skills: list[str] | None = None) -> Any:
        from core import config

        self.steps = []
        self.notes = []
        self._started_at = time.time()
        active_skills = skills or []

        # 1. Определяем лидера.
        lead_step = self._begin_step("инициализация", "определяю главного агента")
        self.lead_name = self.registry.get_lead()
        try:
            self.lead_provider = self.registry.get_provider(self.lead_name)
        except Exception as exc:
            self._end_step(lead_step)
            return self._build_result(success=False,
                stderr=f"Провайдер {self.lead_name}: {exc}")
        if not self.registry.is_configured(self.lead_name):
            self._end_step(lead_step)
            return self._build_result(success=False,
                stderr=f"Провайдер {self.lead_name} не настроен.")
        self._end_step(lead_step)

        # 2. Определяем проект.
        emit("planning.start", {"query": query})
        det_step = self._begin_step("проект", "определяю куда писать код")
        action, proj_name = self._detect_project(query)
        self.project = self._open_or_create_project(action, proj_name)
        self._end_step(det_step)

        # 3. Планируем.
        plan_step = self._begin_step("планирование", "составляю план")
        plan = self._plan(query, self.project)
        self._end_step(plan_step)
        language = plan.get("language", "python")

        # 3.4. Проверка: это Roblox-задача?
        platform = str(plan.get("platform", "")).strip().lower()

        # Дополнительная проверка по ключевым словам в запросе.
        query_lower = query.lower()
        roblox_keywords = (
            "roblox", "роблокс", "luau", "rblx",
            "studio", "рблокс",
            "game:getservice", "instance.new", "workspace",
            "players.playeradded", "startsgame",
        )
        query_is_roblox = any(kw in query_lower for kw in roblox_keywords)

        if platform == "roblox" or query_is_roblox:
            try:
                self._note("Платформа: Roblox")
                return self._solve_roblox(query, plan, language)
            except Exception as exc:
                self._note(f"Roblox-обработка упала: {exc}")

        # 3.5. Проверка библиотек.
        requirements = plan.get("requirements", []) or []
        if requirements:
            lib_step = self._begin_step("библиотеки", "проверяю зависимости")
            from core.library_manager import LibraryManager
            lm = LibraryManager()
            lib_result = lm.ensure_all(requirements)
            self._end_step(lib_step)

            # Записываем requirements.txt в проект.
            try:
                lm.write_requirements(
                    self.project.path,
                    requirements,
                    installed=lib_result.get("installed", []),
                )
            except Exception:
                pass

            # Если чего-то не хватает — останавливаемся и говорим пользователю.
            missing = lib_result.get("missing", [])
            if missing:
                missing_str = ", ".join(missing)
                msg = (
                    f"Не могу продолжить без библиотек: {missing_str}\n"
                    f"Установи вручную:\n"
                    f"  pip install {missing_str}\n"
                    f"или:\n"
                    f"  pkg install {missing_str}"
                )
                self._note(msg)
                try:
                    self.project.add_task(
                        query, "failure",
                        provider=self.lead_name,
                        reasoning_time=time.time() - self._started_at,
                    )
                except Exception:
                    pass
                emit("task.done", {"success": False}, level=LEVEL_ERROR)
                return self._build_result(
                    success=False,
                    language=language,
                    plan=json.dumps(plan, ensure_ascii=False),
                    stderr=msg,
                )

            # Если что-то доустановили — заметка.
            installed = lib_result.get("installed", [])
            if installed:
                names = ", ".join(
                    i["name"] if isinstance(i, dict) else str(i)
                    for i in installed
                )
                self._note(f"Доустановлено: {names}")

        # 4. Исследование (если включено).
        research = ""
        if "deep_research" in active_skills:
            res_step = self._begin_step("исследование", "ищу информацию")
            try:
                from subagents.researcher import ResearcherSubagent
                research = ResearcherSubagent().run(query) or ""
            except Exception as exc:
                self._note(f"Исследование не удалось: {exc}")
            self._end_step(res_step)

        # 5. Генерация кода.
        emit("codegen.start", {})
        gen_step = self._begin_step("генерация", "пишу код")
        files = self._generate(query, self.project, plan)
        if not files:
            self._end_step(gen_step)
            return self._build_result(success=False, language=language,
                plan=json.dumps(plan, ensure_ascii=False),
                stderr="Код не сгенерирован.")
        # Сохраняем файлы в проект.
        for path, content in files.items():
            self.project.write_file(path, content)
            emit("codegen.file.done", {"file": path}, level=LEVEL_SUCCESS)
        self.project.set_language(language)
        self._end_step(gen_step)

        # 6. Компиляция/запуск с фиксами.
        final_stdout, final_stderr, final_exit = "", "", -1
        iterations = 0
        for i in range(config.MAX_FIX_ITERATIONS + 1):
            test_step = self._begin_step("компиляция",
                f"{language}, попытка {i+1}")
            result = self._run(self.project, files, language)
            self._end_step(test_step)
            final_stdout = result.get("stdout", "") or ""
            final_stderr = result.get("stderr", "") or ""
            final_exit = int(result.get("exit_code", -1))
            if final_exit == 0 and not final_stderr.strip():
                break
            if i >= config.MAX_FIX_ITERATIONS:
                break
            fix_step = self._begin_step("фикс", f"итерация {i+1}")
            files = self._fix(self.project, files, language,
                              final_stderr, final_stdout, i+1)
            for path, content in files.items():
                self.project.write_file(path, content)
            self._end_step(fix_step)
            iterations = i + 1

        success = final_exit == 0 and not final_stderr.strip()
        primary_code = ""
        if files:
            primary_code = files[next(iter(files))]

        # 7. Записываем задачу в историю.
        try:
            self.project.add_task(
                query, "success" if success else "failure",
                provider=self.lead_name,
                model=self._lead_model(),
                reasoning_time=time.time() - self._started_at,
                files_created=list(files.keys()),
            )
        except Exception:
            pass

        emit("task.done", {"success": success},
             level=LEVEL_SUCCESS if success else LEVEL_ERROR)

        return self._build_result(
            success=success,
            language=language,
            code=primary_code,
            stdout=final_stdout,
            stderr=final_stderr,
            exit_code=final_exit,
            iterations=iterations,
            plan=json.dumps(plan, ensure_ascii=False),
        )


__all__ = ["TeamLead"]
