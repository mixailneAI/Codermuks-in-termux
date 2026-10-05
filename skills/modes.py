# =============================================================================
#  Codermuks in Termux — скиллы (режимы работы)
# =============================================================================
#  Скиллы — это переключаемые режимы, которые меняют поведение агента.
#  Пользователь включает их командами внутри сессии:
#
#      /research  — глубокое исследование (поиск в web + чтение GitHub)
#      /reason    — показать полную цепочку рассуждений
#      /analyze   — разобрать существующий код
#
#  Каждый скилл может:
#    • добавить свой системный промпт;
#    • включить дополнительные шаги (например, web-исследование);
#    • изменить набор используемых моделей.
#
#  Модуль хранит реестр скиллов и умеет применять их к запросу.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# =============================================================================
#  ОПИСАНИЕ СКИЛЛА
# =============================================================================

@dataclass
class Skill:
    """
    Описание одного скилла.

    Поля:
        name         — короткое имя (используется в командах, например "research")
        display_name — имя для показа пользователю ("Глубокое исследование")
        description  — короткое описание для справки
        system_prompt — опциональный системный промпт, который переопределяет
                        базовый (например, SYSTEM_REASONING)
        extra_flags  — дополнительные флаги, которые читает агент:
                        "use_web", "use_planner", "show_reasoning"
    """
    name: str
    display_name: str
    description: str
    system_prompt: str = ""
    extra_flags: dict[str, bool] = field(default_factory=dict)


# =============================================================================
#  РЕЕСТР СКИЛЛОВ
# =============================================================================

def _build_registry() -> dict[str, Skill]:
    """
    Собирает реестр скиллов.

    Импортируем промпты внутри функции, чтобы не создавать циклических
    зависимостей на уровне модуля — prompts.templates не импортирует
    skills, но лучше перестраховаться.
    """
    from prompts.templates import SYSTEM_REASONING, SYSTEM_ANALYZER

    return {
        "research": Skill(
            name="research",
            display_name="Глубокое исследование",
            description=(
                "Ищет информацию в интернете, читает GitHub и документацию, "
                "обобщает найденное и передаёт кодеру."
            ),
            system_prompt="",
            extra_flags={"use_web": True, "use_planner": True},
        ),

        "reason": Skill(
            name="reason",
            display_name="Рассуждение",
            description=(
                "Показывает полную цепочку рассуждений модели перед финальным "
                "ответом. Полезно для сложных задач и обучения."
            ),
            system_prompt=SYSTEM_REASONING,
            extra_flags={"show_reasoning": True},
        ),

        "analyze": Skill(
            name="analyze",
            display_name="Анализ кода",
            description=(
                "Разбирает существующий код: находит баги, узкие места, "
                "предлагает улучшения. Не пишет код заново."
            ),
            system_prompt=SYSTEM_ANALYZER,
            extra_flags={"analysis_mode": True},
        ),
    }


# Реестр создаётся один раз при импорте модуля.
REGISTRY: dict[str, Skill] = _build_registry()


# =============================================================================
#  ПУБЛИЧНЫЕ ФУНКЦИИ
# =============================================================================

def list_skills() -> list[Skill]:
    """
    Возвращает отсортированный список всех скиллов.
    """
    return sorted(REGISTRY.values(), key=lambda s: s.name)


def get_skill(name: str) -> Skill | None:
    """
    Возвращает скилл по имени или None, если такого нет.

    Регистр не важен: "/research" и "/RESEARCH" — одно и то же.
    """
    if not name:
        return None
    key = name.strip().lower().lstrip("/")
    return REGISTRY.get(key)


def is_valid_skill(name: str) -> bool:
    """Проверяет, существует ли скилл с таким именем."""
    return get_skill(name) is not None


def normalize_skill_names(names: list[str]) -> list[str]:
    """
    Приводит список имён скиллов к каноническому виду.

    Отбрасывает несуществующие имена. Убирает дубликаты, сохраняя
    порядок первого появления.
    """
    result: list[str] = []
    seen: set[str] = set()

    for raw in names or []:
        skill = get_skill(raw)
        if skill is None:
            continue
        if skill.name in seen:
            continue
        seen.add(skill.name)
        result.append(skill.name)

    return result


def apply_skills(
    skills: list[str],
    base_prompt: str = "",
) -> tuple[str, dict[str, bool]]:
    """
    Применяет набор скиллов к базовому промпту.

    Аргументы:
        skills      — список имён скиллов (например, ["research", "reason"])
        base_prompt — базовый системный промпт

    Возвращает кортеж:
        (итоговый_промпт, объединённые_флаги)

    Если несколько скиллов задают system_prompt, они конкатенируются
    через двойной перенос строки. Флаги объединяются по логике «ИЛИ» —
    достаточно, чтобы флаг был включён хотя бы одним скиллом.
    """
    normalized = normalize_skill_names(skills)

    if not normalized:
        return base_prompt, {}

    # Собираем промпты от всех скиллов.
    prompts: list[str] = []
    if base_prompt.strip():
        prompts.append(base_prompt.strip())

    flags: dict[str, bool] = {}

    for name in normalized:
        skill = REGISTRY.get(name)
        if skill is None:
            continue

        if skill.system_prompt.strip():
            prompts.append(skill.system_prompt.strip())

        for flag_name, flag_value in skill.extra_flags.items():
            flags[flag_name] = flags.get(flag_name, False) or flag_value

    combined = "\n\n".join(prompts)
    return combined, flags


def format_skills_help() -> str:
    """
    Формирует текст справки по скиллам — для команды /help.
    """
    lines: list[str] = []
    lines.append("Доступные скиллы:")
    lines.append("")

    for skill in list_skills():
        lines.append(f"  /{skill.name:<10} — {skill.display_name}")
        lines.append(f"               {skill.description}")
        lines.append("")

    return "\n".join(lines).rstrip()


def skills_as_commands() -> list[str]:
    """
    Возвращает список команд (с ведущим слэшем) для всех скиллов.

    Удобно для автодополнения или проверки ввода.
    """
    return [f"/{skill.name}" for skill in list_skills()]