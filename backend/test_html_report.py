import re

import html_report


def _embedded_script(report: str) -> str:
    match = re.search(r"<script>\s*([\s\S]*?)\s*</script>", report, re.IGNORECASE)
    assert match is not None
    return match.group(1)


def test_xss_payload_cannot_close_embedded_script():
    report = html_report.build_html(
        [{
            "id": "TC_XSS",
            "screen": "Cửa hàng",
            "function": "Kiểm tra XSS",
            "ui_function": "UI",
            "steps": 'Nhập <script>alert("xss")</script> rồi nhấn Enter',
            "expected": "Hiển thị nguyên văn </script><img src=x onerror=alert(1)>",
            "actual": "",
            "status": "fail",
        }]
    )

    script = _embedded_script(report)

    # Chỉ thẻ đóng script thật của template được tồn tại trong toàn báo cáo.
    assert report.lower().count("</script>") == 1
    assert "\\u003cscript\\u003e" in script
    assert "\\u003c/script\\u003e" in script
    assert "\\u003cimg src=x onerror=alert(1)\\u003e" in script


def test_report_uses_text_content_for_table_cells():
    report = html_report.build_html([{"id": "TC_001"}])
    script = _embedded_script(report)

    assert "td.textContent =" in script
    assert "badge.textContent =" in script
