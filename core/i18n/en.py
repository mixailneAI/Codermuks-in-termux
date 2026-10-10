# =============================================================================
#  Codermuks in Termux — английские строки интерфейса v1.1.0
# =============================================================================
#  Все тексты интерфейса на английском языке. Используется как:
#    • основной язык для пользователей из других стран;
#    • фолбэк, если в другом языке (например, ru) не хватает ключа.
#
#  Правила именования ключей:
#    • welcome.*       — баннер и приветствие;
#    • memo.*          — памятка (help);
#    • cmd.*           — названия команд;
#    • prompt.*        — строки ввода;
#    • status.*        — статусы во время работы;
#    • result.*        — финальный вывод;
#    • err.*           — ошибки;
#    • fallback.*      — переключение провайдеров;
#    • picker.*        — меню выбора (язык, агент);
#    • agent.*         — информация об агентах;
#    • lang.*          — информация о языках программирования;
#    • provider.*      — информация о провайдерах.
# =============================================================================

STRINGS: dict[str, str] = {

    # -------------------------------------------------------------------------
    #  Баннер и приветствие
    # -------------------------------------------------------------------------

    "welcome.banner":            "CODERMUKS in TERMUX",
    "welcome.subtitle":          "AI coding agent — powered by Mistral",
    "welcome.version":           "v1.1.0",
    "welcome.ready":             "Ready. Type a task or /help for commands.",

    # -------------------------------------------------------------------------
    #  Памятка (help)
    # -------------------------------------------------------------------------

    "memo.title":                "HELP MEMO",
    "memo.usage":                "Usage",
    "memo.commands":             "Commands",
    "memo.footer.model":         "Model",
    "memo.footer.planner":       "Planner",
    "memo.footer.lead":          "Team lead",

    # Описания команд в памятке
    "cmd.help":                  "show this memo",
    "cmd.exit":                  "exit the program",
    "cmd.changeagent":           "change the team lead (main agent)",
    "cmd.language":              "change the interface language",
    "cmd.langs":                 "list supported programming languages",
    "cmd.research":              "deep research (web + GitHub)",
    "cmd.reason":                "show reasoning chain",
    "cmd.analyze":               "analyze existing code",
    "cmd.clear":                 "clear the screen",
    "cmd.skills":                "list available skills",

    # Названия команд с префиксом /
    "cmd.name.help":             "/help",
    "cmd.name.exit":             "/exit",
    "cmd.name.changeagent":      "/changeagent",
    "cmd.name.language":         "/language",
    "cmd.name.langs":            "/langs",
    "cmd.name.research":         "/research",
    "cmd.name.reason":           "/reason",
    "cmd.name.analyze":          "/analyze",
    "cmd.name.clear":            "/clear",
    "cmd.name.skills":           "/skills",

    # -------------------------------------------------------------------------
    #  Ввод и промпты
    # -------------------------------------------------------------------------

    "prompt.main":               "codermuks",
    "prompt.arrow":              "▸",
    "prompt.enter_task":         "Enter your task",
    "prompt.confirm":            "Continue? [y/N]:",
    "prompt.select_number":      "Enter a number:",
    "prompt.press_enter":        "Press Enter to continue...",

    # -------------------------------------------------------------------------
    #  Статусы во время работы
    # -------------------------------------------------------------------------

    "status.thinking":           "thinking",
    "status.planning":           "planning",
    "status.generating":         "generating code",
    "status.compiling":          "compiling",
    "status.running":            "running",
    "status.fixing":             "fixing errors",
    "status.researching":        "researching",
    "status.analyzing":          "analyzing",
    "status.waiting":            "waiting for response",
    "status.timer":              "reasoning",
    "status.attempt":            "attempt",

    # -------------------------------------------------------------------------
    #  Финальный вывод
    # -------------------------------------------------------------------------

    "result.success":            "Task completed",
    "result.failure":            "Task failed",
    "result.language":           "Language",
    "result.iterations":         "Fix iterations",
    "result.reasoning_time":     "Reasoning time",
    "result.exit_code":          "Exit code",
    "result.code":               "Code",
    "result.stdout":             "Program output",
    "result.stderr":             "Errors",
    "result.notes":              "Notes",
    "result.saved":              "Code saved",
    "result.provider":           "Answered by",
    "result.no_code":            "No code generated.",
    "result.reasoning_done":     "Reasoning finished in {duration}",
    "result.artifact":           "Artifact saved: {path}",

    # Плюрализация: количество итераций
    "result.iterations_count_one":  "{count} iteration",
    "result.iterations_count_many": "{count} iterations",

    # -------------------------------------------------------------------------
    #  Ошибки
    # -------------------------------------------------------------------------

    "err.no_key":                "No API key configured. Add at least one key to ~/.codermuks/key.txt",
    "err.no_language":           "Interface language not selected.",
    "err.config_broken":         "Configuration file is broken: {error}",
    "err.provider_auth":         "Provider {name}: invalid API key.",
    "err.provider_rate_limit":   "Provider {name}: rate limit exceeded. Try again later.",
    "err.provider_server":       "Provider {name}: server temporarily unavailable.",
    "err.provider_network":      "Provider {name}: network error.",
    "err.provider_down":         "Provider {name} is unavailable.",
    "err.provider_not_configured": "Provider {name} is not configured. Add an API key.",
    "err.unknown_command":       "Unknown command: {command}",
    "err.hint_help":             "Type /help to see available commands.",
    "err.interrupted":           "Interrupted by user.",
    "err.unexpected":            "Unexpected error: {error}",
    "err.file_not_found":        "File not found: {path}",
    "err.lang_not_supported":    "Language not supported: {name}",
    "err.no_languages_available": "No programming languages available. Install compilers via pkg.",

    # -------------------------------------------------------------------------
    #  Fallback и переключение провайдеров
    # -------------------------------------------------------------------------

    "fallback.switch":           "Provider {name} is down. Switch to {next}? [y/n]:",
    "fallback.switched":         "Switched to {name}.",
    "fallback.kept_default":     "Keeping current provider.",
    "fallback.no_alternative":   "No alternative provider available.",
    "fallback.lead_changed":     "Team lead changed to {name}.",
    "fallback.auto":             "Automatically falling back to {name}.",

    # -------------------------------------------------------------------------
    #  Меню выбора языка
    # -------------------------------------------------------------------------

    "picker.language.title":     "Select a language · Выберите язык",
    "picker.language.prompt":    "Enter number · Введите номер:",
    "picker.language.invalid":   "Invalid choice. Please enter 1 or 2.",
    "picker.language.saved":     "Language saved: {name}. This choice cannot be changed later.",
    "picker.language.cancelled": "Language not selected. Exiting.",

    # -------------------------------------------------------------------------
    #  Меню выбора агента (/changeagent)
    # -------------------------------------------------------------------------

    "picker.agent.title":        "Choose the team lead (main agent):",
    "picker.agent.current":      "current",
    "picker.agent.configured":   "configured",
    "picker.agent.not_configured": "not configured",
    "picker.agent.prompt":       "Enter number or 'exit' to cancel:",
    "picker.agent.invalid":      "Invalid choice. Try again or type 'exit'.",
    "picker.agent.cancelled":    "Cancelled. Team lead unchanged.",
    "picker.agent.changed":      "Team lead changed: {name}",
    "picker.agent.already":      "Already the current team lead: {name}",
    "picker.agent.cannot_select": "Cannot select {name}: not configured. Add an API key first.",
    "picker.agent.hint":         "Only agents with a configured API key can be selected.",

    # -------------------------------------------------------------------------
    #  Информация об агентах
    # -------------------------------------------------------------------------

    "agent.mistral.name":        "Mistral",
    "agent.mistral.desc":        "Balanced. Best for planning and analysis.",
    "agent.qwen.name":           "Qwen Code",
    "agent.qwen.desc":           "Specialized in code generation.",
    "agent.deepseek.name":       "DeepSeek",
    "agent.deepseek.desc":       "Powerful universal model.",
    "agent.openrouter.name":     "OpenRouter",
    "agent.openrouter.desc":     "Aggregator of free models.",

    # -------------------------------------------------------------------------
    #  Информация о провайдерах
    # -------------------------------------------------------------------------

    "provider.model":            "Model",
    "provider.base_url":         "Base URL",
    "provider.api_key":          "API key",
    "provider.enabled":          "Enabled",
    "provider.disabled":         "Disabled",
    "provider.key_set":          "key set",
    "provider.key_missing":      "key missing",

    # -------------------------------------------------------------------------
    #  Информация о языках программирования
    # -------------------------------------------------------------------------

    "lang.title.basic":          "Main languages",
    "lang.title.extended":       "Extended languages",
    "lang.column.name":          "Language",
    "lang.column.tool":          "Tool",
    "lang.column.status":        "Status",
    "lang.column.install":       "Install",
    "lang.available":            "available",
    "lang.not_available":        "not available",
    "lang.summary":              "{available} of {total} languages ready to use.",
    "lang.hint":                 "To enable the rest, install the corresponding packages via pkg.",

    # -------------------------------------------------------------------------
    #  Скиллы
    # -------------------------------------------------------------------------

    "skill.research.name":       "Deep research",
    "skill.research.desc":       "Searches the web, reads GitHub, studies docs.",
    "skill.reason.name":         "Reasoning",
    "skill.reason.desc":         "Shows the full reasoning chain.",
    "skill.analyze.name":        "Analyze code",
    "skill.analyze.desc":        "Reviews existing code, finds bugs and improvements.",
    "skill.enabled":             "Skill enabled: {name}",
    "skill.disabled":            "Skill disabled: {name}",
    "skill.list_title":          "Available skills:",

    # -------------------------------------------------------------------------
    #  Установщик
    # -------------------------------------------------------------------------

    "installer.banner":          "Codermuks in Termux — installer v1.1.0",
    "installer.step":            "Step {current}/{total}",
    "installer.done":            "Codermuks in Termux v1.1.0 installed successfully!",
    "installer.next_run":        "Run: codermuks",
    "installer.help":            "Help: codermuks /help",
    "installer.uninstall":       "Remove: bash uninstall.sh",
    "installer.first_run_hint":  "On first launch codermuks will ask you to choose the interface language.",

    # -------------------------------------------------------------------------
    #  Общие слова
    # -------------------------------------------------------------------------

    "common.yes":                "yes",
    "common.no":                 "no",
    "common.ok":                 "OK",
    "common.cancel":             "Cancel",
    "common.exit":               "exit",
    "common.back":               "back",
    "common.current":            "current",
    "common.new":                "new",
    "common.unknown":            "unknown",
    "common.loading":            "Loading...",
    "common.done":               "Done.",
}