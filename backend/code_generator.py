"""Sinh TÀI LIỆU .md và CODE TỰ ĐỘNG HÓA (Playwright/pytest) bằng AI.

Đây là trường phái "codegen": thay vì chạy test bằng plan JSON nội bộ, ta sinh ra
FILE CODE chạy được bằng pytest + Playwright — tái sử dụng, cắm được vào CI/CD.

Hai mắt xích:
1. dom_to_markdown(): DOM trang (+ spec nếu có) -> tài liệu đặc tả Markdown sạch.
2. generate_playwright_code(): spec/DOM + test case -> file Python pytest+Playwright chạy được.

Dùng lại lớp Provider trong ai_generator (chọn nguồn AI qua .env: ollama/gemini/anthropic).
"""
import re

from ai_generator import Provider


def _extract_block(text: str, langs=("python", "py", "markdown", "md")) -> str:
    """Lấy nội dung trong khối ```...``` nếu AI bọc; nếu không thì trả nguyên văn."""
    if not text:
        return ""
    m = re.search(r"```(?:[a-zA-Z]+)?\s*\n(.*?)```", text, re.S)
    if m:
        return m.group(1).strip()
    # Phòng khi AI chỉ mở ``` mà không đóng
    t = re.sub(r"^```[a-zA-Z]*\s*\n?", "", text.strip())
    t = re.sub(r"\n?```$", "", t)
    return t.strip()


def _context(url: str, dom_summary: str, spec: str, max_dom: int = 0) -> str:
    if max_dom and len(dom_summary) > max_dom:
        dom_summary = dom_summary[:max_dom] + "\n...(rút gọn)"
    spec_block = spec.strip() or "(Không có tài liệu — hãy suy luận từ DOM)"
    return (f"URL: {url}\n\n=== CẤU TRÚC GIAO DIỆN (DOM) ===\n{dom_summary}\n\n"
            f"=== TÀI LIỆU ĐẶC TẢ (nếu có) ===\n{spec_block}")


# ===================== 1) DOM -> Markdown =====================
MD_SYSTEM = (
    "Bạn là Business Analyst kiêm QA. Hãy ĐỌC cấu trúc giao diện (DOM) của một màn hình web "
    "và viết TÀI LIỆU ĐẶC TẢ bằng MARKDOWN tiếng Việt, rõ ràng, để lập trình viên và tester dùng chung.\n"
    "Bố cục tài liệu BẮT BUỘC theo các mục sau (dùng tiêu đề ##):\n"
    "## 1. Mục đích màn hình — màn hình này để làm gì (suy từ tiêu đề, nút, ô nhập).\n"
    "## 2. Thành phần giao diện — bảng Markdown các phần tử: | Thành phần | Loại | Bắt buộc | Ghi chú |.\n"
    "## 3. Luồng người dùng chính — đánh số các bước thao tác bình thường (happy path).\n"
    "## 4. Quy tắc kiểm tra dữ liệu (validation) — trường bắt buộc, định dạng, độ dài, giá trị biên.\n"
    "## 5. Tiêu chí chấp nhận (Acceptance Criteria) — dạng 'Given/When/Then' hoặc gạch đầu dòng, ĐO ĐƯỢC.\n"
    "Viết NGẮN GỌN, đúng trọng tâm, không bịa thành phần không có trong DOM. CHỈ trả về Markdown, không lời dẫn."
)


def dom_to_markdown(url: str, dom_summary: str, spec: str = "") -> str:
    """Sinh tài liệu đặc tả Markdown từ DOM trang web (+ spec sẵn có nếu muốn bổ sung)."""
    provider = Provider()
    ctx = _context(url, dom_summary, spec, max_dom=2000 if provider.compact else 0)
    raw = provider.complete(MD_SYSTEM, ctx, max_tokens=2500 if provider.compact else 4000,
                            json_mode=False)
    md = _extract_block(raw)
    if not md:
        raise ValueError("AI không sinh được tài liệu .md (kiểm tra model/PROVIDER).")
    return md


# ===================== 2) spec/DOM + cases -> code Playwright =====================
CODE_SYSTEM = (
    "Bạn là kỹ sư Automation Test. Hãy sinh MỘT FILE PYTHON hoàn chỉnh dùng **pytest + Playwright** "
    "để kiểm thử tự động màn hình web được mô tả. YÊU CẦU:\n"
    "- Dùng `playwright.sync_api` và fixture `page` của `pytest-playwright`.\n"
    "- MỖI test case là MỘT hàm `def test_...(page):` đặt tên gợi nhớ, có docstring nêu MÃ TC + mục tiêu.\n"
    "- Định vị phần tử bằng API BỀN VỮNG (ưu tiên theo thứ tự): `page.get_by_label`, `page.get_by_role`, "
    "`page.get_by_placeholder`, `page.get_by_text`. HẠN CHẾ CSS/XPath cứng.\n"
    "- Có `page.goto(BASE_URL)` ở đầu mỗi test (đặt hằng BASE_URL ở đầu file = URL đã cho).\n"
    "- Dùng `expect(...)` để khẳng định kết quả (expect(locator).to_be_visible(), to_have_text()...).\n"
    "- Với case ĐĂNG NHẬP/THÊM/XÓA/SỬA (đổi dữ liệu thật): vẫn viết code nhưng THÊM `@pytest.mark.skip"
    "(reason=\"Thao tác đổi dữ liệu — bật khi chạy trên môi trường test\")` để an toàn.\n"
    "- Case kiểm API/responsive/đa trình duyệt mà Playwright khó làm: viết khung + `pytest.skip(...)` kèm lý do.\n"
    "- Thêm comment tiếng Việt ngắn ở mỗi bước. Đầu file ghi hướng dẫn cài & chạy trong docstring module.\n"
    "CHỈ trả về CODE PYTHON (không giải thích, không markdown ngoài code)."
)


def _cases_brief(test_cases: list[dict], limit: int = 24) -> str:
    lines = []
    for c in test_cases[:limit]:
        lines.append(
            f'- [{c.get("id","")}] ({c.get("ui_function","")}) {c.get("function","")}'
            f' | màn: {c.get("screen","")}'
            f' | bước: {str(c.get("steps","")).replace(chr(10), " ")[:180]}'
            f' | mong đợi: {str(c.get("expected","")).replace(chr(10), " ")[:140]}'
        )
    extra = len(test_cases) - limit
    if extra > 0:
        lines.append(f"... (còn {extra} case nữa, sinh code cho các case tiêu biểu/khả thi)")
    return "\n".join(lines)


def generate_playwright_code(url: str, dom_summary: str, spec: str,
                             test_cases: list[dict]) -> str:
    """Sinh file pytest+Playwright từ DOM + spec + danh sách test case (nền tảng WEB)."""
    if not test_cases:
        raise ValueError("Chưa có test case để sinh code.")
    provider = Provider()
    ctx = (_context(url, dom_summary, spec, max_dom=1500 if provider.compact else 3500)
           + "\n\n=== DANH SÁCH TEST CASE CẦN TỰ ĐỘNG HÓA ===\n"
           + _cases_brief(test_cases))
    raw = provider.complete(CODE_SYSTEM, ctx, max_tokens=3500 if provider.compact else 9000,
                            json_mode=False)
    code = _extract_block(raw)
    if "def test" not in code:
        raise ValueError("AI chưa sinh được code hợp lệ (không thấy hàm test). Thử lại hoặc đổi model mạnh hơn.")
    # Bảo đảm có dòng import tối thiểu nếu model quên
    if "import" not in code.split("\n", 1)[0] and "import pytest" not in code:
        code = ("import pytest\nfrom playwright.sync_api import expect\n\n" + code)
    return code


# ===================== 3) Mobile native: spec/UI XML + cases -> code Appium =====================
APPIUM_SYSTEM = (
    "Bạn là kỹ sư Automation Test MOBILE. Hãy sinh MỘT FILE PYTHON hoàn chỉnh dùng "
    "**pytest + Appium (appium-python-client) + UiAutomator2** để kiểm thử tự động app ANDROID native. YÊU CẦU:\n"
    "- Tạo fixture `driver` (scope='function') khởi tạo `webdriver.Remote('http://127.0.0.1:4723', options=UiAutomator2Options()...)` "
    "và `driver.quit()` ở teardown. Đọc `APP_PACKAGE`, `APP_ACTIVITY` từ hằng đầu file (điền từ thông tin app đã cho).\n"
    "- MỖI test case là MỘT hàm `def test_...(driver):` có docstring nêu MÃ TC + mục tiêu.\n"
    "- Định vị phần tử bằng API BỀN VỮNG (ưu tiên theo thứ tự): `AppiumBy.ACCESSIBILITY_ID` (content-desc), "
    "`AppiumBy.ID` (resource-id), `AppiumBy.ANDROID_UIAUTOMATOR` (text/desc), rồi mới `AppiumBy.XPATH`. "
    "Dùng `WebDriverWait(driver, 10).until(EC.presence_of_element_located(...))` để chờ phần tử.\n"
    "- Khẳng định kết quả bằng `assert el.is_displayed()` / so text `el.text`.\n"
    "- Với case ĐĂNG NHẬP/THÊM/XÓA/SỬA (đổi dữ liệu thật): vẫn viết nhưng THÊM `@pytest.mark.skip"
    "(reason=\"Thao tác đổi dữ liệu — bật khi chạy trên môi trường test\")`.\n"
    "- Case kiểm hiệu năng/đa thiết bị khó tự động: viết khung + `pytest.skip(...)` kèm lý do.\n"
    "- Đầu file ghi docstring hướng dẫn cài & chạy (Appium server, emulator/thiết bị, lệnh pytest). "
    "Thêm comment tiếng Việt ngắn mỗi bước.\n"
    "CHỈ trả về CODE PYTHON (không giải thích, không markdown ngoài code)."
)


def _mobile_context(app_info: str, ui_summary: str, spec: str) -> str:
    spec_block = spec.strip() or "(Không có tài liệu — suy luận từ cây giao diện)"
    ui = ui_summary.strip() or "(Chưa có cây giao diện — suy luận từ test case & spec)"
    return (f"=== THÔNG TIN APP ===\n{app_info or '(chưa rõ package/activity — để placeholder)'}\n\n"
            f"=== CÂY GIAO DIỆN APP (Appium page source / mô tả màn) ===\n{ui[:3500]}\n\n"
            f"=== TÀI LIỆU ĐẶC TẢ (nếu có) ===\n{spec_block}")


def generate_appium_code(app_info: str, ui_summary: str, spec: str,
                         test_cases: list[dict]) -> str:
    """Sinh file pytest+Appium từ cây giao diện app + spec + test case (nền tảng ANDROID native).

    DÙNG LẠI lõi AI và danh sách test case y như web — chỉ đổi 'đích sinh code' sang Appium.
    """
    if not test_cases:
        raise ValueError("Chưa có test case để sinh code.")
    provider = Provider()
    ctx = (_mobile_context(app_info, ui_summary, spec)
           + "\n\n=== DANH SÁCH TEST CASE CẦN TỰ ĐỘNG HÓA ===\n"
           + _cases_brief(test_cases))
    raw = provider.complete(APPIUM_SYSTEM, ctx, max_tokens=3500 if provider.compact else 9000,
                            json_mode=False)
    code = _extract_block(raw)
    if "def test" not in code:
        raise ValueError("AI chưa sinh được code Appium hợp lệ (không thấy hàm test). Thử lại hoặc đổi model mạnh hơn.")
    return code


# ===================== Bộ điều phối đa nền tảng =====================
def generate_code(platform: str, url: str = "", ui_summary: str = "", spec: str = "",
                  test_cases: list[dict] = None, app_info: str = "") -> str:
    """Điểm vào DUY NHẤT cho sinh code — chọn đích theo nền tảng người dùng chọn.

    platform = "web"     -> Playwright (dùng ui_summary là DOM)
    platform = "android" -> Appium     (dùng ui_summary là cây giao diện app)
    """
    test_cases = test_cases or []
    p = (platform or "web").strip().lower()
    if p in ("android", "mobile", "ios", "appium"):
        return generate_appium_code(app_info, ui_summary, spec, test_cases)
    return generate_playwright_code(url, ui_summary, spec, test_cases)
