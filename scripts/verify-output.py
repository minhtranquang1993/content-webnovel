#!/usr/bin/env python3
# verify-output.py — Kiểm HTML output của pbn/blog20 (content-webnovel) trước khi giao.
# Đếm & đối chiếu contract cứng mà prompt hay vi phạm âm thầm:
#   - backlink webnovel.vn: mỗi URL đúng 1 lần (flag URL trùng)
#   - self-link nội bộ (pbn: đúng 1; blog20: 0)
#   - JSON-LD / <script>: cấm
#   - word count body: 1000-1500 chữ
#   - năm hiện tại (hoặc --year) xuất hiện >=1 lần
#   - có >=1 <table> hoặc <ul>/<ol>
#
# KHÔNG sửa HTML — chỉ report PASS/WARN/FAIL để agent tự sửa rồi verify lại.
#
# Usage:
#   python3 verify-output.py --type pbn --subtype review [--year 2026] [--site fbu.vn] < bai.html
#   cat bai.html | python3 verify-output.py --type blog20 --subtype toplist
#
# Exit: 0 = PASS (không FAIL) · 1 = có FAIL · 2 = lỗi tham số/không đọc được input

import sys
import re
import argparse
import datetime

WEBNOVEL_HOST = "webnovel.vn"

# Số backlink webnovel.vn kỳ vọng theo subtype (min, max). None = không cố định (toplist/genre/guide: theo pool).
BACKLINK_EXPECT = {
    "review":        (1, 2),   # 1 CTA; auto-switch dual-entity = 2
    "review-short":  (1, 1),
    "faq":           (1, 1),
    "versus":        (2, 2),   # 2 truyện (hoặc CTA danh mục khi input danh mục)
    "toplist":       (1, None),
    "genre":         (1, None),
    "guide":         (1, None),
}


def count_words_vi(text):
    # Đếm "chữ" theo từ (khoảng trắng) — cùng convention SKILL.md 1000-1500 chữ.
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return 0
    return len(text.split())


def strip_tags(html):
    # Bỏ script/style content trước, rồi bỏ tag.
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<style\b.*?</style>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", html)
    text = (text.replace("&amp;", "&").replace("&nbsp;", " ")
                .replace("&quot;", '"').replace("&#39;", "'")
                .replace("&lt;", "<").replace("&gt;", ">"))
    return text


def extract_hrefs(html):
    # Trả list (href, anchor_text) của mọi thẻ <a>.
    out = []
    for m in re.finditer(r'<a\b([^>]*)>(.*?)</a>', html, flags=re.S | re.I):
        attrs, inner = m.group(1), m.group(2)
        hm = re.search(r'href\s*=\s*"([^"]*)"', attrs, flags=re.I) or \
             re.search(r"href\s*=\s*'([^']*)'", attrs, flags=re.I)
        href = hm.group(1).strip() if hm else ""
        anchor = re.sub(r"<[^>]+>", "", inner).strip()
        out.append((href, anchor))
    return out


def norm_url(u):
    return u.rstrip("/").lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", required=True, choices=["pbn", "blog20"])
    ap.add_argument("--subtype", required=True,
                    choices=["review", "review-short", "toplist", "faq",
                             "genre", "guide", "versus"])
    ap.add_argument("--year", type=int, default=datetime.date.today().year)
    ap.add_argument("--site", default="", help="domain PBN (để nhận self-link)")
    ap.add_argument("--min-words", type=int, default=1000)
    ap.add_argument("--max-words", type=int, default=1500)
    args = ap.parse_args()

    html = sys.stdin.read()
    if not html.strip():
        print("ERROR: không có HTML trên stdin.", file=sys.stderr)
        raise SystemExit(2)

    fails, warns, oks = [], [], []

    # --- JSON-LD / script ---
    if re.search(r'<script', html, flags=re.I):
        fails.append("Có thẻ <script> (cấm JSON-LD/schema trong pbn/blog20).")
    else:
        oks.append("Không có <script>/JSON-LD.")

    # --- table / list ---
    has_table = bool(re.search(r"<table\b", html, flags=re.I))
    has_list = bool(re.search(r"<(ul|ol)\b", html, flags=re.I))
    if has_table or has_list:
        oks.append(f"Có {'table' if has_table else ''}{'+list' if has_table and has_list else ('list' if has_list else '')} (>=1 table/list).")
    else:
        fails.append("Không có table lẫn list (cần >=1).")

    # --- word count ---
    wc = count_words_vi(strip_tags(html))
    if wc < args.min_words:
        fails.append(f"Body {wc} chữ < {args.min_words} (quá ngắn).")
    elif wc > args.max_words:
        fails.append(f"Body {wc} chữ > {args.max_words} (quá dài).")
    else:
        oks.append(f"Body {wc} chữ (trong {args.min_words}-{args.max_words}).")

    # --- năm ---
    if re.search(r"\b%d\b" % args.year, html):
        oks.append(f"Năm {args.year} xuất hiện >=1 lần.")
    else:
        fails.append(f"Năm {args.year} KHÔNG xuất hiện (freshness fail).")

    # --- phân loại link ---
    hrefs = extract_hrefs(html)
    webnovel_urls, self_links, other = [], [], []
    for href, anchor in hrefs:
        low = href.lower()
        if WEBNOVEL_HOST in low:
            webnovel_urls.append((href, anchor))
        elif args.site and args.site.lower() in low:
            self_links.append((href, anchor))
        elif low.startswith("http"):
            other.append((href, anchor))

    # --- backlink webnovel unique ---
    seen = {}
    for href, _ in webnovel_urls:
        n = norm_url(href)
        seen[n] = seen.get(n, 0) + 1
    dupes = {u: c for u, c in seen.items() if c > 1}
    n_unique = len(seen)
    if dupes:
        for u, c in dupes.items():
            fails.append(f"Backlink webnovel trùng {c} lần: {u} (mỗi URL chỉ 1 lần).")
    lo, hi = BACKLINK_EXPECT.get(args.subtype, (1, None))
    if n_unique < lo:
        fails.append(f"Backlink webnovel unique = {n_unique} < {lo} (subtype {args.subtype}).")
    elif hi is not None and n_unique > hi:
        warns.append(f"Backlink webnovel unique = {n_unique} > {hi} (subtype {args.subtype} — kiểm lại).")
    elif not dupes:
        oks.append(f"Backlink webnovel unique = {n_unique} (OK cho {args.subtype}).")

    # --- self-link ---
    if args.type == "blog20":
        if self_links:
            fails.append(f"blog20 KHÔNG được self-link, thấy {len(self_links)}.")
        # meta URL/Slug: cấm ở blog20
        if re.search(r'^\s*(URL|Slug)\s*:', html, flags=re.M | re.I):
            warns.append("blog20 không nên có block 'URL:'/'Slug:'.")
        if not self_links:
            oks.append("blog20: không self-link (đúng).")
    else:  # pbn
        if args.site:
            if len(self_links) == 1:
                oks.append("pbn: đúng 1 self-link nội bộ.")
            elif len(self_links) == 0:
                fails.append("pbn: THIẾU self-link nội bộ (cần đúng 1 trong đoạn mở).")
            else:
                fails.append(f"pbn: {len(self_links)} self-link (cần đúng 1).")
        else:
            fails.append("pbn: cần truyền --site để kiểm self-link bắt buộc (self-link phải đúng 1).")

    # --- report ---
    print("=== VERIFY OUTPUT — %s %s ===" % (args.type, args.subtype))
    for m in oks:
        print(f"  OK   {m}")
    for m in warns:
        print(f"  WARN {m}")
    for m in fails:
        print(f"  FAIL {m}")
    print("-" * 40)
    if fails:
        print(f"RESULT: FAIL ({len(fails)} lỗi, {len(warns)} cảnh báo) — sửa rồi verify lại.")
        raise SystemExit(1)
    print(f"RESULT: PASS ({len(warns)} cảnh báo).")
    raise SystemExit(0)


if __name__ == "__main__":
    main()
