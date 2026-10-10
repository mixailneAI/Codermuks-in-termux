#!/data/data/com.termux/files/usr/bin/bash
# =============================================================================
#  Codermuks in Termux — обновление v1.1.0
# =============================================================================
#  Что делает этот скрипт:
#    1. Проверяет, что проект — это git-репозиторий.
#    2. Сохраняет локальные изменения (если есть) в stash.
#    3. Подтягивает свежую версию из ветки origin/main.
#    4. Проверяет, изменилась ли структура config.json — если да,
#       аккуратно дополняет его новыми полями, не трогая существующие.
#    5. Переустанавливает Python-зависимости (включая pytest).
#    6. Обновляет симлинк в $PREFIX/bin и права на скрипты.
#    7. Показывает, что изменилось.
#
#  Запуск:  bash update.sh
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

# --- Проверка Termux -------------------------------------------------------
if [ -z "$PREFIX" ] || [ ! -d "$PREFIX" ]; then
    log_error "Скрипт запущен вне Termux. Обновление прервано."
    exit 1
fi

# --- Директория проекта ----------------------------------------------------
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

USER_DIR="$HOME/.codermuks"
CONFIG_FILE="$USER_DIR/config.json"

# --- Баннер ----------------------------------------------------------------
echo ""
echo -e "${CYAN}══════════════════════════════════════════════════════════════════${RESET}"
echo -e "${CYAN}  Обновление Codermuks in Termux${RESET}"
echo -e "${CYAN}══════════════════════════════════════════════════════════════════${RESET}"
echo ""

# --- Шаг 1: Проверка git-репозитория ---------------------------------------
log_info "Шаг 1/7: Проверка git-репозитория..."
if [ ! -d "$PROJECT_DIR/.git" ]; then
    log_error "Проект не является git-репозиторием."
    log_info "Скачай заново: git clone https://github.com/mixailneAI/Codermuks-in-termux.git"
    exit 1
fi
log_success "Git-репозиторий найден."

# --- Шаг 2: Сохранение локальных изменений ---------------------------------
echo ""
log_info "Шаг 2/7: Сохранение локальных изменений..."
if ! git diff --quiet || ! git diff --cached --quiet; then
    STASH_NAME="codermuks-autostash-$(date +%Y%m%d-%H%M%S)"
    git stash push -u -m "$STASH_NAME" >/dev/null 2>&1
    log_warn "Локальные изменения сохранены в stash: $STASH_NAME"
    log_info "Восстановить позже: git stash pop"
else
    log_success "Локальных изменений нет."
fi

# --- Шаг 3: Подтягиваем обновления из origin -------------------------------
echo ""
log_info "Шаг 3/7: Загрузка обновлений из origin..."
git fetch origin >/dev/null 2>&1 || {
    log_error "Не удалось связаться с GitHub. Проверь интернет."
    exit 1
}

# Определяем основную ветку (main или master).
BRANCH="$(git symbolic-ref --short HEAD 2>/dev/null || echo main)"
if ! git rev-parse --verify "origin/$BRANCH" >/dev/null 2>&1; then
    BRANCH="master"
fi

BEFORE="$(git rev-parse HEAD)"
git pull --rebase origin "$BRANCH" >/dev/null 2>&1 || {
    log_error "Не удалось выполнить git pull. Возможен конфликт."
    log_info "Реши конфликт вручную: git status"
    exit 1
}
AFTER="$(git rev-parse HEAD)"

if [ "$BEFORE" = "$AFTER" ]; then
    log_success "Уже установлена последняя версия."
else
    COMMITS_AHEAD="$(git rev-list --count "$BEFORE".."$AFTER")"
    log_success "Обновлено коммитов: $COMMITS_AHEAD"
fi

# --- Шаг 4: Обновление config.json -----------------------------------------
# Если структура config.json изменилась (например, добавились новые
# провайдеры или поля), аккуратно дополняем файл, не трогая то, что
# уже введено пользователем (язык, team_lead, ключи).
echo ""
log_info "Шаг 4/7: Проверка config.json..."

mkdir -p "$USER_DIR"

if [ ! -f "$CONFIG_FILE" ]; then
    # Файла нет — создаём с нуля.
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
    log_success "config.json создан заново."
else
    # Файл есть — проверяем, что в нём нужные поля.
    # Логику слияния делает Python-модуль core/config.py — вызываем его.
    if [ -f "$PROJECT_DIR/core/config.py" ]; then
        python -c "
import sys
sys.path.insert(0, '$PROJECT_DIR')
try:
    from core import config
    config.migrate_config_file()
    print('OK')
except Exception as e:
    print(f'Ошибка миграции: {e}')
" 2>/dev/null && log_success "config.json актуален." || \
        log_warn "Не удалось проверить config.json — пропускаем."
    else
        log_warn "core/config.py не найден — пропускаем миграцию."
    fi
fi

# --- Шаг 5: Обновление Python-зависимостей ---------------------------------
echo ""
log_info "Шаг 5/7: Обновление Python-зависимостей..."

# pydantic-core — обновляем через индекс TUR.
pip install --upgrade "pydantic-core==2.41.5" \
    --extra-index-url https://termux-user-repository.github.io/pypi/ \
    --prefer-binary >/dev/null 2>&1 || \
    log_warn "pydantic-core не обновлён."

# pydantic.
pip install --upgrade "pydantic==2.12.5" --no-deps >/dev/null 2>&1 || \
    log_warn "pydantic не обновлён."

# mistralai — из GitHub по фиксированному тегу.
pip install --upgrade "mistralai @ git+https://github.com/mistralai/client-python.git@v1.12.4" \
    --no-deps >/dev/null 2>&1 || \
    log_warn "mistralai не обновлён."

# Остальные библиотеки.
for lib in mistralai rich requests pyfiglet pytest; do
    pip install --upgrade "$lib" >/dev/null 2>&1 || true
done

log_success "Python-зависимости обновлены."

# --- Шаг 6: Симлинк и права ------------------------------------------------
echo ""
log_info "Шаг 6/7: Обновление симлинка и прав..."

chmod +x "$PROJECT_DIR/codermuks"
chmod +x "$PROJECT_DIR/install.sh"   2>/dev/null || true
chmod +x "$PROJECT_DIR/uninstall.sh" 2>/dev/null || true
chmod +x "$PROJECT_DIR/update.sh"    2>/dev/null || true

ln -sf "$PROJECT_DIR/codermuks" "$PREFIX/bin/codermuks"
log_success "Симлинк обновлён: $PREFIX/bin/codermuks"

# --- Шаг 7: Проверка -------------------------------------------------------
echo ""
log_info "Шаг 7/7: Проверка установки..."

python -c "import mistralai, rich, requests" 2>/dev/null && \
    log_success "Python-библиотеки в порядке." || \
    log_warn "Не все библиотеки доступны. Запусти install.sh, если что-то сломалось."

# --- Проверка наличия ключа ------------------------------------------------
KEY_FILE="$USER_DIR/key.txt"
if [ ! -f "$KEY_FILE" ]; then
    log_warn "key.txt не найден: $KEY_FILE"
    log_info "Запусти install.sh, чтобы создать его."
fi

# --- Финальное сообщение ---------------------------------------------------
echo ""
echo -e "${GREEN}══════════════════════════════════════════════════════════════════${RESET}"
echo -e "${GREEN}  ✔  Обновление завершено.${RESET}"
echo -e "${GREEN}══════════════════════════════════════════════════════════════════${RESET}"
echo ""
echo -e "  Запуск:  ${GREEN}codermuks${RESET}"
echo ""

# --- Напоминание про stash -------------------------------------------------
if git stash list | grep -q "codermuks-autostash"; then
    echo ""
    log_warn "Не забудь: локальные изменения лежат в stash."
    echo -e "   Посмотреть: ${CYAN}git stash list${RESET}"
    echo -e "   Вернуть:    ${CYAN}git stash pop${RESET}"
    echo ""
fi