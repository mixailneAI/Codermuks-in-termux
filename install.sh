#!/data/data/com.termux/files/usr/bin/bash
# =============================================================================
#  Codermuks in Termux — установщик v1.1.0
# =============================================================================
#  Что делает этот скрипт:
#    1. Проверяет, что мы в Termux.
#    2. Обновляет пакеты Termux.
#    3. Ставит системные зависимости по одной (clang, rust, golang и др.).
#    4. Ставит Python-библиотеки с обходом карантина PyPI.
#    5. Создаёт ~/.codermuks/ и config.json с настройками по умолчанию.
#    6. Создаёт key.txt с JSON-структурой для 4 провайдеров.
#    7. Создаёт симлинк codermuks в $PREFIX/bin.
#    8. Проверяет, что всё установлено.
#
#  При первом запуске codermuks спросит язык интерфейса (EN/RU).
#
#  Запуск:  bash install.sh
# =============================================================================

set -e

# --- Цвета -----------------------------------------------------------------
GREEN="\033[1;32m"
RED="\033[1;31m"
YELLOW="\033[1;33m"
BLUE="\033[1;34m"
CYAN="\033[1;36m"
RESET="\033[0m"

log_info()    { echo -e "${BLUE}[•]${RESET} $1"; }
log_success() { echo -e "${GREEN}[✔]${RESET} $1"; }
log_warn()    { echo -e "${YELLOW}[!]${RESET} $1"; }
log_error()   { echo -e "${RED}[✘]${RESET} $1"; }

# --- Баннер ----------------------------------------------------------------
echo ""
echo -e "${GREEN}"
echo "  ██████╗ ██████╗ ██████╗ ███████╗██████╗ ███╗   ███╗██╗   ██╗██╗  ██╗███████╗"
echo " ██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔══██╗████╗ ████║██║   ██║██║ ██╔╝██╔════╝"
echo " ██║     ██║   ██║██║  ██║█████╗  ██████╔╝██╔████╔██║██║   ██║█████╔╝ ███████╗"
echo " ██║     ██║   ██║██║  ██║██╔══╝  ██╔══██╗██║╚██╔╝██║██║   ██║██╔═██╗ ╚════██║"
echo " ╚██████╗╚██████╔╝██████╔╝███████╗██║  ██║██║ ╚═╝ ██║╚██████╔╝██║  ██╗███████║"
echo "  ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝"
echo "                         ▸  I N   T E R M U X  ◂"
echo -e "${RESET}"
echo -e "${CYAN}Установщик Codermuks in Termux v1.1.0${RESET}"
echo ""

# --- Проверка Termux -------------------------------------------------------
if [ -z "$PREFIX" ] || [ ! -d "$PREFIX" ]; then
    log_error "Скрипт запущен вне Termux. Установка прервана."
    exit 1
fi
log_success "Termux обнаружен: $PREFIX"

# --- Директория проекта ----------------------------------------------------
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
log_info "Директория проекта: $PROJECT_DIR"

# --- Шаг 1: Обновление пакетов ---------------------------------------------
echo ""
log_info "Шаг 1/8: Обновление пакетов Termux..."
pkg update -y >/dev/null 2>&1 || {
    log_warn "Не удалось полностью обновить пакеты. Продолжаем."
}
log_success "Пакеты обновлены."

# --- Шаг 2: Системные зависимости ------------------------------------------
echo ""
log_info "Шаг 2/8: Установка системных зависимостей..."

for pkg_name in python clang rust golang git binutils make openssl ca-certificates; do
    if pkg install -y "$pkg_name" >/dev/null 2>&1; then
        log_success "Установлено: $pkg_name"
    else
        log_warn "Не удалось установить: $pkg_name (продолжаем)"
    fi
done

# Java ставим отдельно — в разных версиях Termux пакет называется по-разному.
if pkg install -y openjdk-21 >/dev/null 2>&1; then
    log_success "Установлено: openjdk-21"
elif pkg install -y openjdk-17 >/dev/null 2>&1; then
    log_success "Установлено: openjdk-17 (устаревший)"
else
    log_warn "Java не установлена. Codermuks будет работать на 14 из 15 языков."
fi

log_success "Системные зависимости готовы."

# --- Шаг 3: Python-библиотеки ----------------------------------------------
# Из-за карантина PyPI ставим всё в обход, с явными версиями.
echo ""
log_info "Шаг 3/8: Установка Python-библиотек..."

pip install --upgrade pip setuptools wheel >/dev/null 2>&1 || true
log_success "pip, setuptools, wheel обновлены."

# pydantic-core — из индекса TUR (готовый бинарник для Android ARM64).
log_info "Устанавливаю pydantic-core из индекса Termux..."
pip install "pydantic-core==2.41.5" \
    --extra-index-url https://termux-user-repository.github.io/pypi/ \
    --prefer-binary >/dev/null 2>&1 || {
    log_warn "Не удалось поставить pydantic-core 2.41.5 из TUR, пробую стандартный источник..."
    pip install "pydantic-core==2.41.5" --prefer-binary >/dev/null 2>&1 || \
        log_warn "pydantic-core не установлен."
}
log_success "pydantic-core готов."

# pydantic без зависимостей.
pip install "pydantic==2.12.5" --no-deps >/dev/null 2>&1 || \
    log_warn "pydantic не установлен."
log_success "pydantic готов."

# mistralai — из GitHub напрямую (обход карантина PyPI).
log_info "Устанавливаю mistralai из GitHub..."
pip install "mistralai @ git+https://github.com/mistralai/client-python.git@v1.12.4" \
    --no-deps >/dev/null 2>&1 || {
    log_warn "Не удалось установить mistralai."
}
log_success "mistralai готов."

# Остальные зависимости по одной.
for lib in annotated-types invoke \
           eval-type-backport python-dateutil pyyaml typing-inspection \
           httpx httpcore h11 anyio certifi idna six \
           opentelemetry-api opentelemetry-sdk opentelemetry-semantic-conventions \
           opentelemetry-exporter-otlp-proto-http \
           googleapis-common-protos protobuf; do
    pip install "$lib" >/dev/null 2>&1 || true
done
log_success "Зависимости mistralai установлены."

# rich, requests, pyfiglet.
for lib in rich requests pyfiglet; do
    if pip install "$lib" >/dev/null 2>&1; then
        log_success "Установлено: $lib"
    else
        log_warn "Не удалось установить: $lib (продолжаем)"
    fi
done

# pytest — для автотестов.
if pip install pytest >/dev/null 2>&1; then
    log_success "Установлено: pytest"
fi

# Проверка критичных библиотек.
echo ""
log_info "Проверяю критичные библиотеки..."
MISSING_LIBS=""
for lib in mistralai rich requests; do
    python -c "import $lib" 2>/dev/null || MISSING_LIBS="$MISSING_LIBS $lib"
done

if [ -n "$MISSING_LIBS" ]; then
    log_error "Не установлены критичные библиотеки:$MISSING_LIBS"
    log_info "Попробуй вручную: pip install$MISSING_LIBS"
    exit 1
fi
log_success "Все критичные библиотеки на месте."

# --- Шаг 4: Пользовательская директория ------------------------------------
echo ""
log_info "Шаг 4/8: Подготовка пользовательской директории..."

USER_DIR="$HOME/.codermuks"
mkdir -p "$USER_DIR"
mkdir -p "$USER_DIR/artifacts"
mkdir -p "$USER_DIR/temp"
log_success "Создана директория: $USER_DIR"

# --- Шаг 5: Создаём config.json с настройками по умолчанию -----------------
echo ""
log_info "Шаг 5/8: Создание config.json..."

CONFIG_FILE="$USER_DIR/config.json"

if [ -f "$CONFIG_FILE" ]; then
    log_success "config.json уже существует: $CONFIG_FILE"
else
    cat > "$CONFIG_FILE" <<'JSON'
{
  "version": "1.1.0",
  "language": null,
  "team_lead": "mistral",
  "fallback_order": ["mistral", "qwen", "deepseek", "openrouter"],
  "providers": {
    "mistral": {
      "enabled": true,
      "model": "mistral-large-latest",
      "base_url": "https://api.mistral.ai/v1",
      "api_key": ""
    },
    "qwen": {
      "enabled": true,
      "model": "qwen3-coder-plus",
      "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
      "api_key": ""
    },
    "deepseek": {
      "enabled": true,
      "model": "deepseek-chat",
      "base_url": "https://api.deepseek.com/v1",
      "api_key": ""
    },
    "openrouter": {
      "enabled": true,
      "model": "qwen/qwen3-coder:free",
      "base_url": "https://openrouter.ai/api/v1",
      "api_key": ""
    }
  }
}
JSON
    log_success "config.json создан: $CONFIG_FILE"
fi

# --- Шаг 6: Создаём key.txt с JSON-структурой ------------------------------
echo ""
log_info "Шаг 6/8: Настройка API-ключей..."

KEY_FILE="$USER_DIR/key.txt"

if [ -f "$KEY_FILE" ]; then
    log_success "key.txt уже существует: $KEY_FILE"
elif [ -f "$PROJECT_DIR/key.txt" ]; then
    cp "$PROJECT_DIR/key.txt" "$KEY_FILE"
    log_success "key.txt скопирован из проекта: $KEY_FILE"
else
    cat > "$KEY_FILE" <<'KEYS'
{
  "_readme": "Вставь свои API-ключи вместо пустых строк ниже. Достаточно одного провайдера.",
  "_links": {
    "mistral": "https://console.mistral.ai/api-keys",
    "qwen": "https://dashscope.console.aliyun.com/apiKey",
    "deepseek": "https://platform.deepseek.com/api_keys",
    "openrouter": "https://openrouter.ai/keys"
  },
  "mistral": "",
  "qwen": "",
  "deepseek": "",
  "openrouter": ""
}
KEYS
    log_warn "key.txt создан: $KEY_FILE"
fi

# Проверяем, есть ли хотя бы один заполненный ключ.
HAS_KEY=0
if [ -f "$KEY_FILE" ]; then
    # Считаем количество пустых значений. Если все пустые — предупреждаем.
    NON_EMPTY=$(grep -E '"(mistral|qwen|deepseek|openrouter)"\s*:\s*"[^"]+"' "$KEY_FILE" 2>/dev/null | wc -l)
    if [ "$NON_EMPTY" -gt 0 ]; then
        HAS_KEY=1
    fi
fi

if [ "$HAS_KEY" -eq 0 ]; then
    log_warn "Ни один API-ключ не заполнен."
    log_warn "Открой файл и вставь хотя бы один ключ: nano $KEY_FILE"
    log_warn "Ссылки на получение ключей — в самом файле."
else
    log_success "API-ключи найдены."
fi

# --- Шаг 7: Симлинк в $PREFIX/bin ------------------------------------------
echo ""
log_info "Шаг 7/8: Создание команды codermuks..."

chmod +x "$PROJECT_DIR/codermuks" 2>/dev/null || true
chmod +x "$PROJECT_DIR/install.sh" 2>/dev/null || true
chmod +x "$PROJECT_DIR/uninstall.sh" 2>/dev/null || true
chmod +x "$PROJECT_DIR/update.sh" 2>/dev/null || true

ln -sf "$PROJECT_DIR/codermuks" "$PREFIX/bin/codermuks"

if [ -L "$PREFIX/bin/codermuks" ] && [ -x "$PREFIX/bin/codermuks" ]; then
    log_success "Команда codermuks установлена: $PREFIX/bin/codermuks"
else
    log_error "Не удалось создать симлинк. Проверь права на $PREFIX/bin/"
    exit 1
fi

# --- Шаг 8: Финальная проверка ---------------------------------------------
echo ""
log_info "Шаг 8/8: Проверка установки..."

MISSING=0
for f in main.py codermuks core/config.py ui/cli.py; do
    if [ ! -f "$PROJECT_DIR/$f" ]; then
        log_error "Отсутствует файл: $f"
        MISSING=1
    fi
done

if [ "$MISSING" -eq 1 ]; then
    log_error "Установка неполная. Проверь содержимое репозитория."
    exit 1
fi

python -c "import mistralai, rich, requests" 2>/dev/null || {
    log_error "Python не видит одну из библиотек (mistralai, rich, requests)."
    log_info "Попробуй вручную: pip install mistralai rich requests"
    exit 1
}
log_success "Все библиотеки на месте."

# --- Финальное сообщение ---------------------------------------------------
echo ""
echo -e "${GREEN}══════════════════════════════════════════════════════════════════${RESET}"
echo -e "${GREEN}  ✔  Codermuks in Termux v1.1.0 успешно установлен!${RESET}"
echo -e "${GREEN}══════════════════════════════════════════════════════════════════${RESET}"
echo ""

if [ "$HAS_KEY" -eq 0 ]; then
    echo -e "${YELLOW}  ⚠  Остался последний шаг: вставь хотя бы один API-ключ.${RESET}"
    echo ""
    echo -e "      ${CYAN}nano $KEY_FILE${RESET}"
    echo ""
    echo -e "      Ссылки на ключи — в самом файле key.txt."
    echo ""
else
    echo -e "${GREEN}  ✔  API-ключи на месте. Можно запускать!${RESET}"
    echo ""
fi

echo -e "  Запуск:  ${GREEN}codermuks${RESET}"
echo -e "  Справка: ${GREEN}codermuks /help${RESET}"
echo -e "  Удалить: ${GREEN}bash uninstall.sh${RESET}"
echo ""
echo -e "${CYAN}  При первом запуске codermuks спросит язык интерфейса.${RESET}"
echo ""