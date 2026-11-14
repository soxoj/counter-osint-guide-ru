#!/usr/bin/env bash
# Собирает книгу из текста руководства: HTML, FB2, EPUB и PDF.
#   tools/build.sh ru            — русская книга из этого репозитория
#   tools/build.sh en ../counter-osint-guide-en
set -euo pipefail

LANG_CODE="${1:-ru}"
REPO="${2:-$(cd "$(dirname "$0")/.." && pwd)}"
OUT="${OUT:-$(cd "$REPO/.." && pwd)/build/$LANG_CODE}"
DATE="${DATE:-$(LC_ALL=C date +'%d.%m.%Y')}"

PANDOC="${PANDOC:-$(command -v pandoc || true)}"
if [ -z "$PANDOC" ]; then
  PANDOC=$(uvx --from pypandoc-binary python -c 'import pypandoc; print(pypandoc.get_pandoc_path())')
fi
command -v wkhtmltopdf >/dev/null || { echo "нужен wkhtmltopdf"; exit 1; }

case "$LANG_CODE" in
  ru) TITLE="Контр-ОСИНТ: руководство по приватности" ;;
  en) TITLE="Counter-OSINT: a guide to protecting your personal data" ;;
  *)  echo "язык: ru или en"; exit 1 ;;
esac
NAME="counter-osint-$LANG_CODE"

BRANCH=$(git -C "$REPO" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "не git")
DIRTY=$(git -C "$REPO" status --porcelain 2>/dev/null | wc -l)
echo "источник: $REPO"
echo "ветка: $BRANCH, несохранённых изменений: $DIRTY"
[ "$BRANCH" = "main" ] || [ "$BRANCH" = "HEAD" ] || echo "ВНИМАНИЕ: сборка идёт не из main"

mkdir -p "$OUT"
python3 "$(dirname "$0")/build-book.py" "$REPO" "$OUT" --lang "$LANG_CODE" --date "$DATE"
cp "$(dirname "$0")/large.css" "$OUT/large.css"
cd "$OUT"

"$PANDOC" book.md -o "$NAME.html" -s --toc --toc-depth=2 --embed-resources \
  --css=large.css --metadata title="$TITLE" --metadata lang="$LANG_CODE"
"$PANDOC" book.md -o "$NAME.fb2" --metadata title="$TITLE" --metadata lang="$LANG_CODE"
"$PANDOC" book.md -o "$NAME.epub" --toc --metadata title="$TITLE" --metadata lang="$LANG_CODE"
wkhtmltopdf --enable-local-file-access --margin-top 18mm --margin-bottom 18mm \
  --footer-center '[page]' --footer-font-size 10 "$NAME.html" "$NAME.pdf" >/dev/null 2>&1

ls -la "$NAME".{pdf,fb2,epub} | awk '{printf "  %-28s %6.1f МБ\n", $9, $5/1048576}'
