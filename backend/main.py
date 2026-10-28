"""API backend cho AutoTest.

Chạy:  uvicorn main:app --reload --port 8000
"""
from dotenv import load_dotenv

load_dotenv()  # đọc .env trước khi import phần dùng API key

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

import ai_generator
import api_testing
import code_generator
import doc_extract
import excel_export
import html_report
import security

app = FastAPI(title="AutoTest API", version="0.1.0")

# Chỉ cho extension Chrome + localhost gọi vào (xem security.py).
# Thứ tự: middleware thêm SAU chạy TRƯỚC -> CORS bọc ngoài guard để lỗi 401/403 vẫn có header CORS.
app.middleware("http")(security.guard_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=security.origin_regex(),
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    url: str = ""
    dom_summary: str = ""
    spec: str = ""
    thorough: bool = True       # True = vét cạn (fan-out các nhóm quan điểm)
    screenshot: str = ""        # ảnh chụp màn hình base64 (tùy chọn, cho AI Vision)


class ExportRequest(BaseModel):
    url: str = ""
    test_cases: list[dict]
    title: str = "Báo cáo kiểm thử"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    """Nhận file đặc tả (.txt/.md/.docx/.pdf) -> trả về văn bản trích xuất."""
    data = await file.read()
    if not data:
        raise HTTPException(400, "File rỗng.")
    try:
        text = doc_extract.extract_text(file.filename, data)
    except Exception as exc:
        raise HTTPException(400, f"Không đọc được file: {exc}")
    return {"filename": file.filename, "chars": len(text), "text": text.strip()}


@app.post("/generate")
def generate(req: GenerateRequest):
    """Nhận DOM + spec → trả về danh sách test case (JSON)."""
    if not req.dom_summary and not req.spec:
        raise HTTPException(400, "Cần ít nhất DOM trang web hoặc tài liệu đặc tả.")
    try:
        cases = ai_generator.generate_test_cases(
            req.url, req.dom_summary, req.spec,
            thorough=req.thorough, screenshot=req.screenshot or None,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:  # lỗi mạng / API
        raise HTTPException(500, f"Lỗi khi gọi AI: {exc}")
    return {"count": len(cases), "test_cases": cases}


class PlanRequest(BaseModel):
    dom_summary: str = ""
    test_cases: list[dict]


@app.post("/plan_auto")
def plan_auto(req: PlanRequest):
    """Biến các test case AN TOÀN thành kế hoạch thao tác để extension tự chạy."""
    if not req.test_cases:
        raise HTTPException(400, "Không có test case.")
    try:
        plans = ai_generator.plan_automation(req.dom_summary, req.test_cases)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        raise HTTPException(500, f"Lỗi lập kế hoạch chạy: {exc}")
    return {"count": len(plans), "plans": plans}


@app.post("/import_cases")
async def import_cases(file: UploadFile = File(...)):
    """Nhận file Excel test case cũ (do tool xuất) -> trả về danh sách case để gộp."""
    data = await file.read()
    if not data:
        raise HTTPException(400, "File rỗng.")
    try:
        cases = excel_export.parse_workbook(data)
    except Exception as exc:
        raise HTTPException(400, f"Không đọc được file test case: {exc}")
    return {"count": len(cases), "test_cases": cases}


@app.post("/export")
def export(req: ExportRequest):
    """Nhận danh sách test case → trả về file Excel .xlsx."""
    if not req.test_cases:
        raise HTTPException(400, "Không có test case để xuất.")
    data = excel_export.to_bytes(req.test_cases, req.url)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="test_cases.xlsx"'},
    )


class SpecMdRequest(BaseModel):
    url: str = ""
    dom_summary: str = ""
    spec: str = ""


@app.post("/gen_spec_md")
def gen_spec_md(req: SpecMdRequest):
    """DOM trang (+ spec sẵn có) → tài liệu đặc tả Markdown (.md)."""
    if not req.dom_summary and not req.spec:
        raise HTTPException(400, "Cần DOM trang (quét trang trước) hoặc tài liệu đặc tả.")
    try:
        md = code_generator.dom_to_markdown(req.url, req.dom_summary, req.spec)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        raise HTTPException(500, f"Lỗi sinh tài liệu .md: {exc}")
    return {"markdown": md, "chars": len(md)}


class CodeRequest(BaseModel):
    url: str = ""
    dom_summary: str = ""       # web: DOM; android: cây giao diện app (Appium page source)
    spec: str = ""
    test_cases: list[dict]
    platform: str = "web"       # "web" -> Playwright | "android" -> Appium
    app_info: str = ""          # mobile: package/activity của app (tùy chọn)


@app.post("/gen_code")
def gen_code(req: CodeRequest):
    """spec/UI + test case → file code tự động hóa (.py) chạy được.

    platform=web     → pytest + Playwright
    platform=android → pytest + Appium (app native)
    """
    if not req.test_cases:
        raise HTTPException(400, "Chưa có test case để sinh code.")
    target = "Appium" if req.platform.lower() in ("android", "mobile", "ios", "appium") else "Playwright"
    try:
        code = code_generator.generate_code(
            req.platform, url=req.url, ui_summary=req.dom_summary, spec=req.spec,
            test_cases=req.test_cases, app_info=req.app_info)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        raise HTTPException(500, f"Lỗi sinh code {target}: {exc}")
    return {"code": code, "lines": code.count(chr(10)) + 1, "platform": req.platform, "target": target}


@app.post("/export_html")
def export_html(req: ExportRequest):
    """Nhận danh sách test case → trả về BÁO CÁO HTML tự chứa (chia sẻ/trình bày)."""
    if not req.test_cases:
        raise HTTPException(400, "Không có test case để xuất.")
    data = html_report.to_bytes(req.test_cases, req.url, req.title)
    return Response(
        content=data,
        media_type="text/html; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="bao_cao_test.html"'},
    )


# ===================== API Testing Hub =====================
class ApiRunRequest(BaseModel):
    cases: list[dict]
    variables: dict[str, object] = {}
    timeout: float = 20.0
    verify_ssl: bool = True
    allow_mutations: bool = False


class ApiManualRequest(BaseModel):
    method: str = "GET"
    url: str
    headers: dict[str, str] = {}
    params: dict[str, object] = {}
    body: object = None
    body_type: str = ""
    expected_status: int | None = 200
    response_contains: str = ""
    assertions: list[dict] = []
    name: str = ""


class ApiCodeRequest(BaseModel):
    cases: list[dict]
    variables: dict[str, object] = {}
    title: str = "AutoTest API"


@app.post("/api/import")
async def api_import(file: UploadFile = File(...), format: str = "auto"):
    """Import Postman Collection or Swagger/OpenAPI JSON/YAML and normalize cases."""
    data = await file.read()
    if not data:
        raise HTTPException(400, "File API rỗng.")
    try:
        return api_testing.parse_definition(file.filename or "api.json", data, format)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        raise HTTPException(400, f"Không đọc được file API: {exc}")


@app.post("/api/manual")
def api_manual(req: ApiManualRequest):
    """Create one real API test case from a manual request."""
    if not req.url.strip():
        raise HTTPException(400, "URL API không được để trống.")
    if not req.url.lower().startswith(("http://", "https://")):
        raise HTTPException(400, "URL API phải bắt đầu bằng http:// hoặc https://.")
    try:
        return {"case": api_testing.manual_case(req.model_dump())}
    except Exception as exc:
        raise HTTPException(400, f"Không tạo được API test case: {exc}")


@app.post("/api/run")
def api_run(req: ApiRunRequest):
    """Run real HTTP requests. No mock mode is used by this endpoint."""
    if not req.cases:
        raise HTTPException(400, "Chưa có API test case.")
    if req.timeout <= 0 or req.timeout > 300:
        raise HTTPException(400, "Timeout phải nằm trong khoảng 0-300 giây.")
    try:
        results = api_testing.run_cases(
            req.cases,
            variables=req.variables,
            timeout=req.timeout,
            verify_ssl=req.verify_ssl,
            allow_mutations=req.allow_mutations,
        )
    except Exception as exc:
        raise HTTPException(500, f"Lỗi chạy API thật: {exc}")
    counts = {"pass": 0, "fail": 0, "blocked": 0, "skipped": 0}
    for result in results:
        key = str(result.get("status", "")).lower()
        if key in counts:
            counts[key] += 1
    return {"results": results, "count": len(results), **counts, "mock": False}


@app.post("/api/code")
def api_code(req: ApiCodeRequest):
    """Generate a pytest file that sends real HTTP requests (not mocked)."""
    if not req.cases:
        raise HTTPException(400, "Chưa có API test case để sinh code.")
    try:
        code = api_testing.generate_api_code(req.cases, req.variables, req.title)
    except Exception as exc:
        raise HTTPException(500, f"Lỗi sinh code API: {exc}")
    return {"code": code, "lines": code.count(chr(10)) + 1, "mock": False}
