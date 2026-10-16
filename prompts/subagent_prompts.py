# =============================================================================
#  Codermuks in Termux — шаблоны задач для субагентов v1.3.0
# =============================================================================
#  Что нового в v1.3.0:
#    • PROJECT_DECIDER_TASK_TEMPLATE — определяет, куда писать код;
#    • PLANNER_TASK_TEMPLATE — теперь с контекстом проекта;
#    • CODER_TASK_TEMPLATE — теперь с существующими файлами;
#    • FIXER_TASK_TEMPLATE — замена старого FIX_TASK_TEMPLATE.
# =============================================================================


# =============================================================================
#  РЕШАТЕЛЬ ПРОЕКТА
# =============================================================================
#  Быстрое определение: продолжить существующий проект или создать новый.
# =============================================================================

PROJECT_DECIDER_TASK_TEMPLATE = """User request:

{query}

Existing projects:

{projects_list}

Decide where this request should go and return JSON with action,
project_name and reason.
"""


# =============================================================================
#  ПЛАНИРОВЩИК
# =============================================================================
#  Полноценный план для кодера — с учётом проекта и контекста.
# =============================================================================

PLANNER_TASK_TEMPLATE = """User request:

{query}

Target project: {project_name}
Project language: {language}

Existing files in project:
{files_list}

Previous tasks in this project:
{history_context}

Create a JSON plan for the coder following the format described in your system prompt.
"""


# =============================================================================
#  КОДЕР
# =============================================================================

CODER_TASK_TEMPLATE = """User request:

{query}

Project: {project_name}
Language: {language}

Plan:

{plan}

Existing files that will be modified (full content):

{existing_files}

Create or update all files according to the plan.
Return each file with `### FILE: <relative path>` marker and a code block.
"""


# =============================================================================
#  ФИКСЕР
# =============================================================================

FIXER_TASK_TEMPLATE = """The previous version failed. This is fix attempt #{iteration}.

Project: {project_name}
Language: {language}

Current content of files that may need fixes:

{current_files}

Compiler / runtime output:

--- stdout ---
{stdout}

--- stderr ---
{stderr}

Return the full corrected content of each file that needs changes.
Use `### FILE: <relative path>` markers.
"""


# =============================================================================
#  ИССЛЕДОВАТЕЛЬ
# =============================================================================

RESEARCH_TASK_TEMPLATE = """The user asked:

{query}

Raw materials collected from the internet:

{materials}

Compress these materials into a short, useful summary following
the format described in your system prompt.
"""


# =============================================================================
#  АНАЛИТИК
# =============================================================================

ANALYZE_TASK_TEMPLATE = """Please review the following {language} code.

Code:

```

{code}

```

Additional question from the user (may be empty):

{question}

Produce a structured review following the format described in your system prompt.
"""


# =============================================================================
#  РЕЖИМ РАССУЖДЕНИЙ
# =============================================================================

REASONING_TASK_TEMPLATE = """The user asked:

{query}

Think through this request step by step and produce the reasoning chain
followed by a short final answer.
"""


# =============================================================================
#  ФАЙЛОВЫЙ МЕНЕДЖЕР (резервный)
# =============================================================================

FILE_MANAGER_TASK_TEMPLATE = """File operation request:

Action: {action}
Path:   {path}

Additional context:

{extra}

Perform the requested operation and report the result in one short line.
"""


# =============================================================================
#  ЭКСПОРТ
# =============================================================================

__all__ = [
    "PROJECT_DECIDER_TASK_TEMPLATE",
    "PLANNER_TASK_TEMPLATE",
    "CODER_TASK_TEMPLATE",
    "FIXER_TASK_TEMPLATE",
    "RESEARCH_TASK_TEMPLATE",
    "ANALYZE_TASK_TEMPLATE",
    "REASONING_TASK_TEMPLATE",
    "FILE_MANAGER_TASK_TEMPLATE",
]
