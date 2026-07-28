#!/usr/bin/env python3
# bulk-plan.py — Lập ma trận bulk cho content-webnovel: tính capacity từ pool + loại
# input, ghép keyword vào từng bài, gọi pick-variant.py lấy slot biến thể. In N dòng TSV.
#
# Đây LÀ --dry-run: script chỉ in ma trận, KHÔNG ghi file bài, KHÔNG sinh nội dung.
#
# N_thực = min(N_yêu_cầu, số_keyword_phân_biệt, capacity). Bị cắt → in lý do ra
# stderr (announce), KHÔNG pad bằng keyword gần trùng.
#
# Ngưỡng trên của --bulk = số domain trong data/pbn-domains.txt (nay 29): 1 keyword →
# 1 bài → 1 domain riêng. Xin quá ngưỡng → BLOCKED yêu cầu chỉnh lại, KHÔNG tự cắt.
#
# Capacity (chốt với user: category mode = P, KHÔNG phải P+7+versus như bảng brief —
# bảng cho pool 5 ra 13 nên --bulk 10 không cắt, ngược Verify bước 3; và 2 toplist trên
# pool nhỏ tất trùng >80% list → tự fail check batch ở verify-bulk.py):
#   - danh mục pool P : P          (P=1 → chặn bulk, auto-switch review đường chạy đơn)
#   - 1 URL truyện    : 6          (review, review-short, faq + 3 versus cùng thể loại)
#   - tác giả A truyện: A + 2
#   Subtype khai tường minh → capacity = số slot của riêng subtype đó.
#
# Usage:
#   bulk-plan.py --type blog20 --bulk 10 --url https://webnovel.vn/dien-van/
#   bulk-plan.py --type pbn --bulk 3 --category "Điền Văn" --site fbu.vn
#   bulk-plan.py --type pbn --bulk 5 --category "Điền Văn" --subtype review
#   bulk-plan.py --type forum --bulk 3 --url https://webnovel.vn/dien-van/
#   bulk-plan.py --type blog20 --bulk 6 --slug tien-nghich
#   bulk-plan.py --type pbn --bulk 5 --author "Osho" --site fbu.vn
#
# Out: TSV header + N dòng:
#   idx keyword kw_source subtype anchor archetype title_idx goc verdict bulk_index site
#
# site (chỉ pbn): 1 domain/bài. --site a,b,c → theo thứ tự; --site-pool → tự lấy N
# domain từ data/pbn-domains.txt; --site a → cả batch chung 1 domain (hành vi cũ).
#
# Exit: 0 OK · 2 thiếu/sai tham số · 3 chặn bulk (pool=1 / không đủ dữ liệu)

import argparse
import subprocess
import sys
from pathlib import Path

import keywords as kwmod  # cùng thư mục scripts/

# Console Windows mặc định cp1252 → in keyword/tên truyện tiếng Việt là
# UnicodeEncodeError. Ép UTF-8 cho stdout/stderr.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

SCRIPTS = Path(__file__).resolve().parent
PICK = SCRIPTS / "pick-variant.py"
DOMAINS_TXT = SCRIPTS.parent / "data" / "pbn-domains.txt"

# Cap tuyệt đối = size pool domain PBN: 1 keyword → 1 bài → 1 domain riêng, nên
# không thể bulk quá số domain đang có (xoay vòng = 2 bài chung domain = footprint).
# Đọc động từ data/pbn-domains.txt, fallback 29 nếu file lỗi. Vượt cap → BLOCKED,
# không cắt âm thầm (user phải tự hạ --bulk để biết mình đang lấy ít hơn đã xin).
HARD_CAP_FALLBACK = 29


def load_domains():
    """Đọc data/pbn-domains.txt → list domain (bỏ comment `#` + dòng trống)."""
    try:
        with open(DOMAINS_TXT, encoding="utf-8") as f:
            return [ln.strip() for ln in f
                    if ln.strip() and not ln.lstrip().startswith("#")]
    except OSError:
        return []


def hard_cap():
    """Cap tuyệt đối cho --bulk = số domain trong pool (xem HARD_CAP_FALLBACK)."""
    return len(load_domains()) or HARD_CAP_FALLBACK


def resolve_sites(raw_site, use_pool, n, type_, scope, notes):
    """Trả list n domain, 1 domain/bài (index i → sites[i]).

    PBN đăng N bài lên N domain khác nhau: nếu tất cả bài dùng chung 1 domain thì
    domain đó nhận cả batch cùng thể loại → dấu vết footprint. Nên mặc định là
    phân N domain phân biệt.

      --site a,b,c  → dùng đúng list đó, theo thứ tự (thiếu thì xoay vòng).
      --site-pool   → lấy n domain từ data/pbn-domains.txt, offset deterministic
                      theo (type, scope) để 2 batch khác scope không đè cùng cụm
                      domain, mà chạy lại cùng scope vẫn ra y cũ. scope = danh mục
                      (category mode) / slug truyện (story) / tên tác giả (author) —
                      dùng category không đủ vì story/author mode có category rỗng
                      nên MỌI batch story/author sẽ rút cùng cụm.
                      Offset chỉ dàn cụm theo kiểu best-effort: pool 29 domain mà
                      scope thì hàng trăm nên 2 scope khác nhau VẪN có thể trùng
                      offset (đã đo: crc32 không khá hơn cộng codepoint, trùng bị ép
                      bởi pool nhỏ). Cần chắc chắn cụm nào thì chỉ định tay --site.
                      Bất biến luôn giữ: trong CÙNG 1 batch, n bài = n domain khác
                      nhau — n <= len(pool) là bảo đảm bởi hard_cap() chặn ở main().
      --site a      → 1 domain cho cả batch (hành vi cũ, giữ nguyên).

    blog20/forum KHÔNG dùng domain → trả list rỗng.
    """
    if type_ != "pbn":
        return [""] * n
    picked = [s.strip() for s in (raw_site or "").replace(";", ",").split(",") if s.strip()]
    pool = load_domains()

    if use_pool and not picked:
        if not pool:
            notes.append(f"--site-pool: không đọc được {DOMAINS_TXT.name} → site để trống")
            return [""] * n
        off = sum(ord(c) for c in f"{type_}|{kwmod.norm(scope or '')}") % len(pool)
        picked = [pool[(off + k) % len(pool)] for k in range(min(n, len(pool)))]
        notes.append(f"--site-pool: lấy {len(picked)} domain từ {DOMAINS_TXT.name} "
                     f"(offset {off} theo danh mục)")

    if not picked:
        return [""] * n

    if pool:
        unknown = [s for s in picked if s not in pool]
        if unknown:
            notes.append(f"CẢNH BÁO: {len(unknown)} domain KHÔNG có trong "
                         f"{DOMAINS_TXT.name}: {', '.join(unknown)} — kiểm lại chính tả")

    if len(picked) < n:
        if len(picked) == 1:
            notes.append(f"chỉ 1 domain cho {n} bài → cả batch đăng chung "
                         f"'{picked[0]}'. Muốn 1 bài 1 domain thì truyền đủ {n} domain "
                         f"hoặc dùng --site-pool")
        else:
            notes.append(f"chỉ {len(picked)} domain cho {n} bài → xoay vòng, "
                         f"{n - len(picked)} bài dùng lại domain đã có")
    return [picked[i % len(picked)] for i in range(n)]


def downloads_dir() -> Path:
    """Thư mục Downloads của user, cross-platform. Fallback về home nếu không có.
    Cùng pattern crawl-webnovel/scripts/crawl.py — KHÔNG hardcode path Windows."""
    home = Path.home()
    d = home / "Downloads"
    return d if d.is_dir() else home


def out_dir(type_: str) -> Path:
    """<Downloads>/webnovel/content-{pbn|blog20|forum}. KHÔNG tạo (đây là dry-run)."""
    return downloads_dir() / "webnovel" / f"content-{type_}"

# Subtype hợp lệ theo type (SKILL.md bảng type/subtype: faq CHỈ pbn; forum không subtype).
SUBTYPES = {
    "pbn":    ["review", "review-short", "toplist", "faq", "genre", "versus", "guide"],
    "blog20": ["review", "review-short", "toplist", "genre", "versus", "guide"],
    "forum":  ["forum"],
}

# Subtype pick-variant.py hỗ trợ (faq KHÔNG có → slot biến thể để "-").
PICK_OK = {"review", "review-short", "toplist", "genre", "guide", "versus", "forum"}


def run_pick(subtype, bulk_index, slug="", target="", slug_a="", slug_b="",
             genres="", site=""):
    """Gọi pick-variant.py, parse KEY<TAB>value. Không tự tính hash tay."""
    cmd = [sys.executable, str(PICK), "--subtype", subtype,
           "--bulk-index", str(bulk_index)]
    if slug:
        cmd += ["--slug", slug]
    if target:
        cmd += ["--target", target]
    if slug_a:
        cmd += ["--slug-a", slug_a]
    if slug_b:
        cmd += ["--slug-b", slug_b]
    if genres:
        cmd += ["--genres", genres]
    if site:
        cmd += ["--site", site]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if p.returncode != 0:
        print(f"ERROR: pick-variant.py fail ({subtype}): {p.stderr.strip()}",
              file=sys.stderr)
        raise SystemExit(2)
    d = {}
    for line in p.stdout.splitlines():
        if "\t" in line:
            k, v = line.split("\t", 1)
            d[k] = v
    return d


def first_int(s, default="-"):
    """'3 (pool review gốc, 6 công thức)' → '3'."""
    if not s:
        return default
    tok = s.split()[0]
    return tok if tok.lstrip("-").isdigit() else default


def build_mix(cap, allowed, pool_size):
    """Trộn subtype round-robin, front-load subtype có pick-variant để 4 bài đầu đủ 4
    archetype. faq (không archetype) đẩy về sau. Toplist chỉ 2 slot khi pool đủ lớn để
    2 list rời nhau (>=16) — pool nhỏ 2 toplist tất trùng >80%."""
    slots = {
        "review":       pool_size,
        "toplist":      2 if pool_size >= 16 else 1,
        "versus":       min(2, pool_size // 2),
        "review-short": 1,
        "genre":        1,
        "guide":        1,
        "faq":          1,
    }
    order = ["review", "toplist", "versus", "review-short", "genre", "guide", "faq"]
    queues = {s: slots.get(s, 0) for s in order if s in allowed}
    mix, guard = [], 0
    while len(mix) < cap and guard < cap * 8:
        guard += 1
        progressed = False
        for s in order:
            if queues.get(s, 0) > 0 and len(mix) < cap:
                mix.append(s)
                queues[s] -= 1
                progressed = True
        if not progressed:
            break
    return mix


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--type", required=True, choices=["pbn", "blog20", "forum"])
    ap.add_argument("--bulk", required=True, type=int,
                    help="N bài yêu cầu (tối đa = số domain trong "
                         "data/pbn-domains.txt, nay 29 — vượt là BLOCKED)")
    ap.add_argument("--subtype", default="", help="khai tường minh → N bài cùng subtype")
    ap.add_argument("--category", default="")
    ap.add_argument("--url", default="")
    ap.add_argument("--cat-desc", dest="cat_desc", default="")
    ap.add_argument("--slug", default="", help="story mode")
    ap.add_argument("--author", default="")
    ap.add_argument("--site", default="",
                    help="pbn: domain đăng. Nhiều domain cách nhau bằng dấu phẩy "
                         "→ 1 bài 1 domain theo thứ tự. 1 domain → cả batch chung")
    ap.add_argument("--site-pool", dest="site_pool", action="store_true",
                    help="pbn: tự lấy N domain từ data/pbn-domains.txt (khỏi gõ tay)")
    ap.add_argument("--gsc-csv", dest="gsc_csv", default="", help="tier B: CSV/ZIP export GSC")
    ap.add_argument("--gsc-api", dest="gsc_api", action="store_true",
                    help="tier A: pull thẳng GSC API (cần scripts/gsc-install.sh)")
    ap.add_argument("--gsc-site", dest="gsc_site", default="",
                    help="tier A: property (vd sc-domain:webnovel.vn). Bỏ = auto")
    ap.add_argument("--gsc-days", dest="gsc_days", type=int, default=90,
                    help="tier A: số ngày lùi (default 90)")
    ap.add_argument("--gsc-page-filter", dest="gsc_page_filter", default="",
                    help="tier A: filter page. Bỏ = tự suy từ --url/--category")
    ap.add_argument("--gsc-key-file", dest="gsc_key_file", default="",
                    help="tier A: service account JSON")
    ap.add_argument("--suggest", action="store_true",
                    help="tier S: keyword liên quan/LSI từ autocomplete Google/Bing/"
                         "DDG/YouTube. Không cần credential — dùng khi không có quyền GSC")
    ap.add_argument("--suggest-depth", dest="suggest_depth", type=int, default=1,
                    choices=(1, 2), help="tier S: 1 = hậu/tiền tố, 2 = thêm a-z")
    ap.add_argument("--seed-keyword", dest="seed_kw", default="",
                    help="primary keyword user ép (không có → auto-resolve)")
    ap.add_argument("--dry-run", action="store_true",
                    help="không đổi gì (script vốn chỉ in ma trận) — nhận cho khớp SKILL.md")
    args = ap.parse_args()

    if args.bulk < 1:
        ap.error("--bulk phải >= 1")
    cap = hard_cap()
    if args.bulk > cap:
        why = (f"1 keyword → 1 bài → 1 domain riêng, quá {cap} là 2 bài phải chung "
               f"1 domain (footprint)"
               if args.type == "pbn" else
               "cap dùng chung cho mọi type, lấy theo size pool domain PBN")
        print(f"BLOCKED: --bulk {args.bulk} vượt ngưỡng {cap}. Ngưỡng = số domain "
              f"trong {DOMAINS_TXT.name} — {why}. Chỉnh lại --bulk xuống <= {cap}, "
              f"hoặc thêm domain vào {DOMAINS_TXT.name} rồi chạy lại.",
              file=sys.stderr)
        raise SystemExit(3)
    if not (args.category or args.url or args.slug or args.author):
        ap.error("cần 1 trong: --category / --url / --slug / --author")

    allowed = SUBTYPES[args.type]
    if args.subtype and args.subtype not in allowed:
        ap.error(f"subtype '{args.subtype}' không hợp lệ cho type {args.type} "
                 f"(hợp lệ: {', '.join(allowed)})")

    records = kwmod.load_data()
    category = kwmod.resolve_category(records, args.category, args.url)
    notes = []

    # ----- pool + capacity theo loại input -----
    if args.slug:
        rec = next((r for r in records if r.get("slug") == args.slug), None)
        if not rec:
            print(f"ERROR: không thấy slug '{args.slug}' trong truyen-data.json",
                  file=sys.stderr)
            raise SystemExit(2)
        mode = "story"
        genres = rec.get("danh_muc") or []
        same = [r for r in kwmod.cat_pool(records, genres[0]) if r.get("slug") != args.slug][:3] if genres else []
        pool = [rec] + same
        capacity = 6
        pool_size = len(pool)
    elif args.author:
        mode = "author"
        pool = [r for r in records if kwmod.norm(r.get("tac_gia") or "") == kwmod.norm(args.author)]
        if not pool:
            print(f"ERROR: không thấy tác giả '{args.author}' trong truyen-data.json",
                  file=sys.stderr)
            raise SystemExit(2)
        genres = [g for r in pool for g in (r.get("danh_muc") or [])]
        capacity = len(pool) + 2
        pool_size = len(pool)
    else:
        mode = "category"
        pool = kwmod.cat_pool(records, category)
        pool_size = len(pool)
        genres = [category] if category else []
        if pool_size == 0:
            print(f"BLOCKED: danh mục '{category}' pool = 0 truyện — không đủ dữ liệu "
                  f"để bulk. Kiểm lại tên danh mục / URL.", file=sys.stderr)
            raise SystemExit(3)
        if pool_size == 1:
            print(f"BLOCKED: danh mục '{category}' pool = 1 truyện — chặn bulk "
                  f"(đường chạy đơn tự auto-switch review). Chạy không --bulk.",
                  file=sys.stderr)
            raise SystemExit(3)
        capacity = pool_size

    # subtype khai tường minh → capacity = slot của riêng subtype đó
    if args.subtype:
        st = args.subtype
        if st == "review":
            cap_sub = pool_size
        elif st == "versus":
            cap_sub = pool_size // 2
        elif st == "toplist":
            cap_sub = 2 if pool_size >= 16 else 1
        elif st == "forum":
            cap_sub = capacity
        else:  # genre / guide / faq / review-short
            cap_sub = 1
        capacity = min(capacity, cap_sub)
        notes.append(f"subtype '{st}' khai tường minh → capacity riêng = {capacity}")

    cls = "non-fiction" if genres and all(kwmod.norm(g) in kwmod.NONFIC_SET for g in genres) else "fiction"
    noun = "truyện" if cls == "fiction" else "sách"

    # ----- keyword pool -----
    seed_kw = args.seed_kw
    if not seed_kw:
        if mode == "story":
            seed_kw = pool[0].get("tu_khoa") or args.slug
        elif mode == "author":
            seed_kw = f"{noun} {args.author}"
        else:
            seed_kw = f"{noun} {kwmod.norm(kwmod.strip_truyen(category))}"

    kw_rows = []
    cores = kwmod.core_tokens(seed_kw, category)
    seen_slug = set()

    def push_kw(kw, src, imp=0):
        kw = " ".join((kw or "").split())
        if not kw:
            return
        sl = kwmod.slugify(kw)
        if not sl or sl in seen_slug:
            return
        seen_slug.add(sl)
        kw_rows.append((kw, src, imp))

    dropped = 0

    # tier A: pull API. Lỗi → note + rơi mềm xuống B/C, KHÔNG dừng bulk.
    if args.gsc_api:
        pf = args.gsc_page_filter or kwmod.derive_page_filter(args.url, category, args.slug)
        a_rows, a_err = kwmod.fetch_tier_a(args.gsc_site, args.gsc_days, pf,
                                          args.gsc_key_file, max(args.bulk * 10, 200))
        if a_err:
            notes.append(f"tier A bỏ qua: {a_err}")
        a_rows.sort(key=lambda x: -x[1])
        for kw, imp in a_rows:
            if not kwmod.is_relevant(kw, cores, category):
                dropped += 1
                continue
            push_kw(kw, "tierA:api", imp)

    if args.gsc_csv:
        gsc = kwmod.read_gsc_csv(args.gsc_csv)
        gsc.sort(key=lambda x: -x[1])
        for kw, imp in gsc:
            if not kwmod.is_relevant(kw, cores, category):
                dropped += 1
                continue
            push_kw(kw, "tierB:gsc", imp)

    # Seed chốt slot 1 trước tier S/C (tier S loại seed khỏi gợi ý — nó là input).
    push_kw(seed_kw, "tierC:primary", 0)

    # tier S: autocomplete thật, không cần credential. Trên tier C (query người ta
    # đang gõ) nhưng dưới A/B (không có volume). Lỗi mạng → rơi mềm, không dừng bulk.
    if args.suggest:
        try:
            import suggest as sgmod
            s_rows, s_drop = sgmod.collect(seed_kw, depth=args.suggest_depth,
                                           category=category)
            n_kept = 0
            for kw, score, grp in s_rows:
                if not kwmod.is_relevant(kw, cores, category):
                    dropped += 1
                    continue
                push_kw(kw, f"tierS:{'+'.join(grp)}", 0)   # imp=0: không có volume
                n_kept += 1
            notes.append(f"tier S: +{n_kept} keyword từ autocomplete "
                         f"(bỏ {s_drop['drift']} lạc đề, {s_drop['block']} đối thủ, "
                         f"{s_drop['stale']} năm cũ)")
        except Exception as e:  # noqa — tier S chết không được làm sập bulk
            notes.append(f"tier S bỏ qua: {type(e).__name__}: {e}")

    if dropped:
        notes.append(f"loại {dropped} query lạc đề")

    for kw, src in kwmod.gen_tier_c(records, seed_kw, category, args.cat_desc,
                                   args.slug, args.author, noun):
        push_kw(kw, src, 0)

    # keyword cho bài cấp-danh-mục (toplist/genre/guide/faq/forum-category): không phải
    # keyword tên truyện (những bài đó dùng tên truyện làm keyword riêng).
    # tierS:* khớp bằng PREFIX — source của nó động ("tierS:bing+google-yt"), so
    # khớp chuỗi chính xác sẽ trượt sạch và cat_queue rỗng.
    cat_queue = [(k, s, i) for k, s, i in kw_rows
                 if s.startswith("tierS:")
                 or s in ("tierA:api", "tierB:gsc", "tierC:primary", "tierC:variant",
                          "tierC:intent", "tierC:author")]
    n_keywords = len(kw_rows)

    # ----- N_thực -----
    n_req = args.bulk
    # HARD_CAP đã chặn ở đầu main() bằng BLOCKED nên không tham gia min() nữa.
    n = min(n_req, n_keywords, capacity)
    reasons = []
    if n_keywords < n_req:
        reasons.append(f"chỉ có {n_keywords} keyword phân biệt")
    if capacity < n_req:
        reasons.append(f"capacity pool = {capacity} ({mode} mode, pool {pool_size})")

    # ----- mix subtype -----
    if args.subtype:
        mix = [args.subtype] * n
    elif args.type == "forum":
        mix = ["forum"] * n
    elif mode == "story":
        # capacity 6 = review + review-short + faq + 3 versus (target ghép với 3 truyện
        # cùng thể loại). faq xếp CUỐI: nó không có archetype (pick-variant không hỗ trợ)
        # nên nằm trong 4 dòng đầu sẽ phá acceptance "4 bài đầu 4 archetype khác".
        base = ["review", "versus", "review-short", "versus", "versus"]
        if "faq" in allowed:
            base.append("faq")
        mix = base[:n]
    elif mode == "author":
        # capacity A+2 = 1 toplist + A review + 1 faq. faq cuối (lý do như story mode).
        base = ["toplist"] + ["review"] * pool_size
        if "faq" in allowed:
            base.append("faq")
        mix = base[:n]
    else:
        mix = build_mix(n, allowed, pool_size)
    if len(mix) < n:
        n = len(mix)
        reasons.append("hết slot subtype hợp lệ")

    # ----- domain per-bài (sau khi n chốt) -----
    # Site per-row cũng làm salt pick-variant: khác domain → khác archetype/góc/title,
    # nên 5 bài trên 5 domain phân hoá mạnh hơn 5 bài chung 1 domain.
    site_scope = category or args.slug or args.author
    sites = resolve_sites(args.site, args.site_pool, n, args.type, site_scope, notes)
    if args.type == "pbn" and not any(sites):
        notes.append("pbn chưa có domain — cột site để trống, skill phải HỎI user "
                     "trước khi ghi file (URL bài cần domain)")

    # ----- dựng từng dòng -----
    used_bi = {}       # subtype → set bulk_index đã dùng
    arch_seen = []     # archetype 4 dòng đầu (giữ acceptance: 4 bài đầu 4 archetype khác)
    story_i = 0        # con trỏ pool cho review
    vs_i = 0           # con trỏ cặp versus (cặp rời nhau)
    cat_i = 0          # con trỏ keyword cấp danh mục
    rows_out = []
    used_kw_slug = set()

    for i in range(n):
        st = mix[i]
        anchor, kw, src = "", "", ""
        slug = target = slug_a = slug_b = ""
        gen_str = ""

        if st in ("review", "review-short"):
            if mode == "story":
                rec = pool[0]   # input là 1 URL truyện → review + review-short cùng bám truyện đó
            elif story_i < len(pool):
                rec = pool[story_i]
                story_i += 1
            else:
                reasons.append("hết truyện trong pool cho review")
                break
            slug = rec.get("slug") or ""
            gen_str = "|".join(rec.get("danh_muc") or [])
            anchor = f"story:{slug}"
            name = rec.get("tu_khoa") or slug
            kw = name if st == "review" else f"đọc thử {name}"
            src = "tierC:story"
        elif st == "versus":
            if mode == "story":
                # truyện input làm neo, đổi truyện đối chiếu (brief: "3 versus ghép 3
                # truyện cùng thể loại") → cặp khác nhau nên thân bài vẫn khác.
                a_i, b_i = 0, vs_i + 1
            else:
                # category/author: cặp RỜI NHAU, không thì 2 bài versus trùng thân bài.
                a_i, b_i = vs_i * 2, vs_i * 2 + 1
            if b_i >= len(pool):
                reasons.append("hết cặp versus trong pool")
                break
            ra, rb = pool[a_i], pool[b_i]
            vs_i += 1
            slug_a, slug_b = ra.get("slug") or "", rb.get("slug") or ""
            gen_str = "|".join(ra.get("danh_muc") or [])
            anchor = f"versus:{slug_a}+{slug_b}"
            kw = f"{ra.get('tu_khoa')} hay {rb.get('tu_khoa')}"
            src = "tierC:versus"
        else:  # toplist / genre / guide / faq / forum
            target = kwmod.strip_truyen(category) if category else (args.author or "")
            if not target and pool:
                target = "|".join((pool[0].get("danh_muc") or [""]))[:40] or "chung"
            gen_str = "|".join(genres[:3]) if genres else ""
            anchor = f"cat:{target}"
            if st == "toplist" and pool_size >= 16:
                half = pool_size // 2
                rng = f"1-{half}" if (i % 2 == 0) else f"{half + 1}-{pool_size}"
                anchor = f"cat:{target}|slice={rng}"
            while cat_i < len(cat_queue):
                cand, csrc, _ = cat_queue[cat_i]
                cat_i += 1
                if kwmod.slugify(cand) not in used_kw_slug:
                    kw, src = cand, csrc
                    break
            if not kw:
                reasons.append("hết keyword cấp danh mục")
                break

        ksl = kwmod.slugify(kw)
        if not ksl or ksl in used_kw_slug:
            reasons.append(f"keyword trùng slug ở idx {i}")
            break
        used_kw_slug.add(ksl)

        # bulk_index: mặc định = i. 4 dòng đầu phải đủ 4 archetype khác (acceptance
        # criteria). Subtype khác nhau (và cặp versus khác nhau) có seed khác nhau nên
        # cùng bulk_index vẫn ra archetype khác → quét tối đa 8 candidate, ưu tiên
        # archetype chưa xuất hiện; không tìm được thì lấy candidate hợp lệ đầu tiên.
        arch = ti = goc = vd = "-"
        bi = i
        if st in PICK_OK:
            fallback = None
            for cand_bi in range(i, i + 8):
                if cand_bi in used_bi.get(st, set()):
                    continue
                d = run_pick(st, cand_bi, slug=slug, target=target, slug_a=slug_a,
                             slug_b=slug_b, genres=gen_str, site=sites[i])
                a = d.get("ARCHETYPE") or first_int(d.get("FORUM_ARCHETYPES", ""))
                picked = (cand_bi, d, a)
                if fallback is None:
                    fallback = picked
                if i < 4 and a in arch_seen:
                    continue
                fallback = picked
                break
            if fallback:
                bi, d, a = fallback
                arch = a or "-"
                ti = first_int(d.get("TITLE_INDEX", ""))
                goc = (d.get("GOC_CHINH", "-") or "-").split()[0].lstrip("#") \
                    if d.get("GOC_CHINH") else "-"
                vd = first_int(d.get("VERDICT", ""), "-")
            used_bi.setdefault(st, set()).add(bi)
            if i < 4 and arch != "-":
                arch_seen.append(arch)

        rows_out.append((i, kw, src, st, anchor, arch, ti, goc, vd, bi, sites[i]))

    n = len(rows_out)

    print("idx\tkeyword\tkw_source\tsubtype\tanchor\tarchetype\ttitle_idx\tgoc\tverdict\tbulk_index\tsite")
    for r in rows_out:
        print("\t".join(str(x) for x in r))

    # ----- announce ra stderr -----
    head = (f"[bulk-plan] type={args.type} mode={mode} "
            f"{'category=' + category if category else ''}"
            f"{' author=' + args.author if args.author else ''}"
            f"{' slug=' + args.slug if args.slug else ''} "
            f"pool={pool_size} capacity={capacity} keyword={n_keywords} noun={noun}")
    print(head, file=sys.stderr)
    print(f"[bulk-plan] OUT_DIR: {out_dir(args.type)}", file=sys.stderr)
    if args.type == "pbn":
        used_sites = [r[10] for r in rows_out]
        nd = len({s for s in used_sites if s})
        print(f"[bulk-plan] domain: {nd} domain phân biệt cho {n} bài"
              f"{' — ' + ', '.join(used_sites) if any(used_sites) else ' (chưa có domain)'}",
              file=sys.stderr)
    if n < n_req:
        uniq = []
        for r in reasons:
            if r not in uniq:
                uniq.append(r)
        print(f"[bulk-plan] CẮT: yêu cầu {n_req} bài → làm {n} bài. Lý do: "
              f"{'; '.join(uniq)}. KHÔNG pad bằng keyword gần trùng.", file=sys.stderr)
    else:
        print(f"[bulk-plan] {n}/{n_req} bài — đủ, không cắt.", file=sys.stderr)
    for nt in notes:
        print(f"[bulk-plan] note: {nt}", file=sys.stderr)
    if n >= 4:
        a4 = [r[5] for r in rows_out[:4] if r[5] != "-"]
        if len(a4) == 4:
            print(f"[bulk-plan] archetype 4 bài đầu: {a4} → "
                  f"{'distinct OK' if len(set(a4)) == 4 else 'TRÙNG (kiểm lại)'}",
                  file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # noqa
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
