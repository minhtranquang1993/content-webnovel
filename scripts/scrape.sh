#!/usr/bin/env bash
# scrape.sh — Live-scrape webnovel.vn cho skill content-webnovel.
# Nhận 1 URL, tự nhận diện loại trang (story | category | homepage),
# bóc dữ liệu thật rồi in ra khối KEY: value dễ đọc.
# KHÔNG bịa — thiếu dữ liệu lõi thì exit != 0 với thông báo lỗi rõ ràng.
#
# Usage: bash scrape.sh "<url>"
# Output: các dòng dạng "KEY<TAB>value". PAGE_TYPE luôn là dòng đầu khi thành công.

set -uo pipefail

URL="${1:-}"
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

if [ -z "$URL" ]; then
  echo "ERROR: thiếu URL. Usage: bash scrape.sh \"<url>\"" >&2
  exit 2
fi

# Chuẩn hoá: chỉ chấp nhận webnovel.vn
case "$URL" in
  http://webnovel.vn/*|https://webnovel.vn/*|http://www.webnovel.vn/*|https://www.webnovel.vn/*) ;;
  *)
    echo "ERROR: URL không thuộc webnovel.vn — $URL" >&2
    exit 2
    ;;
esac

# Tải HTML (browser UA; WebFetch bị 403 nên phải dùng curl)
HTML="$(curl -sS -A "$UA" --compressed --max-time 30 "$URL" 2>/dev/null)"
CURL_RC=$?
if [ $CURL_RC -ne 0 ] || [ -z "$HTML" ]; then
  echo "ERROR: không tải được URL (curl rc=$CURL_RC) — $URL" >&2
  exit 3
fi

# Helper: lấy nội dung thuộc tính content của 1 meta property/name
meta_prop() { # $1 = property value
  printf '%s' "$HTML" | grep -o "<meta property=\"$1\"[^>]*content=\"[^\"]*\"" | head -1 | sed -E 's/.*content="([^"]*)".*/\1/'
}
meta_name() { # $1 = name value
  printf '%s' "$HTML" | grep -o "<meta name=\"$1\"[^>]*content=\"[^\"]*\"" | head -1 | sed -E 's/.*content="([^"]*)".*/\1/'
}
# Gỡ tag HTML + nén khoảng trắng
strip_tags() { sed -E 's/<[^>]+>//g' | sed -E 's/&amp;/\&/g; s/&quot;/"/g; s/&#39;/'"'"'/g; s/&nbsp;/ /g' | tr -s ' \t' ' ' ; }

# Lấy URL path để phát hiện homepage
PATH_ONLY="$(printf '%s' "$URL" | sed -E 's#https?://[^/]+##; s/[?#].*$//')"

OG_TYPE="$(meta_prop 'og:type')"

# ---------- ROUTER ----------
# Dùng shell glob (case) thay vì `grep -q` trên pipe: với input lớn, grep -q thoát
# sớm gây SIGPIPE (141), kết hợp `set -o pipefail` làm điều kiện if luôn fail.
if printf '%s' "$OG_TYPE" | grep -qi 'book' && [[ "$HTML" == *book-detail__title* ]]; then
  PAGE_TYPE="story"
elif [[ "$HTML" == *"page page--category"* ]] && [[ "$HTML" == *page__title* ]]; then
  PAGE_TYPE="category"
elif [ "$PATH_ONLY" = "/" ] || [ -z "$PATH_ONLY" ]; then
  PAGE_TYPE="homepage"
else
  echo "ERROR: không nhận diện được loại trang (story/category/homepage) — $URL" >&2
  exit 4
fi

# ---------- STORY ----------
if [ "$PAGE_TYPE" = "story" ]; then
  TITLE="$(meta_prop 'og:title')"
  [ -z "$TITLE" ] && TITLE="$(printf '%s' "$HTML" | grep -o '<h1 id="book-detail-title"[^>]*>[^<]*</h1>' | strip_tags)"
  AUTHOR="$(printf '%s' "$HTML" | grep -o '<p class="book-detail__author[^"]*"[^>]*>.*' | head -1 | grep -o '<a [^>]*>[^<]*</a>' | head -1 | strip_tags)"
  # Genres: các anchor trong book-detail__genres
  GENRES_BLOCK="$(printf '%s' "$HTML" | tr '\n' ' ' | grep -o '<div class="book-detail__genres">.*</div>' | head -1)"
  GENRES="$(printf '%s' "$HTML" | grep -o '<a class="genre"[^>]*>[^<]*</a>' | strip_tags | paste -sd '|' -)"
  if [ -z "$GENRES" ]; then
    GENRES="$(printf '%s' "$HTML" | grep -o 'class="genre"[^>]*>[^<]*<' | sed -E 's/.*>([^<]*)<.*/\1/' | paste -sd '|' -)"
  fi
  SUMMARY="$(printf '%s' "$HTML" | tr '\n' ' ' | grep -o '<div class="book-detail__summary">.*' | sed -E 's#</div>.*##' | sed -E 's/<br[^>]*>/\n/g' | strip_tags)"
  STATUS="$(printf '%s' "$HTML" | grep -o 'status__text">[^<]*<' | sed -E 's/status__text">([^<]*)<.*/\1/' | grep -v '^ *$' | head -1)"

  if [ -z "$TITLE" ]; then
    echo "ERROR: story nhưng không bóc được tên truyện — $URL" >&2
    exit 5
  fi

  printf 'PAGE_TYPE\tstory\n'
  printf 'URL\t%s\n' "$URL"
  printf 'TITLE\t%s\n' "$TITLE"
  printf 'AUTHOR\t%s\n' "$AUTHOR"
  printf 'GENRES\t%s\n' "$GENRES"
  printf 'STATUS\t%s\n' "$STATUS"
  printf 'SUMMARY\t%s\n' "$(printf '%s' "$SUMMARY" | tr '\n' ' ' | sed -E 's/©.*$//' | tr -s ' ')"
  exit 0
fi

# ---------- CATEGORY ----------
if [ "$PAGE_TYPE" = "category" ]; then
  CAT_TITLE="$(printf '%s' "$HTML" | grep -o '<h1 id="page-title"[^>]*>[^<]*</h1>' | head -1 | strip_tags)"
  [ -z "$CAT_TITLE" ] && CAT_TITLE="$(printf '%s' "$HTML" | grep -o '<h1[^>]*class="page__title"[^>]*>[^<]*</h1>' | head -1 | strip_tags)"
  CAT_DESC="$(meta_name 'description')"

  if [ -z "$CAT_TITLE" ]; then
    echo "ERROR: category nhưng không bóc được tiêu đề danh mục — $URL" >&2
    exit 5
  fi

  printf 'PAGE_TYPE\tcategory\n'
  printf 'URL\t%s\n' "$URL"
  printf 'CAT_TITLE\t%s\n' "$CAT_TITLE"
  printf 'CAT_DESC\t%s\n' "$CAT_DESC"

  # Danh sách truyện: catx-card__title > a (tên + link), kèm desc nếu có
  printf '%s' "$HTML" | tr '\n' ' ' \
    | grep -o '<h2 class="catx-card__title"[^>]*><a href="[^"]*" title="[^"]*">[^<]*</a>' \
    | sed -E 's#.*href="([^"]*)" title="[^"]*">([^<]*)</a>#STORY\t\2\t\1#' \
    | awk '!seen[$0]++' \
    | head -30

  exit 0
fi

# ---------- HOMEPAGE ----------
if [ "$PAGE_TYPE" = "homepage" ]; then
  HOME_TITLE="$(printf '%s' "$HTML" | grep -o '<title>[^<]*</title>' | head -1 | strip_tags)"
  HOME_DESC="$(meta_name 'description')"

  printf 'PAGE_TYPE\thomepage\n'
  printf 'URL\t%s\n' "$URL"
  printf 'HOME_TITLE\t%s\n' "$HOME_TITLE"
  printf 'HOME_DESC\t%s\n' "$HOME_DESC"
  # Một vài thể loại nổi bật để bio homepage kêu gọi
  printf '%s' "$HTML" | grep -o '<a href="https://webnovel.vn/[a-z0-9-]*/" title="truyện [^"]*"' \
    | sed -E 's#.*webnovel.vn/([^/]*)/" title="(truyện [^"]*)"#GENRE_LINK\t\2\t\1#' \
    | awk '!seen[$0]++' | head -15
  exit 0
fi
