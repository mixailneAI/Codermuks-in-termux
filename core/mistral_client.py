# =============================================================================
#  Codermuks in Termux — клиент Mistral API
# =============================================================================
#  Единая точка взаимодействия с моделями Mistral. Все остальные модули
#  (агент, субагенты, инструменты) ходят в Mistral только через этот файл.
#
#  Что здесь есть:
#    • ленивая инициализация клиента (ключ читается один раз);
#    • chat()          — обычный синхронный запрос;
#    • chat_stream()   — потоковый запрос (для будущего посимвольного вывода);
#    • plan()          — запрос к модели-планировщику;
#    • code()          — запрос к Codestral;
#    • retry-логика    — повтор при сетевых ошибках с экспоненциальной задержкой;
#    • обработка ошибок Mistral API в человеко-читаемом виде.
# =============================================================================

from __future__ import annotations

import time
from typing import Any, Iterator

from mistralai import Mistral
from mistralai.models import SDKError

from core import config


# =============================================================================
#  ИСКЛЮЧЕНИЯ
# =============================================================================

class MistralClientError(Exception):
    """Базовая ошибка клиента Mistral."""
    pass


class MistralAuthError(MistralClientError):
    """Ошибка аутентификации: неправильный или просроченный API-ключ."""
    pass


class MistralRateLimitError(MistralClientError):
    """Превышен лимит запросов к Mistral API."""
    pass


class MistralServerError(MistralClientError):
    """Сервер Mistral вернул 5xx — временная проблема на их стороне."""
    pass


class MistralNetworkError(MistralClientError):
    """Сетевая ошибка: нет соединения, таймаут, DNS."""
    pass


# =============================================================================
#  КЛИЕНТ
# =============================================================================

class MistralClient:
    """
    Обёртка над официальным SDK Mistral.

    Ленивая инициализация: реальный клиент создаётся при первом запросе,
    чтобы импорт модуля не падал, если ключа ещё нет (например, при
    запуске справки или установщика).
    """

    def __init__(self) -> None:
        # Внутренний объект SDK. Создаётся при первом обращении.
        self._client: Mistral | None = None
        # Кэш ключа и базового URL — читаем один раз.
        self._api_key: str | None = None
        self._base_url: str | None = None

    # -------------------------------------------------------------------------
    #  Внутренние методы
    # -------------------------------------------------------------------------

    def _ensure_client(self) -> Mistral:
        """
        Создаёт клиент Mistral при первом обращении.

        Читает ключ из ~/.codermuks/key.txt (через config.get_api_key).
        Кэширует клиент, чтобы не создавать его на каждый запрос.
        """
        if self._client is not None:
            return self._client

        # Читаем ключ. Если файла нет — config поднимет понятную ошибку.
        self._api_key = config.get_api_key()
        self._base_url = config.get_base_url()

        self._client = Mistral(
            api_key=self._api_key,
            server_url=self._base_url,
        )
        return self._client

    def _classify_error(self, exc: Exception) -> MistralClientError:
        """
        Превращает исключение SDK в понятную ошибку нашего типа.

        Это нужно, чтобы вызывающий код мог реагировать по-разному:
        например, при rate limit подождать, а при auth error — сразу
        сообщить пользователю.
        """
        text = str(exc).lower()

        # 401 / 403 — неверный ключ.
        if "401" in text or "403" in text or "unauthorized" in text or "invalid api key" in text:
            return MistralAuthError(
                "Неверный API-ключ Mistral. Проверь содержимое ~/.codermuks/key.txt "
                "и получи новый на https://console.mistral.ai/api-keys"
            )

        # 429 — превышен лимит.
        if "429" in text or "rate limit" in text or "too many requests" in text:
            return MistralRateLimitError(
                "Превышен лимит запросов к Mistral. Подожди немного и повтори."
            )

        # 5xx — сервер Mistral.
        if any(code in text for code in ("500", "502", "503", "504")):
            return MistralServerError(
                "Сервер Mistral временно недоступен. Попробуй позже."
            )

        # Сетевые проблемы.
        if any(word in text for word in ("timeout", "connection", "network", "dns", "unreachable")):
            return MistralNetworkError(
                "Не удалось связаться с Mistral. Проверь интернет и повтори."
            )

        # Всё остальное — общая ошибка.
        return MistralClientError(f"Ошибка Mistral API: {exc}")

    def _call_with_retry(self, func, *args, **kwargs) -> Any:
        """
        Вызывает функцию SDK с повторными попытками при временных ошибках.

        Повторяем только при сетевых ошибках и 5xx/429. При auth-ошибке
        повторять бессмысленно — сразу выбрасываем.
        """
        last_error: MistralClientError | None = None

        for attempt in range(config.API_MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except SDKError as exc:
                last_error = self._classify_error(exc)

                # Auth-ошибку нет смысла повторять.
                if isinstance(last_error, MistralAuthError):
                    raise last_error

                # На последней попытке — выбрасываем.
                if attempt == config.API_MAX_RETRIES - 1:
                    raise last_error

                # Экспоненциальный backoff: 1.5, 3, 6 секунд.
                delay = config.API_RETRY_BACKOFF * (2 ** attempt)
                time.sleep(delay)
            except Exception as exc:
                last_error = self._classify_error(exc)

                if attempt == config.API_MAX_RETRIES - 1:
                    raise last_error

                delay = config.API_RETRY_BACKOFF * (2 ** attempt)
                time.sleep(delay)

        # Сюда не дойдём, но на всякий случай.
        raise last_error or MistralClientError("Неизвестная ошибка Mistral")

    # -------------------------------------------------------------------------
    #  Публичные методы
    # -------------------------------------------------------------------------

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """
        Отправляет запрос в Mistral и возвращает текст ответа.

        Аргументы:
            messages    — список сообщений формата [{"role": "user", "content": "..."}]
            model       — имя модели (по умолчанию FAST_MODEL)
            temperature — температура генерации (по умолчанию из config)
            max_tokens  — лимит токенов в ответе

        Возвращает:
            Строку с текстом ответа ассистента.
        """
        client = self._ensure_client()

        # Подставляем значения по умолчанию.
        chosen_model = model or config.FAST_MODEL
        chosen_temp = temperature if temperature is not None else config.TEMPERATURE_PLANNING
        chosen_max = max_tokens or config.MAX_TOKENS

        response = self._call_with_retry(
            client.chat.complete,
            model=chosen_model,
            messages=messages,
            temperature=chosen_temp,
            max_tokens=chosen_max,
            top_p=config.TOP_P,
        )

        # Достаём текст из ответа.
        if not response or not response.choices:
            raise MistralClientError("Mistral вернул пустой ответ.")

        content = response.choices[0].message.content
        if content is None:
            raise MistralClientError("Mistral вернул ответ без содержимого.")

        # content может быть строкой или списком блоков — приводим к строке.
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in content)
        return str(content)

    def chat_stream(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> Iterator[str]:
        """
        Отправляет запрос в Mistral в потоковом режиме.

        Возвращает итератор по кусочкам текста — по мере их поступления.
        Полезно, если хочется показывать ответ «на лету».
        """
        client = self._ensure_client()

        chosen_model = model or config.FAST_MODEL
        chosen_temp = temperature if temperature is not None else config.TEMPERATURE_PLANNING
        chosen_max = max_tokens or config.MAX_TOKENS

        try:
            stream = client.chat.stream(
                model=chosen_model,
                messages=messages,
                temperature=chosen_temp,
                max_tokens=chosen_max,
                top_p=config.TOP_P,
            )
        except SDKError as exc:
            raise self._classify_error(exc)

        for chunk in stream:
            try:
                delta = chunk.data.choices[0].delta.content
            except (AttributeError, IndexError):
                continue
            if not delta:
                continue
            if isinstance(delta, str):
                yield delta
            elif isinstance(delta, list):
                for part in delta:
                    if isinstance(part, dict) and part.get("text"):
                        yield part["text"]

    # -------------------------------------------------------------------------
    #  Специализированные методы
    # -------------------------------------------------------------------------

    def plan(self, system_prompt: str, user_query: str) -> str:
        """
        Запрос к модели-планировщику.

        Используется оркестратором для декомпозиции задачи. Модель
        получает системный промпт и запрос пользователя, возвращает
        структурированный план.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query},
        ]
        return self.chat(
            messages=messages,
            model=config.PLANNER_MODEL,
            temperature=config.TEMPERATURE_PLANNING,
        )

    def code(self, system_prompt: str, user_query: str) -> str:
        """
        Запрос к Codestral.

        Используется субагентом-кодером для генерации и фикса кода.
        Низкая температура — чтобы результат был предсказуемым.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query},
        ]
        return self.chat(
            messages=messages,
            model=config.CODING_MODEL,
            temperature=config.TEMPERATURE_CODING,
        )

    def research(self, system_prompt: str, user_query: str) -> str:
        """
        Запрос к модели-исследователю.

        Используется в режиме deep_research, когда нужно осмыслить
        материалы из интернета или GitHub.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query},
        ]
        return self.chat(
            messages=messages,
            model=config.RESEARCH_MODEL,
            temperature=config.TEMPERATURE_RESEARCH,
        )


# =============================================================================
#  ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР
# =============================================================================

# Один клиент на всё приложение. Клиент ленивый — реально подключается
# только при первом запросе.
_client_instance: MistralClient | None = None


def get_client() -> MistralClient:
    """
    Возвращает глобальный экземпляр клиента Mistral.

    Все модули должны использовать именно эту функцию, чтобы не
    создавать по нескольку клиентов.
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = MistralClient()
    return _client_instance