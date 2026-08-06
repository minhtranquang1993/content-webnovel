# Cheat sheet — `/content-webnovel`

Cách input nhanh cho skill content marketing Webnovel.vn.  
**Skill active:** `~/.claude/skills/content-webnovel/` — đây cũng chính là git repo (commit/push tại chỗ, không có bước copy)  
**Repo:** https://github.com/minhtranquang1993/content-webnovel  
**Chi tiết đầy đủ:** xem `SKILL.md`.

> Khi đổi cú pháp / tham số / hành vi input của skill → **update file này** cùng lúc với `SKILL.md`.

---

## Cú pháp chuẩn

```
/content-webnovel <type> [subtype] <url|tên> [keyword="<kw>"] [--site <domain>[,<domain2>,…] | --site-pool] [--bulk N] [--dry-run]
/content-webnovel super-cate [--dry-run]        # 19 bài toplist / 19 danh mục — không cần URL
```

Freeform cũng được: gửi URL + mô tả bằng lời → skill tự map.

---

## Tham số

| Flag / form | Bắt buộc? | Dùng cho | Ý nghĩa |
|---|---|---|---|
| `--site <domain>` | **Có** với mọi `pbn`; **không dùng** cho `blog20` | PBN | Domain đăng bài → ghép `https://{site}/{slug}/`. **Kèm `--bulk`: nhiều domain cách nhau bằng phẩy** → 1 bài 1 domain theo thứ tự |
| `--site-pool` | Tuỳ chọn | chỉ kèm `--bulk` + `pbn` | Tự lấy N domain từ `data/pbn-domains.txt` — khỏi gõ tay. Nói *"5 bài 5 domain"* là đủ |
| `keyword="..."` hoặc `--kw "..."` | Tuỳ chọn | `pbn toplist` / `blog20 toplist` (chủ yếu) + `forum` | Primary keyword. **Chỉ để viết**, không đổi list truyện |
| `--bulk N` | Tuỳ chọn | `pbn` / `blog20` / `forum` (**không** `bio`) | Sinh N bài, mỗi bài 1 keyword riêng, **ghi file `.txt`** thay vì in chat. Xem **BULK MODE** |
| `--dry-run` | Tuỳ chọn | chỉ kèm `--bulk` | In ma trận kế hoạch rồi DỪNG — không sinh bài, không ghi file |
| `--gsc-api` | Tuỳ chọn | chỉ kèm `--bulk` | **Tier A** — tự pull query thật từ GSC API, khỏi export tay. Cài 1 lần: `scripts/gsc-install.sh` + credential |
| `--gsc-csv <file>` | Tuỳ chọn | chỉ kèm `--bulk` | **Tier B** — export Search Console (CSV/TSV/**ZIP tải thẳng**) anh gửi tay |
| `--suggest` | Tuỳ chọn | chỉ kèm `--bulk` | **Tier S** — keyword liên quan/LSI từ autocomplete Google/Bing/DDG/YouTube. **Không cần credential, không cần quyền GSC** |
| `--suggest-depth 2` | Tuỳ chọn | chỉ kèm `--suggest` | Thêm mở rộng a-z → nhiều keyword đuôi dài hơn (~160 request thay vì 72) |

**Tương thích input cũ:** nếu vẫn truyền `--lo <nhãn>`, skill bỏ qua cả flag và giá trị; không hỏi lại, không báo lỗi, không dùng để lọc dữ liệu.

**Không còn `--img`.** Ảnh = ImgBB (`anh_imgbb` trong JSON / `scripts/imgbb-upload.sh`).

**Không cần** `--site`: `bio`, `forum`.
**`pbn` + `--bulk`:** mặc định 1 bài 1 domain → dùng `--site-pool` hoặc `--site a.vn,b.vn,…`. Xem **Domain PBN**.
**`pbn faq`:** cần `--site`.
**`blog20`:** không nhận/hỏi/suy luận `--site` hay domain; không URL/Slug hoặc self-link.

---

## Copy nhanh

```bash
# BIO
/content-webnovel bio https://webnovel.vn/<slug-truyen>/
/content-webnovel bio https://webnovel.vn/<slug-danh-muc>/
/content-webnovel bio https://webnovel.vn/

# PBN REVIEW
/content-webnovel pbn review https://webnovel.vn/<slug-truyen>/ --site <domain>

# PBN REVIEW-SHORT — đọc chương thật (chỉ fiction; non-fiction/khóa → tự route review)
/content-webnovel pbn review-short https://webnovel.vn/<slug-truyen>/ --site <domain>

# PBN TOPLIST — URL danh mục (list bám URL)
/content-webnovel pbn toplist https://webnovel.vn/<slug-danh-muc>/ --site <domain>

# PBN TOPLIST — URL + keyword cùng lúc (khuyến nghị khi muốn SEO chính xác)
/content-webnovel pbn toplist https://webnovel.vn/dien-van/ keyword="truyện điền văn hoàn" --site tonghoixaydungvn.org.vn

# PBN TOPLIST — tên thể loại
/content-webnovel pbn toplist "Tiên Hiệp" --site <domain>

# PBN TOPLIST — tác giả
/content-webnovel pbn toplist "Tối Bạch Đích Ô Nha" --site <domain>

# PBN FAQ
/content-webnovel pbn faq https://webnovel.vn/<slug>/ --site <domain>

# PBN GENRE — giải thích thể loại (URL danh mục hoặc tên thể loại)
/content-webnovel pbn genre https://webnovel.vn/<slug-danh-muc>/ --site <domain>
/content-webnovel pbn genre "Điền Văn" --site <domain>

# PBN VERSUS — so sánh 2 truyện (2 URL / 2 tên / URL danh mục lấy top 2)
/content-webnovel pbn versus https://webnovel.vn/<truyen-a>/ https://webnovel.vn/<truyen-b>/ --site <domain>
/content-webnovel pbn versus https://webnovel.vn/<slug-danh-muc>/ --site <domain>

# PBN GUIDE — cẩm nang người mới (URL danh mục hoặc tên thể loại)
/content-webnovel pbn guide https://webnovel.vn/<slug-danh-muc>/ --site <domain>

# FORUM — 3 post hỏi đáp dài (plain text)
/content-webnovel forum https://webnovel.vn/<slug>/
/content-webnovel forum https://webnovel.vn/<slug-danh-muc>/ keyword="truyện …"

# BLOG20 REVIEW — HTML thuần, không domain/URL/Slug/self-link
/content-webnovel blog20 review https://webnovel.vn/<slug-truyen>/

# BLOG20 REVIEW-SHORT — đọc chương thật, không domain/URL/Slug/self-link
/content-webnovel blog20 review-short https://webnovel.vn/<slug-truyen>/

# BLOG20 TOPLIST — pool/keyword/ảnh/backlink như PBN, nhưng không --site
/content-webnovel blog20 toplist https://webnovel.vn/<slug-danh-muc>/ keyword="truyện …"
/content-webnovel blog20 toplist "<Tên thể loại hoặc tác giả>"

# BLOG20 GENRE / VERSUS / GUIDE — như pbn tương ứng, không --site/URL/Slug/self-link
/content-webnovel blog20 genre https://webnovel.vn/<slug-danh-muc>/
/content-webnovel blog20 versus https://webnovel.vn/<truyen-a>/ https://webnovel.vn/<truyen-b>/
/content-webnovel blog20 guide "<Tên thể loại>"
```

---

## Theo type

### `bio` — 10 biến thể plain text (120–150 ký tự)

Subtype **auto** theo URL.

| Input | Subtype |
|---|---|
| URL truyện | bio tentruyen |
| URL danh mục | bio danhmuc |
| Homepage `/` | bio homepage |

```
/content-webnovel bio https://webnovel.vn/ai-bao-han-tu-tien/
/content-webnovel bio https://webnovel.vn/xuyen-khong/
/content-webnovel bio https://webnovel.vn/
```

### `pbn review` — HTML thuần + meta URL/Slug

```
/content-webnovel pbn review https://webnovel.vn/ai-bao-han-tu-tien/ --site tonghoixaydungvn.org.vn
```

### `pbn review-short` — đọc chương thật, phân tích cụ thể (HTML thuần + meta URL/Slug)

Biến thể review **đọc thật các chương free đầu** (script `scrape-chapters.sh`) → phân tích nhân vật/phân cảnh/thoại có thật + verdict "ấn tượng ban đầu". **Chỉ fiction** — cần `--site`.

```
/content-webnovel pbn review-short https://webnovel.vn/ai-bao-han-tu-tien/ --site tonghoixaydungvn.org.vn
```

- **Non-fiction** (Phát triển bản thân / Tâm linh) → announce + tự route sang `pbn review` intro (không đọc chương).
- Chương 1 khóa/không đọc được, hoặc **<2 chương free** → announce + route `pbn review` intro (tránh bịa).
- H2 phân tích chỉ dùng nội dung chương đã đọc; không spoiler chương chưa đọc; không kết luận toàn tác phẩm.

### `pbn toplist` — HTML thuần + meta URL/Slug

**Pattern chuẩn (URL + keyword):**

```
/content-webnovel pbn toplist https://webnovel.vn/dien-van/ keyword="truyện điền văn hoàn" --site tonghoixaydungvn.org.vn
```

| Thành phần | Vai trò |
|---|---|
| URL danh mục | **Pool list truyện** (filter `danh_muc` trên toàn bộ JSON) |
| `keyword="..."` | **Cách viết SEO** (H1/body) — không đổi list |
| `--site` | Domain bài PBN |

Cùng pattern với tên thể loại / tác giả:

```
/content-webnovel pbn toplist https://webnovel.vn/tien-hiep/ --site tonghoixaydungvn.org.vn
/content-webnovel pbn toplist "Tiên Hiệp" --site fbu.vn
/content-webnovel pbn toplist "Tối Bạch Đích Ô Nha" --site fbu.vn
```

#### Pool sau lọc toàn bộ JSON theo thể loại/tác giả

| Pool | Hành vi |
|---|---|
| `>= 2` | Toplist (Top N, kể cả Top 2) |
| `== 1` | Tự chuyển **review** (announce). Danh mục: dual-entity + link truyện + link danh mục. Tác giả: link truyện + 1 danh mục chính |
| `== 0` | Thể loại → fallback scrape live (không ảnh). Tác giả → dừng, báo crawl thêm |

#### Keyword vs list

- Không có keyword → auto `truyện {tên danh mục}` (vd URL `/dien-van/` → `truyện điền văn`) + biến thể nhẹ.
- Có `keyword="truyện điền văn hoàn"` → primary đúng chuỗi đó; list vẫn truyện **Điền Văn**.

### `pbn faq` — HTML thuần + meta URL/Slug

```
/content-webnovel pbn faq https://webnovel.vn/tien-hiep/ --site fbu.vn
```

Cần `--site`.

### `pbn genre` — giải thích thể loại (HTML thuần + meta URL/Slug)

Bài định nghĩa thể loại + gợi ý N truyện. Input: URL danh mục **hoặc** tên thể loại (+kw). Cần `--site`.

```
/content-webnovel pbn genre https://webnovel.vn/tien-hiep/ --site fbu.vn
/content-webnovel pbn genre "Điền Văn" --site fbu.vn
```

Pool nhỏ (không phải list xếp hạng): 1-2 vẫn viết; pool==0 + input tên (không URL) → dừng + báo crawl. CTA link danh mục chỉ khi có URL thật.

### `pbn versus` — so sánh 2 truyện (HTML thuần + meta URL/Slug)

Input: **2 URL truyện** / **2 tên** (match `tu_khoa`) / **1 URL danh mục** (top 2). Scrape cả 2; input tường minh mà scrape fail → dừng. Bảng so sánh text-only. Backlink 1/truyện. Cần `--site`.

```
/content-webnovel pbn versus https://webnovel.vn/truyen-a/ https://webnovel.vn/truyen-b/ --site fbu.vn
/content-webnovel pbn versus https://webnovel.vn/tien-hiep/ --site fbu.vn
```

### `pbn guide` — cẩm nang người mới (HTML thuần + meta URL/Slug)

Advisory cho người mới (KHÁC genre: không có block "…là gì"). Input: URL danh mục **hoặc** tên thể loại (+kw). Cần `--site`. Pool nhỏ như genre.

```
/content-webnovel pbn guide https://webnovel.vn/tien-hiep/ --site fbu.vn
```

> **Title pool + non-fiction (áp cho review/toplist + subtype mới):** H1 review/toplist xoay theo hash (không còn 1 công thức cứng). ~48% pool là **sách non-fiction** (Phát triển bản thân, Tâm linh) → danh từ tự đổi "truyện"→"sách", tránh "cày/nghiện".

### `forum` — 3 post plain text (hỏi đáp dài 500–1000 chữ)

Mỗi post: **câu hỏi hook** (title) → body 3–5 đoạn → CTA + **1 URL trần** (truyện → link truyện; danh mục → link danh mục). Không HTML, không hashtag, không `--site`.

```
/content-webnovel forum https://webnovel.vn/ngon-tinh/
/content-webnovel forum https://webnovel.vn/ai-bao-han-tu-tien/
/content-webnovel forum https://webnovel.vn/dien-van/ keyword="truyện điền văn full"
```

| Thành phần | Vai trò |
|---|---|
| URL | Scrape + URL CTA |
| `keyword="..."` | Tuỳ chọn — bám hook/body; không có → auto từ tên truyện/thể loại |

Output chat: `### Post 1` … `### Post 3` (3 biến thể khác hook/góc viết).

### `blog20 review|review-short|toplist|genre|versus|guide` — HTML thuần, không domain/URL/Slug/self-link

`blog20` kế thừa nội dung `pbn` subtype cùng tên (HTML 1000–1500 chữ, tra cứu/lọc JSON, keyword, title pool, category-class, backlink Webnovel.vn và ảnh ImgBB; `review-short` đọc chương thật + route non-fiction/khóa/<2-free → `blog20 review` intro). **KHÔNG có `blog20 faq`.** Chỉ khác:

1. Không nhận, hỏi hoặc suy luận `--site` hay domain đăng bài.
2. Không in block `URL:` / `Slug:` và không gợi ý slug.
3. Không chèn self-link trong đoạn mở; backlink Webnovel.vn vẫn giữ nguyên.

```
/content-webnovel blog20 review https://webnovel.vn/ai-bao-han-tu-tien/
/content-webnovel blog20 toplist https://webnovel.vn/dien-van/ keyword="truyện điền văn hoàn"
/content-webnovel blog20 toplist "Tối Bạch Đích Ô Nha"
/content-webnovel blog20 genre https://webnovel.vn/tien-hiep/
/content-webnovel blog20 versus https://webnovel.vn/truyen-a/ https://webnovel.vn/truyen-b/
/content-webnovel blog20 guide "Ngôn Tình"
```

- Pool `>= 2` → toplist; pool `== 1` → tự chuyển `blog20 review`; pool `== 0` → fallback thể loại / dừng với tác giả như PBN.
- `blog20` chỉ là tên type. Số `20` **không** yêu cầu đủ 20 truyện; không padding hoặc bịa thêm truyện.
- Auto-switch từ danh mục: link truyện đúng 1 lần tại CTA + link danh mục đúng 1 lần trong intro/đoạn thể loại; vẫn không có self-link.

---

## SUPER-CATE — 1 lệnh, 19 bài toplist / 19 danh mục khác nhau

```
/content-webnovel super-cate
/content-webnovel super-cate --dry-run      # xem trước ma trận, không ghi gì
```

**Không cần URL, không cần `--site`, không cần `--bulk`.** Ra đúng **10 pbn + 4 blog20 + 5 forum**, tất cả subtype `toplist`, mỗi bài 1 danh mục riêng.

### Luồng 4 bước (thứ tự CỨNG)

```bash
S=~/.claude/skills/content-webnovel/scripts

# 1) lập ma trận → lấy OUT_DIR từ dòng [super-cate] OUT_DIR:
py -3 "$S/super-cate.py" plan

# 2) sinh 19 bài .txt + manifest.tsv  (LLM viết, theo từng dòng plan.tsv)

# 3) verify — PASS hết mới sang bước 4
py -3 "$S/verify-bulk.py" --plan "{OUT_DIR}/plan.tsv" --manifest "{OUT_DIR}/manifest.tsv"

# 4) commit rotation — CHỈ khi verify PASS
py -3 "$S/super-cate.py" commit-usage --plan "{OUT_DIR}/plan.tsv"
```

> **Verify FAIL → KHÔNG chạy bước 4.** Không commit thì lần sau danh mục vẫn được ưu tiên cấp lại.

### Output

```
<Downloads>/webnovel/{YYYY-MM-DD}/
├── plan.tsv          ← allocation đóng băng (chỉ script ghi)
├── manifest.tsv      ← kết quả (chỉ generator ghi)
├── plan/{idx}.json   ← sidecar: danh sách truyện cho từng bài
├── pbn/*.txt         (10 file)
├── blog20/*.txt      (4 file)
└── forum/*.txt       (5 file)
```

Folder ngày đã tồn tại → tự bump `2026-08-06-2`, `-3`.

### Cột trong `plan.tsv`

| Cột | Dùng để |
|---|---|
| `type` | `pbn` / `blog20` / `forum` → viết theo contract tương ứng |
| `cate_name` / `cate_url` / `cate_slug` | danh mục của bài đó |
| `pool` / `n_display` | pool thật / **số truyện phải liệt kê** (pbn+blog20 ≤10, forum ≤7) |
| `keyword` | primary keyword (H1/title/body) |
| `kw_variants` | biến thể rải nhẹ 1-2 lần, KHÔNG lọc lại pool |
| `site` | domain của **chính dòng đó** (chỉ pbn). Rỗng → DỪNG, hỏi user |
| `archetype` / `title_idx` / `noun` | slot biến thể, dùng nguyên, không tự tính hash |
| `plan_file` | sidecar chứa danh sách truyện |

**Truyện lấy TỪ SIDECAR**, không tự tra `truyen-data.json`, không thêm/bớt. Verify đối chiếu — URL ngoài sidecar = FAIL.

### Rotation (không bao giờ bắt đầu từ mục #1)

State: `data/super-cate-usage.json` — danh mục + domain + con trỏ pool + ledger batch.

- **Danh mục / domain:** ưu tiên ít dùng nhất, tie → random. Domain đi hết 29 (~3 batch) mới lặp.
- **Con trỏ pool:** danh mục lặp ở batch sau vẫn ra **list truyện khác** (Tiên Hiệp pool 61 → 6 batch list rời hẳn).
- **Giới hạn:** 20 danh mục hợp lệ / 19 bài mỗi batch ⇒ **từ batch 2 danh mục buộc phải lặp** (list truyện thì không). Muốn danh mục rời hẳn cần ≥38 danh mục hợp lệ.
- Danh mục `pool ≤1` (Tổng Tài, Kiếm Hiệp, Võng Du) **luôn bị loại** — không viết được toplist.

### Update danh mục

```bash
py -3 ~/.claude/skills/content-webnovel/scripts/import-cate.py            # tự tìm CSV trong Downloads
py -3 ~/.claude/skills/content-webnovel/scripts/import-cate.py --dry-run  # xem trước
```

Nạp `data/categories.tsv` từ CSV export sheet. Nhiều dòng cùng URL → gộp 1 danh mục, keyword thành biến thể. **Vừa update sheet → chạy lệnh này trước khi `plan`.**

### Chạy dở giữa đường

`plan.tsv` cũ là nguồn phục hồi: sinh nốt `idx` còn thiếu vào **đúng folder đó**, append tiếp `manifest.tsv` (không tạo lại dòng version), rồi verify + commit.

Chạy `plan` khi folder ngày đã có batch → script **DỪNG** + in `idx` còn thiếu + chỉ đường resume. Muốn batch thứ 2 cùng ngày: `plan --new-batch`.

### Cờ thoát hiểm

| Cờ | Khi nào |
|---|---|
| `plan --new-batch` | cố ý chạy batch thứ 2 trong cùng ngày |
| `plan --ignore-corrupt-state` | state hỏng, chấp nhận rotation sai lượt này |
| `commit-usage --force-reset-state` | state hỏng, ghi lại từ rỗng (copy `.bak` trước) |
| `plan --seed N` | tái lập tie-break (chỉ đúng khi state+data chưa đổi) |

### `forum toplist` khác `forum` thường

| | `forum` (thường) | `forum toplist` (super-cate) |
|---|---|---|
| Số post | 3 post / lần | **1 post / file** |
| URL | đúng **1** URL trần | **N URL truyện + 1 URL danh mục cuối** = N+1 |
| Chữ | 500–1000 / post | 500–1000 |
| Format | plain text | plain text |

---

## BULK MODE — `--bulk N`

Sinh **N bài, mỗi bài 1 keyword riêng**, ghi ra file `.txt` + 1 manifest TSV. Chỉ `pbn` / `blog20` / `forum`.
**Không truyền `--bulk` → hành vi y hệt trước: in ra chat, KHÔNG tạo file nào.**

```bash
# Xem kế hoạch trước (KHÔNG sinh bài) — nên chạy trước mỗi batch
/content-webnovel blog20 --bulk 3 https://webnovel.vn/dien-van/ --dry-run

# blog20 — 3 bài, tự trộn subtype
/content-webnovel blog20 --bulk 3 https://webnovel.vn/dien-van/

# pbn — 5 bài lên 5 DOMAIN khác nhau, tự chọn domain (khuyến nghị)
/content-webnovel pbn --bulk 5 https://webnovel.vn/tien-hiep/ --site-pool

# pbn — 5 bài lên 5 domain do anh chỉ định, theo thứ tự
/content-webnovel pbn --bulk 5 https://webnovel.vn/tien-hiep/ --site fbu.vn,viap.org.vn,clst.ac.vn,vnptyenbai.vn,tonghoixaydungvn.org.vn

# pbn — cả batch đăng chung 1 domain (chỉ khi anh CHỦ Ý muốn vậy)
/content-webnovel pbn --bulk 3 https://webnovel.vn/tien-hiep/ --site fbu.vn

# forum — 3 post, mỗi post 1 keyword riêng, mỗi post 1 file
/content-webnovel forum --bulk 3 https://webnovel.vn/ngon-tinh/

# Ép 1 subtype cho cả batch
/content-webnovel pbn toplist --bulk 5 https://webnovel.vn/tien-hiep/ --site-pool

# Ép keyword gốc để mở rộng từ đó
/content-webnovel blog20 --bulk 5 https://webnovel.vn/dien-van/ keyword="truyện điền văn hoàn"

# Tier A — tự pull query thật từ GSC API (nói "dùng gsc" là đủ)
/content-webnovel blog20 --bulk 5 https://webnovel.vn/dien-van/ --gsc-api

# Tier B — gửi file export tay (nói đường dẫn là đủ, khỏi gõ flag)
/content-webnovel blog20 --bulk 5 https://webnovel.vn/dien-van/
GSC: ~/Downloads/webnovel-vn-performance.zip

# Tier S — keyword thật từ autocomplete, KHÔNG cần credential/quyền GSC
/content-webnovel blog20 --bulk 5 https://webnovel.vn/dien-van/ --suggest
```

### Nguồn keyword (tuỳ chọn, nên dùng)

Keyword theo 4 tầng, chạy được cùng lúc, tier sau bù chỗ thiếu:

| Tier | Nguồn | Cờ | Có volume? | Cần quyền? |
|---|---|---|---|---|
| **A** | GSC API tự pull | `--gsc-api` | ✅ | account đọc được property |
| **B** | Export CSV/ZIP gửi tay | `--gsc-csv <file>` | ✅ | nhờ ai export hộ cũng được |
| **S** | Autocomplete Google/Bing/DDG/YouTube | `--suggest` | ❌ | **không** |
| **C** | Tự sinh từ JSON | mặc định | ❌ | không |

Không cấu hình gì vẫn chạy (tier C). Tier nào lỗi → tự rơi xuống tier dưới, **batch không chết vì keyword**.

**Không có quyền add email vào GSC?** Quyền đó là của Owner, nhưng không cần nó: dùng **OAuth** (chạy dưới account của anh, mở được property trong GSC là API đọc được), hoặc **nhờ export hộ** (tier B), hoặc **`--suggest`** (tier S, khỏi GSC).

**Cài tier A (1 lần):**

```bash
bash ~/.claude/skills/content-webnovel/scripts/gsc-install.sh   # lib vào venv riêng
# Owner  → ~/.config/webnovel-gsc/service-account.json + add email vào GSC Users
# KHÔNG Owner → ~/.config/webnovel-gsc/oauth-client.json (Desktop app), khỏi add ai
python3 ~/.claude/skills/content-webnovel/scripts/gsc-api.py --list-sites   # kiểm
```

- Tier A tự chọn property + tự suy filter page từ URL/danh mục (`/dien-van/`). Ép: `--gsc-site`, `--gsc-page-filter`, `--gsc-days 365`.
- Tier B: lưu file rồi **nói đường dẫn** (script cần path, không đọc được nội dung dán chat). **ZIP khỏi giải nén.**
- **Trong GSC bấm Export → CSV, KHÔNG chọn Excel** — script không đọc `.xlsx`. Đã mở bằng Excel rồi thì Save As → **CSV UTF-8**.
- **Bao lâu gửi 1 lần: export ngay trước mỗi batch, không cần theo lịch.** Cửa sổ 90 ngày mỗi tuần chỉ xoay ~8% dữ liệu → top keyword sau khi sort gần như y hệt, gửi dày không đổi được thứ tự bài. Muốn nhịp cố định thì **~1 tháng/lần** (khớp cửa sổ 90 ngày). Vừa publish batch xong thì **chờ 3–4 tuần** cho trang mới tích đủ impressions rồi hãy export lại.
- Header EN/VI đều nhận; `3,450` và `3.450` đều ra 3450; query **không dấu** vẫn khớp seed có dấu.
- **Tier S không có search volume** — `impressions` = 0 là đúng, autocomplete không cho volume. Độ tin đọc ở số nhóm nguồn: `tierS:bing+google+google-yt` = 3 nhóm đồng thuận. Tự bỏ keyword lạc đề, đối thủ (`wattpad`, `dtruyen`), định dạng không có (`audio`, `truyện tranh`), và keyword đóng năm đã qua.
- Xem keyword riêng: `python3 scripts/suggest.py --seed "truyện điền văn" --min-groups 2`
- Xem keyword nào vào bài nào: thêm `--dry-run`, đọc cột `kw_source` (`tierA:api` / `tierB:gsc` / `tierS:*` / `tierC:*`).

**Chi tiết đầy đủ + cách lấy credential: `GSC-SETUP.md`.**

### Domain PBN — 1 bài 1 domain (chỉ `pbn`)

**Mặc định N bài = N domain khác nhau.** Cả batch chung 1 domain để lại footprint: 1 domain nhận N bài cùng thể loại, cùng cụm keyword, cùng ngày.

| Cách khai | Kết quả |
|---|---|
| `--site-pool` | Tự lấy N domain từ `data/pbn-domains.txt`. **Khuyến nghị** — nói *"5 bài 5 domain"* là đủ, khỏi gõ |
| `--site a.vn,b.vn,c.vn` | Dùng đúng list đó, **theo thứ tự** (bài 1 → `a.vn`, bài 2 → `b.vn`…) |
| `--site a.vn` (1 domain) | Cả batch chung `a.vn` — script note lại để anh biết |
| Ít domain hơn N | Xoay vòng + note rõ bao nhiêu bài dùng lại domain |

- **Chọn domain của `--site-pool` là deterministic theo scope** (danh mục / slug truyện / tên tác giả): chạy lại cùng scope ra y cũ, scope khác thì thường lệch cụm. **"Thường" chứ không phải "luôn"** — pool chỉ 29 domain nên 2 scope khác nhau vẫn có thể rút trùng cụm (đã đo, đổi hàm băm không khá hơn). Cần chắc chắn cụm nào thì chỉ định tay bằng `--site`. Bất biến luôn giữ: **trong cùng 1 batch, N bài = N domain khác nhau.**
- Domain không có trong `data/pbn-domains.txt` → **vẫn chạy** nhưng script cảnh báo (bắt lỗi chính tả). Muốn thêm domain mới thì sửa file đó.
- Domain của từng bài cũng là **salt biến thể**: khác domain → khác archetype/góc/title, nên 5 bài trên 5 domain phân hoá mạnh hơn 5 bài chung 1 domain.
- Xem domain nào vào bài nào: `--dry-run`, đọc **cột `site`** trong TSV + dòng `[bulk-plan] domain: …`.
- Verify **khỏi truyền `--site`** — `verify-bulk.py` đọc domain theo từng dòng manifest. Domain bị dùng lại → WARN; header `site` ≠ manifest → FAIL.

### Luồng

| Bước | Việc | Script |
|---|---|---|
| 1-3 | Mở rộng keyword → tính capacity → in ma trận | `bulk-plan.py` (tự gọi `keywords.py`) |
| 4 | Sinh + ghi NGAY từng bài (file + 1 dòng manifest) | — |
| 5 | Verify batch | `verify-bulk.py` |

### Capacity (N thực = min(N, #keyword, capacity); `--bulk` > 29 = BLOCKED)

| Input | Capacity |
|---|---|
| Danh mục pool P truyện | **P** (P = 1 → **chặn** bulk, rc=3) |
| 1 URL truyện | 6 |
| Tác giả có A truyện | A + 2 |
| Có khai subtype | số slot của riêng subtype đó |

- **N bị cắt** → skill announce nguyên văn lý do, làm đúng N thực. **Không pad** bằng keyword gần trùng.
- **Pool = 1** → announce + dừng bulk, gợi ý chạy không `--bulk`.
- **Dedup chỉ trong 1 batch, KHÔNG nhớ batch trước.** `bulk-plan.py` không ghi state ra disk (`used_kw_slug` / `used_bi` / `arch_seen` chỉ sống trong 1 lần chạy) và `verify-bulk.py` chỉ đọc manifest của batch đang verify. Chạy lại cùng input + cùng nguồn keyword → **ra trùng bài**, file GSC mới hơn cũng không cứu được. Muốn batch sau không đụng batch trước: nói rõ keyword/bài đã dùng (hoặc đưa manifest cũ) để loại tay, hoặc đổi `keyword=` / subtype / danh mục.

### File output

**Mỗi batch 1 folder riêng** theo ngày-giờ, file bên trong cũng mang ngày-giờ:

```
<Downloads>/webnovel/content-{pbn|blog20|forum}/{YYYY-MM-DD_HHhMM}/{keyword-slug}__{YYYY-MM-DD_HHhMM}.txt
<Downloads>/webnovel/content-{...}/{YYYY-MM-DD_HHhMM}/manifest-{YYYY-MM-DD_HHhMM}.tsv
```

Ví dụ — batch chạy 12h07 ngày 28/07/2026:

```
content-pbn/2026-07-28_12h07/
    truyen-ngon-tinh-full__2026-07-28_12h07.txt
    thap-nien-60-lam-giau-nuoi-con__2026-07-28_12h07.txt
    manifest-2026-07-28_12h07.tsv
```

Stamp = dòng `[bulk-plan] STAMP:`, **cả batch dùng 1 stamp** (giờ lập ma trận), không phải giờ ghi từng bài — giờ thật từng bài nằm ở header `tạo lúc`.

Chạy 2 batch trùng phút → folder thứ 2 thành `2026-07-28_12h07-2`, không ghi đè. Chốt nằm ở bước **tạo folder** (fail-nếu-đã-có rồi bump `-2`), không phải ở path `bulk-plan.py` in ra: stamp không có giây nên 2 lệnh lập ma trận trùng phút vẫn nhận cùng path.

Mỗi file = **header metadata** + `---------- NỘI DUNG ĐĂNG ----------` + **nội dung dán đăng được ngay**.
pbn có `URL`/`Slug`/`site` ở header (không lọt body); blog20 không có; forum plain text 1 URL trần.

### Verify batch

```bash
python3 "~/.claude/skills/content-webnovel/scripts/verify-bulk.py" \
  --type <pbn|blog20|forum> --manifest <đường dẫn manifest .tsv>
```

**Khỏi truyền `--site`** — domain đọc theo từng dòng manifest (bulk pbn 1 bài 1 domain). `--site` chỉ là fallback cho manifest cũ không có cột `site`.

Loop từng file qua `verify-output.py` + check cấp-batch: đủ N file, filename khớp manifest, H1 phân biệt, keyword phân biệt, versus không trùng cặp, toplist không trùng >80% list. Exit 0 PASS / 1 FAIL / 2 lỗi tham số. **forum** verify riêng tại đây (plain text, đúng 1 URL trần, 500-1000 chữ, có năm) vì `verify-output.py` chỉ nhận pbn/blog20.

---

## Ảnh (ImgBB) — không nhập tháng

1. Ưu tiên field `anh_imgbb` trong `data/truyen-data.json`.
2. Thiếu → upload:

```bash
bash "~/.claude/skills/content-webnovel/scripts/imgbb-upload.sh" \
  "$HOME/Downloads/webnovel/{anh_local}" "{slug}"
```

Key: env `IMGBB_API_KEY` hoặc `~/.config/imgbb/api_key`.

---

## Lưu ý nhanh

1. Type: `bio` | `pbn` | `forum` | `blog20`. Thiếu → skill hỏi lại.
2. `pbn` cần subtype: `review` | `review-short` | `toplist` | `faq` | `genre` | `versus` | `guide`; `blog20` cần subtype: `review` | `review-short` | `toplist` | `genre` | `versus` | `guide` (**không** `faq`). `review-short` chỉ fiction (đọc chương thật); non-fiction/chương-khóa/<2-free → tự route `review` intro cùng type.
3. Mọi `pbn` cần `--site` (kèm `--bulk`: **1 bài 1 domain** — `--site-pool` hoặc list phẩy); `blog20` không dùng domain. Review/toplist/genre/versus/guide tra cứu hoặc lọc trên toàn bộ JSON.
4. **Không** truyền `--img` (đã bỏ).
5. Keyword khuyến nghị form: `keyword="..."`. Cũng nhận `--kw` / freeform. Dùng cho `pbn` + `blog20` + `forum`.
6. Output pbn: HTML thuần + `URL`/`Slug` meta — **không** JSON-LD.
7. Output blog20: HTML thuần, ảnh ImgBB, không domain/URL/Slug/self-link; số `20` không phải số lượng truyện.
8. Output forum: plain text **3 post** (hook Q + body 500–1000 chữ + CTA URL trần) — **không** còn 10 cặp Q&A.
9. Pool JSON: `data/truyen-data.json` (đồng bộ từ `/crawl-webnovel`).
10. Chỉ URL thuộc `webnovel.vn`.
11. **Title pool:** H1 review/toplist xoay theo hash slug/target (chống nhàm) — vẫn giữ keyword + `[năm]`.
11b. **Archetype khung bài:** chống "một màu" ở tầng *hình hài* — 4 archetype (Chuẩn / Kể trải nghiệm / Hỏi-đáp / Chốt trước) chọn deterministic theo hash (`//7`, tách pha khỏi title/góc/verdict), đổi trình tự section + ẩn/dời bảng-info & "Giải đáp tò mò" + 4 persona (pin theo 4 archetype) + họ title. Forum: 3 post = 3 archetype khác nhau. **Giữ nguyên contract:** nếu ẩn table phải có list thay thế (≥1 table/list); pbn giữ self-link đoạn mở, blog20 bỏ self-link; versus luôn giữ bảng so sánh; forum plain text không HTML/table, mỗi post 1 URL trần.
12. **Non-fiction:** danh mục Phát triển bản thân / Tâm linh / Kinh doanh → danh từ "sách" thay "truyện". `danh_muc` LUÔN là **list** — non-fiction chỉ khi TẤT CẢ phần tử ∈ set này.
13. **Tác giả** KHÔNG phải subtype riêng → dùng `pbn toplist "<Tên tác giả>"` (author-mode có biến thể intro "dấu ấn qua các tác phẩm").
14. `versus`: 2 truyện; scrape cả 2; 2 tên → match `tu_khoa`; bảng so sánh text-only.
15. **`pick-variant.py` (BẮT BUỘC review/review-short/toplist/genre/guide/versus/forum):** in sẵn archetype/góc/title-index/verdict/category-class theo hash — KHÔNG tự tính hash bằng tay. Truyền `--site` với pbn (salt chống trùng across-domain); blog20 không truyền.
16. **`verify-output.py` (BẮT BUỘC pbn/blog20):** pipe HTML vào `--type <pbn|blog20> --subtype <...> [--site <domain>]`; chỉ giao khi exit 0 (PASS). Đếm backlink unique / self-link / JSON-LD / word count / năm / table-list.
17. **`--bulk N` (pbn/blog20/forum):** ghi file `.txt` + manifest TSV thay vì in chat; `--dry-run` chỉ in ma trận. Xem **BULK MODE**. Không truyền `--bulk` → hành vi cũ y hệt, không tạo file. Sau batch chạy `verify-bulk.py` (BẮT BUỘC), chỉ giao khi exit 0.
