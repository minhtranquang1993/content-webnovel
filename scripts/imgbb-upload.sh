#!/usr/bin/env bash
# Upload 1 ảnh lên ImgBB, in ra direct URL (stdout).
# Usage: imgbb-upload.sh <path-to-image> [name-without-ext]
#
# Key resolution (theo thứ tự):
#   1. $IMGBB_API_KEY
#   2. file $IMGBB_API_KEY_FILE (nếu set)
#   3. file ~/.config/imgbb/api_key
#
# Exit codes:
#   0 = OK (stdout = https://i.ibb.co/...)
#   2 = thiếu arg / file ảnh không tồn tại
#   3 = thiếu API key
#   4 = upload fail / response không có url

set -euo pipefail

IMG_PATH="${1:-}"
NAME="${2:-}"

if [[ -z "$IMG_PATH" ]]; then
  echo "Usage: imgbb-upload.sh <path-to-image> [name]" >&2
  exit 2
fi

if [[ ! -f "$IMG_PATH" ]]; then
  echo "ERROR: file not found: $IMG_PATH" >&2
  exit 2
fi

KEY="${IMGBB_API_KEY:-}"
if [[ -z "$KEY" && -n "${IMGBB_API_KEY_FILE:-}" && -f "$IMGBB_API_KEY_FILE" ]]; then
  KEY="$(tr -d '[:space:]' < "$IMGBB_API_KEY_FILE")"
fi
if [[ -z "$KEY" && -f "$HOME/.config/imgbb/api_key" ]]; then
  KEY="$(tr -d '[:space:]' < "$HOME/.config/imgbb/api_key")"
fi
if [[ -z "$KEY" ]]; then
  echo "ERROR: missing ImgBB API key. Set IMGBB_API_KEY or put key in ~/.config/imgbb/api_key" >&2
  exit 3
fi

# Multipart file upload (@path) — tránh base64 làm nổ argv ("Argument list too long")
FORM=(-F "key=$KEY" -F "image=@${IMG_PATH}")
if [[ -n "$NAME" ]]; then
  FORM+=(-F "name=$NAME")
fi

RESP="$(curl -sS -X POST "https://api.imgbb.com/1/upload" "${FORM[@]}" 2>&1)" || {
  echo "ERROR: curl upload failed: $RESP" >&2
  exit 4
}

# Parse display_url / url bằng grep+sed (không phụ thuộc jq/python)
URL="$(printf '%s' "$RESP" | grep -oE '"display_url"[[:space:]]*:[[:space:]]*"[^"]+"' | head -1 | sed -E 's/.*"display_url"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/' | sed 's/\\//g')"
if [[ -z "$URL" ]]; then
  URL="$(printf '%s' "$RESP" | grep -oE '"url"[[:space:]]*:[[:space:]]*"https://i\.ibb\.co[^"]+"' | head -1 | sed -E 's/.*"url"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/' | sed 's/\\//g')"
fi

if [[ -z "$URL" || "$URL" != https://* ]]; then
  echo "ERROR: no image URL in ImgBB response: $RESP" >&2
  exit 4
fi

printf '%s\n' "$URL"
