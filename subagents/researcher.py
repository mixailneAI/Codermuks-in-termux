# =============================================================================
#  Codermuks in Termux — субагент-исследователь
# =============================================================================
#  Задача исследователя — собрать контекст из внешних источников:
#    • поиск в интернете по теме задачи;
#    • чтение GitHub-репозиториев (README, файлы кода);
#    • чтение документации по URL;
#    • обобщение найденного через модель Mistral Large.
#
#  Включается только в режиме deep_research, потому что каждый шаг —
#  это дополнительный сетевой запрос и расход токенов.
# =============================================================================

from __future__ import annotations

from typing import Any

from core.mistral_client import get_client
from prompts.templates import SYSTEM_RESEARCHER
from subagents.base import BaseSubagent


# =============================================================================
#  СУБАГЕНТ
# =============================================================================

class ResearcherSubagent(BaseSubagent):
    """Субагент, который собирает и обобщает информацию из интернета."""

    name = "researcher"
    description = "Ищет информацию в интернете, читает GitHub и документацию."

    # -------------------------------------------------------------------------
    #  Публичный интерфейс
    # -------------------------------------------------------------------------

    def run(self, task: str, **kwargs: Any) -> str:
        """
        Собирает контекст по задаче.

        Аргументы:
            task — запрос пользователя (например, "напиши сервер на Go с gin")

        Возвращает:
            Строку с обобщённым контекстом — то, что пойдёт кодеру как
            дополнительный материал. Формат свободный, но обычно это:
              • краткое резюме темы;
              • ключевые ссылки;
              • примеры кода (если найдены);
              • подводные камни и рекомендации.
        """
        # Импортируем web-инструменты здесь, чтобы не создавать
        # циклическую зависимость на уровне модуля.
        from tools.web import web_search, fetch_github, read_docs

        # Формируем поисковый запрос. Если пользователь задал его явно
        # через kwargs — используем его, иначе — саму задачу.
        search_query = kwargs.get("search_query", task).strip()

        # Ограничение на количество источников — чтобы не растягивать
        # ответ и не жечь токены.
        max_results = int(kwargs.get("max_results", 3))

        # Копилка собранных материалов.
        collected: list[str] = []

        # --- Шаг 1: поиск в интернете ---------------------------------------
        self.log(f"Ищу в интернете: {search_query[:80]}...")
        try:
            search_results = web_search(search_query, max_results=max_results)
        except Exception as exc:
            self.log(f"Поиск не удался: {exc}")
            search_results = []

        if search_results:
            self.log(f"Найдено результатов: {len(search_results)}")
            for idx, item in enumerate(search_results, start=1):
                title = item.get("title", "Без названия")
                url = item.get("url", "")
                snippet = item.get("snippet", "")
                collected.append(
                    f"[Источник {idx}] {title}\nURL: {url}\n{snippet}"
                )
        else:
            self.log("Поиск не вернул результатов.")

        # --- Шаг 2: GitHub (если в запросе есть репозиторий) ----------------
        github_url = self._detect_github_url(task)
        if github_url:
            self.log(f"Читаю GitHub: {github_url}")
            try:
                gh_content = fetch_github(github_url)
                if gh_content:
                    collected.append(
                        f"[GitHub] {github_url}\n{gh_content[:4000]}"
                    )
                    self.log(f"Получено с GitHub: {len(gh_content)} символов.")
            except Exception as exc:
                self.log(f"Не удалось прочитать GitHub: {exc}")

        # --- Шаг 3: чтение документации по URL -----------------------------
        docs_url = self._detect_docs_url(task)
        if docs_url and docs_url != github_url:
            self.log(f"Читаю документацию: {docs_url}")
            try:
                docs_content = read_docs(docs_url)
                if docs_content:
                    collected.append(
                        f"[Документация] {docs_url}\n{docs_content[:4000]}"
                    )
                    self.log(f"Получено из документации: {len(docs_content)} символов.")
            except Exception as exc:
                self.log(f"Не удалось прочитать документацию: {exc}")

        # --- Шаг 4: обобщение через Mistral Large --------------------------
        if not collected:
            self.log("Внешних источников нет — возвращаю пустой контекст.")
            return ""

        joined = "\n\n---\n\n".join(collected)
        self.log(f"Обобщаю {len(joined)} символов через Mistral Large.")

        summary = self._summarize(task, joined)
        return summary

    # -------------------------------------------------------------------------
    #  Вспомогательные методы
    # -------------------------------------------------------------------------

    def _summarize(self, task: str, materials: str) -> str:
        """
        Обобщает собранные материалы через Mistral Large.

        Возвращает связный текст-контекст для кодера. Если модель
        недоступна или ответ пустой — возвращает исходные материалы
        как есть, чтобы контекст не потерялся.
        """
        client = get_client()

        prompt = (
            f"Задача пользователя:\n{task}\n\n"
            f"Собранные материалы:\n{materials}\n\n"
            f"Сделай краткое резюме по этим материалам. Выдели:\n"
            f"  1. Ключевые факты по теме.\n"
            f"  2. Рекомендуемые библиотеки и подходы.\n"
            f"  3. Подводные камни и типичные ошибки.\n"
            f"  4. Примеры кода, если они есть в источниках.\n"
            f"Пиши сжато, без воды. Только то, что пригодится при написании кода."
        )

        try:
            summary = client.research(SYSTEM_RESEARCHER, prompt)
            if summary and summary.strip():
                return summary.strip()
        except Exception as exc:
            self.log(f"Обобщение не удалось: {exc}")

        # Фолбэк — отдаём сырые материалы.
        return materials

    def _detect_github_url(self, text: str) -> str:
        """
        Ищет URL GitHub-репозитория в тексте задачи.

        Возвращает нормализованный URL вида https://github.com/owner/repo
        или пустую строку, если репозиторий не упомянут.
        """
        import re

        # Ищем что-то вроде github.com/owner/repo или полный URL.
        pattern = re.compile(
            r"(?:https?://)?github\.com/([A-Za-z0-9_.\-]+)/([A-Za-z0-9_.\-]+)"
        )
        match = pattern.search(text)
        if not match:
            return ""

        owner, repo = match.group(1), match.group(2)
        # Отбрасываем лишние суффиксы вроде .git.
        if repo.endswith(".git"):
            repo = repo[:-4]
        return f"https://github.com/{owner}/{repo}"

    def _detect_docs_url(self, text: str) -> str:
        """
        Ищет URL документации (docs.*, документация по библиотеке).

        Возвращает первый найденный URL или пустую строку.
        """
        import re

        # Любой http(s)-URL в тексте.
        pattern = re.compile(r"https?://[^\s\)\]\>,]+")
        for match in pattern.finditer(text):
            url = match.group(0)
            # Пропускаем GitHub — его обрабатывает отдельный шаг.
            if "github.com" in url:
                continue
            return url
        return ""