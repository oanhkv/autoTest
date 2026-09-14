# AutoTest — Nhánh MOBILE (Android native)

Phần này cho **app native** (APK / cài từ CH Play). Nó **dùng chung backend AI** với bản web —
chỉ khác cách lấy giao diện: web đọc DOM, mobile đọc cây giao diện app qua **Appium**.

```
            DÙNG CHUNG (không viết lại)
        ┌───────────────────────────────────┐
Web   → │  Backend AI  →  sinh test case     │ → Excel / HTML / Code
Mobile→ │  (/generate, /gen_code, /export*)  │ → (web: Playwright | mobile: Appium)
        └───────────────────────────────────┘
   ↑ extension (DOM)        ↑ mobile_runner.py (Appium XML)
```

## 1. Cài đặt môi trường (lần đầu)

```powershell
# a) Backend (bản web) phải chạy — mở 1 cửa sổ riêng:
cd ..\backend
.\.venv\Scripts\Activate.ps1
uvicorn main:app --port 8000

# b) Phụ thuộc Python cho mobile:
pip install -r requirements-mobile.txt

# c) Appium server (cần Node.js):
npm install -g appium
appium driver install uiautomator2
appium                       # chạy server ở cổng 4723 (giữ cửa sổ này)

# d) Thiết bị Android:
#  - Điện thoại thật: bật "USB debugging" rồi cắm cáp (KHUYẾN NGHỊ — máy CPU-only nhẹ hơn emulator)
#  - Hoặc mở Android Emulator
adb devices                  # phải thấy thiết bị ở trạng thái "device"
```

## 2. Chạy

Mở app tới màn hình cần test (trên điện thoại), rồi:

```powershell
python mobile_runner.py `
  --app-package com.vidu.app `
  --app-activity .MainActivity `
  --screen "Đăng nhập" `
  --spec spec.md            # tùy chọn
```

Kết quả nhận được (cùng định dạng với bản web):
- `ketqua_mobile_testcases.json` — bộ test case AI sinh.
- `ketqua_mobile_test_appium.py` — **code Appium chạy được** (`pytest ketqua_mobile_test_appium.py -v`).
- `ketqua_mobile_baocao.html` — báo cáo HTML mở bằng trình duyệt.

Tham số hữu ích: `--apk duong_dan.apk` (app chưa cài), `--no-code` (chỉ sinh case), `--device <tên>`.

## 3. Cơ chế (để hiểu)

| Bước | Web (extension) | Mobile (script này) |
|---|---|---|
| Lấy giao diện | `content.js` đọc DOM | Appium `driver.page_source` (XML) |
| Chuẩn hóa | tóm tắt DOM | `summarize_ui()` tóm tắt XML |
| Sinh case | `POST /generate` | **giống hệt** `POST /generate` |
| Sinh code | `/gen_code` platform=web → Playwright | `/gen_code` platform=android → Appium |
| Báo cáo | `/export_html` | **giống hệt** `/export_html` |

→ Chỉ 2 ô đầu (lấy + chuẩn hóa giao diện) là khác nền tảng; phần lõi AI **tái dùng 100%**.

> Lưu ý: `mobile_runner.py` lấy giao diện MỘT màn đang mở. Muốn test nhiều màn, điều hướng app tới
> từng màn rồi chạy lại với `--screen` khác nhau — báo cáo sẽ gom theo màn hình.
