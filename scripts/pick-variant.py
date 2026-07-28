#!/usr/bin/env python3
# pick-variant.py — Tính SẴN mọi lựa chọn deterministic (archetype / góc / title-index /
# verdict / category-class) cho skill content-webnovel, thay cho việc model tự tính hash
# trong prompt (LLM cộng code-point + chia lấy dư thường sai âm thầm → mất tính tái tạo).
#
# Toàn bộ công thức khớp SKILL.md ("Archetype khung bài", "Title pool", "Góc review",
# "Category-class"). In ra khối KEY<TAB>value + các dòng ANNOUNCE_* để dán ngoài HTML.
#
# Usage:
#   pick-variant.py --subtype review        --slug <slug> --genres "Tiên Hiệp|Huyền Huyễn" [--site <domain>]
#   pick-variant.py --subtype review-short  --slug <slug> --genres "..."                    [--site <domain>]
#   pick-variant.py --subtype toplist       --target "Tiên Hiệp"  --genres "Tiên Hiệp"       [--site <domain>]
#   pick-variant.py --subtype genre|guide   --target "Điền Văn"   --genres "Điền Văn"        [--site <domain>]
#   pick-variant.py --subtype versus        --slug-a <a> --slug-b <b> --genres "..."         [--site <domain>]
#   pick-variant.py --subtype forum         --slug <slug>            (story)                 [--site <domain>]
#   pick-variant.py --subtype forum         --target "Điền Văn"      (category)              [--site <domain>]
#
# --site: CHỈ dùng cho pbn (salt chống trùng across-domain). Cùng truyện + khác --site
#         => khác archetype/góc/title. blog20/forum KHÔNG truyền --site.
#
# --bulk-index i: CHỈ dùng cho bulk mode (bài thứ i trong batch, 0-based). Offset cộng
#         SAU phép chia (archetype //7, title //3) — cộng vào seed thì phải tới 7 seed
#         mới đổi được archetype, i=2..8 rơi cùng archetype. Cộng sau chia => phép đếm
#         vòng: 4 bài đầu chắc chắn 4 archetype khác. Seed CỐ ĐỊNH cho cả batch, chỉ i
#         chạy. Không truyền (default 0) => output y hệt đường chạy đơn.
#
# Exit: 0 OK · 2 thiếu/sai tham số.

import argparse
import sys
import unicodedata
from datetime import date

# Console Windows mặc định cp1252 → in tên thể loại/truyện tiếng Việt là
# UnicodeEncodeError, script chết giữa đường. Ép UTF-8 cho stdout/stderr.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

NONFIC_SET = {"phát triển bản thân", "tâm linh", "kinh doanh"}

ARCHETYPE_NAME = {0: "Chuẩn (classic)", 1: "Kể trải nghiệm (narrative)",
                  2: "Hỏi–đáp (Q&A-led)", 3: "Chốt trước (verdict-first)"}
PERSONA = {0: "reviewer khách quan", 1: "người đọc kể lại (ngôi 1 tiết chế)",
           2: "người dẫn-giải trực tiếp", 3: "người tư vấn"}

# Nhóm góc ưu tiên theo thể loại (khớp bảng "Mapping thể loại → nhóm góc").
GOC_NAME = {0: "Nhân vật", 1: "Thế giới & hệ thống", 2: "Cảm xúc & trải nghiệm đọc",
            3: "Motip & khác biệt", 4: "Cốt truyện & nhịp kể", 5: "Đối tượng phù hợp",
            6: "Highlight & điểm sáng", 7: "So sánh nhẹ"}
GOC_GROUPS = [
    (("tiên hiệp", "huyền huyễn", "tu tiên"), [1, 3, 0]),
    (("ngôn tình", "điền văn", "đô thị", "tình cảm"), [0, 2, 5]),
    (("trinh thám", "huyền nghi", "kinh dị"), [4, 6, 7]),
    (("xuyên không", "trọng sinh", "hệ thống"), [3, 0, 1]),
]
GOC_POOL_ALL = [0, 1, 2, 3, 4, 5, 6, 7]

VERDICT_NAME = {0: "điểm số x/10 (bám data scrape)", 1: "verdict chữ (không số)",
                2: "chốt cảm nhận ngắn (không số)"}


def norm(s: str) -> str:
    """Chuẩn hoá để tái tạo hash ổn định: lowercase + gộp khoảng trắng."""
    return " ".join(s.lower().split())


def strip_truyen(s: str) -> str:
    """Bỏ tiền tố 'Truyện ' khỏi tên thể loại (khớp 'CAT_TITLE strip')."""
    s = s.strip()
    low = s.lower()
    if low.startswith("truyện "):
        s = s[len("truyện "):].strip()
    return s


def codepoint_sum(s: str) -> int:
    return sum(ord(c) for c in s)


def parse_genres(raw: str):
    if not raw:
        return []
    return [g.strip() for g in raw.split("|") if g.strip()]


def category_class(genres):
    """non-fiction CHỈ khi MỌI thể loại ∈ NONFIC_SET; lẫn/không rõ → fiction (default)."""
    if not genres:
        return "fiction"
    if all(norm(g) in NONFIC_SET for g in genres):
        return "non-fiction"
    return "fiction"


def pick_goc(h, genres):
    """Góc chính/phụ theo nhóm ưu tiên của THỂ LOẠI ĐẦU; không match → pool chung 8 góc."""
    group = GOC_POOL_ALL
    if genres:
        first = norm(genres[0])
        for keys, grp in GOC_GROUPS:
            if first in keys:
                group = grp
                break
    n = len(group)
    chinh = group[h % n]
    phu = group[(h + 1) % n]
    if phu == chinh:  # invariant: mỗi nhóm ≥2 góc; phòng hờ nhóm suy biến
        for g in GOC_POOL_ALL:
            if g != chinh:
                phu = g
                break
    return chinh, phu


def emit(k, v):
    print(f"{k}\t{v}")


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--subtype", required=True,
                    choices=["review", "review-short", "toplist", "genre",
                             "guide", "versus", "forum"])
    ap.add_argument("--slug", default="")
    ap.add_argument("--target", default="")
    ap.add_argument("--slug-a", dest="slug_a", default="")
    ap.add_argument("--slug-b", dest="slug_b", default="")
    ap.add_argument("--genres", default="")
    ap.add_argument("--site", default="")
    ap.add_argument("--year", default=str(date.today().year))
    ap.add_argument("--bulk-index", dest="bulk_index", type=int, default=0,
                    metavar="i",
                    help="bài thứ i trong batch bulk (0-based); offset cộng SAU phép chia")
    args = ap.parse_args()

    st = args.subtype
    genres = parse_genres(args.genres)
    # target-based subtype (target = tên thể loại): thiếu --genres → suy từ --target
    # để CATEGORY_CLASS/NOUN không mặc định fiction sai (vd genre "Kinh doanh").
    if not genres and st in ("toplist", "genre", "guide") and args.target:
        genres = [strip_truyen(args.target)]
    cls = category_class(genres)
    noun = "truyện" if cls == "fiction" else "sách"
    salt = codepoint_sum(args.site) if args.site else 0
    bi = args.bulk_index  # offset bulk: cộng SAU phép chia, KHÔNG cộng vào seed

    # ----- Tính seed gốc theo subtype -----
    if st in ("review", "review-short"):
        if not args.slug:
            ap.error("review/review-short cần --slug")
        seed = codepoint_sum(norm(args.slug)) + salt
        seed_name = "h"
    elif st in ("toplist", "genre", "guide"):
        if not args.target:
            ap.error(f"{st} cần --target (tên thể loại/tác giả)")
        seed = codepoint_sum(norm(strip_truyen(args.target))) + salt
        seed_name = "h_top"
    elif st == "versus":
        if not (args.slug_a and args.slug_b):
            ap.error("versus cần --slug-a và --slug-b")
        pair = "".join(sorted([norm(args.slug_a), norm(args.slug_b)]))
        seed = codepoint_sum(pair) + salt
        seed_name = "h_vs"
    elif st == "forum":
        base = args.slug or args.target
        if not base:
            ap.error("forum cần --slug (story) hoặc --target (category)")
        key = norm(args.slug) if args.slug else norm(strip_truyen(args.target))
        seed = codepoint_sum(key) + salt
        seed_name = "h_fr"

    emit("SUBTYPE", st)
    emit(seed_name, seed)
    if args.site:
        emit("SITE_SALT", f"{salt} (site={args.site}; salt đã cộng vào {seed_name})")
    emit("CATEGORY_CLASS", cls)
    emit("NOUN", noun)
    if bi:
        emit("BULK_INDEX", f"{bi} (offset cộng sau phép chia; seed giữ nguyên)")

    # ----- Archetype -----
    if st == "review":
        arch = ((seed // 7) + bi) % 4
    elif st == "review-short":
        arch = ((seed // 7) + 1 + bi) % 4
    else:
        arch = ((seed // 7) + bi) % 4

    if st == "forum":
        s0 = arch
        posts = [s0 % 4, (s0 + 1) % 4, (s0 + 2) % 4]
        emit("FORUM_ARCHETYPES", " ".join(str(p) for p in posts))
        for i, p in enumerate(posts, 1):
            emit(f"POST{i}", f"#{p} {ARCHETYPE_NAME[p]} — persona: {PERSONA[p]}")
        print(f"ANNOUNCE_ARCHETYPE\tArchetype forum: post1 #{posts[0]}, "
              f"post2 #{posts[1]}, post3 #{posts[2]}")
        return

    emit("ARCHETYPE", arch)
    emit("ARCHETYPE_NAME", ARCHETYPE_NAME[arch])
    emit("PERSONA", PERSONA[arch])

    # ----- Title index -----
    if st == "review":
        if arch == 0:
            ti = ((seed // 3) + bi) % 6
            emit("TITLE_INDEX", f"{ti} (pool review gốc, 6 công thức)")
        else:
            ti = ((seed // 3) + bi) % 2
            emit("TITLE_INDEX", f"{ti} (họ archetype #{arch}, 2 công thức)")
        print(f"ANNOUNCE_TITLE\tTitle pool: review #{ti} (archetype #{arch})")
    elif st == "review-short":
        if arch == 0:
            ti = ((seed // 3) + 1 + bi) % 6
            emit("TITLE_INDEX", f"{ti} (pool review lệch +1, 6 công thức) + neo trải-nghiệm-chương")
        else:
            ti = ((seed // 3) + bi) % 2
            emit("TITLE_INDEX", f"{ti} (họ archetype #{arch}, 2 công thức) + neo trải-nghiệm-chương")
        print(f"ANNOUNCE_TITLE\tTitle pool: review-short #{ti} (archetype #{arch})")
    elif st == "toplist":
        if arch == 0:
            ti = ((seed // 3) + bi) % 5
            emit("TITLE_INDEX", f"{ti} (pool toplist gốc, 5 công thức)")
        else:
            ti = ((seed // 3) + bi) % 2
            emit("TITLE_INDEX", f"{ti} (họ archetype #{arch}, 2 công thức)")
        print(f"ANNOUNCE_TITLE\tTitle pool: toplist #{ti} (archetype #{arch})")
    elif st == "versus":
        ti = ((seed // 3) + bi) % 5
        emit("TITLE_INDEX", f"{ti} (pool versus, 5 công thức — archetype KHÔNG đổi họ title)")
        print(f"ANNOUNCE_TITLE\tTitle pool: versus #{ti}")
    elif st in ("genre", "guide"):
        ti = ((seed // 3) + bi) % 4
        emit("TITLE_INDEX", f"{ti} (pool {st}, 4 công thức — archetype KHÔNG đổi họ title)")
        print(f"ANNOUNCE_TITLE\tTitle pool: {st} #{ti}")

    # ----- Verdict + Góc -----
    # review: verdict xoay h mod 3 + 8 Góc. review-short: verdict CỐ ĐỊNH "ấn tượng
    # ban đầu" (đọc chương thật, không kế thừa 8 Góc — xem carve-out review-short).
    if st == "review":
        verdict = (seed + bi) % 3
        emit("VERDICT", f"{verdict} — {VERDICT_NAME[verdict]}")
        chinh, phu = pick_goc(seed + bi, genres)
        emit("GOC_CHINH", f"#{chinh} {GOC_NAME[chinh]}")
        emit("GOC_PHU", f"#{phu} {GOC_NAME[phu]}")
        glabel = genres[0] if genres else "pool chung"
        print(f"ANNOUNCE_GOC\tGóc review: {GOC_NAME[chinh]} + {GOC_NAME[phu]} "
              f"(thể loại: {glabel}, verdict: {VERDICT_NAME[verdict]})")
    elif st == "review-short":
        emit("VERDICT", 'ấn tượng ban đầu (nhãn cố định — dựa các chương đầu đã đọc)')

    # ----- Announce archetype -----
    print(f"ANNOUNCE_ARCHETYPE\tArchetype: #{arch} {ARCHETYPE_NAME[arch]} — "
          f"persona: {PERSONA[arch]}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # noqa
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
