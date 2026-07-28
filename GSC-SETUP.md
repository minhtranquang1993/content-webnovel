# Search Console cho bulk mode

Bulk mode chỉ có **1 keyword gốc** nhưng cần **N keyword phân biệt**. Keyword lấy theo 3 tầng:

| Tier | Nguồn | Cờ | Cần quyền gì |
|---|---|---|---|
| **A** | GSC API — script tự pull, không export tay | `--gsc-api` | tài khoản có quyền đọc property |
| **B** | CSV/ZIP export GSC anh gửi tay | `--gsc-csv <file>` | ai có quyền export hộ cũng được |
| **S** | Autocomplete Google/Bing/DDG/YouTube | `--suggest` | **không cần gì** |
| **C** | Tự sinh từ `data/truyen-data.json` + pool biến thể | (mặc định) | không cần gì |

Chạy được cùng lúc. Ưu tiên **A → B → S → C**, tier sau chỉ bù chỗ còn thiếu. Tier nào lỗi (hết hạn, mất mạng, sai quyền) thì **rơi mềm** xuống tier dưới — batch không bao giờ chết vì keyword.

Không cấu hình gì vẫn chạy được (tier C). Muốn keyword **thật** mà không có quyền GSC → dùng **tier S**, xem mục riêng ở dưới.

## Không có quyền add email vào GSC thì làm gì?

Quyền thêm user vào property là của **Owner**. Nhưng có 3 đường không cần quyền đó:

1. **OAuth thay vì service account** *(vẫn là tier A, dữ liệu thật, có volume)* — OAuth chạy bằng **chính tài khoản Google của anh**, nên nó thừa hưởng đúng quyền anh đang có. **Mở được property trong Search Console bằng mắt là API đọc được** — không phải thêm ai vào đâu cả. Đây là lý do service account cần add email mà OAuth thì không: service account là *danh tính thứ ba*, còn OAuth là *anh*. Xem "Cách 2: OAuth" ở dưới.
2. **Nhờ người có quyền export hộ** *(tier B)* — họ vào Search Console → Performance → Export → tải file về gửi anh. Anh chỉ cần nói đường dẫn file, không cần quyền gì trên property.
3. **Bỏ GSC hẳn, dùng tier S** — keyword từ autocomplete, không credential, không quyền, không đăng nhập. Mất phần search volume nhưng vẫn là nhu cầu tìm kiếm thật.

---

# Tier A — cài một lần, dùng mãi

## Bước 1: cài lib (1 lệnh)

```bash
bash ~/.claude/skills/content-webnovel/scripts/gsc-install.sh
```

Lib nằm trong venv riêng ở `~/.local/share/webnovel-gsc/venv`, **không** cài vào python hệ thống. Lý do: python homebrew là EXTERNALLY-MANAGED, và trên máy này `python@3.14.6` còn có `pyexpat` hỏng (link sai `libexpat`) khiến `python3 -m venv` fail. Script đi đường `uv` nên tránh được. Muốn vá python thì `brew reinstall expat python@3.14`, nhưng không bắt buộc — skill vẫn chạy bình thường.

## Bước 2: credential — **cần anh làm phần này**

Chọn 1 trong 2:

- **Không phải Owner của property** (không add được email vào GSC) → **bắt buộc dùng Cách 2 (OAuth)**. Cách 1 sẽ chết ở bước cuối.
- **Là Owner** → Cách 1 gọn hơn: không mở browser, token không hết hạn.

### Cách 1 — Service account (chỉ khi anh là Owner)

1. Vào [Google Cloud Console](https://console.cloud.google.com/) → tạo project mới (hoặc dùng project có sẵn).
2. **APIs & Services → Library** → tìm **Google Search Console API** → **Enable**.
3. **APIs & Services → Credentials → Create credentials → Service account** → đặt tên gì cũng được → Create.
4. Bấm vào service account vừa tạo → tab **Keys** → **Add key → Create new key → JSON** → tải file về.
5. Đổi tên file thành `service-account.json`, đặt vào:
   ```
   ~/.config/webnovel-gsc/service-account.json
   ```
6. **Bước hay bị quên:** mở file, copy giá trị `client_email` (dạng `ten@project.iam.gserviceaccount.com`). Vào [Search Console](https://search.google.com/search-console) → property `webnovel.vn` → **Settings → Users and permissions → Add user** → dán email đó, quyền **Full** (hoặc Restricted).

Không làm bước 6 thì API trả HTTP 403 — service account tự nó không thấy property nào.

### Cách 2 — OAuth (không cần quyền Owner)

1. Cloud Console → bước 1-2 như trên. Project này là **của riêng anh**, tạo mới được, không liên quan quyền trên property.
2. **Credentials → Create credentials → OAuth client ID** → Application type **Desktop app** → tải JSON về.
3. Đổi tên thành `oauth-client.json`, đặt vào `~/.config/webnovel-gsc/oauth-client.json`.
4. Nếu consent screen ở chế độ Testing thì thêm email của anh vào **Test users**.
5. Lần chạy đầu script mở browser để anh đồng ý. Token cache ở `~/.config/webnovel-gsc/token.json` (chmod 600).

**Không cần bước "add user"** — OAuth chạy dưới danh tính của chính anh, nên nó đọc được **đúng những property anh đang mở được** trong Search Console. Không cần Owner, không cần Full: quyền **Restricted** cũng đọc được Performance data. Ngược lại, service account là một danh tính thứ ba nên bắt buộc phải được add vào — đó là chỗ Cách 1 chết nếu anh không phải Owner.

Đổi lại: app chưa verify thì refresh token có thể hết hạn sau ~7 ngày, phải đồng ý lại. Script tự phát hiện và xin lại quyền.

Kiểm nhanh xem có đọc được property nào:

```bash
python3 ~/.claude/skills/content-webnovel/scripts/gsc-api.py --list-sites
```

Danh sách trả về rỗng → account của anh thật sự không có quyền trên property nào. Lúc đó đi tier B (nhờ export hộ) hoặc tier S.

> Credential nằm ở `~/.config/webnovel-gsc/` (chmod 700), **ngoài** skill dir — repo `content-webnovel` là public, không được để key lọt vào đó.

## Bước 3: kiểm

```bash
python3 ~/.claude/skills/content-webnovel/scripts/gsc-api.py --list-sites
```

Ra danh sách property + quyền là xong. Lỗi thường gặp:

| Báo lỗi | Nghĩa |
|---|---|
| `exit 4` / thiếu lib | chưa chạy `gsc-install.sh` |
| `exit 5` / chưa có credential | chưa đặt file vào `~/.config/webnovel-gsc/` |
| `HTTP 403` | chưa add email service account vào property (bước 6) |
| `account này không có property nào` | cùng nguyên nhân 403 |
| `HTTP 404` | sai `--site`, chạy `--list-sites` xem tên đúng |

## Dùng

Chỉ cần nói *"dùng gsc"* / *"pull gsc"* là tôi tự thêm cờ:

```
/content-webnovel blog20 https://webnovel.vn/dien-van/ --bulk 5 --gsc-api
```

Script tự lo phần còn lại:

- **Property:** tự chọn, ưu tiên domain property (`sc-domain:webnovel.vn`). Ép: `--gsc-site`.
- **Filter page:** tự suy từ URL/danh mục (`https://webnovel.vn/dien-van/` → `/dien-van/`) để chỉ lấy query của đúng danh mục đó. Ép: `--gsc-page-filter`.
- **Filter hẹp quá ra 0 query:** tự thử lại không filter, thay vì trả về rỗng.
- **Khoảng ngày:** 90 ngày. Đổi: `--gsc-days 365`.

Xem trước keyword nào vào bài nào, chưa sinh bài:

```bash
python3 ~/.claude/skills/content-webnovel/scripts/bulk-plan.py \
  --type blog20 --url https://webnovel.vn/dien-van/ --bulk 5 --dry-run --gsc-api
```

Cột `kw_source`: `tierA:api` = query thật từ API · `tierB:gsc` = từ file anh gửi · `tierC:*` = tự sinh.

### Cờ tier A

| Cờ | Default | Ý nghĩa |
|---|---|---|
| `--gsc-api` | tắt | bật tier A |
| `--gsc-site` | auto | property, vd `sc-domain:webnovel.vn` |
| `--gsc-days` | 90 | số ngày lùi |
| `--gsc-page-filter` | tự suy | chỉ query dẫn tới URL chứa chuỗi này |
| `--gsc-key-file` | `~/.config/...` | service account JSON khác |

`gsc-api.py` chạy riêng được (thêm `--out file.csv` để lưu lại, `--limit`, `--data-state all` để gồm cả data chưa chốt).

---

# Tier B — gửi file tay

Không muốn cài API thì export tay, vẫn dùng được nguyên phần dưới.

## Export

1. [Search Console](https://search.google.com/search-console) → property → **Performance / Hiệu suất**.
2. Đặt khoảng ngày **3 tháng hoặc 12 tháng** (mặc định 28 ngày quá ít query). Muốn sát 1 danh mục thì thêm filter **Page/Trang** chứa slug, vd `/dien-van/`.
3. Bảng dưới biểu đồ → tab **Queries / Truy vấn** → **Export / Xuất** → **CSV**.

Nhãn nút đổi theo ngôn ngữ giao diện, nhưng chỗ cần luôn là bảng dưới biểu đồ, tab query.

## Gửi

Script cần **đường dẫn file**, không đọc được nội dung dán vào chat. Lưu file rồi nói path:

```
/content-webnovel blog20 https://webnovel.vn/dien-van/ --bulk 5
GSC: ~/Downloads/webnovel-vn-performance.zip
```

Nói kiểu nào cũng được (*"gsc ở ~/Downloads/gsc.zip"*), tôi tự ghép `--gsc-csv`. Để trong `~/Downloads/` và giữ nguyên tên Google đặt là chắc nhất.

## Định dạng đọc được

Đã test, không phải chỉnh tay dạng nào:

| Dạng | Ví dụ | Impressions |
|---|---|---|
| ZIP tải thẳng từ GSC | `webnovel-vn-performance.zip` | ✅ |
| CSV header tiếng Anh | `Top queries,Clicks,Impressions,CTR,Position` | ✅ |
| CSV header tiếng Việt | `Truy vấn hàng đầu,Số lần nhấp,Số lần hiển thị,CTR,Vị trí` | ✅ |
| Paste tay 2 cột, không header | `truyen dien van hay⇥3450` | ❌ bỏ qua, giữ thứ tự sẵn có |

Chọn CSV thì Google tải về **1 zip nhiều sheet** (Queries, Pages, Countries, Devices, Dates…). **Không cần giải nén** — script tự chọn sheet query, đọc được cả sheet tên `Truy vấn.csv` trong zip không bật cờ UTF-8.

Chi tiết khác script tự lo:

- **Cột** dò theo tên không dấu, khớp một phần — `Top queries`, `Query`, `Truy vấn hàng đầu` đều nhận. Impressions nhận `Impressions`, `Số lần hiển thị`, `Lượt hiển thị`; không lẫn với `Số lần nhấp` (clicks).
- **Số** `3,450` (EN) và `3.450` (VI) đều ra 3450.
- **Dấu phân cách** phẩy, chấm phẩy, tab đều được.
- Không thấy header quen → cảnh báo rồi đọc cột 1 làm query, **bỏ impressions** thay vì đoán sai số.

---

# Tier S — autocomplete, không cần credential

Dùng khi **không có quyền GSC** (hoặc chỉ muốn bù thêm keyword). Không cài gì, không đăng nhập, không credential — chỉ cần mạng.

```bash
/content-webnovel blog20 --bulk 5 https://webnovel.vn/dien-van/ --suggest
```

## Nó lấy dữ liệu ở đâu

Gõ dở một cụm vào Google thì hộp gợi ý rơi xuống — đó là **query người thật đang gõ**, do chính Google thống kê. Tier S hỏi thẳng cái hộp đó qua endpoint autocomplete, 4 nguồn:

| Nguồn | Vì sao có mặt |
|---|---|
| Google | nguồn chính, kèm điểm xếp hạng nội bộ |
| Bing | trả bộ **khác** Google (`mỹ thực`, `làm ruộng`, `cổ đại`) → phủ rộng hơn |
| DuckDuckGo | đối chiếu (proxy index Bing nên **tính chung 1 phiếu với Bing**) |
| YouTube | corpus khác → ra cách gọi khác của cùng chủ đề |

Để lấy nhiều hơn 10 gợi ý/lần, script hỏi thêm seed ghép hậu tố/tiền tố hay đi với truyện Việt (`hay`, `hoàn`, `full`, `xuyên không`, `gia đấu`, `top …`, `review …`) — mặc định 72 request, xong trong ~3 giây. `--suggest-depth 2` thêm a-z, nhiều gợi ý đuôi dài hơn nhưng ~160 request.

## Xếp hạng — đọc kỹ chỗ này

**Autocomplete không cho search volume.** Không suy ra lượt tìm kiếm từ nó được, và script không bịa: cột `impressions` của tier S **luôn = 0**.

Thay vào đó xếp theo 2 tín hiệu thật:

1. **Vị trí** trong danh sách gợi ý (Google/Bing tự xếp phổ biến trước).
2. **Số nhóm nguồn đồng thuận** — keyword mà cả Google + Bing + YouTube đều gợi thì chắc hơn keyword chỉ 1 nguồn có. Xem cột `kw_source`: `tierS:bing+google+google-yt` = 3 nhóm.

Muốn chỉ lấy loại chắc: `scripts/suggest.py --seed "..." --min-groups 2`.

## Nó tự bỏ những gì

- **Lạc đề** — autocomplete drift rất mạnh: hỏi `truyện điền văn nữ chính`, Bing trả `nhận định về truyện ngắn`. Keyword phải chứa **đủ** token lõi mới giữ.
- **Đối thủ / nền tảng khác** — `wattpad`, `dtruyen`, `truyenfull`, `nettruyen`… Không lọc thì bài viết đi quảng cáo hộ họ.
- **Định dạng site không có** — `audio`, `mp3`, `nghe truyện`, `truyện tranh`, `pdf`, `epub`, `phim`, `anime`.
- **Lệch nhóm** — `sắc`, `18+`, `đam mỹ`, `bách hợp`.
- **Keyword đóng năm đã qua** — tháng 7/2026 mà viết bài nhắm `truyện ngôn tình mới nhất 2025` là nhắm nhu cầu năm ngoái. Năm nay và năm sau thì giữ; số năm trong **tên truyện** (`Trở Về Làng Chài Nhỏ 1982`) không bị đụng.

Số bị bỏ báo ở `note: tier S: +N keyword từ autocomplete (bỏ … lạc đề, … đối thủ, … năm cũ)`.

## Dùng riêng để xem keyword

```bash
python3 ~/.claude/skills/content-webnovel/scripts/suggest.py --seed "truyện điền văn"
python3 ~/.claude/skills/content-webnovel/scripts/suggest.py --seed "tiên nghịch" --min-groups 2
python3 ~/.claude/skills/content-webnovel/scripts/suggest.py --seed "sách Osho" --depth 2 -n 60
```

Kết quả cache 6 giờ ở `/tmp/webnovel-suggest-cache` (autocomplete không đổi theo phút). Ép gọi lại: `--no-cache`.

## Giới hạn thật

- **Không có volume.** Cần con số để quyết định thì phải đi tier A/B, không có đường khác.
- **Chỉ có keyword đã phổ biến đủ để vào autocomplete.** Đuôi dài rất hẹp sẽ không xuất hiện.
- **Không phải data của site anh** — là nhu cầu của thị trường. Muốn biết site anh *đang* hiển thị với query nào thì chỉ GSC trả lời được.
- Endpoint không phải API công bố. Google có thể đổi format hoặc chặn IP gọi quá dày; script gọi vừa phải + cache, và tier S lỗi thì **rơi mềm xuống tier C**, batch không chết.

---

# Áp dụng cho cả A và B

## Xử lý keyword

1. **Sort giảm dần theo impressions** — query nhiều hiển thị nhất thành bài đầu.
2. **Lọc lạc đề:** keyword phải chứa ≥1 token lõi của seed hoặc tên danh mục. Xuất cả property thì `truyện ngôn tình hay` bị loại khỏi batch `Điền Văn`. Số bị loại báo ở dòng `note: loại N query lạc đề`.
3. **So khớp không dấu 2 phía.** GSC tách `truyện điền văn hay` và `truyen dien van hay` thành 2 dòng riêng, người Việt gõ không dấu rất nhiều — không deaccent thì mất gần hết data thật.
4. **Dedup theo slug**, không chỉ theo chữ. Hai biến thể trên ra cùng tên file nên chỉ giữ 1, bản impressions cao thắng.

## Giới hạn

- **GSC chỉ có query site đã từng hiển thị.** Danh mục mới hoặc chưa index thì gần như rỗng → tier C gánh. Không phải lỗi.
- **Export tay giới hạn 1.000 dòng** (tier A mặc định cũng 1.000, đổi bằng `--limit`). Bulk nhiều nhất 20 bài nên thừa sức.
- **Data GSC trễ 2-3 ngày.** Cần cả phần chưa chốt thì `--data-state all`.
