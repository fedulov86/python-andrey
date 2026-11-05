#!/bin/sh
# Собрать сайт, проверить примеры кода и выложить на GitHub Pages.
set -e
cd "$(dirname "$0")"
python3 build.py
python3 check.py
git add -A
git commit -m "${1:-Обновление курса}" || true
git push origin main
git subtree push --prefix site origin gh-pages
