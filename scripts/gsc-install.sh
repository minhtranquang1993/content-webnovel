#!/usr/bin/env bash
# gsc-install.sh — Tạo venv riêng cho tier A (GSC API).
#
# Vì sao cần venv:
#   - python homebrew là EXTERNALLY-MANAGED (PEP 668) → không pip install thẳng.
#   - Trên máy này python@3.14.6 homebrew còn có `pyexpat` HỎNG (link sai libexpat
#     của macOS, thiếu symbol _XML_SetAllocTrackerActivationThreshold) → chính
#     `python3 -m venv` cũng fail ở bước ensurepip.
#   Nên: ưu tiên `uv` (tự dùng/tải interpreter lành). Không có uv thì thử venv thường.
#
# Venv nằm NGOÀI skill dir (skill dir là git repo public).
#
# Usage: bash gsc-install.sh
# Env:   WEBNOVEL_GSC_VENV    chỗ đặt venv (default ~/.local/share/webnovel-gsc/venv)
#        WEBNOVEL_GSC_CONFIG  chỗ đặt credential (default ~/.config/webnovel-gsc)

set -euo pipefail

VENV="${WEBNOVEL_GSC_VENV:-$HOME/.local/share/webnovel-gsc/venv}"
CONFIG_DIR="${WEBNOVEL_GSC_CONFIG:-$HOME/.config/webnovel-gsc}"
PY_PIN="3.13"

# Pin cứng — khỏi bị bản mới đổi hành vi giữa 2 lần chạy.
PKGS=(
  "google-api-python-client==2.198.0"
  "google-auth==2.56.2"
  "google-auth-oauthlib==1.4.0"
)

echo "==> venv: $VENV"
mkdir -p "$(dirname "$VENV")"

if command -v uv >/dev/null 2>&1; then
  echo "    dùng uv ($(uv --version))"
  uv venv --python "$PY_PIN" "$VENV"
  uv pip install --quiet --python "$VENV/bin/python3" "${PKGS[@]}"
else
  echo "    không có uv → thử python3 -m venv"
  if ! python3 -m venv "$VENV" 2>/tmp/gsc-venv-err.txt; then
    echo
    echo "LỖI: python3 -m venv thất bại:" >&2
    tail -5 /tmp/gsc-venv-err.txt >&2
    echo >&2
    echo "Nếu lỗi nhắc 'pyexpat' hoặc '_XML_SetAllocTrackerActivationThreshold'" >&2
    echo "thì python homebrew đang hỏng. Chọn 1:" >&2
    echo "  brew reinstall expat python@3.14      # vá python" >&2
    echo "  brew install uv                      # rồi chạy lại script này" >&2
    exit 1
  fi
  "$VENV/bin/python3" -m pip install --quiet --upgrade pip
  "$VENV/bin/python3" -m pip install --quiet "${PKGS[@]}"
fi

echo "==> kiểm import"
"$VENV/bin/python3" - <<'PY'
from importlib.metadata import version
import pyexpat  # noqa: F401 — chỗ python homebrew hỏng, xác nhận venv lành
from google.oauth2.service_account import Credentials  # noqa: F401
from google.oauth2.credentials import Credentials as UserCreds  # noqa: F401
from google.auth.transport.requests import Request  # noqa: F401
from googleapiclient.discovery import build  # noqa: F401
from googleapiclient.errors import HttpError  # noqa: F401
from google_auth_oauthlib.flow import InstalledAppFlow  # noqa: F401
import sys
print(f"    python {sys.version.split()[0]}")
for p in ("google-api-python-client", "google-auth", "google-auth-oauthlib"):
    print(f"    {p} == {version(p)}")
print("    OK")
PY

mkdir -p "$CONFIG_DIR"
chmod 700 "$CONFIG_DIR"
echo "==> thư mục credential: $CONFIG_DIR (chmod 700)"

echo
echo "XONG. Còn 1 bước: đặt credential vào $CONFIG_DIR/"
echo "  service-account.json   (khuyến nghị)  — rồi thêm email service account vào GSC"
echo "  oauth-client.json      (thay thế)     — lần đầu chạy sẽ mở browser"
echo
echo "Kiểm bằng:"
echo "  python3 ~/.claude/skills/content-webnovel/scripts/gsc-api.py --list-sites"
