# Setup GSC tier A cho bulk mode

Việc cần làm **một lần** để `--bulk` lấy được keyword thật từ Google Search Console. Xong bước 5 thì tier A chạy; chưa xong thì bulk vẫn chạy bằng tier B/C.

> **Không paste credential vào chat.** Lưu key ra file, rồi chỉ cần nói "xong" — script tự đọc theo đường dẫn cố định.

## Dùng Service Account, không dùng OAuth

| | Service Account | OAuth desktop |
|---|---|---|
| Refresh token | **không có** — key JSON dùng mãi | hết hạn **7 ngày** khi app còn ở chế độ Testing |
| Chạy script | không cần browser | phải mở browser lần đầu, hết hạn lại mở lại |
| Setup Workspace MCP trước đây | — | **tắc đúng ở chỗ refresh token** |

Chọn Service Account. Không cần domain-wide delegation — chỉ cần thêm email service account làm user của property trong Search Console.

## Bước 1 — Tạo project + bật API

1. Vào https://console.cloud.google.com/
2. Tạo project mới (hoặc dùng project cũ đã có sẵn cho Workspace MCP).
3. Vào **APIs & Services → Library**, tìm **Google Search Console API**, bấm **Enable**.

## Bước 2 — Tạo Service Account + key JSON

1. **APIs & Services → Credentials → Create credentials → Service account**
2. Đặt tên bất kỳ (vd `gsc-reader`), bấm **Create and continue**.
3. Phần "Grant this service account access to project" → **Skip** (không cần role GCP nào; quyền cấp ở Search Console, không ở GCP).
4. Bấm vào service account vừa tạo → tab **Keys** → **Add key → Create new key → JSON** → tải file về.
5. **Copy email của service account** — dạng `gsc-reader@<project-id>.iam.gserviceaccount.com`. Bước 3 cần email này.

## Bước 3 — Cấp quyền trong Search Console

1. Vào https://search.google.com/search-console
2. Chọn property `webnovel.vn` → **Settings → Users and permissions**
3. **Add user** → dán email service account ở bước 2 → quyền **Full** (hoặc **Restricted** cũng đủ đọc; Full an toàn hơn để khỏi lỗi phân quyền).

Nếu bỏ bước này thì API trả **403** dù key JSON đúng.

## Bước 4 — Đặt key vào đúng chỗ

Cùng quy ước với ImgBB key đang dùng (`~/.config/imgbb/api_key`):

**macOS / Linux**
```bash
mkdir -p ~/.config/gsc
mv ~/Downloads/<tên-file-tải-về>.json ~/.config/gsc/service-account.json
chmod 600 ~/.config/gsc/service-account.json
```

**Windows (Git Bash)**
```bash
mkdir -p ~/.config/gsc
mv /c/Users/$USERNAME/Downloads/<tên-file-tải-về>.json ~/.config/gsc/service-account.json
```

Hoặc set env `GSC_SERVICE_ACCOUNT` trỏ tới file nếu muốn để chỗ khác.

**File này nằm ngoài repo skill** nên không có nguy cơ commit lên GitHub. Đừng move nó vào trong thư mục skill.

## Bước 5 — Kiểm tra (chạy tối nay)

Paste nguyên khối này vào terminal. Nó tự thử **cả 2 dạng property** và in ra dạng nào đúng:

```bash
py -3 - <<'PY'
import sys, json, pathlib
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import date, timedelta

key = pathlib.Path.home() / ".config" / "gsc" / "service-account.json"
print("key file:", key, "->", "OK" if key.is_file() else "KHONG THAY")
if not key.is_file(): sys.exit(1)
print("service account:", json.loads(key.read_text())["client_email"])

cred = service_account.Credentials.from_service_account_file(
    str(key), scopes=["https://www.googleapis.com/auth/webmasters.readonly"])
sc = build("searchconsole", "v1", credentials=cred, cache_discovery=False)

print("\n--- property doc duoc ---")
try:
    for s in (sc.sites().list().execute().get("siteEntry") or []):
        print(f"  {s['siteUrl']:40} {s.get('permissionLevel')}")
except Exception as e:
    print("  loi list sites:", type(e).__name__, str(e)[:200])

end = date.today() - timedelta(days=3)      # GSC tre 2-3 ngay
start = end - timedelta(days=90)
for prop in ["sc-domain:webnovel.vn", "https://webnovel.vn/"]:
    try:
        r = sc.searchanalytics().query(siteUrl=prop, body={
            "startDate": str(start), "endDate": str(end),
            "dimensions": ["query"], "rowLimit": 10}).execute()
        rows = r.get("rows") or []
        print(f"\nOK  {prop}  -> {len(rows)} query mau")
        for x in rows[:10]:
            print(f"     {x['keys'][0][:55]:55} imp={x['impressions']:>6}")
    except Exception as e:
        print(f"\nFAIL {prop}  {type(e).__name__}: {str(e)[:150]}")
PY
```

**Đọc kết quả:**
- Dòng `OK sc-domain:webnovel.vn` → property dạng **Domain**, script dùng `sc-domain:webnovel.vn`.
- Dòng `OK https://webnovel.vn/` → property dạng **URL-prefix**, script dùng đúng URL đó.
- Cả hai FAIL với **403** → chưa làm bước 3, hoặc email thêm vào Search Console khác email trong key.
- Cả hai FAIL với **404** → sai dạng property; xem lại phần "property đọc được" ở trên in ra gì.

## Sau khi xong, nói gì

Chỉ cần nhắn: **"GSC xong, property dạng `<dán đúng dòng OK ở trên>`"**.

Không cần gửi file JSON, không cần gửi email service account, không cần paste key.

## Tier A sẽ query thế nào

Ghi lại đây để lúc viết `scripts/keywords.py` không phải tra lại:

```python
sc.searchanalytics().query(siteUrl=PROPERTY, body={
    "startDate": "...", "endDate": "...",       # GSC trễ 2-3 ngày, có data 16 tháng
    "dimensions": ["query"],
    "dimensionFilterGroups": [{"filters": [
        {"dimension": "page", "operator": "equals", "expression": URL_TRUYEN}
    ]}],
    "rowLimit": 25000,                          # max của API
}).execute()
```

- **Lọc theo `page`** = URL truyện/danh mục đang được backlink tới → ra đúng query mà URL đó thật sự có impression. Đây là thứ hơn hẳn tier C (suy luận).
- URL mới / ít traffic → ít hoặc không có row. **Fallback:** bỏ filter `page`, query toàn site rồi lọc query nào chứa tên danh mục.
- Sort theo `impressions` giảm dần, cắt lấy N keyword đầu sau khi dedup + lọc liên quan.
- Trong manifest, keyword từ nguồn này ghi `kw_source = gsc`.

## Nhớ

- Key JSON là credential — không commit, không paste vào chat, không đưa lên Drive dùng chung.
- Cần lặp lại bước 4 ở **mỗi máy** (Windows và MacBook mỗi máy 1 bản key ở `~/.config/gsc/`). Key không đi theo git.
- Muốn thu hồi: xoá key trong GCP Console → tab Keys, hoặc xoá user trong Search Console.
