#!/usr/bin/env python3
# keywords.py — Mở rộng 1 keyword gốc thành N keyword phân biệt cho bulk mode
# (content-webnovel). Chỉ có 1 keyword seed → phải sinh thêm keyword liên quan/LSI.
#
# 3 tier (theo brief "Keyword theo tầng A→B→C"):
#   A — GSC API: --gsc-api. Gọi scripts/gsc-api.py (subprocess) → CSV → parse như
#       tier B. Tự suy filter page từ --url/--category. Lỗi/thiếu credential thì
#       RƠI MỀM xuống B/C, không làm sập batch.
#   B — export GSC user gửi tay: --gsc-csv <file>. Nhận CSV/TSV VÀ .zip tải thẳng
#       từ GSC (tự chọn sheet query). Header EN/VI, số kiểu 3,450 và 3.450.
#   C — tự sinh: từ data/truyen-data.json + CAT_DESC/GENRES scrape + pool biến thể
#       trong SKILL.md ("Resolve SEO keyword" mục 3).
#
# Tier B đi kèm LỌC LIÊN QUAN (query rác từ CSV): keyword phải chứa token lõi của
# seed hoặc tên danh mục — so khớp KHÔNG DẤU 2 phía, vì GSC tách query có dấu và
# không dấu thành 2 dòng. Tier C sinh từ chính pool nên liên quan sẵn.
#
# Usage:
#   # category mode (danh mục)
#   keywords.py --seed "truyện điền văn" --category "Điền Văn" [--cat-desc "..."] [-n 10]
#   keywords.py --seed "truyện điền văn" --url https://webnovel.vn/dien-van/    [-n 10]
#   # story mode (1 URL truyện)
#   keywords.py --seed "tiên nghịch" --slug tien-nghich
#   # author mode
#   keywords.py --seed "sách Osho" --author "Osho"
#   # tier B (trộn export GSC vào, ưu tiên trước tier C) — csv hoặc zip đều được
#   keywords.py --seed "truyện điền văn" --category "Điền Văn" --gsc-csv ~/Downloads/gsc.csv
#   keywords.py --seed "truyện điền văn" --category "Điền Văn" --gsc-csv ~/Downloads/gsc.zip
#
# Out: TSV `keyword<TAB>kw_source<TAB>impressions` trên stdout (summary ra stderr).
#      kw_source: tierA:api · tierB:gsc · tierC:primary · tierC:variant ·
#                 tierC:intent · tierC:story · tierC:versus · tierC:author
#
# Exit: 0 OK · 2 thiếu/sai tham số hoặc không đọc được data.

import argparse
import csv
import io
import json
import re
import subprocess
import sys
import unicodedata
import zipfile
from collections import Counter
from pathlib import Path

# Khớp NONFIC_SET của pick-variant.py (giữ đồng bộ tay — 2 script không import nhau).
NONFIC_SET = {"phát triển bản thân", "tâm linh", "kinh doanh"}

DATA_JSON = Path(__file__).resolve().parent.parent / "data" / "truyen-data.json"

# Stopword khi tách token lõi của seed (để lọc liên quan tier B).
CORE_STOP = {"truyện", "sách", "top", "hay", "nhất", "full", "hoàn", "mới",
             "review", "đọc", "của", "và", "cho", "là", "gì", "the", "a"}


def norm(s: str) -> str:
    return " ".join(s.lower().split())


def strip_truyen(s: str) -> str:
    s = s.strip()
    if s.lower().startswith("truyện "):
        s = s[len("truyện "):].strip()
    return s


def deacc(s: str) -> str:
    """Bỏ dấu, giữ khoảng trắng, lowercase. Dùng để so khớp 'không dấu'.

    GSC báo cáo query có dấu và không dấu là 2 dòng riêng ("truyện điền văn hay"
    vs "truyen dien van hay") — user VN gõ không dấu rất nhiều. So khớp phải
    deaccent 2 phía, không thì tier B loại sạch query không dấu.
    """
    s = (s or "").replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return " ".join(s.lower().split())


# Bản không dấu của CORE_STOP (dẫn xuất, khỏi phải maintain 2 danh sách).
CORE_STOP_DEACC = {deacc(w) for w in CORE_STOP}


def slugify(s: str) -> str:
    """Bỏ dấu → lowercase → non-alnum thành '-'. Khớp contract tên file trong brief."""
    s = s.replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def cat_from_url(url: str) -> str:
    """URL danh mục → slug đoạn đầu (vd /dien-van/ → 'dien-van')."""
    m = re.sub(r"^https?://(www\.)?webnovel\.vn/", "", url.strip())
    return m.split("/")[0].split("?")[0].strip()


def load_data():
    try:
        with open(DATA_JSON, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR: không đọc được {DATA_JSON}: {e}", file=sys.stderr)
        raise SystemExit(2)


def cat_pool(records, category):
    """Truyện có `category` trong danh_muc (không phân biệt hoa thường)."""
    c = norm(strip_truyen(category))
    return [r for r in records
            if any(norm(g) == c for g in (r.get("danh_muc") or []))]


def resolve_category(records, category, url):
    """Trả tên danh mục 'đẹp' (từ JSON) khi user truyền --url slug."""
    if category:
        return strip_truyen(category)
    if not url:
        return ""
    slug = cat_from_url(url)
    for r in records:
        for g in (r.get("danh_muc") or []):
            if slugify(g) == slug:
                return g
    return slug.replace("-", " ")


def core_tokens(seed, category):
    """Token lõi để lọc liên quan: từ seed + tên danh mục, bỏ stopword. Đã deaccent."""
    toks = set()
    for src in (seed, category):
        for t in deacc(strip_truyen(src or "")).split():
            if t and t not in CORE_STOP_DEACC:
                toks.add(t)
    return toks


def is_relevant(kw, cores, category):
    """Keyword phải chứa ≥1 token lõi HOẶC tên danh mục (lọc query rác tier B).

    So khớp không dấu 2 phía: query GSC không dấu vẫn khớp seed có dấu.
    """
    low = deacc(kw)
    if category and deacc(strip_truyen(category)) in low:
        return True
    return any(t in low for t in cores) if cores else True


# Khớp header theo SUBSTRING KHÔNG DẤU — GSC đổi header theo ngôn ngữ giao diện:
#   EN "Top queries" / "Query"      · VI "Truy vấn hàng đầu" / "Truy vấn"
#   EN "Impressions"                · VI "Số lần hiển thị" / "Lượt hiển thị"
# "hien thi" không đụng cột clicks ("Số lần nhấp") nên không nhận lẫn.
QKEY_SUBS = ("quer", "truy van", "keyword", "tu khoa")
IKEY_SUBS = ("impression", "hien thi")

# Sheet trong zip KHÔNG phải query (GSC xuất 1 zip nhiều CSV).
ZIP_SKIP = ("filter", "bo loc", "date", "ngay", "page", "trang", "countr",
            "quoc gia", "device", "thiet bi", "appearance", "hien thi tren")


def parse_int(raw):
    """'3,450' (EN) · '3.450' (VI) · '3 450' → 3450. Không phải số nguyên → 0."""
    s = str(raw or "").strip()
    for ch in (",", ".", " ", " ", " "):
        s = s.replace(ch, "")
    return int(s) if s.isdigit() else 0


def _rows_from_text(fh):
    """Parse 1 file handle text → list (keyword, impressions)."""
    out = []
    sample = fh.read(4096)
    fh.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    rd = csv.reader(fh, dialect=dialect)
    rows = [r for r in rd if any((c or "").strip() for c in r)]
    if not rows:
        return out

    head = [(c or "").strip() for c in rows[0]]
    qcol = icol = None
    for i, name in enumerate(head):
        low = deacc(name)
        if qcol is None and any(k in low for k in QKEY_SUBS):
            qcol = i
        if icol is None and any(k in low for k in IKEY_SUBS):
            icol = i

    if qcol is None and icol is None:
        # Không thấy header nào quen → coi như KHÔNG có header (user paste tay từ
        # bảng GSC). Cột 0 = query, bỏ qua impressions (giữ nguyên thứ tự GSC đã
        # sort sẵn) — thà mất số hơn là đọc sai số.
        body, qcol = rows, 0
        print("[keywords] CSV không có header quen → đọc cột 1 làm query, "
              "bỏ qua impressions (giữ thứ tự có sẵn)", file=sys.stderr)
    else:
        body = rows[1:]
        if qcol is None:
            qcol = 0  # có cột impressions nhưng header query lạ → cột đầu

    for r in body:
        if qcol >= len(r):
            continue
        kw = (r[qcol] or "").strip()
        if not kw:
            continue
        imp = parse_int(r[icol]) if icol is not None and icol < len(r) else 0
        out.append((kw, imp))
    return out


def read_gsc_csv(path):
    """Đọc export GSC: CSV/TSV, hoặc thẳng file .zip GSC tải về.

    Cột query/impressions dò theo header không dấu (EN + VI). Zip thì tự chọn
    sheet Queries/Truy vấn.
    """
    p = Path(path).expanduser()
    if not p.exists():
        print(f"ERROR: không thấy file {p}", file=sys.stderr)
        raise SystemExit(2)
    try:
        if p.suffix.lower() == ".zip" or zipfile.is_zipfile(p):
            with zipfile.ZipFile(p) as z:
                # Zip không bật cờ UTF-8 (0x800) thì zipfile decode tên bằng cp437 →
                # "Truy vấn.csv" thành rác. Khôi phục bytes rồi decode lại UTF-8,
                # không thì không nhận ra sheet query tên tiếng Việt.
                def real_name(info):
                    if info.flag_bits & 0x800:
                        return info.filename
                    try:
                        return info.filename.encode("cp437").decode("utf-8")
                    except (UnicodeEncodeError, UnicodeDecodeError):
                        return info.filename

                pairs = [(real_name(i), i.filename) for i in z.infolist()
                         if not i.is_dir()]
                pairs = [(disp, raw) for disp, raw in pairs
                         if disp.lower().endswith(".csv")
                         and "__MACOSX" not in raw.upper()]
                names = [disp for disp, _ in pairs]
                raw_of = dict(pairs)
                if not names:
                    print(f"ERROR: zip {p.name} không có CSV nào", file=sys.stderr)
                    raise SystemExit(2)
                pick = next((n for n in names
                             if any(k in deacc(Path(n).stem) for k in QKEY_SUBS)), None)
                if pick is None:
                    pick = next((n for n in names
                                 if not any(k in deacc(Path(n).stem) for k in ZIP_SKIP)), None)
                if pick is None:
                    print(f"ERROR: zip {p.name} chỉ có sheet không phải query "
                          f"({', '.join(names)}) — giải nén rồi trỏ đúng file query",
                          file=sys.stderr)
                    raise SystemExit(2)
                print(f"[keywords] zip {p.name} → dùng sheet '{pick}'", file=sys.stderr)
                text = z.read(raw_of[pick]).decode("utf-8-sig", errors="replace")
            return _rows_from_text(io.StringIO(text, newline=""))
        with open(p, encoding="utf-8-sig", newline="") as f:
            return _rows_from_text(f)
    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: đọc export GSC lỗi: {e}", file=sys.stderr)
        raise SystemExit(2)


def derive_page_filter(url, category, slug):
    """Suy filter page cho tier A: URL → path; danh mục → /slug/; truyện → slug.

    Lọc ngay trên API sát hơn tier B (user hay export cả property). Filter hẹp quá
    → gsc-api.py tự thử lại không filter, nên đoán sai vẫn không mất data.
    """
    if url:
        m = re.sub(r"^https?://(www\.)?[^/]+", "", url.strip())
        m = m.split("?")[0].split("#")[0]
        return m if m and m != "/" else ""
    if slug:
        return slug
    if category:
        return f"/{slugify(strip_truyen(category))}/"
    return ""


def fetch_tier_a(site, days, page_filter, key_file, limit):
    """Gọi scripts/gsc-api.py, parse CSV nó in ra. Trả (rows, err|"").

    Lỗi thì trả err chứ KHÔNG raise: tier A chết phải rơi mềm xuống B/C, không
    được làm sập cả batch bulk.
    """
    script = Path(__file__).resolve().parent / "gsc-api.py"
    if not script.exists():
        return [], f"không thấy {script.name}"
    cmd = [sys.executable, str(script), "--limit", str(max(limit, 200)),
           "--days", str(days)]
    if site:
        cmd += ["--site", site]
    if page_filter:
        cmd += ["--page-filter", page_filter]
    if key_file:
        cmd += ["--key-file", key_file]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        return [], "gsc-api.py quá 180s"
    except Exception as e:
        return [], f"không chạy được gsc-api.py: {type(e).__name__}"
    for line in (p.stderr or "").splitlines():
        if line.strip():
            print(f"  {line}", file=sys.stderr)
    if p.returncode != 0:
        hint = {4: "chưa cài lib — chạy scripts/gsc-install.sh",
                5: "chưa có credential — xem GSC-SETUP.md",
                6: "không tìm được property"}.get(p.returncode, "xem log trên")
        return [], f"gsc-api.py exit {p.returncode} ({hint})"
    if not (p.stdout or "").strip():
        return [], ""
    return _rows_from_text(io.StringIO(p.stdout, newline="")), ""


def co_genres(pool, category, limit=3):
    """Thể loại đi kèm nhiều nhất trong pool (thay cho việc đoán từ CAT_DESC)."""
    c = norm(strip_truyen(category))
    cnt = Counter()
    for r in pool:
        for g in (r.get("danh_muc") or []):
            if norm(g) != c:
                cnt[g] += 1
    return [g for g, _ in cnt.most_common(limit)]


def desc_genres(cat_desc, category, limit=2):
    """Thể loại được CAT_DESC gợi (khớp SKILL.md mục 3: 'compound nếu CAT_DESC gợi')."""
    if not cat_desc:
        return []
    low = norm(cat_desc)
    c = norm(strip_truyen(category))
    hits = []
    for g in ("ngôn tình", "xuyên không", "trọng sinh", "huyền huyễn", "tiên hiệp",
              "đô thị", "hệ thống", "trinh thám", "kinh dị", "cổ đại", "hiện đại"):
        if g in low and g != c and g not in hits:
            hits.append(g)
    return hits[:limit]


def gen_tier_c(records, seed, category, cat_desc, slug, author, noun):
    """Sinh keyword tier C. Trả list (keyword, kw_source)."""
    out = []

    def add(kw, src):
        if kw and kw.strip():
            out.append((" ".join(kw.split()), src))

    if author:
        pool = [r for r in records if norm(r.get("tac_gia") or "") == norm(author)]
        add(seed, "tierC:primary")
        add(f"{noun} của {author}", "tierC:author")
        add(f"top {noun} {author}", "tierC:author")
        add(f"{noun} {author} hay nhất", "tierC:author")
        add(f"{noun} {author} nên đọc", "tierC:author")
        for r in pool:
            add(r.get("tu_khoa") or "", "tierC:story")
            add(f"review {r.get('tu_khoa')}", "tierC:story")
        return out

    if slug:
        rec = next((r for r in records if r.get("slug") == slug), None)
        name = (rec or {}).get("tu_khoa") or slug.replace("-", " ")
        genres = (rec or {}).get("danh_muc") or []
        add(seed, "tierC:primary")
        add(name, "tierC:story")
        add(f"review {name}", "tierC:story")
        add(f"{name} có hay không", "tierC:intent")
        add(f"đọc thử {name}", "tierC:story")
        add(f"{name} review", "tierC:story")
        if genres:
            add(f"{noun} {norm(genres[0])} hay như {name}", "tierC:intent")
        # versus: ghép với truyện cùng thể loại đầu
        if genres:
            same = [r for r in cat_pool(records, genres[0])
                    if r.get("slug") != slug][:3]
            for r in same:
                add(f"{name} hay {r.get('tu_khoa')}", "tierC:versus")
        return out

    # ----- category mode -----
    pool = cat_pool(records, category)
    dm = norm(strip_truyen(category))
    add(seed, "tierC:primary")
    # pool biến thể SKILL.md ("Resolve SEO keyword" mục 3)
    for pat in (f"{noun} {dm} hay", f"{noun} {dm} hay nhất", f"{noun} {dm} full",
                f"{noun} {dm} hoàn", f"{noun} hoàn {dm}", f"top {noun} {dm}",
                f"{noun} {dm} mới nhất", f"{noun} {dm} đáng đọc"):
        add(pat, "tierC:variant")
    # intent theo subtype (genre/guide/faq/versus có shape keyword riêng)
    for pat in (f"{noun} {dm} là gì", f"cách chọn {noun} {dm}",
                f"{noun} {dm} cho người mới", f"nên đọc {noun} {dm} nào"):
        add(pat, "tierC:intent")
    # compound từ CAT_DESC (ưu tiên) rồi từ thể loại đi kèm trong pool
    for g in desc_genres(cat_desc, category):
        add(f"{noun} {dm} {g}", "tierC:variant")
    for g in co_genres(pool, category):
        add(f"{noun} {dm} {norm(g)}", "tierC:variant")
    # story-level: mỗi bài review dùng tên truyện làm keyword riêng
    for r in pool:
        add(r.get("tu_khoa") or "", "tierC:story")
    for r in pool:
        add(f"review {r.get('tu_khoa')}", "tierC:story")
    # versus: ghép cặp liền kề trong pool
    for a, b in zip(pool, pool[1:]):
        add(f"{a.get('tu_khoa')} hay {b.get('tu_khoa')}", "tierC:versus")
    return out


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--seed", required=True, help="keyword gốc user gõ / auto-resolve")
    ap.add_argument("--category", default="", help="tên danh mục (vd 'Điền Văn')")
    ap.add_argument("--url", default="", help="URL danh mục (suy ra --category)")
    ap.add_argument("--cat-desc", dest="cat_desc", default="",
                    help="CAT_DESC scrape được (sinh compound keyword)")
    ap.add_argument("--slug", default="", help="story mode: slug 1 truyện")
    ap.add_argument("--author", default="", help="author mode: tên tác giả")
    ap.add_argument("--gsc-csv", dest="gsc_csv", default="",
                    help="tier B: CSV/ZIP export GSC (cột query + impressions)")
    ap.add_argument("--gsc-api", dest="gsc_api", action="store_true",
                    help="tier A: pull thẳng từ GSC API (cần scripts/gsc-install.sh)")
    ap.add_argument("--gsc-site", dest="gsc_site", default="",
                    help="tier A: property (vd sc-domain:webnovel.vn). Bỏ = auto")
    ap.add_argument("--gsc-days", dest="gsc_days", type=int, default=90,
                    help="tier A: số ngày lùi (default 90)")
    ap.add_argument("--gsc-page-filter", dest="gsc_page_filter", default="",
                    help="tier A: filter page. Bỏ = tự suy từ --url/--category")
    ap.add_argument("--gsc-key-file", dest="gsc_key_file", default="",
                    help="tier A: service account JSON (mặc định đọc ~/.config/webnovel-gsc)")
    ap.add_argument("-n", "--limit", type=int, default=20,
                    help="số keyword tối đa in ra (default 20 = cap bulk)")
    args = ap.parse_args()

    if not (args.category or args.url or args.slug or args.author):
        ap.error("cần 1 trong: --category / --url / --slug / --author")

    records = load_data()
    category = resolve_category(records, args.category, args.url)

    # noun theo category-class (khớp pick-variant.py: non-fiction CHỈ khi MỌI thể loại ∈ set)
    if args.slug:
        rec = next((r for r in records if r.get("slug") == args.slug), None)
        genres = (rec or {}).get("danh_muc") or []
    elif args.author:
        pool_a = [r for r in records if norm(r.get("tac_gia") or "") == norm(args.author)]
        genres = [g for r in pool_a for g in (r.get("danh_muc") or [])]
    else:
        genres = [category] if category else []
    cls = "non-fiction" if genres and all(norm(g) in NONFIC_SET for g in genres) else "fiction"
    noun = "truyện" if cls == "fiction" else "sách"

    cores = core_tokens(args.seed, category)

    rows = []          # (keyword, kw_source, impressions)
    seen_slug = {}     # slug → keyword đầu tiên chiếm slug đó

    def push(kw, src, imp):
        """Dedup theo cả text lẫn SLUG (2 keyword khác nhau không được ra cùng tên file)."""
        kw = " ".join(kw.split())
        if not kw:
            return
        sl = slugify(kw)
        if not sl or sl in seen_slug:
            return
        seen_slug[sl] = kw
        rows.append((kw, src, imp))

    dropped = 0        # query lạc đề bị loại (tier A + B)
    tier_a_err = ""

    # tier A trước nhất: pull thẳng API. Lỗi → rơi mềm xuống B/C.
    if args.gsc_api:
        pf = args.gsc_page_filter or derive_page_filter(args.url, category, args.slug)
        a_rows, tier_a_err = fetch_tier_a(args.gsc_site, args.gsc_days, pf,
                                          args.gsc_key_file, args.limit)
        if tier_a_err:
            print(f"[keywords] tier A BỎ QUA: {tier_a_err} → dùng tier B/C",
                  file=sys.stderr)
        a_rows.sort(key=lambda x: -x[1])
        for kw, imp in a_rows:
            if not is_relevant(kw, cores, category):
                dropped += 1
                continue
            push(kw, "tierA:api", imp)

    # tier B: CSV/ZIP user gửi tay. Chạy được cùng tier A (bù thêm), dedup lo phần trùng.
    if args.gsc_csv:
        gsc = read_gsc_csv(args.gsc_csv)
        gsc.sort(key=lambda x: -x[1])
        for kw, imp in gsc:
            if not is_relevant(kw, cores, category):
                dropped += 1
                continue
            push(kw, "tierB:gsc", imp)

    # tier C bù cho đủ limit
    for kw, src in gen_tier_c(records, args.seed, category, args.cat_desc,
                             args.slug, args.author, noun):
        if len(rows) >= args.limit:
            break
        push(kw, src, 0)

    rows = rows[:args.limit]

    print("keyword\tkw_source\timpressions")
    for kw, src, imp in rows:
        print(f"{kw}\t{src}\t{imp}")

    n_a = sum(1 for r in rows if r[1].startswith("tierA"))
    n_b = sum(1 for r in rows if r[1].startswith("tierB"))
    print(f"[keywords] {len(rows)} keyword phân biệt "
          f"(tierA={n_a}, tierB={n_b}, tierC={len(rows) - n_a - n_b}, "
          f"limit={args.limit}) · category={category or '-'} · noun={noun}"
          + (f" · loại {dropped} query lạc đề" if dropped else ""),
          file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # noqa
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
