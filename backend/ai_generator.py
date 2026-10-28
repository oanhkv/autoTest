"""Sinh bộ test case từ DOM trang web + tài liệu đặc tả, theo bộ checklist QA chuẩn.

Nguồn AI chọn qua biến PROVIDER trong .env:
- "ollama"    : mô hình chạy local, miễn phí (mặc định). Khuyến nghị qwen2.5:1.5b trở lên.
- "anthropic" : Claude API cloud, nhanh & chất lượng cao hơn nhưng tính phí.

Cột test case (khớp template thực tế của người dùng):
STT, Mã TC, Loại tài khoản, Màn hình, Chức năng, Chức năng con, UI/Function,
Tiền điều kiện, Bước tái hiện, Kết quả mong muốn, Kết quả thực tế, Tình trạng,
Dẫn link bug (Clickup), Ngày test.
"""
import json
import os
import re
import time
import urllib.error
import urllib.request

# Các trường do AI sinh (4 cột kết quả test để trống cho tester tự điền)
TEST_CASE_FIELDS = [
    "id",            # Mã TC
    "account_type",  # Loại tài khoản (Admin / User / Khách...)
    "screen",        # Màn hình
    "function",      # Chức năng
    "sub_function",  # Chức năng con
    "ui_function",   # "UI" hoặc "Function"
    "precondition",  # Tiền điều kiện
    "steps",         # Bước tái hiện
    "expected",      # Kết quả mong muốn
]

# Bộ checklist quan điểm kiểm thử CHUẨN, chắt lọc từ QA_Common_checklists_VI (Sun* style)
UNIVERSAL_CHECKLIST = """BỘ QUAN ĐIỂM KIỂM THỬ CHUẨN (áp dụng cho mọi chức năng web):
- Hiển thị màn hình: tiêu đề, nhãn, nút, bố cục, thông báo; ô mật khẩu hiển thị dạng ●; có placeholder.
- Trường bắt buộc để trống -> hiển thị thông báo lỗi tương ứng trên TỪNG trường.
- Sai định dạng (email/số điện thoại/ngày/số) -> báo lỗi tương ứng.
- Giá trị biên: độ dài tối thiểu/tối đa, min-1/min/max/max+1, số 0/âm, ngày quá khứ/tương lai.
- TRIM khoảng trắng đầu/cuối; chuỗi chỉ toàn dấu cách -> coi như rỗng.
- Dữ liệu hợp lệ -> thao tác thành công + lưu DB đúng + hiển thị thông báo thành công.
- Bấm nút Gửi/Lưu nhiều lần liên tiếp -> chỉ tạo 1 bản ghi (chống double-submit).
- Dữ liệu trùng/đã tồn tại -> báo lỗi, không lưu.
- Ký tự đặc biệt, unicode/emoji, input siêu dài vẫn lưu & hiển thị đúng.
- Bảo mật: SQL injection ('; DROP TABLE--), XSS (<script>alert(1)</script>), không lộ thông tin nhạy cảm.
- Phân quyền: tài khoản không đủ quyền KHÔNG truy cập được chức năng/URL của vai trò khác.
- Phiên đăng nhập: sai nhiều lần -> khóa; session hết hạn -> tự đăng xuất.
- Khi xảy ra lỗi -> KHÔNG lưu DB, KHÔNG gửi email/SMS.
- Tương thích: đa trình duyệt; responsive mobile/tablet; zoom 200%.
- Hiệu năng: thời gian phản hồi hợp lý; dữ liệu lớn không treo.
- API: kiểm mã trạng thái (200/400/401/403/500), định dạng JSON, xác thực token, validate phía server, lỗi/timeout.
- Responsive: hiển thị đúng trên mobile/tablet/desktop, xoay màn hình, zoom, menu hamburger, vùng chạm đủ lớn.

THEO TỪNG THÀNH PHẦN (nếu trang có thành phần đó):
- Ô tìm kiếm: tìm với giá trị mặc định/rỗng (trả tất cả), giá trị tồn tại/không tồn tại, khớp một phần/chính xác,
  ký tự đặc biệt/tiếng Anh/số, TRIM khoảng trắng, độ dài tối đa/tối đa+1, dữ liệu đã xóa không hiển thị.
- Phân trang: số bản ghi/trang đúng cấu hình; hiển thị khi 0/1/N/N+1 bản ghi; nút Previous/Next/First/Last
  ở trang đầu/giữa/cuối; nhấn F5 giữ đúng trang; thời gian tải trang.
- Upload/Download file: định dạng hợp lệ/không hợp lệ; dung lượng tối đa/tối đa+1; kích thước (cao/rộng) biên;
  tên file dài/ký tự đặc biệt; kéo-thả; đổi tên; xóa; xem trước (preview); tải xuống đúng nội dung.
- Combo box/Dropdown: giá trị mặc định; đúng thứ tự danh sách; gợi ý khi gõ (khớp đầu/giữa/đầy đủ);
  chọn rỗng; nhập ký tự đặc biệt; không có kết quả.
- Datepicker/Chọn ngày: ngày hợp lệ; quá khứ/tương lai; khoảng ngày (từ > đến); định dạng; ngày biên
  (cuối tháng, năm nhuận 29/2); nhập tay sai định dạng.
- Bảng/Danh sách: sắp xếp tăng/giảm theo cột; cột rỗng; nhiều dữ liệu; chọn nhiều dòng; thao tác hàng loạt."""

ACCOUNT_HINT = ('Loại tài khoản ví dụ: "Admin", "User", "Khách (chưa đăng nhập)" '
                "— suy ra từ ngữ cảnh trang; nếu không rõ để \"User\".")

SCREEN_HINT = ('Nếu đặc tả mô tả NHIỀU màn hình/chức năng, PHẢI sinh test case cho TỪNG màn hình '
               'và ghi đúng tên màn hình vào trường "screen" (ví dụ "Đăng nhập", "Quản lý sản phẩm", '
               '"Đơn hàng"). Đừng bỏ sót màn hình nào.')

ORDER_HINT = (
    "CẤU TRÚC & THỨ TỰ bộ test case PHẢI theo ĐÚNG 5 PHẦN dưới đây, sinh lần lượt theo thứ tự này, "
    'và đặt trường "function" = đúng tên phần (hoặc "Check event - <tên sự kiện>"):\n'
    '1) "Transition" (Điều hướng vào màn) — 3-4 case: từ màn nào điều hướng tới màn này; '
    "truy cập URL khi CHƯA đăng nhập và khi ĐÃ đăng nhập (ui_function=Function).\n"
    '2) "UI" (Đúng so với thiết kế/spec) — 1-2 case: màu sắc các thành phần, font-size, layout, căn lề '
    "(ui_function=UI).\n"
    '3) "Initial" (Khởi tạo - hiển thị ban đầu) — 2-3 case: kiểm Header có gì, Title, Content, Bộ lọc, '
    "ô Tìm kiếm, các Button hiển thị đúng (ui_function=UI).\n"
    '4) "Check data" (Kiểm dữ liệu): Default data (spec hiển thị dữ liệu thế nào, đúng dữ liệu DB); '
    "Combine data — Add (hiển thị danh sách mới nhất), Xóa (dữ liệu bị xóa & list cập nhật), Sửa "
    "(ui_function=Function).\n"
    '5) "Check event - <tên sự kiện>" (TẤT CẢ thao tác trên màn — phần NHIỀU nhất): với MỖI nút/sự kiện '
    "(Submit, Tìm kiếm, Lọc, Thêm, Xóa...): kiểm Trường bắt buộc → Format/Policy → Max length → Normal case "
    "(happy) → Other case (SQL injection, bấm nhiều lần, responsive...). Liệt kê sự kiện từ TRÊN xuống DƯỚI màn hình; "
    "kiểm từ nhỏ đến lớn (lớn bao gồm nhỏ).\n"
    "TRONG mỗi phần: case UI để TRƯỚC, Function sau. KHÔNG để trùng lặp giữa các phần.")

TECHNIQUES = (
    'ÁP DỤNG đầy đủ các KỸ THUẬT THIẾT KẾ TEST để không lọt trường hợp nào: '
    'phân vùng tương đương (Equivalence Partitioning), phân tích giá trị biên (Boundary Value Analysis: '
    'min-1/min/max/max+1), bảng quyết định (Decision Table cho tổ hợp điều kiện), chuyển trạng thái '
    '(State Transition cho luồng nhiều bước), đoán lỗi (Error Guessing), kiểm thử cặp (Pairwise).')

DEDUP_HINT = ('TUYỆT ĐỐI KHÔNG tạo test case TRÙNG LẶP: nếu hai case có cùng các bước thực hiện và cho cùng '
              'một kết quả thì CHỈ GIỮ MỘT (tránh tốn tài nguyên). Mỗi case phải kiểm tra một điều khác biệt.')

SUBSCREEN_HINT = (
    "PHẠM VI MÀN HÌNH: với nút/hành động MỞ RA một màn hình/form/popup KHÁC (ví dụ Thêm mới, Sửa, Chi tiết, "
    "Cấu hình...): ở MÀN HIỆN TẠI chỉ test việc click có ĐIỀU HƯỚNG/HIỂN THỊ ĐÚNG form/màn đó hay không "
    "(thường 1 case trong 'Check event - <tên nút>'). KHÔNG test sâu các trường bên trong màn/form con — "
    "đó là MỘT MÀN RIÊNG, phải test riêng. KHÔNG trộn case của màn con vào màn cha.")

EXPECTED_DETAIL = (
    'CỘT "Kết quả mong muốn" phải CHI TIẾT, BÁM SÁT từng màn hình. Với case kiểm UI/hiển thị (UI, Initial), '
    'viết dạng DANH SÁCH gạch đầu dòng, MỖI Ý XUỐNG DÒNG (dùng ký tự \\n), nêu rõ và cụ thể:\n'
    '  • Kích thước thành phần (px), cỡ chữ (px), kiểu chữ/font, độ đậm, có đồng nhất không;\n'
    '  • Màu sắc thành phần (mã màu nếu suy được), độ tương phản;\n'
    '  • Text/nhãn hiển thị chính xác, icon đứng trước/sau text (nếu có);\n'
    '  • Tên đầy đủ trên button, nội dung placeholder của TỪNG ô nhập, căn lề/khoảng cách.\n'
    'Ví dụ expected: "- Tiêu đề \\"Đăng nhập\\": font 20px, đậm, màu #1F3864, căn giữa\\n'
    '- Ô Email: rộng ~320px, viền xám #CCC, placeholder \\"Nhập email của bạn\\"\\n'
    '- Nút \\"Đăng nhập\\": nền xanh #2F5597, chữ trắng 14px, có icon mũi tên ở sau".')

OUTPUT_SHAPE = (
    '{"test_cases":[{"id":"","account_type":"","screen":"","function":"","sub_function":"",'
    '"ui_function":"","precondition":"","steps":"","expected":""}]}'
)
OUTPUT_RULES = (
    "Trả về DUY NHẤT một JSON đúng dạng: " + OUTPUT_SHAPE + "\n"
    "- Mỗi test case đủ 9 khóa, mọi giá trị là CHUỖI (không lồng object/mảng).\n"
    '- "ui_function" chỉ là "UI" hoặc "Function".\n'
    '- "steps" PHẢI chi tiết, đánh số từng thao tác cụ thể (mở màn hình nào, nhập dữ liệu gì, '
    'bấm nút nào...), tối thiểu 2-5 bước: "1. ...\\n2. ...\\n3. ...".\n'
    '- "expected" mô tả kết quả CỤ THỂ, đo được (nêu rõ thông báo, màn hình hiển thị, dữ liệu lưu...).\n'
    '- "precondition" ghi rõ điều kiện trước khi test (đã đăng nhập, đã có dữ liệu...).\n'
    "- TẤT CẢ nội dung PHẢI viết bằng TIẾNG VIỆT CÓ DẤU, văn phong tài liệu test chuyên nghiệp. "
    "TUYỆT ĐỐI KHÔNG viết tiếng Anh (chỉ giữ thuật ngữ kỹ thuật: SQL, XSS, URL, API, email...).\n"
    "- CHỈ trả JSON, không giải thích, không markdown."
)


# ===================== Provider (nguồn AI) =====================
class Provider:
    def __init__(self):
        self.kind = os.environ.get("PROVIDER", "ollama").strip().lower()
        if self.kind == "gemini":
            self.api_key = os.environ.get("GEMINI_API_KEY")
            if not self.api_key:
                raise ValueError("PROVIDER=gemini nhưng chưa cấu hình GEMINI_API_KEY trong .env")
            self.model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
            self.max_workers = 2  # free tier giới hạn ~10-15 req/phút -> gọi ít đồng thời cho đỡ 429
        elif self.kind == "anthropic":
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("PROVIDER=anthropic nhưng chưa cấu hình ANTHROPIC_API_KEY trong .env")
            from anthropic import Anthropic
            self.client = Anthropic(api_key=api_key)
            self.model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")
            self.max_workers = 4
        else:
            self.kind = "ollama"
            self.host = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
            self.model = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")
            self.max_workers = 1
        # Chỉ model local nhỏ mới cần prompt ngắn gọn; cloud (gemini/anthropic) dùng prompt đầy đủ
        self.compact = self.kind == "ollama"

    def complete(self, system: str, user: str, max_tokens: int = 3000, image_b64: str = None,
                 json_mode: bool = True) -> str:
        """json_mode=True: ép model trả JSON (cho sinh test case).
        json_mode=False: trả VĂN BẢN THUẦN (cho sinh tài liệu .md / code Playwright)."""
        if self.kind == "gemini":
            return self._complete_gemini(system, user, max_tokens, image_b64, json_mode)
        if self.kind == "anthropic":
            content = [{"type": "text", "text": user}]
            if image_b64:
                content.insert(0, {"type": "image", "source": {
                    "type": "base64", "media_type": "image/jpeg", "data": image_b64}})
            msg = self.client.messages.create(
                model=self.model, max_tokens=max_tokens, system=system,
                messages=[{"role": "user", "content": content}],
            )
            return "".join(b.text for b in msg.content if b.type == "text")
        return self._complete_ollama(system, user, max_tokens, json_mode)  # Ollama text-only

    def _complete_gemini(self, system: str, user: str, max_tokens: int, image_b64: str,
                         json_mode: bool = True) -> str:
        parts = [{"text": user}]
        if image_b64:
            parts.append({"inline_data": {"mime_type": "image/jpeg", "data": image_b64}})
        gen_config = {
            "temperature": 0.4,
            "maxOutputTokens": max_tokens,
            # Tắt "thinking" để dồn token cho kết quả (model 2.5 mặc định bật, gây rỗng)
            "thinkingConfig": {"thinkingBudget": 0},
        }
        if json_mode:
            gen_config["responseMimeType"] = "application/json"
        payload = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"parts": parts}],
            "generationConfig": gen_config,
        }
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{self.model}:generateContent")
        data = json.dumps(payload).encode("utf-8")
        last_detail = ""
        # Tự thử lại khi Gemini quá tải (503) hoặc giới hạn tốc độ (429) tạm thời
        for attempt in range(6):
            # API key gửi qua header (không đặt trên URL để tránh lộ key trong log/proxy)
            req = urllib.request.Request(
                url, data=data,
                headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key})
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    body = json.loads(resp.read().decode("utf-8"))
                cands = body.get("candidates", [])
                if not cands:
                    raise ValueError(f"Gemini không trả về kết quả: {str(body)[:200]}")
                parts = cands[0].get("content", {}).get("parts", [])
                return "".join(p.get("text", "") for p in parts)
            except urllib.error.HTTPError as exc:
                last_detail = exc.read().decode("utf-8", errors="ignore")
                # Quota ngày/free-tier không thể giải quyết bằng retry ngắn.
                # Trả lỗi ngay để các luồng có fallback local không phải chờ
                # 75 giây (5 + 10 + 15 + 20 + 25).
                quota_text = last_detail.lower()
                if exc.code == 429 and (
                    "quota exceeded" in quota_text
                    or "free_tier" in quota_text
                    or "current quota" in quota_text
                ):
                    raise ValueError(f"Gemini hết quota: {last_detail[:600]}")
                if exc.code in (429, 503) and attempt < 5:
                    time.sleep(5 * (attempt + 1))  # 5,10,15,20,25s — chờ qua cửa sổ giới hạn/phút
                    continue
                raise ValueError(f"Gemini lỗi HTTP {exc.code}: {last_detail[:600]}")
            except urllib.error.URLError as exc:
                raise ValueError(f"Không gọi được Gemini (kiểm tra mạng/API key): {exc}")
        raise ValueError(f"Gemini đang quá tải, đã thử lại nhiều lần. Chi tiết: {last_detail[:400]}")

    def _complete_ollama(self, system: str, user: str, max_tokens: int,
                         json_mode: bool = True) -> str:
        payload = {
            "model": self.model, "stream": False,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "options": {"temperature": 0.4, "num_predict": max_tokens},
        }
        if json_mode:
            payload["format"] = "json"  # chỉ ép JSON khi sinh test case
        req = urllib.request.Request(
            self.host + "/api/chat", data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=900) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise ValueError(
                f"Không kết nối được Ollama ở {self.host}. Hãy chắc Ollama đang chạy và đã tải "
                f"model '{self.model}' (ollama pull {self.model}). Chi tiết: {exc}"
            )
        return body.get("message", {}).get("content", "")


# ===================== Tiện ích JSON =====================
def _extract_json(text: str):
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    s, e = text.find("["), text.rfind("]")
    if s != -1 and e != -1:
        return json.loads(text[s : e + 1])
    raise json.JSONDecodeError("Khong tim thay JSON", text, 0)


def _salvage_objects(text: str) -> list:
    """Vớt mọi object {...} hoàn chỉnh, kể cả khi JSON tổng bị cắt ngang (model nhỏ)."""
    objs, stack, in_str, esc = [], [], False, False
    for i, ch in enumerate(text):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            stack.append(i)
        elif ch == "}" and stack:
            start = stack.pop()
            try:
                o = json.loads(text[start : i + 1])
            except json.JSONDecodeError:
                continue
            if isinstance(o, dict):
                objs.append(o)
    return [o for o in objs if o.get("steps") or o.get("expected") or o.get("function")]


def _call_model(provider: "Provider", system: str, user: str, max_tokens: int = 3000,
                image_b64: str = None) -> list:
    raw = provider.complete(system, user, max_tokens, image_b64)
    result = None
    try:
        result = _extract_json(raw)
    except json.JSONDecodeError:
        result = None
    if isinstance(result, dict):
        items = None
        for key in ("test_cases", "testcases", "cases", "data", "items"):
            if isinstance(result.get(key), list):
                items = result[key]
                break
        if items is None:
            items = [result] if result.get("steps") or result.get("function") else []
        result = items
    cases = [c for c in result if isinstance(c, dict)] if isinstance(result, list) else []
    if not cases:
        cases = _salvage_objects(raw)
    return cases


def _build_context(url: str, dom_summary: str, spec: str, max_dom: int = 0) -> str:
    if max_dom and len(dom_summary) > max_dom:
        dom_summary = dom_summary[:max_dom] + "\n...(rút gọn)"
    spec_block = spec.strip() or "(Không có tài liệu đặc tả — hãy suy luận từ giao diện)"
    return (f"URL trang: {url}\n\n=== CẤU TRÚC GIAO DIỆN (trích từ DOM) ===\n{dom_summary}\n\n"
            f"=== TÀI LIỆU ĐẶC TẢ YÊU CẦU ===\n{spec_block}")


# ===================== Sinh test case =====================
def _comprehensive_system(thorough: bool, compact: bool = False) -> str:
    if compact:
        count = "Sinh khoảng 14-16 test case, mỗi case khác biệt, chi tiết."
    elif thorough:
        count = ("Sinh THẬT NHIỀU test case để VÉT CẠN mọi trường hợp (tối thiểu 35, lý tưởng 40-60), "
                 "mỗi case kiểm tra một điều KHÁC BIỆT.")
    else:
        count = "Sinh khoảng 18-25 test case bao quát các trường hợp chính, mỗi case khác biệt."
    return (
        "Bạn là kỹ sư kiểm thử (QA) cao cấp. Hãy sinh bộ test case CHI TIẾT, ĐẦY ĐỦ, KHÔNG TRÙNG LẶP cho màn hình web, "
        "TỔ CHỨC theo ĐÚNG CẤU TRÚC 5 PHẦN ở dưới (đây là yêu cầu QUAN TRỌNG NHẤT).\n"
        f"{ORDER_HINT}\n"
        "Trong từng phần, dùng các quan điểm sau làm nguồn case: Bình thường, Bất thường (rỗng/sai định dạng/biên/"
        "TRIM/double-submit/trùng), Giao diện UI, Toàn vẹn dữ liệu, Bảo mật (SQL injection/XSS/phân quyền/session), "
        "Hiệu năng, API (mã trạng thái/JSON/token/lỗi), Responsive, Tương thích.\n"
        f"{SUBSCREEN_HINT}\n{EXPECTED_DETAIL}\n{TECHNIQUES}\n{DEDUP_HINT}\n"
        f"{UNIVERSAL_CHECKLIST}\n{ACCOUNT_HINT}\n{SCREEN_HINT}\n"
        f"{count}\n{OUTPUT_RULES}"
    )


def _nsteps(s: str) -> str:
    """Chuẩn hóa bước thực hiện để so trùng: bỏ số thứ tự, gộp khoảng trắng, thường hóa."""
    s = re.sub(r"\d+\s*[.)]\s*", "", str(s))  # bỏ "1." "2)" ...
    return re.sub(r"\s+", " ", s).strip().lower()


def _normalize(cases: list) -> list:
    seen, cleaned = set(), []
    for case in cases:
        if not isinstance(case, dict):
            continue
        row = {f: str(case.get(f, "")).strip() for f in TEST_CASE_FIELDS}
        if not (row["steps"] or row["expected"]):
            continue  # bỏ case rỗng ruột
        uf = row["ui_function"].lower()
        row["ui_function"] = "UI" if uf.startswith("ui") else "Function"
        if not row["function"]:
            row["function"] = "Chung"
        # Chống trùng MẠNH: cùng màn + cùng bước thực hiện -> coi là một (dù lời văn kết quả khác chút)
        sig = (re.sub(r"\s+", " ", row["screen"]).strip().lower(), _nsteps(row["steps"]))
        if sig in seen:
            continue
        seen.add(sig)
        row["actual"] = ""
        row["status"] = ""
        row["bug_link"] = ""
        row["test_date"] = ""
        cleaned.append(row)

    # Sắp xếp: gom theo KHU VỰC (function) theo thứ tự xuất hiện (trên→dưới),
    # trong mỗi khu vực để case UI lên TRƯỚC, Function sau (sort ổn định giữ thứ tự gốc còn lại).
    func_idx = {}
    for row in cleaned:
        if row["function"] not in func_idx:
            func_idx[row["function"]] = len(func_idx)
    cleaned.sort(key=lambda r: (func_idx[r["function"]], 0 if r["ui_function"] == "UI" else 1))

    for i, row in enumerate(cleaned, start=1):
        row["id"] = f"TC_{i:03d}"
    return cleaned


def generate_test_cases(url: str, dom_summary: str, spec: str = "", thorough: bool = True,
                        screenshot: str = None) -> list[dict]:
    """Sinh bộ test case bằng MỘT lượt gọi AI (để AI tự gom theo khu vực, sắp xếp UI->Function,
    áp dụng kỹ thuật test và tự loại trùng). thorough=True: sinh nhiều case hơn (vét cạn).

    screenshot: ảnh chụp màn hình dạng base64 (tùy chọn) — gửi kèm cho AI có Vision (Gemini/Claude).
    """
    provider = Provider()
    context = _build_context(url, dom_summary, spec, max_dom=1500 if provider.compact else 0)

    if provider.compact:
        max_tokens = 3200
    elif thorough:
        max_tokens = 12000
    else:
        max_tokens = 6000

    system = _comprehensive_system(thorough, provider.compact)
    try:
        cases = _call_model(provider, system, context, max_tokens=max_tokens, image_b64=screenshot)
    except Exception as exc:
        last_err = str(exc)
        msg = "AI không sinh được test case."
        if "429" in last_err or "quota" in last_err.lower():
            msg += " Gemini đang quá giới hạn miễn phí (chờ 1-2 phút rồi thử lại)."
        else:
            msg += f" Chi tiết: {last_err[:200]}"
        raise ValueError(msg)

    if not cases:
        raise ValueError("AI không sinh được test case (kiểm tra model/PROVIDER).")
    return _normalize(cases)


# ===================== Lập kế hoạch tự động chạy (Giai đoạn 2) =====================
PLAN_SHAPE = ('{"plans":[{"id":"","runnable":true,"risk":"safe","type":"ui","find":"","assert":"present",'
              '"inputs":[],"submit":"","assert_text":"","reason":""}]}')

PLAN_SYSTEM = (
    "Bạn là kỹ sư tự động hóa kiểm thử. Với MỖI test case, hãy phân loại và lập kế hoạch chạy trên trình duyệt.\n"
    "Phân 3 nhóm:\n"
    'A) runnable=true, risk="safe" — chạy tự động ngay, KHÔNG ảnh hưởng dữ liệu:\n'
    '   • type "ui": kiểm HIỂN THỊ (phần tử/nút/ô/tiêu đề tồn tại; ô mật khẩu dạng ●). Điền "find" + "assert"=present|absent|is_password.\n'
    '   • type "validation": ĐIỀN sai/để trống rồi bấm nút, mong đợi HIỆN LỖI (không tạo dữ liệu). '
    '"inputs"=[{"find":"<nhãn ô>","value":"<giá trị sai>"}], "submit"="<chữ nút>", "assert_text"="<phần thông báo lỗi>".\n'
    'B) runnable=true, risk="confirm", type "action" — THAY ĐỔI DỮ LIỆU THẬT (thêm/sửa/XÓA, đăng nhập THÀNH CÔNG, '
    'gửi form hợp lệ) hoặc SQL injection/XSS. Đặt: "inputs"=[{"find","value"}] (giá trị hợp lệ/payload), '
    '"submit"="<chữ nút>", "assert_text"="<thông báo thành công mong đợi>". (Sẽ hỏi người dùng trước khi chạy.)\n'
    'C) runnable=false (kèm "reason" ngắn) — KHÔNG chạy được trên trình duyệt: kiểm API/mã trạng thái, responsive, '
    "đa trình duyệt, kiểm tra trực tiếp CSDL.\n"
    '"find": dùng NHÃN/placeholder/tên/đoạn chữ trên nút hoặc ô (lấy từ DOM đã cho).\n'
    "CHỈ trả về JSON đúng dạng: " + PLAN_SHAPE + " — không giải thích, không markdown. Mỗi case một plan, đúng \"id\"."
)


def _first_quoted(text: str) -> str:
    """Lấy cụm từ trong dấu nháy để dùng làm locator gần đúng."""
    text = str(text or "")
    for pattern in (r'"([^"\n]{1,80})"', r"'([^'\n]{1,80})'", r"“([^”\n]{1,80})”"):
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return ""


def _local_plan_automation(test_cases: list[dict]) -> list[dict]:
    """Lập kế hoạch cơ bản tại máy, không gọi API và không tốn quota.

    Planner local ưu tiên chạy các case UI/validation phổ biến. Những case cần
    API, CSDL, responsive hoặc đa trình duyệt được giữ ở trạng thái thủ công.
    """
    plans = []
    manual_words = (
        " api", "mã trạng thái", "status code", "cơ sở dữ liệu", "database", " db",
        "responsive", "mobile", "tablet", "đa trình duyệt", "cross-browser",
        "hiệu năng", "performance", "thời gian phản hồi", "zoom ",
    )
    validation_words = (
        "để trống", "rỗng", "bắt buộc", "không hợp lệ", "sai định dạng",
        "quá dài", "tối đa", "tối thiểu", "min", "max", "ký tự đặc biệt",
        "trim", "khoảng trắng",
    )
    confirm_words = (
        "thêm mới", "tạo mới", "xóa", "sửa", "cập nhật", "lưu", "gửi form",
        "đăng nhập thành công", "thanh toán", "xss", "sql injection",
    )

    for case in test_cases:
        case_id = str(case.get("id", "")).strip()
        function = str(case.get("function", "")).strip()
        sub_function = str(case.get("sub_function", "")).strip()
        steps = str(case.get("steps", "")).strip()
        expected = str(case.get("expected", "")).strip()
        ui_function = str(case.get("ui_function", "")).strip().lower()
        text = f" {function} {sub_function} {steps} {expected}".lower()

        base = {
            "id": case_id,
            "runnable": True,
            "risk": "safe",
            "type": "ui",
            "find": "",
            "assert": "present",
            "inputs": [],
            "submit": "",
            "assert_text": "",
            "reason": "",
        }

        if any(word in text for word in manual_words):
            base.update(
                runnable=False,
                reason="Case cần môi trường/API/CSDL hoặc kích thước trình duyệt chuyên dụng.",
            )
            plans.append(base)
            continue

        quoted_expected = _first_quoted(expected)
        quoted_steps = _first_quoted(steps)
        find = quoted_expected or quoted_steps or sub_function or function
        find = re.sub(
            r"^(check event|kiểm tra|check|hiển thị|initial|transition)\s*[-:–—]?\s*",
            "",
            find,
            flags=re.IGNORECASE,
        ).strip()
        base["find"] = find[:120]

        if "mật khẩu" in text and ("dạng" in text or "che" in text or "●" in text):
            base["assert"] = "is_password"
        elif any(word in text for word in ("không hiển thị", "không tồn tại", "bị ẩn")):
            base["assert"] = "absent"

        if any(word in text for word in confirm_words):
            base.update(
                risk="confirm",
                type="action",
                submit=quoted_steps or sub_function or function,
                assert_text=quoted_expected,
            )
        elif any(word in text for word in validation_words):
            base.update(
                type="validation",
                submit=quoted_steps or sub_function or function,
                assert_text=quoted_expected,
            )
        elif ui_function != "ui" and not base["find"]:
            base.update(
                runnable=False,
                reason="Không xác định được phần tử cần thao tác từ nội dung test case.",
            )

        plans.append(base)
    return plans


def plan_automation(dom_summary: str, test_cases: list[dict]) -> list[dict]:
    """AI biến các test case AN TOÀN thành kế hoạch thao tác máy chạy được (Giai đoạn 2)."""
    # Chạy test không nên tiêu thêm quota Gemini. Mặc định dùng planner local;
    # đặt AUTOTEST_PLAN_MODE=ai nếu muốn AI lập kế hoạch chi tiết hơn.
    mode = os.environ.get("AUTOTEST_PLAN_MODE", "local").strip().lower()
    if mode != "ai":
        return _local_plan_automation(test_cases)

    provider = Provider()
    lines = []
    for c in test_cases:
        lines.append(f'- id={c.get("id")} | loại={c.get("ui_function")} | chức năng={c.get("function")} '
                     f'| bước: {c.get("steps","")[:160]} | mong đợi: {c.get("expected","")[:120]}')
    user = (f"=== CẤU TRÚC GIAO DIỆN (DOM) ===\n{dom_summary[:2500]}\n\n"
            f"=== DANH SÁCH TEST CASE ===\n" + "\n".join(lines) +
            "\n\nHãy lập kế hoạch chạy cho từng case theo đúng định dạng JSON.")
    try:
        raw = provider.complete(PLAN_SYSTEM, user, max_tokens=8000)
    except Exception:
        # Quota/rate limit/mất mạng không được làm hỏng toàn bộ chức năng chạy.
        return _local_plan_automation(test_cases)
    try:
        data = _extract_json(raw)
    except json.JSONDecodeError:
        data = {}
    plans = data.get("plans") if isinstance(data, dict) else (data if isinstance(data, list) else [])
    parsed = [p for p in (plans or []) if isinstance(p, dict)]
    return parsed or _local_plan_automation(test_cases)
