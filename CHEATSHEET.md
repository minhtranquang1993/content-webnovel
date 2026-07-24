# Cheat sheet — `/content-webnovel`

Cách input nhanh cho skill content marketing Webnovel.vn.  
**Skill active:** `C:\Users\Admin\.claude\skills\content-webnovel\`  
**Repo:** https://github.com/minhtranquang1993/content-webnovel  
**Chi tiết đầy đủ:** xem `SKILL.md`.

> Khi đổi cú pháp / tham số / hành vi input của skill → **update file này** cùng lúc với `SKILL.md`.

---

## Cú pháp chuẩn

```
/content-webnovel <type> [subtype] <url|tên> [keyword="<kw>"] [--site <domain>]
```

Freeform cũng được: gửi URL + mô tả bằng lời → skill tự map.

---

## Tham số

| Flag / form | Bắt buộc? | Dùng cho | Ý nghĩa |
|---|---|---|---|
| `--site <domain>` | **Có** với mọi `pbn`; **không dùng** cho `blog20` | PBN | Domain đăng bài → ghép `https://{site}/{slug}/` |
| `keyword="..."` hoặc `--kw "..."` | Tuỳ chọn | `pbn toplist` / `blog20 toplist` (chủ yếu) + `forum` | Primary keyword. **Chỉ để viết**, không đổi list truyện |

**Tương thích input cũ:** nếu vẫn truyền `--lo <nhãn>`, skill bỏ qua cả flag và giá trị; không hỏi lại, không báo lỗi, không dùng để lọc dữ liệu.

**Không còn `--img`.** Ảnh = ImgBB (`anh_imgbb` trong JSON / `scripts/imgbb-upload.sh`).

**Không cần** `--site`: `bio`, `forum`.
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

## Ảnh (ImgBB) — không nhập tháng

1. Ưu tiên field `anh_imgbb` trong `data/truyen-data.json`.
2. Thiếu → upload:

```bash
bash "C:\Users\Admin\.claude\skills\content-webnovel\scripts\imgbb-upload.sh" \
  "$HOME/Downloads/webnovel/{anh_local}" "{slug}"
```

Key: env `IMGBB_API_KEY` hoặc `~/.config/imgbb/api_key`.

---

## Lưu ý nhanh

1. Type: `bio` | `pbn` | `forum` | `blog20`. Thiếu → skill hỏi lại.
2. `pbn` cần subtype: `review` | `review-short` | `toplist` | `faq` | `genre` | `versus` | `guide`; `blog20` cần subtype: `review` | `review-short` | `toplist` | `genre` | `versus` | `guide` (**không** `faq`). `review-short` chỉ fiction (đọc chương thật); non-fiction/chương-khóa/<2-free → tự route `review` intro cùng type.
3. Mọi `pbn` cần `--site`; `blog20` không dùng domain. Review/toplist/genre/versus/guide tra cứu hoặc lọc trên toàn bộ JSON.
4. **Không** truyền `--img` (đã bỏ).
5. Keyword khuyến nghị form: `keyword="..."`. Cũng nhận `--kw` / freeform. Dùng cho `pbn` + `blog20` + `forum`.
6. Output pbn: HTML thuần + `URL`/`Slug` meta — **không** JSON-LD.
7. Output blog20: HTML thuần, ảnh ImgBB, không domain/URL/Slug/self-link; số `20` không phải số lượng truyện.
8. Output forum: plain text **3 post** (hook Q + body 500–1000 chữ + CTA URL trần) — **không** còn 10 cặp Q&A.
9. Pool JSON: `data/truyen-data.json` (đồng bộ từ `/crawl-data-webnovel`).
10. Chỉ URL thuộc `webnovel.vn`.
11. **Title pool:** H1 review/toplist xoay theo hash slug/target (chống nhàm) — vẫn giữ keyword + `[năm]`.
12. **Non-fiction:** danh mục Phát triển bản thân / Tâm linh → danh từ "sách" thay "truyện".
13. **Tác giả** KHÔNG phải subtype riêng → dùng `pbn toplist "<Tên tác giả>"` (author-mode có biến thể intro "dấu ấn qua các tác phẩm").
14. `versus`: 2 truyện; scrape cả 2; 2 tên → match `tu_khoa`; bảng so sánh text-only.
