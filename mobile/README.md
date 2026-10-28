# AutoTest Mobile — Kiểm thử Android Native bằng AI và Appium

> Adapter kiểm thử **Android native** của dự án [AutoTest](../README.md). Công cụ đọc cây giao diện ứng dụng qua Appium, gửi dữ liệu sang backend AI để sinh test case, tạo mã kiểm thử `pytest + Appium` và xuất báo cáo HTML.

## Mục lục

- [Tổng quan](#tổng-quan)
- [Tính năng chính](#tính-năng-chính)
- [Kiến trúc hệ thống](#kiến-trúc-hệ-thống)
- [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
- [Cài đặt](#cài-đặt)
- [Chạy kiểm thử](#chạy-kiểm-thử)
- [Tham số dòng lệnh](#tham-số-dòng-lệnh)
- [Kết quả đầu ra](#kết-quả-đầu-ra)
- [Cơ chế hoạt động](#cơ-chế-hoạt-động)
- [Xử lý lỗi thường gặp](#xử-lý-lỗi-thường-gặp)
- [Giới hạn hiện tại](#giới-hạn-hiện-tại)
- [Bảo mật và lưu ý an toàn](#bảo-mật-và-lưu-ý-an-toàn)

## Tổng quan

`mobile_runner.py` đóng vai trò tương tự Chrome Extension của bản web, nhưng dành cho ứng dụng Android native:

- **Web:** Extension đọc DOM của trang HTML.
- **Mobile:** Appium đọc cây giao diện Android dưới dạng XML.
- **Dùng chung:** Backend FastAPI, nguồn AI, quy trình sinh test case, sinh code và xuất báo cáo.

Công cụ phù hợp khi cần:

- Khảo sát nhanh một màn hình Android và tạo danh sách test case.
- Sinh bộ khung kiểm thử tự động bằng Appium.
- Kết hợp giao diện thực tế với tài liệu đặc tả `.md` hoặc `.txt`.
- Xuất báo cáo HTML để review hoặc chia sẻ trong nhóm QA.

## Tính năng chính

- Kết nối điện thoại Android thật hoặc Android Emulator qua Appium.
- Đọc và tóm tắt các phần tử có ý nghĩa trên màn hình:
  - Nút bấm.
  - Ô nhập liệu.
  - Nội dung văn bản.
  - Phần tử có thể tương tác.
  - `resource-id`, `content-desc` và `text`.
- Sinh test case bằng AI từ giao diện và tài liệu đặc tả.
- Sinh mã nguồn kiểm thử `pytest + Appium`.
- Xuất báo cáo HTML tự chứa, có thể mở trực tiếp bằng trình duyệt.
- Cho phép tùy chỉnh backend, Appium server, thiết bị và tên file đầu ra.

## Kiến trúc hệ thống

```text
┌──────────────────────┐
│ Ứng dụng Android     │
│ Thiết bị / Emulator  │
└──────────┬───────────┘
           │ UI hierarchy (XML)
           ▼
┌──────────────────────┐
│ Appium Server        │
│ UiAutomator2 Driver  │
└──────────┬───────────┘
           │
           ▼
┌────────────────────────────┐
│ mobile/mobile_runner.py    │
│ - Kết nối ứng dụng         │
│ - Tóm tắt cây giao diện    │
│ - Gọi API backend          │
└──────────┬─────────────────┘
           │ HTTP/JSON
           ▼
┌──────────────────────────────────────────┐
│ Backend AutoTest — FastAPI               │
│ /generate → sinh test case               │
│ /gen_code → sinh code Appium             │
│ /export_html → xuất báo cáo HTML         │
└──────────┬───────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────┐
│ JSON test case · Python test · HTML      │
└──────────────────────────────────────────┘
```

### Cấu trúc thư mục

```text
mobile/
├── README.md                   # Tài liệu hướng dẫn
├── mobile_runner.py            # Chương trình chính
└── requirements-mobile.txt     # Thư viện Python cho mobile testing
```

## Yêu cầu hệ thống

Trước khi cài đặt, máy cần có:

| Thành phần | Mục đích |
|---|---|
| Python 3 | Chạy backend, mobile runner và test được sinh |
| Node.js và npm | Cài đặt, khởi chạy Appium |
| Java Development Kit (JDK) | Phục vụ Android SDK và UiAutomator2 |
| Android SDK Platform Tools | Cung cấp lệnh `adb` |
| Appium 2 | Điều khiển ứng dụng Android |
| UiAutomator2 Driver | Driver Android cho Appium |
| Thiết bị Android hoặc Emulator | Môi trường chạy ứng dụng |
| Backend AutoTest | Sinh test case, code và báo cáo |

Kiểm tra nhanh các công cụ:

```bash
python --version
node --version
npm --version
java -version
adb version
```

> Trên một số hệ điều hành, lệnh Python có thể là `python3` thay vì `python`.

## Cài đặt

Các lệnh dưới đây được thực hiện từ thư mục gốc của repository.

### 1. Tải mã nguồn

```bash
git clone https://github.com/oanhkv/autoTest.git
cd autoTest
```

Nếu đã có mã nguồn, bỏ qua bước này.

### 2. Cài đặt và cấu hình backend

Tạo môi trường ảo:

```bash
cd backend
python -m venv .venv
```

Kích hoạt môi trường:

**Windows PowerShell**

```powershell
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

Cài thư viện và tạo file cấu hình:

```bash
pip install -r requirements.txt
```

**Windows**

```powershell
Copy-Item .env.example .env
```

**macOS / Linux**

```bash
cp .env.example .env
```

Mở `backend/.env`, chọn `PROVIDER` và cấu hình thông tin tương ứng:

- `gemini`: cần `GEMINI_API_KEY`.
- `ollama`: cần Ollama và model chạy trên máy.
- `anthropic`: cần `ANTHROPIC_API_KEY`.

Khởi chạy backend:

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Kiểm tra backend tại:

```text
http://127.0.0.1:8000/health
```

Kết quả hợp lệ:

```json
{"status":"ok"}
```

> Giữ cửa sổ terminal backend hoạt động trong suốt quá trình sử dụng mobile runner.

### 3. Cài thư viện Python cho mobile

Mở terminal mới và chuyển đến thư mục `mobile`:

```bash
cd mobile
```

Bạn có thể dùng lại môi trường ảo của backend hoặc tạo một môi trường riêng.

**Dùng môi trường backend trên Windows**

```powershell
..\backend\.venv\Scripts\Activate.ps1
pip install -r requirements-mobile.txt
```

**Dùng môi trường backend trên macOS / Linux**

```bash
source ../backend/.venv/bin/activate
pip install -r requirements-mobile.txt
```

> Nếu môi trường ảo được tạo ở vị trí khác, hãy thay đường dẫn kích hoạt cho phù hợp.

### 4. Cài Appium và UiAutomator2

```bash
npm install --global appium
appium driver install uiautomator2
```

Kiểm tra cài đặt:

```bash
appium --version
appium driver list --installed
```

Khởi chạy Appium server:

```bash
appium
```

Mặc định, mobile runner kết nối đến:

```text
http://127.0.0.1:4723
```

> Giữ cửa sổ terminal Appium hoạt động khi chạy công cụ.

### 5. Kết nối thiết bị Android

#### Điện thoại thật

1. Bật **Developer options**.
2. Bật **USB debugging**.
3. Kết nối điện thoại với máy tính bằng cáp USB.
4. Chấp nhận thông báo cấp quyền gỡ lỗi trên điện thoại.

#### Android Emulator

Khởi động emulator từ Android Studio trước khi chạy mobile runner.

Kiểm tra kết nối:

```bash
adb devices
```

Thiết bị phải xuất hiện với trạng thái `device`:

```text
List of devices attached
emulator-5554    device
```

Nếu trạng thái là `unauthorized`, hãy mở khóa điện thoại và cấp lại quyền USB debugging.

### 6. Xác định package và activity

Liệt kê package đã cài:

```bash
adb shell pm list packages
```

Lọc theo tên ứng dụng:

**Windows**

```powershell
adb shell pm list packages | Select-String "ten-ung-dung"
```

**macOS / Linux**

```bash
adb shell pm list packages | grep "ten-ung-dung"
```

Mở ứng dụng tới màn hình cần kiểm thử, sau đó xem activity hiện tại:

**Windows**

```powershell
adb shell dumpsys window | Select-String "mCurrentFocus|mFocusedApp"
```

**macOS / Linux**

```bash
adb shell dumpsys window | grep -E "mCurrentFocus|mFocusedApp"
```

Ví dụ kết quả:

```text
com.example.app/.MainActivity
```

Trong đó:

- App package: `com.example.app`
- App activity: `.MainActivity`

## Chạy kiểm thử

### Cách chạy cơ bản

1. Khởi chạy backend.
2. Khởi chạy Appium server.
3. Kết nối thiết bị hoặc mở emulator.
4. Mở ứng dụng tới đúng màn hình cần phân tích.
5. Chạy lệnh trong thư mục `mobile`.

```bash
python mobile_runner.py \
  --app-package com.example.app \
  --app-activity .MainActivity \
  --screen "Đăng nhập"
```

**Windows PowerShell**

```powershell
python mobile_runner.py `
  --app-package com.example.app `
  --app-activity .MainActivity `
  --screen "Đăng nhập"
```

### Chạy với tài liệu đặc tả

`--spec` hỗ trợ file văn bản `.md` hoặc `.txt`:

```bash
python mobile_runner.py \
  --app-package com.example.app \
  --app-activity .MainActivity \
  --screen "Đăng nhập" \
  --spec specs/login.md
```

### Chạy trực tiếp từ file APK

Nếu ứng dụng chưa được cài trên thiết bị:

```bash
python mobile_runner.py \
  --apk builds/app-debug.apk \
  --screen "Trang chủ"
```

### Chỉ sinh test case, không sinh code Appium

```bash
python mobile_runner.py \
  --app-package com.example.app \
  --app-activity .MainActivity \
  --screen "Đăng nhập" \
  --no-code
```

### Đặt tên riêng cho file kết quả

```bash
python mobile_runner.py \
  --app-package com.example.app \
  --app-activity .MainActivity \
  --screen "Đăng ký" \
  --out results/dang_ky
```

> Thư mục cha của giá trị `--out` phải tồn tại trước khi chạy.

### Dùng backend hoặc Appium server khác

```bash
python mobile_runner.py \
  --app-package com.example.app \
  --app-activity .MainActivity \
  --backend http://192.168.1.10:8000 \
  --appium http://192.168.1.10:4723
```

## Tham số dòng lệnh

| Tham số | Bắt buộc | Mặc định | Mô tả |
|---|---:|---|---|
| `--app-package` | Có điều kiện | Rỗng | Package của ứng dụng đã cài, ví dụ `com.example.app` |
| `--app-activity` | Không | Rỗng | Activity khởi động, ví dụ `.MainActivity` |
| `--apk` | Có điều kiện | Rỗng | Đường dẫn APK nếu ứng dụng chưa được cài |
| `--device` | Không | `Android` | Tên thiết bị hoặc emulator gửi cho Appium |
| `--appium` | Không | `http://127.0.0.1:4723` | URL Appium server |
| `--backend` | Không | `http://127.0.0.1:8000` | URL backend AutoTest |
| `--screen` | Không | Rỗng | Tên màn hình gắn vào test case và báo cáo |
| `--spec` | Không | Rỗng | Đường dẫn file đặc tả `.md` hoặc `.txt` |
| `--no-code` | Không | `false` | Bỏ qua bước sinh mã kiểm thử Appium |
| `--out` | Không | `ketqua_mobile` | Tiền tố hoặc đường dẫn file kết quả |

Điều kiện đầu vào:

- Dùng `--app-package` khi ứng dụng đã được cài.
- Dùng `--apk` khi muốn Appium cài ứng dụng từ file APK.
- Có thể truyền đồng thời package, activity và APK nếu cấu hình ứng dụng yêu cầu.

Xem trợ giúp trực tiếp:

```bash
python mobile_runner.py --help
```

## Kết quả đầu ra

Với cấu hình mặc định `--out ketqua_mobile`, công cụ tạo:

| File | Nội dung |
|---|---|
| `ketqua_mobile_testcases.json` | Danh sách test case do AI sinh |
| `ketqua_mobile_test_appium.py` | Mã kiểm thử `pytest + Appium`; không tạo khi dùng `--no-code` |
| `ketqua_mobile_baocao.html` | Báo cáo HTML của lần chạy hiện tại |

Chạy file kiểm thử được sinh:

```bash
pytest ketqua_mobile_test_appium.py -v
```

> Mã kiểm thử được AI tạo dựa trên cây giao diện tại thời điểm quét. Hãy review locator, dữ liệu đầu vào và assertion trước khi chạy trên môi trường có dữ liệu thật.

### Quét nhiều màn hình

Mobile runner chỉ đọc **màn hình đang hiển thị tại thời điểm chạy**. Để phân tích nhiều màn hình:

1. Điều hướng ứng dụng tới màn hình cần quét.
2. Chạy lại công cụ với `--screen` và `--out` khác nhau.

Ví dụ:

```bash
python mobile_runner.py \
  --app-package com.example.app \
  --app-activity .MainActivity \
  --screen "Đăng nhập" \
  --out results/dang_nhap

python mobile_runner.py \
  --app-package com.example.app \
  --app-activity .MainActivity \
  --screen "Trang chủ" \
  --out results/trang_chu
```

Việc dùng `--out` khác nhau giúp tránh ghi đè kết quả của lần chạy trước.

## Cơ chế hoạt động

| Bước | Web | Android native |
|---|---|---|
| Đọc giao diện | Extension đọc DOM | Appium đọc `driver.page_source` |
| Chuẩn hóa dữ liệu | Tóm tắt DOM | `summarize_ui()` tóm tắt XML |
| Sinh test case | `POST /generate` | `POST /generate` |
| Sinh code | `/gen_code`, platform `web` | `/gen_code`, platform `android` |
| Công nghệ chạy test | Playwright | Appium + UiAutomator2 |
| Xuất báo cáo | `POST /export_html` | `POST /export_html` |

Luồng xử lý của mobile runner:

1. Tạo Appium session với thiết bị Android.
2. Mở hoặc kết nối vào ứng dụng.
3. Đọc XML của màn hình hiện tại.
4. Giữ lại tối đa 80 phần tử có ý nghĩa.
5. Đóng Appium session dùng để khảo sát giao diện.
6. Gửi bản tóm tắt UI và đặc tả tới backend.
7. Lưu test case JSON.
8. Sinh file test Appium nếu không dùng `--no-code`.
9. Xuất báo cáo HTML.

## Xử lý lỗi thường gặp

### `Không gọi được backend`

Nguyên nhân thường gặp:

- Backend chưa chạy.
- Sai URL hoặc cổng `--backend`.
- Firewall chặn kết nối.

Kiểm tra:

```bash
curl http://127.0.0.1:8000/health
```

### Không kết nối được Appium

Kiểm tra server và driver:

```bash
appium
appium driver list --installed
```

Đảm bảo `uiautomator2` đã được cài và URL `--appium` đúng.

### `adb devices` không hiển thị thiết bị

- Kiểm tra cáp USB.
- Bật lại USB debugging.
- Chấp nhận quyền gỡ lỗi trên điện thoại.
- Khởi động lại ADB:

```bash
adb kill-server
adb start-server
adb devices
```

### Thiết bị ở trạng thái `unauthorized`

1. Rút và cắm lại cáp USB.
2. Chọn **Revoke USB debugging authorizations** trong Developer options.
3. Kết nối lại và chấp nhận hộp thoại cấp quyền.

### Sai package hoặc activity

Các biểu hiện thường gặp:

- Appium không mở được ứng dụng.
- Lỗi `Activity ... does not exist`.
- Appium session kết thúc ngay sau khi tạo.

Hãy mở ứng dụng thủ công và dùng `adb shell dumpsys window` để lấy lại package/activity hiện tại.

### Backend không sinh được test case

Kiểm tra:

- `PROVIDER` trong `backend/.env`.
- API key tương ứng với provider.
- Ollama server và model nếu dùng local AI.
- Log tại terminal backend.

### File đặc tả không đọc được

- Kiểm tra đường dẫn truyền vào `--spec`.
- Mobile runner hiện đọc trực tiếp file văn bản UTF-8.
- Với `.docx`, `.pdf` hoặc `.xlsx`, hãy chuyển nội dung cần thiết sang `.md` hoặc `.txt` trước khi dùng.

## Giới hạn hiện tại

- Chỉ hỗ trợ Android native qua UiAutomator2; chưa có adapter iOS.
- Mỗi lần chạy chỉ khảo sát một màn hình đang hiển thị.
- Chỉ tối đa 80 phần tử UI có ý nghĩa được đưa vào bản tóm tắt.
- Không tự điều hướng qua toàn bộ ứng dụng để thu thập nhiều màn hình.
- Báo cáo HTML được tạo riêng cho từng lần chạy, không tự gộp các lần chạy trước.
- Chất lượng test case và code phụ thuộc vào:
  - Chất lượng cây accessibility của ứng dụng.
  - `resource-id`, `content-desc` và nội dung hiển thị.
  - Mức độ đầy đủ của tài liệu đặc tả.
  - Model AI đang được cấu hình.

Để có kết quả tốt hơn, đội phát triển nên:

- Gán `resource-id` ổn định cho phần tử tương tác.
- Cung cấp `content-desc` phù hợp cho accessibility.
- Tránh locator phụ thuộc hoàn toàn vào vị trí hoặc XPath dài.
- Viết rõ business rule, dữ liệu hợp lệ và dữ liệu không hợp lệ trong file đặc tả.

## Bảo mật và lưu ý an toàn

- Không commit `backend/.env`, API key, token hoặc thông tin đăng nhập thật.
- Không đưa mật khẩu, dữ liệu cá nhân hoặc dữ liệu sản xuất vào file đặc tả.
- Review test được sinh trước khi chạy vì một số thao tác có thể tạo, sửa hoặc xóa dữ liệu.
- Ưu tiên chạy trên môi trường test, tài khoản test và thiết bị không chứa dữ liệu nhạy cảm.
- Chỉ mở Appium và backend ra mạng nội bộ khi thật sự cần thiết.

## Tài liệu liên quan

- [README chính của AutoTest](../README.md)
- [Hướng dẫn API Testing](../API_TESTING.md)
- [Cấu hình backend mẫu](../backend/.env.example)

## Đóng góp

Khi đóng góp cho module mobile:

1. Tạo branch mới từ branch chính.
2. Thực hiện thay đổi với phạm vi rõ ràng.
3. Kiểm tra cú pháp:

   ```bash
   python -m py_compile mobile_runner.py
   ```

4. Chạy thử với thiết bị hoặc emulator.
5. Không đưa file kết quả, API key hoặc dữ liệu nhạy cảm vào commit.
6. Tạo Pull Request và mô tả rõ thay đổi, cách kiểm tra cùng kết quả mong đợi.

## Giấy phép

Repository hiện chưa khai báo file giấy phép. Vui lòng liên hệ chủ sở hữu dự án trước khi sao chép, phân phối hoặc sử dụng mã nguồn ngoài phạm vi được cho phép.
