---
name: content-webnovel
description: >-
  Tạo content marketing tiếng Việt cho website đọc truyện Webnovel.vn (https://webnovel.vn/) từ URL bài truyện/danh mục/homepage.
  Live-scrape trang bằng curl (browser UA) để lấy dữ liệu thật (tên truyện, tác giả, thể loại, tóm tắt, tình trạng, list truyện), rồi sinh 3 nhóm content theo yêu cầu:
  bio (mô tả ngắn 120-150 ký tự, 10 biến thể, có hashtag), pbn (bài blog SEO/GEO/AEO 1000-1500 chữ dạng review/toplist/faq, xuất HTML thuần + URL/slug gợi ý, ảnh host ImgBB), forum (3 post plain text hỏi đáp dài 500-1000 chữ, tiêu đề = câu hỏi hook + body + CTA URL trần).
  Trigger: "/content-webnovel", "content webnovel", "viết bio truyện webnovel", "viết pbn webnovel", "forum webnovel", "bài hỏi đáp forum webnovel", hoặc khi user gửi URL webnovel.vn kèm yêu cầu tạo content.
---

# Skill: content-webnovel

Tạo content marketing cho **Webnovel.vn** (website đọc truyện chữ có bản quyền) từ URL. Skill live-scrape trang thật rồi viết content tiếng Việt theo đúng loại/subtype yêu cầu. **Không bịa** — thiếu dữ liệu thật thì báo lỗi và dừng.

## Repo

Skill đồng bộ với repo GitHub: **https://github.com/minhtranquang1993/content-webnovel** (branch `main`).
- **Push:** commit + push ngay trong `C:\Users\Admin\.claude\skills\content-webnovel\` (chính là git repo).
- **Pull:** `git pull` tại thư mục skill.

## Usage

> **Cheat sheet input nhanh:** [`CHEATSHEET.md`](CHEATSHEET.md) — copy lệnh + bảng tham số. Đổi cú pháp/tham số skill → update cả file đó.

```
/content-webnovel <type> [subtype] <url|tên> [keyword="<kw>"] [--site <domain>] [--lo <nhãn>]
```

| type | subtype | input | output |
|---|---|---|---|
| `bio` | (auto-detect từ URL) | 1 URL (homepage / danh mục / truyện) | plain text, 10 biến thể, 120-150 ký tự |
| `pbn` | `review` \| `toplist` \| `faq` | review→1 URL truyện; toplist→URL danh mục / tên thể loại / tên tác giả (+ optional keyword); faq→1 URL | HTML thuần (không JSON-LD) + block URL/Slug, 1000-1500 chữ |
| `forum` | (không có) | 1 URL (truyện hoặc danh mục) (+ optional keyword) | plain text, **3 post** biến thể; mỗi post = câu hỏi hook + body 500–1000 chữ + CTA URL trần |

**Tham số:**
- `--site <domain>` — domain đăng bài PBN (1 trong `data/pbn-domains.txt`). Dùng ghép URL bài `https://{site}/{slug}/` + đối chiếu domain hợp lệ. **Thiếu ở mọi subtype pbn → HỎI LẠI, KHÔNG đoán.**
- `--lo <nhãn>` — lô truyện trong `data/truyen-data.json` (vd `01`, `02`). **Bắt buộc** với `pbn review` / `pbn toplist`. Thiếu → hỏi lại. `bio` / `forum` / `pbn faq` không cần.
- `keyword="..."` **hoặc** `--kw "..."` **hoặc** freeform (`keyword là …`, `viết cho kw …`) — primary keyword do user ép (vd `keyword="truyện điền văn hoàn"`). **Chỉ ảnh hưởng cách viết** (H1/title/body/hook forum); **KHÔNG** đổi pool truyện. List vẫn bám URL danh mục / filter JSON. Dùng cho `pbn` (chủ yếu toplist) và `forum` (tuỳ chọn). Không có → skill auto-resolve (pbn: xem **"Resolve SEO keyword"**; forum: từ scrape — tên truyện / thể loại).

> **Đã bỏ `--img`.** Ảnh không host trên WordPress domain. Ảnh bìa lấy từ ImgBB (field `anh_imgbb` hoặc upload qua `scripts/imgbb-upload.sh`).

Ví dụ:
```
/content-webnovel bio https://webnovel.vn/ai-bao-han-tu-tien/
/content-webnovel bio https://webnovel.vn/xuyen-khong/
/content-webnovel bio https://webnovel.vn/
/content-webnovel pbn review https://webnovel.vn/ai-bao-han-tu-tien/ --site tonghoixaydungvn.org.vn --lo 01
/content-webnovel pbn toplist https://webnovel.vn/tien-hiep/ --site tonghoixaydungvn.org.vn --lo 01
/content-webnovel pbn toplist https://webnovel.vn/dien-van/ keyword="truyện điền văn hoàn" --site tonghoixaydungvn.org.vn --lo 01
/content-webnovel pbn toplist "Tiên Hiệp" --site fbu.vn --lo 01
/content-webnovel pbn toplist "Tối Bạch Đích Ô Nha" --site fbu.vn --lo 01
/content-webnovel pbn faq https://webnovel.vn/tien-hiep/ --site fbu.vn
/content-webnovel forum https://webnovel.vn/ngon-tinh/
/content-webnovel forum https://webnovel.vn/ai-bao-han-tu-tien/
/content-webnovel forum https://webnovel.vn/dien-van/ keyword="truyện điền văn full"
```

Nếu user chỉ gửi URL + mô tả bằng lời ("viết bio cho truyện này", "làm bài review", "top truyện xuyên không cho fbu.vn", "top truyện của Tối Bạch Đích Ô Nha", "bài hỏi đáp forum", "forum webnovel", "keyword điền văn full") → tự map sang type/subtype + tham số tương ứng.

**Pattern chuẩn pbn toplist danh mục + keyword (khuyến nghị):**
```
/content-webnovel pbn toplist <URL_DANH_MỤC> keyword="<primary keyword>" --site <domain> --lo <nhãn>
```
→ URL = pool list truyện; keyword = cách viết SEO. Cả hai dùng cùng lúc cho chính xác hơn.

---

## Nguồn dữ liệu truyện (dùng cho pbn toplist + ảnh)

Skill đọc file JSON đã cào sẵn để chọn đúng truyện theo thể loại/tác giả và lấy ảnh:

```
data/truyen-data.json
```

- File này **đồng bộ tự động** từ skill `/crawl-data-webnovel`: mỗi lần user chạy crawl, `crawl.py` ghi bản chính vào `~/Downloads/webnovel/truyen-data.json` **và copy 1 bản** vào `data/truyen-data.json` của skill này. Không cần sync tay.
- Mỗi record: `tu_khoa`, `slug`, `link_truyen`, `anh_local`, `anh_url` (CDN webnovel — **không** hotlink trong bài PBN), `anh_imgbb` (direct URL ImgBB — **ưu tiên dùng**), `danh_muc`, `tac_gia`, `lo`.
- **File ảnh local** = `~/Downloads/webnovel/{anh_local}` — chỉ dùng khi `anh_imgbb` trống (upload mới qua ImgBB).
- **Lọc theo lô:** `pbn toplist`/`pbn review` chỉ bốc record `lo == <--lo>`. Thiếu `--lo` → hỏi lại, KHÔNG bốc chung tất cả lô.

Nếu file không tồn tại hoặc **pool = 0** sau lọc lô + tiêu chí → **fallback scrape live** URL danh mục (thể loại) / dừng (tác giả). Pool = 1 → auto-switch review (xem pbn toplist).

---

## BƯỚC 1 — Scrape dữ liệu (BẮT BUỘC trước khi viết)

Với `pbn toplist` lấy pool từ JSON: scrape chỉ khi cần `CAT_TITLE` từ URL danh mục, khi fallback `pool=0`, hoặc khi auto-switch review 1 truyện. Các type khác: luôn scrape trước, KHÔNG tự đoán nội dung từ slug URL.

```bash
bash "C:\Users\Admin\.claude\skills\content-webnovel\scripts\scrape.sh" "<url>"
```

Script tự nhận diện loại trang từ HTML markers và in ra các dòng `KEY<TAB>value`:

- **story** (`og:type=book` + `book-detail__title`): `TITLE`, `AUTHOR`, `GENRES` (phân tách `|`), `STATUS`, `SUMMARY`
- **category** (`page page--category` + `page__title`): `CAT_TITLE`, `CAT_DESC`, nhiều dòng `STORY<TAB>tên<TAB>link` (top 30 truyện trong danh mục)
- **homepage** (path `/`): `HOME_TITLE`, `HOME_DESC`, nhiều dòng `GENRE_LINK<TAB>tên thể loại<TAB>slug`

**Fail rõ ràng — DỪNG, không viết content, báo user:**
- `rc=2`: URL thiếu / không thuộc webnovel.vn
- `rc=3`: không tải được URL (curl fail) → có thể site chặn hoặc URL sai, báo user kiểm tra
- `rc=4`: không nhận diện được loại trang → báo user kiểm tra URL
- `rc=5`: nhận diện được loại trang nhưng không bóc được field lõi (tên truyện / tiêu đề danh mục)

> Ngoại lệ bio truyện: nếu scrape được `TITLE` + `GENRES` nhưng thiếu `SUMMARY`, vẫn viết được (bio ngắn). Chỉ fail khi thiếu cả `TITLE`.

---

## BƯỚC 2 — Xác định type + subtype

1. **type** do user khai báo (`bio` / `pbn` / `forum`). Không có → hỏi lại, KHÔNG đoán.
2. **bio subtype** = suy từ `PAGE_TYPE` của scrape:
   - `homepage` → **bio homepage**
   - `category` → **bio danhmuc**
   - `story` → **bio tentruyen**
3. **pbn subtype** do user khai báo (`review` / `toplist` / `faq`). Không có → hỏi lại.
   - `review` + `faq` yêu cầu đúng loại trang phù hợp; `toplist` nhận URL danh mục **hoặc** tên thể loại/tác giả gõ tay.
   - Mọi subtype pbn cần `--site`. `review`/`toplist` cần thêm `--lo`. Thiếu → hỏi lại (không đoán).
4. **forum**: không subtype, bám theo `PAGE_TYPE` (story → post hỏi đáp về truyện; category → post hỏi đáp về thể loại). Keyword tuỳ chọn (xem **LOẠI forum**).

---

## Quy tắc hashtag (dùng cho bio)

Sinh hashtag từ tên tiếng Việt: **bỏ dấu → bỏ ký tự đặc biệt/khoảng trắng → viết liền → chữ thường**.
- "Ai Bảo Hắn Tu Tiên!" → `#aibaohantutien`
- "Xuyên Không" → `#truyenxuyenkhong` (thêm tiền tố "truyen" cho hashtag danh mục)
- "Tiên Hiệp" → `#truyentienhiep`

---

## LOẠI bio — plain text, 10 biến thể, 120-150 ký tự mỗi biến thể

Chung cho cả 3 subtype:
- Mỗi biến thể **120-150 ký tự** (đếm cả hashtag).
- **Nhắc "Webnovel.vn" trong text** ở cả 3 subtype.
- Tone: marketing nhẹ, hấp dẫn, kêu gọi hành động (đọc/khám phá truyện).
- 10 biến thể phải **khác nhau rõ** (đổi câu mở, động từ CTA, cách diễn đạt) — tránh chỉ đổi 1-2 từ.
- Xuất dạng danh sách đánh số 1-10 trong chat, mỗi dòng kèm số ký tự ở cuối `(N ký tự)` để user dễ kiểm.

### bio homepage
- Nội dung chung, kêu gọi khám phá các thể loại truyện.
- Có thể nhắc vài thể loại nổi bật từ `GENRE_LINK`.
- **Hashtag:** `#webnovel` + hashtag keyword chung. Pool gợi ý (chọn 2-3/biến thể, xoay vòng): `#doctruyen #truyenchu #truyenonline #truyenhay #docsach #truyenfull`.

### bio danhmuc
- Nội dung chung về danh mục (dựa `CAT_TITLE` + `CAT_DESC`), kêu gọi xem truyện trong danh mục đó.
- **Hashtag:** `#webnovel` + hashtag keyword danh mục (vd danh mục Xuyên Không → `#truyenxuyenkhong`). Có thể thêm 1 keyword chung.

### bio tentruyen
- Giới thiệu truyện (dựa `TITLE` + `GENRES` + `SUMMARY`), gợi tò mò, kêu gọi đọc.
- **Hashtag:** CHỈ `#<danhmục>` + `#<têntruyện>` (vd `#truyentienhiep #aibaohantutien`). **KHÔNG ép `#webnovel`.** Nếu truyện nhiều thể loại, lấy thể loại đầu (hoặc 2 thể loại chính) làm hashtag danh mục.

---

## LOẠI pbn — HTML thuần, 1000-1500 chữ (KHÔNG JSON-LD)

Nguyên tắc chung SEO/GEO/AEO (áp cho cả 3 subtype):
- **Câu định nghĩa entity dứt khoát ở đầu bài** (ngay sau/trong đoạn mở): "*[Tên] là truyện [thể loại] của tác giả [X], [đặc điểm nổi bật]*" — câu AI dễ trích dẫn nhất.
- **Answer-first** chỉ ở: đoạn intro, mỗi câu FAQ, đầu mỗi mục toplist. KHÔNG nhồi answer-first vào mọi đoạn (đọc như bot → mất E-E-A-T).
- Có **bảng hoặc list** (dễ ăn featured snippet + AI trích).
- **Freshness:** H1 + intro có năm hiện tại (2026).
- **Brand tiết chế:** "Webnovel.vn" xuất hiện tối đa 2-3 lần/bài **dạng text**, chủ yếu ở CTA. Giữ giọng blogger bên thứ 3, KHÔNG nhồi quảng cáo.
- **Backlink unique (BẮT BUỘC):** mỗi URL `webnovel.vn` (bất kỳ path) chỉ được chèn **đúng 1 lần** dưới dạng `<a href="...">` trong toàn bộ HTML. Trùng URL = vi phạm.
  - `review` / `faq`: đúng **1** backlink — đặt ở **CTA cuối**. Chỗ khác (bảng info, đoạn giữa) chỉ text "Webnovel.vn", không bọc `<a>`.
  - `toplist`: mỗi truyện **1** link `link_truyen` riêng (N URL khác nhau → N thẻ `<a>`, mỗi URL 1 lần). Bảng so sánh **không** lặp lại link đã dùng ở mục truyện (chỉ text tên hoặc "xem ở mục trên"). CTA cuối: 1 link danh mục **nếu URL đó chưa dùng** ở item nào.
  - Auto-switch review từ danh mục (pool=1): cho phép **2** backlink webnovel khác nhau — 1 link truyện (CTA) + 1 link danh mục (trong intro hoặc đoạn thể loại). Mỗi URL vẫn chỉ 1 lần.
- **Self-link internal (BẮT BUỘC):** đúng **1** thẻ `<a href="{URL bài PBN}">` trong **đoạn mở** (sau câu định nghĩa entity). Anchor text = biến thể title ngắn (tên truyện / "review [tên]" / "top truyện [thể loại]") — **không** dùng raw URL làm anchor. **Không** `rel="nofollow"` (internal cùng site PBN).
- Tone: blogger review khách quan, đáng tin, tự nhiên.
- Xuất **HTML thuần** (thẻ `<h1><h2><p><table><ul><img><a>`). **KHÔNG** xuất `<script type="application/ld+json">` hay bất kỳ schema/JSON-LD nào.
- Hiển thị trực tiếp trong chat để user copy.

### URL + Slug bài PBN (mọi subtype pbn)

Sinh **sau khi chốt H1/title**, trước khi viết body:

1. Lấy chuỗi title (thường = nội dung H1).
2. Bỏ dấu tiếng Việt → lowercase → thay khoảng trắng/ký tự không phải `[a-z0-9]` bằng `-` → gộp `-` liên tiếp → trim `-` đầu/cuối.
   - VD: `Review Ai Bảo Hắn Tu Tiên – Tiên Hiệp 2026` → `review-ai-bao-han-tu-tien-tien-hiep-2026`
3. Full URL: `https://{site}/{slug}/` (trailing slash; `{site}` = giá trị `--site`, không thêm `www.` nếu user không truyền).
4. **In block meta trước HTML** (bắt buộc):

```
URL: https://{site}/{slug}/
Slug: {slug}
```

Self-link trong body dùng đúng full URL này.

### Ảnh bìa ImgBB (review + toplist)

Ảnh bìa **host trên ImgBB**, không còn ghép `/wp-content/uploads/` trên domain PBN. **Không còn tham số `--img`.**

**Thứ tự lấy URL ảnh (BẮT BUỘC):**

1. **Ưu tiên `anh_imgbb`** trong `data/truyen-data.json` nếu field có giá trị `https://...` → dùng thẳng, **không** upload lại.
2. Nếu `anh_imgbb` trống/thiếu → upload từ file local rồi (nên) ghi ngược URL vào JSON:

```bash
bash "C:\Users\Admin\.claude\skills\content-webnovel\scripts\imgbb-upload.sh" \
  "$HOME/Downloads/webnovel/{anh_local}" "{slug}"
```

- Input path = `~/Downloads/webnovel/` + `anh_local` từ JSON (vd `hinh-anh-ten-truyen/huyen-giam-tien-toc.webp`).
- Arg 2 (name) = `slug` truyện — tiện quản lý trên ImgBB.
- Stdout = direct URL (thường `https://i.ibb.co/...`).
- **rc:** `0` OK · `2` thiếu file · `3` thiếu key · `4` upload/parse fail.

**API key (chỉ cần khi phải upload mới — không hardcode, không commit):**
1. Env `IMGBB_API_KEY`, hoặc
2. File `~/.config/imgbb/api_key` (1 dòng, chỉ chứa key)

Lấy key miễn phí: https://api.imgbb.com/ (đăng nhập ImgBB → API).

**Chèn HTML:**

```html
<a href="{imgbb_url}" rel="nofollow noopener" target="_blank">
  <img src="{imgbb_url}" alt="[Tên truyện] – truyện [thể loại chính]" loading="lazy" referrerpolicy="no-referrer">
</a>
```

- Bọc `<a rel="nofollow noopener" target="_blank">` quanh ảnh (link ra host ngoài).
- **Alt text:** `[Tên truyện] – truyện [thể loại chính]` (thể loại đầu trong `danh_muc`).
- Truyện không có `anh_imgbb` + không upload được (thiếu file/key/fail) / đến từ fallback scrape live → **báo user rõ** — **KHÔNG** fallback path WP, **KHÔNG** hotlink `cdn.webnovel.vn`.

### H2 mục giải đáp (thay cho "FAQ")

Bỏ chữ "FAQ" tiếng Anh ở heading user-facing. Chọn **1** H2 theo subtype (xoay pool cho đa dạng giữa các bài):

| Subtype | Mặc định | Biến thể xoay |
|---|---|---|
| **review** | `Giải đáp tò mò về truyện [Tên]` | `Thắc mắc thường gặp về [Tên]` · `Đọc [Tên]: những câu hỏi hay gặp` |
| **toplist** (thể loại) | `Giải đáp tò mò về truyện [Thể loại]` | `Câu hỏi thường gặp khi chọn truyện [Thể loại]` · `Thắc mắc hay gặp về truyện [Thể loại]` |
| **toplist** (tác giả) | `Giải đáp tò mò về truyện của [Tác giả]` | `Thắc mắc thường gặp về [Tác giả]` |
| **faq** (toàn bài Q&A) | Không thêm H2 bọc "FAQ" — mỗi câu hỏi là H2/H3 riêng | — |

### Resolve SEO keyword (danh mục) — tách bạch với pool truyện

Dùng cho `pbn toplist` kiểu thể loại (và cho case auto-switch review từ danh mục). **Hai lớp độc lập:**

| Lớp | Nguồn | Dùng để |
|---|---|---|
| **Pool / list truyện** | URL danh mục → `CAT_TITLE` strip → match `danh_muc` trong JSON (hoặc scrape `STORY` khi pool=0) | Chọn truyện nào vào bài |
| **SEO keyword** | `keyword="..."` / `--kw` / freeform user, hoặc auto từ URL + `CAT_TITLE` + `CAT_DESC` | H1, title, rải body/H2 giải đáp |

**Quy tắc resolve primary keyword (thể loại):**
1. Có `keyword="..."` **hoặc** `--kw "..."` **hoặc** freeform ("keyword là …", "viết cho kw …", "kw: …") → primary = đúng chuỗi user (giữ nguyên wording).
2. Không có → primary auto = `truyện {tên danh mục thường}` sau khi strip tiền tố "Truyện " khỏi `CAT_TITLE` (vd URL `/dien-van/` → `CAT_TITLE` "Truyện Điền Văn" → primary **`truyện điền văn`**). Tên gõ tay không URL: primary = `truyện {tên đã chuẩn hoá thường}`.
3. **Biến thể phụ** (rải nhẹ 1–3 lần trong intro/H2 — KHÔNG spam): sinh từ seed danh mục + tín hiệu `CAT_DESC`/slug. Pool gợi ý:
   - `truyện {dm} hay` / `truyện {dm} hay nhất`
   - `truyện {dm} full` / `truyện {dm} hoàn` / `truyện hoàn {dm}` (rải tối đa 1–2 lần)
   - compound nếu `CAT_DESC` gợi (vd desc điền văn có "ngôn tình" → `truyện điền văn ngôn tình` 1 lần)
4. **CẤM** dùng biến thể keyword để **lọc lại** pool. User gõ `keyword="truyện điền văn hoàn"` + URL `/dien-van/` → list vẫn là truyện `danh_muc` chứa **Điền Văn**, không lọc "hoàn".

**Kiểu tác giả:** primary mặc định xoay quanh tên tác giả (`truyện của [Tác giả]`, `top truyện [Tác giả]`); `keyword=` / `--kw` vẫn override nếu user truyền.

### pbn review (1 URL truyện)
Cấu trúc:
1. Block meta `URL` + `Slug`
2. `<h1>` — `Review [Tên truyện] – [thể loại] [năm]`
3. Đoạn mở: câu định nghĩa entity → **1 self-link** về URL bài → TL;DR 2-3 câu. Ngay dưới chèn **1 ảnh ImgBB** (nếu có).
4. `<table>` thông tin nhanh: Tác giả / Thể loại / Tình trạng / Đọc tại (**text** "Webnovel.vn", không link)
5. `<h2>` Nội dung truyện — tóm tắt cốt (KHÔNG spoiler kết)
6. `<h2>` Điểm mạnh — list
7. `<h2>` Điểm yếu / lưu ý — list
8. `<h2>` Truyện hợp với ai
9. Box đánh giá: "Đánh giá tổng: x/10" (điểm khách quan, kèm 1 câu lý do)
10. `<h2>` theo pool "Giải đáp tò mò…" — 3-4 câu Q&A **đặc thù truyện này**
11. CTA đọc full: **duy nhất 1** `<a href="{link truyện}">` về webnovel.vn

### pbn toplist (theo THỂ LOẠI hoặc theo TÁC GIẢ)

Toplist có 2 kiểu lọc — xác định từ input user:
- **Theo thể loại:** URL danh mục (`https://webnovel.vn/tien-hiep/`) hoặc tên thể loại gõ tay ("top truyện tiên hiệp").
- **Theo tác giả:** user nêu tên tác giả ("top truyện của Tối Bạch Đích Ô Nha", "toplist tác giả Nhĩ Căn").

**Nguồn truyện (BẮT BUỘC theo thứ tự ưu tiên):**

1. **Đọc `data/truyen-data.json`** rồi lọc pool:
   - **Lọc lô trước tiên:** chỉ giữ record có `lo` == `--lo`. Thiếu `--lo` → hỏi lại, KHÔNG bốc toàn bộ JSON.
   - Kiểu **thể loại** → trong pool lô đó, lọc record có `danh_muc` chứa thể loại target (match không phân biệt hoa thường: "Tiên Hiệp", "Xuyên Không", "Ngôn Tình", "Điền Văn"...).
   - Kiểu **tác giả** → trong pool lô đó, lọc record có `tac_gia` khớp tên tác giả target (không phân biệt hoa thường; chấp nhận khớp gần đúng).
2. **Xác định target (tên thể loại/tác giả để LỌC — không phải SEO keyword):**
   - Thể loại từ URL danh mục → scrape live lấy `CAT_TITLE`, bỏ tiền tố "Truyện " nếu có (vd "Truyện Tiên Hiệp" → "Tiên Hiệp"; "Truyện Điền Văn" → "Điền Văn").
   - Thể loại / tác giả gõ tay → dùng đúng tên đó (chuẩn hoá hoa/thường).
3. **Nhánh theo kích thước pool (sau lọc lô + tiêu chí):**
   - **`pool >= 2`** → viết **toplist**. N = số truyện lấy được (khuyến nghị top 5–10; 2 truyện vẫn toplist "Top 2").
   - **`pool == 1`** → **TỰ CHUYỂN `pbn review`** truyện đó (xem **"Auto-switch pool=1 → review"**). **KHÔNG** viết "Top 1…".
   - **`pool == 0`** (hoặc JSON không tồn tại/rỗng) → fallback:
     - Kiểu **thể loại**: scrape live URL danh mục (`STORY` lines), KHÔNG có ảnh ImgBB (báo user + gợi ý crawl thêm vào lô). Nếu scrape cũng ra đúng 1 `STORY` → vẫn auto-switch review.
     - Kiểu **tác giả**: KHÔNG có trang tác giả → báo user "chưa có truyện của tác giả này trong lô `<--lo>`, hãy crawl thêm rồi chạy lại", DỪNG (không bịa).
4. **Chọn N truyện** từ pool khi `pool >= 2` (lấy theo thứ tự trong JSON, cắt theo N).

> Chỉ fallback khi **pool = 0**. Pool 2 truyện **không** scrape live, **không** chuyển review.

**Ảnh bìa mỗi truyện:** dùng `anh_imgbb` từ JSON nếu có; chỉ upload ImgBB khi field trống.

#### Auto-switch pool=1 → review

Khi bước lọc cho ra **đúng 1 truyện**, skill **bắt buộc**:

1. **Announce** rõ trong output (trước meta/HTML):  
   `Pool = 1 ([thể loại|tác giả] "<target>" / lo=<--lo>) → chuyển pbn review truyện "<tên>".`
2. Scrape live URL truyện đó (lấy `TITLE`/`AUTHOR`/`GENRES`/`STATUS`/`SUMMARY`) nếu chưa có đủ field; ảnh dùng `anh_imgbb` / upload ImgBB.
3. Viết theo **cấu trúc pbn review**, với bổ sung:

**A. Từ toplist THỂ LOẠI (URL/tên danh mục):** — **dual-entity**
- Primary SEO = keyword đã resolve, **không** đổi sang chỉ tên truyện.
- H1 gợi ý: `Review [Tên truyện] – [primary keyword] [năm]` (vd `Review … – truyện điền văn hoàn 2026` nếu user truyền keyword đó).
- Intro: câu định nghĩa truyện + neo thể loại/keyword + **1 self-link** URL bài.
- **Backlink webnovel (2 URL khác nhau, mỗi URL 1 lần):**
  - 1 link truyện (`link_truyen`) — CTA cuối
  - 1 link danh mục (URL user đưa) — trong intro hoặc đoạn thể loại
- Mục giải đáp: 3–4 câu — phần lớn về truyện, **1–2 câu** về thể loại/keyword.
- Ảnh ImgBB như review thường.

**B. Từ toplist TÁC GIẢ:**
- H1 gợi ý: `Review [Tên truyện] – truyện của [Tác giả] [năm]` (hoặc keyword user nếu có).
- **Backlink:** 1 link truyện (CTA).
- **Không bịa** URL trang tác giả.
- Nếu record có `danh_muc` → **thêm 1 link danh mục chính** = thể loại đầu (map URL webnovel nếu biết; không chắc thì chỉ nêu tên thể loại + link truyện).
- Mục giải đáp: về truyện + 1 câu về phong cách tác giả.

4. Giữ contract `--site` / `--lo`. Output HTML thuần + meta URL/Slug (không JSON-LD).

#### Cấu trúc toplist (khi pool >= 2)

Trước khi viết: chạy **Resolve SEO keyword** (thể loại) — H1/body bám primary + biến thể; list truyện vẫn theo target lọc.

1. Block meta `URL` + `Slug`
2. `<h1>` — kiểu thể loại: ưu tiên chứa primary keyword (vd `Top N truyện điền văn hoàn hay nhất 2026`); kiểu tác giả: `Top N truyện hay nhất của [Tên tác giả] [năm]`
3. Intro answer-first: liệt kê nhanh N tên + **1 self-link** về URL bài; rải primary keyword 1 lần tự nhiên
4. Đoạn **"Tiêu chí chọn"** (lượt đọc/đánh giá/tình trạng full-đang ra/độ hot) — bắt buộc. Kiểu tác giả: nêu thêm dấu ấn/phong cách chung của tác giả.
5. Mỗi truyện = `<h2>` [số]. [Tên truyện] + ảnh ImgBB + câu định nghĩa ngắn + vì sao đáng đọc (2-4 câu) + **1** link đọc (`link_truyen`, mỗi URL 1 lần)
6. `<table>` so sánh cuối bài — **không** chèn lại `<a>` trùng URL đã dùng ở mục 5 (text tên / "xem ở mục trên")
7. `<h2>` theo pool "Giải đáp tò mò…" — 3-4 câu Q&A về danh mục/keyword (hoặc về tác giả); được phép 1 biến thể "full/hoàn" nếu hợp
8. CTA khám phá thêm: 1 link danh mục webnovel **chỉ khi URL chưa xuất hiện** ở bước 5

- N = số truyện trong pool đã chọn (tối thiểu 2 khi vào nhánh này; khuyến nghị top 5-10).
- **Thể loại trong bảng so sánh** = `danh_muc` của từng truyện (join bằng dấu phẩy), KHÔNG bịa.

### pbn faq (1 URL truyện hoặc danh mục)
Cấu trúc:
1. Block meta `URL` + `Slug`
2. `<h1>` — câu hỏi lớn + năm (vd "Truyện tiên hiệp hay nhất 2026: giải đáp mọi thắc mắc")
3. Đoạn mở ngắn + **1 self-link** về URL bài
4. 6-10 cặp Q&A: mỗi Q = `<h2>` hoặc `<h3>` (không bọc thêm H2 "FAQ"), A answer-first 2-4 câu rồi mở rộng
5. Câu hỏi bám chủ đề trang (truyện cụ thể hoặc thể loại)
6. CTA: **duy nhất 1** backlink webnovel.vn

---

## LOẠI forum — plain text, 3 post hỏi đáp dài (500–1000 chữ/post)

**Không còn** format 10 cặp Q&A ngắn. Mỗi lần chạy sinh **3 post biến thể** — mỗi post là **1 bài hỏi đáp liền mạch** (gần PBN về độ sâu nhưng ngắn hơn, plain text, thiên chủ đề câu hỏi).

### Input
- **URL bắt buộc** (truyện hoặc danh mục). Homepage → hỏi lại / gợi ý URL truyện hoặc danh mục.
- **`keyword="..."` / `--kw` / freeform** — tuỳ chọn. Có → hook + body bám keyword; **không** đổi dữ liệu scrape. Không có → auto primary từ scrape:
  - story → tên truyện (+ thể loại chính nếu hợp)
  - category → `truyện {tên danh mục}` sau strip tiền tố "Truyện " (vd `Truyện Điền Văn` → `truyện điền văn`)
- **Không** cần `--site` / `--lo`. **Không** HTML, **không** meta URL/Slug, **không** ảnh.

### Cấu trúc mỗi post (BẮT BUỘC)
1. **Dòng tiêu đề = câu hỏi hook** — như title thread forum, gây tò mò, tự nhiên (không khô kiểu SEO “X là gì 2026”). Có thể neo keyword/tên truyện/thể loại.
2. **Body 500–1000 chữ**, **3–5 đoạn** tự do:
   - mở / định nghĩa–giải đáp trực tiếp câu hỏi
   - mở rộng (góc đáng chú ý, gợi ý đọc, so sánh nhẹ nếu hợp — **không bịa** plot/điểm số)
   - lưu ý / chốt cảm nhận
3. **CTA cuối + đúng 1 URL trần** (không thẻ `<a>`):
   - story → URL truyện đã scrape
   - category → URL danh mục user đưa
   - Ví dụ wording: *“Đọc thêm chi tiết truyện trên Webnovel.vn: https://webnovel.vn/…”* / *“Xem thêm truyện [thể loại] tại: https://webnovel.vn/…”*
   - Mỗi post **1** URL; không dán thêm URL webnovel khác.

### Quy tắc viết
- **3 post khác nhau rõ:** đổi hook (góc hỏi), cách mở, trọng tâm body — tránh chỉ paraphrase 1–2 câu.
- **KHÔNG hashtag.**
- **KHÔNG** bảng / list SEO dài / khung mini-PBN cứng / JSON-LD / HTML.
- Brand: nhắc “Webnovel.vn” tự nhiên (chủ yếu CTA); không nhồi quảng cáo.
- Tone: **giọng sạch, dễ đọc, đúng chính tả** — KHÔNG viết tắt kiểu seeding (`e`, `mn`, `k`...). Thân thiện như người đọc forum thật, vẫn chuẩn.
- Bám dữ liệu scrape (`TITLE`/`SUMMARY`/`GENRES` hoặc `CAT_TITLE`/`CAT_DESC`/`STORY`). **Không bịa** cốt/spoiler kết/đánh giá số liệu không có.
- Đếm “chữ” theo đơn vị từ tiếng Việt (cùng convention pbn 1000–1500 chữ), **không** đếm ký tự như bio.

### Output trong chat
```
### Post 1
[Câu hỏi hook?]

[đoạn 1]

[đoạn 2]
...

Đọc thêm chi tiết truyện trên Webnovel.vn: https://webnovel.vn/...

### Post 2
...

### Post 3
...
```
Cuối mỗi post có thể ghi `(~N chữ)` để user kiểm độ dài.

---

## Rules

- **Luôn scrape trước khi viết** (trừ `pbn toplist` lấy pool từ JSON — scrape chỉ khi fallback `pool=0`, cần `CAT_TITLE` từ URL danh mục, hoặc auto-switch review 1 truyện). Không đoán nội dung từ slug.
- **Không bịa.** Scrape fail (rc≠0) → báo lỗi rõ theo mã lỗi, DỪNG. (Ngoại lệ bio truyện thiếu summary như mô tả trên.)
- **Toplist chọn truyện đúng tiêu chí** từ JSON: lọc theo `lo` trước, rồi theo thể loại (`danh_muc`) hoặc tác giả (`tac_gia`).
- **Tách pool vs keyword:** list truyện bám URL danh mục / filter JSON; keyword (`keyword=` / `--kw` / freeform / auto) chỉ để viết (pbn + forum). **Không** dùng keyword để lọc pool.
- **Pool size (sau lọc lô + tiêu chí):** `>= 2` → toplist; `== 1` → **auto-switch review** (announce + dual-entity nếu từ danh mục; author → link truyện + 1 danh mục chính); `== 0` → fallback scrape (thể loại) hoặc dừng (tác giả).
- **Lô truyện (`--lo`):** bắt buộc với `pbn review`/`pbn toplist`. Thiếu → hỏi lại.
- **PBN bắt buộc `--site`.** Thiếu → hỏi lại. **Không còn `--img`.**
- **Ảnh PBN:** ưu tiên `anh_imgbb`; thiếu thì upload ImgBB từ file local. Không hotlink CDN webnovel, không ghép path WP.
- **URL bài:** sinh slug từ title, in `URL` + `Slug` trước HTML; 1 self-link internal trong đoạn mở.
- **Không schema/JSON-LD** trong output pbn.
- Toàn bộ content **tiếng Việt**.
- Type do user khai báo; subtype bio auto-detect; subtype pbn do user khai báo — **ngoại lệ:** `pbn toplist` pool=1 được phép tự chuyển review (phải announce).
- bio: plain text 10 biến thể trong chat. **forum: plain text 3 post** (hook Q + body 500–1000 chữ + CTA URL trần). pbn: HTML thuần + meta URL/Slug trong chat.
- Sau khi tạo content xong: hỏi user có muốn push skill lên repo không (nếu vừa sửa skill).

## Scripts & Data
- `scripts/scrape.sh` — live-scrape webnovel.vn (curl browser-UA), auto-detect loại trang, in field dạng `KEY<TAB>value`. Fail rõ ràng rc 2/3/4/5.
- `scripts/imgbb-upload.sh` — upload 1 ảnh lên ImgBB, stdout = direct URL. Key: `IMGBB_API_KEY` hoặc `~/.config/imgbb/api_key`. rc 2/3/4 khi lỗi.
- `data/truyen-data.json` — pool truyện đã crawl (đồng bộ từ `/crawl-data-webnovel`). Có `anh_imgbb`, `lo`.
- `data/pbn-domains.txt` — domain PBN hợp lệ (đối chiếu `--site`). Dùng ghép URL bài, **không** host ảnh.
- `CHEATSHEET.md` — input cheat sheet (update cùng SKILL khi đổi Usage).

## Category
content-seo
