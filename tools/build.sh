#!/bin/sh
# Собирает сервис в app/index.html и кабинет ученика в u/index.html из прототипа и копирует картинки.
# Главная страница (index.html) лежит в корне и правится отдельно.
set -e
cd "$(dirname "$0")/.."
{ printf '<!doctype html>\n<html lang="ru">\n'; cat ../prototype/kletka.html; printf '\n</html>\n'; } > app/index.html
mkdir -p u && cp app/index.html u/index.html
cp ../prototype/art/*.webp art/
echo "app/ и u/ собраны"
