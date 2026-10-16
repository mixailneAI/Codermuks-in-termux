<div align="center">

<img src="assets/banner.png" alt="Codermuks in Termux — banner" width="800">

# 🤖 CODERMUKS IN TERMUX

### AI coding agent for Termux — 4 free providers, real projects, full history

[![Version](https://img.shields.io/badge/version-1.2.0-brightgreen?style=for-the-badge)](https://github.com/mixailneAI/Codermuks-in-termux/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-Termux-orange?style=for-the-badge&logo=android&logoColor=white)](https://termux.dev)
[![CI](https://img.shields.io/github/actions/workflow/status/mixailneAI/Codermuks-in-termux/ci.yml?branch=main&style=for-the-badge)](https://github.com/mixailneAI/Codermuks-in-termux/actions)

**🌐 [English](#-english) · 🇷🇺 [Русский](#-русский)**

</div>

---

## 🆕 What's new in v1.2.0 · Что нового в v1.2.0

<table>
<tr>
<th>🇬🇧 English</th>
<th>🇷🇺 Русский</th>
</tr>
<tr>
<td>

**✨ Added**

- **Real projects** — every task creates a named folder in `~/codermuks-workspace/`
- **Project history** — Codermuks remembers what was done before
- **Context reading** — reads existing files to understand the project
- **Smart naming** — `snake-game` instead of `project000001`
- **Real-time reasoning chain** — you see every step of the agent
- **`/projects`** — list, view, and delete your projects
- **`/history <name>`** — see what was done in any project

**🔧 Changed**

- Launcher resolves symlinks correctly
- No blocking `input()` during live display
- `stdin=DEVNULL` prevents hangs on `input()` in generated code
- Default Mistral model: `codestral-latest` (works on free tier)

</td>
<td>

**✨ Добавлено**

- **Настоящие проекты** — каждая задача создаёт папку в `~/codermuks-workspace/`
- **История проектов** — Codermuks помнит, что было сделано раньше
- **Чтение контекста** — читает существующие файлы, чтобы понять проект
- **Умные имена** — `snake-game` вместо `project000001`
- **Real-time цепочка рассуждений** — видно каждый шаг агента
- **`/projects`** — список, просмотр и удаление проектов
- **`/history <имя>`** — что было сделано в проекте

**🔧 Изменено**

- Лаунчер корректно разыменовывает симлинки
- Нет блокирующего `input()` во время Live-панели
- `stdin=DEVNULL` — не зависает на `input()` в сгенерированном коде
- Модель Mistral по умолчанию: `codestral-latest` (работает на free tier)

</td>
</tr>
</table>

### 📊 Version history · История версий

- **v1.2.0** — current · текущая: real projects, history, live reasoning
- **v1.1.0** — multi-provider, i18n, tests
- **v1.0.1** — fixes: filenames, install.sh, symlink
- **v1.0.0** — initial release · первый релиз

[Compare v1.1.0 → v1.2.0](https://github.com/mixailneAI/Codermuks-in-termux/compare/v1.1.0...v1.2.0)

---

## 🌐 English

### What is Codermuks?

**Codermuks in Termux** is an autonomous AI coding agent that turns your Android terminal into a full development workspace. You describe a task — it writes the code, compiles it, runs it, catches errors, fixes them in a loop, and delivers the final result only when everything works cleanly.

**What's new in v1.2.0:** Codermuks now works with **real projects**. Every task creates a named folder in `~/codermuks-workspace/`. It remembers what it did before, reads existing files to understand the context, and shows you a real-time reasoning chain in the live panel.

```bash
codermuks
```

📁 Real projects in a real workspace

Every task creates a project with a meaningful name — no more project000001:

```
~/codermuks-workspace/
├── snake-game/
│   ├── snake.py
│   ├── README.md
│   └── .codermuks/
│       ├── metadata.json
│       └── history.json
├── calculator/
│   └── calculator.py
└── http-server-go/
    ├── main.go
    └── go.mod
```

Ask once — Codermuks creates the project. Ask again a week later — it reads the existing code and continues from where it left off.

🤖 Meet the team

Codermuks is a multi-agent system. One agent is your team lead — it receives your request, plans the task, and coordinates the rest. The others are specialists called in when needed.

Agent Role Free tier Works in RU
Mistral AI ⭐ Default leader · planning + analysis Free tier ✅
Qwen Code Code generation specialist (qwen3-coder) 1000 req/day ✅
DeepSeek Powerful universal model 5M tokens on signup ✅
OpenRouter Aggregator of free models (:free suffix) 50 req/day ✅

🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/mixailneAI/Codermuks-in-termux.git
cd Codermuks-in-termux

# 2. Run the installer
bash install.sh

# 3. Insert at least one API key
nano ~/.codermuks/key.txt

# 4. Launch
codermuks
```

On first launch, Codermuks will ask you to choose the interface language:

```
╔═══════════════════════════════════════════════════════╗
║                                                       ║
║              Select a language · Выберите язык        ║
║                                                       ║
║                     [1] English                       ║
║                     [2] Русский                       ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝
```

💡 Get free API keys:

· Mistral: console.mistral.ai/api-keys
· Qwen: dashscope.console.aliyun.com/apiKey
· DeepSeek: platform.deepseek.com/api_keys
· OpenRouter: openrouter.ai/keys

🎮 Usage

```bash
codermuks                                # interactive mode
codermuks "write an HTTP server in Go"   # run a task immediately
codermuks /research "study tokio async"  # deep research mode
```

📖 Commands

Command What it does
/changeagent Change the team lead — see the list of agents with ✅/❌ statuses
/projects List all your projects in the workspace
/history <name> Show history of a specific project
/language Change the interface language (EN/RU)
/research Enable deep research (web + GitHub)
/reason Show the full reasoning chain
/analyze Analyze existing code
/langs List supported programming languages
/skills List available skills
/clear Clear the screen
/help Show help
/exit Exit the program

⚙️ How it works

```
User query
    │
    ▼
┌─────────────────────┐
│  Project Decider    │  ← continue / create / new?
│                     │    e.g. "snake-game" or "calculator"
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Planner (JSON)     │  ← language, steps, files, edge cases
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Coder              │  ← writes files with ### FILE: markers
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Compile & Run      │  ← errors? → Fixer → retry
└──────────┬──────────┘
           │
           ▼
      ✅ Result
      📁 Saved to ~/codermuks-workspace/<project>/
      📜 Logged to .codermuks/history.json
```

Every step emits an event through the EventBus → the LivePanel draws it in real time:

```
⏱  00:12   ·   пишу код

  ✔  проект       ·   snake-game
  ✔  планирую     ·   определил язык: Python
  ✔  пишу код     ·   snake.py
  ✔  компилирую   ·   python, попытка 1
```

✨ Features

 
📁 Real projects Named folders in ~/codermuks-workspace/
📚 Project history Every task logged, agent remembers context
🧠 Multi-agent team Lead + specialists, coordinated automatically
🌐 4 free providers Mistral, Qwen, DeepSeek, OpenRouter
🔁 Automatic fallback Switch agents when one fails
🌍 Bilingual UI English / Русский, selected at first launch
⚙️ 15+ languages C, C++, Rust, Go, Python, Java, C#, Kotlin, Swift, Ruby, PHP, Dart, Elixir, Haskell, Lua
🔁 Self-fixing loop Writes → compiles → runs → catches errors → fixes
⏱ Live reasoning chain Real-time view of every agent step
🔎 Deep research mode Searches web, reads GitHub, studies docs
🚀 One command Install once — type codermuks forever
🔒 Local & private Code stays on device; only prompts go to providers

📦 Requirements

· Termux (Android 7.0+)
· Python 3.11+
· At least one API key — all free, all work in Russia
· ~500 MB free space (for compilers & runtimes)

❓ FAQ

<details>
<summary><b>Is it really free?</b></summary>

Yes. All 4 providers have permanent free tiers. You only need to create accounts and get API keys.

</details>

<details>
<summary><b>Where are my projects stored?</b></summary>

In ~/codermuks-workspace/ on your device. Each project is a folder with a meaningful name. You can open them in any editor, version them with Git, or share them.

</details>

<details>
<summary><b>Does it remember previous tasks?</b></summary>

Yes. Every project has a .codermuks/history.json file that stores every task. When you ask for a new change, Codermuks reads the existing code and history, and continues from where it left off.

</details>

<details>
<summary><b>Can I add my own provider?</b></summary>

Yes. Create a subclass of OpenAICompatibleProvider in core/llm_providers/, set name, display_name, default_model, and register it. That's it.

</details>

<details>
<summary><b>Where are my API keys stored?</b></summary>

In ~/.codermuks/key.txt on your device. They are never sent to us — only to the provider you call.

</details>

⚖️ Disclaimer

Codermuks in Termux is an independent open-source project. It is not affiliated with OpenAI, Inc., does not use their trademarks, and is not a clone of the Codex product.

📜 License

Apache License 2.0 — see LICENSE for details.

---

<br>
<br>

🇷🇺 Русский

Что такое Codermuks?

Codermuks in Termux — это автономный AI-агент для программирования, который превращает твой Android-терминал в полноценную среду разработки. Ты описываешь задачу — он пишет код, компилирует его, запускает, ловит ошибки, исправляет их в цикле и выдаёт финальный результат только тогда, когда всё работает без ошибок.

Что нового в v1.2.0: Codermuks теперь работает с настоящими проектами. Каждая задача создаёт папку с осмысленным именем в ~/codermuks-workspace/. Он помнит, что делал раньше, читает существующие файлы для понимания контекста и показывает цепочку рассуждений в реальном времени.

```bash
codermuks
```

📁 Настоящие проекты в настоящем workspace

Каждая задача создаёт проект с осмысленным именем — никаких project000001:

```
~/codermuks-workspace/
├── snake-game/
│   ├── snake.py
│   ├── README.md
│   └── .codermuks/
│       ├── metadata.json
│       └── history.json
├── calculator/
│   └── calculator.py
└── http-server-go/
    ├── main.go
    └── go.mod
```

Спросил один раз — Codermuks создал проект. Спросил через неделю — читает существующий код и продолжает с того места, где остановился.

🤖 Знакомься с командой

Codermuks — это мультиагентная система. Один агент — главный: он получает твой запрос, планирует задачу и координирует остальных.

Агент Роль Бесплатно Работает в РФ
Mistral AI ⭐ Главный по умолчанию · планирование и анализ Free tier ✅
Qwen Code Специалист по коду (qwen3-coder) 1000 запросов/день ✅
DeepSeek Мощная универсальная модель 5M токенов при регистрации ✅
OpenRouter Агрегатор бесплатных моделей (:free) 50 запросов/день ✅

🚀 Быстрый старт

```bash
# 1. Клонируй репозиторий
git clone https://github.com/mixailneAI/Codermuks-in-termux.git
cd Codermuks-in-termux

# 2. Запусти установщик
bash install.sh

# 3. Вставь хотя бы один API-ключ
nano ~/.codermuks/key.txt

# 4. Запусти
codermuks
```

💡 Получи бесплатные API-ключи:

· Mistral: console.mistral.ai/api-keys
· Qwen: dashscope.console.aliyun.com/apiKey
· DeepSeek: platform.deepseek.com/api_keys
· OpenRouter: openrouter.ai/keys

🎮 Использование

```bash
codermuks                                # интерактивный режим
codermuks "напиши HTTP-сервер на Go"     # сразу выполнить задачу
codermuks /research "изучи tokio async"  # режим глубокого исследования
```

📖 Команды

Команда Что делает
/changeagent Сменить главного агента — список с пометками ✅/❌
/projects Список всех твоих проектов
/history <имя> История конкретного проекта
/language Сменить язык интерфейса (EN/RU)
/research Включить глубокое исследование (web + GitHub)
/reason Показать полную цепочку рассуждений
/analyze Проанализировать существующий код
/langs Список поддерживаемых языков программирования
/skills Список доступных скиллов
/clear Очистить экран
/help Показать справку
/exit Выйти из программы

⚙️ Как это работает

```
Запрос пользователя
    │
    ▼
┌─────────────────────┐
│  Решатель проекта   │  ← continue / create / new?
│                     │    например "snake-game" или "calculator"
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Планировщик (JSON) │  ← язык, шаги, файлы, edge cases
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Кодер              │  ← пишет файлы с ### FILE: маркерами
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Компиляция и запуск│  ← ошибки? → Фиксер → повтор
└──────────┬──────────┘
           │
           ▼
      ✅ Результат
      📁 Сохранено в ~/codermuks-workspace/<проект>/
      📜 Записано в .codermuks/history.json
```

Каждый шаг эмитит событие в EventBus → LivePanel рисует его в реальном времени:

```
⏱  00:12   ·   пишу код

  ✔  проект       ·   snake-game
  ✔  планирую     ·   определил язык: Python
  ✔  пишу код     ·   snake.py
  ✔  компилирую   ·   python, попытка 1
```

✨ Возможности

 
📁 Настоящие проекты Именованные папки в ~/codermuks-workspace/
📚 История проектов Каждая задача записана, агент помнит контекст
🧠 Мультиагентная команда Лидер + специалисты, координация автоматическая
🌐 4 бесплатных провайдера Mistral, Qwen, DeepSeek, OpenRouter
🔁 Автоматический fallback Переключение при сбое лидера
🌍 Двуязычный интерфейс English / Русский, выбор при первом запуске
⚙️ 15+ языков C, C++, Rust, Go, Python, Java, C#, Kotlin, Swift, Ruby, PHP, Dart, Elixir, Haskell, Lua
🔁 Цикл фикса Пишет → компилирует → запускает → ловит ошибки → исправляет
⏱ Real-time цепочка Каждый шаг агента виден в реальном времени
🔎 Deep research Поиск в сети, чтение GitHub, изучение доков
🚀 Одна команда Установил один раз — codermuks навсегда
🔒 Локально и приватно Код остаётся у тебя

📦 Требования

· Termux (Android 7.0+)
· Python 3.11+
· Минимум один API-ключ — все бесплатные, работают в России
· ~500 МБ свободного места

❓ Частые вопросы

<details>
<summary><b>Это действительно бесплатно?</b></summary>

Да. У всех 4 провайдеров есть постоянные бесплатные тарифы.

</details>

<details>
<summary><b>Где хранятся мои проекты?</b></summary>

В ~/codermuks-workspace/ на твоём устройстве. Каждый проект — папка с осмысленным именем. Можно открыть в любом редакторе, версионировать Git, делиться.

</details>

<details>
<summary><b>Он помнит предыдущие задачи?</b></summary>

Да. У каждого проекта есть .codermuks/history.json, где хранятся все задачи. Когда ты просишь новое изменение, Codermuks читает существующий код и историю и продолжает с того места, где остановился.

</details>

<details>
<summary><b>Можно ли добавить своего провайдера?</b></summary>

Да. Создай наследника OpenAICompatibleProvider в core/llm_providers/ и зарегистрируй.

</details>

<details>
<summary><b>Где хранятся мои API-ключи?</b></summary>

В ~/.codermuks/key.txt на твоём устройстве. Они не передаются ни нам, ни кому-либо ещё — только тому провайдеру, к которому идёт запрос.

</details>

⚖️ Дисклеймер

Codermuks in Termux — независимый проект с открытым исходным кодом. Он не связан с OpenAI, Inc., не использует их торговые марки и не является клоном продукта Codex.

📜 Лицензия

Apache License 2.0 — подробности в файле LICENSE.

---

<div align="center">

<img src="assets/logo.png" alt="Codermuks logo" width="120">

💚 Спасибо, что используешь Codermuks! · Thanks for using Codermuks!

⭐ Поставь звезду, если проект помог · Star the repo if it helped

Made with ❤️ by mixailneAI

</div>
