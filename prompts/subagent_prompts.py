
# =============================================================================
#  Codermuks in Termux — шаблоны задач для субагентов
# =============================================================================
#  Здесь живут шаблоны пользовательских сообщений, которые оркестратор
#  отправляет субагентам и моделям. В отличие от системных промптов
#  (prompts/templates.py), эти шаблоны содержат конкретные данные:
#  запрос пользователя, план, код, ошибки компиляции.
#
#  Все шаблоны используют именованные плейсхолдеры {name}, которые
#  подставляются через str.format(). Это позволяет легко менять
#  формулировки, не трогая логику агента.
# =============================================================================


# =============================================================================
#  ЗАДАЧА ДЛЯ ПЛАНИРОВЩИКА
# =============================================================================
#  Отправляется модели-планировщику вместе с SYSTEM_PLANNER.
#  Плейсхолдеры:
#      {query} — исходный запрос пользователя
# =============================================================================

PLANNER_TASK_TEMPLATE = """User request:

{query}

Produce a structured plan following the format described in your system prompt.
Remember: do NOT write code. Only identify the language, the goal, the steps, the required libraries, and the edge cases.
"""


# =============================================================================
#  ЗАДАЧА ДЛЯ КОДЕРА (первичная генерация)
# =============================================================================
#  Отправляется кодеру вместе с SYSTEM_CODER. Содержит исходный запрос,
#  план от планировщика и (опционально) материалы исследования.
#  Плейсхолдеры:
#      {query}    — исходный запрос пользователя
#      {plan}     — план от планировщика
#      {research} — контекст из интернета (или пометка, что его нет)
# =============================================================================

CODER_TASK_TEMPLATE = """User request:

{query}

Plan from the planning module:

{plan}

Research context:

{research}

Write the complete, compilable, runnable code that fulfills the user's request following the plan.
Return exactly one code block, with the language tag on the opening line. Do not add any text outside the block.
"""


# =============================================================================
#  ЗАДАЧА ДЛЯ КОДЕРА (исправление ошибки)
# =============================================================================
#  Отправляется кодеру, когда компиляция или запуск упали. Содержит
#  текущий код и сообщение об ошибке.
#  Плейсхолдеры:
#      {language}  — язык, на котором написан код
#      {code}      — текущий код
#      {stderr}    — ошибки компиляции или исполнения
#      {stdout}    — что программа успела напечатать
#      {iteration} — номер попытки исправления (1, 2, 3...)
# =============================================================================

FIX_TASK_TEMPLATE = """The previous version of the code failed to compile or run cleanly. This is fix attempt #{iteration}.

Language: {language}

Current code:

```

{code}

```

Compiler / runtime output:

--- stdout ---
{stdout}
--- stderr ---
{stderr}

Analyze the error carefully and return a corrected version of the ENTIRE program.

Rules:
- Return exactly one complete code block, with the language tag on the opening line.
- Include the whole program, not just the changed parts.
- Do not add explanations or comments outside the code block.
- Do not change the language unless the error clearly indicates the language is unsupported.
- If the error is caused by a missing library, replace it with a standard-library alternative.
- If the error is caused by a timeout, make the program faster or reduce its work.
"""


# =============================================================================
#  ЗАДАЧА ДЛЯ ИССЛЕДОВАТЕЛЯ
# =============================================================================
#  Отправляется модели-исследователю вместе с SYSTEM_RESEARCHER.
#  Плейсхолдеры:
#      {query}     — исходный запрос пользователя
#      {materials} — собранные материалы из web и GitHub
# =============================================================================

RESEARCH_TASK_TEMPLATE = """The user asked:

{query}

Raw materials collected from the internet:

{materials}

Compress these materials into a short, useful summary following the format described in your system prompt.
Focus only on what will help the coding module write better code for this specific task.
"""


# =============================================================================
#  ЗАДАЧА ДЛЯ АНАЛИТИКА
# =============================================================================
#  Отправляется модели-аналитику вместе с SYSTEM_ANALYZER.
#  Плейсхолдеры:
#      {language} — язык кода
#      {code}     — код для анализа
#      {question} — дополнительный вопрос пользователя (может быть пустым)
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
#  ЗАДАЧА ДЛЯ РЕЖИМА РАССУЖДЕНИЙ
# =============================================================================
#  Отправляется модели в режиме /reason вместе с SYSTEM_REASONING.
#  Плейсхолдеры:
#      {query} — запрос пользователя
# =============================================================================

REASONING_TASK_TEMPLATE = """The user asked:

{query}

Think through this request step by step and produce the reasoning chain followed by a short final answer, as described in your system prompt.
"""


# =============================================================================
#  ЗАДАЧА ДЛЯ СУБАГЕНТА-ФАЙЛОВОГО МЕНЕДЖЕРА
# =============================================================================
#  Используется, когда оркестратор хочет попросить файлового менеджера
#  выполнить действие, но само действие уже описано в kwargs
#  (action, path, content). Этот шаблон — резервный, для случая, когда
#  файловая операция идёт через текстовый интерфейс.
#  Плейсхолдеры:
#      {action} — что нужно сделать (read / write / patch / delete / list)
#      {path}   — путь к файлу или директории
#      {extra}  — дополнительный контекст (содержимое, старый фрагмент и т. п.)
# =============================================================================

FILE_MANAGER_TASK_TEMPLATE = """File operation request:

Action: {action}
Path:   {path}

Additional context:

{extra}

Perform the requested operation and report the result in one short line.
"""