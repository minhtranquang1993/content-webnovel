---
name: content-webnovel
description: >-
  Tạo content marketing tiếng Việt cho website đọc truyện Webnovel.vn (https://webnovel.vn/) từ URL bài truyện/danh mục/homepage.
  Live-scrape trang bằng curl (browser UA) để lấy dữ liệu thật (tên truyện, tác giả, thể loại, tóm tắt, tình trạng, list truyện), rồi sinh 4 nhóm content theo yêu cầu:
  bio (mô tả ngắn 120-150 ký tự, 10 biến thể, có hashtag), pbn (bài blog SEO/GEO/AEO 1000-1500 chữ dạng review/toplist/faq/genre/versus/guide, title xoay theo pool sáng tạo, xuất HTML thuần + URL/slug gợi ý, ảnh host ImgBB), forum (3 post plain text hỏi đáp dài 500-1000 chữ, tiêu đề = câu hỏi hook + body + CTA URL trần), blog20 (HTML 1000-1500 chữ dạng review/toplist/genre/versus/guide, không cần domain, không URL/Slug hay self-link, ảnh host ImgBB). Hỗ trợ cả sách non-fiction (Phát triển bản thân, Tâm linh) với danh từ "sách" thay "truyện".
  Trigger: "/content-webnovel", "content webnovel", "viết bio truyện webnovel", "viết pbn webnovel", "forum webnovel", "blog20 webnovel", "viết blog20", "bài hỏi đáp forum webnovel", "giải thích thể loại", "thể loại là gì", "so sánh 2 truyện", "truyện A hay truyện B", "cẩm nang đọc", "người mới nên đọc", hoặc khi user gửi URL webnovel.vn kèm yêu cầu tạo content.
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
/content-webnovel <type> [subtype] <url|tên> [keyword="<kw>"] [--site <domain>]
```

| type | subtype | input | output |
|---|---|---|---|
| `bio` | (auto-detect từ URL) | 1 URL (homepage / danh mục / truyện) | plain text, 10 biến thể, 120-150 ký tự |
| `pbn` | `review` \| `toplist` \| `faq` \| `genre` \| `versus` \| `guide` | review→1 URL truyện; toplist→URL danh mục / tên thể loại / tên tác giả; faq→1 URL; genre→URL danh mục / tên thể loại; versus→2 URL truyện / 2 tên / URL danh mục; guide→URL danh mục / tên thể loại (+ optional keyword) | HTML thuần (không JSON-LD) + block URL/Slug, 1000-1500 chữ |
| `forum` | (không có) | 1 URL (truyện hoặc danh mục) (+ optional keyword) | plain text, **3 post** biến thể; mỗi post = câu hỏi hook + body 500–1000 chữ + CTA URL trần |
| `blog20` | `review` \| `toplist` \| `genre` \| `versus` \| `guide` | như pbn tương ứng (KHÔNG có `faq`) | HTML thuần (không JSON-LD), **KHÔNG** block URL/Slug, **KHÔNG** self-link, 1000-1500 chữ |

**Tham số:**
- `--site <domain>` — domain đăng bài PBN (1 trong `data/pbn-domains.txt`). Dùng ghép URL bài `https://{site}/{slug}/` + đối chiếu domain hợp lệ. **Thiếu ở mọi subtype pbn (review/toplist/faq/genre/versus/guide) → HỎI LẠI, KHÔNG đoán.** **`blog20` KHÔNG dùng `--site`** — không hỏi, không suy luận domain.
- `keyword="..."` **hoặc** `--kw "..."` **hoặc** freeform (`keyword là …`, `viết cho kw …`) — primary keyword do user ép (vd `keyword="truyện điền văn hoàn"`). **Chỉ ảnh hưởng cách viết** (H1/title/body/hook forum); **KHÔNG** đổi pool truyện. List vẫn bám URL danh mục / filter JSON. Dùng cho `pbn` / `blog20` (chủ yếu toplist) và `forum` (tuỳ chọn). Không có → skill auto-resolve (pbn/blog20: xem **"Resolve SEO keyword"**; forum: từ scrape — tên truyện / thể loại).

> **Tương thích input cũ:** nếu user vẫn truyền `--lo <nhãn>`, bỏ qua cả flag và giá trị; không hỏi lại, không báo lỗi và không dùng để lọc dữ liệu.

> **Đã bỏ `--img`.** Ảnh không host trên WordPress domain. Ảnh bìa lấy từ ImgBB (field `anh_imgbb` hoặc upload qua `scripts/imgbb-upload.sh`).

Ví dụ:
```
/content-webnovel bio https://webnovel.vn/ai-bao-han-tu-tien/
/content-webnovel bio https://webnovel.vn/xuyen-khong/
/content-webnovel bio https://webnovel.vn/
/content-webnovel pbn review https://webnovel.vn/ai-bao-han-tu-tien/ --site tonghoixaydungvn.org.vn
/content-webnovel pbn toplist https://webnovel.vn/tien-hiep/ --site tonghoixaydungvn.org.vn
/content-webnovel pbn toplist https://webnovel.vn/dien-van/ keyword="truyện điền văn hoàn" --site tonghoixaydungvn.org.vn
/content-webnovel pbn toplist "Tiên Hiệp" --site fbu.vn
/content-webnovel pbn toplist "Tối Bạch Đích Ô Nha" --site fbu.vn
/content-webnovel pbn faq https://webnovel.vn/tien-hiep/ --site fbu.vn
/content-webnovel pbn genre https://webnovel.vn/tien-hiep/ --site fbu.vn
/content-webnovel pbn genre "Điền Văn" --site fbu.vn
/content-webnovel pbn versus https://webnovel.vn/ai-bao-han-tu-tien/ https://webnovel.vn/... --site fbu.vn
/content-webnovel pbn versus https://webnovel.vn/tien-hiep/ --site fbu.vn
/content-webnovel pbn guide https://webnovel.vn/tien-hiep/ --site fbu.vn
/content-webnovel forum https://webnovel.vn/ngon-tinh/
/content-webnovel forum https://webnovel.vn/ai-bao-han-tu-tien/
/content-webnovel forum https://webnovel.vn/dien-van/ keyword="truyện điền văn full"
/content-webnovel blog20 review https://webnovel.vn/ai-bao-han-tu-tien/
/content-webnovel blog20 toplist https://webnovel.vn/dien-van/ keyword="truyện điền văn hoàn"
/content-webnovel blog20 toplist "Tối Bạch Đích Ô Nha"
```

Nếu user chỉ gửi URL + mô tả bằng lời ("viết bio cho truyện này", "làm bài review", "top truyện xuyên không cho fbu.vn", "top truyện của Tối Bạch Đích Ô Nha", "bài hỏi đáp forum", "forum webnovel", "viết blog20 review", "blog20 toplist", "keyword điền văn full", "giải thích thể loại tiên hiệp", "tiên hiệp là gì", "so sánh truyện A với truyện B", "truyện A hay truyện B hơn", "cẩm nang đọc ngôn tình cho người mới", "người mới nên bắt đầu từ đâu") → tự map sang type/subtype + tham số tương ứng.

**Pattern chuẩn pbn toplist danh mục + keyword (khuyến nghị):**
```
/content-webnovel pbn toplist <URL_DANH_MỤC> keyword="<primary keyword>" --site <domain>
```
→ URL = pool list truyện; keyword = cách viết SEO. Cả hai dùng cùng lúc cho chính xác hơn.

---

## Nguồn dữ liệu truyện (dùng cho pbn/blog20 toplist + ảnh)

Skill đọc file JSON đã cào sẵn để chọn đúng truyện theo thể loại/tác giả và lấy ảnh:

```
data/truyen-data.json
```

- File này **đồng bộ tự động** từ skill `/crawl-data-webnovel`: mỗi lần user chạy crawl, `crawl.py` ghi bản chính vào `~/Downloads/webnovel/truyen-data.json` **và copy 1 bản** vào `data/truyen-data.json` của skill này. Không cần sync tay.
- Mỗi record: `tu_khoa`, `slug`, `link_truyen`, `anh_local`, `anh_url` (CDN webnovel — **không** hotlink trong bài PBN), `anh_imgbb` (direct URL ImgBB — **ưu tiên dùng**), `danh_muc`, `tac_gia`.
- **File ảnh local** = `~/Downloads/webnovel/{anh_local}` — chỉ dùng khi `anh_imgbb` trống (upload mới qua ImgBB).
- **Review:** tìm record trên toàn bộ JSON bằng `link_truyen` đã chuẩn hoá (bỏ trailing slash khi so sánh); nếu chưa khớp thì fallback theo `slug` lấy từ URL input. Record khớp dùng để lấy `anh_imgbb` / `anh_local`. Không có record khớp → vẫn scrape live và áp quy tắc báo thiếu ảnh hiện tại; không bịa hoặc hotlink ảnh.
- **Toplist:** đọc toàn bộ JSON rồi lọc trực tiếp theo thể loại (`danh_muc`) hoặc tác giả (`tac_gia`).

Nếu file không tồn tại hoặc **pool = 0** sau lọc theo tiêu chí → **fallback scrape live** URL danh mục (thể loại) / dừng (tác giả). Pool = 1 → auto-switch review (xem pbn toplist).

---

## BƯỚC 1 — Scrape dữ liệu (BẮT BUỘC trước khi viết)

Với `pbn toplist` / `blog20 toplist` lấy pool từ JSON: scrape chỉ khi cần `CAT_TITLE` từ URL danh mục, khi fallback `pool=0`, hoặc khi auto-switch review 1 truyện. Các type khác: luôn scrape trước, KHÔNG tự đoán nội dung từ slug URL.

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

1. **type** do user khai báo (`bio` / `pbn` / `forum` / `blog20`). Không có → hỏi lại, KHÔNG đoán.
2. **bio subtype** = suy từ `PAGE_TYPE` của scrape:
   - `homepage` → **bio homepage**
   - `category` → **bio danhmuc**
   - `story` → **bio tentruyen**
3. **pbn subtype** do user khai báo (`review` / `toplist` / `faq` / `genre` / `versus` / `guide`). Không có → hỏi lại.
   - `review` + `faq` yêu cầu đúng loại trang phù hợp; `toplist` / `genre` / `guide` nhận URL danh mục **hoặc** tên thể loại/tác giả gõ tay; `versus` nhận 2 URL truyện / 2 tên / URL danh mục.
   - Mọi subtype pbn cần `--site`. Thiếu → hỏi lại (không đoán).
4. **forum**: không subtype, bám theo `PAGE_TYPE` (story → post hỏi đáp về truyện; category → post hỏi đáp về thể loại). Keyword tuỳ chọn (xem **LOẠI forum**).
5. **blog20 subtype** do user khai báo (`review` / `toplist` / `genre` / `versus` / `guide` — **KHÔNG** có `faq`). Không có → hỏi lại.
   - `review` nhận 1 URL truyện; `toplist` / `genre` / `guide` nhận URL danh mục **hoặc** tên thể loại/tác giả gõ tay; `versus` nhận 2 URL truyện / 2 tên / URL danh mục.
   - Các subtype đọc toàn bộ `data/truyen-data.json` khi cần tìm record hoặc lọc pool.
   - **KHÔNG** yêu cầu, hỏi hoặc suy luận `--site` hay domain đăng bài ở bất kỳ nhánh nào.

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

## Category-class — fiction vs non-fiction (danh từ "truyện" / "sách")

~48% pool là **sách non-fiction** (self-help / tâm linh), không phải "truyện". Trước khi sinh title/entity/CTA cho **mọi** subtype pbn/blog20, xác định category-class từ `danh_muc` (hoặc `CAT_TITLE` scrape):

- **Non-fiction set** (mở rộng khi crawl thêm): `Phát triển bản thân`, `Tâm linh`.
- **Còn lại = fiction** (default khi không rõ / nhiều thể loại lẫn).

**Noun-swap áp cho TẤT CẢ touchpoint:**

| Touchpoint | fiction | non-fiction |
|---|---|---|
| Danh từ chính | truyện | sách / tác phẩm |
| Động từ đọc | đọc / cày | đọc (KHÔNG "cày") |
| Alt text ảnh (xem mục Ảnh bìa) | `[Tên] – truyện [thể loại]` | `[Tên] – sách [thể loại]` |
| Connotation wording | "cày liền mạch", "từ nhập môn tới nghiện" | "đáng suy ngẫm", "được yêu thích" (KHÔNG "nghiện/cày") |
| H1 / câu định nghĩa entity / CTA | truyện | sách |

Ký hiệu `[noun]` trong các công thức title/H1 bên dưới = "truyện" (fiction) hoặc "sách" (non-fiction) theo category-class.

---

## Title pool — chống "nhàm" cho review + toplist (deterministic theo hash)

Vấn đề: title 1 công thức cứng → search result bài nào cũng giống nhau. Pool xoay theo hash cho đa dạng **across-bài** mà vẫn stateless/tái tạo được, KHÔNG phá contract SEO (keyword + `[năm]`).

### Pool title review (6 công thức)

`h` = tổng code-point của `slug` truyện (đã có sẵn ở "Góc review"). **Index = `(h // 3) mod 6`** (`// 3` để tách khỏi verdict `h mod 3`, hai thứ xoay độc lập). Slot đầu = **primary keyword đã resolve** (tên truyện với review), giữ `[năm]` trong H1:

| # | Công thức (fiction; non-fiction đổi `[noun]`/connotation) |
|---|---|
| 0 | `Review [Tên] – [noun] [thể loại] [năm]` |
| 1 | `[Tên] có đáng đọc? Review [noun] [thể loại] [năm]` |
| 2 | `[Tên] – [noun] [thể loại] khiến người đọc cày liền mạch [năm]` (non-fiction: `…đáng suy ngẫm [năm]`) |
| 3 | `[Tên]: [thể loại] nên đọc hay bỏ qua? Review [năm]` |
| 4 | `[Tên] – trải nghiệm đọc [noun] [thể loại] [năm]` |
| 5 | `[Tên] – [neo góc chính] [noun] [thể loại] [năm]` (neo theo góc chính đã chọn) |

- **Ngoại lệ auto-switch dual-entity:** khi ở nhánh auto-switch pool=1 (xem "Auto-switch pool=1 → review"), H1 dual-entity `Review [Tên] – [primary keyword] [năm]` **thắng** pool (giữ đúng contract dual-entity), KHÔNG dùng pool.

### Pool title toplist (5 công thức)

Seed = `h_top` = tổng code-point của **chuỗi target đã chuẩn hoá** (tên thể loại sau strip "Truyện ", hoặc tên tác giả) — luôn tồn tại TRƯỚC khi sinh title (article slug sinh *sau* H1 nên KHÔNG seed được trên slug; input tên/tác giả cũng không có slug URL). **Index = `(h_top // 3) mod 5`**. Giữ N + primary keyword + `[năm]`:

| # | Công thức |
|---|---|
| 0 | `Top N [noun] [thể loại] hay nhất [năm]` |
| 1 | `Hết [noun] để đọc? N [noun] [thể loại] nên đọc [năm]` |
| 2 | `N [noun] [thể loại] được nhắc nhiều [năm] và vì sao đáng đọc` |
| 3 | `Mê [noun] [thể loại]? N gợi ý hay [năm]` |
| 4 | `N [noun] [thể loại] [năm]: từ nhập môn tới nghiện` (non-fiction: `…từ nhập môn tới yêu thích`) |

- N = **pool thật** (không bịa để đủ số); "hoàn/full" chỉ khi data đỡ; **cấm** claim "đọc nhiều nhất / bán chạy" nếu data không có.
- **Announce title pool (ngoài HTML), như dòng góc review:** `Title pool: review #[i]` hoặc `toplist #[i]` (thể loại: [X], class: [fiction/non-fiction]).

---

## LOẠI pbn — HTML thuần, 1000-1500 chữ (KHÔNG JSON-LD)

Nguyên tắc chung SEO/GEO/AEO (áp cho **mọi** subtype):
- **Câu định nghĩa entity dứt khoát ở đầu bài** (ngay sau/trong đoạn mở) — cho **ENTITY CHÍNH** của bài:
  - review / toplist / faq: truyện hoặc thể loại — "*[Tên] là [noun] [thể loại] của tác giả [X], [đặc điểm]*".
  - genre: thể loại — "*[Thể loại] là dòng [noun] [đặc trưng cốt lõi]…*".
  - versus: cả 2 truyện — mỗi truyện 1 câu định nghĩa.
  - guide: thể loại (góc người mới) — "*[Thể loại] là dòng [noun]… phù hợp người mới vì…*".
  Đây là câu AI dễ trích dẫn nhất — BẮT BUỘC có ở mọi subtype.
- **Answer-first** chỉ ở: đoạn intro, mỗi câu FAQ, đầu mỗi mục toplist. KHÔNG nhồi answer-first vào mọi đoạn (đọc như bot → mất E-E-A-T).
- Có **bảng hoặc list** (dễ ăn featured snippet + AI trích).
- **Freshness:** H1 + intro có năm hiện tại (2026).
- **Brand tiết chế:** "Webnovel.vn" xuất hiện tối đa 2-3 lần/bài **dạng text**, chủ yếu ở CTA. Giữ giọng blogger bên thứ 3, KHÔNG nhồi quảng cáo.
- **Backlink unique (BẮT BUỘC):** mỗi URL `webnovel.vn` (bất kỳ path) chỉ được chèn **đúng 1 lần** dưới dạng `<a href="...">` trong toàn bộ HTML. Trùng URL = vi phạm.
  - `review` / `faq`: đúng **1** backlink — đặt ở **CTA cuối**. Chỗ khác (bảng info, đoạn giữa) chỉ text "Webnovel.vn", không bọc `<a>`.
  - `toplist`: mỗi truyện **1** link `link_truyen` riêng (N URL khác nhau → N thẻ `<a>`, mỗi URL 1 lần). Bảng so sánh **không** lặp lại link đã dùng ở mục truyện (chỉ text tên hoặc "xem ở mục trên"). CTA cuối: 1 link danh mục **nếu URL đó chưa dùng** ở item nào.
  - Auto-switch review từ danh mục (pool=1): cho phép **2** backlink webnovel khác nhau — 1 link truyện (CTA) + 1 link danh mục (**chỉ trong intro** — không đặt trong H2 thân giữa theo góc). Mỗi URL vẫn chỉ 1 lần.
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

### Ảnh bìa ImgBB (review / toplist / genre / versus / guide)

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
  <img src="{imgbb_url}" alt="[Tên] – [noun] [thể loại chính]" loading="lazy" referrerpolicy="no-referrer">
</a>
```

- Bọc `<a rel="nofollow noopener" target="_blank">` quanh ảnh (link ra host ngoài).
- **Alt text:** `[Tên] – [noun] [thể loại chính]` (thể loại đầu trong `danh_muc`; `[noun]` = "truyện" fiction / "sách" non-fiction theo Category-class).
- Truyện không có `anh_imgbb` + không upload được (thiếu file/key/fail) / đến từ fallback scrape live → **báo user rõ** — **KHÔNG** fallback path WP, **KHÔNG** hotlink `cdn.webnovel.vn`.

### H2 mục giải đáp (thay cho "FAQ")

Bỏ chữ "FAQ" tiếng Anh ở heading user-facing. Chọn **1** H2 theo subtype (xoay pool cho đa dạng giữa các bài):

`[noun]` = "truyện" (fiction) / "sách" (non-fiction) theo Category-class.

| Subtype | Mặc định | Biến thể xoay |
|---|---|---|
| **review** | `Giải đáp tò mò về [noun] [Tên]` | `Thắc mắc thường gặp về [Tên]` · `Đọc [Tên]: những câu hỏi hay gặp` |
| **toplist / genre / guide** (thể loại) | `Giải đáp tò mò về [noun] [Thể loại]` | `Câu hỏi thường gặp khi chọn [noun] [Thể loại]` · `Thắc mắc hay gặp về [noun] [Thể loại]` |
| **toplist** (tác giả) | `Giải đáp tò mò về [noun] của [Tác giả]` | `Thắc mắc thường gặp về [Tác giả]` |
| **versus** | `Giải đáp tò mò khi chọn giữa [Tên A] và [Tên B]` | `Thắc mắc thường gặp: nên đọc [Tên A] hay [Tên B]?` |
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

### Góc review (chống "một màu") — áp cho MỌI dạng review

Định nghĩa **một lần ở đây**; `blog20 review` và auto-switch pool=1 chỉ tham chiếu lại, KHÔNG mô tả lại.

Vấn đề: nếu bài review nào cũng cùng khung Điểm mạnh / Điểm yếu / Hợp với ai + box điểm x/10 thì đọc bài nào cũng giống nhau. Cơ chế "Góc review" đa dạng hóa **phần thân giữa + verdict + câu mở**, giữ nguyên toàn bộ contract SEO/GEO.

**Pool 8 góc** (mỗi góc = trọng tâm + gợi ý H2, tự đặt lại tên H2 cho hợp truyện):

| # | Góc | Trọng tâm | Gợi ý H2 |
|---|---|---|---|
| 0 | Nhân vật | Nam/nữ chính, phản diện, quan hệ | "Nhân vật khiến người đọc nhớ" · "Cặp đôi chính có gì đáng theo dõi" |
| 1 | Thế giới & hệ thống | Bối cảnh, hệ thống tu luyện/ma pháp/quy tắc | "Thế giới trong truyện" · "Hệ thống [tu luyện/…] có gì lạ" |
| 2 | Cảm xúc & trải nghiệm đọc | Bài đem lại cảm giác gì, nhịp cày | "Đọc truyện này cảm giác thế nào" · "Vì sao dễ cày liền mạch" |
| 3 | Motip & khác biệt | So với motip chung của thể loại | "Có gì khác truyện [thể loại] thường gặp" · "Motip quen xử lý mới" |
| 4 | Cốt truyện & nhịp kể | Dẫn dắt, cao trào, tiết tấu | "Mạch truyện dẫn dắt ra sao" · "Nhịp truyện nhanh hay chậm" |
| 5 | Đối tượng phù hợp | Ai nên / không nên đọc | "Truyện hợp gu người đọc nào" |
| 6 | Highlight & điểm sáng | Điểm sáng đáng nhớ | "Những điểm sáng đáng nhớ" |
| 7 | So sánh nhẹ | Đặt cạnh dòng truyện cùng thể loại | "Đứng ở đâu trong dòng truyện [thể loại]" |

**Mapping thể loại → nhóm góc ưu tiên** (match `GENRES`/`danh_muc`, không phân biệt hoa thường):

| Thể loại | Nhóm ưu tiên (theo #) |
|---|---|
| Tiên hiệp / Huyền huyễn / Tu tiên | 1, 3, 0 |
| Ngôn tình / Điền văn / Đô thị / Tình cảm | 0, 2, 5 |
| Trinh thám / Huyền nghi / Kinh dị | 4, 6, 7 |
| Xuyên không / Trọng sinh / Hệ thống | 3, 0, 1 |
| Không match / nhiều thể loại lẫn | pool chung 8 góc (0-7) |

**Chọn góc — DETERMINISTIC theo slug (skill stateless, KHÔNG nhớ bài trước):**
1. Tính `h` = tổng mã ký tự (code point) của `slug` truyện.
2. Gọi `nhóm` = danh sách góc ưu tiên của thể loại (thể loại đầu trong `GENRES`/`danh_muc`); không match → pool chung 8 góc.
3. **Góc chính** = `nhóm[h mod len(nhóm)]`.
4. **Góc phụ** = `nhóm[(h + 1) mod len(nhóm)]`.
   - **Invariant:** mỗi nhóm ưu tiên phải có **≥ 2 góc**. Nếu một nhóm (nay hoặc sau này) có < 2 góc → lấy góc phụ từ **pool chung 8 góc** (góc kế tiếp khác góc chính) để phụ không trùng chính.
- Cùng 1 truyện → luôn cùng góc (ổn định, tái tạo được). Truyện khác nhau cùng thể loại → phân tán qua nhiều góc → đa dạng across-truyện mà không cần state.

**Góc chi phối những gì:**
- **Câu mở:** góc chính định hình cách mở (vd góc Nhân vật → mở bằng nhân vật; góc Cảm xúc → mở bằng cảm giác đọc). **CẤM mở bài bằng chữ "Review"/"Top"** (đó là title, không phải câu mở) — dẫn bằng góc-hook trước. **BẮT BUỘC vẫn có câu định nghĩa entity** ("[Tên] là [noun] [thể loại] của [tác giả]…") ở đâu đó trong đoạn mở cho AEO. Non-fiction: dùng "sách", tránh từ "cày" trong gợi ý H2 góc #2 (đổi "nhịp cày / cày liền mạch" → "nhịp đọc / cuốn liền mạch").
- **Thân giữa:** thay 3 khối cứng (Điểm mạnh / Điểm yếu / Hợp với ai) bằng **2-3 H2 sinh theo góc chính + góc phụ**.
- **Mục "Giải đáp tò mò":** câu Q&A bám góc chính khi hợp.

**Guard cứng theo góc (BẮT BUỘC — chống bịa & phá backlink):**
- **Highlight & điểm sáng (#6):** chỉ dựa dữ liệu `SUMMARY` đã scrape; **CẤM** spoiler kết, CẤM bịa cảnh không có trong summary.
- **So sánh nhẹ (#7):** chỉ so ở mức **motip / thể loại chung**; **CẤM nêu tên truyện khác** trừ khi truyện đó có trong pool JSON; **CẤM sinh thêm bất kỳ URL webnovel.vn nào**.
- **H2 thân giữa (mọi góc):** chỉ **text + list**, **KHÔNG** chứa thẻ `<a>` webnovel.vn, **KHÔNG** self-link thứ 2. Toàn bộ đếm backlink/self-link giữ nguyên contract (mục backlink unique + self-link ở đầu LOẠI pbn).
- **Bám SUMMARY (mọi góc, đặc biệt #4 Cốt truyện / #0 Nhân vật / #1 Thế giới):** mọi H2 thân giữa chỉ dựa dữ liệu `SUMMARY` đã scrape; **CẤM spoiler kết**, **CẤM dựng tình tiết / nhân vật / bối cảnh / cao trào không có trong SUMMARY**.

**Verdict xoay (thay box "x/10" cứng)** — chọn 1 trong 3 dạng theo `h mod 3`:
- `0` → **điểm số**: "Đánh giá tổng: x/10" + 1 câu lý do. **Điểm phải bám dữ liệu scrape**; CẤM bịa số lượt đọc/rating nếu JSON/scrape không có.
- `1` → **verdict chữ**: "Đáng đọc nếu…" / "Nên thử khi…" (không số).
- `2` → **chốt cảm nhận** ngắn, không điểm số.

**Announce góc (NGOÀI block HTML, như dòng "Pool = 1…"):**
```
Góc review: [góc chính] + [góc phụ] (thể loại: [X], verdict: [dạng])
```
Đặt trước block meta/HTML để không lẫn vào bài đăng.

### pbn review (1 URL truyện)
Cấu trúc (**áp Góc review** ở trên):
1. Dòng announce góc (ngoài HTML)
2. Block meta `URL` + `Slug`
3. `<h1>` — chọn theo **Pool title review** (`(h//3) mod 6`, xem section Title pool); giữ tên truyện ở slot đầu + `[năm]`. Non-fiction → `[noun]`="sách".
4. Đoạn mở: **câu mở theo góc chính** (KHÔNG mở bằng "Review") + câu định nghĩa entity → **1 self-link** về URL bài → TL;DR 2-3 câu. Ngay dưới chèn **1 ảnh ImgBB** (nếu có).
5. `<table>` thông tin nhanh: Tác giả / Thể loại / Tình trạng / Đọc tại (**text** "Webnovel.vn", không link)
6. `<h2>` Nội dung truyện — tóm tắt cốt (KHÔNG spoiler kết) — **khối lõi, luôn giữ**
7. **2-3 `<h2>` theo góc chính + góc phụ** (thay cho Điểm mạnh / Điểm yếu / Hợp với ai). Chỉ text + list, KHÔNG `<a>` webnovel.vn, KHÔNG self-link.
8. **Verdict xoay** theo `h mod 3` (điểm x/10 / verdict chữ / chốt cảm nhận)
9. `<h2>` theo pool "Giải đáp tò mò…" — 3-4 câu Q&A **đặc thù truyện này**, bám góc chính khi hợp
10. CTA đọc full: **duy nhất 1** `<a href="{link truyện}">` về webnovel.vn

### pbn toplist (theo THỂ LOẠI hoặc theo TÁC GIẢ)

Toplist có 2 kiểu lọc — xác định từ input user:
- **Theo thể loại:** URL danh mục (`https://webnovel.vn/tien-hiep/`) hoặc tên thể loại gõ tay ("top truyện tiên hiệp").
- **Theo tác giả:** user nêu tên tác giả ("top truyện của Tối Bạch Đích Ô Nha", "toplist tác giả Nhĩ Căn").

**Nguồn truyện (BẮT BUỘC theo thứ tự ưu tiên):**

1. **Đọc toàn bộ `data/truyen-data.json`** rồi lọc pool:
   - Kiểu **thể loại** → lọc record có `danh_muc` chứa thể loại target (match không phân biệt hoa thường: "Tiên Hiệp", "Xuyên Không", "Ngôn Tình", "Điền Văn"...).
   - Kiểu **tác giả** → lọc record có `tac_gia` khớp tên tác giả target (không phân biệt hoa thường; chấp nhận khớp gần đúng).
2. **Xác định target (tên thể loại/tác giả để LỌC — không phải SEO keyword):**
   - Thể loại từ URL danh mục → scrape live lấy `CAT_TITLE`, bỏ tiền tố "Truyện " nếu có (vd "Truyện Tiên Hiệp" → "Tiên Hiệp"; "Truyện Điền Văn" → "Điền Văn").
   - Thể loại / tác giả gõ tay → dùng đúng tên đó (chuẩn hoá hoa/thường).
3. **Nhánh theo kích thước pool (sau lọc theo tiêu chí):**
   - **`pool >= 2`** → viết **toplist**. N = số truyện lấy được (khuyến nghị top 5–10; 2 truyện vẫn toplist "Top 2").
   - **`pool == 1`** → **TỰ CHUYỂN `pbn review`** truyện đó (xem **"Auto-switch pool=1 → review"**). **KHÔNG** viết "Top 1…".
   - **`pool == 0`** (hoặc JSON không tồn tại/rỗng) → fallback:
     - Kiểu **thể loại**: scrape live URL danh mục (`STORY` lines), KHÔNG có ảnh ImgBB (báo user + gợi ý crawl thêm vào dữ liệu). Nếu scrape cũng ra đúng 1 `STORY` → vẫn auto-switch review.
     - Kiểu **tác giả**: KHÔNG có trang tác giả → báo user "chưa có truyện của tác giả này trong dữ liệu, hãy crawl thêm rồi chạy lại", DỪNG (không bịa).
4. **Chọn N truyện** từ pool khi `pool >= 2` (lấy theo thứ tự trong JSON, cắt theo N).

> Chỉ fallback khi **pool = 0**. Pool 2 truyện **không** scrape live, **không** chuyển review.

**Ảnh bìa mỗi truyện:** dùng `anh_imgbb` từ JSON nếu có; chỉ upload ImgBB khi field trống.

#### Auto-switch pool=1 → review

Khi bước lọc cho ra **đúng 1 truyện**, skill **bắt buộc**:

1. **Announce** rõ trong output (trước meta/HTML):  
   `Pool = 1 ([thể loại|tác giả] "<target>") → chuyển pbn review truyện "<tên>".`
2. Scrape live URL truyện đó (lấy `TITLE`/`AUTHOR`/`GENRES`/`STATUS`/`SUMMARY`) nếu chưa có đủ field; ảnh dùng `anh_imgbb` / upload ImgBB.
3. Viết theo **cấu trúc pbn review** (**áp Góc review** như pbn review), với bổ sung:

**A. Từ toplist THỂ LOẠI (URL/tên danh mục):** — **dual-entity**
- Primary SEO = keyword đã resolve, **không** đổi sang chỉ tên truyện.
- H1 gợi ý: `Review [Tên truyện] – [primary keyword] [năm]` (vd `Review … – truyện điền văn hoàn 2026` nếu user truyền keyword đó).
- Intro: câu định nghĩa truyện + neo thể loại/keyword + **1 self-link** URL bài.
- **Backlink webnovel (2 URL khác nhau, mỗi URL 1 lần):**
  - 1 link truyện (`link_truyen`) — CTA cuối
  - 1 link danh mục (URL user đưa) — **chỉ đặt trong intro** (KHÔNG đặt trong H2 góc thân giữa)
- Mục giải đáp: 3–4 câu — phần lớn về truyện, **1–2 câu** về thể loại/keyword.
- Ảnh ImgBB như review thường.

**B. Từ toplist TÁC GIẢ:**
- H1 gợi ý: `Review [Tên truyện] – truyện của [Tác giả] [năm]` (hoặc keyword user nếu có).
- **Backlink:** 1 link truyện (CTA).
- **Không bịa** URL trang tác giả.
- Nếu record có `danh_muc` → **thêm 1 link danh mục chính** = thể loại đầu (map URL webnovel nếu biết; không chắc thì chỉ nêu tên thể loại + link truyện).
- Mục giải đáp: về truyện + 1 câu về phong cách tác giả.

4. Giữ contract `--site`. Output HTML thuần + meta URL/Slug (không JSON-LD).

#### Cấu trúc toplist (khi pool >= 2)

Trước khi viết: chạy **Resolve SEO keyword** (thể loại) — H1/body bám primary + biến thể; list truyện vẫn theo target lọc.

1. Block meta `URL` + `Slug`
2. `<h1>` — chọn theo **Pool title toplist** (`(h_top//3) mod 5`, xem section Title pool): kiểu thể loại giữ N + primary keyword + `[năm]` (vd `Top N truyện điền văn hoàn hay nhất 2026`); kiểu tác giả thay `[thể loại]` bằng `của [Tên tác giả]` (vd `Top N truyện hay nhất của [Tên tác giả] [năm]`). Non-fiction → `[noun]`="sách".
3. Intro answer-first: liệt kê nhanh N tên + **1 self-link** về URL bài; rải primary keyword 1 lần tự nhiên
4. Đoạn **"Tiêu chí chọn"** (lượt đọc/đánh giá/tình trạng full-đang ra/độ hot) — bắt buộc. Kiểu tác giả: nêu thêm dấu ấn/phong cách chung của tác giả.
   - **Biến thể intro biên tập (kiểu tác giả):** thay đoạn "Tiêu chí chọn" khô bằng 1 đoạn nêu **"dấu ấn qua các tác phẩm"** — chỉ suy từ **phân bố `danh_muc` thật** của tác giả (vd "phần lớn là tiên hiệp, huyền huyễn"). **CẤM bịa** tiểu sử / sự nghiệp / tên thật / "văn phong" không có trong data. Đây là chỗ author được xử lý (KHÔNG có subtype `author` riêng).
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

### pbn genre (giải thích thể loại — URL danh mục hoặc tên thể loại)

Bài định nghĩa + giới thiệu thể loại (mạnh AEO/GEO). Input: URL danh mục **hoặc** tên thể loại gõ tay (+ optional keyword). Đọc `data/truyen-data.json` lọc theo thể loại để lấy pool gợi ý; scrape URL danh mục khi cần `CAT_TITLE`/`CAT_DESC`.

Cấu trúc:
1. Block meta `URL` + `Slug`
2. `<h1>` — fiction: `Truyện [thể loại] là gì? Đặc trưng & N truyện hay nên đọc [năm]`; non-fiction: `Sách [thể loại] là gì? Đặc trưng & N cuốn hay nên đọc [năm]`
3. Đoạn mở answer-first + **câu định nghĩa entity thể loại** ("[Thể loại] là dòng [noun]…") → **1 self-link** về URL bài
4. `<h2>` **Đặc trưng nhận biết** — dựa `CAT_DESC` + kiến thức thể loại chung; **KHÔNG bịa** truyện/nhân vật cụ thể
5. `<h2>` **Vì sao [thể loại] hấp dẫn** — text + list
6. `<h2>` **Gợi ý N [noun] [thể loại] nên bắt đầu** — 3-5 truyện từ pool JSON, mỗi truyện 1-2 câu mức thể loại + **1** backlink `link_truyen` (mỗi URL 1 lần); ảnh ImgBB tùy chọn
7. `<h2>` theo pool "Giải đáp tò mò…" — Q&A về thể loại
8. CTA: link danh mục webnovel **chỉ khi có URL danh mục thật** (input tên → CTA text, **KHÔNG** bịa URL)

**Pool nhỏ (genre + guide — KHÔNG phải list xếp hạng):** pool 1-2 vẫn viết (liệt kê những gì có). **pool==0 + input URL** → giữ CTA link danh mục thật làm backlink duy nhất + ghi chú "chưa có truyện khớp trong dữ liệu". **pool==0 + input tên** (không URL) → announce + **DỪNG** + báo crawl (tránh bài 0 backlink).

### pbn versus (so sánh 2 truyện)

Bài so sánh head-to-head, dễ click + tự nhiên có 2 backlink. Input: **2 URL truyện** / **2 tên** / **1 URL danh mục** (lấy top 2 từ pool).

**Resolve + fail (BẮT BUỘC):**
- **2 tên:** match `tu_khoa` trong JSON (không phân biệt hoa/thường). Zero-match hoặc đa nghĩa (nhiều record khớp) → announce + **DỪNG**, KHÔNG bịa URL.
- **Scrape cả 2 truyện** (lấy `SUMMARY`/`STATUS`/`GENRES` thật cho bảng so sánh). Input 2-truyện/2-tên tường minh mà **scrape fail (rc≠0)** → announce + **DỪNG** (theo Rules "Không bịa"), **KHÔNG** xuất bảng "—".
- **Input danh mục:** pool≥2 → versus; pool==1 → chuyển **pbn review** truyện đó (announce); pool==0 → theo fallback toplist pool==0 (scrape live danh mục; vẫn <2 → review 1 truyện, hoặc DỪNG + báo crawl nếu 0).

Cấu trúc:
1. Block meta `URL` + `Slug`
2. `<h1>` — `[Tên A] hay [Tên B]? Nên đọc [noun] [thể loại] nào [năm]`
3. Đoạn mở: **2 câu định nghĩa entity** (mỗi truyện 1 câu) → **1 self-link** về URL bài
4. `<h2>` mỗi truyện — giới thiệu ngắn (KHÔNG spoiler kết) + **1** backlink `link_truyen`/truyện (2 URL khác nhau, mỗi URL 1 lần) + ảnh ImgBB tùy chọn
5. `<table>` so sánh — Tác giả / Thể loại / Tình trạng / Nhịp-tông (**text-only, KHÔNG** thẻ `<a>`; chỉ dựa data scrape)
6. `<h2>` **Nên đọc cái nào?** — cân bằng: A hợp gu X, B hợp gu Y (cả 2 tích cực vì cùng dẫn về 1 site). **KHÔNG** bịa mâu thuẫn để dìm 1 bên
7. `<h2>` theo pool "Giải đáp tò mò…" — Q&A so sánh
8. CTA: webnovel link **chỉ khi input danh mục** (dùng URL danh mục chưa dùng); input 2-truyện/2-tên → **CTA text-only** (KHÔNG link thứ 3, KHÔNG re-link truyện đã dùng)

### pbn guide (cẩm nang cho người mới — URL danh mục hoặc tên thể loại)

Bài **advisory** cho người mới vào thể loại (KHÁC `genre`: genre = "là gì" định nghĩa; guide = "bắt đầu từ đâu, đọc thế nào"). **KHÔNG có block định nghĩa "…là gì"** — dẫn thẳng bằng lộ trình. Input như genre.

Cấu trúc:
1. Block meta `URL` + `Slug`
2. `<h1>` — `Người mới đọc [noun] [thể loại] nên bắt đầu từ đâu? [năm]`
3. Đoạn mở answer-first tóm lộ trình + neo entity thể loại (góc người mới) → **1 self-link** về URL bài
4. `<h2>` **Bắt đầu từ đâu** — 2-3 truyện dễ tiếp cận từ pool, mỗi truyện + **1** backlink unique
5. `<h2>` **Sau đó khám phá thêm** — nhóm mở rộng; truyện **đã link ở mục 4** = text "xem mục trên", truyện **mới** = backlink unique
6. `<h2>` **Lưu ý cho người mới** — mẹo đọc chung an toàn (KHÔNG bịa data truyện cụ thể)
7. `<h2>` theo pool "Giải đáp tò mò…" — Q&A người mới
8. CTA: link danh mục **chỉ khi có URL thật** (input tên → CTA text)

Áp **Pool nhỏ** như genre (mục pbn genre): pool 1-2 vẫn viết; pool==0 + URL → CTA danh mục là backlink duy nhất + ghi chú; pool==0 + tên → DỪNG + báo crawl.

---

## LOẠI blog20 — HTML thuần, 1000-1500 chữ (review / toplist / genre / versus / guide)

`blog20` là **tên type thuần**. Số `20` **KHÔNG** quyết định số truyện, heading hoặc độ dài danh sách; tuyệt đối không thêm/bịa truyện để đủ 20. `blog20 toplist` dùng đúng quy tắc N và pool của `pbn toplist` (pool `>= 2`, khuyến nghị 5–10 truyện).

### Contract kế thừa

`blog20 review` / `toplist` / `genre` / `versus` / `guide` kế thừa **toàn bộ** contract tương ứng của `pbn` subtype cùng tên (**KHÔNG** có `blog20 faq` — faq chỉ pbn), gồm:
- HTML thuần 1000–1500 chữ, SEO/GEO/AEO, freshness, tone, bảng/list, mục giải đáp và không JSON-LD.
- **Title pool** (review 6 / toplist 5) + **Category-class** noun-swap y hệt pbn.
- Cách scrape, resolve keyword, tra cứu toàn bộ JSON, chọn pool, fallback, auto-switch pool=1, resolve 2-tên versus, quy tắc pool nhỏ genre/guide.
- Backlink unique về `webnovel.vn` và CTA theo đúng subtype.
- Ảnh ImgBB: ưu tiên `anh_imgbb`, thiếu thì upload từ file local; không hotlink CDN, không ghép path WordPress.

**CHỈ có 3 khác biệt bắt buộc so với PBN (áp cho MỌI subtype blog20):**
1. **Không domain:** không nhận, không yêu cầu, không hỏi và không suy luận `--site` hay domain đăng bài ở bất kỳ nhánh nào.
2. **Không meta bài đích:** không sinh/in block `URL:` + `Slug:` và không gợi ý slug.
3. **Không self-link:** đoạn mở không chèn link nội bộ về bài đang viết. Việc bỏ self-link **không** loại bỏ backlink về `webnovel.vn`.

### blog20 review

Dùng cấu trúc `pbn review` từ H1 đến CTA (**áp Góc review** như `pbn review`: chọn góc theo hash slug, câu mở theo góc chính, 2-3 H2 thân giữa theo góc, verdict xoay, dòng announce góc ngoài HTML), nhưng bỏ bước block meta và thay đoạn mở bằng câu định nghĩa entity + TL;DR **không self-link**. URL truyện xuất hiện đúng **1 lần** dưới dạng backlink ở CTA cuối.

### blog20 toplist

Dùng toàn bộ logic pool và cấu trúc `pbn toplist`, nhưng bỏ block meta và intro **không self-link**. Khi pool `>= 2`, mỗi truyện giữ đúng 1 backlink `link_truyen`; CTA danh mục chỉ link khi URL đó chưa dùng.

Khi pool `== 1`, announce và tự chuyển thành **`blog20 review`** (không chuyển thành PBN):
- Từ danh mục: URL truyện đúng 1 lần tại CTA cuối + URL danh mục đúng 1 lần **trong intro** (KHÔNG đặt trong H2 thân giữa theo góc). Không có URL `webnovel.vn` thứ ba.
- Từ tác giả: URL truyện đúng 1 lần tại CTA; chỉ link danh mục chính khi map được URL chắc chắn, không bịa URL.
- Mọi trường hợp vẫn không domain, không block URL/Slug và không self-link.

### blog20 genre / versus / guide

Dùng đúng cấu trúc + quy tắc `pbn genre` / `pbn versus` / `pbn guide` tương ứng, chỉ áp 3 khác biệt blog20 (không `--site`, không block URL/Slug, không self-link). Backlink `webnovel.vn` (mỗi URL 1 lần), Category-class noun-swap, resolve 2-tên versus, quy tắc pool nhỏ genre/guide đều giữ nguyên. `versus` CTA text-only khi input 2-truyện/2-tên; chỉ dùng URL danh mục chưa dùng khi input danh mục.

---

## LOẠI forum — plain text, 3 post hỏi đáp dài (500–1000 chữ/post)

**Không còn** format 10 cặp Q&A ngắn. Mỗi lần chạy sinh **3 post biến thể** — mỗi post là **1 bài hỏi đáp liền mạch** (gần PBN về độ sâu nhưng ngắn hơn, plain text, thiên chủ đề câu hỏi).

### Input
- **URL bắt buộc** (truyện hoặc danh mục). Homepage → hỏi lại / gợi ý URL truyện hoặc danh mục.
- **`keyword="..."` / `--kw` / freeform** — tuỳ chọn. Có → hook + body bám keyword; **không** đổi dữ liệu scrape. Không có → auto primary từ scrape:
  - story → tên truyện (+ thể loại chính nếu hợp)
  - category → `truyện {tên danh mục}` sau strip tiền tố "Truyện " (vd `Truyện Điền Văn` → `truyện điền văn`)
- **Không** cần `--site`. **Không** HTML, **không** meta URL/Slug, **không** ảnh.

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

- **Luôn scrape trước khi viết** (trừ `pbn toplist` / `blog20 toplist` lấy pool từ JSON — scrape chỉ khi fallback `pool=0`, cần `CAT_TITLE` từ URL danh mục, hoặc auto-switch review 1 truyện). Không đoán nội dung từ slug.
- **Không bịa.** Scrape fail (rc≠0) → báo lỗi rõ theo mã lỗi, DỪNG. (Ngoại lệ bio truyện thiếu summary như mô tả trên.)
- **Toplist chọn truyện đúng tiêu chí** từ toàn bộ JSON: lọc theo thể loại (`danh_muc`) hoặc tác giả (`tac_gia`).
- **Tách pool vs keyword:** list truyện bám URL danh mục / filter JSON; keyword (`keyword=` / `--kw` / freeform / auto) chỉ để viết (pbn + blog20 + forum). **Không** dùng keyword để lọc pool.
- **Pool size (sau lọc theo tiêu chí):** `>= 2` → toplist; `== 1` → **auto-switch review cùng type** (announce + dual-entity nếu từ danh mục; author → link truyện + 1 danh mục chính); `== 0` → fallback scrape (thể loại) hoặc dừng (tác giả).
- **Input cũ có `--lo <nhãn>`:** bỏ qua flag và giá trị; không dùng để lọc dữ liệu.
- **PBN bắt buộc `--site`.** Thiếu → hỏi lại. **Blog20 không nhận, hỏi hoặc suy luận `--site`/domain.** Không còn `--img`.
- **Ảnh PBN/blog20:** ưu tiên `anh_imgbb`; thiếu thì upload ImgBB từ file local. Không hotlink CDN webnovel, không ghép path WP.
- **URL bài PBN:** sinh slug từ title, in `URL` + `Slug` trước HTML; 1 self-link internal trong đoạn mở. **Blog20 không có URL/Slug hoặc self-link.**
- **Không schema/JSON-LD** trong output pbn/blog20.
- **`blog20` là tên type, không phải số lượng:** không ép đủ 20 truyện; dùng N theo pool như PBN toplist.
- **Góc review (mọi dạng review):** `pbn review` / `blog20 review` / auto-switch pool=1 phải chọn góc deterministic theo hash slug (xem "Góc review"), câu mở + 2-3 H2 thân giữa theo góc, verdict xoay `h mod 3`, announce góc ngoài HTML. H2 thân giữa KHÔNG chứa `<a>` webnovel.vn / self-link; đếm backlink giữ nguyên contract.
- **Title pool (review + toplist):** H1 chọn từ pool theo hash (review `(h//3) mod 6`; toplist `(h_top//3) mod 5`) — giữ primary keyword slot đầu + `[năm]`; announce dòng "Title pool: …" ngoài HTML. Câu mở review CẤM bắt đầu bằng "Review"/"Top". Auto-switch dual-entity H1 thắng pool khi ở nhánh auto-switch.
- **Category-class:** trước khi sinh title/entity/CTA/alt, phân loại fiction / non-fiction (set non-fiction = Phát triển bản thân, Tâm linh). Non-fiction → danh từ "sách", tránh "cày/nghiện". Áp mọi touchpoint (xem section Category-class).
- **Subtype mới:** `genre` (định nghĩa thể loại) / `versus` (so 2 truyện, scrape cả 2, table text-only, resolve 2-tên qua `tu_khoa`, fail tường minh → DỪNG) / `guide` (advisory người mới, KHÔNG block "…là gì"). genre+guide pool nhỏ: 1-2 vẫn viết; pool==0 + tên (không URL) → DỪNG + báo crawl. CTA link danh mục chỉ khi có URL thật, KHÔNG bịa URL.
- **Author KHÔNG phải subtype:** xử lý trong toplist author-mode (biến thể intro "dấu ấn qua các tác phẩm" từ `danh_muc` thật; cấm bịa tiểu sử).
- Toàn bộ content **tiếng Việt**.
- Type do user khai báo; subtype bio auto-detect; subtype pbn (review/toplist/faq/genre/versus/guide) / blog20 (review/toplist/genre/versus/guide — KHÔNG faq) do user khai báo — **ngoại lệ:** toplist/versus pool=1 được phép tự chuyển review cùng type (phải announce).
- bio: plain text 10 biến thể trong chat. **forum: plain text 3 post** (hook Q + body 500–1000 chữ + CTA URL trần). pbn: HTML thuần + meta URL/Slug. blog20: HTML thuần, không meta URL/Slug/self-link.
- Sau khi tạo content xong: hỏi user có muốn push skill lên repo không (nếu vừa sửa skill).

## Scripts & Data
- `scripts/scrape.sh` — live-scrape webnovel.vn (curl browser-UA), auto-detect loại trang, in field dạng `KEY<TAB>value`. Fail rõ ràng rc 2/3/4/5.
- `scripts/imgbb-upload.sh` — upload 1 ảnh lên ImgBB, stdout = direct URL. Key: `IMGBB_API_KEY` hoặc `~/.config/imgbb/api_key`. rc 2/3/4 khi lỗi.
- `data/truyen-data.json` — pool truyện đã crawl (đồng bộ từ `/crawl-data-webnovel`). Có `anh_imgbb`; toàn bộ record được xét khi tra cứu/lọc.
- `data/pbn-domains.txt` — domain PBN hợp lệ (đối chiếu `--site`). Dùng ghép URL bài, **không** host ảnh.
- `CHEATSHEET.md` — input cheat sheet (update cùng SKILL khi đổi Usage).

## Category
content-seo
