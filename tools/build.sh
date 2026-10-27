#!/bin/sh
# Собирает сервис в app/index.html из прототипа и копирует картинки.
# Главная страница (index.html) лежит в корне и правится отдельно.
set -e
cd "$(dirname "$0")/.."
{ printf '<!doctype html>\n<html lang="ru">\n'; cat ../prototype/kletka.html; printf '\n</html>\n'; } > app/index.html
cp ../prototype/art/*.webp art/
echo "app/index.html собран"
