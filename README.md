<div align="center">

<img src="assets/banner.png" alt="Codermuks in Termux — banner" width="800">

# 🤖 CODERMUKS IN TERMUX

### AI coding agent for Termux — 4 free providers, real projects, Roblox Studio via MCP

[![Version](https://img.shields.io/badge/version-1.4.0-brightgreen?style=for-the-badge)](https://github.com/mixailneAI/Codermuks-in-termux/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-Termux-orange?style=for-the-badge&logo=android&logoColor=white)](https://termux.dev)
[![CI](https://img.shields.io/github/actions/workflow/status/mixailneAI/Codermuks-in-termux/ci.yml?branch=main&style=for-the-badge)](https://github.com/mixailneAI/Codermuks-in-termux/actions)

**🌐 [English](#-english) · 🇷🇺 [Русский](#-русский)**

</div>

---

## 🆕 What's new in v1.4.0 · Что нового в v1.4.0

<table>
<tr>
<th>🇬🇧 English</th>
<th>🇷🇺 Русский</th>
</tr>
<tr>
<td>

**✨ Added**

- **Roblox Studio integration via MCP** — Codermuks connects to Roblox Studio through the Model Context Protocol
- **Remote MCP over HTTP** — control Roblox Studio on your PC from your phone via LAN or Tailscale
- **4 specialized Roblox subagents** — ScriptAgent, WorldAgent, TestAgent, FixAgent
- **Iterative workflow** — write → compile → test → fix (up to 3 iterations)
- **Real console reading** — reads actual errors from Studio, not from files
- **`/roblox <url>`** command — connect to remote MCP server
- **Auto-discovery** — finds local StudioMCP on Windows/macOS/Linux

**🔧 Changed**

- `_solve_roblox_files` removed — no more raw .luau files
- If MCP not found: explicitly asks for path/URL
- LivePanel pauses during user input

</td>
<td>

**✨ Добавлено**

- **Интеграция с Roblox Studio через MCP** — Codermuks подключается к Roblox Studio через Model Context Protocol
- **Удалённый MCP по HTTP** — управляй Roblox Studio на ПК с телефона через LAN или Tailscale
- **4 Roblox-субагента** — ScriptAgent, WorldAgent, TestAgent, FixAgent
- **Итеративный цикл** — пишет → компилирует → тестирует → исправляет (до 3 итераций)
- **Чтение консоли** — читает реальные ошибки из Studio, а не из файлов
- **`/roblox <url>`** — команда для подключения к удалённому MCP
- **Авто-обнаружение** — находит StudioMCP на Windows/macOS/Linux

**🔧 Изменено**

- `_solve_roblox_files` удалён — больше никаких сырых .luau-файлов
- Если MCP не найден: явно спрашивает путь/URL
- LivePanel замирает во время ввода пользователя

</td>
</tr>
</table>

### 📊 Version history · История версий

- **v1.4.0** — current · текущая: Roblox Studio via MCP, remote HTTP transport
- **v1.3.0** — smart library manager, project commands
- **v1.2.0** — real projects, history, live reasoning
- **v1.1.0** — multi-provider, i18n, tests
- **v1.0.1** — fixes: filenames, install.sh, symlink
- **v1.0.0** — initial release

[Compare v1.3.0 → v1.4.0](https://github.com/mixailneAI/Codermuks-in-termux/compare/v1.3.0...v1.4.0)

---

## 🌐 English

### What is Codermuks?

**Codermuks in Termux** is an autonomous AI coding agent that turns your Android terminal into a full development workspace. Describe a task — it writes code, compiles, runs, catches errors, fixes them in a loop, and delivers the final result only when everything works cleanly.

**What's new in v1.4.0:** Codermuks can now **control Roblox Studio** on your PC from your phone. It talks to Studio via **Model Context Protocol (MCP)** over HTTP. You get 4 specialized subagents that write Luau scripts, create parts, run playtests, and fix runtime errors — all in real time.

### 🎮 Roblox Studio integration

Codermuks becomes a **real MCP client** for Roblox Studio:

| Agent | Role | Tool |
|---|---|---|
| **ScriptAgent** | Writes and edits Luau scripts | `multi_edit`, `script_read` |
| **WorldAgent** | Creates parts, platforms, lighting | `insert_instance`, `execute_luau` |
| **TestAgent** | Runs playtest, reads console | `playtest_start`, `get_console_output` |
| **FixAgent** | Fixes runtime errors from console | `edit_script` |

**Iterative workflow:** Script → World → Test → Fix → repeat (up to 3 iterations).

### 📡 Connecting Roblox Studio (3 ways)

#### Way 1: Local (same machine as Termux)

If Roblox Studio is on the **same machine** as Codermuks:

1. Open Roblox Studio.
2. **Assistant → ⋯ → Manage MCP Servers → Enable Studio as MCP server**.
3. Copy the path Studio shows (e.g. `C:\Users\you\AppData\Local\Roblox\Versions\...\StudioMCP.exe`).
4. In Codermuks: run any Roblox task — it will ask for the path, paste it.

#### Way 2: Remote via LAN (phone + PC on same Wi-Fi)

**On PC:**

```bash
# Install Node.js first if you don't have it
npx -y @purplepiratepeep/rbx-mcp
```

This starts an MCP server on port 3030, listening on 0.0.0.0 (all network interfaces).

Install the plugin in Studio:

1. Download MCPPlugin.rbxmx from github.com/purplepiratepeep/rbx-mcp/releases.
2. Put it in:
   · Windows: %LOCALAPPDATA%\Roblox\Plugins\
   · macOS: ~/Documents/Roblox/Plugins/
3. Restart Studio.

Enable HTTP requests in Studio:

Open project → Game Settings → Security → Allow HTTP Requests ✅

Find PC's IP:

· Windows: ipconfig → look for IPv4 Address (e.g. 192.168.1.50)
· macOS: ifconfig | grep "inet " → look for 192.168.x.x

On phone (Termux):

```bash
codermuks
codermuks ▸ /roblox http://192.168.1.50:3030/mcp
✔ URL MCP-сервера сохранён: http://192.168.1.50:3030/mcp
codermuks ▸ напиши игру в роблокс — платформер
```

Now Codermuks writes directly into your Roblox Studio in real time.

Way 3: Remote via Tailscale (works from anywhere)

On PC:

1. Install Tailscale and log in.
2. Start MCP server: npx -y @purplepiratepeep/rbx-mcp
3. Expose to Tailnet:
   ```bash
   tailscale serve --bg 3030
   ```
4. Tailscale gives you a URL like https://my-pc.tailnet-xxx.ts.net.

On phone:

1. Install Tailscale, log in with the same account.
2. In Codermuks:
   ```
   codermuks ▸ /roblox https://my-pc.tailnet-xxx.ts.net/mcp
   ```

Now Codermuks controls Studio from anywhere.

🚀 Quick Start (non-Roblox)

```bash
git clone https://github.com/mixailneAI/Codermuks-in-termux.git
cd Codermuks-in-termux
bash install.sh
nano ~/.codermuks/key.txt    # insert at least one API key
codermuks
```

📖 Commands

Command What it does
/changeagent Change the team lead
/projects List your projects
/open <name> Open a project for editing
/delete <name> Delete a project
/export <name> Export project as ZIP
/deps <name> Show project dependencies
/run <name> Run a project
/history <name> Show project history
/roblox <url> Connect to remote Roblox MCP server
/roblox disconnect Forget the remote URL
/language Change interface language
/research Enable deep research
/reason Show reasoning chain
/analyze Analyze existing code
/langs List supported languages
/skills List available skills
/clear Clear the screen
/help Show help
/exit Exit

🤖 Meet the team (LLM providers)

Agent Role Free tier Works in RU
Mistral AI ⭐ Default leader · planning Free tier ✅
Qwen Code Code generation (qwen3-coder) 1000 req/day ✅
DeepSeek Universal model 5M tokens on signup ✅
OpenRouter Aggregator of free models 50 req/day ✅

📦 Requirements

· Termux (Android 7.0+)
· Python 3.11+
· At least one free API key (Mistral, Qwen, DeepSeek or OpenRouter)
· For Roblox: requests (installed by default)
· For Roblox remote: MCP server on PC (@purplepiratepeep/rbx-mcp)

⚖️ Disclaimer

Codermuks in Termux is an independent open-source project. Not affiliated with OpenAI, Inc. Not a clone of the Codex product.

📜 License

Apache License 2.0 — see LICENSE.

---

<br>
<br>

🇷🇺 Русский

Что такое Codermuks?

Codermuks in Termux — автономный AI-агент для программирования, который превращает Android-терминал в полноценную среду разработки. Ты описываешь задачу — он пишет код, компилирует, запускает, ловит ошибки, исправляет их в цикле и выдаёт финальный результат только тогда, когда всё работает без ошибок.

Что нового в v1.4.0: Codermuks теперь умеет управлять Roblox Studio на твоём ПК с телефона. Он говорит со Studio через Model Context Protocol (MCP) по HTTP. Работают 4 специализированных субагента — пишут Luau-скрипты, создают объекты, запускают плейтест и чинят runtime-ошибки. Всё в реальном времени.

🎮 Интеграция с Roblox Studio

Codermuks стал настоящим MCP-клиентом для Roblox Studio:

Агент Роль Инструменты
ScriptAgent Пишет и правит Luau-скрипты multi_edit, script_read
WorldAgent Создаёт детали, платформы, свет insert_instance, execute_luau
TestAgent Запускает плейтест, читает консоль playtest_start, get_console_output
FixAgent Исправляет runtime-ошибки edit_script

Итеративный цикл: Script → World → Test → Fix → повтор (до 3 итераций).

📡 Подключение Roblox Studio (3 способа)

Способ 1: Локально (Studio на том же устройстве, что и Codermuks)

1. Открой Roblox Studio.
2. Assistant → ⋯ → Manage MCP Servers → Enable Studio as MCP server.
3. Скопируй путь, который показывает Studio (например C:\Users\you\AppData\Local\Roblox\Versions\...\StudioMCP.exe).
4. В Codermuks запусти любую Roblox-задачу — он спросит путь, вставь его.

Способ 2: Удалённо по LAN (телефон и ПК в одной Wi-Fi)

На ПК:

```bash
# Установи Node.js, если ещё нет
npx -y @purplepiratepeep/rbx-mcp
```

Запустится MCP-сервер на порту 3030, слушающий 0.0.0.0 (все сетевые интерфейсы).

Установи плагин в Studio:

1. Скачай MCPPlugin.rbxmx из github.com/purplepiratepeep/rbx-mcp/releases.
2. Положи в:
   · Windows: %LOCALAPPDATA%\Roblox\Plugins\
   · macOS: ~/Documents/Roblox/Plugins/
3. Перезапусти Studio.

Включи HTTP в Studio:

Открой проект → Game Settings → Security → Allow HTTP Requests ✅

Узнай IP ПК:

· Windows: ipconfig → ищи IPv4 Address (например 192.168.1.50)
· macOS: ifconfig | grep "inet " → ищи 192.168.x.x

На телефоне (Termux):

```bash
codermuks
codermuks ▸ /roblox http://192.168.1.50:3030/mcp
✔ URL MCP-сервера сохранён: http://192.168.1.50:3030/mcp
codermuks ▸ напиши игру в роблокс — платформер
```

Codermuks пишет прямо в твой Studio в реальном времени.

Способ 3: Удалённо через Tailscale (работает откуда угодно)

На ПК:

1. Установи Tailscale, войди.
2. Запусти MCP-сервер: npx -y @purplepiratepeep/rbx-mcp
3. Открой доступ в Tailnet:
   ```bash
   tailscale serve --bg 3030
   ```
4. Tailscale даст URL вида https://my-pc.tailnet-xxx.ts.net.

На телефоне:

1. Установи Tailscale, войди в тот же аккаунт.
2. В Codermuks:
   ```
   codermuks ▸ /roblox https://my-pc.tailnet-xxx.ts.net/mcp
   ```

Теперь Codermuks управляет Studio из любой точки мира.

🚀 Быстрый старт (не Roblox)

```bash
git clone https://github.com/mixailneAI/Codermuks-in-termux.git
cd Codermuks-in-termux
bash install.sh
nano ~/.codermuks/key.txt    # вставь хотя бы один API-ключ
codermuks
```

📖 Команды

Команда Что делает
/changeagent Сменить главного агента
/projects Список проектов
/open <имя> Открыть проект
/delete <имя> Удалить проект
/export <имя> Экспорт в ZIP
/deps <имя> Зависимости проекта
/run <имя> Запустить проект
/history <имя> История проекта
/roblox <url> Подключиться к удалённому Roblox MCP
/roblox disconnect Забыть URL
/language Сменить язык интерфейса
/research Включить deep research
/reason Показать цепочку рассуждений
/analyze Анализ кода
/langs Список языков
/skills Список скиллов
/clear Очистить экран
/help Справка
/exit Выход

🤖 Команда агентов (LLM-провайдеры)

Агент Роль Бесплатно Работает в РФ
Mistral AI ⭐ Главный · планирование Free tier ✅
Qwen Code Генерация кода 1000 запросов/день ✅
DeepSeek Универсальная модель 5M токенов при регистрации ✅
OpenRouter Агрегатор free-моделей 50 запросов/день ✅

📦 Требования

· Termux (Android 7.0+)
· Python 3.11+
· Хотя бы один бесплатный API-ключ (Mistral, Qwen, DeepSeek или OpenRouter)
· Для Roblox: requests (ставится автоматически)
· Для Roblox удалённо: MCP-сервер на ПК (@purplepiratepeep/rbx-mcp)

❓ Частые вопросы

<details>
<summary><b>Roblox Studio на ПК, Codermuks на телефоне — это сработает?</b></summary>

Да, двумя способами:

1. LAN (Wi-Fi): запусти MCP-сервер на ПК, подключись по IP из телефона через /roblox http://<IP>:3030/mcp.
2. Tailscale: создай туннель на ПК, подключись через https://...ts.net/mcp.

Подробности — в разделе «Подключение Roblox Studio».

</details>

<details>
<summary><b>MCP-сервер на ПК — какой использовать?</b></summary>

Рекомендую @purplepiratepeep/rbx-mcp — он сразу слушает 0.0.0.0 (готов к LAN) и поддерживает HTTP/SSE.

Альтернатива: Chrrxs/robloxstudio-mcp — нужно явно задать ROBLOX_STUDIO_HOST=0.0.0.0.

Официальный StudioMCP от Roblox слушает только 127.0.0.1, поэтому для удалённого подключения не подходит.

</details>

<details>
<summary><b>Что делать, если Roblox Studio не находится?</b></summary>

Codermuks спросит путь или URL. Если Studio на ПК:

· Введи http://<IP>:3030/mcp — для LAN.
· Введи https://...ts.net/mcp — для Tailscale.
· Введи путь к StudioMCP — если Studio на том же устройстве.

</details>

<details>
<summary><b>Где хранятся мои API-ключи?</b></summary>

В ~/.codermuks/key.txt на твоём устройстве. Не уходят никуда, кроме самого провайдера.

</details>

<details>
<summary><b>Можно добавить своего LLM-провайдера?</b></summary>

Да. Создай наследника OpenAICompatibleProvider в core/llm_providers/ и зарегистрируй в core/llm_providers/__init__.py.

</details>

⚖️ Дисклеймер

Codermuks in Termux — независимый проект с открытым исходным кодом. Не связан с OpenAI, Inc. Не является клоном продукта Codex.

📜 Лицензия

Apache License 2.0 — подробности в LICENSE.

---

<div align="center">

<img src="assets/logo.png" alt="Codermuks logo" width="120">

💚 Спасибо, что используешь Codermuks! · Thanks for using Codermuks!

⭐ Поставь звезду, если помог · Star the repo if it helped

Made with ❤️ by mixailneAI

</div>
