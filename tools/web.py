# =============================================================================
#  Codermuks in Termux — веб-инструменты
# =============================================================================
#  Модуль собирает информацию из внешних источников:
#    • web_search(query)   — поиск в интернете через публичный API;
#    • fetch_github(url)   — чтение README и файлов GitHub-репозитория;
#    • read_docs(url)      — чтение текста страницы документации.
#
#  Используется субагентом-исследователем в режиме deep_research.
#  Все функции устойчивы к сетевым сбоям: возвращают пустой результат
#  вместо выброса исключения, чтобы не валить основную задачу агента.
# =============================================================================

from __future__ import annotations

import json
import re
import urllib.parse
from typing import Any

import requests


# =============================================================================
#  НАСТРОЙКИ СЕТИ
# =============================================================================

# Таймаут одного HTTP-запроса в секундах. Небольшой, чтобы агент
# не висел, если сайт недоступен.
HTTP_TIMEOUT: int = 15

# Стандартный User-Agent. Некоторые сайты блокируют запросы без него.
USER_AGENT: str = (
    "Mozilla/5.0 (Linux; Android 12; Termux) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0 Mobile Safari/537.36 Codermuks/1.0"
)

# Базовые заголовки для всех запросов.
DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/json,text/plain,*/*",
    "Accept-Language": "ru,en;q=0.9",
}


# =============================================================================
#  ВЕБ-ПОИСК
# =============================================================================

def web_search(query: str, max_results: int = 3) -> list[dict[str, str]]:
    """
    Ищет информацию в интернете через DuckDuckGo HTML-эндпоинт.

    DuckDuckGo выбран потому, что не требует API-ключа и работает
    из Termux без регистрации.

    Аргументы:
        query       — поисковый запрос
        max_results — сколько результатов вернуть (по умолчанию 3)

    Возвращает список словарей:
        [
            {"title": "...", "url": "...", "snippet": "..."},
            ...
        ]

    При любой сетевой ошибке возвращает пустой список — вызывающий
    код сам решает, что делать дальше.
    """
    if not query or not query.strip():
        return []

    # Ограничиваем длину запроса — поисковики плохо реагируют на простыни.
    clean_query = query.strip()[:300]

    try:
        response = requests.post(
            "https://html.duckduckgo.com/html/",
            data={"q": clean_query},
            headers=DEFAULT_HEADERS,
            timeout=HTTP_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException:
        return []

    return _parse_duckduckgo_html(response.text, max_results)


def _parse_duckduckgo_html(html: str, max_results: int) -> list[dict[str, str]]:
    """
    Извлекает результаты поиска из HTML-страницы DuckDuckGo.

    Работает регулярками — без BeautifulSoup, чтобы не тянуть лишнюю
    зависимость в Termux. Формат HTML у DuckDuckGo стабильный уже
    много лет, парсер переживает небольшие изменения разметки.
    """
    results: list[dict[str, str]] = []

    # Каждый результат обёрнут в блок с классом "result__body" или похожим.
    # Ищем ссылки, заголовки и сниппеты отдельными регулярками.
    link_pattern = re.compile(
        r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
        re.DOTALL,
    )
    snippet_pattern = re.compile(
        r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
        re.DOTALL,
    )

    links = link_pattern.findall(html)
    snippets = snippet_pattern.findall(html)

    for idx, (raw_url, raw_title) in enumerate(links):
        if len(results) >= max_results:
            break

        url = _clean_duckduckgo_url(raw_url)
        title = _strip_html(raw_title)
        snippet = ""

        if idx < len(snippets):
            snippet = _strip_html(snippets[idx])

        if not url or not title:
            continue

        results.append({
            "title": title,
            "url": url,
            "snippet": snippet[:500],
        })

    return results


def _clean_duckduckgo_url(raw: str) -> str:
    """
    Убирает редирект-обёртку DuckDuckGo из URL.

    DuckDuckGo отдаёт ссылки вида:
        //duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com&rut=...
    Нам нужен чистый URL из параметра uddg.
    """
    if not raw:
        return ""

    # Если URL относительный — добавляем схему.
    if raw.startswith("//"):
        raw = "https:" + raw

    # Извлекаем параметр uddg, если он есть.
    if "uddg=" in raw:
        parsed = urllib.parse.urlparse(raw)
        params = urllib.parse.parse_qs(parsed.query)
        if "uddg" in params and params["uddg"]:
            return params["uddg"][0]

    return raw


def _strip_html(text: str) -> str:
    """
    Убирает HTML-теги и декодирует HTML-сущности из строки.

    Простой парсер без зависимостей: удаляем всё между < и >,
    затем раскрываем основные сущности.
    """
    if not text:
        return ""

    # Убираем теги.
    no_tags = re.sub(r"<[^>]+>", "", text)

    # Декодируем HTML-сущности.
    entities = {
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&quot;": '"',
        "&#39;": "'",
        "&nbsp;": " ",
        "&hellip;": "…",
        "&mdash;": "—",
        "&ndash;": "–",
    }
    for entity, char in entities.items():
        no_tags = no_tags.replace(entity, char)

    # Сжимаем пробелы.
    return re.sub(r"\s+", " ", no_tags).strip()


# =============================================================================
#  ЧТЕНИЕ GITHUB
# =============================================================================

def fetch_github(url: str) -> str:
    """
    Читает README и основные файлы GitHub-репозитория.

    Аргументы:
        url — ссылка вида https://github.com/owner/repo

    Возвращает текст README (или другого файла) в виде строки.
    При ошибке возвращает пустую строку.
    """
    if not url:
        return ""

    # Разбираем owner и repo из URL.
    parsed = _parse_github_url(url)
    if parsed is None:
        return ""

    owner, repo = parsed

    # Пробуем несколько веток и несколько имён README по очереди.
    # Порядок важен: сначала main, потом master — это самые частые варианты.
    branches = ["main", "master"]
    readme_names = ["README.md", "README.rst", "README.txt", "readme.md"]

    for branch in branches:
        for readme in readme_names:
            content = _fetch_raw_github_file(owner, repo, branch, readme)
            if content:
                # Ограничиваем размер — README бывают огромными.
                return content[:6000]

    # README не нашли — попробуем прочитать описание репозитория через API.
    description = _fetch_github_description(owner, repo)
    if description:
        return description

    return ""


def _parse_github_url(url: str) -> tuple[str, str] | None:
    """
    Извлекает owner и repo из ссылки GitHub.

    Понимает форматы:
        https://github.com/owner/repo
        github.com/owner/repo
        https://github.com/owner/repo/tree/main
        https://github.com/owner/repo.git
    """
    pattern = re.compile(
        r"(?:https?://)?github\.com/([A-Za-z0-9_.\-]+)/([A-Za-z0-9_.\-]+)"
    )
    match = pattern.search(url)
    if not match:
        return None

    owner = match.group(1)
    repo = match.group(2)
    if repo.endswith(".git"):
        repo = repo[:-4]
    return owner, repo


def _fetch_raw_github_file(
    owner: str,
    repo: str,
    branch: str,
    filename: str,
) -> str:
    """
    Скачивает один файл из репозитория через raw.githubusercontent.com.

    Возвращает содержимое или пустую строку, если файла нет.
    """
    raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{filename}"

    try:
        response = requests.get(
            raw_url,
            headers=DEFAULT_HEADERS,
            timeout=HTTP_TIMEOUT,
        )
        if response.status_code != 200:
            return ""
        return response.text
    except requests.RequestException:
        return ""


def _fetch_github_description(owner: str, repo: str) -> str:
    """
    Получает описание репозитория через публичный GitHub API.

    Используется, если README не найден. Не требует авторизации,
    но имеет лимит в 60 запросов в час — этого более чем достаточно.
    """
    api_url = f"https://api.github.com/repos/{owner}/{repo}"

    try:
        response = requests.get(
            api_url,
            headers={**DEFAULT_HEADERS, "Accept": "application/vnd.github+json"},
            timeout=HTTP_TIMEOUT,
        )
        if response.status_code != 200:
            return ""

        data = response.json()
        parts: list[str] = []

        if data.get("description"):
            parts.append(f"Описание: {data['description']}")
        if data.get("language"):
            parts.append(f"Основной язык: {data['language']}")
        if data.get("topics"):
            parts.append(f"Темы: {', '.join(data['topics'])}")
        if data.get("stargazers_count") is not None:
            parts.append(f"Звёзд: {data['stargazers_count']}")

        return "\n".join(parts)
    except (requests.RequestException, json.JSONDecodeError):
        return ""


# =============================================================================
#  ЧТЕНИЕ ДОКУМЕНТАЦИИ
# =============================================================================

def read_docs(url: str) -> str:
    """
    Читает текст веб-страницы (обычно документации).

    Аргументы:
        url — ссылка на страницу

    Возвращает очищенный текст без HTML-тегов, скриптов и стилей.
    При ошибке возвращает пустую строку.
    """
    if not url:
        return ""

    try:
        response = requests.get(
            url,
            headers=DEFAULT_HEADERS,
            timeout=HTTP_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException:
        return ""

    # Проверяем, что это HTML, а не бинарник или JSON.
    content_type = response.headers.get("Content-Type", "").lower()
    if "html" not in content_type and "text" not in content_type:
        return ""

    return _extract_text_from_html(response.text)[:8000]


def _extract_text_from_html(html: str) -> str:
    """
    Извлекает читаемый текст из HTML-страницы.

    Алгоритм:
        1. Убираем <script>, <style>, <noscript>, <svg>, <nav>, <footer>.
        2. Убираем все остальные теги.
        3. Декодируем HTML-сущности.
        4. Сжимаем пустые строки и пробелы.
    """
    if not html:
        return ""

    text = html

    # Убираем целиком ненужные блоки.
    for tag in ("script", "style", "noscript", "svg", "nav", "footer", "header"):
        text = re.sub(
            rf"<{tag}\b[^>]*>.*?</{tag}>",
            " ",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )

    # Убираем HTML-комментарии.
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)

    # Убираем оставшиеся теги.
    text = re.sub(r"<[^>]+>", " ", text)

    # Декодируем сущности.
    text = _strip_html(text)

    # Разбиваем на строки, убираем пустые.
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if len(line) > 2]

    return "\n".join(lines)


# =============================================================================
#  УТИЛИТЫ ДЛЯ ОТЛАДКИ
# =============================================================================

def is_online(timeout: int = 5) -> bool:
    """
    Проверяет, есть ли у устройства доступ в интернет.

    Делает лёгкий запрос к публичному DNS-резолверу. Используется
    CLI, чтобы заранее предупредить пользователя, если сети нет.
    """
    try:
        response = requests.get(
            "https://api.mistral.ai/",
            timeout=timeout,
        )
        # Нас интересует сам факт ответа — код может быть любым.
        return response.status_code < 500
    except requests.RequestException:
        return False


def fetch_url_json(url: str) -> Any:
    """
    Скачивает JSON по URL и возвращает распарсенный объект.

    Полезно для работы с публичными API (GitHub, npm, PyPI).
    При ошибке возвращает None.
    """
    if not url:
        return None

    try:
        response = requests.get(
            url,
            headers={**DEFAULT_HEADERS, "Accept": "application/json"},
            timeout=HTTP_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, json.JSONDecodeError):
        return None