---
name: content-webnovel
description: >-
  Tạo content marketing tiếng Việt cho website đọc truyện Webnovel.vn (https://webnovel.vn/) từ URL bài truyện/danh mục/homepage.
  Live-scrape trang bằng curl (browser UA) để lấy dữ liệu thật (tên truyện, tác giả, thể loại, tóm tắt, tình trạng, list truyện), rồi sinh 3 nhóm content theo yêu cầu:
  bio (mô tả ngắn 120-150 ký tự, 10 biến thể, có hashtag), pbn (bài blog SEO/GEO/AEO 1000-1500 chữ dạng review/toplist/faq, xuất HTML + JSON-LD), forum (10 cặp Q&A FAQ gây tò mò).
  Trigger: "/content-webnovel", "content webnovel", "viết bio truyện webnovel", "viết pbn webnovel", "faq forum webnovel", hoặc khi user gửi URL webnovel.vn kèm yêu cầu tạo content.
---

# Skill: content-webnovel

Tạo content marketing cho **Webnovel.vn** (website đọc truyện chữ có bản quyền) từ URL. Skill live-scrape trang thật rồi viết content tiếng Việt theo đúng loại/subtype yêu cầu. **Không bịa** — thiếu dữ liệu thật thì báo lỗi và dừng.

## Repo

Skill đồng bộ với repo GitHub: **https://github.com/minhtranquang1993/content-webnovel** (branch `main`).
- **Push:** copy `SKILL.md` + `scripts/` vào clone local của repo, commit, push.
- **Pull:** lấy từ repo, ghi đè vào `C:\Users\Admin\.claude\skills\content-webnovel\`.

## Usage

```
/content-webnovel <type> [subtype] <url> [--site <domain>] [--img <YYYY/MM>]
```

| type | subtype | input | output |
|---|---|---|---|
| `bio` | (auto-detect từ URL) | 1 URL (homepage / danh mục / truyện) | plain text, 10 biến thể, 120-150 ký tự |
| `pbn` | `review` \| `toplist` \| `faq` | review→1 URL truyện; toplist→URL danh mục / tên thể loại / tên tác giả; faq→1 URL | HTML + JSON-LD, 1000-1500 chữ |
| `forum` | (không có) | 1 URL (truyện hoặc danh mục) | plain text, 10 cặp Q&A |

**Tham số cho pbn (chỉ pbn dùng ảnh):**
- `--site <domain>` — domain sẽ đăng bài PBN (1 trong list `data/pbn-domains.txt`). Quyết định origin của ảnh + CTA.
- `--img <YYYY/MM>` — tháng đã upload ảnh lên WordPress (vd `2026/07`). Ghép vào URL ảnh. **Thiếu tham số này ở `pbn review`/`pbn toplist` → HỎI LẠI user tháng, KHÔNG tự đoán tháng hiện tại.**

Ví dụ:
```
/content-webnovel bio https://webnovel.vn/ai-bao-han-tu-tien/
/content-webnovel bio https://webnovel.vn/xuyen-khong/
/content-webnovel bio https://webnovel.vn/
/content-webnovel pbn review https://webnovel.vn/ai-bao-han-tu-tien/ --site tonghoixaydungvn.org.vn --img 2026/07
/content-webnovel pbn toplist https://webnovel.vn/tien-hiep/ --site tonghoixaydungvn.org.vn --img 2026/07
/content-webnovel pbn toplist "Tiên Hiệp" --site fbu.vn --img 2026/07
/content-webnovel pbn toplist "Tối Bạch Đích Ô Nha" --site fbu.vn --img 2026/07
/content-webnovel pbn faq https://webnovel.vn/tien-hiep/ --site fbu.vn
/content-webnovel forum https://webnovel.vn/ngon-tinh/
```

Nếu user chỉ gửi URL + mô tả bằng lời ("viết bio cho truyện này", "làm bài review", "top truyện xuyên không cho fbu.vn", "top truyện của Tối Bạch Đích Ô Nha", "faq forum") → tự map sang type/subtype + tham số tương ứng.

---

## Nguồn dữ liệu truyện (dùng cho pbn toplist + ảnh)

Skill đọc file JSON đã cào sẵn để chọn đúng truyện theo thể loại/tác giả và lấy slug ảnh:

```
data/truyen-data.json
```

- File này **đồng bộ tự động** từ skill `/crawl-data-webnovel`: mỗi lần user chạy crawl, `crawl.py` ghi bản chính vào `~/Downloads/webnovel/truyen-data.json` **và copy 1 bản** vào `data/truyen-data.json` của skill này. Không cần sync tay.
- Mỗi record: `tu_khoa` (tên truyện), `slug`, `link_truyen`, `anh_local`, `anh_url` (ảnh CDN webnovel), `danh_muc` (mảng thể loại tiếng Việt chuẩn), `tac_gia` (tên tác giả).
- **Tên file ảnh trên WordPress = `<slug>.webp`** (khớp `anh_local`). Đây là cơ sở để ghép URL ảnh PBN.

Nếu file không tồn tại (máy chưa chạy crawl) hoặc thiếu truyện cho tiêu chí yêu cầu → **fallback scrape live** URL danh mục như luồng cũ.

Công thức URL ảnh + quy tắc chèn theo subtype: xem mục **"Ghép URL ảnh cho bài PBN"** trong phần LOẠI pbn. Thiếu `--site`/`--img` ở review/toplist → hỏi lại, không đoán.

---

## BƯỚC 1 — Scrape dữ liệu (BẮT BUỘC trước khi viết)

Với `pbn toplist` lấy pool từ JSON: scrape chỉ khi cần `CAT_TITLE` từ URL danh mục, hoặc khi fallback. Các type khác: luôn scrape trước, KHÔNG tự đoán nội dung từ slug URL.

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
   - `review` + `faq` yêu cầu đúng loại trang phù hợp; `toplist` nhận URL danh mục **hoặc** tên thể loại gõ tay.
   - `pbn review` / `pbn toplist` cần `--site` + `--img`. Thiếu → hỏi lại trước khi viết (không đoán tháng, không đoán domain).
4. **forum**: không subtype, bám theo `PAGE_TYPE` (story → FAQ về truyện; category → FAQ về thể loại).

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

## LOẠI pbn — HTML + JSON-LD, 1000-1500 chữ

Nguyên tắc chung SEO/GEO/AEO (áp cho cả 3 subtype):
- **Câu định nghĩa entity dứt khoát ở đầu bài** (ngay sau/trong đoạn mở): "*[Tên] là truyện [thể loại] của tác giả [X], [đặc điểm nổi bật]*" — câu AI dễ trích dẫn nhất.
- **Answer-first** chỉ ở: đoạn intro, mỗi câu FAQ, đầu mỗi mục toplist. KHÔNG nhồi answer-first vào mọi đoạn (đọc như bot → mất E-E-A-T).
- Có **bảng hoặc list** (dễ ăn featured snippet + AI trích).
- **Freshness:** H1 + intro có năm hiện tại (2026).
- **Brand tiết chế:** "Webnovel.vn" xuất hiện tối đa 2-3 lần/bài, chủ yếu ở CTA "đọc full tại...". Giữ giọng blogger bên thứ 3, KHÔNG nhồi quảng cáo.
- **Internal link 1 chiều** về webnovel.vn (link truyện/danh mục thật từ scrape).
- Tone: blogger review khách quan, đáng tin, tự nhiên.
- Xuất **HTML** (thẻ `<h1><h2><p><table><ul>`) + 1 block `<script type="application/ld+json">` ở cuối. Hiển thị trực tiếp trong chat để user copy.

### Ghép URL ảnh cho bài PBN (dùng cho review + toplist)

Ảnh bìa truyện chèn vào bài PBN là ảnh đã upload lên chính domain đích (WordPress). Công thức URL cố định:

```
https://{site}/wp-content/uploads/{img}/{slug}.webp
```

- **`{site}`** = domain đích, do user truyền qua `--site <domain>` (vd `tonghoixaydungvn.org.vn`). Danh sách domain hợp lệ tham chiếu ở `data/pbn-domains.txt`. Không có `--site` → **hỏi lại**, KHÔNG đoán.
- **`{img}`** = tháng upload ảnh dạng `YYYY/MM` (vd `2026/07`), do user truyền qua `--img <YYYY/MM>`. WordPress đóng băng URL ảnh theo tháng upload, nên **phải hỏi user tháng này** nếu chưa truyền — KHÔNG tự lấy tháng hiện tại.
- **`{slug}`** = trường `slug` trong `data/truyen-data.json` (chính là tên file ảnh đã crawl). Đuôi mặc định `.webp` (khớp ảnh crawl); nếu record có `anh_local` đuôi khác thì dùng đuôi đó.
- **Alt text** tự sinh: `[Tên truyện] – truyện [thể loại chính]` (thể loại đầu trong `danh_muc`).
- Chỉ ghép ảnh cho truyện **có trong JSON** (mới có slug đã upload). Truyện đến từ fallback scrape live → KHÔNG có ảnh, báo user.

`<img>` chuẩn: `<img src="https://{site}/wp-content/uploads/{img}/{slug}.webp" alt="[alt]" loading="lazy">`

### pbn review (1 URL truyện)
Cấu trúc:
1. `<h1>` — `Review [Tên truyện] – [thể loại] [năm]`
2. Đoạn mở: câu định nghĩa entity → TL;DR 2-3 câu (truyện nói về gì, ai nên đọc). Ngay dưới `<h1>` chèn **1 `<img>`** ảnh bìa (theo công thức trên) nếu truyện có trong JSON và có `--site` + `--img`.
3. `<table>` thông tin nhanh: Tác giả / Thể loại / Tình trạng / Đọc tại
4. `<h2>` Nội dung truyện — tóm tắt cốt (KHÔNG spoiler kết)
5. `<h2>` Điểm mạnh — list
6. `<h2>` Điểm yếu / lưu ý — list
7. `<h2>` Truyện hợp với ai
8. Box đánh giá: "Đánh giá tổng: x/10" (điểm khách quan, kèm 1 câu lý do)
9. `<h2>` FAQ — 3-4 câu Q&A **đặc thù truyện này**
10. CTA đọc full tại webnovel.vn (link truyện)

JSON-LD: `Article` + `Review` (itemReviewed = `Book`) + `FAQPage`.

### pbn toplist (theo THỂ LOẠI hoặc theo TÁC GIẢ)

Toplist có 2 kiểu lọc — xác định từ input user:
- **Theo thể loại:** URL danh mục (`https://webnovel.vn/tien-hiep/`) hoặc tên thể loại gõ tay ("top truyện tiên hiệp").
- **Theo tác giả:** user nêu tên tác giả ("top truyện của Tối Bạch Đích Ô Nha", "toplist tác giả Nhĩ Căn").

**Nguồn truyện (BẮT BUỘC theo thứ tự ưu tiên):**

1. **Đọc `data/truyen-data.json`** rồi lọc pool:
   - Kiểu **thể loại** → lọc record có `danh_muc` chứa thể loại target (match không phân biệt hoa thường, so khớp tên thể loại chuẩn: "Tiên Hiệp", "Xuyên Không", "Ngôn Tình"...).
   - Kiểu **tác giả** → lọc record có `tac_gia` khớp tên tác giả target (không phân biệt hoa thường; chấp nhận khớp gần đúng vì tên tác giả dài).
2. **Xác định target:**
   - Thể loại từ URL danh mục → scrape live lấy `CAT_TITLE`, bỏ tiền tố "Truyện " nếu có (vd "Truyện Tiên Hiệp" → "Tiên Hiệp").
   - Thể loại / tác giả gõ tay → dùng đúng tên đó (chuẩn hoá hoa/thường).
3. **Chọn N truyện** từ pool đã lọc (mặc định 5–10, lấy theo thứ tự trong JSON).
4. **Fallback khi pool có dưới 3 truyện (hoặc JSON không tồn tại/rỗng):**
   - Kiểu **thể loại**: scrape live URL danh mục như cũ (`STORY` lines), KHÔNG có ảnh PBN (báo user biết và gợi ý crawl thêm).
   - Kiểu **tác giả**: KHÔNG có trang tác giả để scrape → báo user "chưa đủ truyện của tác giả này trong dữ liệu, hãy crawl thêm URL truyện của họ rồi chạy lại", DỪNG (không bịa).

**Ảnh bìa mỗi truyện:** ghép theo công thức URL ảnh ở mục "Ghép URL ảnh cho bài PBN" (cần `--site` + `--img`).

Cấu trúc:
1. `<h1>` — kiểu thể loại: `Top N truyện [danh mục] hay nhất [năm]`; kiểu tác giả: `Top N truyện hay nhất của [Tên tác giả] [năm]`
2. Intro answer-first: liệt kê nhanh N tên truyện sẽ review
3. Đoạn **"Tiêu chí chọn"** (lượt đọc/đánh giá/tình trạng full-đang ra/độ hot) — bắt buộc, để AEO tin đây không phải list spam. Kiểu tác giả: nêu thêm dấu ấn/phong cách chung của tác giả.
4. Mỗi truyện = `<h2>` [số]. [Tên truyện] + ngay dưới là `<img src="..." alt="..." loading="lazy">` + câu định nghĩa ngắn + vì sao đáng đọc (2-4 câu) + link đọc (dùng `link_truyen` từ JSON)
5. `<table>` so sánh cuối bài — kiểu thể loại: Tên / Thể loại / Link; kiểu tác giả: Tên / Thể loại / Link (thêm cột tác giả không cần vì cùng 1 người)
6. `<h2>` FAQ — 3-4 câu Q&A về danh mục (hoặc về tác giả)
7. CTA khám phá thêm tại webnovel.vn (link danh mục nếu có)

- N mặc định = số truyện lấy được (khuyến nghị top 5-10). Dùng dữ liệu JSON (tên + link + `danh_muc` + `tac_gia`) là đủ cho mô tả sơ; muốn mô tả sâu hơn thì scrape từng URL truyện.
- **Thể loại trong bảng so sánh** = `danh_muc` của từng truyện (join bằng dấu phẩy), KHÔNG bịa.

JSON-LD: `Article` + `ItemList` (mỗi item là `Book`/`ListItem`) + `FAQPage`.

### pbn faq (1 URL truyện hoặc danh mục)
Cấu trúc:
1. `<h1>` — câu hỏi lớn + năm (vd "Truyện tiên hiệp hay nhất 2026: giải đáp mọi thắc mắc")
2. 6-10 cặp Q&A: mỗi Q = `<h2>` hoặc `<h3>`, A answer-first 2-4 câu rồi mở rộng
3. Câu hỏi bám chủ đề trang (truyện cụ thể hoặc thể loại)
4. CTA đọc tại webnovel.vn

JSON-LD: `Article` + `FAQPage`.

---

## LOẠI forum — plain text, 10 cặp Q&A

- Bám URL: truyện → FAQ quanh truyện đó; danh mục → FAQ quanh thể loại.
- **10 cặp Q&A.** Câu hỏi kiểu **gây tò mò, tự nhiên như người dùng forum thật hỏi** (không phải câu hỏi SEO khô khan). Câu trả lời **2-4 câu**, giải đáp thỏa đáng.
- **KHÔNG hashtag.**
- **Nhắc "Webnovel.vn" tự nhiên** trong một số câu trả lời (dẫn dắt nhẹ về việc đọc truyện ở đó), KHÔNG lộ liễu, không nhồi vào mọi câu.
- Tone: **giọng sạch, dễ đọc, đúng chính tả** — KHÔNG viết tắt kiểu seeding (`e`, `mn`, `k`...). Thân thiện nhưng chuẩn.
- Xuất dạng đánh số 1-10 trong chat, mỗi cặp: **Q:** ... / **A:** ...

---

## Rules

- **Luôn scrape trước khi viết** (trừ `pbn toplist` lấy pool từ `data/truyen-data.json` — scrape chỉ khi fallback hoặc cần CAT_TITLE từ URL danh mục). Không đoán nội dung từ slug.
- **Không bịa.** Scrape fail (rc≠0) → báo lỗi rõ theo mã lỗi, DỪNG. (Ngoại lệ bio truyện thiếu summary như mô tả trên.)
- **Toplist chọn truyện đúng tiêu chí** từ JSON: theo thể loại (`danh_muc`) hoặc theo tác giả (`tac_gia`). Không tin list site nếu đã có JSON.
- **Ảnh PBN:** chỉ ghép URL theo công thức `--site` + `--img` + `slug`. Thiếu tham số → hỏi lại. Không hotlink `cdn.webnovel.vn` trong bài PBN.
- Toàn bộ content **tiếng Việt**.
- Type do user khai báo; subtype của bio auto-detect, subtype của pbn do user khai báo.
- bio + forum: plain text trong chat. pbn: HTML kèm JSON-LD trong chat.
- JSON-LD phải điền dữ liệu thật từ scrape/JSON (tên, tác giả, url...), không để placeholder.
- Sau khi tạo content xong: hỏi user có muốn push skill lên repo không (nếu vừa sửa skill).

## Scripts & Data
- `scripts/scrape.sh` — live-scrape webnovel.vn (curl browser-UA), auto-detect loại trang, in field dạng `KEY<TAB>value`. Fail rõ ràng với mã lỗi rc 2/3/4/5.
- `data/truyen-data.json` — pool truyện đã crawl (đồng bộ tự động từ `/crawl-data-webnovel`). Dùng cho toplist + slug ảnh.
- `data/pbn-domains.txt` — danh sách domain PBN hợp lệ (đối chiếu `--site`). Ảnh nằm cùng domain đăng bài.

## Category
content-seo
