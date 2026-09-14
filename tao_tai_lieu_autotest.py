# -*- coding: utf-8 -*-
"""
Sinh 3 file Excel tài liệu học tập chi tiết:
1. TaiLieu_AutomationTesting.xlsx   - Học automation testing từ con số 0 -> nâng cao
2. TaiLieu_ISTQB_Foundation.xlsx    - Ôn thi chứng chỉ ISTQB Foundation Level (CTFL)
3. TaiLieu_CauHoiPhongVan_AutoTest.xlsx - Bộ câu hỏi phỏng vấn Automation Test

Chạy: python tao_tai_lieu_autotest.py
"""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ------------------------- STYLE HELPERS -------------------------
TITLE_FILL   = PatternFill("solid", fgColor="1F4E78")   # xanh đậm
HEADER_FILL  = PatternFill("solid", fgColor="2E75B6")   # xanh
SUB_FILL     = PatternFill("solid", fgColor="DDEBF7")   # xanh nhạt
ALT_FILL     = PatternFill("solid", fgColor="F2F7FC")   # zebra
PHASE_FILL   = PatternFill("solid", fgColor="C6E0B4")   # xanh lá nhạt cho giai đoạn

TITLE_FONT   = Font(name="Calibri", size=16, bold=True, color="FFFFFF")
HEADER_FONT  = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
NORMAL_FONT  = Font(name="Calibri", size=11, color="000000")
BOLD_FONT    = Font(name="Calibri", size=11, bold=True, color="1F4E78")

THIN = Side(style="thin", color="BBBBBB")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

WRAP_TOP = Alignment(wrap_text=True, vertical="top")
CENTER   = Alignment(horizontal="center", vertical="center", wrap_text=True)


def style_title(ws, text, ncols):
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ncols)
    c = ws.cell(row=1, column=1, value=text)
    c.fill = TITLE_FILL
    c.font = TITLE_FONT
    c.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30


def style_header(ws, headers, row=2):
    for j, h in enumerate(headers, start=1):
        c = ws.cell(row=row, column=j, value=h)
        c.fill = HEADER_FILL
        c.font = HEADER_FONT
        c.alignment = CENTER
        c.border = BORDER
    ws.row_dimensions[row].height = 26


def fill_rows(ws, rows, start_row=3, zebra=True, phase_col=None):
    r = start_row
    for row in rows:
        is_phase = phase_col is not None and len(row) == 1
        for j, val in enumerate(row, start=1):
            c = ws.cell(row=r, column=j, value=val)
            c.font = NORMAL_FONT
            c.alignment = WRAP_TOP
            c.border = BORDER
            if is_phase:
                c.fill = PHASE_FILL
                c.font = Font(name="Calibri", size=11, bold=True, color="1F4E78")
            elif zebra and (r % 2 == 0):
                c.fill = ALT_FILL
        if is_phase and phase_col:
            ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=phase_col)
        r += 1
    return r


def set_widths(ws, widths):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w


def freeze(ws, cell="A3"):
    ws.freeze_panes = cell


def make_sheet(wb, name, title, headers, rows, widths, first=False, phase_merge=False):
    ws = wb.active if first else wb.create_sheet()
    ws.title = name[:31]
    style_title(ws, title, len(headers))
    style_header(ws, headers)
    fill_rows(ws, rows, start_row=3, phase_col=(len(headers) if phase_merge else None))
    set_widths(ws, widths)
    freeze(ws, "A3")
    return ws


# =====================================================================
# ============ FILE 1: AUTOMATION TESTING =============================
# =====================================================================
def build_automation():
    wb = Workbook()

    # ---------- Sheet 0: Giới thiệu & cách dùng ----------
    intro_rows = [
        ["1. Mục tiêu", "Tài liệu giúp người MỚI HOÀN TOÀN (chưa biết gì) học Automation Testing bài bản từ nền tảng tới nâng cao: Web, Mobile, API, CI/CD."],
        ["2. Đối tượng", "Người muốn chuyển sang nghề QA/Automation Tester; sinh viên CNTT; manual tester muốn lên automation."],
        ["3. Thời lượng đề xuất", "16–24 tuần (mỗi ngày 1–2 giờ). Có thể nhanh hơn nếu học full-time."],
        ["4. Thứ tự đọc các sheet", "Lo_Trinh_Hoc -> Nen_Tang_Coding -> Khai_Niem -> Tools_Frameworks -> Web/API/Mobile -> CI_CD -> Design_Pattern -> Bai_Tap -> Cau_Hoi_On_Tap -> Tai_Nguyen"],
        ["5. Nguyên tắc học", "Học tới đâu CODE tới đó. 70% thời gian phải gõ tay, không chỉ đọc. Mỗi khái niệm phải tự viết được 1 ví dụ."],
        ["6. Công cụ tối thiểu", "Máy tính, trình duyệt Chrome, VS Code, Git, Java hoặc Python (chọn 1 ngôn ngữ chính)."],
        ["7. Ngôn ngữ nên chọn", "Người mới: Python (dễ) hoặc Java (nhiều job ở VN). JavaScript nếu thích Playwright/Cypress."],
        ["8. Cách đánh giá tiến độ", "Cuối mỗi giai đoạn làm 1 mini-project; tự trả lời sheet Cau_Hoi_On_Tap không nhìn tài liệu."],
        ["9. Lưu ý", "Đừng nhảy thẳng vào framework khi chưa biết lập trình cơ bản và chưa hiểu manual testing."],
        ["10. Sản phẩm cuối khoá", "1 framework tự build (Web UI + API), tích hợp report + CI/CD, đẩy lên GitHub làm portfolio."],
    ]
    make_sheet(wb, "Bat_Dau", "AUTOMATION TESTING – HƯỚNG DẪN BẮT ĐẦU & CÁCH DÙNG TÀI LIỆU",
               ["Mục", "Nội dung"], intro_rows, [26, 120], first=True)

    # ---------- Sheet 1: Lộ trình học theo giai đoạn ----------
    road = [
        ["GIAI ĐOẠN 0 – NỀN TẢNG (Tuần 1–2): Hiểu nghề & môi trường"],
        ["Tuần 1", "Hiểu Testing là gì, vai trò QA/Tester, SDLC, STLC, vòng đời 1 bug",
         "Đọc lý thuyết Manual Testing cơ bản", "Viết được 5 test case cho form đăng nhập", "Tài liệu QA cơ bản"],
        ["Tuần 2", "Cài đặt môi trường: VS Code, Git, JDK/Python, trình duyệt, DevTools (F12)",
         "Cài đặt & chạy 'Hello World'", "Chạy được chương trình đầu tiên + push lên GitHub", "Git, VS Code"],
        ["GIAI ĐOẠN 1 – LẬP TRÌNH CƠ BẢN (Tuần 3–5): Bắt buộc trước khi automation"],
        ["Tuần 3", "Biến, kiểu dữ liệu, toán tử, if/else, vòng lặp for/while",
         "Bài tập syntax cơ bản", "Giải 20 bài tập nhỏ", "Python/Java cơ bản"],
        ["Tuần 4", "Hàm, mảng/list, dictionary/map, string, xử lý ngoại lệ (try/catch)",
         "Viết hàm xử lý chuỗi & list", "Viết 1 chương trình quản lý danh bạ đơn giản", "Ngôn ngữ chính"],
        ["Tuần 5", "OOP: class, object, kế thừa, đa hình, đóng gói (RẤT QUAN TRỌNG cho framework)",
         "Mô hình hoá đối tượng", "Tạo class Student/Account có method", "OOP"],
        ["GIAI ĐOẠN 2 – WEB AUTOMATION (Tuần 6–10): Trọng tâm"],
        ["Tuần 6", "HTML, CSS, DOM, XPath, CSS Selector – cách tìm phần tử web",
         "Luyện locator trên web thật", "Viết 30 XPath/CSS cho 1 trang web", "DevTools, SelectorsHub"],
        ["Tuần 7", "Selenium/Playwright cơ bản: mở trình duyệt, click, nhập liệu, đọc text",
         "Tự động đăng nhập 1 web demo", "Script tự động login + verify", "Selenium / Playwright"],
        ["Tuần 8", "Wait (implicit/explicit), xử lý dropdown, alert, iframe, table, upload file",
         "Xử lý phần tử phức tạp", "Tự động đặt hàng trên web demo", "Selenium / Playwright"],
        ["Tuần 9", "Test runner: TestNG/JUnit/PyTest – assertion, group, data provider, parallel",
         "Viết test case có assert", "10 test case có report pass/fail", "TestNG/PyTest"],
        ["Tuần 10", "Page Object Model (POM) – tổ chức code chuyên nghiệp",
         "Refactor code sang POM", "Chuyển project tuần 8 sang POM", "Design Pattern"],
        ["GIAI ĐOẠN 3 – API TESTING (Tuần 11–12)"],
        ["Tuần 11", "HTTP, REST, method GET/POST/PUT/DELETE, status code, JSON, Postman",
         "Test API bằng Postman", "Test 1 bộ CRUD API + viết collection", "Postman"],
        ["Tuần 12", "Tự động API bằng code: RestAssured (Java) / requests+pytest (Python)",
         "Viết API test tự động", "10 API test có assert response & schema", "RestAssured / requests"],
        ["GIAI ĐOẠN 4 – NÂNG CAO & TÍCH HỢP (Tuần 13–16)"],
        ["Tuần 13", "Data-driven, đọc Excel/CSV/JSON, cấu hình môi trường, biến môi trường",
         "Tách data ra khỏi code", "Test chạy với 20 bộ dữ liệu từ Excel", "Apache POI / openpyxl"],
        ["Tuần 14", "Báo cáo: Allure/Extent Report, chụp ảnh khi lỗi, log",
         "Tích hợp report đẹp", "Report có ảnh chụp lỗi", "Allure / Extent"],
        ["Tuần 15", "CI/CD: Git nâng cao, Jenkins/GitHub Actions chạy test tự động, Docker cơ bản",
         "Cho test chạy tự động trên CI", "Pipeline chạy test mỗi lần push", "Jenkins / GitHub Actions"],
        ["Tuần 16", "BDD (Cucumber/Behave), Mobile cơ bản (Appium), tổng hợp build framework",
         "Hoàn thiện framework cá nhân", "Framework hoàn chỉnh đẩy GitHub làm portfolio", "Cucumber / Appium"],
        ["GIAI ĐOẠN 5 – CHUYÊN SÂU (sau tuần 16, học suốt nghề)"],
        ["Liên tục", "Performance (JMeter/k6), Security cơ bản, Cloud (Selenium Grid/BrowserStack), AI in testing",
         "Mở rộng kỹ năng", "Tham gia dự án thật / freelance", "JMeter, k6, BrowserStack"],
    ]
    make_sheet(wb, "Lo_Trinh_Hoc", "LỘ TRÌNH HỌC AUTOMATION TESTING (16 TUẦN, CÓ THỂ ĐIỀU CHỈNH)",
               ["Mốc thời gian", "Nội dung học", "Thực hành", "Tiêu chí đạt", "Công cụ/Thư viện"],
               road, [14, 46, 26, 34, 22], phase_merge=True)

    # ---------- Sheet 2: Nền tảng coding cho tester ----------
    coding = [
        ["Vì sao cần code?", "Automation = lập trình + testing. Không biết code thì chỉ dùng được tool kéo-thả, rất hạn chế và lương thấp.", "Cao"],
        ["Chọn ngôn ngữ", "Python (cú pháp dễ, hợp người mới), Java (nhiều job VN, mạnh với Selenium/RestAssured), JavaScript/TypeScript (Playwright, Cypress).", "Cao"],
        ["Biến & kiểu dữ liệu", "int, float, string, boolean, list/array, dict/map. Hiểu cách lưu và truy xuất dữ liệu.", "Cao"],
        ["Cấu trúc điều kiện", "if / else if / else – dùng để verify kết quả test (nếu A thì pass, ngược lại fail).", "Cao"],
        ["Vòng lặp", "for, while – dùng lặp qua danh sách phần tử, chạy test nhiều bộ dữ liệu.", "Cao"],
        ["Hàm/Method", "Tách logic dùng lại nhiều lần (vd: hàm login). Tham số, giá trị trả về.", "Cao"],
        ["OOP", "Class, Object, kế thừa, đóng gói, đa hình. NỀN TẢNG để xây Page Object Model & framework.", "Rất cao"],
        ["Exception handling", "try/catch/finally – xử lý khi phần tử không tìm thấy, timeout, lỗi mạng.", "Cao"],
        ["Collections", "List, Set, Map/Dict – lưu nhiều test data, xử lý kết quả.", "Trung bình"],
        ["File I/O", "Đọc/ghi file CSV, Excel, JSON, properties – phục vụ data-driven testing.", "Trung bình"],
        ["Cấu trúc project", "Hiểu package/module, import, quản lý thư mục src/test/resources.", "Trung bình"],
        ["Quản lý thư viện", "Maven/Gradle (Java), pip/poetry (Python), npm (JS) – cài thư viện, quản lý version.", "Cao"],
        ["Git cơ bản", "clone, add, commit, push, pull, branch, merge, pull request. Bắt buộc khi làm việc nhóm.", "Rất cao"],
        ["Debug", "Đặt breakpoint, đọc log, đọc stack trace để tìm nguyên nhân lỗi.", "Cao"],
    ]
    make_sheet(wb, "Nen_Tang_Coding", "NỀN TẢNG LẬP TRÌNH BẮT BUỘC CHO AUTOMATION TESTER",
               ["Chủ đề", "Nội dung cần nắm", "Mức độ quan trọng"],
               coding, [22, 100, 18])

    # ---------- Sheet 3: Khái niệm lý thuyết ----------
    concepts = [
        ["Manual Testing", "Kiểm thử thủ công bằng tay, không dùng tool tự động.", "Tester click vào nút và kiểm tra kết quả."],
        ["Automation Testing", "Dùng công cụ/script để thực thi test case tự động, so sánh kết quả thực tế với mong đợi.", "Script tự đăng nhập và kiểm tra hiển thị."],
        ["Khi nào nên automation", "Test lặp lại nhiều, regression, smoke, data lớn, cần chạy nhanh & thường xuyên.", "Chạy lại 500 test mỗi đêm."],
        ["Khi nào KHÔNG nên", "Test chạy 1 lần, UI thay đổi liên tục, kiểm thử cảm tính/UX, ad-hoc.", "Test giao diện mới đang prototype."],
        ["SDLC", "Software Development Life Cycle – vòng đời phát triển phần mềm.", "Waterfall, Agile, Scrum."],
        ["STLC", "Software Testing Life Cycle – các giai đoạn của hoạt động kiểm thử.", "Phân tích yêu cầu -> thiết kế -> thực thi -> đóng."],
        ["Test Case", "Tập hợp bước, dữ liệu, điều kiện để kiểm tra 1 chức năng.", "TC01: Đăng nhập đúng -> vào trang chủ."],
        ["Test Scenario", "Kịch bản kiểm thử mức cao, gom nhiều test case.", "Kiểm thử toàn bộ chức năng thanh toán."],
        ["Test Script", "Đoạn code tự động thực hiện test case.", "File login_test.py."],
        ["Assertion", "Câu lệnh kiểm tra kết quả mong đợi; sai thì test fail.", "assertEquals('Trang chủ', tieuDe)."],
        ["Regression Testing", "Chạy lại test để đảm bảo thay đổi mới không làm hỏng chức năng cũ.", "Sau khi sửa bug vẫn test lại login."],
        ["Smoke Testing", "Test nhanh các chức năng chính xem build có chạy được không.", "Mở app, login, mở trang chính."],
        ["Sanity Testing", "Test hẹp, sâu vào chức năng vừa sửa.", "Chỉ test lại đúng phần vừa fix."],
        ["Locator", "Cách định vị phần tử trên web/app (id, name, class, xpath, css).", "//input[@id='username']"],
        ["XPath", "Ngôn ngữ định vị phần tử theo cấu trúc XML/HTML.", "//button[text()='Đăng nhập']"],
        ["CSS Selector", "Định vị phần tử theo cú pháp CSS, thường nhanh hơn XPath.", "input#username, .btn-login"],
        ["DOM", "Document Object Model – cây cấu trúc của trang web.", "Xem bằng F12 -> Elements."],
        ["Wait", "Chờ phần tử sẵn sàng. Implicit (chung), Explicit (theo điều kiện), Fluent.", "Chờ tối đa 10s tới khi nút hiện."],
        ["Flaky Test", "Test lúc pass lúc fail không ổn định, thường do wait/timing/dữ liệu.", "Test fail ngẫu nhiên do mạng chậm."],
        ["Page Object Model", "Mẫu thiết kế: mỗi trang là 1 class chứa locator & action, tách khỏi test.", "LoginPage.login(user, pass)."],
        ["Data-driven Testing", "Một test chạy với nhiều bộ dữ liệu từ file/DB.", "Login với 50 tài khoản từ Excel."],
        ["Keyword-driven", "Test được mô tả bằng từ khoá/hành động, tách logic khỏi data.", "Robot Framework."],
        ["BDD", "Behavior Driven Development – viết test bằng ngôn ngữ tự nhiên Given/When/Then.", "Cucumber, SpecFlow, Behave."],
        ["Framework", "Bộ quy tắc + thư viện + cấu trúc để viết automation hiệu quả, dễ bảo trì.", "POM + TestNG + Allure + Maven."],
        ["CI/CD", "Continuous Integration/Delivery – tự động build, test, deploy.", "Jenkins chạy test mỗi lần push."],
        ["Cross-browser Testing", "Test trên nhiều trình duyệt (Chrome, Firefox, Edge, Safari).", "Selenium Grid / BrowserStack."],
        ["Headless", "Chạy trình duyệt không hiển thị giao diện, nhanh hơn, hợp CI.", "chrome --headless."],
        ["Test Pyramid", "Mô hình: nhiều Unit test, vừa API/Integration, ít UI test.", "Unit > API > UI."],
    ]
    make_sheet(wb, "Khai_Niem", "KHÁI NIỆM & LÝ THUYẾT CỐT LÕI (GIẢI THÍCH DỄ HIỂU)",
               ["Khái niệm", "Giải thích", "Ví dụ"],
               concepts, [24, 80, 46])

    # ---------- Sheet 4: Tools & Frameworks ----------
    tools = [
        ["Selenium WebDriver", "Web UI Automation", "Java, Python, C#, JS", "Phổ biến nhất, miễn phí, hỗ trợ mọi trình duyệt, cộng đồng lớn", "Cần tự cấu hình wait, dễ flaky, setup nhiều", "★★★★★ phải học"],
        ["Playwright", "Web UI + API", "JS/TS, Python, Java, C#", "Hiện đại, auto-wait, nhanh, hỗ trợ nhiều tab/trình duyệt, trace viewer", "Mới hơn, ít tài liệu tiếng Việt", "★★★★★ nên học"],
        ["Cypress", "Web UI (Front-end)", "JavaScript/TS", "Dễ debug, chạy nhanh, time-travel, hợp dev front-end", "Chỉ JS, hạn chế đa tab/đa domain, không mobile", "★★★★ tuỳ dự án"],
        ["TestNG", "Test runner (Java)", "Java", "Annotation, group, data provider, parallel, report", "Chỉ cho Java", "★★★★★ nếu dùng Java"],
        ["JUnit 5", "Test runner (Java)", "Java", "Chuẩn unit test Java, tích hợp tốt", "Ít tính năng hơn TestNG cho automation", "★★★★"],
        ["PyTest", "Test runner (Python)", "Python", "Cú pháp gọn, fixture mạnh, plugin nhiều", "Chỉ Python", "★★★★★ nếu dùng Python"],
        ["RestAssured", "API Testing", "Java", "DSL đọc dễ (given/when/then), validate JSON mạnh", "Chỉ Java", "★★★★★ API Java"],
        ["Postman", "API Testing (manual+auto)", "GUI + JS", "Dễ dùng, test nhanh, collection, Newman chạy CLI/CI", "Khó scale framework lớn", "★★★★★ phải biết"],
        ["requests + pytest", "API Testing", "Python", "Đơn giản, linh hoạt, hợp người Python", "Tự viết nhiều helper", "★★★★ API Python"],
        ["Appium", "Mobile Automation", "Java, Python, JS...", "Test Android & iOS, native/hybrid/web, dùng chung API Selenium", "Setup phức tạp, chạy chậm", "★★★★ nếu làm mobile"],
        ["Cucumber", "BDD Framework", "Java, JS, Ruby", "Viết test bằng Gherkin, BA/PO đọc được", "Tốn công maintain step definition", "★★★★"],
        ["Robot Framework", "Keyword-driven", "Python", "Dễ với người ít code, nhiều thư viện sẵn", "Khó tuỳ biến sâu", "★★★"],
        ["Allure Report", "Báo cáo", "Đa ngôn ngữ", "Report đẹp, có step, ảnh, lịch sử, biểu đồ", "Cần cài thêm", "★★★★★ nên dùng"],
        ["Extent Report", "Báo cáo", "Java, .NET", "Report HTML đẹp, dễ tích hợp", "Chủ yếu Java/.NET", "★★★★"],
        ["Maven / Gradle", "Build & quản lý thư viện (Java)", "Java", "Quản lý dependency, build, chạy test", "Học cấu hình pom.xml", "★★★★★ Java"],
        ["Jenkins", "CI/CD", "Đa ngôn ngữ", "Tự động chạy test, plugin nhiều, miễn phí", "Cần server, cấu hình nhiều", "★★★★ phổ biến DN"],
        ["GitHub Actions", "CI/CD", "Đa ngôn ngữ", "Tích hợp sẵn GitHub, YAML đơn giản, miễn phí mức cơ bản", "Phụ thuộc GitHub", "★★★★★ dễ bắt đầu"],
        ["GitLab CI", "CI/CD", "Đa ngôn ngữ", "Tích hợp GitLab, mạnh mẽ", "Học cú pháp .gitlab-ci.yml", "★★★★"],
        ["Docker", "Container", "Đa ngôn ngữ", "Đóng gói môi trường test đồng nhất, chạy Selenium Grid", "Khái niệm mới với người mới", "★★★★ nâng cao"],
        ["Selenium Grid", "Chạy song song/đa máy", "Đa ngôn ngữ", "Chạy test nhiều trình duyệt/máy cùng lúc", "Cấu hình hạ tầng", "★★★ nâng cao"],
        ["BrowserStack/SauceLabs", "Cloud testing", "Đa ngôn ngữ", "Test trên hàng ngàn thiết bị/trình duyệt thật trên cloud", "Trả phí", "★★★ doanh nghiệp"],
        ["JMeter", "Performance Testing", "GUI/Java", "Test tải, hiệu năng, miễn phí, phổ biến", "Giao diện cũ", "★★★ mở rộng"],
        ["k6", "Performance Testing", "JavaScript", "Hiện đại, viết bằng JS, hợp CI", "Cần biết JS", "★★★ mở rộng"],
        ["Git", "Version control", "—", "Quản lý code, làm việc nhóm, nền tảng CI/CD", "Cần luyện tập", "★★★★★ bắt buộc"],
        ["VS Code / IntelliJ", "IDE", "—", "Viết & debug code, plugin phong phú", "—", "★★★★★ bắt buộc"],
    ]
    make_sheet(wb, "Tools_Frameworks", "CÔNG CỤ & FRAMEWORK – TỔNG QUAN, ƯU/NHƯỢC ĐIỂM & MỨC ƯU TIÊN",
               ["Tool/Framework", "Loại", "Ngôn ngữ", "Ưu điểm", "Nhược điểm", "Mức ưu tiên học"],
               tools, [22, 22, 20, 44, 34, 22])

    # ---------- Sheet 5: Web Automation chi tiết ----------
    web = [
        ["Mở/đóng trình duyệt", "Khởi tạo WebDriver, mở URL, maximize, đóng", "driver.get(url); driver.quit()", "Cơ bản"],
        ["Tìm phần tử", "By id, name, class, tag, link, xpath, css", "find_element(By.ID, 'user')", "Cơ bản"],
        ["Thao tác cơ bản", "click(), send_keys(), clear(), getText(), getAttribute()", "el.send_keys('abc')", "Cơ bản"],
        ["Wait", "Implicit, Explicit (WebDriverWait + ExpectedConditions), Fluent", "wait.until(EC.visible(...))", "Quan trọng"],
        ["Dropdown", "Select by text/value/index", "Select(el).select_by_visible_text('VN')", "Trung bình"],
        ["Checkbox/Radio", "click, isSelected để verify", "if not el.is_selected(): el.click()", "Trung bình"],
        ["Alert/Popup", "switch_to.alert, accept/dismiss/sendKeys", "driver.switch_to.alert.accept()", "Trung bình"],
        ["iFrame", "switch_to.frame / default_content", "driver.switch_to.frame('main')", "Trung bình"],
        ["Multiple windows/tabs", "window_handles, switch_to.window", "driver.switch_to.window(handles[1])", "Trung bình"],
        ["Table", "Duyệt row/cell bằng xpath, đọc dữ liệu", "rows = find_elements(...tr)", "Trung bình"],
        ["Mouse/Keyboard", "Actions: hover, drag&drop, right click, double click", "ActionChains(driver).move_to_element(el)", "Nâng cao"],
        ["Upload/Download file", "send_keys đường dẫn file; cấu hình thư mục tải", "el.send_keys('C:/a.png')", "Nâng cao"],
        ["Chụp ảnh màn hình", "save_screenshot khi lỗi để debug", "driver.save_screenshot('err.png')", "Quan trọng"],
        ["JavaScript Executor", "Thực thi JS: scroll, click ẩn, set value", "execute_script('arguments[0].click()', el)", "Nâng cao"],
        ["Cookie/Storage", "Lấy/đặt cookie để bỏ qua login", "driver.add_cookie({...})", "Nâng cao"],
        ["Headless & options", "Chạy không giao diện, set window size, disable popup", "options.add_argument('--headless')", "Quan trọng CI"],
        ["Cross-browser", "Chạy trên Chrome/Firefox/Edge", "Tham số hoá driver", "Nâng cao"],
        ["Page Object Model", "Tách locator + action thành class theo trang", "LoginPage(driver).login()", "Bắt buộc"],
    ]
    make_sheet(wb, "Web_Automation", "WEB AUTOMATION – KỸ THUẬT CẦN THÀNH THẠO (SELENIUM/PLAYWRIGHT)",
               ["Kỹ thuật", "Mô tả", "Ví dụ lệnh", "Mức độ"],
               web, [26, 56, 46, 16])

    # ---------- Sheet 6: API Testing ----------
    api = [
        ["HTTP cơ bản", "Hiểu request/response, header, body, query param, path param", "GET /users?id=1"],
        ["HTTP Methods", "GET (đọc), POST (tạo), PUT (cập nhật toàn bộ), PATCH (một phần), DELETE (xoá)", "POST /login"],
        ["Status Code", "2xx thành công, 3xx redirect, 4xx lỗi client, 5xx lỗi server", "200, 201, 400, 401, 404, 500"],
        ["JSON", "Định dạng dữ liệu phổ biến của API, key-value", '{"name":"An","age":20}'],
        ["Authentication", "Basic Auth, Bearer Token (JWT), API Key, OAuth2", "Authorization: Bearer <token>"],
        ["Postman cơ bản", "Tạo request, collection, environment, variable", "Gửi GET và xem response"],
        ["Postman nâng cao", "Pre-request script, Tests (assert), chạy collection bằng Newman/CI", "pm.test('status 200', ...)"],
        ["Validate response", "Kiểm tra status, body field, header, thời gian phản hồi", "assert body.id == 1"],
        ["JSON Schema Validation", "Kiểm tra cấu trúc response đúng định dạng", "matchesJsonSchema(schema)"],
        ["RestAssured (Java)", "given().header().when().get().then().statusCode(200)", "DSL đọc dễ"],
        ["requests + pytest (Python)", "r = requests.get(url); assert r.status_code==200", "Đơn giản, linh hoạt"],
        ["Data-driven API", "Chạy 1 test với nhiều bộ dữ liệu từ file", "Test login 20 account"],
        ["Chuỗi request (chaining)", "Lấy token từ request A dùng cho request B", "Login -> lấy token -> gọi API khác"],
        ["Mock API", "Giả lập API khi backend chưa xong (WireMock, Postman Mock)", "Mock server trả dữ liệu giả"],
        ["API trong CI", "Chạy API test tự động trên pipeline, nhanh & ổn định hơn UI", "Newman/pytest trên Jenkins"],
    ]
    make_sheet(wb, "API_Testing", "API TESTING – KIẾN THỨC & KỸ NĂNG (POSTMAN, RESTASSURED, REQUESTS)",
               ["Chủ đề", "Nội dung", "Ví dụ"],
               api, [26, 74, 44])

    # ---------- Sheet 7: Mobile Automation ----------
    mobile = [
        ["Loại app mobile", "Native (viết riêng iOS/Android), Hybrid (web nhúng), Web mobile (mở bằng browser)", "Cơ bản"],
        ["Appium", "Tool chính cho mobile automation, dùng chung API kiểu Selenium (WebDriver)", "Cơ bản"],
        ["Môi trường Android", "Cài Android Studio, SDK, AVD (giả lập) hoặc máy thật + USB debug", "Setup"],
        ["Môi trường iOS", "Cần macOS, Xcode, simulator (test iOS bắt buộc máy Mac)", "Setup"],
        ["Appium Inspector", "Công cụ xem cây phần tử mobile để lấy locator", "Locator"],
        ["Locator mobile", "accessibility id, id, xpath, UIAutomator (Android), Predicate (iOS)", "Locator"],
        ["Desired Capabilities", "Cấu hình thiết bị: platformName, deviceName, app path", "Setup"],
        ["Gesture", "Tap, swipe, scroll, long press, pinch/zoom", "Thao tác"],
        ["Context", "Chuyển NATIVE_APP <-> WEBVIEW cho app hybrid", "Nâng cao"],
        ["Thực thi thật", "Chạy trên cloud (BrowserStack/SauceLabs) khi không có nhiều thiết bị", "Nâng cao"],
        ["Lưu ý", "Mobile automation chậm & khó hơn web; chỉ học sau khi vững web automation", "Định hướng"],
    ]
    make_sheet(wb, "Mobile_Automation", "MOBILE AUTOMATION – TỔNG QUAN (APPIUM) – HỌC SAU KHI VỮNG WEB",
               ["Chủ đề", "Nội dung", "Phân loại"],
               mobile, [26, 86, 18])

    # ---------- Sheet 8: CI/CD & DevOps cho tester ----------
    cicd = [
        ["Git nâng cao", "Branch strategy, merge/rebase, pull request, resolve conflict", "Bắt buộc"],
        ["CI là gì", "Continuous Integration: mỗi lần push code, tự động build & chạy test", "Cốt lõi"],
        ["CD là gì", "Continuous Delivery/Deployment: tự động triển khai bản build đã test", "Cốt lõi"],
        ["Pipeline", "Chuỗi bước: checkout -> build -> test -> report -> deploy", "Cốt lõi"],
        ["GitHub Actions", "Viết workflow YAML trong .github/workflows, chạy test khi push/PR", "Nên học đầu tiên"],
        ["Jenkins", "Tạo job/pipeline (Jenkinsfile), schedule, trigger, plugin Allure", "Phổ biến DN"],
        ["GitLab CI", "File .gitlab-ci.yml định nghĩa stage/job", "Tuỳ công ty"],
        ["Trigger", "Chạy theo push, PR, lịch (cron nightly), thủ công", "Quan trọng"],
        ["Báo cáo trên CI", "Xuất Allure/JUnit XML, gửi kết quả qua email/Slack/Teams", "Quan trọng"],
        ["Chạy song song", "Parallel test, Selenium Grid, matrix build để giảm thời gian", "Nâng cao"],
        ["Docker", "Đóng gói môi trường test đồng nhất, chạy ở mọi máy", "Nâng cao"],
        ["Quản lý secret", "Lưu password/token an toàn (CI secrets), không hard-code", "Bảo mật"],
        ["Mục tiêu cuối", "Mỗi lần dev push code -> test tự chạy -> có report -> biết ngay pass/fail", "Tổng kết"],
    ]
    make_sheet(wb, "CI_CD", "CI/CD & DEVOPS CHO AUTOMATION TESTER",
               ["Chủ đề", "Nội dung", "Ghi chú"],
               cicd, [24, 82, 24])

    # ---------- Sheet 9: Design Pattern & Best Practices ----------
    bp = [
        ["Page Object Model (POM)", "Mỗi trang = 1 class chứa locator + action; test chỉ gọi method.", "Dễ bảo trì, tái sử dụng"],
        ["Page Factory", "Khởi tạo phần tử bằng annotation @FindBy (Java).", "Gọn locator"],
        ["Singleton (WebDriver)", "Một instance driver dùng chung hợp lý.", "Quản lý driver"],
        ["Factory Pattern", "Tạo driver theo loại trình duyệt qua 1 nơi.", "Cross-browser"],
        ["Data-driven", "Tách test data ra Excel/CSV/JSON/DB.", "Linh hoạt dữ liệu"],
        ["BDD layer", "Gherkin Given/When/Then cho dễ đọc với non-tech.", "Giao tiếp BA/PO"],
        ["Đặt tên rõ ràng", "Tên test/biến/method mô tả đúng ý nghĩa.", "Code sạch"],
        ["Tránh hard-code", "Đưa URL, account, timeout vào file config.", "Dễ đổi môi trường"],
        ["Explicit wait thay vì sleep", "Không dùng Thread.sleep cố định; dùng wait theo điều kiện.", "Giảm flaky"],
        ["Độc lập giữa các test", "Mỗi test tự chuẩn bị & dọn dữ liệu, không phụ thuộc test khác.", "Ổn định"],
        ["Tự dọn dữ liệu (teardown)", "Xoá data tạo ra sau test để chạy lại được.", "Sạch môi trường"],
        ["Báo cáo & log", "Có report + log + ảnh lỗi để debug nhanh.", "Dễ điều tra"],
        ["Tuân thủ Test Pyramid", "Ưu tiên Unit/API test, hạn chế lạm dụng UI test.", "Nhanh & ổn định"],
        ["Code review & Git flow", "Review code automation như code dev thật.", "Chất lượng"],
        ["Tránh phụ thuộc thứ tự", "Không để test B cần test A chạy trước.", "Parallel an toàn"],
    ]
    make_sheet(wb, "Design_Pattern_BP", "DESIGN PATTERN & BEST PRACTICES KHI XÂY FRAMEWORK",
               ["Pattern / Nguyên tắc", "Mô tả", "Lợi ích"],
               bp, [30, 74, 30])

    # ---------- Sheet 10: Bài tập thực hành ----------
    ex = [
        ["GĐ1 - Coding", "B1", "Viết chương trình kiểm tra số nguyên tố, FizzBuzz, đảo chuỗi", "Dễ", "Chạy đúng mọi input"],
        ["GĐ1 - Coding", "B2", "Viết class Account (deposit/withdraw) có kiểm tra số dư", "Dễ", "Có OOP, exception"],
        ["GĐ1 - Git", "B3", "Tạo repo GitHub, push code, tạo branch, mở pull request", "Dễ", "Repo public có 3 commit"],
        ["GĐ2 - Locator", "B4", "Vào trang demoqa.com / saucedemo.com, viết 20 XPath & 20 CSS", "TB", "Tất cả locator tìm đúng phần tử"],
        ["GĐ2 - Web", "B5", "Tự động login saucedemo.com (đúng & sai), verify thông báo", "TB", "Có assert pass/fail"],
        ["GĐ2 - Web", "B6", "Tự động thêm 3 sản phẩm vào giỏ và checkout trên saucedemo", "TB", "Hoàn tất luồng mua hàng"],
        ["GĐ2 - Web", "B7", "Xử lý dropdown, alert, iframe trên the-internet.herokuapp.com", "TB", "Pass tất cả case"],
        ["GĐ2 - Runner", "B8", "Viết 10 test case dùng TestNG/PyTest có @BeforeMethod/@AfterMethod", "TB", "Report pass/fail rõ ràng"],
        ["GĐ2 - POM", "B9", "Refactor B6 sang Page Object Model (LoginPage, ProductPage...)", "TB", "Tách locator khỏi test"],
        ["GĐ3 - API", "B10", "Dùng Postman test reqres.in: GET list, POST tạo user, kiểm status & body", "TB", "Collection có Tests assert"],
        ["GĐ3 - API", "B11", "Viết API test tự động (RestAssured/requests) cho reqres.in CRUD", "TB", "10 test có assert"],
        ["GĐ3 - API", "B12", "Chaining: login lấy token -> gọi API cần auth", "Khó", "Token truyền đúng"],
        ["GĐ4 - Data", "B13", "Đọc 20 tài khoản từ Excel/CSV, chạy data-driven login", "Khó", "1 test chạy 20 lần"],
        ["GĐ4 - Report", "B14", "Tích hợp Allure/Extent, chụp ảnh khi test fail", "Khó", "Report có ảnh lỗi"],
        ["GĐ4 - CI/CD", "B15", "Cấu hình GitHub Actions chạy test mỗi lần push", "Khó", "Pipeline xanh/đỏ tự động"],
        ["GĐ4 - BDD", "B16", "Viết 3 scenario Cucumber/Behave cho chức năng login", "Khó", "Gherkin chạy được"],
        ["GĐ4 - Capstone", "B17", "Xây framework hoàn chỉnh: POM + API + data-driven + report + CI, đẩy GitHub", "Rất khó", "Portfolio hoàn chỉnh"],
    ]
    make_sheet(wb, "Bai_Tap_Thuc_Hanh", "BÀI TẬP THỰC HÀNH (LÀM THEO THỨ TỰ – CÓ TRANG WEB DEMO MIỄN PHÍ)",
               ["Giai đoạn", "Mã", "Đề bài", "Độ khó", "Tiêu chí hoàn thành"],
               ex, [18, 8, 70, 12, 34])

    # ---------- Sheet 11: Câu hỏi ôn tập ----------
    quiz = [
        ["Lý thuyết", "Automation testing là gì? Khác manual thế nào?", "Dùng tool/script chạy test tự động, so sánh kết quả; manual làm tay."],
        ["Lý thuyết", "Khi nào nên/không nên automation?", "Nên: lặp lại, regression, data lớn. Không nên: chạy 1 lần, UI đổi liên tục, UX."],
        ["Lý thuyết", "Test Pyramid là gì?", "Nhiều Unit > vừa API > ít UI test, để nhanh và ổn định."],
        ["Locator", "Phân biệt XPath và CSS Selector?", "CSS nhanh, gọn; XPath mạnh hơn (đi ngược cây, theo text)."],
        ["Locator", "Thứ tự ưu tiên locator?", "id > name > css > xpath; ưu tiên locator ổn định, duy nhất."],
        ["Wait", "Phân biệt implicit, explicit, fluent wait?", "Implicit: chung; explicit: theo điều kiện; fluent: explicit + polling + bỏ qua exception."],
        ["Wait", "Vì sao không nên dùng Thread.sleep?", "Cố định thời gian, chậm & dễ flaky; nên dùng wait theo điều kiện."],
        ["POM", "Page Object Model là gì? Lợi ích?", "Mỗi trang 1 class chứa locator+action; dễ bảo trì, tái sử dụng."],
        ["Flaky", "Flaky test là gì? Nguyên nhân & cách khắc phục?", "Test lúc pass lúc fail; do wait/timing/data; fix bằng explicit wait, data độc lập."],
        ["API", "REST API là gì? Các method chính?", "Kiến trúc giao tiếp qua HTTP; GET/POST/PUT/PATCH/DELETE."],
        ["API", "Ý nghĩa status code 200/201/400/401/404/500?", "OK/Created/Bad request/Unauthorized/Not found/Server error."],
        ["API", "Vì sao nên ưu tiên API test hơn UI test?", "Nhanh hơn, ổn định hơn, ít flaky, gần logic nghiệp vụ."],
        ["Framework", "Một framework automation tốt gồm gì?", "POM, runner, data-driven, config, report, log, CI, dễ bảo trì."],
        ["Framework", "Data-driven testing là gì?", "Một test chạy nhiều bộ dữ liệu từ file/DB."],
        ["CI/CD", "CI/CD là gì? Lợi ích cho tester?", "Tự động build/test/deploy; phát hiện lỗi sớm, chạy test thường xuyên."],
        ["CI/CD", "Làm sao cho test chạy tự động khi push code?", "Cấu hình pipeline (GitHub Actions/Jenkins) trigger theo push/PR."],
        ["Git", "Pull request là gì?", "Yêu cầu merge code có review trước khi vào nhánh chính."],
        ["BDD", "BDD là gì? Cú pháp Gherkin?", "Viết test bằng ngôn ngữ tự nhiên Given/When/Then."],
        ["Thực hành", "Cách debug khi test fail?", "Đọc log/stack trace, xem ảnh chụp lỗi, chạy lại, kiểm tra locator/wait/data."],
        ["Thực hành", "Cross-browser testing làm thế nào?", "Tham số hoá driver, dùng Grid/cloud chạy nhiều trình duyệt."],
    ]
    make_sheet(wb, "Cau_Hoi_On_Tap", "CÂU HỎI ÔN TẬP (TỰ TRẢ LỜI TRƯỚC KHI XEM ĐÁP ÁN)",
               ["Chủ đề", "Câu hỏi", "Gợi ý đáp án"],
               quiz, [16, 60, 70])

    # ---------- Sheet 12: Tài nguyên học ----------
    res = [
        ["Web luyện tập", "saucedemo.com", "Trang demo shop để luyện Selenium UI", "Miễn phí"],
        ["Web luyện tập", "the-internet.herokuapp.com", "Đủ tình huống: alert, iframe, table, upload...", "Miễn phí"],
        ["Web luyện tập", "demoqa.com", "Form, widget, element đa dạng", "Miễn phí"],
        ["Web luyện tập", "automationexercise.com", "E-commerce thật để luyện end-to-end", "Miễn phí"],
        ["API luyện tập", "reqres.in", "Fake REST API cho test CRUD", "Miễn phí"],
        ["API luyện tập", "jsonplaceholder.typicode.com", "Fake API JSON phổ biến", "Miễn phí"],
        ["API luyện tập", "petstore.swagger.io", "API mẫu có Swagger doc", "Miễn phí"],
        ["Tài liệu", "selenium.dev/documentation", "Tài liệu chính thức Selenium", "Miễn phí"],
        ["Tài liệu", "playwright.dev", "Tài liệu chính thức Playwright", "Miễn phí"],
        ["Tài liệu", "learning.postman.com", "Học Postman chính thức", "Miễn phí"],
        ["Chứng chỉ", "istqb.org", "Chứng chỉ tester quốc tế ISTQB", "Có phí thi"],
        ["Cộng đồng", "Ministry of Testing", "Cộng đồng tester lớn", "Miễn phí"],
        ["YouTube", "Tìm: 'Selenium tutorial', 'Playwright tutorial', 'ISTQB foundation'", "Học qua video", "Miễn phí"],
        ["Sách", "'Mastering Selenium WebDriver', 'Clean Code'", "Đọc nâng cao", "—"],
        ["Luyện code", "leetcode.com / hackerrank.com", "Luyện tư duy lập trình", "Miễn phí"],
        ["Git", "github.com", "Lưu code & làm portfolio", "Miễn phí"],
    ]
    make_sheet(wb, "Tai_Nguyen", "TÀI NGUYÊN HỌC TẬP (TRANG WEB DEMO, TÀI LIỆU, CỘNG ĐỒNG)",
               ["Loại", "Nguồn", "Mô tả", "Chi phí"],
               res, [16, 40, 64, 14])

    fn = "TaiLieu_AutomationTesting.xlsx"
    wb.save(fn)
    return fn


# =====================================================================
# ============ FILE 2: ISTQB FOUNDATION ===============================
# =====================================================================
def build_istqb():
    wb = Workbook()

    intro = [
        ["1. Chứng chỉ", "ISTQB CTFL – Certified Tester Foundation Level (nền tảng, phổ biến toàn cầu)."],
        ["2. Phù hợp", "Người mới vào nghề testing, manual & automation tester muốn chuẩn hoá kiến thức."],
        ["3. Hình thức thi", "Trắc nghiệm 40 câu, thời gian 60 phút (75 phút nếu thi ngôn ngữ không phải tiếng mẹ đẻ)."],
        ["4. Điểm đậu", "Đạt 65% (26/40 câu đúng)."],
        ["5. Syllabus", "Dựa trên Foundation Level Syllabus v4.0 (phiên bản mới). Có 6 chương chính."],
        ["6. Thời gian ôn", "4–6 tuần nếu mỗi ngày 1–2 giờ. Đọc syllabus + glossary + làm đề mẫu."],
        ["7. Tài liệu gốc", "Tải MIỄN PHÍ syllabus & glossary tại istqb.org (bản tiếng Anh chuẩn)."],
        ["8. Chiến lược", "Hiểu khái niệm + thuộc thuật ngữ + luyện thật nhiều đề mẫu (mock exam)."],
        ["9. Cấu trúc tài liệu", "Mỗi chương 1 sheet tóm tắt; có sheet thuật ngữ, đề mẫu, mẹo thi, kế hoạch ôn."],
        ["10. Lưu ý", "Đề thi bám sát Learning Objectives (K1=nhớ, K2=hiểu, K3=áp dụng) trong syllabus."],
    ]
    make_sheet(wb, "Gioi_Thieu", "ÔN THI ISTQB FOUNDATION LEVEL (CTFL) – GIỚI THIỆU & CÁCH DÙNG",
               ["Mục", "Nội dung"], intro, [24, 116], first=True)

    # Kế hoạch ôn
    plan = [
        ["GIAI ĐOẠN 1 – LÀM QUEN (Tuần 1)"],
        ["Tuần 1", "Chương 1: Nền tảng kiểm thử (Fundamentals of Testing)", "Đọc syllabus ch.1 + ghi chú thuật ngữ", "Làm 20 câu hỏi ch.1"],
        ["GIAI ĐOẠN 2 – QUY TRÌNH & THIẾT KẾ (Tuần 2–3)"],
        ["Tuần 2", "Chương 2: Kiểm thử trong vòng đời phát triển; Chương 3: Kiểm thử tĩnh", "Đọc + sơ đồ tư duy", "Làm câu hỏi ch.2-3"],
        ["Tuần 3", "Chương 4: Phân tích & thiết kế test (kỹ thuật black-box, white-box, kinh nghiệm)", "Luyện EP, BVA, Decision Table, State Transition", "Làm bài tập thiết kế test"],
        ["GIAI ĐOẠN 3 – QUẢN LÝ & CÔNG CỤ (Tuần 4)"],
        ["Tuần 4", "Chương 5: Quản lý hoạt động kiểm thử; Chương 6: Công cụ hỗ trợ kiểm thử", "Đọc + ghi nhớ vai trò", "Làm câu hỏi ch.5-6"],
        ["GIAI ĐOẠN 4 – LUYỆN ĐỀ (Tuần 5–6)"],
        ["Tuần 5", "Ôn lại toàn bộ glossary + làm 3 đề mock full 40 câu", "Bấm giờ 60 phút", "Đạt > 70% mỗi đề"],
        ["Tuần 6", "Làm thêm 3–5 đề mock, soát lỗi sai, ôn điểm yếu", "Phân tích câu sai", "Ổn định > 80% -> đăng ký thi"],
    ]
    make_sheet(wb, "Ke_Hoach_On", "KẾ HOẠCH ÔN THI ISTQB (4–6 TUẦN)",
               ["Thời gian", "Nội dung", "Cách ôn", "Mục tiêu"],
               plan, [14, 60, 40, 30], phase_merge=True)

    # Chương 1
    ch1 = [
        ["Tại sao cần kiểm thử", "Giảm rủi ro, phát hiện lỗi sớm, đảm bảo chất lượng, tuân thủ yêu cầu/hợp đồng.", "K1"],
        ["Lỗi: Error/Defect/Failure", "Error (sai sót của con người) -> Defect (lỗi trong sản phẩm) -> Failure (hệ thống chạy sai).", "K2"],
        ["Testing là gì", "Tập hợp hoạt động để đánh giá chất lượng và giảm rủi ro, không chỉ là chạy test.", "K1"],
        ["Mục tiêu testing", "Tìm lỗi, ngăn lỗi, đánh giá chất lượng, tạo niềm tin, cung cấp thông tin để ra quyết định.", "K1"],
        ["Testing vs Debugging", "Testing tìm ra failure; Debugging là dev tìm & sửa nguyên nhân.", "K2"],
        ["7 nguyên lý kiểm thử", "1.Testing chỉ ra sự hiện diện của lỗi 2.Không thể test toàn bộ 3.Test sớm 4.Lỗi co cụm 5.Nghịch lý thuốc trừ sâu 6.Test phụ thuộc ngữ cảnh 7.Sai lầm 'không lỗi'.", "K2"],
        ["Quy trình test (cơ bản)", "Lập kế hoạch, giám sát & điều khiển, phân tích, thiết kế, hiện thực, thực thi, hoàn tất.", "K2"],
        ["Test ware", "Sản phẩm của quá trình test: test plan, test case, test data, report...", "K2"],
        ["Kỹ năng & tư duy tester", "Tư duy phản biện, tỉ mỉ, giao tiếp, tư duy test (test mindset).", "K1"],
        ["Whole-team approach", "Cả nhóm cùng chịu trách nhiệm chất lượng (Agile).", "K1"],
    ]
    make_sheet(wb, "Ch1_Nen_Tang", "CHƯƠNG 1 – NỀN TẢNG CỦA KIỂM THỬ (FUNDAMENTALS OF TESTING)",
               ["Chủ đề", "Nội dung tóm tắt", "Mức (K)"],
               ch1, [28, 92, 12])

    # Chương 2
    ch2 = [
        ["Mô hình SDLC", "Sequential (Waterfall, V-Model) và Iterative/Incremental (Agile, Scrum).", "K2"],
        ["V-Model", "Mỗi mức phát triển gắn 1 mức test (component, integration, system, acceptance).", "K2"],
        ["Agile & testing", "Test liên tục, tự động hoá nhiều, tester tham gia sớm, whole-team.", "K1"],
        ["Test Levels", "Component, Component Integration, System, System Integration, Acceptance.", "K2"],
        ["Component Testing", "Test đơn vị nhỏ nhất (hàm/class), thường do dev, dùng unit test.", "K2"],
        ["Integration Testing", "Test sự tương tác giữa các thành phần/hệ thống.", "K2"],
        ["System Testing", "Test toàn hệ thống so với yêu cầu.", "K2"],
        ["Acceptance Testing", "UAT, hợp đồng, alpha/beta – khách hàng chấp nhận.", "K2"],
        ["Test Types", "Functional, Non-functional, Black-box (Structural), liên quan thay đổi (Confirmation/Regression).", "K2"],
        ["Functional Testing", "Kiểm tra hệ thống LÀM GÌ (chức năng).", "K2"],
        ["Non-functional Testing", "Kiểm tra hệ thống LÀM TỐT THẾ NÀO: hiệu năng, bảo mật, khả dụng...", "K2"],
        ["Confirmation Testing", "Test lại sau khi sửa lỗi để xác nhận đã hết lỗi.", "K2"],
        ["Regression Testing", "Đảm bảo thay đổi không gây lỗi cho phần đang chạy tốt.", "K2"],
        ["Maintenance Testing", "Test khi bảo trì/nâng cấp/di trú hệ thống; impact analysis.", "K2"],
    ]
    make_sheet(wb, "Ch2_VongDoi", "CHƯƠNG 2 – KIỂM THỬ TRONG VÒNG ĐỜI PHÁT TRIỂN PHẦN MỀM",
               ["Chủ đề", "Nội dung tóm tắt", "Mức (K)"],
               ch2, [28, 92, 12])

    # Chương 3
    ch3 = [
        ["Static Testing là gì", "Kiểm thử KHÔNG chạy chương trình: review tài liệu, code, phân tích tĩnh.", "K1"],
        ["Lợi ích", "Phát hiện lỗi sớm (rẻ hơn), tìm lỗi mà test động khó thấy (yêu cầu mơ hồ...).", "K2"],
        ["Review process", "Lập kế hoạch, bắt đầu, đánh giá cá nhân, trao đổi & phân tích, sửa & báo cáo.", "K2"],
        ["Vai trò trong review", "Author, Manager, Facilitator (moderator), Reviewer, Scribe.", "K2"],
        ["Loại review", "Informal, Walkthrough, Technical Review, Inspection (chính thức nhất).", "K2"],
        ["Static Analysis", "Công cụ tự phân tích code không chạy (lỗi cú pháp, code smell, bảo mật).", "K1"],
        ["Reviewable work product", "Bất kỳ tài liệu nào: yêu cầu, thiết kế, code, test case...", "K1"],
        ["Thành công của review", "Mục tiêu rõ, đúng người, không khí xây dựng, lãnh đạo ủng hộ.", "K2"],
    ]
    make_sheet(wb, "Ch3_KiemThuTinh", "CHƯƠNG 3 – KIỂM THỬ TĨNH (STATIC TESTING)",
               ["Chủ đề", "Nội dung tóm tắt", "Mức (K)"],
               ch3, [28, 92, 12])

    # Chương 4 - quan trọng nhất
    ch4 = [
        ["Phân loại kỹ thuật", "Black-box (đặc tả), White-box (cấu trúc), Experience-based (kinh nghiệm).", "K2", ""],
        ["Equivalence Partitioning", "Chia input thành lớp tương đương, test 1 đại diện mỗi lớp (hợp lệ & không hợp lệ).", "K3", "Tuổi 0-17,18-60,>60 -> chọn 1 giá trị mỗi nhóm"],
        ["Boundary Value Analysis", "Test tại biên & sát biên của lớp tương đương (nơi hay lỗi nhất).", "K3", "Biên 18: test 17,18,19"],
        ["Decision Table Testing", "Lập bảng điều kiện -> hành động, bao phủ tổ hợp logic.", "K3", "Nếu hội viên & >500k thì giảm giá"],
        ["State Transition Testing", "Kiểm thử theo trạng thái & sự kiện chuyển trạng thái.", "K3", "ATM: nhập PIN sai 3 lần -> khoá"],
        ["Black-box chung", "Dựa trên yêu cầu/đặc tả, không cần biết code bên trong.", "K2", ""],
        ["Statement Coverage", "Đo % câu lệnh được thực thi bởi test.", "K2", "Cần test chạy hết các dòng"],
        ["Branch Coverage", "Đo % nhánh (true/false) được thực thi.", "K2", "Test cả nhánh if và else"],
        ["White-box chung", "Dựa trên cấu trúc code; coverage thể hiện độ kỹ.", "K2", ""],
        ["Error Guessing", "Đoán lỗi dựa vào kinh nghiệm & nơi thường sai.", "K2", "Thử input rỗng, ký tự đặc biệt"],
        ["Exploratory Testing", "Đồng thời học-thiết kế-thực thi, không kịch bản cứng.", "K2", "Session-based testing"],
        ["Checklist-based", "Test dựa trên danh sách kiểm tra đã chuẩn bị.", "K2", "Checklist usability"],
        ["Collaboration-based", "ATDD, user story, acceptance criteria viết test chung với team.", "K2", "Given/When/Then"],
    ]
    make_sheet(wb, "Ch4_ThietKeTest", "CHƯƠNG 4 – PHÂN TÍCH & THIẾT KẾ TEST (QUAN TRỌNG NHẤT – CÓ K3)",
               ["Kỹ thuật", "Nội dung", "Mức (K)", "Ví dụ"],
               ch4, [26, 64, 10, 44])

    # Chương 5
    ch5 = [
        ["Test Planning", "Lập kế hoạch: mục tiêu, phạm vi, rủi ro, nguồn lực, lịch.", "K2"],
        ["Entry/Exit Criteria", "Điều kiện bắt đầu (definition of ready) & kết thúc (definition of done) test.", "K2"],
        ["Estimation", "Ước lượng công sức test (theo metric, chuyên gia, 3 điểm).", "K2"],
        ["Test Prioritization", "Ưu tiên test theo rủi ro, mức độ quan trọng.", "K2"],
        ["Risk & Testing", "Risk = khả năng xảy ra × tác động; test dựa trên rủi ro (risk-based).", "K2"],
        ["Product vs Project Risk", "Product risk: lỗi sản phẩm; Project risk: trễ tiến độ, nguồn lực.", "K2"],
        ["Test Monitoring & Control", "Theo dõi tiến độ bằng metric, điều chỉnh khi lệch kế hoạch.", "K1"],
        ["Test Reporting", "Test progress report & test completion report (summary).", "K2"],
        ["Configuration Management", "Quản lý phiên bản testware, truy vết.", "K1"],
        ["Defect Management", "Quy trình ghi nhận, phân loại, theo dõi lỗi; nội dung 1 báo cáo lỗi.", "K3"],
        ["Nội dung báo cáo lỗi", "ID, tiêu đề, mô tả, bước tái hiện, mong đợi/thực tế, severity, priority, môi trường.", "K3"],
        ["Severity vs Priority", "Severity: mức nghiêm trọng kỹ thuật; Priority: mức ưu tiên sửa theo nghiệp vụ.", "K2"],
    ]
    make_sheet(wb, "Ch5_QuanLyTest", "CHƯƠNG 5 – QUẢN LÝ HOẠT ĐỘNG KIỂM THỬ",
               ["Chủ đề", "Nội dung tóm tắt", "Mức (K)"],
               ch5, [28, 92, 12])

    # Chương 6
    ch6 = [
        ["Test Tool – mục đích", "Hỗ trợ & tự động hoá hoạt động test: quản lý, thực thi, dữ liệu, hiệu năng.", "K1"],
        ["Phân loại công cụ", "Quản lý test, quản lý lỗi, static analysis, automation, performance, CI/CD.", "K1"],
        ["Lợi ích của tool", "Giảm việc lặp lại, tăng nhất quán, dễ truy cập thông tin, đánh giá khách quan.", "K1"],
        ["Rủi ro của tool", "Kỳ vọng quá cao, đánh giá thấp công sức, phụ thuộc tool, bảo trì tool.", "K1"],
        ["Test Automation", "Lợi ích & giới hạn; không thay thế hoàn toàn con người.", "K1"],
        ["Lưu ý khi áp dụng", "Cần pilot, đánh giá phù hợp tổ chức, có người đủ kỹ năng.", "K1"],
        ["Tool & CI/CD", "Automation gắn với CI/CD để chạy test liên tục.", "K1"],
    ]
    make_sheet(wb, "Ch6_CongCu", "CHƯƠNG 6 – CÔNG CỤ HỖ TRỢ KIỂM THỬ",
               ["Chủ đề", "Nội dung tóm tắt", "Mức (K)"],
               ch6, [28, 92, 12])

    # Glossary
    glo = [
        ["Error (sai sót)", "Hành động sai của con người tạo ra kết quả sai."],
        ["Defect (lỗi/bug)", "Khiếm khuyết trong sản phẩm có thể gây failure."],
        ["Failure (hỏng hóc)", "Hệ thống không thực hiện đúng chức năng mong đợi."],
        ["Test Case", "Bộ input, điều kiện thực thi và kết quả mong đợi."],
        ["Test Basis", "Cơ sở để thiết kế test (yêu cầu, đặc tả...)."],
        ["Test Condition", "Khía cạnh cần kiểm thử."],
        ["Test Oracle", "Nguồn xác định kết quả mong đợi."],
        ["Coverage", "Mức độ test bao phủ đối tượng kiểm thử (theo %)."],
        ["Quality", "Mức độ sản phẩm đáp ứng yêu cầu & kỳ vọng."],
        ["Quality Assurance (QA)", "Hoạt động đảm bảo quy trình tạo chất lượng (phòng ngừa)."],
        ["Quality Control (QC)", "Hoạt động kiểm tra sản phẩm (phát hiện lỗi)."],
        ["Verification", "Kiểm tra 'làm đúng cách' – đúng đặc tả."],
        ["Validation", "Kiểm tra 'làm đúng thứ' – đúng nhu cầu người dùng."],
        ["Regression", "Lỗi mới phát sinh do thay đổi ở phần đang chạy tốt."],
        ["Confirmation Test", "Test lại để xác nhận lỗi đã được sửa."],
        ["Severity", "Mức nghiêm trọng kỹ thuật của lỗi."],
        ["Priority", "Mức ưu tiên xử lý lỗi theo nghiệp vụ."],
        ["Equivalence Partition", "Nhóm input được xử lý giống nhau."],
        ["Boundary Value", "Giá trị tại biên của một phân vùng."],
        ["Exit Criteria", "Điều kiện để kết thúc một hoạt động test."],
        ["Entry Criteria", "Điều kiện để bắt đầu một hoạt động test."],
        ["Test Plan", "Tài liệu mô tả phạm vi, cách tiếp cận, nguồn lực, lịch test."],
        ["Risk", "Khả năng xảy ra sự kiện bất lợi × tác động."],
        ["Static Testing", "Kiểm thử không thực thi code (review, phân tích tĩnh)."],
        ["Dynamic Testing", "Kiểm thử bằng cách thực thi phần mềm."],
    ]
    make_sheet(wb, "Thuat_Ngu", "THUẬT NGỮ ISTQB CẦN THUỘC (GLOSSARY)",
               ["Thuật ngữ", "Định nghĩa"], glo, [30, 100])

    # Đề mẫu
    mock = [
        ["1", "Nguyên lý nào nói rằng kiểm thử không thể chứng minh phần mềm không còn lỗi?", "Testing shows presence of defects (Testing chỉ ra sự hiện diện của lỗi)", "B"],
        ["2", "Error -> Defect -> Failure mô tả điều gì?", "Sai sót con người gây lỗi sản phẩm, khi chạy gây hỏng hóc", "—"],
        ["3", "Kỹ thuật nào test tại biên của phân vùng?", "Boundary Value Analysis", "—"],
        ["4", "Test do dev viết cho 1 hàm/lớp gọi là gì?", "Component (Unit) Testing", "—"],
        ["5", "Review chính thức & kỹ lưỡng nhất là loại nào?", "Inspection", "—"],
        ["6", "Severity khác Priority thế nào?", "Severity: nghiêm trọng kỹ thuật; Priority: ưu tiên sửa theo nghiệp vụ", "—"],
        ["7", "Phân vùng tương đương dùng để làm gì?", "Giảm số test bằng cách test 1 đại diện mỗi nhóm input", "—"],
        ["8", "Static testing có thực thi code không?", "Không", "—"],
        ["9", "Confirmation testing là gì?", "Test lại sau khi sửa lỗi để xác nhận đã hết", "—"],
        ["10", "Risk-based testing ưu tiên test theo gì?", "Theo mức độ rủi ro (khả năng × tác động)", "—"],
        ["11", "Decision Table phù hợp khi nào?", "Khi có nhiều điều kiện kết hợp tạo hành động khác nhau", "—"],
        ["12", "State Transition testing kiểm thử cái gì?", "Trạng thái và sự kiện chuyển trạng thái của hệ thống", "—"],
        ["13", "Branch coverage đo cái gì?", "Phần trăm nhánh true/false được thực thi", "—"],
        ["14", "Nguyên lý 'pesticide paradox' nghĩa là gì?", "Lặp lại cùng test sẽ không tìm thêm lỗi mới -> cần làm mới test", "—"],
        ["15", "Maintenance testing diễn ra khi nào?", "Khi hệ thống được sửa đổi, nâng cấp hoặc di trú", "—"],
    ]
    make_sheet(wb, "De_Mau", "ĐỀ MẪU / CÂU HỎI ÔN (TỰ TRẢ LỜI RỒI ĐỐI CHIẾU)",
               ["STT", "Câu hỏi", "Gợi ý đáp án", "Đáp án (nếu trắc nghiệm)"],
               mock, [6, 64, 60, 16])

    # Mẹo thi
    tips = [
        ["Đọc kỹ syllabus chính thức", "Đề bám sát Learning Objectives; học theo từ khoá trong syllabus."],
        ["Thuộc 7 nguyên lý kiểm thử", "Gần như đề nào cũng có câu về 7 principles."],
        ["Nắm chắc Ch.4", "Kỹ thuật thiết kế test (EP, BVA, Decision Table, State Transition) ra nhiều câu K3."],
        ["Phân biệt cặp dễ nhầm", "Error/Defect/Failure, Verification/Validation, Severity/Priority, QA/QC."],
        ["Luyện đề mock có bấm giờ", "Quen áp lực 40 câu/60 phút; phân bổ ~1.5 phút/câu."],
        ["Đọc kỹ từ phủ định", "Câu hỏi có 'NOT', 'EXCEPT' rất dễ bẫy."],
        ["Loại trừ đáp án", "Gạch đáp án sai rõ ràng để tăng xác suất đúng."],
        ["Không bỏ trống câu nào", "Không trừ điểm câu sai -> luôn chọn 1 đáp án."],
        ["Đánh dấu câu phân vân", "Làm câu dễ trước, quay lại câu khó sau."],
        ["Ôn glossary đều đặn", "Nhiều câu chỉ kiểm tra định nghĩa thuật ngữ."],
        ["Làm tối thiểu 5-6 đề mock", "Khi ổn định > 80% mới đăng ký thi thật."],
    ]
    make_sheet(wb, "Meo_Thi", "MẸO & CHIẾN LƯỢC LÀM BÀI THI ISTQB",
               ["Mẹo", "Giải thích"], tips, [34, 96])

    fn = "TaiLieu_ISTQB_Foundation.xlsx"
    wb.save(fn)
    return fn


# =====================================================================
# ============ FILE 3: INTERVIEW QUESTIONS ============================
# =====================================================================
def build_interview():
    wb = Workbook()

    intro = [
        ["1. Mục tiêu", "Bộ câu hỏi phỏng vấn Automation Tester từ cơ bản tới nâng cao, kèm gợi ý trả lời."],
        ["2. Cách dùng", "Tự trả lời TRƯỚC khi xem cột gợi ý. Trả lời thành tiếng, ngắn gọn, có ví dụ thực tế."],
        ["3. Phân loại sheet", "Cơ bản/Lý thuyết, Selenium/Web, API, Framework/Design, CI-CD-Git, Coding & Scenario, Hành vi (HR)."],
        ["4. Mức độ", "Junior: nắm cơ bản + Selenium + 1 framework. Middle: API + CI/CD + design pattern. Senior: kiến trúc, chiến lược, tối ưu."],
        ["5. Mẹo trả lời", "Dùng cấu trúc: Khái niệm -> Ví dụ thực tế -> Kinh nghiệm cá nhân. Trung thực khi không biết."],
        ["6. Chuẩn bị thêm", "Chuẩn bị 1-2 project automation để demo & nói rõ vai trò bản thân."],
        ["7. Tổng số", "Hơn 110 câu hỏi chia theo chủ đề, có cột độ khó để luyện theo cấp."],
    ]
    make_sheet(wb, "Huong_Dan", "CÂU HỎI PHỎNG VẤN AUTOMATION TEST – HƯỚNG DẪN SỬ DỤNG",
               ["Mục", "Nội dung"], intro, [22, 118], first=True)

    basic = [
        ["Bạn hiểu automation testing là gì?", "Dùng tool/script chạy test tự động & so kết quả thực tế với mong đợi.", "Junior"],
        ["Khác biệt manual và automation?", "Manual làm tay, linh hoạt, hợp UX/ad-hoc; automation nhanh, lặp lại, hợp regression.", "Junior"],
        ["Khi nào nên automation?", "Test lặp lại nhiều, regression, smoke, data lớn, chạy thường xuyên, ổn định.", "Junior"],
        ["Khi nào KHÔNG nên automation?", "Test 1 lần, UI đổi liên tục, kiểm thử cảm tính/UX, thời gian gấp.", "Junior"],
        ["Ưu điểm của automation?", "Nhanh, chính xác, chạy lại được, tiết kiệm về lâu dài, chạy ban đêm/CI.", "Junior"],
        ["Hạn chế của automation?", "Chi phí ban đầu cao, cần kỹ năng code, tốn bảo trì, không thay thế hết manual.", "Junior"],
        ["SDLC và STLC là gì?", "Vòng đời phát triển phần mềm và vòng đời kiểm thử.", "Junior"],
        ["Test case gồm những gì?", "ID, tiêu đề, tiền điều kiện, bước, dữ liệu, kết quả mong đợi, thực tế, trạng thái.", "Junior"],
        ["Severity vs Priority?", "Severity: nghiêm trọng kỹ thuật; Priority: mức ưu tiên sửa theo nghiệp vụ.", "Junior"],
        ["Smoke vs Sanity vs Regression?", "Smoke: chức năng chính; Sanity: kiểm nhanh phần vừa sửa; Regression: chạy lại đảm bảo không hỏng cũ.", "Junior"],
        ["Test Pyramid là gì?", "Nhiều Unit > vừa API > ít UI; giúp test nhanh, ổn định, rẻ.", "Middle"],
        ["Vòng đời 1 bug?", "New -> Assigned -> Open -> Fixed -> Retest -> Closed/Reopened.", "Junior"],
        ["Bạn chọn test case nào để automation?", "Ổn định, lặp lại nhiều, quan trọng, tốn công làm tay, data-driven.", "Middle"],
        ["ROI của automation đo thế nào?", "Thời gian/công sức tiết kiệm so với chi phí xây & bảo trì script.", "Senior"],
    ]
    make_sheet(wb, "1_CoBan_LyThuyet", "PHỎNG VẤN – PHẦN CƠ BẢN & LÝ THUYẾT",
               ["Câu hỏi", "Gợi ý trả lời", "Cấp độ"], basic, [50, 80, 12])

    sel = [
        ["Selenium WebDriver là gì?", "Thư viện điều khiển trình duyệt để tự động test web UI.", "Junior"],
        ["Các loại locator trong Selenium?", "id, name, className, tagName, linkText, partialLinkText, cssSelector, xpath.", "Junior"],
        ["Thứ tự ưu tiên locator?", "id > name > css selector > xpath; ưu tiên ổn định & duy nhất.", "Junior"],
        ["XPath vs CSS Selector?", "CSS nhanh & gọn; XPath mạnh hơn (đi ngược cây, theo text).", "Junior"],
        ["XPath absolute vs relative?", "Absolute từ gốc (/html/...), dễ vỡ; relative (//) ngắn & ổn định hơn.", "Junior"],
        ["Các loại wait?", "Implicit (chung), Explicit (theo điều kiện), Fluent (explicit + polling).", "Junior"],
        ["Vì sao không nên Thread.sleep?", "Cố định thời gian, chậm & dễ flaky; dùng explicit wait theo điều kiện.", "Junior"],
        ["Xử lý dropdown thế nào?", "Dùng class Select: selectByVisibleText/Value/Index.", "Junior"],
        ["Xử lý alert/popup?", "switch_to.alert + accept/dismiss/sendKeys.", "Junior"],
        ["Xử lý iframe?", "switch_to.frame() rồi switch_to.default_content().", "Junior"],
        ["Xử lý nhiều tab/cửa sổ?", "Lấy window_handles và switch_to.window().", "Middle"],
        ["findElement vs findElements?", "Một trả về 1 phần tử (lỗi nếu không có); nhiều trả về list (rỗng nếu không có).", "Junior"],
        ["StaleElementReferenceException là gì?", "Phần tử đã thay đổi/không còn trong DOM; cần tìm lại phần tử.", "Middle"],
        ["NoSuchElementException xử lý sao?", "Kiểm tra locator, thêm explicit wait, đảm bảo phần tử đã render.", "Junior"],
        ["JavascriptExecutor dùng khi nào?", "Scroll, click phần tử bị che, set value, khi cách thường không được.", "Middle"],
        ["Chụp ảnh màn hình khi lỗi?", "TakesScreenshot / save_screenshot trong listener khi test fail.", "Middle"],
        ["Cross-browser testing thế nào?", "Tham số hoá driver, dùng Selenium Grid/cloud.", "Middle"],
        ["Headless là gì, lợi ích?", "Chạy không giao diện, nhanh hơn, hợp CI.", "Middle"],
        ["Selenium Grid là gì?", "Chạy test song song trên nhiều máy/trình duyệt.", "Senior"],
        ["Playwright khác Selenium?", "Playwright auto-wait, nhanh, đa tab/context tốt, có trace viewer.", "Middle"],
        ["Xử lý dynamic element (id đổi liên tục)?", "Dùng xpath theo text/attribute ổn định, contains(), không dựa id động.", "Middle"],
        ["Drag & drop, hover làm sao?", "Dùng Actions/ActionChains.", "Middle"],
    ]
    make_sheet(wb, "2_Selenium_Web", "PHỎNG VẤN – SELENIUM / WEB AUTOMATION",
               ["Câu hỏi", "Gợi ý trả lời", "Cấp độ"], sel, [50, 80, 12])

    apiq = [
        ["API testing là gì?", "Kiểm thử trực tiếp tầng API (logic/dữ liệu) không qua giao diện.", "Junior"],
        ["REST API là gì?", "Kiến trúc giao tiếp qua HTTP dùng method & resource.", "Junior"],
        ["Các HTTP method?", "GET, POST, PUT, PATCH, DELETE và ý nghĩa từng cái.", "Junior"],
        ["PUT vs PATCH?", "PUT cập nhật toàn bộ resource; PATCH cập nhật một phần.", "Junior"],
        ["Status code quan trọng?", "200, 201, 204, 301, 400, 401, 403, 404, 500.", "Junior"],
        ["200 vs 201 vs 204?", "200 OK; 201 Created; 204 No Content (thành công, không body).", "Junior"],
        ["401 vs 403?", "401 chưa xác thực; 403 đã xác thực nhưng không có quyền.", "Junior"],
        ["Trong API test, kiểm tra gì?", "Status code, response body, header, schema, thời gian phản hồi, lỗi.", "Junior"],
        ["JSON Schema validation là gì?", "Kiểm tra cấu trúc/định dạng response đúng chuẩn.", "Middle"],
        ["Authentication các kiểu?", "Basic, Bearer token (JWT), API key, OAuth2.", "Middle"],
        ["JWT là gì?", "JSON Web Token: token mã hoá thông tin xác thực dạng header.payload.signature.", "Middle"],
        ["Postman test script viết sao?", "Dùng pm.test + pm.expect để assert status/body.", "Junior"],
        ["Chạy Postman trên CI?", "Xuất collection chạy bằng Newman trong pipeline.", "Middle"],
        ["RestAssured cú pháp cơ bản?", "given().when().get().then().statusCode(200).body(...).", "Middle"],
        ["Request chaining là gì?", "Lấy dữ liệu (token/id) từ response trước dùng cho request sau.", "Middle"],
        ["Vì sao API test ưu tiên hơn UI?", "Nhanh, ổn định, ít flaky, gần logic nghiệp vụ, dễ vào CI.", "Middle"],
        ["Mock API dùng khi nào?", "Khi backend chưa xong hoặc cần cô lập phụ thuộc (WireMock, Postman mock).", "Senior"],
        ["Test API bảo mật cơ bản?", "Kiểm tra auth, phân quyền, SQL injection, dữ liệu nhạy cảm, rate limit.", "Senior"],
        ["Idempotent là gì?", "Gọi nhiều lần cho cùng kết quả (GET, PUT, DELETE) khác POST.", "Senior"],
    ]
    make_sheet(wb, "3_API_Testing", "PHỎNG VẤN – API TESTING",
               ["Câu hỏi", "Gợi ý trả lời", "Cấp độ"], apiq, [50, 80, 12])

    fw = [
        ["Page Object Model là gì?", "Mẫu thiết kế: mỗi trang = 1 class chứa locator + action, tách khỏi test.", "Junior"],
        ["Lợi ích của POM?", "Dễ bảo trì, tái sử dụng, giảm trùng lặp, locator tập trung.", "Junior"],
        ["Page Factory là gì?", "Cơ chế khởi tạo phần tử bằng @FindBy trong Selenium Java.", "Middle"],
        ["Cấu trúc 1 framework tốt?", "POM, runner, data-driven, config, utils, report, log, CI, README.", "Middle"],
        ["Data-driven testing là gì?", "Một test chạy nhiều bộ data từ Excel/CSV/JSON/DB.", "Junior"],
        ["Keyword-driven là gì?", "Test mô tả bằng từ khoá/hành động (vd Robot Framework).", "Middle"],
        ["BDD là gì? Cucumber hoạt động sao?", "Viết test Gherkin Given/When/Then; map sang step definition code.", "Middle"],
        ["TestNG hơn JUnit ở điểm nào?", "Group, dataProvider, parallel, dependsOnMethods, listener mạnh hơn.", "Middle"],
        ["Annotation TestNG hay dùng?", "@Test, @BeforeMethod/Class/Suite, @AfterMethod, @DataProvider.", "Middle"],
        ["Quản lý test data thế nào?", "Tách ra file/DB, tạo & dọn data trong setup/teardown, tránh hard-code.", "Middle"],
        ["Làm sao giảm flaky test?", "Explicit wait, test độc lập, data ổn định, locator tốt, retry hợp lý.", "Middle"],
        ["Retry test fail nên không?", "Có thể retry cho lỗi hạ tầng, nhưng phải điều tra gốc rễ, không lạm dụng.", "Senior"],
        ["Quản lý cấu hình nhiều môi trường?", "File config theo env (dev/staging/prod), biến môi trường, profile.", "Middle"],
        ["Parallel execution làm sao?", "TestNG parallel/PyTest-xdist, Grid; đảm bảo test độc lập, thread-safe.", "Senior"],
        ["ThreadLocal WebDriver để làm gì?", "Giữ driver riêng mỗi thread khi chạy song song.", "Senior"],
        ["Làm sao chọn tool cho dự án?", "Theo công nghệ app, kỹ năng team, ngân sách, mobile/web/api, cộng đồng.", "Senior"],
        ["Chiến lược automation cho dự án mới?", "Xác định phạm vi, chọn tool, dựng framework, ưu tiên smoke/regression, vào CI.", "Senior"],
        ["Đo lường chất lượng bộ test?", "Coverage, tỉ lệ pass, độ ổn định (flaky rate), thời gian chạy, bug thoát.", "Senior"],
        ["Bảo trì test khi UI đổi liên tục?", "POM tập trung locator, dùng locator ổn định, review thường xuyên.", "Senior"],
    ]
    make_sheet(wb, "4_Framework_Design", "PHỎNG VẤN – FRAMEWORK & DESIGN PATTERN",
               ["Câu hỏi", "Gợi ý trả lời", "Cấp độ"], fw, [50, 80, 12])

    ci = [
        ["CI/CD là gì?", "Tích hợp & triển khai liên tục: tự động build, test, deploy.", "Junior"],
        ["Lợi ích CI/CD với tester?", "Phát hiện lỗi sớm, test chạy thường xuyên & tự động, phản hồi nhanh.", "Junior"],
        ["Pipeline gồm bước nào?", "Checkout -> build -> test -> report -> deploy.", "Junior"],
        ["Git command hay dùng?", "clone, add, commit, push, pull, branch, checkout, merge, rebase.", "Junior"],
        ["Merge vs Rebase?", "Merge giữ lịch sử rẽ nhánh; rebase làm lịch sử thẳng, gọn hơn.", "Middle"],
        ["Pull request là gì?", "Yêu cầu merge có review trước khi vào nhánh chính.", "Junior"],
        ["Resolve conflict thế nào?", "Sửa file xung đột, chọn nội dung đúng, add & commit lại.", "Middle"],
        ["GitHub Actions cấu hình ở đâu?", "File YAML trong .github/workflows.", "Middle"],
        ["Jenkins là gì?", "Công cụ CI/CD tạo job/pipeline tự động chạy test.", "Middle"],
        ["Trigger test tự động khi nào?", "Theo push, pull request, lịch (nightly), hoặc thủ công.", "Middle"],
        ["Tích hợp report vào CI?", "Xuất Allure/JUnit XML, hiển thị kết quả, gửi thông báo.", "Middle"],
        ["Docker giúp gì cho automation?", "Môi trường test đồng nhất, chạy Grid, dễ scale.", "Senior"],
        ["Quản lý secret trong CI?", "Dùng CI secrets/credentials, không hard-code password/token.", "Senior"],
        ["Chạy test song song trên CI giảm thời gian?", "Chia test, parallel/matrix build, Grid/cloud.", "Senior"],
        ["Nightly build để làm gì?", "Chạy full regression ban đêm, sáng có report.", "Middle"],
    ]
    make_sheet(wb, "5_CICD_Git", "PHỎNG VẤN – CI/CD, GIT & DEVOPS",
               ["Câu hỏi", "Gợi ý trả lời", "Cấp độ"], ci, [50, 80, 12])

    coding = [
        ["Đảo ngược 1 chuỗi không dùng hàm reverse", "Viết vòng lặp ghép ký tự từ cuối về đầu.", "Junior"],
        ["Kiểm tra chuỗi palindrome", "So sánh chuỗi với chuỗi đảo, hoặc 2 con trỏ.", "Junior"],
        ["Đếm số lần xuất hiện ký tự trong chuỗi", "Dùng dict/map đếm tần suất.", "Junior"],
        ["Tìm số lớn nhất/nhỏ nhất trong mảng", "Duyệt 1 lần giữ max/min.", "Junior"],
        ["FizzBuzz", "Lặp 1..n, chia hết 3->Fizz, 5->Buzz, cả hai->FizzBuzz.", "Junior"],
        ["Loại bỏ phần tử trùng trong list", "Dùng set hoặc duyệt & kiểm tra tồn tại.", "Junior"],
        ["Đọc dữ liệu từ file Excel/CSV để test", "Apache POI/openpyxl/csv reader, trả về list bộ data.", "Middle"],
        ["Viết hàm login dùng POM", "LoginPage có method login(user, pass) trả về trang kế tiếp.", "Middle"],
        ["Viết explicit wait cho 1 nút", "WebDriverWait + ExpectedConditions.elementToBeClickable.", "Middle"],
        ["Sắp xếp list theo 1 trường (object)", "Dùng sort với key/comparator.", "Middle"],
        ["Tìm phần tử trùng nhau (2 list)", "Dùng set giao nhau.", "Middle"],
        ["Đếm từ trong câu", "Tách theo khoảng trắng rồi đếm.", "Junior"],
    ]
    make_sheet(wb, "6_Coding_Test", "PHỎNG VẤN – BÀI CODING THƯỜNG GẶP (LUYỆN TAY)",
               ["Đề bài", "Hướng giải", "Cấp độ"], coding, [54, 76, 12])

    scen = [
        ["Test fail trên CI nhưng local pass, làm sao?", "Kiểm tra môi trường, data, wait/timing, headless, độ phân giải, song song.", "Middle"],
        ["Test bị flaky, bạn xử lý thế nào?", "Tìm nguyên nhân (wait/data/locator), fix gốc, thêm explicit wait, retry hợp lý.", "Middle"],
        ["UI thay đổi liên tục, framework bạn chịu ảnh hưởng sao?", "POM tập trung locator, dùng locator ổn định, sửa 1 chỗ.", "Middle"],
        ["Phải test 1 trang chưa có API doc, làm gì?", "Dùng DevTools/Network xem request, hỏi dev, dùng exploratory.", "Middle"],
        ["Deadline gấp, không kịp automation hết, ưu tiên gì?", "Ưu tiên smoke + critical path + regression rủi ro cao.", "Senior"],
        ["Sếp muốn 100% automation, bạn tư vấn sao?", "Giải thích không khả thi/không hiệu quả; áp dụng test pyramid & risk-based.", "Senior"],
        ["Test mất 4 giờ chạy, giảm thế nào?", "Parallel, đẩy bớt xuống API/unit, Grid/cloud, bỏ test trùng.", "Senior"],
        ["Bạn kế thừa framework cũ rối, làm gì?", "Đánh giá, refactor dần sang POM, thêm report/CI, viết tài liệu.", "Senior"],
        ["Tester & dev tranh cãi 1 bug, bạn xử lý?", "Đưa bằng chứng (log, ảnh, bước tái hiện), giữ khách quan, dựa yêu cầu.", "Middle"],
        ["Làm sao thuyết phục team đầu tư automation?", "Chỉ ra ROI, giảm thời gian regression, tăng độ tin cậy, demo nhỏ.", "Senior"],
    ]
    make_sheet(wb, "7_Tinh_Huong", "PHỎNG VẤN – CÂU HỎI TÌNH HUỐNG (SCENARIO)",
               ["Tình huống", "Hướng trả lời", "Cấp độ"], scen, [54, 76, 12])

    hr = [
        ["Giới thiệu bản thân?", "Ngắn gọn: kinh nghiệm, kỹ năng automation chính, dự án nổi bật, mục tiêu.", "Mọi cấp"],
        ["Điểm mạnh / điểm yếu?", "Trung thực; điểm yếu kèm cách bạn đang cải thiện.", "Mọi cấp"],
        ["Dự án automation bạn tự hào nhất?", "Nêu vấn đề, giải pháp, vai trò bạn, kết quả đo được.", "Mọi cấp"],
        ["Bạn học công nghệ mới thế nào?", "Tài liệu chính thức, làm project nhỏ, cộng đồng, kiên trì.", "Mọi cấp"],
        ["Vì sao chọn nghề automation test?", "Đam mê chất lượng + lập trình, cơ hội phát triển, nhu cầu thị trường.", "Junior"],
        ["Xử lý áp lực deadline thế nào?", "Ưu tiên theo rủi ro, giao tiếp sớm, quản lý thời gian.", "Mọi cấp"],
        ["Bất đồng với đồng nghiệp, bạn làm gì?", "Lắng nghe, dựa dữ liệu/yêu cầu, hướng tới mục tiêu chung.", "Mọi cấp"],
        ["Mục tiêu 3-5 năm tới?", "Lộ trình rõ: senior/automation lead/SDET/QA manager.", "Mọi cấp"],
        ["Bạn có câu hỏi gì cho chúng tôi?", "Hỏi về team, quy trình test, tech stack, cơ hội phát triển.", "Mọi cấp"],
        ["Vì sao rời công ty cũ?", "Tích cực, hướng phát triển, không nói xấu công ty cũ.", "Mọi cấp"],
    ]
    make_sheet(wb, "8_Hanh_Vi_HR", "PHỎNG VẤN – CÂU HỎI HÀNH VI / HR",
               ["Câu hỏi", "Gợi ý trả lời", "Cấp độ"], hr, [50, 80, 12])

    fn = "TaiLieu_CauHoiPhongVan_AutoTest.xlsx"
    wb.save(fn)
    return fn


if __name__ == "__main__":
    f1 = build_automation()
    f2 = build_istqb()
    f3 = build_interview()
    print("Da tao xong 3 file:")
    print(" -", f1)
    print(" -", f2)
    print(" -", f3)
