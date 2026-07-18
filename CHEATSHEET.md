# Cheat sheet — `/content-webnovel`

Cách input nhanh cho skill content marketing Webnovel.vn.  
**Skill active:** `C:\Users\Admin\.claude\skills\content-webnovel\`  
**Repo:** https://github.com/minhtranquang1993/content-webnovel  
**Chi tiết đầy đủ:** xem `SKILL.md`.

> Khi đổi cú pháp / tham số / hành vi input của skill → **update file này** cùng lúc với `SKILL.md`.

---

## Cú pháp chuẩn

```
/content-webnovel <type> [subtype] <url|tên> [keyword="<kw>"] [--site <domain>] [--lo <nhãn>]
```

Freeform cũng được: gửi URL + mô tả bằng lời → skill tự map.

---

## Tham số

| Flag / form | Bắt buộc? | Dùng cho | Ý nghĩa |
|---|---|---|---|
| `--site <domain>` | **Có** với mọi `pbn` | PBN | Domain đăng bài → ghép `https://{site}/{slug}/` |
| `--lo <nhãn>` | **Có** với `pbn review` / `pbn toplist` | PBN | Lô trong `data/truyen-data.json` (vd `01`) |
| `keyword="..."` hoặc `--kw "..."` | Tuỳ chọn | Chủ yếu `pbn toplist` danh mục | Primary SEO keyword. **Chỉ để viết**, không đổi list truyện |

**Không còn `--img`.** Ảnh = ImgBB (`anh_imgbb` trong JSON / `scripts/imgbb-upload.sh`).

**Không cần** `--site` / `--lo`: `bio`, `forum`.  
**`pbn faq`:** cần `--site`, không cần `--lo`.

---

## Copy nhanh

```bash
# BIO
/content-webnovel bio https://webnovel.vn/<slug-truyen>/
/content-webnovel bio https://webnovel.vn/<slug-danh-muc>/
/content-webnovel bio https://webnovel.vn/

# PBN REVIEW
/content-webnovel pbn review https://webnovel.vn/<slug-truyen>/ --site <domain> --lo 01

# PBN TOPLIST — URL danh mục (list bám URL)
/content-webnovel pbn toplist https://webnovel.vn/<slug-danh-muc>/ --site <domain> --lo 01

# PBN TOPLIST — URL + keyword cùng lúc (khuyến nghị khi muốn SEO chính xác)
/content-webnovel pbn toplist https://webnovel.vn/dien-van/ keyword="truyện điền văn hoàn" --site tonghoixaydungvn.org.vn --lo 01

# PBN TOPLIST — tên thể loại
/content-webnovel pbn toplist "Tiên Hiệp" --site <domain> --lo 01

# PBN TOPLIST — tác giả
/content-webnovel pbn toplist "Tối Bạch Đích Ô Nha" --site <domain> --lo 01

# PBN FAQ
/content-webnovel pbn faq https://webnovel.vn/<slug>/ --site <domain>

# FORUM
/content-webnovel forum https://webnovel.vn/<slug>/
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
/content-webnovel pbn review https://webnovel.vn/ai-bao-han-tu-tien/ --site tonghoixaydungvn.org.vn --lo 01
```

### `pbn toplist` — HTML thuần + meta URL/Slug

**Pattern chuẩn (URL + keyword):**

```
/content-webnovel pbn toplist https://webnovel.vn/dien-van/ keyword="truyện điền văn hoàn" --site tonghoixaydungvn.org.vn --lo 01
```

| Thành phần | Vai trò |
|---|---|
| URL danh mục | **Pool list truyện** (filter `danh_muc` sau `--lo`) |
| `keyword="..."` | **Cách viết SEO** (H1/body) — không đổi list |
| `--site` | Domain bài PBN |
| `--lo` | Lô JSON |

Cùng pattern với tên thể loại / tác giả:

```
/content-webnovel pbn toplist https://webnovel.vn/tien-hiep/ --site tonghoixaydungvn.org.vn --lo 01
/content-webnovel pbn toplist "Tiên Hiệp" --site fbu.vn --lo 01
/content-webnovel pbn toplist "Tối Bạch Đích Ô Nha" --site fbu.vn --lo 01
```

#### Pool sau lọc `--lo` + thể loại/tác giả

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

Cần `--site`, không cần `--lo`.

### `forum` — 10 cặp Q&A plain text

```
/content-webnovel forum https://webnovel.vn/ngon-tinh/
/content-webnovel forum https://webnovel.vn/ai-bao-han-tu-tien/
```

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

1. Type: `bio` | `pbn` | `forum`. Thiếu → skill hỏi lại.
2. `pbn` cần subtype: `review` | `toplist` | `faq`.
3. Mọi `pbn` cần `--site`. `review`/`toplist` cần thêm `--lo`.
4. **Không** truyền `--img` (đã bỏ).
5. Keyword khuyến nghị form: `keyword="..."`. Cũng nhận `--kw` / freeform.
6. Output pbn: HTML thuần + `URL`/`Slug` meta — **không** JSON-LD.
7. Pool JSON: `data/truyen-data.json` (đồng bộ từ `/crawl-data-webnovel`).
8. Chỉ URL thuộc `webnovel.vn`.
