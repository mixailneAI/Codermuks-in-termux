#!/data/data/com.termux/files/usr/bin/bash
# =============================================================================
#  Codermuks in Termux — удаление
# =============================================================================
#  Что делает этот скрипт:
#    1. Спрашивает подтверждение у пользователя.
#    2. Удаляет симлинк из $PREFIX/bin.
#    3. Опционально удаляет пользовательскую директорию ~/.codermuks/
#       вместе с ключом, логами и артефактами.
#    4. Опционально удаляет Python-библиотеки, установленные установщиком.
#    5. Показывает, что осталось удалить вручную (папку проекта).
#
#  Запуск:  bash uninstall.sh
# =============================================================================

set -e

# --- Цвета для красивого вывода --------------------------------------------
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

# --- Проверяем, что мы в Termux --------------------------------------------
if [ -z "$PREFIX" ] || [ ! -d "$PREFIX" ]; then
    log_error "Скрипт запущен вне Termux. Удаление прервано."
    exit 1
fi

# --- Определяем директорию проекта -----------------------------------------
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER_DIR="$HOME/.codermuks"

# --- Баннер ----------------------------------------------------------------
echo ""
echo -e "${RED}══════════════════════════════════════════════════════════════════${RESET}"
echo -e "${RED}  Удаление Codermuks in Termux${RESET}"
echo -e "${RED}══════════════════════════════════════════════════════════════════${RESET}"
echo ""
log_warn "Будут удалены:"
echo "   • Симлинк:            $PREFIX/bin/codermuks"
echo "   • Пользовательская:   $USER_DIR (по желанию)"
echo "   • Python-библиотеки:  mistralai, rich, requests, pyfiglet (по желанию)"
echo ""

# --- Общее подтверждение ---------------------------------------------------
read -rp "$(echo -e "${YELLOW}Продолжить удаление? [y/N]: ${RESET}")" CONFIRM
if [[ ! "$CONFIRM" =~ ^[YyДд]$ ]]; then
    log_info "Удаление отменено пользователем."
    exit 0
fi

# --- Шаг 1: Удаляем симлинк из $PREFIX/bin ---------------------------------
echo ""
log_info "Шаг 1/3: Удаление симлинка..."
if [ -L "$PREFIX/bin/codermuks" ]; then
    rm -f "$PREFIX/bin/codermuks"
    log_success "Симлинк удалён: $PREFIX/bin/codermuks"
elif [ -f "$PREFIX/bin/codermuks" ]; then
    # На случай, если был скопирован, а не симлинк.
    rm -f "$PREFIX/bin/codermuks"
    log_success "Файл удалён: $PREFIX/bin/codermuks"
else
    log_warn "Симлинк не найден — возможно, уже удалён."
fi

# --- Шаг 2: Удаляем пользовательскую директорию (по желанию) ---------------
echo ""
log_info "Шаг 2/3: Пользовательские данные..."
if [ -d "$USER_DIR" ]; then
    echo -e "${YELLOW}Директория $USER_DIR содержит:${RESET}"
    [ -f "$USER_DIR/key.txt" ]                && echo "   • key.txt        (ваш API-ключ Mistral)"
    [ -f "$HOME/.codermuks.log" ]             && echo "   • ~/.codermuks.log (лог работы)"
    [ -d "$USER_DIR/artifacts" ]              && echo "   • artifacts/     (сохранённые результаты)"
    echo ""
    read -rp "$(echo -e "${YELLOW}Удалить $USER_DIR? [y/N]: ${RESET}")" DEL_USER
    if [[ "$DEL_USER" =~ ^[YyДд]$ ]]; then
        rm -rf "$USER_DIR"
        rm -f "$HOME/.codermuks.log"
        log_success "Пользовательские данные удалены."
    else
        log_warn "Пользовательские данные сохранены: $USER_DIR"
    fi
else
    log_warn "Пользовательская директория не найдена — пропускаем."
fi

# --- Шаг 3: Удаляем Python-библиотеки (по желанию) -------------------------
echo ""
log_info "Шаг 3/3: Python-библиотеки..."
read -rp "$(echo -e "${YELLOW}Удалить библиотеки mistralai, rich, requests, pyfiglet? [y/N]: ${RESET}")" DEL_PIP
if [[ "$DEL_PIP" =~ ^[YyДд]$ ]]; then
    pip uninstall -y mistralai rich requests pyfiglet >/dev/null 2>&1 || true
    log_success "Python-библиотеки удалены."
else
    log_warn "Python-библиотеки оставлены. Они могут использоваться другими проектами."
fi

# --- Финальное сообщение ---------------------------------------------------
echo ""
echo -e "${GREEN}══════════════════════════════════════════════════════════════════${RESET}"
echo -e "${GREEN}  ✔  Codermuks in Termux удалён.${RESET}"
echo -e "${GREEN}══════════════════════════════════════════════════════════════════${RESET}"
echo ""
log_info "Осталось удалить вручную папку проекта:"
echo -e "   ${CYAN}rm -rf $PROJECT_DIR${RESET}"
echo ""