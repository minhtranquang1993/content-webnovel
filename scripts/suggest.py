#!/usr/bin/env python3
# suggest.py — Tier S: keyword liên quan / LSI / đồng nghĩa từ AUTOCOMPLETE thật.
# (content-webnovel bulk mode). Không cần credential, không cần quyền GSC.
#
# Vì sao dùng được: autocomplete là query người ta ĐANG gõ thật, do chính Google/
# Bing trả về — không phải LSI bịa ra bằng cách ghép từ đồng nghĩa. Đây là nguồn
# thay thế khi không có quyền Search Console (tier A/B).
#
# Nguồn (gộp, mỗi nguồn trả bộ khác nhau nên phủ rộng hơn 1 nguồn):
#   google   suggestqueries.google.com client=chrome  (kèm điểm xếp hạng nội bộ)
#   bing     api.bing.com/osjson.aspx
#   ddg      duckduckgo.com/ac
#   youtube  suggestqueries client=youtube (intent xem/nghe, hay ra cách gọi khác)
#
# Mở rộng seed để lấy nhiều hơn 10 gợi ý/lần:
#   depth 1 (default) — seed trần + hậu tố/tiền tố tiếng Việt hay đi với truyện
#   depth 2           — thêm a-z (kiểu "alphabet soup" của dân SEO)
#
# XẾP HẠNG — đọc kỹ chỗ này:
#   Autocomplete KHÔNG cho search volume. Không suy ra lượng tìm kiếm từ nó được.
#   Script xếp theo (số nguồn cùng gợi ý) rồi (vị trí trong danh sách). Keyword mà
#   cả Google + Bing + DDG đều gợi thì tin hơn keyword chỉ 1 nguồn có. Cột
#   impressions LUÔN = 0 cho tier S — không bịa số.
#
# Usage:
#   suggest.py --seed "truyện điền văn"
#   suggest.py --seed "truyện điền văn" --depth 2 -n 40
#   suggest.py --seed "tiên nghịch" --sources google,bing --no-cache
#
# Out: TSV `keyword<TAB>kw_source<TAB>score<TAB>sources` (summary ra stderr).
# Exit: 0 OK (kể cả 0 gợi ý) · 2 sai tham số.

import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
TIMEOUT = 12
CACHE_DIR = Path("/tmp/webnovel-suggest-cache")
CACHE_TTL = 6 * 3600          # 6h — autocomplete không đổi theo phút

SOURCES = ("google", "bing", "ddg", "youtube")

# DDG proxy index Bing → 2 nguồn này gần như luôn trả y hệt nhau. Đếm "2 nguồn
# đồng thuận" cho cặp này là tự lừa mình, nên gộp thành 1 phiếu.
SOURCE_GROUP = {"google": "google", "youtube": "google-yt",
                "bing": "bing", "ddg": "bing"}

# Hậu tố/tiền tố hay đi với truyện tiếng Việt. Sát domain hơn a-z thuần.
SUFFIXES = ("hay", "hoàn", "full", "mới", "ngắn", "review", "nữ chính", "xuyên không",
            "trọng sinh", "cổ đại", "hiện đại", "nhẹ nhàng", "gia đấu", "không gian")
PREFIXES = ("top", "đọc", "review")
ALPHABET = tuple("abcdeghiklmnoprstuvxy")   # bỏ chữ không mở đầu từ tiếng Việt

# Gợi ý nhắc ĐỐI THỦ / nền tảng khác / định dạng site không có → bỏ.
# Không lọc thì keyword thành "truyện điền văn wattpad", viết bài quảng cáo hộ họ.
BLOCK_SUBS = (
    # site truyện khác
    "dtruyen", "wattpad", "wikidich", "truyenfull", "metruyen", "sstruyen",
    "tangthuvien", "truyenyy", "nettruyen", "bachngocsach", "vtruyen", "webtoon",
    "truyencv", "truyenchu", "truyenq", "docln", "sangtacviet", "truyen1", "truyen2",
    # nền tảng chung
    "facebook", "tiktok", "youtube", "shopee", "reddit", "quora", "google",
    # KHÔNG để "tải" dạng từ đơn: bỏ dấu thành "tai", trùng "tài" trong "sách tài
    # chính" (hàng thật của site). Ý "tải về" đã có ở BLOCK_PHRASES.
    "wikipedia", "app", "download", "apk", "pdf", "epub", "prc",
    # định dạng site không có
    "audio", "mp3", "nghe", "podcast", "phim", "anime", "manhua", "manhwa",
    "hoạt hình", "trailer", "tập 1", "vietsub", "thuyết minh",
    "truyện tranh", "truyện chữ scan", "ngôn tình audio",
    # 18+ / lệch nhóm
    "sắc", "h văn", "np", "nc17", "18+", "đam mỹ", "bách hợp", "gl", "bl",
)

# Vài mục trên là CỤM, không phải từ đơn — vì từ đơn khớp oan:
#   "tải" → không dấu "tai" → khớp luôn "tài chính" (sách tài chính là hàng thật)
# nên ở đây dùng cụm để giữ đúng ý "tải về / tải miễn phí".
BLOCK_PHRASES = ("tai ve", "tai mien phi", "tai truyen", "tai sach", "tai full")


def _has_word(hay: str, needle: str) -> bool:
    """Khớp theo BIÊN TỪ, không phải substring.

    Substring gây khớp oan nặng: BLOCK_SUBS có "sắc" (→"sac") mà deacc("sách") là
    "sach" — CHỨA "sac" — nên mọi keyword non-fiction ("sách hay của Osho") bị loại
    sạch. Biên từ = ký tự 2 đầu không phải chữ/số.
    """
    if not needle:
        return False
    return re.search(r"(?<![0-9a-z])" + re.escape(needle) + r"(?![0-9a-z])",
                     hay) is not None


# Cửa sổ năm "gần hiện tại". Năm ngoài cửa sổ là phần TÊN TRUYỆN, không phải
# ý định tìm theo năm — "Trở Về Làng Chài Nhỏ 1982" phải giữ nguyên.
YEAR_WINDOW = (2015, 2099)


def stale_year(kw: str, this_year: int) -> bool:
    """Keyword đóng năm đã qua → query chết. Tháng 7/2026 mà viết bài nhắm
    "truyện ngôn tình mới nhất 2025" là nhắm nhu cầu năm ngoái."""
    for m in re.finditer(r"(?<!\d)(\d{4})(?!\d)", kw):
        y = int(m.group(1))
        if YEAR_WINDOW[0] <= y <= YEAR_WINDOW[1] and y < this_year:
            return True
    return False


def deacc(s: str) -> str:
    s = (s or "").replace("đ", "d").replace("Đ", "D")
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return " ".join(s.lower().split())


def norm(s: str) -> str:
    return " ".join((s or "").lower().split())


def _n_marks(s: str) -> int:
    """Đếm dấu tiếng Việt — dùng để chọn bản có dấu khi gộp trùng."""
    d = unicodedata.normalize("NFD", s or "")
    return sum(1 for c in d if unicodedata.category(c) == "Mn") + (s or "").count("đ")


def _cache_path(url):
    import hashlib
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
    return CACHE_DIR / f"{h}.txt"


def fetch(url, use_cache=True):
    """GET → text. Lỗi/timeout trả "" (1 nguồn chết không được làm sập cả bộ)."""
    if use_cache:
        p = _cache_path(url)
        try:
            if p.exists() and (time.time() - p.stat().st_mtime) < CACHE_TTL:
                return p.read_text(encoding="utf-8")
        except OSError:
            pass
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "*/*",
        "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.5",
    })
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            raw = r.read()
        text = raw.decode("utf-8", errors="replace")
    except Exception:
        return ""
    if use_cache:
        try:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            _cache_path(url).write_text(text, encoding="utf-8")
        except OSError:
            pass
    return text


def _url(source, q):
    qs = urllib.parse.quote(q)
    if source == "google":
        return ("https://suggestqueries.google.com/complete/search"
                f"?client=chrome&hl=vi&gl=vn&q={qs}")
    if source == "youtube":
        return ("https://suggestqueries.google.com/complete/search"
                f"?client=youtube&ds=yt&hl=vi&gl=vn&q={qs}")
    if source == "bing":
        return f"https://api.bing.com/osjson.aspx?market=vi-VN&query={qs}"
    if source == "ddg":
        return f"https://duckduckgo.com/ac/?kl=vn-vi&q={qs}"
    raise ValueError(source)


def parse(source, text):
    """Trả list keyword theo đúng thứ tự nguồn xếp. Parse fail → []."""
    if not text.strip():
        return []
    try:
        if source == "youtube":
            m = re.search(r"^[^(]*\((.*)\)\s*;?\s*$", text.strip(), re.S)
            data = json.loads(m.group(1)) if m else json.loads(text)
            return [it[0] for it in data[1]
                    if isinstance(it, list) and it and isinstance(it[0], str)]
        data = json.loads(text)
        if source == "ddg":
            return [d.get("phrase", "") for d in data if isinstance(d, dict)]
        # google + bing: ["seed", [suggestions], ...]
        if isinstance(data, list) and len(data) > 1 and isinstance(data[1], list):
            return [s for s in data[1] if isinstance(s, str)]
    except Exception:
        return []
    return []


def variants(seed, depth):
    """Sinh query để hỏi autocomplete. depth 1 = hậu/tiền tố, 2 = thêm a-z."""
    out = [seed]
    out += [f"{seed} {s}" for s in SUFFIXES]
    out += [f"{p} {seed}" for p in PREFIXES]
    if depth >= 2:
        out += [f"{seed} {c}" for c in ALPHABET]
    seen, uniq = set(), []
    for q in out:
        k = norm(q)
        if k and k not in seen:
            seen.add(k)
            uniq.append(q)
    return uniq


def blocked(kw, extra=()):
    """Nhắc đối thủ/nền tảng khác/định dạng site không có → loại.

    Khớp theo biên từ, KHÔNG substring (xem _has_word: substring làm "sách" trúng
    luật "sắc"). Cụm nhiều từ khớp thẳng vì đã đủ hẹp.
    """
    low = deacc(kw)
    if any(_has_word(low, deacc(b)) for b in BLOCK_SUBS):
        return True
    if any(deacc(p) in low for p in BLOCK_PHRASES):
        return True
    return any(_has_word(low, deacc(b)) for b in extra)


# Stopword khi tách token lõi (khớp CORE_STOP của keywords.py, dạng không dấu).
CORE_STOP = {"truyen", "sach", "top", "hay", "nhat", "full", "hoan", "moi",
             "review", "doc", "cua", "va", "cho", "la", "gi", "the", "a"}


def core_tokens(*srcs):
    """Token lõi (không dấu) để lọc drift. Bỏ stopword vì 'truyện' thì query nào cũng có."""
    toks = set()
    for s in srcs:
        for t in deacc(s or "").split():
            if t and t not in CORE_STOP:
                toks.add(t)
    return toks


def is_relevant(kw, cores):
    """Autocomplete drift rất mạnh: hỏi 'truyện điền văn nữ chính' mà Bing trả
    'nhận định về truyện ngắn'. Bắt buộc chứa ĐỦ token lõi mới giữ."""
    if not cores:
        return True
    low = deacc(kw)
    return all(t in low for t in cores)


def collect(seed, sources=SOURCES, depth=1, use_cache=True, workers=6,
            extra_block=(), cores=None, category="", this_year=None):
    """Gọi autocomplete, gộp, xếp hạng. Trả list (keyword, score, [nhóm nguồn]).

    score = TRUNG BÌNH trọng số vị trí (1/(i+1)) trên các query đã hỏi, không phải
    tổng — tổng thì keyword lọt vào nhiều biến thể tự phồng lên, đọc như "phổ biến
    hơn" trong khi chỉ là "khớp nhiều biến thể hơn".

    Nhóm nguồn: bing+ddg tính 1 phiếu (DDG proxy Bing). Nhiều nhóm đồng thuận =
    tin hơn, nhưng KHÔNG phải search volume.
    """
    if cores is None:
        cores = core_tokens(seed, category)
    if this_year is None:
        from datetime import date
        this_year = date.today().year
    qs = variants(seed, depth)
    jobs = [(s, q) for s in sources for q in qs]
    hits = {}
    seed_n = norm(seed)
    # Đếm theo KEYWORD RIÊNG BIỆT, không theo lượt: 1 keyword lọt vào nhiều query
    # biến thể sẽ bị loại nhiều lần, đếm lượt thì log phồng ("bỏ 229" trong khi
    # chỉ có 90 keyword khác nhau).
    drop_sets = {"block": set(), "drift": set(), "stale": set()}

    def work(job):
        src, q = job
        return src, parse(src, fetch(_url(src, q), use_cache))

    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        for src, kws in ex.map(work, jobs):
            for i, kw in enumerate(kws):
                kw = " ".join((kw or "").split())
                k = norm(kw)
                if not k or k == seed_n:
                    continue
                if blocked(kw, extra_block):
                    drop_sets["block"].add(k)
                    continue
                if not is_relevant(kw, cores):
                    drop_sets["drift"].add(k)
                    continue
                if stale_year(kw, this_year):
                    drop_sets["stale"].add(k)
                    continue
                h = hits.setdefault(k, {"kw": kw, "sum": 0.0, "grp": set()})
                h["sum"] += 1.0 / (i + 1)
                h["grp"].add(SOURCE_GROUP.get(src, src))

    # Gộp bản không dấu vào bản có dấu ("doc truyen dien van" = "đọc truyện điền
    # văn", cùng 1 query). Giữ bản nhiều dấu hơn để bài viết ra chữ đúng chính tả.
    merged = {}
    for h in hits.values():
        k = deacc(h["kw"])
        cur = merged.get(k)
        if cur is None:
            merged[k] = h
            continue
        cur["sum"] += h["sum"]
        cur["grp"] |= h["grp"]
        if _n_marks(h["kw"]) > _n_marks(cur["kw"]):
            cur["kw"] = h["kw"]

    n_q = max(1, len(qs))
    rows = [(h["kw"], round(h["sum"] / n_q, 4), sorted(h["grp"]))
            for h in merged.values()]
    # điểm trước, rồi số nhóm đồng thuận, rồi ngắn trước
    rows.sort(key=lambda r: (-r[1], -len(r[2]), len(r[0])))
    return rows, {k: len(v) for k, v in drop_sets.items()}


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--seed", required=True, help="keyword gốc")
    ap.add_argument("--sources", default=",".join(SOURCES),
                    help=f"nguồn, phẩy phân cách. Có: {','.join(SOURCES)}")
    ap.add_argument("--depth", type=int, default=1, choices=(1, 2),
                    help="1 = hậu/tiền tố (default), 2 = thêm a-z (nhiều request hơn)")
    ap.add_argument("--no-cache", dest="cache", action="store_false", default=True,
                    help="bỏ cache /tmp (mặc định cache 6h)")
    ap.add_argument("-n", "--limit", type=int, default=40, help="số keyword in ra")
    ap.add_argument("--min-groups", type=int, default=1,
                    help="chỉ giữ keyword >= N nhóm nguồn đồng thuận (2 = chắc hơn)")
    ap.add_argument("--category", default="",
                    help="thêm token lõi để siết bộ lọc drift, vd 'điền văn'")
    args = ap.parse_args()

    srcs = tuple(s.strip() for s in args.sources.split(",") if s.strip() in SOURCES)
    if not srcs:
        ap.error(f"--sources không hợp lệ. Có: {','.join(SOURCES)}")

    t0 = time.time()
    rows, dropped = collect(args.seed, srcs, args.depth, args.cache,
                            category=args.category)
    kept = [r for r in rows if len(r[2]) >= args.min_groups][:args.limit]

    print("keyword\tkw_source\tscore\tsource_groups")
    for kw, score, grp in kept:
        print(f"{kw}\ttierS:suggest\t{score}\t{'+'.join(grp)}")

    n_req = len(srcs) * len(variants(args.seed, args.depth))
    multi = sum(1 for r in kept if len(r[2]) >= 2)
    print(f"[suggest] {len(kept)} keyword · {n_req} request ({','.join(srcs)}, "
          f"depth={args.depth}) · {multi} có ≥2 nhóm nguồn · "
          f"bỏ {dropped['drift']} lạc đề + {dropped['block']} đối thủ/định dạng "
          f"+ {dropped['stale']} năm cũ · "
          f"{time.time() - t0:.1f}s\n"
          f"[suggest] score = trung bình trọng số vị trí, KHÔNG phải search volume "
          f"(autocomplete không cho volume)", file=sys.stderr)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:  # noqa
        print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(2)
