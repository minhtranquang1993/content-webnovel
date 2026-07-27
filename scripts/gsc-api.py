#!/usr/bin/env python3
# gsc-api.py — Tier A: pull query thật từ Google Search Console API.
# (content-webnovel bulk mode). Thay cho việc export CSV tay mỗi lần (tier B).
#
# In ra CSV ĐÚNG SHAPE export GSC (`Top queries,Clicks,Impressions,CTR,Position`)
# để keywords.py dùng lại nguyên bộ parse của tier B — 1 đường parse duy nhất.
#
# Auth (thử theo thứ tự, cái nào có thì dùng):
#   1. --key-file / $WEBNOVEL_GSC_KEY            → service account JSON
#   2. --oauth-client / $WEBNOVEL_GSC_OAUTH_CLIENT → OAuth desktop client
#   3. ~/.config/webnovel-gsc/service-account.json
#   4. ~/.config/webnovel-gsc/oauth-client.json
# Credential KHÔNG BAO GIỜ nằm trong skill dir (repo public). Token OAuth cache ở
# ~/.config/webnovel-gsc/token.json, chmod 600.
#
# Lib Google nằm trong venv riêng (homebrew python EXTERNALLY-MANAGED): script tự
# re-exec sang venv python nếu import fail. Tạo venv: scripts/gsc-install.sh
#
# Usage:
#   gsc-api.py --list-sites
#   gsc-api.py                                    # auto-detect property, 90 ngày
#   gsc-api.py --site sc-domain:webnovel.vn --days 365
#   gsc-api.py --page-filter /dien-van/ --out ~/Downloads/gsc.csv
#
# Exit: 0 OK · 2 sai tham số / lỗi API · 4 thiếu lib · 5 thiếu credential
#       6 không tìm được property

import argparse
import csv
import datetime
import os
import sys
from pathlib import Path

CONFIG_DIR = Path(os.environ.get("WEBNOVEL_GSC_CONFIG",
                                 Path.home() / ".config" / "webnovel-gsc"))
TOKEN_PATH = CONFIG_DIR / "token.json"
DEFAULT_SA = CONFIG_DIR / "service-account.json"
DEFAULT_OAUTH = CONFIG_DIR / "oauth-client.json"
VENV_DIR = Path(os.environ.get("WEBNOVEL_GSC_VENV",
                               Path.home() / ".local" / "share" / "webnovel-gsc" / "venv"))

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
API_ROW_CAP = 25000          # trần rowLimit 1 request của API
DEFAULT_LIMIT = 1000         # khớp mặc định export bảng trên UI
INSTALL_HINT = ("Thiếu lib Google. Chạy:\n"
                "  bash ~/.claude/skills/content-webnovel/scripts/gsc-install.sh")


def _import_google():
    """Import lib Google; thiếu thì re-exec sang venv python (1 lần)."""
    try:
        from google.oauth2.service_account import Credentials as SACreds
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
        return SACreds, build, HttpError
    except ImportError:
        venv_py = VENV_DIR / "bin" / "python3"
        if not os.environ.get("WEBNOVEL_GSC_REEXEC") and venv_py.exists() \
                and Path(sys.executable).resolve() != venv_py.resolve():
            os.environ["WEBNOVEL_GSC_REEXEC"] = "1"
            os.execv(str(venv_py), [str(venv_py), os.path.abspath(__file__)] + sys.argv[1:])
        print(f"ERROR: {INSTALL_HINT}", file=sys.stderr)
        raise SystemExit(4)


def creds_service_account(path, SACreds):
    return SACreds.from_service_account_file(str(path), scopes=SCOPES)


def creds_oauth(client_path):
    """OAuth desktop flow. Token cache 600. Lần đầu mở browser để đồng ý."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print(f"ERROR: {INSTALL_HINT}", file=sys.stderr)
        raise SystemExit(4)

    creds = None
    if TOKEN_PATH.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        except Exception:
            creds = None  # token hỏng → xin lại, không chết
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as e:
            print(f"[gsc-api] refresh token hỏng ({type(e).__name__}) → xin lại quyền",
                  file=sys.stderr)
            creds = None
    if not creds or not creds.valid:
        print("[gsc-api] mở browser để đồng ý quyền đọc Search Console…", file=sys.stderr)
        flow = InstalledAppFlow.from_client_secrets_file(str(client_path), SCOPES)
        creds = flow.run_local_server(port=0)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")
    os.chmod(TOKEN_PATH, 0o600)
    return creds


def resolve_creds(args, SACreds):
    """Trả (creds, nhãn cách auth). Không in nội dung credential."""
    sa = args.key_file or os.environ.get("WEBNOVEL_GSC_KEY") or ""
    oc = args.oauth_client or os.environ.get("WEBNOVEL_GSC_OAUTH_CLIENT") or ""
    if sa:
        p = Path(sa).expanduser()
        if not p.exists():
            print(f"ERROR: không thấy service account key: {p}", file=sys.stderr)
            raise SystemExit(5)
        return creds_service_account(p, SACreds), f"service-account ({p.name})"
    if oc:
        p = Path(oc).expanduser()
        if not p.exists():
            print(f"ERROR: không thấy OAuth client: {p}", file=sys.stderr)
            raise SystemExit(5)
        return creds_oauth(p), f"oauth ({p.name})"
    if DEFAULT_SA.exists():
        return creds_service_account(DEFAULT_SA, SACreds), "service-account (mặc định)"
    if DEFAULT_OAUTH.exists():
        return creds_oauth(DEFAULT_OAUTH), "oauth (mặc định)"
    print("ERROR: chưa có credential Search Console.\n"
          f"  Đặt 1 trong 2 file vào {CONFIG_DIR}/ :\n"
          "    service-account.json  (khuyến nghị — không cần browser)\n"
          "    oauth-client.json     (dùng account Google của bạn)\n"
          "  Hướng dẫn lấy file: GSC-SETUP.md", file=sys.stderr)
    raise SystemExit(5)


def build_service(creds, build):
    """API 'searchconsole' v1; fallback 'webmasters' v3 cho lib cũ."""
    try:
        return build("searchconsole", "v1", credentials=creds, cache_discovery=False)
    except Exception:
        return build("webmasters", "v3", credentials=creds, cache_discovery=False)


def list_sites(service):
    resp = service.sites().list().execute()
    return [(e.get("siteUrl", ""), e.get("permissionLevel", ""))
            for e in (resp.get("siteEntry") or [])]


def pick_site(service, want):
    """Chọn property. Ưu tiên domain-property khớp, rồi URL-prefix khớp."""
    sites = list_sites(service)
    if not sites:
        print("ERROR: account này không có property nào trong Search Console.\n"
              "  Service account thì phải THÊM email của nó vào property "
              "(Settings → Users and permissions).", file=sys.stderr)
        raise SystemExit(6)
    urls = [u for u, _ in sites]
    if want:
        if want in urls:
            return want
        low = want.lower().replace("sc-domain:", "").rstrip("/")
        low = low.replace("https://", "").replace("http://", "")
        for u in urls:
            if u == f"sc-domain:{low}":
                return u
        for u in urls:
            if low in u.lower():
                return u
        print(f"ERROR: không thấy property khớp '{want}'. Có: {', '.join(urls)}",
              file=sys.stderr)
        raise SystemExit(6)
    for u in urls:                      # ưu tiên domain property
        if u.startswith("sc-domain:"):
            return u
    return urls[0]


def fetch_rows(service, site, start, end, limit, page_filter="",
               data_state="final", search_type="web"):
    """Query dimension=query, phân trang tới `limit`. Trả list dict row của API."""
    out = []
    start_row = 0
    while len(out) < limit:
        body = {
            "startDate": start,
            "endDate": end,
            "dimensions": ["query"],
            "rowLimit": min(API_ROW_CAP, limit - len(out)),
            "startRow": start_row,
            "type": search_type,
            "dataState": data_state,
        }
        if page_filter:
            body["dimensionFilterGroups"] = [{
                "filters": [{"dimension": "page",
                             "operator": "contains",
                             "expression": page_filter}]
            }]
        resp = service.searchanalytics().query(siteUrl=site, body=body).execute()
        rows = resp.get("rows") or []
        out.extend(rows)
        if len(rows) < body["rowLimit"]:
            break
        start_row += len(rows)
    return out[:limit]


def write_csv(rows, fh):
    """Ghi CSV đúng shape export GSC (EN header) — keywords.py parse sẵn."""
    w = csv.writer(fh)
    w.writerow(["Top queries", "Clicks", "Impressions", "CTR", "Position"])
    for r in rows:
        keys = r.get("keys") or [""]
        w.writerow([
            keys[0],
            int(r.get("clicks") or 0),
            int(r.get("impressions") or 0),
            f"{float(r.get('ctr') or 0) * 100:.2f}%",
            f"{float(r.get('position') or 0):.1f}",
        ])


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--site", default="", help="property (vd sc-domain:webnovel.vn). Bỏ = auto")
    ap.add_argument("--days", type=int, default=90, help="số ngày lùi (default 90)")
    ap.add_argument("--start", default="", help="YYYY-MM-DD (ưu tiên hơn --days)")
    ap.add_argument("--end", default="", help="YYYY-MM-DD (default hôm nay)")
    ap.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help=f"số query (default {DEFAULT_LIMIT})")
    ap.add_argument("--page-filter", dest="page_filter", default="",
                    help="chỉ query dẫn tới URL chứa chuỗi này (vd /dien-van/)")
    ap.add_argument("--no-retry-unfiltered", dest="retry_unfiltered",
                    action="store_false", default=True,
                    help="filter ra 0 query thì THÔI, không thử lại không filter")
    ap.add_argument("--data-state", dest="data_state", default="final",
                    choices=("final", "all"), help="all = gồm data chưa chốt")
    ap.add_argument("--search-type", dest="search_type", default="web",
                    choices=("web", "image", "video", "news", "discover", "googleNews"))
    ap.add_argument("--key-file", dest="key_file", default="", help="service account JSON")
    ap.add_argument("--oauth-client", dest="oauth_client", default="", help="OAuth client JSON")
    ap.add_argument("--out", default="", help="ghi CSV ra file (default stdout)")
    ap.add_argument("--list-sites", dest="list_sites", action="store_true",
                    help="in property khả dụng rồi thoát")
    args = ap.parse_args()

    SACreds, build, HttpError = _import_google()
    creds, how = resolve_creds(args, SACreds)
    service = build_service(creds, build)

    try:
        if args.list_sites:
            for u, perm in list_sites(service):
                print(f"{u}\t{perm}")
            print(f"[gsc-api] auth={how}", file=sys.stderr)
            return

        site = pick_site(service, args.site)
        end = args.end or datetime.date.today().isoformat()
        if args.start:
            start = args.start
        else:
            end_d = datetime.date.fromisoformat(end)
            start = (end_d - datetime.timedelta(days=max(1, args.days))).isoformat()

        rows = fetch_rows(service, site, start, end, args.limit,
                          args.page_filter, args.data_state, args.search_type)
        # Filter page (nhất là loại tự suy từ URL danh mục) có thể hẹp quá → rỗng.
        # Thử lại 1 lần không filter, hơn là trả 0 query rồi rơi hết về tier C.
        if not rows and args.page_filter and args.retry_unfiltered:
            print(f"[gsc-api] filter page '{args.page_filter}' ra 0 query → "
                  f"thử lại KHÔNG filter", file=sys.stderr)
            rows = fetch_rows(service, site, start, end, args.limit,
                              "", args.data_state, args.search_type)
            if rows:
                args.page_filter = ""  # để dòng announce cuối nói đúng sự thật
    except HttpError as e:
        code = getattr(getattr(e, "resp", None), "status", "?")
        msg = {
            403: "không có quyền đọc property này. Service account thì phải thêm "
                 "email của nó vào Search Console → Settings → Users and permissions.",
            404: "property không tồn tại (sai siteUrl). Chạy --list-sites để xem đúng tên.",
            429: "bị rate-limit, thử lại sau.",
        }.get(code, "API trả lỗi.")
        print(f"ERROR: HTTP {code} — {msg}", file=sys.stderr)
        raise SystemExit(2)
    except Exception as e:
        print(f"ERROR: gọi GSC API lỗi: {type(e).__name__}: {e}", file=sys.stderr)
        raise SystemExit(2)

    if args.out:
        p = Path(args.out).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="") as f:
            write_csv(rows, f)
        where = str(p)
    else:
        write_csv(rows, sys.stdout)
        where = "stdout"

    flt = f" · filter page contains '{args.page_filter}'" if args.page_filter else ""
    print(f"[gsc-api] {len(rows)} query · {site} · {start}→{end}{flt} · "
          f"auth={how} · out={where}", file=sys.stderr)
    if not rows:
        print("[gsc-api] KHÔNG có query nào — property mới/chưa index, hoặc filter "
              "quá hẹp, hoặc khoảng ngày quá ngắn. Bulk sẽ chạy tier C.", file=sys.stderr)


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
