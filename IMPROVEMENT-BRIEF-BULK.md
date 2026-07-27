# Improvement Brief: Bulk mode cho pbn / blog20 / forum

> **Trạng thái:** plan đã chốt, **chưa code gì**. Audit chạy trên commit `8b4c0f8` (đã pull, mới nhất).
> Bước tiếp theo: Change/Verify #1 ở cuối file.

## Bối cảnh

User muốn `--bulk N` sinh N bài cho `pbn` / `blog20` / `forum`. Chỉ có 1 keyword gốc → phải mở rộng thêm keyword liên quan / LSI / đồng nghĩa. Mỗi bài ghi ra 1 file `.txt` (tên = keyword + ngày giờ tạo) thay vì in ra chat. Ghi vào `Downloads/webnovel/content-{pbn,blog20,forum}`, chạy được cả Windows và macOS.

## 4 quyết định đã chốt với user

1. **`--bulk N`** = N bài. Flag riêng — KHÔNG nhét `bulk-10` vào `--site` như ví dụ ban đầu, vì `--site` đang là domain PBN.
2. **Keyword theo tầng A→B→C**: A = GSC API, B = CSV export tay, C = tự sinh từ `truyen-data.json` + `CAT_DESC`/`GENRES` scrape + pool biến thể sẵn có trong SKILL.md.
3. **Không khai subtype → tự trộn subtype**; khai subtype → N bài cùng subtype đó.
4. **File .txt** = metadata header + separator + nội dung đăng.

## Audit hiện trạng (sau pull `8b4c0f8`)

| Mặt | Hiện tại |
|---|---|
| Output | 100% in ra chat, 1 bài / 1 lần chạy. Grep `bulk` / `.txt` / ghi file trong SKILL.md → **không có** |
| Keyword | 1 primary (`keyword=` hoặc auto `truyện {danh mục}`) + 3-4 biến thể phụ rải nhẹ body |
| Chọn biến thể | **Đã chuyển sang script** `scripts/pick-variant.py` — tính sẵn archetype / góc / title-index / verdict / category-class, vì "LLM cộng code-point + chia lấy dư thường sai âm thầm" |
| Verify output | **Đã có** `scripts/verify-output.py` — check backlink-unique, self-link, JSON-LD, word count 1000-1500, năm, ≥1 table/list. Nhận `--type pbn\|blog20 --subtype … --site`, đọc HTML từ stdin |
| 3 folder đích | `Downloads/webnovel/content-{pbn,blog20,forum}` đã tồn tại, đang rỗng |
| Cross-platform | `crawl-data-webnovel/scripts/crawl.py` có `downloads_dir()` — pattern dùng lại |
| Pool data | 229 record, 23 danh mục, 179 tác giả |

**Hai script mới thu hẹp phạm vi việc phải làm:**
- Fix determinism phải nằm trong `pick-variant.py`, **không** phải trong prompt.
- Không cần viết `verify-bulk.py` từ đầu — chỉ cần wrapper mỏng loop từng file qua `verify-output.py`, cộng thêm check cấp-batch (trùng H1 / trùng keyword / trùng thân bài).

## Ràng buộc phải giữ (contract hiện có)

Mỗi URL `webnovel.vn` đúng 1 thẻ `<a>` toàn bài · pbn có self-link đoạn mở + block URL/Slug · blog20 KHÔNG URL/Slug/self-link · forum plain text đúng 1 URL trần mỗi post · ≥1 table hoặc list · có năm hiện tại · KHÔNG JSON-LD · 1000-1500 chữ (forum 500-1000).

## Lỗi 1 — công thức phá determinism (đã sửa)

Bản plan đầu tiên viết `h_i = h_base + Σ code-point(keyword_i)` rồi `+i`. **Sai.** Cho base biến theo từng bài thì `+i` mất tác dụng: hai keyword khác nhau vẫn rơi cùng residue sau `mod 4`.

Cũng KHÔNG dùng lại được cách salt của `--site` (`salt = codepoint_sum(site)` cộng thẳng vào seed), vì selector dùng `//7` và `//3` — phải cộng tới 7 seed mới đổi được archetype.

Đo trên slug thật `ai-bao-han-tu-tien` (seed 1664), N=10:

| Cách | archetype phân biệt | Vấn đề |
|---|---|---|
| Cộng `i` vào seed (kiểu `--site` salt) | **3/10** — bài i=2..8 cùng archetype 2 | 7 bài liền cùng hình hài |
| **Cộng `i` SAU phép chia** | **4/10** (tối đa của `mod 4`), xoay vòng 1→2→3→0 | — |

Công thức chốt (base **cố định cho cả batch**, chỉ `i` chạy, 0-based):

```
archetype = ((seed // 7) + i) mod 4          → 4 bài đầu chắc chắn 4 archetype khác
title     = ((seed // 3) + i) mod len(pool)  → chu kỳ 2/4/5/6 tuỳ pool+archetype
verdict   = (seed + i) mod 3                 → 3 bài đầu chắc chắn 3 verdict khác
góc       = (seed + i) mod len(nhóm)
```

Thành **phép đếm vòng** — phân biệt bảo đảm bằng cấu trúc, không nhờ may mắn của hash. Đã đo tuple `(archetype, title, verdict)` = **12/12 phân biệt** trên 3 slug thật với N=12 (chu kỳ `lcm(4,6,3)=12`). N > 12 thì tuple quay vòng nhưng keyword + H1 vẫn khác.

## Lỗi 2 — bỏ sót ràng buộc chặt hơn keyword: pool size

Bản đầu khẳng định "N bài cần ≥ N keyword phân biệt" là ràng buộc chặt nhất. **Sai.**

- `versus` với pool 2 → chỉ có **đúng 1 cặp**. 2 bài versus = 2 bài trùng nội dung, dù khác keyword khác H1.
- `toplist` với pool 3 → 6 bài toplist đều liệt kê đúng 3 truyện đó.

Keyword và H1 khác nhau **không cứu được phần thân trùng**. Và `verify-output.py` hiện tại **không bắt được** loại trùng này (nó check contract từng file, không so file với file). → wrapper batch phải thêm check trùng thân bài.

## Lỗi 3 — cap phải suy ra từ pool, không hardcode

Bản đầu hardcode cap tác giả = 10. Nhưng data thật: **tác giả nhiều truyện nhất chỉ có 7** (Osho). Cap đó không dựa trên gì.

Pool thật (229 record, 23 danh mục):

| Pool | Số danh mục | Ví dụ |
|---|---|---|
| ≥ 10 truyện | **13** | Phát triển bản thân 73 · Tiên Hiệp 61 · Huyền Huyễn 53 · Xuyên Không 46 · Ngôn Tình 42 · Tâm linh 38 · Điền Văn 22 · Đô Thị 10 |
| 2-9 truyện | 7 | Dị Năng 5 · Khoa Huyễn 5 |
| 1 truyện | 3 | → auto-switch review; chặn bulk |

Tác giả: **chỉ 12/179 có ≥3 truyện**. Top: Osho 7 · Brian Tracy 5 · Napoleon Hill 5 · Eckhart Tolle 5 · Sean Covey 4.

Capacity suy từ pool thay cho 3 số cứng:

| Input | Capacity |
|---|---|
| Danh mục pool P | `P` review (mỗi bài 1 truyện khác) + 2 toplist + 1 genre + 1 guide + 1 faq + `min(2, P//2)` versus + 1 review-short |
| 1 URL truyện | 6 — review, review-short, faq + 3 versus ghép 3 truyện cùng thể loại |
| Tác giả có A truyện | `A + 2` |

`N_thực = min(N_yêu_cầu, số_keyword_phân_biệt, capacity, 20)`. Bị cắt → **announce rõ lý do**, KHÔNG pad bằng keyword gần trùng.

Với pool thật: 13 danh mục lớn chạy `--bulk 10` thoải mái · 7 danh mục pool 2-9 bị cắt và phải nói rõ · 3 danh mục pool 1 chặn bulk ngay.

## Hai điểm nhỏ hơn đã sửa

- **GSC tier A hoãn lại.** Không có credential GSC nào trên máy (đã tìm `~/.config`, `~/.claude`, không có `~/.config/gcloud`); MCP đang bật chỉ Gmail/Drive/Docs/Sheets/Calendar, **không** có Search Console API. `google-api-python-client` đã cài nên script khả thi — nhưng đừng làm OAuth cho thứ chưa biết có quyền property `webnovel.vn` không. **Ship tier B + C trước**, thêm A sau khi user xác nhận.
- **Manifest ghi từng dòng ngay sau mỗi file**, không dồn cuối batch — để bài 7/10 chết vì hết context thì 6 bài trước vẫn còn vết và resume được.

## Thiết kế

### Luồng

```
1. Mở rộng keyword:  seed keyword + URL → tier B/C → dedup → lọc liên quan → cap
2. Tính capacity:    từ pool size + loại input → N_thực = min(N, #keyword, capacity, 20)
3. Lập ma trận:      bài i = (keyword_i, subtype_i, archetype_i, title_i, góc_i, verdict_i)
4. Sinh + ghi ngay:  xong bài nào ghi file + 1 dòng manifest bài đó, drop khỏi context
5. Verify + báo:     loop verify-output.py từng file + check cấp-batch, in bảng tổng kết
```

Bước 4 ghi ngay là điều kiện để `--bulk 10` không ngập context — không giữ 10 bài × 1200 chữ trong đầu.

### Output

```
<Downloads>/webnovel/content-{pbn|blog20|forum}/{keyword-slug}__{YYYYMMDD-HHmmss}.txt
```

- `keyword-slug` = keyword bỏ dấu → lowercase → non-alnum thành `-`. Trùng slug → thêm `-2`, `-3`.
- Header: `keyword`, `subtype`, `site` (pbn), `URL` + `Slug` (pbn), `archetype`/`góc`/`title`/`verdict` seed, `số chữ`, `tạo lúc`. Rồi `---------- NỘI DUNG ĐĂNG ----------`, rồi bài.
- **pbn:** URL/Slug ở header, KHÔNG lọt vào body. **blog20:** không URL/Slug, không self-link. **forum:** plain text, 1 URL trần.
- `manifest-{YYYYMMDD-HHmmss}.tsv` cùng folder: `idx, keyword, kw_source, subtype, archetype, title_idx, goc, verdict, site, url, slug, so_chu, filename, created_at`.
- Dùng `downloads_dir()` như `crawl.py` → macOS tự detect, tạo folder nếu thiếu. Không hardcode `C:\Users\Admin`.

### Ngoài phạm vi

`bio` không có bulk (10 biến thể sẵn là bulk rồi) · không auto-đăng WordPress · không đổi contract chọn-biến-thể của đường chạy đơn · không refactor `scrape.sh` / `imgbb-upload.sh` / `verify-output.py` · không đổi logic bất kỳ subtype hiện có.

## Rủi ro regression

| Rủi ro | Chặn bằng |
|---|---|
| Chạy đơn bị đổi hành vi | Không `--bulk` → `--bulk-index` không truyền → `pick-variant.py` cho kết quả **y hệt hôm nay**. Verify bằng so output trước/sau |
| Bulk phá backlink / self-link contract | Loop `verify-output.py` từng file |
| N file trùng H1 | Check cấp-batch, fail → dừng |
| Trùng thân bài (versus trùng cặp, toplist trùng list) | Check cấp-batch mới — `verify-output.py` không bắt được loại này |
| Keyword tier B lạc đề (query rác từ CSV) | Lọc liên quan: keyword phải chứa token lõi của seed hoặc tên danh mục |
| Ngập context khi sinh 10 bài dài | Ghi file + manifest ngay sau mỗi bài |
| macOS thiếu folder | `downloads_dir()` + tạo folder nếu chưa có |

## Các bước (Change / Verify)

1. **Change:** `pick-variant.py` — thêm `--bulk-index i` (default 0), offset **SAU** phép chia: archetype `((seed//7)+i)%4`, title `((seed//3)+i)%len(pool)`, verdict `(seed+i)%3`, góc `(seed+i)%len(nhóm)`.
   **Verify:** không truyền `--bulk-index` → output byte-identical với hiện tại (so `diff`). Truyền `i=0..3` → 4 archetype khác nhau. Truyền `i=0..11` → 12 tuple phân biệt.

2. **Change:** `scripts/keywords.py` — tier B (đọc CSV export GSC) + tier C (tự sinh từ `truyen-data.json` + `CAT_DESC`/`GENRES` + pool biến thể SKILL.md). In TSV `keyword<TAB>kw_source<TAB>impressions`.
   **Verify:** tier C với seed `truyện điền văn` + URL `/dien-van/` → ≥10 keyword phân biệt, không 2 keyword nào slugify ra cùng tên file.

3. **Change:** `scripts/bulk-plan.py` — tính capacity từ pool + loại input, in ma trận N dòng `idx, keyword, subtype, archetype, title_idx, goc, verdict`. Đây là `--dry-run`.
   **Verify:** `--bulk 10` trên `/dien-van/` (pool 22) → 10 dòng đủ. Trên danh mục pool 5 → bị cắt + in rõ lý do. Trên danh mục pool 1 → chặn.

4. **Change:** SKILL.md — section "Bulk mode": parse `--bulk N`, gọi `bulk-plan.py`, contract file + manifest, ghi-ngay-sau-mỗi-bài, tự trộn subtype, announce khi N bị cắt.
   **Verify:** `--bulk 3 --dry-run` in đúng ma trận 3 dòng, 3 keyword khác, 3 archetype khác.

5. **Change:** `scripts/verify-bulk.py` — wrapper: loop từng file qua `verify-output.py` + check cấp-batch (đủ N, H1 phân biệt, keyword phân biệt, versus không trùng cặp, toplist không trùng >80% danh sách, filename khớp manifest).
   **Verify:** sửa tay 1 file thành trùng H1 → script fail đúng chỗ đó.

6. **Change:** chạy thật `blog20 --bulk 3` (nhẹ nhất: không `--site`, không scrape chương).
   **Verify:** `verify-bulk.py` pass; đọc tay 1 file xem có đọc được như bài đăng thật.

7. **Change:** chạy `pbn --bulk 3 --site fbu.vn`.
   **Verify:** verify-bulk pass; URL/Slug nằm ở header, không lọt body.

8. **Change:** chạy `forum --bulk 3`.
   **Verify:** verify-bulk pass; mỗi file đúng 1 URL trần, không thẻ HTML.

9. **Change:** CHEATSHEET.md — cú pháp bulk + bảng capacity + đường dẫn output.
   **Verify:** copy lệnh từ cheatsheet chạy được không sửa.

10. **Change:** regression chạy đơn — `blog20 review <url>` không `--bulk`.
    **Verify:** vẫn in chat, KHÔNG tạo file nào trong 3 folder.

## Acceptance criteria

- [ ] N file trong đúng folder theo type, mỗi file 1 keyword riêng
- [ ] N keyword phân biệt + N H1 phân biệt
- [ ] 4 bài đầu có 4 archetype khác nhau
- [ ] Không 2 bài versus trùng cặp; không 2 bài toplist trùng >80% danh sách
- [ ] Mỗi file pass `verify-output.py` đúng type/subtype của nó
- [ ] N bị cắt (thiếu keyword / capacity) → announce rõ lý do, không pad
- [ ] macOS chạy không sửa path
- [ ] **Không `--bulk` → hành vi giống hệt hôm nay** (in chat, không tạo file)

## Còn mở

- Tier A (GSC API) cần user xác nhận có quyền property `webnovel.vn` + OAuth scope `webmasters.readonly`. Chưa có thì tier C vẫn chạy được ngay.
- SKILL.md đang lẫn 2 path convention: `~/.claude/skills/content-webnovel` (7 chỗ) và `~/.commandcode/skills/content-webnovel` (2 chỗ); CHEATSHEET.md 2 vs 1. Chỉ báo lại, chưa sửa (ngoài phạm vi task này).
