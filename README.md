
<div align="center">

<img src="assets/banner.png" alt="Codermuks in Termux — banner" width="800">

# 🤖 CODERMUKS IN TERMUX

### AI coding agent for Termux — 4 free providers, one team

[![Version](https://img.shields.io/badge/version-1.1.0-brightgreen?style=for-the-badge)](https://github.com/mixailneAI/Codermuks-in-termux/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-Termux-orange?style=for-the-badge&logo=android&logoColor=white)](https://termux.dev)
[![Providers](https://img.shields.io/badge/providers-4-red?style=for-the-badge)](https://github.com/mixailneAI/Codermuks-in-termux#-providers)

**🌐 [English](#-english) · 🇷🇺 [Русский](#-русский)**

</div>

---

## 🆕 What's new in v1.1.0 · Что нового в v1.1.0

<table>
<tr>
<th>🇬🇧 English</th>
<th>🇷🇺 Русский</th>
</tr>
<tr>
<td>

**✨ Added**

- **Multi-provider support** — 4 free LLMs: Mistral, Qwen, DeepSeek, OpenRouter
- **Multi-agent team** — one lead agent + specialists, coordinated by `TeamLead`
- **`/changeagent` command** — switch the team lead on the fly
- **Automatic fallback** — if the lead fails, you're asked to switch to another agent
- **Interface language selection** — English / Русский at first launch
- **Bilingual UI** — all commands, help, and messages translated (EN/RU)
- **Provider badges** — see which agent answered your request
- **Config migration** — `update.sh` safely upgrades `config.json` between versions

**🔧 Changed**

- `key.txt` is now JSON with 4 provider keys
- `config.json` stores language, team lead, fallback order, provider settings
- All CLI strings go through the i18n system
- Improved installer with per-package error tolerance
- `mistralai` installed from GitHub to bypass PyPI quarantine

**🛠 Fixed**

- Launcher correctly resolves symlinks
- Typos in filenames and folder names
- `openjdk-17` → `openjdk-21` migration
- Imports after folder rename

</td>
<td>

**✨ Добавлено**

- **Поддержка 4 провайдеров** — Mistral, Qwen, DeepSeek, OpenRouter
- **Мультиагентная команда** — главный агент + специалисты, координация через `TeamLead`
- **Команда `/changeagent`** — смена главного агента на лету
- **Автоматический fallback** — если лидер упал, предлагается переключиться
- **Выбор языка интерфейса** — English / Русский при первом запуске
- **Двуязычный интерфейс** — все команды, справка и сообщения переведены (EN/RU)
- **Метка провайдера** — видно, какой агент ответил на запрос
- **Миграция конфига** — `update.sh` аккуратно обновляет `config.json` между версиями

**🔧 Изменено**

- `key.txt` теперь JSON с 4 ключами провайдеров
- `config.json` хранит язык, главного агента, порядок fallback, настройки провайдеров
- Все строки CLI идут через i18n
- Установщик стал устойчивее к ошибкам отдельных пакетов
- `mistralai` ставится из GitHub, минуя карантин PyPI

**🛠 Исправлено**

- Лаунчер корректно разыменовывает симлинки
- Опечатки в именах файлов и папок
- `openjdk-17` → `openjdk-21`
- Импорты после переименования папок

</td>
</tr>
</table>

### 📊 Version history · История версий

- **v1.1.0** — current · текущая: multi-provider, multi-agent, bilingual
- **v1.0.1** — fixes: filenames, install.sh, symlink
- **v1.0.0** — initial release · первый релиз

[Compare v1.0.1 → v1.1.0](https://github.com/mixailneAI/Codermuks-in-termux/compare/v1.0.1...v1.1.0)

---

## 🌐 English

### What is Codermuks?

**Codermuks in Termux** is an autonomous AI coding agent that turns your Android terminal into a full development workspace. You describe a task — it writes the code, compiles it, runs it, catches errors, fixes them in a loop, and delivers the final result only when everything works cleanly.

**What's new in v1.1.0:** Codermuks is no longer tied to a single LLM. It's a **team of 4 free AI agents** (Mistral, Qwen, DeepSeek, OpenRouter) with a user-selectable leader. You can switch the leader with `/changeagent`. If the leader goes down, Codermuks asks if you want to switch to an alternative.

No IDE. No editor. No browser. Just your terminal and one command.

```bash
codermuks
```

<div align="center">
  <img src="assets/demo.gif" alt="Codermuks demo" width="700">
  <br>
  <em>Codermuks writing, compiling and testing code in real time</em>
</div>

🤖 Meet the team

Codermuks is a multi-agent system. One agent is your team lead — it receives your request, plans the task, and coordinates the rest. The others are specialists called in when needed.

Agent Role Free tier Works in RU
Mistral AI ⭐ Default leader · planning + analysis Free tier ✅
Qwen Code Code generation specialist (qwen3-coder) 1000 req/day ✅
DeepSeek Powerful universal model 5M tokens on signup ✅
OpenRouter Aggregator of free models (:free suffix) 50 req/day ✅

💡 You only need one API key to start. The rest can be added later.

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
/language Change the interface language (EN/RU)
/research Enable deep research (web + GitHub)
/reason Show the full reasoning chain
/analyze Analyze existing code
/langs List supported programming languages
/skills List available skills
/clear Clear the screen
/help Show help
/exit Exit the program

🔄 /changeagent in action

```
🤖 Choose the team lead (main agent):

  [1]  ✔ Mistral AI     Balanced. Best for planning…    ✅ current
  [2]  ✔ Qwen Code      Specialized in code generation… ✅ configured
  [3]  ✘ DeepSeek       Powerful universal model…       ❌ not configured
  [4]  ✘ OpenRouter     Aggregator of free models…      ❌ not configured

  ⓘ Only agents with a configured API key can be selected.

  ▸ 2

  ✔ Team lead changed: Qwen Code
```

Once changed, every subsequent request is handled by Qwen. The change persists across restarts.

⚙️ How it works

```
User query
    │
    ▼
┌─────────────────┐
│    TeamLead     │  ← selected agent (default: Mistral)
│  (team leader)  │
└────────┬────────┘
         │  plans, delegates, coordinates
   ┌─────┴─────┬─────────┬──────────┐
   ▼           ▼         ▼          ▼
┌──────┐   ┌──────┐  ┌──────┐  ┌──────────┐
│Coder │   │Tester│  │Resea-│  │File mgr  │
│      │   │      │  │rcher │  │          │
└──┬───┘   └──┬───┘  └──┬───┘  └────┬─────┘
   │          │         │           │
   ▼          ▼         ▼           ▼
 writes    compile    web/GitHub   read/write
  code     & run      search       files
    │          │
    └────┬─────┘
         ▼
   error? → fix loop
         │
         ▼
   ✅ final answer + timer
```

If the leader fails (network, rate limit), a FallbackManager picks the next configured agent from fallback_order and asks you to confirm the switch.

✨ Features

 
🧠 Multi-agent team Lead + specialists, coordinated automatically
🌐 4 free providers Mistral, Qwen, DeepSeek, OpenRouter
🔁 Automatic fallback Switch agents when one fails
🌍 Bilingual UI English / Русский, selected at first launch
⚙️ 15+ languages C, C++, Rust, Go, Python, Java, C#, Kotlin, Swift, Ruby, PHP, Dart, Elixir, Haskell, Lua
🔁 Self-fixing loop Writes → compiles → runs → catches errors → fixes
⏱ Live reasoning timer Watch how long the agent thinks
🔎 Deep research mode Searches web, reads GitHub, studies docs
🎨 Beautiful TUI Colored output, syntax highlighting, tables
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

Yes. All 4 providers have permanent free tiers. You only need to create accounts and get API keys. Heavy usage may require paid plans from individual providers, but the agent itself never charges you.

</details>

<details>
<summary><b>Why 4 providers and not just one?</b></summary>

Reliability + specialization. If Mistral is down, you can switch to Qwen with /changeagent. If Qwen hits its daily limit, DeepSeek or OpenRouter are ready. Plus, qwen3-coder is specifically trained on code and often writes better code than general-purpose models.

</details>

<details>
<summary><b>Can I add my own provider?</b></summary>

Yes. Create a subclass of OpenAICompatibleProvider in core/llm_providers/, set name, display_name, default_model, and register it in core/llm_providers/__init__.py. That's it.

</details>

<details>
<summary><b>Where are my API keys stored?</b></summary>

In ~/.codermuks/key.txt on your device. They are never sent to us or anyone else — only to the provider you're calling. The file is excluded from Git via .gitignore.

</details>

<details>
<summary><b>Does it work outside Termux?</b></summary>

The core logic works on any Linux with Python 3.11+. The installer is Termux-specific, but you can install dependencies manually on any Linux.

</details>

⚖️ Disclaimer

Codermuks in Termux is an independent open-source project. It is not affiliated with OpenAI, Inc., does not use their trademarks, and is not a clone of the Codex product. It is a standalone AI agent.

📜 License

Apache License 2.0 — see LICENSE for details.

---

<br>
<br>

🇷🇺 Русский

Что такое Codermuks?

Codermuks in Termux — это автономный AI-агент для программирования, который превращает твой Android-терминал в полноценную среду разработки. Ты описываешь задачу — он пишет код, компилирует его, запускает, ловит ошибки, исправляет их в цикле и выдаёт финальный результат только тогда, когда всё работает без ошибок.

Что нового в v1.1.0: Codermuks больше не привязан к одному LLM. Это команда из 4 бесплатных AI-агентов (Mistral, Qwen, DeepSeek, OpenRouter) с выбираемым вручную главным агентом. Переключить лидера можно командой /changeagent. Если лидер упал — Codermuks предложит переключиться на альтернативу.

Никаких IDE. Никаких редакторов. Никаких браузеров. Только твой терминал и одна команда.

```bash
codermuks
```

<div align="center">
  <img src="assets/demo.gif" alt="Демонстрация Codermuks" width="700">
  <br>
  <em>Codermuks пишет, компилирует и тестирует код в реальном времени</em>
</div>

🤖 Знакомься с командой

Codermuks — это мультиагентная система. Один агент — главный: он получает твой запрос, планирует задачу и координирует остальных. Другие — специалисты, вызываются по необходимости.

Агент Роль Бесплатно Работает в РФ
Mistral AI ⭐ Главный по умолчанию · планирование и анализ Free tier ✅
Qwen Code Специалист по коду (qwen3-coder) 1000 запросов/день ✅
DeepSeek Мощная универсальная модель 5M токенов при регистрации ✅
OpenRouter Агрегатор бесплатных моделей (:free) 50 запросов/день ✅

💡 Достаточно одного API-ключа, чтобы начать. Остальные можно добавить позже.

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

При первом запуске Codermuks спросит язык интерфейса:

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
/language Сменить язык интерфейса (EN/RU)
/research Включить глубокое исследование (web + GitHub)
/reason Показать полную цепочку рассуждений
/analyze Проанализировать существующий код
/langs Список поддерживаемых языков программирования
/skills Список доступных скиллов
/clear Очистить экран
/help Показать справку
/exit Выйти из программы

🔄 /changeagent в действии

```
🤖 Выбери главного агента команды:

  [1]  ✔ Mistral AI     Сбалансированный. Лучше для плани… ✅ текущий
  [2]  ✔ Qwen Code      Специализируется на генерации кода… ✅ настроен
  [3]  ✘ DeepSeek       Мощная универсальная модель…       ❌ не настроен
  [4]  ✘ OpenRouter     Агрегатор бесплатных моделей…      ❌ не настроен

  ⓘ Выбрать можно только агентов с заполненным API-ключом.

  ▸ 2

  ✔ Главный агент изменён: Qwen Code
```

После смены все последующие запросы обрабатываются Qwen. Выбор сохраняется между запусками.

⚙️ Как это работает

```
Запрос пользователя
    │
    ▼
┌─────────────────┐
│    TeamLead     │  ← выбранный агент (по умолчанию Mistral)
│  (лидер команды)│
└────────┬────────┘
         │  планирует, делегирует, координирует
   ┌─────┴─────┬─────────┬──────────┐
   ▼           ▼         ▼          ▼
┌──────┐   ┌──────┐  ┌──────┐  ┌──────────┐
│Кодер │   │Тест-р│  │Иссле-│  │Файловый  │
│      │   │      │  │доват.│  │менеджер  │
└──┬───┘   └──┬───┘  └──┬───┘  └────┬─────┘
   │          │         │           │
   ▼          ▼         ▼           ▼
 пишет     компил.   web/GitHub   чтение /
  код      и запуск   поиск       запись
    │          │
    └────┬─────┘
         ▼
   ошибка? → цикл фикса
         │
         ▼
   ✅ финал + таймер
```

Если лидер упал (сеть, лимит), FallbackManager выбирает следующего настроенного агента из fallback_order и спрашивает подтверждение на переключение.

✨ Возможности

 
🧠 Мультиагентная команда Лидер + специалисты, координация автоматическая
🌐 4 бесплатных провайдера Mistral, Qwen, DeepSeek, OpenRouter
🔁 Автоматический fallback Переключение при сбое лидера
🌍 Двуязычный интерфейс English / Русский, выбор при первом запуске
⚙️ 15+ языков C, C++, Rust, Go, Python, Java, C#, Kotlin, Swift, Ruby, PHP, Dart, Elixir, Haskell, Lua
🔁 Цикл фикса Пишет → компилирует → запускает → ловит ошибки → исправляет
⏱ Таймер рассуждения Видно, сколько агент думает
🔎 Deep research Поиск в сети, чтение GitHub, изучение доков
🎨 Красивый TUI Цвета, подсветка синтаксиса, таблицы
🚀 Одна команда Установил один раз — codermuks навсегда
🔒 Локально и приватно Код остаётся у тебя; в провайдеры уходят только промпты

📦 Требования

· Termux (Android 7.0+)
· Python 3.11+
· Минимум один API-ключ — все бесплатные, все работают в России
· ~500 МБ свободного места (для компиляторов и рантаймов)

❓ Частые вопросы

<details>
<summary><b>Это действительно бесплатно?</b></summary>

Да. У всех 4 провайдеров есть постоянные бесплатные тарифы. Нужно только создать аккаунт и получить API-ключ. При интенсивном использовании может понадобиться платный план у отдельного провайдера, но сам агент денег не берёт.

</details>

<details>
<summary><b>Почему 4 провайдера, а не один?</b></summary>

Надёжность + специализация. Если Mistral недоступен — переключаешься на Qwen через /changeagent. Если у Qwen кончился дневной лимит — есть DeepSeek и OpenRouter. Плюс qwen3-coder специально обучен на коде и часто пишет лучше универсальных моделей.

</details>

<details>
<summary><b>Можно ли добавить своего провайдера?</b></summary>

Да. Создай наследника OpenAICompatibleProvider в core/llm_providers/, задай name, display_name, default_model и зарегистрируй в core/llm_providers/__init__.py. Всё.

</details>

<details>
<summary><b>Где хранятся мои API-ключи?</b></summary>

В ~/.codermuks/key.txt на твоём устройстве. Они не передаются ни нам, ни кому-либо ещё — только тому провайдеру, к которому идёт запрос. Файл исключён из Git через .gitignore.

</details>

<details>
<summary><b>Работает ли вне Termux?</b></summary>

Ядро работает на любом Linux с Python 3.11+. Установщик оптимизирован под Termux, но зависимости можно поставить вручную на любом Linux.

</details>

⚖️ Дисклеймер

Codermuks in Termux — независимый проект с открытым исходным кодом. Он не связан с OpenAI, Inc., не использует их торговые марки и не является клоном продукта Codex. Это самостоятельный AI-агент.

📜 Лицензия

Apache License 2.0 — подробности в файле LICENSE.

---

<div align="center">

<img src="assets/logo.png" alt="Codermuks logo" width="120">

💚 Спасибо, что используешь Codermuks! · Thanks for using Codermuks!

⭐ Поставь звезду, если проект помог · Star the repo if it helped

https://img.shields.io/github/stars/mixailneAI/Codermuks-in-termux?style=social
https://img.shields.io/github/forks/mixailneAI/Codermuks-in-termux?style=social

Made with ❤️ by mixailneAI

</div>