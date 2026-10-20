#!/data/data/com.termux/files/usr/bin/bash
# =============================================================================
#  Codermuks in Termux — установщик v1.4.0
# =============================================================================
#  С автообновляющимся прогресс-индикатором: спиннер + таймер для каждой
#  долгой операции (pkg, pip). Пользователь видит, что установка идёт.
# =============================================================================

set -e

# --- Цвета -----------------------------------------------------------------
GREEN="\033[1;32m"
RED="\033[1;31m"
YELLOW="\033[1;33m"
BLUE="\033[1;34m"
CYAN="\033[1;36m"
DIM="\033[2m"
RESET="\033[0m"

log_info()    { echo -e "${BLUE}[•]${RESET} $1"; }
log_success() { echo -e "${GREEN}[✔]${RESET} $1"; }
log_warn()    { echo -e "${YELLOW}[!]${RESET} $1"; }
log_error()   { echo -e "${RED}[✘]${RESET} $1"; }

# --- Прогресс-индикатор ----------------------------------------------------
# Запускает команду в фоне, показывает спиннер + таймер, скрывает вывод.
# После завершения — строка с ✔ / ✘ и длительностью.
# При ошибке — показывает последние строки лога.
run_with_progress() {
    local label="$1"
    shift

    local start_time=$(date +%s)
    local pid
    local logfile="${TMPDIR:-$PREFIX/tmp}/codermuks_step_$$.log"
    mkdir -p "$(dirname "$logfile")"
    local frames=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
    local i=0

    # Запускаем команду в фоне.
    ("$@" > "$logfile" 2>&1) &
    pid=$!

    # Пока команда работает — крутим спиннер.
    while kill -0 "$pid" 2>/dev/null; do
        local elapsed=$(( $(date +%s) - start_time ))
        local mins=$(( elapsed / 60 ))
        local secs=$(( elapsed % 60 ))
        printf "\r  ${CYAN}%s${RESET}  %s  ${DIM}%02d:%02d${RESET}  " \
            "${frames[$i]}" "$label" "$mins" "$secs"
        i=$(( (i + 1) % ${#frames[@]} ))
        sleep 0.1
    done

    wait "$pid"
    local exit_code=$?
    local elapsed=$(( $(date +%s) - start_time ))
    local mins=$(( elapsed / 60 ))
    local secs=$(( elapsed % 60 ))

    printf "\r\033[K"

    if [ "$exit_code" -eq 0 ]; then
        printf "  ${GREEN}✔${RESET}  %s  ${DIM}(%02d:%02d)${RESET}\n" \
            "$label" "$mins" "$secs"
    else
        printf "  ${RED}✘${RESET}  %s  ${DIM}(%02d:%02d)${RESET}\n" \
            "$label" "$mins" "$secs"
        if [ -f "$logfile" ]; then
            echo -e "    ${DIM}--- последние строки ---${RESET}"
            tail -5 "$logfile" 2>/dev/null | sed 's/^/    /'
        fi
    fi

    rm -f "$logfile"
    return $exit_code
}

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
echo -e "${CYAN}Установщик Codermuks in Termux v1.4.0${RESET}"
echo ""

INSTALL_START=$(date +%s)

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
run_with_progress "Обновление индексов и пакетов" pkg update -y || true
log_success "Пакеты обновлены."

# --- Шаг 2: Системные зависимости ------------------------------------------
echo ""
log_info "Шаг 2/8: Установка системных зависимостей..."

for pkg_name in python clang rust golang git binutils make openssl ca-certificates; do
    if run_with_progress "Установка: $pkg_name" pkg install -y "$pkg_name"; then
        :
    else
        log_warn "Не удалось установить: $pkg_name (продолжаем)"
    fi
done

# Java отдельно — версии разные.
if run_with_progress "Установка: openjdk-21" pkg install -y openjdk-21; then
    :
elif run_with_progress "Установка: openjdk-17 (legacy)" pkg install -y openjdk-17; then
    :
else
    log_warn "Java не установлена. Codermuks будет работать на 14 из 15 языков."
fi

log_success "Системные зависимости готовы."

# --- Шаг 3: Python-библиотеки ----------------------------------------------
echo ""
log_info "Шаг 3/8: Установка Python-библиотек..."

run_with_progress "Обновление pip, setuptools, wheel" \
    pip install --upgrade pip setuptools wheel || true

log_info "Устанавливаю pydantic-core (может занять 1-2 минуты)..."
run_with_progress "Установка pydantic-core из Termux-индекса" \
    pip install --no-input "pydantic-core==2.41.5" \
        --extra-index-url https://termux-user-repository.github.io/pypi/ \
        --prefer-binary || \
    run_with_progress "Установка pydantic-core (fallback)" \
        pip install --no-input "pydantic-core==2.41.5" --prefer-binary || true

run_with_progress "Установка pydantic" \
    pip install --no-input "pydantic==2.12.5" --no-deps || true

log_info "Устанавливаю mistralai из GitHub (обход карантина PyPI)..."
run_with_progress "Установка mistralai" \
    pip install --no-input "mistralai @ git+https://github.com/mistralai/client-python.git@v1.12.4" \
        --no-deps || true

log_info "Устанавливаю зависимости mistralai (по одной)..."
for lib in annotated-types invoke eval-type-backport python-dateutil pyyaml \
           typing-inspection httpx httpcore h11 anyio certifi idna six \
           opentelemetry-api opentelemetry-sdk opentelemetry-semantic-conventions \
           opentelemetry-exporter-otlp-proto-http googleapis-common-protos protobuf; do
    run_with_progress "Установка: $lib" pip install --no-input "$lib" || true
done

log_info "Устанавливаю rich, requests, pyfiglet..."
for lib in rich requests pyfiglet; do
    run_with_progress "Установка: $lib" pip install --no-input "$lib" || true
done

run_with_progress "Установка: pytest" pip install --no-input pytest || true

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
mkdir -p "$HOME/codermuks-workspace"
log_success "Создана директория: $USER_DIR"

# --- Шаг 5: config.json ----------------------------------------------------
echo ""
log_info "Шаг 5/8: Создание config.json..."

CONFIG_FILE="$USER_DIR/config.json"
if [ -f "$CONFIG_FILE" ]; then
    log_success "config.json уже существует: $CONFIG_FILE"
else
    cat > "$CONFIG_FILE" <<'JSON'
{
  "version": "1.4.0",
  "language": null,
  "team_lead": "mistral",
  "fallback_order": ["mistral", "qwen", "deepseek", "openrouter"],
  "providers": {
    "mistral": {
      "enabled": true,
      "model": "codestral-latest",
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

# --- Шаг 6: key.txt --------------------------------------------------------
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
  "_readme": "Вставь свои API-ключи вместо пустых строк. Достаточно одного.",
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

HAS_KEY=0
if [ -f "$KEY_FILE" ]; then
    NON_EMPTY=$(grep -E '"(mistral|qwen|deepseek|openrouter)"\s*:\s*"[^"]+"' "$KEY_FILE" 2>/dev/null | wc -l)
    if [ "$NON_EMPTY" -gt 0 ]; then
        HAS_KEY=1
    fi
fi

if [ "$HAS_KEY" -eq 0 ]; then
    log_warn "Ни один API-ключ не заполнен."
    log_warn "Открой файл и вставь хотя бы один ключ: nano $KEY_FILE"
else
    log_success "API-ключи найдены."
fi

# --- Шаг 7: Симлинк --------------------------------------------------------
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
    log_error "Не удалось создать симлинк."
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
    log_error "Установка неполная."
    exit 1
fi

python -c "import mistralai, rich, requests" 2>/dev/null || {
    log_error "Python не видит одну из библиотек."
    exit 1
}
log_success "Все библиотеки на месте."

# --- Финальное сообщение ---------------------------------------------------
INSTALL_END=$(date +%s)
TOTAL_SECS=$(( INSTALL_END - INSTALL_START ))
TOTAL_MINS=$(( TOTAL_SECS / 60 ))
TOTAL_REM=$(( TOTAL_SECS % 60 ))

echo ""
echo -e "${GREEN}══════════════════════════════════════════════════════════════════${RESET}"
echo -e "${GREEN}  ✔  Codermuks in Termux v1.4.0 успешно установлен!${RESET}"
echo -e "${GREEN}══════════════════════════════════════════════════════════════════${RESET}"
echo -e "  ${DIM}Общее время установки: ${TOTAL_MINS} мин ${TOTAL_REM} сек${RESET}"
echo ""

if [ "$HAS_KEY" -eq 0 ]; then
    echo -e "${YELLOW}  ⚠  Остался последний шаг: вставь хотя бы один API-ключ.${RESET}"
    echo ""
    echo -e "      ${CYAN}nano $KEY_FILE${RESET}"
    echo ""
else
    echo -e "${GREEN}  ✔  API-ключи на месте. Можно запускать!${RESET}"
    echo ""
fi

echo -e "  Запуск:   ${GREEN}codermuks${RESET}"
echo -e "  Справка:  ${GREEN}codermuks /help${RESET}"
echo -e "  Удалить:  ${GREEN}bash uninstall.sh${RESET}"
echo ""
echo -e "${CYAN}  При первом запуске codermuks спросит язык интерфейса.${RESET}"
echo ""
