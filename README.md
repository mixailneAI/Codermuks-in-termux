
<div align="center">

# 🤖 CODERMUKS IN TERMUX

### AI coding agent for Termux — powered by Mistral

[![License](https://img.shields.io/badge/license-Apache%202.0-blue?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-Termux-orange?style=for-the-badge&logo=android&logoColor=white)](https://termux.dev)
[![Model](https://img.shields.io/badge/model-Mistral-red?style=for-the-badge)](https://mistral.ai)

**🌐 [English](#-english) · 🇷🇺 [Русский](#-русский)**

</div>

---

## 🌐 English

### What is Codermuks?

**Codermuks in Termux** is an autonomous AI coding agent that turns your Android terminal into a full development workspace. You describe a task — it writes the code, compiles it, runs it, catches errors, fixes them in a loop, and delivers the final result only when everything works cleanly.

No IDE. No editor. No browser. Just your terminal and one command.

```bash
codermuks
```

### ✨ Features

| | |
|---|---|
| 🧠 **Multi-agent architecture** | Planner, coder, tester, researcher, file manager — all coordinated by an orchestrator |
| ⚙️ **15+ languages** | C, C++, Rust, Go, Python, Java, C#, Kotlin, Swift, Ruby, PHP, Dart, Elixir, Haskell, Lua |
| 🔁 **Self-fixing loop** | Writes → compiles → runs → catches `stderr` → fixes → repeats until clean |
| ⏱ **Live reasoning timer** | Watch how long the agent thinks before answering |
| 🌐 **Deep research mode** | Searches the web, reads GitHub repos and docs, studies theory |
| 🎨 **Beautiful TUI** | Bilingual help memo (RU/EN), colored output, syntax-highlighted code |
| 🚀 **One command** | Install once — type `codermuks` forever |
| 🔒 **Local & private** | Your code stays on your device; only prompts go to Mistral |

### 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/mixailneAI/Codermuks-in-termux.git
cd Codermuks-in-termux

# 2. Run the installer
bash install.sh

# 3. Insert your Mistral API key
nano key.txt

# 4. Launch
codermuks
```

> 💡 Get a **free Mistral API key** → [console.mistral.ai/api-keys](https://console.mistral.ai/api-keys)

### 🎮 Usage

```bash
codermuks                                # interactive mode
codermuks "write an HTTP server in Go"   # run a task immediately
codermuks /research "study tokio async"  # deep research mode
```

Inside a session:

| Command | Action |
|---|---|
| `/research` | Enable deep research (web + GitHub) |
| `/reason` | Show the full reasoning chain |
| `/analyze` | Analyze existing code |
| `/help` | Show help |
| `/exit` | Exit the program |

### 🏗 How It Works

```
User query
    │
    ▼
┌─────────────────┐
│   Orchestrator  │  ← Mistral Large (planner)
└────────┬────────┘
         │  delegates tasks
   ┌─────┴─────┬─────────┬──────────┐
   ▼           ▼         ▼          ▼
┌──────┐   ┌──────┐  ┌──────┐  ┌──────────┐
│Coder │   │Tester│  │Resea-│  │File mgr  │
│      │   │      │  │rcher │  │          │
└──┬───┘   └──┬───┘  └──┬───┘  └────┬─────┘
   │          │         │           │
   ▼          ▼         ▼           ▼
 Codestral  Compile   Web / GH    Read/Write
  writes    & run     search      files
    │          │
    └────┬─────┘
         ▼
   error? → fix loop
         │
         ▼
   ✅ final answer + timer
```

### 📦 Requirements

- **Termux** (Android 7.0+)
- **Python 3.11+**
- **Mistral API key** ([free tier available](https://console.mistral.ai/api-keys))
- ~500 MB free space (for compilers & runtimes)

### 🛠 Manual Installation (advanced)

```bash
pkg update && pkg upgrade -y
pkg install -y python clang rust golang openjdk-17 git
pip install mistralai rich requests pyfiglet

ln -sf "$PWD/codermuks" "$PREFIX/bin/codermuks"
chmod +x codermuks install.sh
```

### ❓ FAQ

<details>
<summary><b>Is it free?</b></summary>

Yes — the agent itself is free and open-source. You only need a Mistral API key, and Mistral offers a free tier. Heavy usage may require a paid plan from Mistral.

</details>

<details>
<summary><b>Does it work on regular Linux?</b></summary>

Yes, but the installer is optimized for Termux. On Linux, install dependencies with your package manager and run `python main.py`.

</details>

<details>
<summary><b>Can I use a different LLM provider?</b></summary>

Not yet, but support for Gemini, Groq, Cerebras and OpenAI-compatible endpoints is planned.

</details>

<details>
<summary><b>Is my code sent to Mistral?</b></summary>

Only the code the agent is actively working on, as part of the prompt. Your files are never uploaded unless required for the task.

</details>

### ⚖️ Disclaimer

**Codermuks in Termux** is an independent open-source project. It is **not affiliated with OpenAI, Inc.**, does not use their trademarks, and is **not a clone of the Codex product**. It is a standalone AI agent built on Mistral models.

### 📜 License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

---

<br>
<br>

## 🇷🇺 Русский

### Что такое Codermuks?

**Codermuks in Termux** — это автономный AI-агент для программирования, который превращает твой Android-терминал в полноценную среду разработки. Ты описываешь задачу — он пишет код, компилирует его, запускает, ловит ошибки, исправляет их в цикле и выдаёт финальный результат только тогда, когда всё работает без ошибок.

Никаких IDE. Никаких редакторов. Никаких браузеров. Только твой терминал и одна команда.

```bash
codermuks
```

### ✨ Возможности

| | |
|---|---|
| 🧠 **Мультиагентная архитектура** | Планировщик, кодер, тестировщик, исследователь и файловый менеджер — всё координируется оркестратором |
| ⚙️ **15+ языков** | C, C++, Rust, Go, Python, Java, C#, Kotlin, Swift, Ruby, PHP, Dart, Elixir, Haskell, Lua |
| 🔁 **Самокорректирующийся цикл** | Пишет → компилирует → запускает → ловит `stderr` → исправляет → повторяет до чистого результата |
| ⏱ **Таймер рассуждения** | Видно, сколько времени агент думает перед ответом |
| 🌐 **Режим глубокого исследования** | Ищет в интернете, читает GitHub-репозитории и документацию, изучает теорию |
| 🎨 **Красивый TUI** | Двуязычная памятка (RU/EN), цветной вывод, подсветка синтаксиса |
| 🚀 **Одна команда** | Установил один раз — пишешь `codermuks` навсегда |
| 🔒 **Локально и приватно** | Твой код остаётся на устройстве; в Mistral уходят только промпты |

### 🚀 Быстрый старт

```bash
# 1. Клонируй репозиторий
git clone https://github.com/mixailneAI/Codermuks-in-termux.git
cd Codermuks-in-termux

# 2. Запусти установщик
bash install.sh

# 3. Вставь свой API-ключ Mistral
nano key.txt

# 4. Запусти
codermuks
```

> 💡 Получи **бесплатный API-ключ Mistral** → [console.mistral.ai/api-keys](https://console.mistral.ai/api-keys)

### 🎮 Использование

```bash
codermuks                                # интерактивный режим
codermuks "напиши HTTP-сервер на Go"     # сразу выполнить задачу
codermuks /research "изучи tokio async"  # режим глубокого исследования
```

Внутри сессии:

| Команда | Действие |
|---|---|
| `/research` | Включить глубокое исследование (web + GitHub) |
| `/reason` | Показать полную цепочку рассуждений |
| `/analyze` | Проанализировать существующий код |
| `/help` | Показать справку |
| `/exit` | Выйти из программы |

### 🏗 Как это работает

```
Запрос пользователя
    │
    ▼
┌─────────────────┐
│   Оркестратор   │  ← Mistral Large (планировщик)
└────────┬────────┘
         │  делегирует задачи
   ┌─────┴─────┬─────────┬──────────┐
   ▼           ▼         ▼          ▼
┌──────┐   ┌──────┐  ┌──────┐  ┌──────────┐
│Кодер │   │Тест-р│  │Иссле-│  │Файловый  │
│      │   │      │  │доват.│  │менеджер  │
└──┬───┘   └──┬───┘  └──┬───┘  └────┬─────┘
   │          │         │           │
   ▼          ▼         ▼           ▼
Codestral  Компил.   Web / GH    Чтение /
  пишет    и запуск   поиск      запись
    │          │
    └────┬─────┘
         ▼
   ошибка? → цикл фикса
         │
         ▼
   ✅ финал + таймер
```

### 📦 Требования

- **Termux** (Android 7.0+)
- **Python 3.11+**
- **API-ключ Mistral** ([есть бесплатный тариф](https://console.mistral.ai/api-keys))
- ~500 МБ свободного места (для компиляторов и рантаймов)

### 🛠 Ручная установка (для продвинутых)

```bash
pkg update && pkg upgrade -y
pkg install -y python clang rust golang openjdk-17 git
pip install mistralai rich requests pyfiglet

ln -sf "$PWD/codermuks" "$PREFIX/bin/codermuks"
chmod +x codermuks install.sh
```

### ❓ Частые вопросы

<details>
<summary><b>Это бесплатно?</b></summary>

Да — сам агент бесплатный и с открытым исходным кодом. Нужен только API-ключ Mistral, а у Mistral есть бесплатный тариф. При интенсивном использовании может понадобиться платный план Mistral.

</details>

<details>
<summary><b>Работает ли на обычном Linux?</b></summary>

Да, но установщик оптимизирован под Termux. На Linux установи зависимости через свой пакетный менеджер и запусти `python main.py`.

</details>

<details>
<summary><b>Можно ли использовать другого LLM-провайдера?</b></summary>

Пока нет, но поддержка Gemini, Groq, Cerebras и OpenAI-совместимых эндпоинтов запланирована.

</details>

<details>
<summary><b>Мой код отправляется в Mistral?</b></summary>

Только тот код, с которым агент активно работает, — как часть промпта. Твои файлы никогда не загружаются, если это не требуется для задачи.

</details>

### ⚖️ Дисклеймер

**Codermuks in Termux** — независимый проект с открытым исходным кодом. Он **не связан с OpenAI, Inc.**, не использует их торговые марки и **не является клоном продукта Codex**. Это самостоятельный AI-агент, работающий на моделях Mistral.

### 📜 Лицензия

Apache License 2.0 — подробности в файле [LICENSE](LICENSE).

---

<div align="center">

### 💚 Спасибо, что используешь Codermuks! · Thanks for using Codermuks!

**⭐ Поставь звезду, если проект помог · Star the repo if it helped**

**Made with ❤️ by [mixailneAI](https://github.com/mixailneAI)**

</div>
