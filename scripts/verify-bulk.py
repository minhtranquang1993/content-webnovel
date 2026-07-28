#!/usr/bin/env python3
# verify-bulk.py — Verify 1 batch bulk (content-webnovel). Wrapper MỎNG: loop từng file
# qua verify-output.py (không sửa/không viết lại script đó) rồi cộng thêm check CẤP-BATCH
# mà verify-output.py không bắt được vì nó chỉ soi từng file rời:
#   - đủ N file theo manifest, filename khớp manifest
#   - H1 phân biệt giữa các file
#   - keyword phân biệt giữa các file
#   - versus không trùng cặp (trùng cặp = trùng thân bài dù khác keyword/H1)
#   - toplist không trùng >80% danh sách truyện
#
# forum KHÔNG đi qua verify-output.py (script đó chỉ nhận --type pbn|blog20). Check riêng
# tại đây theo contract forum: plain text, đúng 1 URL trần, 500-1000 chữ, có năm.
#
# Usage:
#   verify-bulk.py --type pbn    --manifest <...>/manifest-20260727-185203.tsv --site fbu.vn
#   verify-bulk.py --type blog20 --manifest <...>/manifest-20260727-185203.tsv
#   verify-bulk.py --type forum  --manifest <...>/manifest-20260727-185203.tsv
#
# Exit: 0 = PASS (không FAIL) · 1 = có FAIL · 2 = lỗi tham số / không đọc được manifest

import argparse
import csv
import datetime
import re
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
VERIFY_ONE = SCRIPTS / "verify-output.py"

SEPARATOR = "---------- NỘI DUNG ĐĂNG ----------"
WEBNOVEL_HOST = "webnovel.vn"
TOPLIST_OVERLAP_MAX = 0.80

FORUM_MIN_WORDS, FORUM_MAX_WORDS = 500, 1000


def parse_file(path: Path):
    """Tách header metadata / body đăng theo separator. Không có separator → coi cả file
    là body (và báo FAIL vì thiếu header contract)."""
    raw = path.read_text(encoding="utf-8")
    if SEPARATOR in raw:
        head_raw, body = raw.split(SEPARATOR, 1)
    else:
        head_raw, body = "", raw
    header = {}
    for line in head_raw.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            header[k.strip().lower()] = v.strip()
    return header, body.strip(), bool(head_raw)


def strip_tags(html: str) -> str:
    html = re.sub(r"<script\b.*?</script>", " ", html, flags=re.S | re.I)
    html = re.sub(r"<style\b.*?</style>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", html)
    return (text.replace("&amp;", "&").replace("&nbsp;", " ")
                .replace("&quot;", '"').replace("&#39;", "'")
                .replace("&lt;", "<").replace("&gt;", ">"))


def count_words(text: str) -> int:
    text = re.sub(r"\s+", " ", text).strip()
    return len(text.split()) if text else 0


def get_h1(body: str) -> str:
    """pbn/blog20: nội dung <h1>. forum: dòng không rỗng đầu tiên (câu hỏi hook)."""
    m = re.search(r"<h1\b[^>]*>(.*?)</h1>", body, flags=re.S | re.I)
    if m:
        return " ".join(strip_tags(m.group(1)).split()).lower()
    for line in body.splitlines():
        if line.strip():
            return " ".join(line.split()).lower()
    return ""


def webnovel_slugs(body: str):
    """Slug truyện webnovel.vn xuất hiện trong body (để so cặp versus / list toplist)."""
    out = []
    for m in re.finditer(r"https?://(?:www\.)?webnovel\.vn/([^\s\"'<>)\]]*)", body, re.I):
        seg = m.group(1).split("/")[0].split("?")[0].strip().lower()
        if seg and seg not in out:
            out.append(seg)
    return out


def bare_urls(text: str):
    return re.findall(r"https?://[^\s\"'<>)\]]+", text)


def check_forum(body: str, year: int):
    """Contract forum: plain text (không thẻ HTML), đúng 1 URL trần, 500-1000 chữ, có năm."""
    fails, oks = [], []
    if re.search(r"<[a-zA-Z/][^>]*>", body):
        tags = sorted(set(re.findall(r"<\s*(/?[a-zA-Z][a-zA-Z0-9]*)", body)))[:6]
        fails.append(f"forum phải plain text, thấy thẻ HTML: {', '.join(tags)}")
    else:
        oks.append("plain text (không thẻ HTML)")

    urls = bare_urls(body)
    wn = [u for u in urls if WEBNOVEL_HOST in u.lower()]
    if len(wn) == 1:
        oks.append("đúng 1 URL webnovel.vn trần")
    elif not wn:
        fails.append("THIẾU URL webnovel.vn trần (cần đúng 1)")
    else:
        fails.append(f"{len(wn)} URL webnovel.vn (cần đúng 1)")

    wc = count_words(body)
    if wc < FORUM_MIN_WORDS:
        fails.append(f"body {wc} chữ < {FORUM_MIN_WORDS}")
    elif wc > FORUM_MAX_WORDS:
        fails.append(f"body {wc} chữ > {FORUM_MAX_WORDS}")
    else:
        oks.append(f"body {wc} chữ (trong {FORUM_MIN_WORDS}-{FORUM_MAX_WORDS})")

    if re.search(r"\b%d\b" % year, body):
        oks.append(f"năm {year} xuất hiện")
    else:
        fails.append(f"năm {year} KHÔNG xuất hiện (freshness fail)")
    return fails, oks


def check_header(header, body, type_, row):
    """Contract header/body theo type: pbn có URL+Slug ở header và KHÔNG lọt body;
    blog20 không được có URL/Slug ở đâu cả."""
    fails = []
    if type_ == "pbn":
        if not header.get("url"):
            fails.append("pbn: thiếu 'URL:' ở header")
        if not header.get("slug"):
            fails.append("pbn: thiếu 'Slug:' ở header")
        if re.search(r"^\s*(URL|Slug)\s*:", body, flags=re.M | re.I):
            fails.append("pbn: block URL/Slug LỌT vào body (phải nằm ở header)")
        # LƯU Ý: URL bài đích PHẢI xuất hiện trong body dưới dạng self-link (contract C8).
        # Chỉ block metadata "URL:"/"Slug:" là không được lọt vào body — đã check ở trên.
        # verify-output.py đếm self-link đúng 1 qua --site, khỏi check lại ở đây.
    elif type_ == "blog20":
        if header.get("url") or header.get("slug"):
            fails.append("blog20: KHÔNG được có URL/Slug (kể cả ở header)")
        if re.search(r"^\s*(URL|Slug)\s*:", body, flags=re.M | re.I):
            fails.append("blog20: body có block URL/Slug")
    for k in ("keyword", "subtype"):
        if not header.get(k):
            fails.append(f"header thiếu '{k}:'")
    if header.get("keyword") and row.get("keyword") and \
            header["keyword"].strip().lower() != row["keyword"].strip().lower():
        fails.append(f"header keyword '{header['keyword']}' ≠ manifest '{row['keyword']}'")
    if header.get("subtype") and row.get("subtype") and \
            header["subtype"].strip().lower() != row["subtype"].strip().lower():
        fails.append(f"header subtype '{header['subtype']}' ≠ manifest '{row['subtype']}'")
    return fails


def run_verify_one(body, type_, subtype, year, site):
    """Gọi verify-output.py cho 1 file (chỉ pbn/blog20). Trả (ok, output)."""
    cmd = [sys.executable, str(VERIFY_ONE), "--type", type_,
           "--subtype", subtype, "--year", str(year)]
    if site:
        cmd += ["--site", site]
    p = subprocess.run(cmd, input=body, capture_output=True, text=True)
    return p.returncode == 0, (p.stdout + p.stderr).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", required=True, choices=["pbn", "blog20", "forum"])
    ap.add_argument("--manifest", required=True, help="đường dẫn manifest-*.tsv")
    ap.add_argument("--site", default="", help="domain PBN (bắt buộc để verify self-link)")
    ap.add_argument("--year", type=int, default=datetime.date.today().year)
    ap.add_argument("--expect", type=int, default=0,
                    help="số bài kỳ vọng (0 = lấy theo số dòng manifest)")
    args = ap.parse_args()

    man = Path(args.manifest).expanduser()
    if not man.is_file():
        print(f"ERROR: không thấy manifest {man}", file=sys.stderr)
        raise SystemExit(2)
    folder = man.parent

    try:
        with open(man, encoding="utf-8", newline="") as f:
            rows = [r for r in csv.DictReader(f, delimiter="\t")]
    except Exception as e:
        print(f"ERROR: đọc manifest lỗi: {e}", file=sys.stderr)
        raise SystemExit(2)

    if not rows:
        print("ERROR: manifest rỗng (0 dòng).", file=sys.stderr)
        raise SystemExit(2)

    batch_fails, batch_warns = [], []
    per_file = []          # (filename, subtype, [fail], [ok])
    h1_map = {}            # h1 → filename
    kw_map = {}            # keyword lower → filename
    versus_pairs = {}      # frozenset(slug,slug) → filename
    toplists = []          # (filename, [slug])

    for row in rows:
        fname = (row.get("filename") or "").strip()
        subtype = (row.get("subtype") or "").strip()
        fails, oks = [], []
        path = folder / fname

        if not fname:
            batch_fails.append(f"manifest idx {row.get('idx')} thiếu cột filename")
            continue
        if not path.is_file():
            batch_fails.append(f"manifest trỏ file KHÔNG tồn tại: {fname}")
            continue

        header, body, had_header = parse_file(path)
        if not had_header:
            fails.append(f"thiếu separator '{SEPARATOR}' (không tách được header/body)")
        if not body.strip():
            fails.append("body rỗng sau separator")

        fails += check_header(header, body, args.type, row)

        if args.type == "forum":
            f2, o2 = check_forum(body, args.year)
            fails += f2
            oks += o2
        else:
            ok1, out1 = run_verify_one(body, args.type, subtype, args.year, args.site)
            if ok1:
                oks.append("verify-output.py PASS")
            else:
                detail = [l.strip() for l in out1.splitlines() if "FAIL" in l]
                fails.append("verify-output.py FAIL → " +
                             (" | ".join(detail) if detail else out1[:200]))

        # gom dữ liệu cấp-batch
        h1 = get_h1(body)
        if h1:
            if h1 in h1_map:
                batch_fails.append(f"H1 TRÙNG giữa {h1_map[h1]} và {fname}: \"{h1[:60]}\"")
            else:
                h1_map[h1] = fname
        else:
            fails.append("không tìm được H1/tiêu đề")

        kw = (row.get("keyword") or "").strip().lower()
        if kw:
            if kw in kw_map:
                batch_fails.append(f"keyword TRÙNG giữa {kw_map[kw]} và {fname}: \"{kw}\"")
            else:
                kw_map[kw] = fname

        slugs = webnovel_slugs(body)
        if subtype == "versus":
            story = [s for s in slugs if s]
            if len(story) >= 2:
                pair = frozenset(story[:2])
                if pair in versus_pairs:
                    batch_fails.append(
                        f"versus TRÙNG CẶP giữa {versus_pairs[pair]} và {fname}: "
                        f"{' + '.join(sorted(pair))} (trùng thân bài)")
                else:
                    versus_pairs[pair] = fname
        elif subtype == "toplist":
            toplists.append((fname, slugs))

        per_file.append((fname, subtype, fails, oks))

    # ----- toplist overlap -----
    for i in range(len(toplists)):
        for j in range(i + 1, len(toplists)):
            fa, sa = toplists[i]
            fb, sb = toplists[j]
            if not sa or not sb:
                continue
            inter = len(set(sa) & set(sb))
            ratio = inter / min(len(sa), len(sb))
            if ratio > TOPLIST_OVERLAP_MAX:
                batch_fails.append(
                    f"toplist TRÙNG {ratio:.0%} danh sách giữa {fa} và {fb} "
                    f"({inter}/{min(len(sa), len(sb))} truyện) — max "
                    f"{TOPLIST_OVERLAP_MAX:.0%}")

    # ----- đủ N -----
    expect = args.expect or len(rows)
    n_ok_files = len(per_file)
    if n_ok_files != expect:
        batch_fails.append(f"chỉ verify được {n_ok_files} file, kỳ vọng {expect}")

    # ----- file lạ trong folder (cùng batch timestamp) -----
    stamp = re.search(r"manifest-(\d{8}-\d{6})\.tsv$", man.name)
    if stamp:
        listed = {(r.get("filename") or "").strip() for r in rows}
        stray = [p.name for p in folder.glob(f"*__{stamp.group(1)}.txt")
                 if p.name not in listed]
        if stray:
            batch_warns.append(f"{len(stray)} file cùng timestamp batch nhưng KHÔNG có "
                               f"trong manifest: {', '.join(stray[:5])}")

    # ----- report -----
    print(f"=== VERIFY BULK — {args.type} · {len(rows)} bài · {man.name} ===")
    print(f"folder: {folder}")
    print()
    n_fail_files = 0
    for fname, subtype, fails, oks in per_file:
        mark = "FAIL" if fails else "PASS"
        if fails:
            n_fail_files += 1
        print(f"  [{mark}] {fname}  ({subtype})")
        for m in oks:
            print(f"          OK   {m}")
        for m in fails:
            print(f"          FAIL {m}")
    print()
    print("--- CHECK CẤP-BATCH ---")
    checks = [
        (f"đủ {expect} file theo manifest", n_ok_files == expect),
        (f"H1 phân biệt ({len(h1_map)} H1)", not any("H1 TRÙNG" in m for m in batch_fails)),
        (f"keyword phân biệt ({len(kw_map)} keyword)",
         not any("keyword TRÙNG" in m for m in batch_fails)),
        (f"versus không trùng cặp ({len(versus_pairs)} cặp)",
         not any("versus TRÙNG" in m for m in batch_fails)),
        (f"toplist không trùng >{TOPLIST_OVERLAP_MAX:.0%} ({len(toplists)} toplist)",
         not any("toplist TRÙNG" in m for m in batch_fails)),
    ]
    for label, ok in checks:
        print(f"  {'OK  ' if ok else 'FAIL'} {label}")
    for m in batch_warns:
        print(f"  WARN {m}")
    for m in batch_fails:
        print(f"  FAIL {m}")

    print("-" * 52)
    total_fail = n_fail_files + len(batch_fails)
    if total_fail:
        print(f"RESULT: FAIL — {n_fail_files} file lỗi, {len(batch_fails)} lỗi cấp-batch, "
              f"{len(batch_warns)} cảnh báo. Sửa rồi verify lại.")
        raise SystemExit(1)
    print(f"RESULT: PASS — {n_ok_files}/{expect} file OK, {len(batch_warns)} cảnh báo.")
    raise SystemExit(0)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # noqa
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
