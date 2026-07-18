# Cheat sheet — `/content-webnovel`

Cách input nhanh cho skill content marketing Webnovel.vn.  
**Skill active:** `C:\Users\Admin\.claude\skills\content-webnovel\`  
**Repo:** https://github.com/minhtranquang1993/content-webnovel  
**Chi tiết đầy đủ:** xem `SKILL.md`.

> Khi đổi cú pháp / tham số / hành vi input của skill → **update file này** cùng lúc với `SKILL.md`.

---

## Cú pháp chuẩn

```
/content-webnovel <type> [subtype] <url|tên> [--site <domain>] [--img <YYYY/MM>] [--lo <nhãn>] [--kw "<keyword>"]
```

Freeform cũng được: gửi URL + mô tả bằng lời → skill tự map type/subtype/tham số.

---

## Tham số

| Flag | Bắt buộc? | Dùng cho | Ý nghĩa |
|---|---|---|---|
| `--site <domain>` | **Có** với `pbn review` / `pbn toplist` | PBN | Domain đăng bài (trong `data/pbn-domains.txt`) → origin ảnh + CTA |
| `--img <YYYY/MM>` | **Có** với `pbn review` / `pbn toplist` | PBN | Tháng upload ảnh WP (vd `2026/07`). Thiếu → hỏi lại, không đoán |
| `--lo <nhãn>` | **Có** với `pbn review` / `pbn toplist` | PBN | Lô trong `data/truyen-data.json` (vd `01`). Thiếu → hỏi lại |
| `--kw "<keyword>"` | Tuỳ chọn | Chủ yếu `pbn toplist` danh mục | Primary SEO keyword ép tay. **Chỉ ảnh hưởng cách viết**, không đổi list truyện |

**Không cần** `--site` / `--img` / `--lo`: `bio`, `forum`, `pbn faq`.

Freeform keyword cũng được: `keyword là …`, `viết cho kw …`.

---

## Copy nhanh

```bash
# BIO
/content-webnovel bio https://webnovel.vn/<slug-truyen>/
/content-webnovel bio https://webnovel.vn/<slug-danh-muc>/
/content-webnovel bio https://webnovel.vn/

# PBN REVIEW
/content-webnovel pbn review https://webnovel.vn/<slug-truyen>/ --site <domain> --img 2026/07 --lo 01

# PBN TOPLIST (thể loại URL)
/content-webnovel pbn toplist https://webnovel.vn/<slug-danh-muc>/ --site <domain> --img 2026/07 --lo 01

# PBN TOPLIST (thể loại + ép keyword)
/content-webnovel pbn toplist https://webnovel.vn/dien-van/ --site <domain> --img 2026/07 --lo 01 --kw "truyện điền văn hoàn"

# PBN TOPLIST (tên thể loại)
/content-webnovel pbn toplist "Tiên Hiệp" --site <domain> --img 2026/07 --lo 01

# PBN TOPLIST (tác giả)
/content-webnovel pbn toplist "Tối Bạch Đích Ô Nha" --site <domain> --img 2026/07 --lo 01

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

### `pbn review` — HTML + JSON-LD

```
/content-webnovel pbn review https://webnovel.vn/ai-bao-han-tu-tien/ --site tonghoixaydungvn.org.vn --img 2026/07 --lo 01
```

### `pbn toplist` — HTML + JSON-LD

**Target thể loại:** URL danh mục hoặc tên gõ tay.  
**Target tác giả:** tên tác giả gõ tay / freeform.

```
/content-webnovel pbn toplist https://webnovel.vn/tien-hiep/ --site tonghoixaydungvn.org.vn --img 2026/07 --lo 01
/content-webnovel pbn toplist "Tiên Hiệp" --site fbu.vn --img 2026/07 --lo 01
/content-webnovel pbn toplist https://webnovel.vn/dien-van/ --site fbu.vn --img 2026/07 --lo 01 --kw "truyện điền văn hoàn"
/content-webnovel pbn toplist "Tối Bạch Đích Ô Nha" --site fbu.vn --img 2026/07 --lo 01
```

#### Pool sau lọc `--lo` + thể loại/tác giả

| Pool | Hành vi |
|---|---|
| `>= 2` | Toplist (Top N, kể cả Top 2) |
| `== 1` | Tự chuyển **review** (announce). Danh mục: dual-entity + link truyện + link danh mục. Tác giả: link truyện + 1 danh mục chính, không bịa URL author |
| `== 0` | Thể loại → fallback scrape live (không ảnh). Tác giả → dừng, báo crawl thêm |

#### Keyword vs list

- **List truyện** bám URL danh mục / filter JSON.
- **Keyword** chỉ để viết: có `--kw`/freeform → dùng đó; không có → auto `truyện {tên danh mục}` + biến thể nhẹ (`full`/`hoàn`/…).

### `pbn faq` — HTML + JSON-LD

```
/content-webnovel pbn faq https://webnovel.vn/tien-hiep/ --site fbu.vn
```

Không bắt buộc `--img` / `--lo`.

### `forum` — 10 cặp Q&A plain text

```
/content-webnovel forum https://webnovel.vn/ngon-tinh/
/content-webnovel forum https://webnovel.vn/ai-bao-han-tu-tien/
```

---

## Lưu ý nhanh

1. Type: `bio` | `pbn` | `forum`. Thiếu → skill hỏi lại.
2. `pbn` cần subtype: `review` | `toplist` | `faq`.
3. `pbn review` / `pbn toplist` thiếu `--site` / `--img` / `--lo` → hỏi, không đoán.
4. Ảnh PBN: `https://{site}/wp-content/uploads/{img}/{slug}.webp`
5. Pool JSON: `data/truyen-data.json` (đồng bộ từ `/crawl-data-webnovel`)
6. Chỉ URL thuộc `webnovel.vn`
