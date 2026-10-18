# =============================================================================
#  Codermuks in Termux — Roblox-субагенты v1.4.0
# =============================================================================
#  Три специализированных субагента для работы с Roblox Studio через MCP:
#
#    • RobloxScriptAgent — пишет и правит скрипты
#    • RobloxWorldAgent  — создаёт и меняет объекты в Workspace
#    • RobloxTestAgent   — запускает playtest, читает логи
#
#  Каждый субагент:
#    1. Получает задачу + контекст.
#    2. Просит LLM составить JSON-план действий.
#    3. Парсит JSON (с fallback-логикой).
#    4. Выполняет действия через tools.
#    5. Возвращает человеко-читаемый отчёт.
# =============================================================================

from __future__ import annotations

import json
import re
import time
from typing import Any

from core.roblox import (
    call_tool,
    extract_text,
    get_tool_names,
    is_available,
    list_tools,
)
from core.roblox import tools as rbx_tools
from core.roblox.prompts import (
    SCRIPT_AGENT_SYSTEM,
    SCRIPT_AGENT_TASK,
    TEST_AGENT_SYSTEM,
    TEST_AGENT_TASK,
    WORLD_AGENT_SYSTEM,
    WORLD_AGENT_TASK,
)
from core.events import emit, LEVEL_INFO, LEVEL_SUCCESS, LEVEL_WARNING, LEVEL_ERROR


# =============================================================================
#  БАЗОВЫЙ КЛАСС
# =============================================================================

class BaseRobloxSubagent:
    """
    Базовый Roblox-субагент.

    Содержит общие методы:
        • парсинг JSON из ответа LLM,
        • вызов LLM через провайдера,
        • логирование шагов.
    """

    name: str = "base"
    display_name: str = "Base Roblox Agent"
    system_prompt: str = ""

    def __init__(self, provider: Any) -> None:
        """
        provider — экземпляр провайдера (MistralProvider, QwenProvider, ...).
        """
        self.provider = provider
        self.log: list[str] = []

    # -------------------------------------------------------------------------
    #  LLM
    # -------------------------------------------------------------------------

    def _call_llm(self, user_prompt: str, temperature: float = 0.2) -> str:
        """Отправляет запрос в LLM и возвращает текст ответа."""
        if self.provider is None:
            return ""

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        try:
            response = self.provider.chat(messages, temperature=temperature)
            return response.text or ""
        except Exception as exc:
            self.log.append(f"LLM ошибка: {exc}")
            return ""

    @staticmethod
    def _parse_json(text: str) -> dict | None:
        """Парсит JSON из ответа LLM (снимает markdown-обёртку)."""
        if not text:
            return None

        text = text.strip()

        # Убираем ```json ... ```
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
            text = re.sub(r"\s*```\s*$", "", text)

        # Ищем первый {...}
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None

        candidate = text[start:end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Пробуем "починить" типичные проблемы.
            try:
                fixed = candidate.replace("'", '"')
                return json.loads(fixed)
            except json.JSONDecodeError:
                return None

    # -------------------------------------------------------------------------
    #  УТИЛИТЫ
    # -------------------------------------------------------------------------

    def _log(self, message: str) -> None:
        """Записывает сообщение в лог."""
        self.log.append(message)
        self._log(f"[{self.name}] {message}") if False else None  # noqa

    def _emit_step(self, message: str) -> None:
        """Публикует событие в EventBus."""
        emit(f"roblox.{self.name}", {"message": message}, level=LEVEL_INFO)

    def is_ready(self) -> bool:
        """Проверяет, что Roblox подключён."""
        return is_available()

    def run(self, query: str, **kwargs: Any) -> str:
        """Основной метод — переопределяется в наследниках."""
        raise NotImplementedError


# =============================================================================
#  SCRIPT AGENT
# =============================================================================

class RobloxScriptAgent(BaseRobloxSubagent):
    """
    Субагент для работы со скриптами.

    Умеет:
        • читать скрипты (script_read),
        • создавать новые (create_script),
        • редактировать существующие (edit_script),
        • искать по коду (search_scripts).
    """

    name = "script"
    display_name = "Roblox Script Agent"
    system_prompt = SCRIPT_AGENT_SYSTEM

    def _list_existing_scripts(self) -> str:
        """Возвращает краткий список существующих скриптов."""
        tree = rbx_tools.get_game_tree(max_depth=3)
        if not tree:
            return "(нет данных)"
        # Ограничиваем длину.
        if len(tree) > 2000:
            tree = tree[:2000] + "\n... (truncated)"
        return tree

    def _execute_actions(self, actions: list[dict]) -> list[str]:
        """Выполняет список действий. Возвращает отчёты."""
        reports: list[str] = []

        for action in actions:
            if not isinstance(action, dict):
                continue

            tool = str(action.get("tool", "")).strip()
            path = str(action.get("path", "")).strip()
            source = str(action.get("source", ""))
            script_type = str(action.get("script_type", "Script")).strip()
            query = str(action.get("query", "")).strip()
            reason = str(action.get("reason", "")).strip()

            self._emit_step(f"{tool}: {path or query or '...'}")

            if tool == "script_read":
                content = rbx_tools.read_script(path)
                if content:
                    reports.append(f"📖 Прочитан {path} ({len(content)} символов)")
                else:
                    reports.append(f"⚠️ Не удалось прочитать {path}")

            elif tool == "search_scripts":
                result = rbx_tools.search_scripts(query)
                if result:
                    reports.append(f"🔍 Найдено по '{query}': {result[:200]}")
                else:
                    reports.append(f"🔍 Ничего не найдено по '{query}'")

            elif tool in ("create_script", "edit_script"):
                if not path or not source:
                    reports.append(f"⚠️ Пропущено {tool}: пустой path или source")
                    continue
                result = rbx_tools.create_or_edit_script(
                    path, source, script_type,
                )
                if result:
                    verb = "Создан" if tool == "create_script" else "Изменён"
                    reports.append(f"✏️ {verb} {path} ({len(source)} символов)")
                else:
                    reports.append(f"❌ Ошибка при записи {path}")

            else:
                reports.append(f"⚠️ Неизвестный инструмент: {tool}")

        return reports

    def run(self, query: str, **kwargs: Any) -> str:
        """Пишет/правит скрипты по запросу."""
        if not self.is_ready():
            return "❌ Roblox Studio не подключён"

        project_name = kwargs.get("project_name", "untitled")
        plan = kwargs.get("plan", {})

        # Собираем контекст.
        scripts_list = self._list_existing_scripts()
        plan_str = json.dumps(plan, ensure_ascii=False, indent=2) if plan else "{}"

        user_prompt = SCRIPT_AGENT_TASK.format(
            query=query,
            project_name=project_name,
            scripts_list=scripts_list,
            plan=plan_str,
        )

        # Запрос к LLM.
        self._emit_step("думаю над скриптами...")
        raw = self._call_llm(user_prompt, temperature=0.2)
        parsed = self._parse_json(raw)

        if not parsed:
            return f"⚠️ LLM не вернул валидный JSON.\n\nСырой ответ:\n{raw[:500]}"

        actions = parsed.get("actions", [])
        summary = str(parsed.get("summary", "")).strip()

        if not actions:
            return f"✅ Нечего делать: {summary or 'нет действий'}"

        # Выполняем.
        reports = self._execute_actions(actions)

        # Формируем отчёт.
        result_lines = [f"🤖 {self.display_name}"]
        if summary:
            result_lines.append(f"📝 {summary}")
        result_lines.append("")
        result_lines.extend(reports)

        return "\n".join(result_lines)


# =============================================================================
#  WORLD AGENT
# =============================================================================

class RobloxWorldAgent(BaseRobloxSubagent):
    """
    Субагент для работы с объектами в Workspace.

    Умеет:
        • создавать объекты (insert_instance),
        • выполнять произвольный Luau (execute_luau),
        • читать дерево (get_game_tree).
    """

    name = "world"
    display_name = "Roblox World Agent"
    system_prompt = WORLD_AGENT_SYSTEM

    def _get_tree(self) -> str:
        """Краткое дерево проекта."""
        tree = rbx_tools.get_game_tree(max_depth=3)
        if not tree:
            return "(нет данных)"
        if len(tree) > 3000:
            tree = tree[:3000] + "\n... (truncated)"
        return tree

    def _execute_actions(self, actions: list[dict]) -> list[str]:
        """Выполняет действия World Agent."""
        reports: list[str] = []

        for action in actions:
            if not isinstance(action, dict):
                continue

            tool = str(action.get("tool", "")).strip()
            code = str(action.get("code", ""))
            class_name = str(action.get("class_name", "")).strip()
            parent_path = str(action.get("parent_path", "game.Workspace")).strip()
            properties = action.get("properties", {}) or {}

            self._emit_step(f"{tool}: {class_name or 'luau code'}")

            if tool == "get_game_tree":
                tree = rbx_tools.get_game_tree()
                reports.append(f"🌳 Дерево получено ({len(tree)} символов)")

            elif tool == "insert_instance":
                if not class_name:
                    reports.append("⚠️ Пропущено: пустой class_name")
                    continue
                result = rbx_tools.insert_instance(
                    class_name, parent_path, properties,
                )
                if result:
                    reports.append(f"🧱 Создан {class_name} в {parent_path}")
                else:
                    reports.append(f"❌ Не удалось создать {class_name}")

            elif tool == "execute_luau":
                if not code:
                    reports.append("⚠️ Пропущено: пустой code")
                    continue
                result = rbx_tools.execute_luau(code)
                snippet = result[:150].replace("\n", " ") if result else "(нет вывода)"
                reports.append(f"⚙️ Luau: {snippet}")

            else:
                reports.append(f"⚠️ Неизвестный инструмент: {tool}")

        return reports

    def run(self, query: str, **kwargs: Any) -> str:
        """Создаёт/меняет объекты по запросу."""
        if not self.is_ready():
            return "❌ Roblox Studio не подключён"

        project_name = kwargs.get("project_name", "untitled")
        plan = kwargs.get("plan", {})

        tree = self._get_tree()
        plan_str = json.dumps(plan, ensure_ascii=False, indent=2) if plan else "{}"

        user_prompt = WORLD_AGENT_TASK.format(
            query=query,
            project_name=project_name,
            game_tree=tree,
            plan=plan_str,
        )

        self._emit_step("думаю над объектами...")
        raw = self._call_llm(user_prompt, temperature=0.3)
        parsed = self._parse_json(raw)

        if not parsed:
            return f"⚠️ LLM не вернул валидный JSON.\n\nСырой ответ:\n{raw[:500]}"

        actions = parsed.get("actions", [])
        summary = str(parsed.get("summary", "")).strip()

        if not actions:
            return f"✅ Нечего делать: {summary or 'нет действий'}"

        reports = self._execute_actions(actions)

        result_lines = [f"🌍 {self.display_name}"]
        if summary:
            result_lines.append(f"📝 {summary}")
        result_lines.append("")
        result_lines.extend(reports)

        return "\n".join(result_lines)


# =============================================================================
#  TEST AGENT
# =============================================================================

class RobloxTestAgent(BaseRobloxSubagent):
    """
    Субагент для тестирования.

    Умеет:
        • запускать playtest,
        • читать console output,
        • останавливать playtest,
        • проверять объекты через execute_luau.
    """

    name = "test"
    display_name = "Roblox Test Agent"
    system_prompt = TEST_AGENT_SYSTEM

    def _execute_actions(self, actions: list[dict]) -> tuple[list[str], str, list[str]]:
        """
        Выполняет действия.

        Возвращает:
            (reports, verdict, issues)
        """
        reports: list[str] = []
        issues: list[str] = []
        verdict = "unknown"

        for action in actions:
            if not isinstance(action, dict):
                continue

            tool = str(action.get("tool", "")).strip()
            code = str(action.get("code", ""))
            lines = int(action.get("lines", 50))
            wait_seconds = float(action.get("wait_seconds", 2.0))

            self._emit_step(f"{tool}")

            if tool == "start_playtest":
                result = rbx_tools.start_playtest()
                reports.append(f"▶️ Playtest запущен")

            elif tool == "stop_playtest":
                result = rbx_tools.stop_playtest()
                reports.append(f"⏹ Playtest остановлен")

            elif tool == "get_console_output":
                output = rbx_tools.get_console_output(lines=lines)
                if output:
                    reports.append(f"📜 Консоль ({len(output)} символов):\n{output[:500]}")
                    # Ищем типичные ошибки.
                    lower = output.lower()
                    for pattern in ("error", "failed", "nil", "attempt to"):
                        if pattern in lower:
                            for line in output.splitlines():
                                if pattern in line.lower():
                                    issues.append(line.strip()[:200])
                            break
                else:
                    reports.append("📜 Консоль пуста")

            elif tool == "execute_luau":
                if not code:
                    continue
                result = rbx_tools.execute_luau(code)
                snippet = result[:200] if result else "(нет вывода)"
                reports.append(f"⚙️ Проверка: {snippet}")

            # Ждём после действий, где это указано.
            if wait_seconds > 0:
                time.sleep(wait_seconds)

        # Определяем verdict.
        if issues:
            verdict = "errors"
        elif any("Playtest" in r for r in reports):
            verdict = "ok"

        return reports, verdict, issues

    def run(self, query: str, **kwargs: Any) -> str:
        """Запускает playtest и проверяет результат."""
        if not self.is_ready():
            return "❌ Roblox Studio не подключён"

        project_name = kwargs.get("project_name", "untitled")
        changes_summary = kwargs.get("changes_summary", "(нет изменений)")
        previous_results = kwargs.get("previous_results", "(нет)")

        user_prompt = TEST_AGENT_TASK.format(
            query=query,
            project_name=project_name,
            changes_summary=changes_summary,
            previous_results=previous_results,
        )

        self._emit_step("думаю над тестами...")
        raw = self._call_llm(user_prompt, temperature=0.1)
        parsed = self._parse_json(raw)

        if not parsed:
            return f"⚠️ LLM не вернул валидный JSON.\n\nСырой ответ:\n{raw[:500]}"

        actions = parsed.get("actions", [])
        if not actions:
            return "✅ Нечего тестировать."

        reports, llm_verdict, llm_issues = self._execute_actions(actions)

        # Комбинируем вердикт от LLM и от наших проверок.
        verdict = parsed.get("verdict", llm_verdict)
        issues = parsed.get("issues", []) + llm_issues
        summary = str(parsed.get("summary", "")).strip()

        # Формируем отчёт.
        result_lines = [f"🧪 {self.display_name}"]

        if verdict == "ok":
            result_lines.append("✅ Тест пройден — ошибок не обнаружено")
        elif verdict == "errors":
            result_lines.append("❌ Обнаружены проблемы:")
            for issue in issues[:10]:
                result_lines.append(f"   • {issue}")
        else:
            result_lines.append("⚠️ Не удалось определить результат")

        if summary:
            result_lines.append(f"📝 {summary}")

        result_lines.append("")
        result_lines.extend(reports)

        return "\n".join(result_lines)


# =============================================================================
#  ФАБРИКА
# =============================================================================

ALL_SUBAGENTS = {
    "script": RobloxScriptAgent,
    "world": RobloxWorldAgent,
    "test": RobloxTestAgent,
}


def create_subagent(name: str, provider: Any) -> BaseRobloxSubagent | None:
    """
    Создаёт субагента по имени.

    Аргументы:
        name     — "script" | "world" | "test"
        provider — экземпляр LLM-провайдера.
    """
    cls = ALL_SUBAGENTS.get(name.strip().lower())
    if cls is None:
        return None
    return cls(provider)


def list_subagent_names() -> list[str]:
    """Возвращает имена доступных Roblox-субагентов."""
    return list(ALL_SUBAGENTS.keys())


__all__ = [
    "BaseRobloxSubagent",
    "RobloxScriptAgent",
    "RobloxWorldAgent",
    "RobloxTestAgent",
    "ALL_SUBAGENTS",
    "create_subagent",
    "list_subagent_names",
]
