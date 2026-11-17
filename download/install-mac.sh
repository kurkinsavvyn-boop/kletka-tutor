#!/bin/bash
# Установка «Клетки» начисто: убирает все старые версии, их данные и разрешения, ставит последнюю версию.
# Запуск одной строкой в Терминале:
#   curl -fsSL https://kurkinsavvyn-boop.github.io/kletka-tutor/download/install-mac.sh | bash
# DRY=1 — только показать, что будет сделано, ничего не меняя.

REPO="kurkinsavvyn-boop/kletka-tutor"
BUNDLE="ru.kletka.desktop"
DEST="/Applications/Клетка.app"
DRY="${DRY:-}"
do_() { if [ -n "$DRY" ]; then echo "   [проверка] $*"; else "$@"; fi; }
fail() { echo; echo "❌ $1"; echo "Напишите об этом и пришлите снимок этого окна."; exit 1; }

echo
echo "Установка «Клетки» начисто"
echo "──────────────────────────"

echo "1/5 Закрываю «Клетку», если открыта…"
do_ osascript -e 'quit app "Клетка"' >/dev/null 2>&1
sleep 2
do_ pkill -x "Клетка" >/dev/null 2>&1

echo "2/5 Убираю все старые копии…"
mdfind "kMDItemCFBundleIdentifier == '$BUNDLE'" 2>/dev/null | while IFS= read -r p; do
  case "$p" in *.app) ;; *) continue ;; esac
  case "$p" in */.Trash/*) continue ;; esac
  case "$p" in
    /Volumes/*)
      vol=$(echo "$p" | cut -d/ -f1-3)
      echo "   извлекаю диск: $vol"
      do_ diskutil eject "$vol" >/dev/null 2>&1 ;;
    *)
      echo "   в корзину: ${p/#$HOME/~}"
      if [ -z "$DRY" ]; then
        mv "$p" "$HOME/.Trash/Клетка-старая-$(date +%s)-$RANDOM.app" 2>/dev/null || rm -rf "$p"
      fi ;;
  esac
done
[ -e "$DEST" ] && { echo "   удаляю: $DEST"; do_ rm -rf "$DEST"; }
do_ rm -rf "$HOME/Library/Application Support/kletka-desktop" "$HOME/Library/Saved Application State/$BUNDLE.savedState"

echo "3/5 Стираю старые разрешения macOS…"
do_ tccutil reset All "$BUNDLE" >/dev/null 2>&1

echo "4/5 Скачиваю новую версию…"
ARCH=$(uname -m); [ "$ARCH" = "arm64" ] || ARCH="x64"
URL=$(curl -fsSL "https://api.github.com/repos/$REPO/releases?per_page=30" \
  | grep -o "https://github.com/$REPO/releases/download/desktop-v[0-9.]*/Kletka-[0-9.]*-mac-$ARCH\.zip" \
  | awk -F'desktop-v' '{split($2,a,"/"); print a[1]" "$0}' | sort -V | tail -1 | cut -d' ' -f2)
[ -n "$URL" ] || fail "Не нашёл новую версию. Проверьте интернет и запустите ещё раз."
echo "   $(basename "$URL")"
if [ -n "$DRY" ]; then echo "   [проверка] скачать и поставить в $DEST"; echo; echo "Проверка закончена, ничего не изменено."; exit 0; fi
T=$(mktemp -d)
curl -fL --progress-bar "$URL" -o "$T/k.zip" || fail "Не получилось скачать. Проверьте интернет и запустите ещё раз."
ditto -x -k "$T/k.zip" "$T/x" || fail "Скачанный файл повреждён. Запустите ещё раз."
[ -d "$T/x/Клетка.app" ] || fail "В скачанном файле нет программы."
ditto "$T/x/Клетка.app" "$DEST" || fail "Не получилось положить программу в папку «Программы»."
rm -rf "$T"
xattr -dr com.apple.quarantine "$DEST" >/dev/null 2>&1

echo "5/5 Открываю «Клетку»…"
open "$DEST"
echo
echo "✅ Готово. В «Клетке» войдите в аккаунт — откроется окно «Разрешения для Клетки»."
echo "   Шаг 1 «Сбросить старые разрешения» уже сделан: нажмите «Уже сбрасывали»."
echo "   Потом нажимайте «Разрешить» по очереди. Это окно Терминала можно закрыть."
