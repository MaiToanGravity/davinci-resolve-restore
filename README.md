# davinci-resolve-restore

Bộ công cụ Python hỗ trợ làm việc với cây thư mục backup DaVinci Resolve: quét thư mục gốc, thống kê folder có nhiều file, xuất danh mục ra **Excel** và **JSON**, cùng script kiểm tra **Scripting API** và automation (bàn phím / chuột).

## Yêu cầu

- **Python 3.10+** (khuyến nghị 64-bit trên Windows)
- DaVinci Resolve (khi dùng API trong `davinci-resolve-restore.py` — thường cần **Resolve đang mở**)

## Cài đặt

```bash
cd davinci-resolve-restore
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Phụ thuộc** (xem `requirements.txt`):

| Gói        | Dùng cho |
|-----------|-----------|
| `pandas`, `openpyxl` | `generate-data.py` — xuất Excel |
| `pyautogui`, `keyboard` | `davinci-resolve-restore.py` — smoke test UI / phím |

## Cấu trúc thư mục

| Đường dẫn | Mô tả |
|-----------|--------|
| `original/` | Thư mục nguồn cần quét (mặc định; có thể truyền đường dẫn khác). Thư mục này thường không commit (`.gitignore`). |
| `output/` | `data.xlsx`, `data.json` do `generate-data.py` tạo. |

## Scripts

### `generate-data.py`

Quét `original` (hoặc thư mục bạn chỉ định), chỉ xử lý các đường dẫn tương đối có **đúng 4 phần** (4 cấp folder dưới root), gom file trong từng folder đó, in thống kê và xuất:

- `output/data.xlsx` — nhiều sheet; tên sheet lấy từ hai phần đầu của path (ví dụ `Myers\Laptop\...` → sheet `Myers - Laptop`), cột: Folder, Backup Name, Timeline Name, Short description, Notes, Status (một số cột để trống cho chỉnh sau).
- `output/data.json` — mảng `{ "name": "<đường dẫn folder>", "files": ["<tên file>", ...] }`.

```bash
python generate-data.py
python generate-data.py "D:\path\to\backup\root"
python generate-data.py --folders -r
python generate-data.py -a
```

| Tham số | Ý nghĩa |
|---------|---------|
| `folder` (tùy chọn) | Thư mục gốc quét; mặc định `./original` cạnh script |
| `--folders` | Liệt kê thư mục con thay vì file làm “items” |
| `-r`, `--recursive` | Đệ quy khi duyệt |
| `-a`, `--absolute` | Dùng đường dẫn tuyệt đối thay vì tương đối `root` |

### `get-high-number-file.py`

Cùng logic lọc **4 phần path** và đếm file trong từng folder, nhưng **chỉ in** thống kê (folder có nhiều file nhất, tổng số file) — **không** ghi Excel/JSON.

```bash
python get-high-number-file.py
python get-high-number-file.py "D:\path\to\backup\root" -r
```

Tham số dòng lệnh giống `generate-data.py` (`folder`, `--folders`, `-r`, `-a`).

### `davinci-resolve-restore.py`

Smoke test:

- Kết nối **DaVinci Resolve Scripting API** (`DaVinciResolveScript`, `scriptapp("Resolve")`) sau khi cấu hình `sys.path` / biến môi trường (`RESOLVE_SCRIPT_LIB`, v.v.).
- `pyautogui` và `keyboard` (hook phím có thể cần chạy terminal **Administrator** trên Windows).

```bash
python davinci-resolve-restore.py
python davinci-resolve-restore.py --skip-resolve
python davinci-resolve-restore.py --skip-ui
python davinci-resolve-restore.py --listen --stop-key esc
```

### `davinci-resolve-automate-bins.py`

Đọc `output/data.json` (sau khi chạy `generate-data.py`). Hiện in dữ liệu ra console; phần tự động hóa bin trong Resolve đang mở rộng dần.

```bash
python davinci-resolve-automate-bins.py
```

## DaVinci Resolve API (ngắn gọn)

API không cài qua `pip`: module nằm trong thư mục **Scripting / Modules** của bản cài Resolve. Script trong repo tự thêm đường dẫn và gợi ý `RESOLVE_SCRIPT_LIB` trỏ `fusionscript.dll` trên Windows — chi tiết trong `configure_resolve_paths()` và `get_resolve()` trong `davinci-resolve-restore.py`.

Tài liệu chính thức: thư mục *Developer / Scripting* kèm Resolve, hoặc [Blackmagic Design — DaVinci Resolve](https://www.blackmagicdesign.com/products/davinciresolve).

## Ghi chú

- Định dạng path 4 phần phụ thuộc cách bạn đặt cây thư mục dưới `original`; nếu không khớp, script có thể không thu được `folder_data` nào.
- `original/` và `output/` được liệt kê trong `.gitignore` để tránh commit dữ liệu cục bộ.


## Backup Location: C:\Toan\Project\Davinci Restore\Resolve Project Backups