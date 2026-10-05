#!/data/data/com.termux/files/usr/bin/bash
# =============================================================================
#  Codermuks in Termux — обновление
# =============================================================================
#  Что делает этот скрипт:
#    1. Проверяет, что проект — это git-репозиторий.
#    2. Сохраняет локальные изменения (если есть) в stash.
#    3. Подтягивает свежую версию из ветки origin/main.
#    4. Переустанавливает Python-зависимости, если менялся requirements.
#    5. Обновляет симлинк в $PREFIX/bin, если менялся лаунчер.
#    6. Показывает, что изменилось.
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

# --- Проверяем Termux ------------------------------------------------------
if [ -z "$PREFIX" ] || [ ! -d "$PREFIX" ]; then
    log_error "Скрипт запущен вне Termux. Обновление прервано."
    exit 1
fi

# --- Определяем директорию проекта -----------------------------------------
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# --- Баннер ----------------------------------------------------------------
echo ""
echo -e "${CYAN}══════════════════════════════════════════════════════════════════${RESET}"
echo -e "${CYAN}  Обновление Codermuks in Termux${RESET}"
echo -e "${CYAN}══════════════════════════════════════════════════════════════════${RESET}"
echo ""

# --- Шаг 1: Проверяем, что это git-репозиторий -----------------------------
log_info "Шаг 1/5: Проверка git-репозитория..."
if [ ! -d "$PROJECT_DIR/.git" ]; then
    log_error "Проект не является git-репозиторием."
    log_info "Скачай заново: git clone https://github.com/mixailneAI/Codermuks-in-termux.git"
    exit 1
fi
log_success "Git-репозиторий найден."

# --- Шаг 2: Сохраняем локальные изменения ----------------------------------
echo ""
log_info "Шаг 2/5: Сохранение локальных изменений..."
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
log_info "Шаг 3/5: Загрузка обновлений из origin..."
git fetch origin >/dev/null 2>&1 || {
    log_error "Не удалось связаться с GitHub. Проверь интернет."
    exit 1
}

# Определяем основную ветку — main или master.
BRANCH="$(git symbolic-ref --short HEAD 2>/dev/null || echo main)"
if ! git rev-parse --verify "origin/$BRANCH" >/dev/null 2>&1; then
    BRANCH="master"
fi

# Считаем, сколько коммитов мы отстаём — для информативного вывода.
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

# --- Шаг 4: Обновляем Python-библиотеки ------------------------------------
echo ""
log_info "Шаг 4/5: Обновление Python-библиотек..."
pip install --upgrade mistralai rich requests pyfiglet >/dev/null 2>&1
log_success "Python-библиотеки обновлены."

# --- Шаг 5: Обновляем симлинк и права --------------------------------------
echo ""
log_info "Шаг 5/5: Обновление симлинка и прав..."
chmod +x "$PROJECT_DIR/codermuks"
chmod +x "$PROJECT_DIR/install.sh"   2>/dev/null || true
chmod +x "$PROJECT_DIR/uninstall.sh" 2>/dev/null || true
chmod +x "$PROJECT_DIR/update.sh"    2>/dev/null || true
ln -sf "$PROJECT_DIR/codermuks" "$PREFIX/bin/codermuks"
log_success "Симлинк обновлён: $PREFIX/bin/codermuks"

# --- Проверка, что ключ на месте ------------------------------------------
echo ""
USER_KEY="$HOME/.codermuks/key.txt"
if [ ! -f "$USER_KEY" ] || grep -q "ВСТАВЬ_СЮДА_СВОЙ_MISTRAL_API_KEY" "$USER_KEY" 2>/dev/null; then
    log_warn "API-ключ Mistral не установлен."
    log_info "Вставь ключ: nano $USER_KEY"
    log_info "Получить: https://console.mistral.ai/api-keys"
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