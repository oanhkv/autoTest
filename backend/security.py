"""Bảo vệ backend local khỏi bị trang web lạ gọi trộm (CSRF / SSRF qua trình duyệt).

Backend chạy ở 127.0.0.1 nhưng nếu mở CORS "*" thì BẤT KỲ trang web nào bạn đang mở
cũng có thể gửi request tới http://127.0.0.1:8000/api/run (gửi HTTP tùy ý từ máy bạn).

Hai lớp bảo vệ:
1) Kiểm tra header Origin: chỉ chấp nhận extension Chrome và localhost.
   Request không có Origin (curl, pytest, mobile_runner.py) vẫn được phép.
2) (Tùy chọn) Token: nếu đặt AUTOTEST_TOKEN trong .env thì mọi request (trừ /health)
   phải gửi header "X-AutoTest-Token" đúng giá trị.

Biến môi trường:
- AUTOTEST_EXTENSION_ID   : chỉ cho phép đúng ID extension này (mặc định: mọi extension).
- AUTOTEST_ALLOWED_ORIGINS: thêm origin khác, phân cách bằng dấu phẩy.
- AUTOTEST_TOKEN          : bật xác thực token.
"""
import hmac
import os
import re

from fastapi.responses import JSONResponse

_LOCAL_ORIGIN = r"https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?"
PUBLIC_PATHS = {"/health"}


def origin_regex() -> str:
    ext_id = os.environ.get("AUTOTEST_EXTENSION_ID", "").strip()
    ext = f"chrome-extension://{re.escape(ext_id)}" if ext_id else r"chrome-extension://[a-p]{32}"
    extra = [re.escape(o.strip().rstrip("/"))
             for o in os.environ.get("AUTOTEST_ALLOWED_ORIGINS", "").split(",") if o.strip()]
    return "^(" + "|".join([ext, _LOCAL_ORIGIN, *extra]) + ")$"


def is_allowed_origin(origin: str | None) -> bool:
    if not origin:  # không phải trình duyệt (curl, script Python...)
        return True
    return re.match(origin_regex(), origin) is not None


def _token_ok(provided: str | None) -> bool:
    expected = os.environ.get("AUTOTEST_TOKEN", "").strip()
    if not expected:
        return True
    return hmac.compare_digest((provided or "").encode(), expected.encode())


async def guard_middleware(request, call_next):
    """Middleware FastAPI: chặn origin lạ & sai token trước khi vào endpoint."""
    if request.method != "OPTIONS":
        if not is_allowed_origin(request.headers.get("origin")):
            return JSONResponse({"detail": "Origin không được phép gọi AutoTest backend."}, 403)
        if request.url.path not in PUBLIC_PATHS and not _token_ok(request.headers.get("x-autotest-token")):
            return JSONResponse({"detail": "Thiếu hoặc sai X-AutoTest-Token."}, 401)
    return await call_next(request)
