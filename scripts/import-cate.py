#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""import-cate.py — nạp danh sách danh mục từ CSV export Google Sheet vào
data/categories.tsv của skill.

Vì sao cần bản copy trong skill: file CSV nằm ở Downloads với tên có 2 khoảng
trắng ("webnovel.vn  - SEO - Minh - Sheet60.csv"), dễ bị đổi tên/move/xoá. Skill
đọc data/categories.tsv nên chạy được kể cả khi CSV gốc không còn, và bản này
commit lên repo được.

Input CSV cần 2 cột (header tiếng Việt như sheet gốc):
    tên danh mục truyện, link

Output TSV (1 dòng / 1 danh mục, keyword biến thể gộp bằng '|'):
    cate_slug   cate_name   cate_url   keywords

Nhiều dòng CSV trỏ cùng URL (vd xuyen-khong có 3 keyword) → gộp thành 1 dòng,
keyword giữ nguyên thứ tự xuất hiện. cate_name lấy từ danh_muc trong
truyen-data.json nếu khớp slug (tên "đẹp" có dấu), không khớp thì suy từ slug.

Usage:
    py -3 scripts/import-cate.py                      # tự tìm CSV trong Downloads
    py -3 scripts/import-cate.py --csv <path>         # chỉ định file
    py -3 scripts/import-cate.py --dry-run            # in ra, không ghi

Exit: 0 OK · 2 không tìm/đọc được CSV · 3 CSV thiếu cột bắt buộc
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"
OUT_TSV = DATA_DIR / "categories.tsv"
DATA_JSON = DATA_DIR / "truyen-data.json"

# Cột trong CSV export từ Google Sheet (khớp sheet "webnovel.vn - SEO - Minh").
COL_NAME = "tên danh mục truyện"
COL_LINK = "link"

sys.path.insert(0, str(Path(__file__).resolve().parent))
import keywords as kwmod  # slugify() đã xử lý 'đ' → 'd' đúng, tái dùng


def downloads_dir() -> Path:
    """Thư mục Downloads, cross-platform. Cùng pattern bulk-plan.py — KHÔNG
    hardcode path Windows."""
    home = Path.home()
    d = home / "Downloads"
    return d if d.is_dir() else home


def find_csv() -> Path | None:
    """Tìm CSV export sheet trong Downloads. Tên file có khoảng trắng đôi và có
    thể kèm suffix '(1)' khi tải lại → match theo prefix + đuôi .csv, lấy file
    mới nhất."""
    dl = downloads_dir()
    if not dl.is_dir():
        return None
    cands = [p for p in dl.glob("*.csv")
             if p.name.lower().startswith("webnovel.vn")]
    if not cands:
        return None
    return max(cands, key=lambda p: p.stat().st_mtime)


def cat_from_url(url: str) -> str:
    """URL danh mục → slug. Tái dùng helper của keywords.py."""
    return kwmod.cat_from_url(url)


def load_pretty_names() -> dict:
    """slug → tên danh mục 'đẹp' (có dấu) lấy từ danh_muc trong truyen-data.json."""
    try:
        with open(DATA_JSON, encoding="utf-8") as f:
            records = json.load(f)
    except Exception:
        return {}
    out = {}
    for r in records:
        for g in (r.get("danh_muc") or []):
            g = (g or "").strip()
            if g:
                out.setdefault(kwmod.slugify(g), g)
    return out


def read_csv(path: Path):
    """Đọc CSV → list (cate_slug, cate_url, keyword) theo đúng thứ tự xuất hiện."""
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except OSError as e:
        print(f"ERROR: không đọc được {path}: {e}", file=sys.stderr)
        raise SystemExit(2)
    rdr = csv.DictReader(raw.splitlines())
    cols = {(c or "").strip().lower() for c in (rdr.fieldnames or [])}
    if COL_NAME not in cols or COL_LINK not in cols:
        print(f"ERROR: CSV thiếu cột bắt buộc. Cần '{COL_NAME}' + '{COL_LINK}', "
              f"thấy: {sorted(cols)}", file=sys.stderr)
        raise SystemExit(3)
    rows = []
    for r in rdr:
        # DictReader giữ nguyên key gốc; chuẩn hoá lại để không phụ thuộc hoa/thường.
        low = {(k or "").strip().lower(): (v or "").strip() for k, v in r.items()}
        kw, url = low.get(COL_NAME, ""), low.get(COL_LINK, "")
        if not kw or not url:
            continue
        slug = cat_from_url(url)
        if not slug:
            continue
        rows.append((slug, url.rstrip("/") + "/", kw))
    return rows


def merge(rows, pretty):
    """Gộp theo slug, giữ thứ tự xuất hiện đầu tiên; keyword dedupe giữ thứ tự."""
    out = {}
    for slug, url, kw in rows:
        e = out.setdefault(slug, {"url": url, "kws": []})
        if kw not in e["kws"]:
            e["kws"].append(kw)
    return [
        {
            "slug": slug,
            "name": pretty.get(slug) or slug.replace("-", " ").title(),
            "url": e["url"],
            "kws": e["kws"],
        }
        for slug, e in out.items()
    ]


def write_tsv(cats, path: Path):
    """Ghi atomic: tmp + os.replace, tránh để lại file dở khi bị ngắt."""
    lines = ["cate_slug\tcate_name\tcate_url\tkeywords"]
    for c in cats:
        lines.append(f"{c['slug']}\t{c['name']}\t{c['url']}\t{'|'.join(c['kws'])}")
    body = "\n".join(lines) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(body, encoding="utf-8")
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--csv", default="", help="đường dẫn CSV export sheet. "
                                             "Bỏ = tự tìm trong Downloads")
    ap.add_argument("--dry-run", action="store_true",
                    help="in kết quả rồi dừng, không ghi data/categories.tsv")
    args = ap.parse_args()

    src = Path(args.csv).expanduser() if args.csv else find_csv()
    if not src or not src.is_file():
        print("ERROR: không tìm thấy CSV. Truyền --csv <path> hoặc để file export "
              f"trong {downloads_dir()} (tên bắt đầu bằng 'webnovel.vn').",
              file=sys.stderr)
        raise SystemExit(2)

    pretty = load_pretty_names()
    cats = merge(read_csv(src), pretty)

    print(f"[import-cate] nguồn: {src}", file=sys.stderr)
    print(f"[import-cate] {len(cats)} danh mục (đã gộp keyword trùng URL)",
          file=sys.stderr)
    for c in cats:
        extra = f" (+{len(c['kws']) - 1} keyword)" if len(c["kws"]) > 1 else ""
        print(f"  {c['slug']:24} {c['name']}{extra}", file=sys.stderr)

    if args.dry_run:
        print("[import-cate] --dry-run: KHÔNG ghi file.", file=sys.stderr)
        return
    write_tsv(cats, OUT_TSV)
    print(f"[import-cate] đã ghi {OUT_TSV}", file=sys.stderr)


if __name__ == "__main__":
    main()
