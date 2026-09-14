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
import code_generator
import doc_extract
import excel_export
import html_report

app = FastAPI(title="AutoTest API", version="0.1.0")

# Cho phép extension (chrome-extension://...) gọi vào.
# Để đơn giản trong giai đoạn dev, mở cho mọi origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
