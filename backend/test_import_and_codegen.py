import code_generator
import excel_export


def test_excel_import_round_trip():
    cases = [{
        "id": "TC_001",
        "screen": "Đăng nhập",
        "function": "Hiển thị nút",
        "ui_function": "UI",
        "steps": "1. Mở trang",
        "expected": "Nút hiển thị",
        "status": "",
    }]

    imported = excel_export.parse_workbook(excel_export.to_bytes(cases, "https://example.test"))

    assert len(imported) == 1
    assert imported[0]["id"] == "TC_001"
    assert imported[0]["screen"] == "Đăng nhập"
    assert imported[0]["expected"] == "Nút hiển thị"


def test_codegen_falls_back_when_ai_is_unavailable(monkeypatch):
    class QuotaProvider:
        compact = True

        def __init__(self):
            raise ValueError("Gemini hết quota")

    monkeypatch.setattr(code_generator, "Provider", QuotaProvider)
    cases = [{
        "id": "TC_001",
        "function": "Hiển thị nút Đăng nhập",
        "steps": "Mở trang",
        "expected": 'Nút "Đăng nhập" hiển thị',
    }]

    python_code = code_generator.generate_playwright_code(
        "https://example.test", "", "", cases
    )
    ts_code = code_generator.generate_playwright_ts_code(
        "https://example.test", "", "", cases
    )

    assert "def test_TC_001" in python_code
    assert "get_by_text" in python_code
    compile(python_code, "generated_fallback.py", "exec")
    assert "test(" in ts_code
    assert "getByText" in ts_code
