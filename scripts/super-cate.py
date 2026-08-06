#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""super-cate.py — orchestrator cho type `super-cate`: 1 lệnh → 19 bài toplist
trên 19 danh mục KHÁC NHAU (10 pbn + 4 blog20 + 5 forum).

Vì sao script riêng, KHÔNG nhồi vào bulk-plan.py: bulk-plan là single-scope by
design (1 danh mục / 1 truyện / 1 tác giả mỗi lệnh) và cap toplist ở 1-2 slot vì
2 toplist cùng pool trùng >80% list. super-cate ngược lại: multi-scope, mỗi dòng
1 danh mục riêng, toàn bộ là toplist. Nhồi vào sẽ phá 5 mode hiện có.

2 SUBCOMMAND — allocation đóng băng ở bước plan:

    plan [--dry-run]        lập ma trận, ghi plan.tsv + sidecar plan/{idx}.json
    commit-usage --plan F   đọc plan.tsv đó, tăng used_count, ghi state atomic

Vì sao tách: commit phải cộng cho ĐÚNG batch đã verify PASS. Nếu commit tự lập
lại ma trận thì nó re-random và cộng cho danh mục/domain khác → rotation sai.

2 FILE, MỖI FILE 1 WRITER DUY NHẤT (1 file 2 người ghi sẽ ra dòng trùng):
    plan.tsv      chỉ `plan` ghi      — allocation đóng băng
    manifest.tsv  chỉ generator ghi   — kết quả thật (filename/so_chu/...)
commit-usage đọc plan.tsv, KHÔNG đọc manifest.tsv → generator không làm lệch đếm.

STATE = 1 FILE DUY NHẤT data/super-cate-usage.json (cate + site + pool cursor +
ledger). Hai file riêng sinh two-phase write: crash giữa 2 lần ghi là đếm lệch.

Exit: 0 OK · 2 lỗi tham số/đọc file · 3 BLOCKED (không đủ danh mục hợp lệ)
"""

import argparse
import datetime
import hashlib
import json
import os
import random
import subprocess
import sys
import time
import uuid
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_DIR / "scripts"
DATA_DIR = SKILL_DIR / "data"
CATEGORIES_TSV = DATA_DIR / "categories.tsv"
DATA_JSON = DATA_DIR / "truyen-data.json"
DOMAINS_TXT = DATA_DIR / "pbn-domains.txt"
STATE_JSON = DATA_DIR / "super-cate-usage.json"
LOCK_FILE = DATA_DIR / "super-cate-usage.json.lock"
PICK_VARIANT = SCRIPTS_DIR / "pick-variant.py"

sys.path.insert(0, str(SCRIPTS_DIR))
import keywords as kwmod  # slugify() xử lý 'đ' → 'd' đúng; tái dùng, không viết lại

# Số bài mỗi nhóm — CHỐT CỨNG (Decision #11). Không có cờ điều chỉnh.
LAYOUT = [("pbn", 10), ("blog20", 4), ("forum", 5)]
TOTAL = sum(n for _, n in LAYOUT)

# n_display = min(pool, cap). SKILL.md gốc tự mâu thuẫn ("N = pool thật" vs
# "khuyến nghị top 5-10"): pool 61 thì không thể liệt kê hết trong 1000-1500
# chữ, forum 500-1000 chữ càng không. Cap chỉ áp trong super-cate.
CAP_DISPLAY = {"pbn": 10, "blog20": 10, "forum": 7}

MIN_POOL = 2          # pool 1 → không viết được toplist (SKILL.md: auto-switch review)
LOCK_TIMEOUT = 10.0   # giây, chờ lock của commit-usage khác


# ---------------------------------------------------------------- data loading

def die(msg, code=2):
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(code)


def load_categories():
    """data/categories.tsv → list dict. Dedupe theo cate_slug (giữ dòng đầu)."""
    if not CATEGORIES_TSV.is_file():
        die(f"không thấy {CATEGORIES_TSV.name}. Chạy trước: "
            f"py -3 scripts/import-cate.py")
    out, seen = [], set()
    for i, ln in enumerate(CATEGORIES_TSV.read_text(encoding="utf-8").splitlines()):
        if not ln.strip() or ln.startswith("#"):
            continue
        parts = ln.split("\t")
        if i == 0 and parts[0] == "cate_slug":
            continue
        if len(parts) < 4:
            continue
        slug, name, url, kws = parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3]
        if not slug or slug in seen:
            continue
        seen.add(slug)
        out.append({"slug": slug, "name": name, "url": url,
                    "kws": [k.strip() for k in kws.split("|") if k.strip()]})
    if not out:
        die(f"{CATEGORIES_TSV.name} rỗng/không parse được")
    return out


def load_records():
    try:
        with open(DATA_JSON, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        die(f"không đọc được {DATA_JSON}: {e}")


def canon_link(url: str) -> str:
    return (url or "").strip().rstrip("/")


def pool_for(records, slug):
    """Record có >=1 phần tử danh_muc mà slugify(phần tử) == slug.

    slugify() của keywords.py map 'đ'→'d' TRƯỚC khi strip dấu — bắt buộc, thiếu
    bước đó thì dien-van/co-dai/do-thi/hien-dai mismatch → pool = 0 sai.
    Dedupe theo link_truyen chuẩn hoá để 1 truyện không đếm 2 lần.
    """
    out, seen = [], set()
    for r in records:
        if not any(kwmod.slugify(g) == slug for g in (r.get("danh_muc") or [])):
            continue
        key = canon_link(r.get("link_truyen") or "") or (r.get("slug") or "")
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def load_domains():
    """Cùng convention bulk-plan.py: bỏ comment '#' + dòng trống."""
    try:
        return [ln.strip() for ln in DOMAINS_TXT.read_text(encoding="utf-8").splitlines()
                if ln.strip() and not ln.lstrip().startswith("#")]
    except OSError:
        return []


# ---------------------------------------------------------------------- state

EMPTY_STATE = {"version": 1, "cate": {}, "site": {}, "cursor": {}, "batches": []}


def state_hash(st) -> str:
    """Hash ổn định của state (sort_keys) — dùng cho state_revision + CAS."""
    blob = json.dumps(st, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


def data_revision() -> str:
    """sha256 byte-level của 2 file data. Chốt cứng thuật toán: đọc RAW bytes
    (không normalize newline, không parse JSON), thứ tự file cố định, file thiếu
    dùng b"". Không chốt thì CRLF của Windows / JSON reformat làm hash lệch giả.
    """
    h = hashlib.sha256()
    for p in (CATEGORIES_TSV, DATA_JSON):
        h.update(p.name.encode("utf-8"))
        h.update(b"\0")
        try:
            h.update(p.read_bytes())
        except OSError:
            h.update(b"")
        h.update(b"\0")
    return h.hexdigest()[:16]


class StateCorrupt(Exception):
    """State file tồn tại nhưng không parse được — KHÁC hẳn 'file chưa có'.

    Phân biệt 2 ca này là bắt buộc: 'chưa có' thì usage rỗng là đúng, còn 'hỏng'
    mà coi là rỗng thì rotation cấp lại đúng danh mục/domain vừa dùng, và tệ hơn
    là ghi đè mất ledger. Không gộp vào một giá trị trả về được.
    """


def read_state(strict: bool):
    """strict=True → state hỏng là FAIL FAST (thoát chương trình).

    Áp cho CẢ `plan` lẫn `commit-usage`, lý do khác nhau nhưng cùng nghiêm trọng:
      - commit-usage: ghi đè lên state hỏng = xoá sạch lịch sử rotation + ledger
        → danh mục/domain lặp sớm, batch đã commit có thể commit lại.
      - plan: coi state hỏng là rỗng thì allocation cấp lại đúng những danh mục
        vừa dùng nhiều nhất (rotation hỏng ngay từ gốc), rồi commit sau đó chỉ
        hợp thức hoá allocation sai.

    strict=False → RAISE StateCorrupt cho caller tự xử; **không** trả EMPTY_STATE.
    Trả rỗng ở đây từng là bug: đường CAS-recheck trước khi ghi mà nuốt lỗi thì
    state hỏng-nhưng-cứu-được vẫn bị đè.
    """
    if not STATE_JSON.is_file():
        return json.loads(json.dumps(EMPTY_STATE))
    try:
        st = json.loads(STATE_JSON.read_text(encoding="utf-8"))
        if not isinstance(st, dict):
            raise ValueError("state không phải object")
        for k, default in (("cate", {}), ("site", {}), ("cursor", {}), ("batches", [])):
            st.setdefault(k, default)
        st.setdefault("version", 1)
        return st
    except Exception as e:
        if strict:
            die(f"{STATE_JSON.name} hỏng ({e}). KHÔNG tự coi là rỗng vì rotation "
                f"sẽ cấp lại đúng danh mục/domain vừa dùng.\n"
                f"  • Kiểm/sửa tay file đó, HOẶC\n"
                f"  • plan: thêm --ignore-corrupt-state (chấp nhận rotation sai lượt này)\n"
                f"  • commit-usage: thêm --force-reset-state (ghi lại từ rỗng, "
                f"copy .bak trước)")
        raise StateCorrupt(str(e))


def write_state_atomic(st):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_JSON.with_suffix(STATE_JSON.suffix + ".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, STATE_JSON)


def acquire_lock():
    """Lock quanh TOÀN BỘ read-check-update-write. os.replace chống ghi dở nhưng
    KHÔNG chống lost update: 2 process đọc state trước khi process nào ghi thì cả
    hai cùng cộng và writer sau đè writer trước.
    O_CREAT|O_EXCL thay vì fcntl để chạy được trên Windows.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + LOCK_TIMEOUT
    while True:
        try:
            fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return
        except FileExistsError:
            if time.monotonic() >= deadline:
                die(f"không lấy được lock {LOCK_FILE.name} sau {LOCK_TIMEOUT:.0f}s "
                    f"— có commit-usage khác đang chạy. Nếu chắc không có, xoá file "
                    f"lock đó rồi chạy lại.")
            time.sleep(0.2)


def release_lock():
    try:
        LOCK_FILE.unlink()
    except OSError:
        pass


# ------------------------------------------------------------------ allocation

def rank(counts, items, rng):
    """Ít dùng nhất trước; tie → shuffle. Trả list đã xếp hạng.

    Shuffle trong tie quan trọng: không có nó thì thứ tự file quyết định và batch
    nào cũng bắt đầu từ phần tử #1 — đúng cái user yêu cầu tránh cho domain.
    """
    buckets = {}
    for it in items:
        buckets.setdefault(counts.get(key_of(it), 0), []).append(it)
    out = []
    for c in sorted(buckets):
        grp = buckets[c][:]
        rng.shuffle(grp)
        out.extend(grp)
    return out


def key_of(it):
    return it["slug"] if isinstance(it, dict) else it


def pick_stories(pool, slug, cursor, n):
    """Con trỏ pool cuốn tiếp mỗi batch (Decision #9).

    Danh mục lặp lại là điều không tránh được (20 danh mục hợp lệ / 19 bài mỗi
    batch), nên nếu luôn lấy 10 truyện ĐẦU thì list giống hệt batch trước →
    duplicate content thật giữa các domain PBN. Con trỏ cho pool 61 truyện 6
    batch list rời nhau hoàn toàn. Pool nhỏ (2-9) buộc phải lặp — chấp nhận.
    """
    if not pool:
        return [], 0
    start = cursor.get(slug, 0) % len(pool)
    take = min(n, len(pool))
    picked = [pool[(start + k) % len(pool)] for k in range(take)]
    return picked, (start + take) % len(pool)


def run_pick(target, site, noun_hint=""):
    """pick-variant.py --subtype toplist cho MỌI dòng, kể cả forum.

    KHÔNG dùng --subtype forum cho dòng forum: nó trả FORUM_ARCHETYPES '0 1 2'
    (3 post), sai với forum toplist 1 post. Đã verify: --subtype toplist trả
    ARCHETYPE / TITLE_INDEX / CATEGORY_CLASS / NOUN — đúng cho 1 bài.
    """
    cmd = [sys.executable, str(PICK_VARIANT), "--subtype", "toplist",
           "--target", target]
    if site:
        cmd += ["--site", site]
    if noun_hint:
        cmd += ["--genres", noun_hint]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           timeout=60)
    except Exception as e:
        print(f"[super-cate] note: pick-variant lỗi ({e}) → slot biến thể để '-'",
              file=sys.stderr)
        return {}
    if p.returncode != 0:
        print(f"[super-cate] note: pick-variant rc={p.returncode} cho "
              f"'{target}' → slot biến thể để '-'", file=sys.stderr)
        return {}
    out = {}
    for ln in (p.stdout or "").splitlines():
        if "\t" in ln:
            k, v = ln.split("\t", 1)
            out[k.strip()] = v.strip()
    return out


def first_int(s, default="-"):
    for tok in (s or "").replace("#", " ").split():
        if tok.isdigit():
            return tok
    return default


# --------------------------------------------------------------------- output

def downloads_dir() -> Path:
    """Cross-platform, cùng pattern bulk-plan.py — KHÔNG hardcode path Windows."""
    home = Path.home()
    d = home / "Downloads"
    return d if d.is_dir() else home


def out_dir_for(date_str: str):
    """<Downloads>/webnovel/{YYYY-MM-DD}. Trả (path, existing_plan_or_None).

    Folder ngày đã có `plan.tsv` = batch cũ (có thể đang dở). KHÔNG âm thầm bump
    sang -2: chạy lại giữa chừng thì việc đúng là RESUME batch đó, không phải đẻ
    batch mới (đẻ mới sẽ re-random allocation + phân mảnh output). Caller quyết
    định: mặc định dừng và chỉ đường resume, `--new-batch` mới cho bump.
    """
    base = downloads_dir() / "webnovel"
    d = base / date_str
    if not d.exists():
        return d, None
    if (d / "plan.tsv").is_file():
        return d, d / "plan.tsv"
    return d, None


def next_free_dir(date_str: str) -> Path:
    """Bump -2, -3 cho --new-batch (chủ ý chạy batch thứ 2 trong cùng ngày)."""
    base = downloads_dir() / "webnovel"
    d = base / date_str
    n = 2
    while d.exists():
        d = base / f"{date_str}-{n}"
        n += 1
    return d


PLAN_COLS = ["idx", "type", "subtype", "cate_name", "cate_url", "cate_slug",
             "pool", "n_display", "keyword", "kw_variants", "site",
             "archetype", "title_idx", "noun", "plan_file"]


# ------------------------------------------------------------------ cmd: plan

def cmd_plan(args):
    cats = load_categories()
    records = load_records()
    domains = load_domains()
    if args.ignore_corrupt_state:
        # Cờ thoát hiểm: user CHỦ Ý chấp nhận lập ma trận từ usage rỗng khi state
        # hỏng. plan chỉ đọc state (không ghi) nên không mất gì thêm, nhưng
        # rotation lượt này sẽ cấp lại danh mục/domain vừa dùng → phải cảnh báo.
        try:
            st = read_state(strict=False)
        except StateCorrupt as e:
            print(f"[super-cate] CẢNH BÁO: {STATE_JSON.name} hỏng ({e}) và có "
                  f"--ignore-corrupt-state → lập ma trận từ usage RỖNG. Rotation "
                  f"lượt này có thể trùng danh mục/domain vừa dùng. File hỏng "
                  f"KHÔNG bị sửa.", file=sys.stderr)
            st = json.loads(json.dumps(EMPTY_STATE))
    else:
        st = read_state(strict=True)

    seed = args.seed if args.seed is not None else random.randrange(1, 2**31)
    rng = random.Random(seed)

    # --- lọc theo pool -----------------------------------------------------
    eligible, dropped_small, dropped_zero = [], [], []
    pools = {}
    for c in cats:
        pl = pool_for(records, c["slug"])
        pools[c["slug"]] = pl
        c["pool"] = len(pl)
        if len(pl) == 0:
            dropped_zero.append(c)
        elif len(pl) < MIN_POOL:
            dropped_small.append(c)
        else:
            eligible.append(c)

    if dropped_zero:
        print(f"[super-cate] LOẠI {len(dropped_zero)} danh mục pool=0 (không có "
              f"trong {DATA_JSON.name}): "
              f"{', '.join(c['slug'] for c in dropped_zero)}", file=sys.stderr)
    if dropped_small:
        detail = ", ".join(f"{c['slug']}(pool={c['pool']})" for c in dropped_small)
        print(f"[super-cate] LOẠI {len(dropped_small)} danh mục pool<{MIN_POOL} "
              f"(không viết được toplist, SKILL.md auto-switch review): {detail}",
              file=sys.stderr)

    if len(eligible) < TOTAL:
        print(f"[super-cate] CẮT: chỉ {len(eligible)} danh mục hợp lệ (pool>="
              f"{MIN_POOL}) cho {TOTAL} bài → làm {len(eligible)} bài. KHÔNG pad "
              f"bằng danh mục đã dùng trong batch. Muốn đủ {TOTAL}: crawl thêm "
              f"truyện cho danh mục pool nhỏ, hoặc thêm danh mục vào "
              f"{CATEGORIES_TSV.name} rồi chạy lại import-cate.py.", file=sys.stderr)
    if not eligible:
        die("không có danh mục nào pool>=2 → không lập được ma trận", 3)

    # --- xếp hạng danh mục: ít dùng nhất trước, tie → random ---------------
    ranked = rank(st["cate"], eligible, rng)

    # Pool lớn ưu tiên pbn (Decision #14): pbn đi domain riêng nên cần list dài
    # và rời nhau nhất; pool nhỏ dạt về forum (cap 7, không backlink domain).
    # Chỉ sắp lại TRONG cùng bậc used_count để không phá rotation.
    by_count = {}
    for c in ranked:
        by_count.setdefault(st["cate"].get(c["slug"], 0), []).append(c)
    ordered = []
    for cnt in sorted(by_count):
        grp = sorted(by_count[cnt], key=lambda c: -c["pool"])
        ordered.extend(grp)

    need = min(TOTAL, len(ordered))
    chosen = ordered[:need]

    # --- domain cho pbn ----------------------------------------------------
    # Domain là dữ liệu BẮT BUỘC của pbn (ghép URL bài + self-link). Không đủ
    # domain thì CẮT số bài pbn + announce, KHÔNG phát dòng pbn với site rỗng —
    # dòng đó chắc chắn fail verify hoặc bắt user sửa tay, trái nguyên tắc
    # "cắt theo pool + announce, KHÔNG pad".
    want_pbn = min(LAYOUT[0][1], need)
    sites = []
    if domains:
        sites = rank(st["site"], domains, rng)[:want_pbn]
    n_pbn = len(sites)
    if n_pbn < want_pbn:
        if not domains:
            die(f"không đọc được domain nào từ {DOMAINS_TXT.name} → không lập được "
                f"ma trận pbn (pbn bắt buộc có domain để ghép URL bài + self-link). "
                f"Kiểm lại file đó rồi chạy lại.", 3)
        print(f"[super-cate] CẮT pbn: chỉ {n_pbn} domain trong {DOMAINS_TXT.name} "
              f"cho {want_pbn} bài pbn → làm {n_pbn} bài pbn. KHÔNG phát bài pbn "
              f"thiếu domain. Thêm domain vào file đó rồi chạy lại nếu muốn đủ "
              f"{want_pbn}.", file=sys.stderr)

    # --- dựng từng dòng ----------------------------------------------------
    date_str = args.date or datetime.date.today().strftime("%Y-%m-%d")
    out_dir, existing = out_dir_for(date_str)
    if existing and not args.dry_run:
        if args.new_batch:
            out_dir = next_free_dir(date_str)
            print(f"[super-cate] --new-batch: folder ngày đã có batch → dùng "
                  f"{out_dir.name}", file=sys.stderr)
        else:
            # Chạy lại giữa chừng: việc đúng là RESUME, không đẻ batch mới.
            done = set()
            man = existing.parent / "manifest.tsv"
            if man.is_file():
                for ln in man.read_text(encoding="utf-8").splitlines():
                    if ln.startswith("#") or ln.split("	")[0] in ("idx", ""):
                        continue
                    done.add(ln.split("	")[0].strip())
            total = sum(1 for ln in existing.read_text(encoding="utf-8").splitlines()[2:]
                        if ln.strip())
            miss = [str(i) for i in range(total) if str(i) not in done]
            miss_txt = (", thiếu idx: " + ", ".join(miss[:10])) if miss else ""
            die(f"folder {out_dir} ĐÃ có plan.tsv ({len(done)}/{total} bài xong"
                f"{miss_txt}).\n"
                f"  • Batch dở → RESUME: sinh nốt idx còn thiếu vào chính folder "
                f"đó (dùng plan.tsv + sidecar sẵn có), rồi verify + commit-usage. "
                f"KHÔNG chạy lại 'plan' (sẽ re-random allocation).\n"
                f"  • Muốn batch MỚI trong cùng ngày → thêm --new-batch.", 2)
    batch_id = str(uuid.uuid4())
    st_rev, dt_rev = state_hash(st), data_revision()

    cursor_next = {}
    rows, sidecars = [], {}
    idx = 0
    slot_plan = []
    for typ, cnt in LAYOUT:
        slot_plan.extend([typ] * (n_pbn if typ == "pbn" else cnt))
    slot_plan = slot_plan[:need]

    pbn_i = 0
    for typ in slot_plan:
        c = chosen[idx]
        pl = pools[c["slug"]]
        n_disp = min(len(pl), CAP_DISPLAY[typ])
        picked, nxt = pick_stories(pl, c["slug"], st["cursor"], n_disp)
        cursor_next[c["slug"]] = nxt

        site = ""
        if typ == "pbn":
            site = sites[pbn_i] if pbn_i < len(sites) else ""
            pbn_i += 1

        # keyword: random 1 biến thể làm primary (Decision #8), còn lại rải trong bài
        kws = c["kws"][:] or [f"truyện {c['name'].lower()}"]
        primary = rng.choice(kws)
        variants = [k for k in kws if k != primary]

        noun_hint = "|".join((picked[0].get("danh_muc") or [])[:3]) if picked else ""
        pv = run_pick(c["name"], site, noun_hint)

        plan_file = "-" if args.dry_run else f"plan/{idx}.json"
        rows.append({
            "idx": idx, "type": typ, "subtype": "toplist",
            "cate_name": c["name"], "cate_url": c["url"], "cate_slug": c["slug"],
            "pool": len(pl), "n_display": n_disp,
            "keyword": primary, "kw_variants": "|".join(variants),
            "site": site,
            "archetype": pv.get("ARCHETYPE", "-") or "-",
            "title_idx": first_int(pv.get("TITLE_INDEX", "")),
            "noun": pv.get("NOUN", "truyện") or "truyện",
            "plan_file": plan_file,
        })
        sidecars[idx] = [
            {"tu_khoa": r.get("tu_khoa"), "slug": r.get("slug"),
             "link_truyen": r.get("link_truyen"), "anh_imgbb": r.get("anh_imgbb"),
             "danh_muc": r.get("danh_muc"), "tac_gia": r.get("tac_gia")}
            for r in picked
        ]
        idx += 1

    # --- in TSV ------------------------------------------------------------
    ver = (f"# super-cate-plan v1 batch_id={batch_id} seed={seed} "
           f"state_revision={st_rev} data_revision={dt_rev} rows={len(rows)}")
    if args.dry_run:
        ver += " DRY_RUN_ONLY"
    print(ver)
    print("\t".join(PLAN_COLS))
    for r in rows:
        print("\t".join(str(r[c]) for c in PLAN_COLS))

    # --- ghi file ----------------------------------------------------------
    if args.dry_run:
        print("[super-cate] --dry-run: KHÔNG ghi file nào (không plan.tsv, không "
              "sidecar, không đổi state). plan_file='-' + cờ DRY_RUN_ONLY → "
              "verify-bulk.py sẽ FAIL fast nếu ai đó đem output này đi verify.",
              file=sys.stderr)
    else:
        out_dir.mkdir(parents=True)          # KHÔNG exist_ok: xem docstring out_dir_for
        (out_dir / "plan").mkdir()
        for typ, _ in LAYOUT:
            (out_dir / typ).mkdir()
        lines = [ver, "\t".join(PLAN_COLS)]
        lines += ["\t".join(str(r[c]) for c in PLAN_COLS) for r in rows]
        (out_dir / "plan.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")
        for i, recs in sidecars.items():
            (out_dir / "plan" / f"{i}.json").write_text(
                json.dumps(recs, ensure_ascii=False, indent=1), encoding="utf-8")
        # cursor_next ghi vào plan.tsv? Không — nó là state, commit-usage tính lại
        # từ n_display để plan.tsv chỉ chứa allocation (1 nguồn sự thật cho commit).

    # --- announce ----------------------------------------------------------
    print(f"[super-cate] DATE: {date_str}", file=sys.stderr)
    print(f"[super-cate] OUT_DIR: {out_dir}", file=sys.stderr)
    print(f"[super-cate] batch_id: {batch_id}", file=sys.stderr)
    print(f"[super-cate] {len(rows)}/{TOTAL} bài — "
          f"{'đủ' if len(rows) == TOTAL else 'CẮT (xem dòng CẮT ở trên)'}: "
          f"{sum(1 for r in rows if r['type'] == 'pbn')} pbn, "
          f"{sum(1 for r in rows if r['type'] == 'blog20')} blog20, "
          f"{sum(1 for r in rows if r['type'] == 'forum')} forum",
          file=sys.stderr)
    print(f"[super-cate] danh mục: {len({r['cate_slug'] for r in rows})} phân biệt "
          f"/ {len(eligible)} hợp lệ / {len(cats)} trong {CATEGORIES_TSV.name}",
          file=sys.stderr)
    used_sites = [r["site"] for r in rows if r["type"] == "pbn"]
    print(f"[super-cate] domain: {len({s for s in used_sites if s})} phân biệt cho "
          f"{len(used_sites)} bài pbn"
          f"{' — ' + ', '.join(s for s in used_sites if s) if any(used_sites) else ' (CHƯA CÓ DOMAIN)'}",
          file=sys.stderr)
    # Con trỏ pool: nêu rõ dòng nào cuốn tiếp để user thấy list không trùng batch cũ
    reused = [r for r in rows if st["cursor"].get(r["cate_slug"], 0) > 0]
    if reused:
        print(f"[super-cate] con trỏ pool: {len(reused)} danh mục đã dùng ở batch "
              f"trước → lấy truyện TIẾP THEO, không trùng list cũ "
              f"({', '.join(r['cate_slug'] + '@' + str(st['cursor'].get(r['cate_slug'], 0)) for r in reused[:6])}"
              f"{' …' if len(reused) > 6 else ''})", file=sys.stderr)
    if len(eligible) < TOTAL * 2:
        print(f"[super-cate] LƯU Ý: {len(eligible)} danh mục hợp lệ mà mỗi batch "
              f"tiêu {len(rows)} → 2 batch KHÔNG THỂ rời nhau hoàn toàn; danh mục "
              f"sẽ lặp nhưng con trỏ pool đảm bảo LIST TRUYỆN rời nhau. Muốn danh "
              f"mục rời hẳn cần >={TOTAL * 2} danh mục hợp lệ.", file=sys.stderr)
    if not args.dry_run:
        print(f"[super-cate] BƯỚC SAU: sinh {len(rows)} bài → verify-bulk.py "
              f"--plan {out_dir / 'plan.tsv'} --manifest {out_dir / 'manifest.tsv'} "
              f"→ PASS rồi mới: super-cate.py commit-usage --plan "
              f"{out_dir / 'plan.tsv'}", file=sys.stderr)


# ----------------------------------------------------------- cmd: commit-usage

def parse_plan(path: Path):
    """Đọc plan.tsv → (meta dict, rows). FAIL fast nếu thiếu dòng version hoặc là
    output dry-run (không có sidecar → không thể verify/sinh bài)."""
    if not path.is_file():
        die(f"không thấy plan file: {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or not lines[0].startswith("# super-cate-plan v1"):
        die(f"{path.name} thiếu dòng version '# super-cate-plan v1' → không phải "
            f"plan.tsv hợp lệ (hoặc đã bị sửa tay). KHÔNG đoán, dừng.")
    meta = {}
    for tok in lines[0].split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            meta[k] = v
    if "DRY_RUN_ONLY" in lines[0]:
        die(f"{path.name} là output --dry-run (DRY_RUN_ONLY): không có sidecar, "
            f"KHÔNG dùng để commit. Chạy 'plan' thật trước.")
    hdr = lines[1].split("\t") if len(lines) > 1 else []
    rows = []
    for ln in lines[2:]:
        if not ln.strip():
            continue
        rows.append(dict(zip(hdr, ln.split("\t"))))
    if not rows:
        die(f"{path.name} không có dòng dữ liệu nào")
    if any(r.get("plan_file", "-") == "-" for r in rows):
        die(f"{path.name} có plan_file='-' (output dry-run) → không commit được.")
    return meta, rows


def cmd_commit(args):
    plan_path = Path(args.plan).expanduser()
    meta, rows = parse_plan(plan_path)
    batch_id = meta.get("batch_id", "")
    if not batch_id:
        die(f"{plan_path.name} thiếu batch_id ở dòng version")

    acquire_lock()
    try:
        if args.force_reset_state and STATE_JSON.is_file():
            bak = STATE_JSON.with_suffix(STATE_JSON.suffix + ".bak")
            bak.write_bytes(STATE_JSON.read_bytes())
            print(f"[super-cate] --force-reset-state: đã copy state sang "
                  f"{bak.name} trước khi ghi.", file=sys.stderr)
            st = json.loads(json.dumps(EMPTY_STATE))
        else:
            st = read_state(strict=True)

        if batch_id in st["batches"]:
            print(f"[super-cate] batch {batch_id} ĐÃ commit trước đó → bỏ qua "
                  f"(idempotent, không cộng đôi).", file=sys.stderr)
            return

        # Cảnh báo drift: state/data đổi so với lúc lập ma trận. Vẫn commit vì
        # đếm là cộng dồn (không mất dữ liệu), chỉ là rotation lượt đó kém tối ưu.
        cur_st, cur_dt = state_hash(st), data_revision()
        if meta.get("state_revision") and meta["state_revision"] != cur_st:
            print(f"[super-cate] WARN: state_revision lệch (plan="
                  f"{meta['state_revision']} vs nay={cur_st}) — có batch khác đã "
                  f"commit xen giữa. Vẫn commit (đếm cộng dồn), nhưng rotation "
                  f"lượt này không tối ưu.", file=sys.stderr)
        if meta.get("data_revision") and meta["data_revision"] != cur_dt:
            print(f"[super-cate] WARN: data_revision lệch (plan="
                  f"{meta['data_revision']} vs nay={cur_dt}) — categories.tsv "
                  f"hoặc truyen-data.json đã đổi sau khi lập ma trận.",
                  file=sys.stderr)

        n_cate = n_site = 0
        for r in rows:
            cs = (r.get("cate_slug") or "").strip()
            if cs:
                st["cate"][cs] = st["cate"].get(cs, 0) + 1
                n_cate += 1
                # con trỏ pool cuốn tiếp: tính từ n_display của chính dòng đó
                try:
                    nd = int(r.get("n_display") or 0)
                    pl = int(r.get("pool") or 0)
                except ValueError:
                    nd = pl = 0
                if pl > 0:
                    st["cursor"][cs] = (st["cursor"].get(cs, 0) + nd) % pl
            site = (r.get("site") or "").strip()
            if site:
                st["site"][site] = st["site"].get(site, 0) + 1
                n_site += 1
        st["batches"].append(batch_id)
        st["batches"] = st["batches"][-500:]   # ledger bounded, khỏi phình vô hạn

        # CAS: state có thể đã đổi giữa read và write dù đang giữ lock (vd ai đó
        # sửa tay). Recheck rồi mới replace. State hỏng ở ĐÚNG bước này thì DỪNG,
        # KHÔNG ghi đè — file hỏng vẫn có thể cứu tay, đè lên là mất hẳn ledger.
        try:
            on_disk = read_state(strict=False)
        except StateCorrupt as e:
            die(f"{STATE_JSON.name} vừa hỏng ({e}) giữa lúc commit → DỪNG, KHÔNG "
                f"ghi đè. Kiểm tay rồi chạy lại; batch {batch_id} chưa được cộng.")
        if STATE_JSON.is_file() and batch_id in on_disk.get("batches", []):
            print(f"[super-cate] batch {batch_id} vừa được commit bởi process "
                  f"khác → bỏ qua.", file=sys.stderr)
            return
        write_state_atomic(st)
        print(f"[super-cate] đã commit batch {batch_id}: +1 cho {n_cate} danh mục, "
              f"+1 cho {n_site} domain, con trỏ pool cuốn tiếp.", file=sys.stderr)
        print(f"[super-cate] state: {STATE_JSON}", file=sys.stderr)
    finally:
        release_lock()


# ------------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser(add_help=True, description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("plan", help="lập ma trận 19 dòng (ghi plan.tsv + sidecar)")
    p1.add_argument("--dry-run", action="store_true",
                    help="chỉ in stdout, KHÔNG ghi file nào")
    p1.add_argument("--seed", type=int, default=None,
                    help="seed cho tie-break. CHỈ để truy vết/tái lập trong cùng "
                         "state+data; KHÔNG phải cơ chế phục hồi batch")
    p1.add_argument("--date", default="", help="ghi đè ngày folder (YYYY-MM-DD)")
    p1.add_argument("--new-batch", dest="new_batch", action="store_true",
                    help="folder ngày đã có batch: cố ý tạo batch MỚI (bump -2) "
                         "thay vì dừng để resume")
    p1.add_argument("--ignore-corrupt-state", dest="ignore_corrupt_state",
                    action="store_true",
                    help="state hỏng: vẫn lập ma trận từ usage rỗng. CẢNH BÁO: "
                         "rotation sẽ cấp lại danh mục/domain vừa dùng")
    p1.set_defaults(func=cmd_plan)

    p2 = sub.add_parser("commit-usage", help="cộng usage cho batch trong plan.tsv")
    p2.add_argument("--plan", required=True, help="đường dẫn plan.tsv của batch")
    p2.add_argument("--force-reset-state", action="store_true",
                    help="state hỏng: cho ghi lại từ rỗng (copy .bak trước)")
    p2.set_defaults(func=cmd_commit)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
