# =============================================================================
#  Codermuks in Termux — Roblox-субагенты v1.4.0
# =============================================================================

from __future__ import annotations

import json
import re
import time
from typing import Any

from core.roblox import (
    call_tool, extract_text, is_available,
)
from core.roblox import tools as rbx_tools
from core.roblox.prompts import (
    SCRIPT_AGENT_SYSTEM, SCRIPT_AGENT_TASK,
    WORLD_AGENT_SYSTEM, WORLD_AGENT_TASK,
    TEST_AGENT_SYSTEM, TEST_AGENT_TASK,
    FIX_AGENT_SYSTEM, FIX_AGENT_TASK,
)
from core.events import emit, LEVEL_INFO, LEVEL_SUCCESS, LEVEL_WARNING, LEVEL_ERROR


class BaseRobloxSubagent:
    name: str = "base"
    display_name: str = "Base Roblox Agent"
    system_prompt: str = ""

    def __init__(self, provider: Any) -> None:
        self.provider = provider
        self.log: list[str] = []

    def _call_llm(self, user_prompt: str, temperature: float = 0.2) -> str:
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
        if not text:
            return None
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
            text = re.sub(r"\s*```\s*$", "", text)
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            try:
                return json.loads(text[start:end + 1].replace("'", '"'))
            except json.JSONDecodeError:
                return None

    def is_ready(self) -> bool:
        return is_available()

    def run(self, query: str, **kwargs: Any) -> str:
        raise NotImplementedError


class RobloxScriptAgent(BaseRobloxSubagent):
    name = "script"
    display_name = "Roblox Script Agent"
    system_prompt = SCRIPT_AGENT_SYSTEM

    def _execute_actions(self, actions: list[dict]) -> list[str]:
        reports: list[str] = []
        for action in actions[:2]:  # Не более 2 действий
            if not isinstance(action, dict):
                continue
            tool = str(action.get("tool", "")).strip()
            path = str(action.get("path", "")).strip()
            source = str(action.get("source", ""))
            script_type = str(action.get("script_type", "Script")).strip()
            query = str(action.get("query", "")).strip()

            if tool == "script_read":
                content = rbx_tools.read_script(path)
                reports.append(f"📖 {path} ({len(content)} символов)" if content else f"⚠️ Не прочитать {path}")
            elif tool == "search_scripts":
                result = rbx_tools.search_scripts(query)
                reports.append(f"🔍 Найдено: {result[:150]}" if result else f"🔍 Пусто")
            elif tool in ("create_script", "edit_script"):
                if not path or not source:
                    reports.append(f"⚠️ Пропущено: пустой path/source")
                    continue
                result = rbx_tools.create_or_edit_script(path, source, script_type)
                verb = "Создан" if tool == "create_script" else "Изменён"
                if result:
                    reports.append(f"✏️ {verb} {path} ({len(source)} симв)")
                else:
                    reports.append(f"❌ Ошибка записи {path}")
            else:
                reports.append(f"⚠️ Неизвестный tool: {tool}")
        return reports

    def run(self, query: str, **kwargs: Any) -> str:
        if not self.is_ready():
            return "❌ Roblox Studio не подключён"

        project_name = kwargs.get("project_name", "untitled")
        plan = kwargs.get("plan", {})
        console_errors = kwargs.get("console_errors", "(нет)")

        scripts_list = rbx_tools.get_game_tree(max_depth=3)[:2000] or "(пусто)"
        plan_str = json.dumps(plan, ensure_ascii=False, indent=2) if plan else "{}"

        user_prompt = SCRIPT_AGENT_TASK.format(
            query=query, project_name=project_name,
            scripts_list=scripts_list, console_errors=console_errors,
            plan=plan_str,
        )
        raw = self._call_llm(user_prompt, temperature=0.2)
        parsed = self._parse_json(raw)

        if not parsed:
            return f"⚠️ LLM не вернул JSON.\n\n{raw[:400]}"

        actions = parsed.get("actions", [])
        summary = str(parsed.get("summary", "")).strip()

        if not actions:
            return f"✅ {summary or 'Нет действий'}"

        reports = self._execute_actions(actions)
        result_lines = [f"🤖 {self.display_name}"]
        if summary:
            result_lines.append(f"📝 {summary}")
        result_lines.append("")
        result_lines.extend(reports)
        return "\n".join(result_lines)


class RobloxWorldAgent(BaseRobloxSubagent):
    name = "world"
    display_name = "Roblox World Agent"
    system_prompt = WORLD_AGENT_SYSTEM

    def _execute_actions(self, actions: list[dict]) -> list[str]:
        reports: list[str] = []
        for action in actions[:3]:
            if not isinstance(action, dict):
                continue
            tool = str(action.get("tool", "")).strip()
            code = str(action.get("code", ""))
            class_name = str(action.get("class_name", "")).strip()
            parent_path = str(action.get("parent_path", "game.Workspace")).strip()
            properties = action.get("properties", {}) or {}

            if tool == "get_game_tree":
                tree = rbx_tools.get_game_tree()
                reports.append(f"🌳 Дерево ({len(tree)} симв)")
            elif tool == "insert_instance":
                if not class_name:
                    continue
                result = rbx_tools.insert_instance(class_name, parent_path, properties)
                reports.append(f"🧱 {class_name} в {parent_path}" if result else f"❌ {class_name}")
            elif tool == "execute_luau":
                if not code:
                    continue
                result = rbx_tools.execute_luau(code)
                snippet = result[:120].replace("\n", " ") if result else "(нет вывода)"
                reports.append(f"⚙️ {snippet}")
            else:
                reports.append(f"⚠️ tool: {tool}")
        return reports

    def run(self, query: str, **kwargs: Any) -> str:
        if not self.is_ready():
            return "❌ Roblox Studio не подключён"

        project_name = kwargs.get("project_name", "untitled")
        plan = kwargs.get("plan", {})
        console_errors = kwargs.get("console_errors", "(нет)")

        tree = rbx_tools.get_game_tree(max_depth=3)[:3000] or "(пусто)"
        plan_str = json.dumps(plan, ensure_ascii=False, indent=2) if plan else "{}"

        user_prompt = WORLD_AGENT_TASK.format(
            query=query, project_name=project_name,
            game_tree=tree, console_errors=console_errors, plan=plan_str,
        )
        raw = self._call_llm(user_prompt, temperature=0.3)
        parsed = self._parse_json(raw)
        if not parsed:
            return f"⚠️ LLM без JSON.\n\n{raw[:400]}"

        actions = parsed.get("actions", [])
        summary = str(parsed.get("summary", "")).strip()
        if not actions:
            return f"✅ {summary or 'Нет действий'}"

        reports = self._execute_actions(actions)
        result_lines = [f"🌍 {self.display_name}"]
        if summary:
            result_lines.append(f"📝 {summary}")
        result_lines.append("")
        result_lines.extend(reports)
        return "\n".join(result_lines)


class RobloxTestAgent(BaseRobloxSubagent):
    name = "test"
    display_name = "Roblox Test Agent"
    system_prompt = TEST_AGENT_SYSTEM

    def _execute(self, actions: list[dict]) -> tuple[list[str], str, list[str]]:
        reports: list[str] = []
        issues: list[str] = []
        verdict = "unknown"

        for action in actions:
            if not isinstance(action, dict):
                continue
            tool = str(action.get("tool", "")).strip()
            lines = int(action.get("lines", 100))
            wait_seconds = float(action.get("wait_seconds", 2.0))

            if tool == "start_playtest":
                rbx_tools.start_playtest()
                reports.append("▶️ Playtest запущен")
            elif tool == "stop_playtest":
                rbx_tools.stop_playtest()
                reports.append("⏹ Playtest остановлен")
            elif tool == "get_console_output":
                output = rbx_tools.get_console_output(lines=lines)
                if output:
                    reports.append(f"📜 Консоль:\n{output[:800]}")
                    lower = output.lower()
                    for line in output.splitlines():
                        if any(p in line.lower() for p in ("error", "failed", "attempt to", "stack traceback")):
                            issues.append(line.strip()[:200])
                else:
                    reports.append("📜 Консоль пуста")
            if wait_seconds > 0:
                time.sleep(wait_seconds)

        if issues:
            verdict = "errors"
        elif any("Playtest" in r for r in reports):
            verdict = "ok"
        return reports, verdict, issues

    def run(self, query: str, **kwargs: Any) -> str:
        if not self.is_ready():
            return "❌ Roblox Studio не подключён"

        project_name = kwargs.get("project_name", "untitled")
        changes = kwargs.get("changes_summary", "(нет)")

        user_prompt = TEST_AGENT_TASK.format(
            query=query, project_name=project_name, changes_summary=changes,
        )
        raw = self._call_llm(user_prompt, temperature=0.1)
        parsed = self._parse_json(raw)
        if not parsed:
            return f"⚠️ LLM без JSON.\n\n{raw[:400]}"

        actions = parsed.get("actions", [])
        if not actions:
            return "✅ Нечего тестировать."

        reports, llm_verdict, llm_issues = self._execute(actions)
        verdict = parsed.get("verdict", llm_verdict)
        issues = parsed.get("issues", []) + llm_issues
        summary = str(parsed.get("summary", "")).strip()

        result_lines = [f"🧪 {self.display_name}"]
        if verdict == "ok":
            result_lines.append("✅ Тест пройден")
        elif verdict == "errors":
            result_lines.append("❌ Обнаружены ошибки:")
            for issue in issues[:10]:
                result_lines.append(f"   • {issue}")
        else:
            result_lines.append("⚠️ Результат неопределён")
        if summary:
            result_lines.append(f"📝 {summary}")
        result_lines.append("")
        result_lines.extend(reports)
        return "\n".join(result_lines)


class RobloxFixAgent(BaseRobloxSubagent):
    name = "fix"
    display_name = "Roblox Fix Agent"
    system_prompt = FIX_AGENT_SYSTEM

    def _execute_actions(self, actions: list[dict]) -> list[str]:
        reports: list[str] = []
        for action in actions[:2]:
            if not isinstance(action, dict):
                continue
            tool = str(action.get("tool", "")).strip()
            path = str(action.get("path", "")).strip()
            source = str(action.get("source", ""))

            if tool == "script_read":
                content = rbx_tools.read_script(path)
                reports.append(f"📖 {path} ({len(content)})" if content else f"⚠️ {path}")
            elif tool == "edit_script":
                if not path or not source:
                    continue
                result = rbx_tools.create_or_edit_script(path, source)
                reports.append(f"✏️ Исправлен {path}" if result else f"❌ {path}")
        return reports

    def run(self, query: str, **kwargs: Any) -> str:
        if not self.is_ready():
            return "❌ Roblox Studio не подключён"

        errors = kwargs.get("errors", "(нет)")
        scripts_state = kwargs.get("scripts_state", "(нет)")

        user_prompt = FIX_AGENT_TASK.format(errors=errors, scripts_state=scripts_state)
        raw = self._call_llm(user_prompt, temperature=0.1)
        parsed = self._parse_json(raw)
        if not parsed:
            return f"⚠️ LLM без JSON.\n\n{raw[:400]}"

        actions = parsed.get("actions", [])
        summary = str(parsed.get("summary", "")).strip()
        if not actions:
            return f"✅ {summary or 'Нечего исправлять'}"

        reports = self._execute_actions(actions)
        result_lines = [f"🔧 {self.display_name}"]
        if summary:
            result_lines.append(f"📝 {summary}")
        result_lines.append("")
        result_lines.extend(reports)
        return "\n".join(result_lines)


ALL_SUBAGENTS = {
    "script": RobloxScriptAgent,
    "world": RobloxWorldAgent,
    "test": RobloxTestAgent,
    "fix": RobloxFixAgent,
}


def create_subagent(name: str, provider: Any) -> BaseRobloxSubagent | None:
    cls = ALL_SUBAGENTS.get(name.strip().lower())
    return cls(provider) if cls else None


def list_subagent_names() -> list[str]:
    return list(ALL_SUBAGENTS.keys())


__all__ = [
    "BaseRobloxSubagent", "RobloxScriptAgent", "RobloxWorldAgent",
    "RobloxTestAgent", "RobloxFixAgent", "ALL_SUBAGENTS",
    "create_subagent", "list_subagent_names",
]
