#!/data/data/com.termux/files/usr/bin/bash
# =============================================================================
#  Codermuks in Termux — установщик
# =============================================================================
#  Что делает этот скрипт:
#    1. Проверяет, что мы в Termux.
#    2. Обновляет пакеты Termux.
#    3. Ставит системные зависимости (Python, компиляторы, рантаймы).
#    4. Ставит Python-библиотеки (mistralai, rich, requests, pyfiglet).
#    5. Копирует key.txt из проекта в ~/.codermuks/key.txt.
#    6. Создаёт симлинк в $PREFIX/bin, чтобы команда `codermuks` работала
#       из любой директории.
#    7. Делает финальную проверку установки.
#
#  Запуск:  bash install.sh
# =============================================================================

# --- Строгий режим: любая ошибка останавливает выполнение ------------------
set -e

# --- Цвета для красивого вывода --------------------------------------------
GREEN="\033[1;32m"
RED="\033[1;31m"
YELLOW="\033[1;33m"
BLUE="\033[1;34m"
CYAN="\033[1;36m"
RESET="\033[0m"

# --- Вспомогательные функции для вывода ------------------------------------
log_info()    { echo -e "${BLUE}[•]${RESET} $1"; }
log_success() { echo -e "${GREEN}[✔]${RESET} $1"; }
log_warn()    { echo -e "${YELLOW}[!]${RESET} $1"; }
log_error()   { echo -e "${RED}[✘]${RESET} $1"; }

# --- Красивый баннер при старте --------------------------------------------
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
echo -e "${CYAN}Установщик Codermuks in Termux v1.0.0${RESET}"
echo ""

# --- Проверяем, что мы действительно в Termux ------------------------------
# Termux всегда имеет переменную PREFIX, указывающую на /data/data/.../usr.
if [ -z "$PREFIX" ] || [ ! -d "$PREFIX" ]; then
    log_error "Скрипт запущен вне Termux. Установка прервана."
    exit 1
fi
log_success "Termux обнаружен: $PREFIX"

# --- Определяем директорию проекта -----------------------------------------
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
log_info "Директория проекта: $PROJECT_DIR"

# --- Шаг 1: Обновляем пакеты Termux ----------------------------------------
echo ""
log_info "Шаг 1/7: Обновление пакетов Termux..."
pkg update -y >/dev/null 2>&1 || {
    log_warn "Не удалось обновить пакеты. Продолжаем с текущими версиями."
}
log_success "Пакеты обновлены."

# --- Шаг 2: Устанавливаем системные зависимости ----------------------------
echo ""
log_info "Шаг 2/7: Установка системных зависимостей..."
# Список:
#   python        — основной интерпретатор
#   clang         — компилятор C и C++
#   rust          — язык Rust
#   golang        — язык Go
#   openjdk-17    — Java
#   git           — система контроля версий (для update.sh)
#   binutils      — утилиты для линковки
#   make          — сборщик проектов
pkg install -y python clang rust golang openjdk-17 git binutils make >/dev/null 2>&1
log_success "Системные зависимости установлены."

# --- Шаг 3: Устанавливаем Python-библиотеки --------------------------------
echo ""
log_info "Шаг 3/7: Установка Python-библиотек..."
pip install --upgrade pip >/dev/null 2>&1
pip install mistralai rich requests pyfiglet >/dev/null 2>&1
log_success "Python-библиотеки установлены."

# --- Шаг 4: Создаём пользовательскую директорию ----------------------------
echo ""
log_info "Шаг 4/7: Подготовка пользовательской директории..."

# Пользовательская директория — там живут ключ, логи и артефакты.
USER_DIR="$HOME/.codermuks"
mkdir -p "$USER_DIR"
mkdir -p "$USER_DIR/artifacts"
log_success "Создана директория: $USER_DIR"

# --- Шаг 5: Копируем key.txt в пользовательскую директорию -----------------
echo ""
log_info "Шаг 5/7: Настройка API-ключа Mistral..."

if [ -f "$USER_DIR/key.txt" ]; then
    # Ключ уже есть — не перезаписываем, чтобы не потерять введённое значение.
    log_success "Файл ключа уже существует: $USER_DIR/key.txt"
elif [ -f "$PROJECT_DIR/key.txt" ]; then
    # Копируем key.txt из проекта в пользовательскую директорию.
    cp "$PROJECT_DIR/key.txt" "$USER_DIR/key.txt"
    log_success "Ключ скопирован: $PROJECT_DIR/key.txt → $USER_DIR/key.txt"
else
    # Файла нет ни там, ни там — создаём вручную с заглушкой.
    cat > "$USER_DIR/key.txt" <<'EOF'
# =============================================================================
#  Codermuks in Termux — файл с API-ключом Mistral
# =============================================================================
#
#  Вставь свой настоящий ключ вместо строки-заглушки ниже.
#  Ключ — одна длинная строка без пробелов и кавычек.
#
#  Получить бесплатный ключ:  https://console.mistral.ai/api-keys
#
# =============================================================================

ВСТАВЬ_СЮДА_СВОЙ_MISTRAL_API_KEY
EOF
    log_warn "Файл key.txt не найден в проекте — создан новый: $USER_DIR/key.txt"
fi

# Проверяем, вставлен ли настоящий ключ (а не заглушка).
if grep -q "ВСТАВЬ_СЮДА_СВОЙ_MISTRAL_API_KEY" "$USER_DIR/key.txt" 2>/dev/null; then
    log_warn "API-ключ ещё не вставлен."
    log_warn "Открой файл и вставь ключ: nano $USER_DIR/key.txt"
    log_warn "Получить бесплатный ключ: https://console.mistral.ai/api-keys"
else
    log_success "API-ключ на месте."
fi

# --- Шаг 6: Создаём симлинк в $PREFIX/bin ----------------------------------
echo ""
log_info "Шаг 6/7: Создание команды codermuks..."

# Делаем лаунчер и служебные скрипты исполняемыми.
chmod +x "$PROJECT_DIR/codermuks"
chmod +x "$PROJECT_DIR/install.sh"
chmod +x "$PROJECT_DIR/uninstall.sh" 2>/dev/null || true
chmod +x "$PROJECT_DIR/update.sh"    2>/dev/null || true

# Симлинк — чтобы команда была доступна из любой директории.
ln -sf "$PROJECT_DIR/codermuks" "$PREFIX/bin/codermuks"

# Проверяем, что симлинк создан и ведёт куда надо.
if [ -L "$PREFIX/bin/codermuks" ] && [ -x "$PREFIX/bin/codermuks" ]; then
    log_success "Команда codermuks установлена: $PREFIX/bin/codermuks"
else
    log_error "Не удалось создать симлинк. Проверь права на $PREFIX/bin/"
    exit 1
fi

# --- Шаг 7: Финальная проверка --------------------------------------------
echo ""
log_info "Шаг 7/7: Проверка установки..."

# Проверяем наличие всех ключевых файлов проекта.
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

# Проверяем, что Python видит установленные библиотеки.
python -c "import mistralai, rich, requests" 2>/dev/null || {
    log_error "Python не видит одну из библиотек (mistralai, rich, requests)."
    log_info "Попробуй вручную: pip install mistralai rich requests pyfiglet"
    exit 1
}
log_success "Все библиотеки на месте."

# --- Финальное сообщение ---------------------------------------------------
echo ""
echo -e "${GREEN}══════════════════════════════════════════════════════════════════${RESET}"
echo -e "${GREEN}  ✔  Codermuks in Termux успешно установлен!${RESET}"
echo -e "${GREEN}══════════════════════════════════════════════════════════════════${RESET}"
echo ""

# Ещё раз напоминаем про ключ, если он не вставлен.
if grep -q "ВСТАВЬ_СЮДА_СВОЙ_MISTRAL_API_KEY" "$USER_DIR/key.txt" 2>/dev/null; then
    echo -e "${YELLOW}  ⚠  Остался последний шаг: вставь свой API-ключ Mistral.${RESET}"
    echo ""
    echo -e "      ${CYAN}nano $USER_DIR/key.txt${RESET}"
    echo ""
    echo -e "      Получить бесплатный ключ:"
    echo -e "      ${CYAN}https://console.mistral.ai/api-keys${RESET}"
    echo ""
else
    echo -e "${GREEN}  ✔  API-ключ уже вставлен. Можно запускать!${RESET}"
    echo ""
fi

echo -e "  Запуск:  ${GREEN}codermuks${RESET}"
echo -e "  Справка: ${GREEN}codermuks /help${RESET}"
echo -e "  Удалить: ${GREEN}bash uninstall.sh${RESET}"
echo ""