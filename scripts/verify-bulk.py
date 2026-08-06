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
# Manifest nằm CÙNG folder với file bài (mỗi batch 1 folder riêng theo stamp), nên
# folder = manifest.parent — không cần truyền path folder.
#
# Usage:
#   verify-bulk.py --type pbn    --manifest <...>/2026-07-28_12h07/manifest-2026-07-28_12h07.tsv --site fbu.vn
#   verify-bulk.py --type blog20 --manifest <...>/2026-07-28_12h07/manifest-2026-07-28_12h07.tsv
#   verify-bulk.py --type forum  --manifest <...>/2026-07-28_12h07/manifest-2026-07-28_12h07.tsv
#
# Exit: 0 = PASS (không FAIL) · 1 = có FAIL · 2 = lỗi tham số / không đọc được manifest

import argparse
import csv
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

# Console Windows mặc định cp1252 → in keyword/H1 tiếng Việt trong report là
# UnicodeEncodeError. Ép UTF-8 cho stdout/stderr.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

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


def check_forum_toplist(body, year, n_display, sidecar_links, cate_url):
    """Contract `forum toplist` (type super-cate) — KHÁC forum thường ở số URL.

    forum thường: đúng 1 URL trần. forum toplist: n_display URL truyện trần
    (mỗi truyện 1 link) + 1 URL danh mục ở CUỐI bài làm CTA. Vẫn plain text,
    không thẻ HTML, 500-1000 chữ, có năm.

    Mọi URL truyện phải nằm trong sidecar plan/{idx}.json — biến "không bịa" từ
    lời hứa thành check máy được.
    """
    fails, oks = [], []
    if re.search(r"<[a-zA-Z/][^>]*>", body):
        tags = sorted(set(re.findall(r"<\s*(/?[a-zA-Z][a-zA-Z0-9]*)", body)))[:6]
        fails.append(f"forum toplist phải plain text, thấy thẻ HTML: {', '.join(tags)}")
    else:
        oks.append("plain text (không thẻ HTML)")

    urls = [u.rstrip(".,;") for u in bare_urls(body)]
    wn = [u for u in urls if WEBNOVEL_HOST in u.lower()]
    canon = lambda u: u.strip().rstrip("/").lower()
    cate_c = canon(cate_url)
    side_c = {canon(u) for u in sidecar_links}

    story_urls = [u for u in wn if canon(u) != cate_c]
    cate_hits = [u for u in wn if canon(u) == cate_c]

    # URL unique
    seen, dups = set(), []
    for u in wn:
        c = canon(u)
        if c in seen:
            dups.append(u)
        seen.add(c)
    if dups:
        fails.append(f"URL webnovel.vn LẶP: {', '.join(sorted(set(dups))[:4])} "
                     f"(mỗi URL chỉ 1 lần)")
    else:
        oks.append(f"{len(wn)} URL webnovel.vn, không lặp")

    # đúng n_display URL truyện
    if n_display and len(story_urls) != n_display:
        fails.append(f"{len(story_urls)} URL truyện, cần đúng {n_display} "
                     f"(= n_display trong plan.tsv)")
    elif n_display:
        oks.append(f"đúng {n_display} URL truyện trần")

    # mọi URL truyện ∈ sidecar
    if side_c:
        outside = [u for u in story_urls if canon(u) not in side_c]
        if outside:
            fails.append(f"{len(outside)} URL truyện KHÔNG có trong sidecar "
                         f"(bịa/lấy ngoài plan): {', '.join(outside[:3])}")
        else:
            oks.append("mọi URL truyện đều thuộc sidecar plan/")

    # 1 URL danh mục ở cuối
    if len(cate_hits) != 1:
        fails.append(f"{len(cate_hits)} URL danh mục, cần đúng 1 ({cate_url})")
    else:
        tail = body.strip()[-400:]
        if cate_url.rstrip("/") in tail or cate_url in tail:
            oks.append("URL danh mục ở cuối bài (CTA)")
        else:
            fails.append("URL danh mục KHÔNG nằm ở cuối bài (phải là CTA chốt)")

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


def read_plan(path: Path):
    """Đọc plan.tsv của super-cate → (meta, {idx: row}).

    FAIL fast, KHÔNG silent fallback: plan.tsv thiếu dòng version hoặc là output
    --dry-run thì dừng ngay. Rơi về nhánh cũ ở đây rất nguy hiểm — forum toplist
    cần n+1 URL mà nhánh forum cũ lại đòi đúng 1 URL → false PASS/FAIL.
    """
    if not path.is_file():
        print(f"ERROR: không thấy plan {path}", file=sys.stderr)
        raise SystemExit(2)
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or not lines[0].startswith("# super-cate-plan v1"):
        print(f"ERROR: {path.name} thiếu dòng version '# super-cate-plan v1' → "
              f"không phải plan.tsv hợp lệ (hoặc đã bị sửa tay). KHÔNG đoán, dừng.",
              file=sys.stderr)
        raise SystemExit(2)
    if "DRY_RUN_ONLY" in lines[0]:
        print(f"ERROR: {path.name} là output --dry-run (DRY_RUN_ONLY) — không có "
              f"sidecar nên KHÔNG verify được. Chạy 'super-cate.py plan' thật trước.",
              file=sys.stderr)
        raise SystemExit(2)
    meta = {}
    for tok in lines[0].split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            meta[k] = v
    hdr = lines[1].split("\t") if len(lines) > 1 else []
    rows = {}
    for ln in lines[2:]:
        if not ln.strip():
            continue
        r = dict(zip(hdr, ln.split("\t")))
        rows[str(r.get("idx", "")).strip()] = r
    if not rows:
        print(f"ERROR: {path.name} không có dòng dữ liệu", file=sys.stderr)
        raise SystemExit(2)
    if any(r.get("plan_file", "-") == "-" for r in rows.values()):
        print(f"ERROR: {path.name} có plan_file='-' (output dry-run) → không "
              f"verify được.", file=sys.stderr)
        raise SystemExit(2)
    return meta, rows


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
    p = subprocess.run(cmd, input=body, capture_output=True, text=True,
                       encoding="utf-8")
    return p.returncode == 0, (p.stdout + p.stderr).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", default="", choices=["", "pbn", "blog20", "forum"],
                    help="chế độ CŨ (1 type/batch). Bỏ khi dùng --plan (super-cate "
                         "đọc type theo từng dòng)")
    ap.add_argument("--manifest", required=True, help="đường dẫn manifest .tsv")
    ap.add_argument("--plan", default="",
                    help="super-cate: plan.tsv của batch. Có cờ này → chế độ "
                         "multi-type (type/subtype đọc theo từng dòng plan)")
    ap.add_argument("--site", default="",
                    help="domain PBN fallback cho dòng manifest KHÔNG có cột site. "
                         "Bulk 1-bài-1-domain thì khỏi truyền — đọc từ manifest")
    ap.add_argument("--year", type=int, default=datetime.date.today().year)
    ap.add_argument("--expect", type=int, default=0,
                    help="số bài kỳ vọng (0 = lấy theo số dòng manifest)")
    args = ap.parse_args()

    if not args.plan and not args.type:
        print("ERROR: cần --type (chế độ cũ) hoặc --plan (super-cate).",
              file=sys.stderr)
        raise SystemExit(2)

    man = Path(args.manifest).expanduser()
    if not man.is_file():
        print(f"ERROR: không thấy manifest {man}", file=sys.stderr)
        raise SystemExit(2)
    folder = man.parent

    # --- super-cate: join plan.tsv (allocation) + manifest.tsv (kết quả) ------
    plan_rows, plan_meta = {}, {}
    if args.plan:
        plan_meta, plan_rows = read_plan(Path(args.plan).expanduser())

    try:
        with open(man, encoding="utf-8", newline="") as f:
            raw = f.read()
    except Exception as e:
        print(f"ERROR: đọc manifest lỗi: {e}", file=sys.stderr)
        raise SystemExit(2)

    man_lines = raw.splitlines()
    if args.plan:
        # manifest.tsv của super-cate: 1 dòng version + 1 header, sau đó chỉ append.
        ver_lines = [l for l in man_lines if l.startswith("# super-cate-manifest")]
        if not ver_lines:
            print(f"ERROR: {man.name} thiếu dòng '# super-cate-manifest v1' "
                  f"(generator phải tạo 1 lần trước bài đầu).", file=sys.stderr)
            raise SystemExit(2)
        if len(ver_lines) > 1:
            print(f"ERROR: {man.name} có {len(ver_lines)} dòng version — dấu hiệu "
                  f"generation bị ngắt rồi khởi tạo lại. Kiểm tay.", file=sys.stderr)
            raise SystemExit(2)
        mb = ""
        for tok in ver_lines[0].split():
            if tok.startswith("batch_id="):
                mb = tok.split("=", 1)[1]
        if mb and plan_meta.get("batch_id") and mb != plan_meta["batch_id"]:
            print(f"ERROR: batch_id lệch — manifest={mb} vs plan="
                  f"{plan_meta['batch_id']}. Ghép nhầm batch.", file=sys.stderr)
            raise SystemExit(2)
        body_lines = [l for l in man_lines if not l.startswith("#")]
        if len(body_lines) > 1 and body_lines[0].split("\t")[0] == "idx":
            hdr_count = sum(1 for l in body_lines if l.split("\t")[0] == "idx")
            if hdr_count > 1:
                print(f"ERROR: {man.name} có {hdr_count} dòng header — generation "
                      f"bị khởi tạo lại giữa chừng.", file=sys.stderr)
                raise SystemExit(2)
        raw = "\n".join(body_lines)

    try:
        rows = [r for r in csv.DictReader(raw.splitlines(), delimiter="\t")]
    except Exception as e:
        print(f"ERROR: parse manifest lỗi: {e}", file=sys.stderr)
        raise SystemExit(2)

    if not rows:
        print("ERROR: manifest rỗng (0 dòng dữ liệu) — chưa sinh bài nào.",
              file=sys.stderr)
        raise SystemExit(2)

    if args.plan:
        # join: mỗi dòng manifest phải khớp 1 dòng plan; thiếu idx = bài chưa sinh
        missing = [i for i in plan_rows if i not in {str(r.get("idx", "")).strip()
                                                     for r in rows}]
        if missing:
            print(f"ERROR: thiếu {len(missing)} bài chưa sinh (idx: "
                  f"{', '.join(missing[:10])}). Sinh nốt rồi verify lại.",
                  file=sys.stderr)
            raise SystemExit(1)
        merged = []
        for r in rows:
            i = str(r.get("idx", "")).strip()
            if i not in plan_rows:
                print(f"ERROR: manifest có idx {i} KHÔNG có trong plan.tsv",
                      file=sys.stderr)
                raise SystemExit(2)
            m = dict(plan_rows[i])
            m.update({k: v for k, v in r.items() if v})
            merged.append(m)
        rows = merged

    batch_fails, batch_warns = [], []
    per_file = []          # (filename, subtype, [fail], [ok])
    h1_map = {}            # h1 → filename
    kw_map = {}            # keyword lower → filename
    versus_pairs = {}      # frozenset(slug,slug) → filename
    toplists = []          # (filename, [slug])

    sites_seen = []        # domain theo từng dòng (bulk pbn = 1 domain/bài)

    for row in rows:
        fname = (row.get("filename") or "").strip()
        subtype = (row.get("subtype") or "").strip()
        # type: chế độ cũ = 1 type toàn batch; super-cate = đọc theo từng dòng plan
        row_type = (row.get("type") or "").strip() if args.plan else args.type
        # Site đọc THEO DÒNG: bulk pbn phân 1 domain/bài nên self-link mỗi file trỏ
        # domain riêng. --site chỉ là fallback cho manifest cũ (không có cột site).
        row_site = (row.get("site") or "").strip() or args.site
        fails, oks = [], []
        # super-cate: filename là path tương đối từ OUT_DIR, LUÔN có prefix type
        # ("pbn/x.txt"). Verify resolve OUT_DIR/filename, KHÔNG tự ghép type —
        # tránh 2 cách hiểu giữa generator và verifier.
        path = folder / fname

        if not fname:
            batch_fails.append(f"manifest idx {row.get('idx')} thiếu cột filename")
            continue
        if args.plan:
            if "/" not in fname:
                batch_fails.append(f"idx {row.get('idx')}: filename '{fname}' thiếu "
                                   f"prefix type (cần dạng '{row_type}/ten-bai.txt')")
                continue
            if fname.split("/", 1)[0] != row_type:
                batch_fails.append(f"idx {row.get('idx')}: filename prefix "
                                   f"'{fname.split('/', 1)[0]}' ≠ type '{row_type}'")
                continue
        if not path.is_file():
            batch_fails.append(f"manifest trỏ file KHÔNG tồn tại: {fname}")
            continue

        header, body, had_header = parse_file(path)
        if not had_header:
            fails.append(f"thiếu separator '{SEPARATOR}' (không tách được header/body)")
        if not body.strip():
            fails.append("body rỗng sau separator")

        fails += check_header(header, body, row_type, row)

        if row_type == "forum":
            if args.plan and subtype == "toplist":
                # nhánh MỚI: n_display URL truyện + 1 URL danh mục cuối bài
                try:
                    nd = int(row.get("n_display") or 0)
                except ValueError:
                    nd = 0
                links = []
                pf = (row.get("plan_file") or "").strip()
                if pf and pf != "-":
                    try:
                        side = json.loads((folder / pf).read_text(encoding="utf-8"))
                        links = [s.get("link_truyen") or "" for s in side]
                    except Exception as e:
                        fails.append(f"không đọc được sidecar {pf}: {e}")
                f2, o2 = check_forum_toplist(body, args.year, nd, links,
                                             (row.get("cate_url") or "").strip())
            else:
                # forum thường (3 post/1 URL) — KHÔNG đổi hành vi cũ
                f2, o2 = check_forum(body, args.year)
            fails += f2
            oks += o2
        else:
            ok1, out1 = run_verify_one(body, row_type, subtype, args.year, row_site)
            if ok1:
                oks.append("verify-output.py PASS")
            else:
                detail = [l.strip() for l in out1.splitlines() if "FAIL" in l]
                fails.append("verify-output.py FAIL → " +
                             (" | ".join(detail) if detail else out1[:200]))

        # super-cate pbn/blog20: mọi URL truyện phải thuộc sidecar (check "không bịa")
        if args.plan and row_type in ("pbn", "blog20"):
            pf = (row.get("plan_file") or "").strip()
            if pf and pf != "-":
                try:
                    side = json.loads((folder / pf).read_text(encoding="utf-8"))
                    allowed = {(s.get("link_truyen") or "").rstrip("/").lower()
                               for s in side}
                    cate_c = (row.get("cate_url") or "").rstrip("/").lower()
                    used = {u.rstrip("/.,;").lower() for u in bare_urls(body)
                            if WEBNOVEL_HOST in u.lower()}
                    outside = [u for u in used if u not in allowed and u != cate_c]
                    if outside:
                        fails.append(f"{len(outside)} URL truyện NGOÀI sidecar "
                                     f"(bịa/lấy ngoài plan): {', '.join(sorted(outside)[:3])}")
                    else:
                        oks.append("mọi URL truyện thuộc sidecar plan/")
                except Exception as e:
                    fails.append(f"không đọc được sidecar {pf}: {e}")

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

        if row_type == "pbn":
            sites_seen.append(row_site)
            if not row_site:
                fails.append("thiếu domain (manifest không có cột site, cũng không "
                             "truyền --site) → không verify được self-link")
            elif header.get("site") and header["site"].strip().lower() != row_site.lower():
                fails.append(f"header site '{header['site']}' ≠ manifest '{row_site}'")

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

    # ----- domain per-bài (pbn) -----
    # Mục tiêu bulk pbn: N bài → N domain khác nhau. Trùng domain không phải lỗi cứng
    # (user có thể chủ ý, hoặc pool không đủ) nhưng phải báo để thấy footprint.
    n_sites = len({s for s in sites_seen if s})
    if sites_seen:
        if n_sites and n_sites < len(sites_seen):
            dup = {}
            for s in sites_seen:
                if s:
                    dup[s] = dup.get(s, 0) + 1
            rep = [f"{s} ×{c}" for s, c in dup.items() if c > 1]
            batch_warns.append(f"{n_sites} domain cho {len(sites_seen)} bài — dùng lại: "
                               f"{', '.join(rep)}. Muốn 1 bài 1 domain thì truyền đủ "
                               f"domain (hoặc --site-pool) khi lập ma trận")

    # ----- đủ N -----
    expect = args.expect or len(rows)
    n_ok_files = len(per_file)
    if n_ok_files != expect:
        batch_fails.append(f"chỉ verify được {n_ok_files} file, kỳ vọng {expect}")

    # ----- file lạ trong folder (cùng batch timestamp) -----
    # Nhận 2 format stamp: mới 2026-07-28_12h07 (kèm -2 nếu batch trùng phút) và cũ
    # 20260728-120732 — batch cũ trên disk vẫn phải verify được.
    stamp = re.search(r"manifest-(\d{4}-\d{2}-\d{2}_\d{2}h\d{2}(?:-\d+)?|\d{8}-\d{6})\.tsv$",
                      man.name)
    if stamp:
        listed = {(r.get("filename") or "").strip() for r in rows}
        stray = [p.name for p in folder.glob(f"*__{stamp.group(1)}.txt")
                 if p.name not in listed]
        if stray:
            batch_warns.append(f"{len(stray)} file cùng timestamp batch nhưng KHÔNG có "
                               f"trong manifest: {', '.join(stray[:5])}")

    # ----- report -----
    label = args.type or "super-cate (multi-type)"
    print(f"=== VERIFY BULK — {label} · {len(rows)} bài · {man.name} ===")
    print(f"folder: {folder}")
    if args.plan:
        by_t = {}
        for r in rows:
            by_t[(r.get("type") or "?").strip()] = by_t.get((r.get("type") or "?").strip(), 0) + 1
        print("type: " + ", ".join(f"{k} ×{v}" for k, v in sorted(by_t.items())))
    if sites_seen:
        print(f"domain: {n_sites} domain phân biệt cho {len(sites_seen)} bài"
              f"{' (1 bài 1 domain)' if n_sites == len(sites_seen) else ''}")
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
