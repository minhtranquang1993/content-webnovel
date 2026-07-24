#!/usr/bin/env bash
# scrape-chapters.sh — Đọc nội dung chương thật của 1 truyện webnovel.vn cho
# subtype `review-short` của skill content-webnovel.
#
# Chọn ~10 chương rải đều trong vùng free (1-20) theo hash slug (stride-7,
# deterministic/tái tạo), fetch + classify từng chương (FREE/LOCKED/không tồn tại),
# in nội dung các chương đọc được. KHÔNG bịa — chương khóa/không tồn tại thì loại.
#
# Usage: bash scrape-chapters.sh "<url truyện>"
# Output: khối KEY<TAB>value + các block chương phân tách bằng "<<<ENDCHAP>>>".
# Exit: 0 OK (>=2 chương free) · 2 URL sai · 3 chương 1 không đọc được (gợi ý intro)
#       · 4 đọc được <2 chương free (route intro)

set -uo pipefail

URL="${1:-}"

if [ -z "$URL" ]; then
  echo "ERROR: thiếu URL. Usage: bash scrape-chapters.sh \"<url truyện>\"" >&2
  exit 2
fi

# Chỉ chấp nhận webnovel.vn
case "$URL" in
  http://webnovel.vn/*|https://webnovel.vn/*|http://www.webnovel.vn/*|https://www.webnovel.vn/*) ;;
  *)
    echo "ERROR: URL không thuộc webnovel.vn — $URL" >&2
    exit 2
    ;;
esac

# Tìm Python (Windows: py -3; *nix: python3/python)
if command -v py >/dev/null 2>&1; then PY="py -3"
elif command -v python3 >/dev/null 2>&1; then PY="python3"
elif command -v python >/dev/null 2>&1; then PY="python"
else
  echo "ERROR: không tìm thấy Python để parse chương." >&2
  exit 2
fi

PYTHONUTF8=1 PYTHONIOENCODING=utf-8 $PY - "$URL" <<'PYEOF'
import sys, re, html, subprocess, time

URL = sys.argv[1].rstrip('/')
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

CEIL = 20          # trần paywall fiction đã verify
K = 10             # số candidate rải trong [1, CEIL]
STRIDE = 7         # coprime với 20 -> 10 số phân biệt, mixed-parity, đổi theo hash
WORD_MIN = 200     # >WORD_MIN từ = FREE; ~11 từ = teaser (locked)
EXPAND = [30, 40]  # probe mở rộng khi chương 20 free (ý user: free >20 -> chương cao)

def err(msg, code):
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)

# slug = phần path cuối của URL truyện
m = re.match(r'https?://(?:www\.)?webnovel\.vn/([^/]+)/?$', URL + '/')
if not m:
    # URL có thể là URL truyện không trailing; thử lấy segment đầu sau domain
    m = re.match(r'https?://(?:www\.)?webnovel\.vn/([^/]+)', URL)
if not m:
    err(f"không tách được slug truyện từ URL — {URL}", 2)
slug = m.group(1)

def fetch(n):
    """Trả (http_code, word_count, text). Chương không tồn tại -> code 302/3xx, text ''."""
    url = f"https://webnovel.vn/{slug}/chuong-{n}"
    try:
        p = subprocess.run(
            ["curl", "-sS", "-A", UA, "--compressed", "--max-time", "30",
             "-w", "\n__HTTP__%{http_code}", url],
            capture_output=True, timeout=60,
        )
    except Exception:
        return (0, 0, "")
    raw = p.stdout.decode("utf-8", "ignore")
    code = "0"
    mc = re.search(r'__HTTP__(\d+)\s*$', raw)
    if mc:
        code = mc.group(1)
        raw = raw[:mc.start()]
    if not raw.strip():
        return (int(code) if code.isdigit() else 0, 0, "")
    mm = re.search(r'<div id="chapter-c"[^>]*>(.*)', raw, flags=re.S)
    if not mm:
        return (int(code) if code.isdigit() else 0, 0, "")
    inner = re.split(r'</article|reader__nav|reader-tools|reader-drawer|unlock-card|<footer|<script',
                     mm.group(1))[0]
    inner = re.sub(r'<br\s*/?>', '\n', inner)
    inner = re.sub(r'</p>', '\n\n', inner)
    text = re.sub(r'<[^>]+>', '', inner)
    text = html.unescape(text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return (int(code) if code.isdigit() else 0, len(text.split()), text)

def classify(n, retry=True):
    """FREE -> ('free', words, text) · LOCKED -> ('locked',...) · NOEXIST -> ('noexist',...)."""
    code, words, text = fetch(n)
    if code and code != 200:      # 302/404... = chương không tồn tại
        return ('noexist', words, text)
    if words > WORD_MIN:
        return ('free', words, text)
    # words thấp: có thể teaser thật HOẶC rate-limit false-lock -> retry 1 lần
    if retry:
        time.sleep(4)
        code2, words2, text2 = fetch(n)
        if code2 and code2 != 200:
            return ('noexist', words2, text2)
        if words2 > WORD_MIN:
            return ('free', words2, text2)
        return ('locked', words2, text2)
    return ('locked', words, text)

# --- Sinh candidate: stride-7 theo hash slug, luôn ép {1, 20} ---
h = sum(ord(c) for c in slug)
cands = [1 + ((h + STRIDE * i) % CEIL) for i in range(K)]
cands = sorted(set(cands) | {1, CEIL})

# --- Probe chương 1 TRƯỚC (fail-fast) ---
state1, w1, t1 = classify(1)
if state1 != 'free':
    reason = "chương 1 không tồn tại (URL sai?)" if state1 == 'noexist' else "chương 1 bị khóa"
    err(f"{reason} — truyện '{slug}' không đọc được chương free; hãy dùng review intro.", 3)

free = {1: (w1, t1)}
time.sleep(2)

# --- Classify các candidate còn lại ---
rest = [n for n in cands if n != 1]
for idx, n in enumerate(rest):
    st, w, t = classify(n)
    if st == 'free':
        free[n] = (w, t)
    time.sleep(2 if idx < len(rest) - 1 else 0)

# --- Mở rộng khi chương 20 free (lấy chương số cao) ---
if CEIL in free:
    for n in EXPAND:
        time.sleep(2)
        st, w, t = classify(n)
        if st == 'free':
            free[n] = (w, t)
        else:
            break  # mốc đầu không free -> dừng mở rộng

# --- Output ---
chosen = sorted(free)
print(f"SLUG\t{slug}")
print(f"URL\thttps://webnovel.vn/{slug}/")
print(f"CANDIDATES\t{' '.join(str(c) for c in cands)}")
print(f"FREE_CHAPTERS\t{' '.join(str(c) for c in chosen)}")
print(f"FREE_COUNT\t{len(chosen)}")

if len(chosen) < 2:
    print("NOTE\tĐọc được <2 chương free — không đủ liệu cho review-short, hãy dùng review intro.")
    for n in chosen:
        w, t = free[n]
        print(f"<<<CHAP\t{n}\t{w}>>>")
        print(t)
        print("<<<ENDCHAP>>>")
    raise SystemExit(4)

for n in chosen:
    w, t = free[n]
    print(f"<<<CHAP\t{n}\t{w}>>>")
    print(t)
    print("<<<ENDCHAP>>>")
PYEOF
