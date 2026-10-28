"""AutoTest — Bộ chạy MOBILE (Android native) qua Appium.

Đây là "adapter mobile": đóng VAI TRÒ như Chrome extension nhưng cho app native.
Nó dùng CHUNG backend AI với bản web — chỉ khác cách LẤY giao diện:
- Web:    extension đọc DOM (HTML)
- Mobile: script này đọc cây giao diện app qua Appium (XML page source)

Luồng:
  Appium kết nối app  →  dump cây giao diện (XML)  →  tóm tắt thành "UI summary"
  →  gửi backend /generate  →  nhận test case  →  (tùy chọn) /gen_code platform=android
  →  lưu: test case (.json), code Appium (.py), báo cáo (.html)

CÀI ĐẶT (xem thêm README ở thư mục này):
  pip install -r requirements-mobile.txt
  npm install -g appium && appium driver install uiautomator2
  appium                         # chạy Appium server (cổng 4723)
  # Cắm điện thoại (bật USB debugging) hoặc mở emulator; kiểm: adb devices

CHẠY:
  python mobile_runner.py --app-package com.vd.app --app-activity .MainActivity \
         --screen "Đăng nhập" --spec spec.md --backend http://127.0.0.1:8000

Backend (bản web) PHẢI đang chạy: uvicorn main:app --port 8000
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET


# ===================== Gọi backend (dùng chung với bản web) =====================
def _post(backend: str, path: str, payload: dict, timeout: int = 600) -> dict:
    req = urllib.request.Request(
        backend.rstrip("/") + path,
        data=json.dumps(payload).encode("utf-8"),
        # Token khớp AUTOTEST_TOKEN của backend (nếu backend bật xác thực)
        headers={"Content-Type": "application/json",
                 **({"X-AutoTest-Token": os.environ["AUTOTEST_TOKEN"]} if os.environ.get("AUTOTEST_TOKEN") else {})},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise SystemExit(f"[Lỗi backend {exc.code}] {detail[:400]}")
    except urllib.error.URLError as exc:
        raise SystemExit(f"[Không gọi được backend] {exc} — backend đã chạy ở {backend} chưa?")


# ===================== Tóm tắt cây giao diện app (vai trò như content.js) =====================
def summarize_ui(xml_source: str, max_nodes: int = 80) -> str:
    """Biến XML page source của Appium thành bản tóm tắt dễ đọc cho AI.

    Giống content.js bên web: chỉ trích phần tử tương tác (nút, ô nhập, text...) kèm
    thuộc tính định vị bền (resource-id, content-desc, text)."""
    try:
        root = ET.fromstring(xml_source)
    except ET.ParseError as exc:
        return f"(Không phân tích được XML giao diện: {exc})"

    lines, count = [], 0
    for el in root.iter():
        if count >= max_nodes:
            break
        a = el.attrib
        cls = (a.get("class") or el.tag or "").split(".")[-1]
        text = (a.get("text") or "").strip()
        desc = (a.get("content-desc") or "").strip()
        rid = (a.get("resource-id") or "").split("/")[-1]
        clickable = a.get("clickable") == "true"
        editable = "EditText" in cls or a.get("password") == "true"
        # Chỉ giữ phần tử có ý nghĩa (có chữ/định danh hoặc bấm/nhập được)
        if not (text or desc or rid or clickable or editable):
            continue
        kind = ("[ô nhập]" if editable else "[nút]" if clickable and cls.endswith("Button")
                else "[bấm được]" if clickable else "[text]")
        label = text or desc or rid or cls
        extra = []
        if rid:
            extra.append(f"id={rid}")
        if desc and desc != label:
            extra.append(f"desc={desc}")
        suffix = (" (" + ", ".join(extra) + ")") if extra else ""
        lines.append(f"{kind} {label}{suffix}")
        count += 1
    return "Cây giao diện app (Android):\n" + "\n".join(f"  {ln}" for ln in lines)


# ===================== Kết nối Appium =====================
def connect_appium(server: str, app_package: str, app_activity: str,
                   apk: str = "", device: str = "Android"):
    """Mở phiên Appium tới app đang cài (theo package/activity) hoặc cài từ .apk."""
    try:
        from appium import webdriver
        from appium.options.android import UiAutomator2Options
    except ImportError:
        raise SystemExit(
            "Thiếu thư viện Appium. Cài: pip install -r requirements-mobile.txt"
        )
    opts = UiAutomator2Options()
    opts.platform_name = "Android"
    opts.device_name = device
    opts.automation_name = "UiAutomator2"
    if apk:
        opts.app = apk
    if app_package:
        opts.app_package = app_package
    if app_activity:
        opts.app_activity = app_activity
    opts.no_reset = True
    print(f"[1/5] Kết nối Appium {server} → {app_package or apk} ...")
    return webdriver.Remote(server, options=opts)


# ===================== Luồng chính =====================
def main():
    ap = argparse.ArgumentParser(description="AutoTest mobile runner (Appium + backend AI dùng chung)")
    ap.add_argument("--app-package", default="", help="package app, vd com.vd.app")
    ap.add_argument("--app-activity", default="", help="activity khởi động, vd .MainActivity")
    ap.add_argument("--apk", default="", help="đường dẫn file .apk (nếu app chưa cài)")
    ap.add_argument("--device", default="Android", help="tên thiết bị/emulator")
    ap.add_argument("--appium", default="http://127.0.0.1:4723", help="Appium server")
    ap.add_argument("--backend", default="http://127.0.0.1:8000", help="backend AutoTest (bản web)")
    ap.add_argument("--screen", default="", help="tên màn hình (gom đúng sheet/báo cáo)")
    ap.add_argument("--spec", default="", help="file tài liệu đặc tả (.md/.txt) tùy chọn")
    ap.add_argument("--no-code", action="store_true", help="bỏ qua bước sinh code Appium")
    ap.add_argument("--out", default="ketqua_mobile", help="tiền tố tên file kết quả")
    args = ap.parse_args()

    spec = ""
    if args.spec:
        with open(args.spec, encoding="utf-8") as f:
            spec = f.read()

    driver = connect_appium(args.appium, args.app_package, args.app_activity, args.apk, args.device)
    try:
        print("[2/5] Đọc cây giao diện màn hình hiện tại ...")
        ui_summary = summarize_ui(driver.page_source)
    finally:
        driver.quit()

    app_info = f"APP_PACKAGE={args.app_package or '(từ apk)'}, APP_ACTIVITY={args.app_activity or '(mặc định)'}"

    print("[3/5] Gửi backend sinh test case (dùng chung lõi AI với web) ...")
    gen = _post(args.backend, "/generate", {
        "url": app_info, "dom_summary": ui_summary, "spec": spec, "thorough": True,
    })
    cases = gen.get("test_cases", [])
    if args.screen:
        for c in cases:
            c["screen"] = args.screen
    print(f"      → Nhận {len(cases)} test case.")
    if not cases:
        raise SystemExit("Backend không sinh được test case (kiểm tra model/PROVIDER trong .env backend).")

    cases_file = f"{args.out}_testcases.json"
    with open(cases_file, "w", encoding="utf-8") as f:
        json.dump(cases, f, ensure_ascii=False, indent=2)
    print(f"      → Lưu {cases_file}")

    if not args.no_code:
        print("[4/5] Sinh code Appium (pytest) từ test case ...")
        code_res = _post(args.backend, "/gen_code", {
            "url": app_info, "dom_summary": ui_summary, "spec": spec,
            "test_cases": cases, "platform": "android", "app_info": app_info,
        })
        code_file = f"{args.out}_test_appium.py"
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(code_res.get("code", ""))
        print(f"      → Lưu {code_file} ({code_res.get('lines')} dòng). Chạy: pytest {code_file} -v")

    print("[5/5] Xuất báo cáo HTML (dùng chung endpoint với web) ...")
    # /export_html trả về HTML bytes (không phải JSON) -> lưu nhị phân riêng:
    _save_html(args.backend, app_info, cases, args.screen or args.app_package, f"{args.out}_baocao.html")
    print("\n✓ XONG. Mở file *_baocao.html để xem, hoặc chạy file *_test_appium.py bằng pytest.")


def _save_html(backend: str, url: str, cases: list, screen: str, out: str):
    payload = {"url": url, "test_cases": cases, "title": f"Báo cáo kiểm thử Mobile — {screen}"}
    req = urllib.request.Request(
        backend.rstrip("/") + "/export_html",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            with open(out, "wb") as f:
                f.write(resp.read())
        print(f"      → Lưu {out}")
    except Exception as exc:  # noqa: BLE001
        print(f"      (Bỏ qua báo cáo HTML: {exc})")


if __name__ == "__main__":
    sys.exit(main())
