#!/usr/bin/env python3
# batch-imgbb.py — Upload hàng loạt ảnh bìa lên ImgBB cho record còn thiếu `anh_imgbb`,
# rồi ghi ngược URL vào data/truyen-data.json. Nâng coverage ảnh TRƯỚC khi viết bài
# (toplist 5-10 truyện dễ dính truyện thiếu ảnh → bài lỗ chỗ).
#
# An toàn: backup JSON trước khi ghi, ghi atomic (tmp + replace), skip record thiếu
# file local thay vì crash, không đụng record đã có `anh_imgbb`.
#
# Usage:
#   python3 batch-imgbb.py                 # quét & upload thật
#   python3 batch-imgbb.py --dry-run       # chỉ liệt kê việc sẽ làm, KHÔNG upload/ghi
#   python3 batch-imgbb.py --limit 20      # giới hạn số ảnh upload lần này
#   python3 batch-imgbb.py --json <path> --images-dir <dir>
#
# Key ImgBB: qua scripts/imgbb-upload.sh (env IMGBB_API_KEY hoặc ~/.config/imgbb/api_key).
# Exit: 0 = xong (kể cả có skip) · 2 = lỗi tham số/không đọc được JSON · 3 = thiếu API key.

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(HERE)
DEFAULT_JSON = os.path.join(SKILL_DIR, "data", "truyen-data.json")
DEFAULT_IMAGES = os.path.expanduser("~/Downloads/webnovel")
UPLOAD_SH = os.path.join(HERE, "imgbb-upload.sh")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def atomic_write_json(path, data):
    d = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def has_key():
    if os.environ.get("IMGBB_API_KEY"):
        return True
    kf = os.environ.get("IMGBB_API_KEY_FILE")
    if kf and os.path.isfile(kf):
        return True
    return os.path.isfile(os.path.expanduser("~/.config/imgbb/api_key"))


def upload(img_path, name):
    """Gọi imgbb-upload.sh; trả URL hoặc None."""
    try:
        p = subprocess.run(
            ["bash", UPLOAD_SH, img_path, name],
            capture_output=True, text=True, timeout=120,
        )
    except Exception as e:  # noqa
        print(f"    ERR  upload exception: {e}", file=sys.stderr)
        return None
    if p.returncode != 0:
        print(f"    ERR  imgbb rc={p.returncode}: {p.stderr.strip()}", file=sys.stderr)
        return None
    url = p.stdout.strip()
    return url if url.startswith("http") else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=DEFAULT_JSON)
    ap.add_argument("--images-dir", default=DEFAULT_IMAGES)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="0 = không giới hạn")
    args = ap.parse_args()

    if not os.path.isfile(args.json):
        print(f"ERROR: không thấy JSON: {args.json}", file=sys.stderr)
        raise SystemExit(2)

    try:
        data = load_json(args.json)
    except Exception as e:  # noqa
        print(f"ERROR: JSON hỏng: {e}", file=sys.stderr)
        raise SystemExit(2)

    # Phân loại record
    base = os.path.realpath(args.images_dir)
    todo, no_local, missing_file, unsafe = [], 0, [], []
    for r in data:
        if r.get("anh_imgbb"):
            continue
        local = r.get("anh_local")
        if not local:
            no_local += 1
            continue
        # Chặn path escape: anh_local từ JSON có thể bị chỉnh tay/poison (../ hoặc path tuyệt đối)
        fp = os.path.realpath(os.path.join(base, local))
        if fp != base and not fp.startswith(base + os.sep):
            unsafe.append(local)
            continue
        if not os.path.isfile(fp):
            missing_file.append(local)
            continue
        todo.append((r, fp))

    total_missing = sum(1 for r in data if not r.get("anh_imgbb"))
    print(f"Records: {len(data)} | thiếu anh_imgbb: {total_missing}")
    print(f"  → upload được (có file local): {len(todo)}")
    print(f"  → skip (không field anh_local): {no_local}")
    print(f"  → skip (file local không tồn tại): {len(missing_file)}")
    if unsafe:
        print(f"  → skip (anh_local escape thư mục ảnh — KHÔNG upload): {len(unsafe)}")
        for u in unsafe[:5]:
            print(f"      unsafe: {u}")
    if missing_file[:5]:
        for m in missing_file[:5]:
            print(f"      thiếu: {m}")
        if len(missing_file) > 5:
            print(f"      … +{len(missing_file) - 5} file khác")

    if args.limit and len(todo) > args.limit:
        print(f"  (giới hạn --limit {args.limit}, làm {args.limit}/{len(todo)} lần này)")
        todo = todo[:args.limit]

    if not todo:
        print("Không có ảnh nào để upload. Xong.")
        return

    if args.dry_run:
        print("\n--dry-run: chỉ liệt kê, KHÔNG upload/ghi JSON.")
        for r, fp in todo:
            print(f"  would upload: {r.get('slug', '?')} <- {fp}")
        return

    if not has_key():
        print("ERROR: thiếu ImgBB API key (IMGBB_API_KEY hoặc ~/.config/imgbb/api_key).",
              file=sys.stderr)
        raise SystemExit(3)

    # Backup trước khi ghi
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = f"{args.json}.bak-{stamp}"
    shutil.copy2(args.json, backup)
    print(f"\nBackup JSON → {backup}")

    ok, fail = 0, 0
    for i, (r, fp) in enumerate(todo, 1):
        slug = r.get("slug", "") or os.path.splitext(os.path.basename(fp))[0]
        print(f"[{i}/{len(todo)}] {slug} …", flush=True)
        url = upload(fp, slug)
        if url:
            r["anh_imgbb"] = url
            ok += 1
            print(f"    OK   {url}")
            atomic_write_json(args.json, data)  # ghi dần để không mất tiến độ nếu gián đoạn
        else:
            fail += 1

    print(f"\nXong: {ok} upload OK, {fail} lỗi. JSON đã cập nhật ({args.json}).")
    if fail:
        print("Có ảnh lỗi — chạy lại để thử tiếp các record còn thiếu.")


if __name__ == "__main__":
    main()
