# API Testing Hub

## Luồng sử dụng nhanh

1. Chạy backend bằng `backend/start_backend.bat`.
2. Reload extension tại `chrome://extensions`.
3. Mở `API Testing Hub` trong side panel.
4. Chọn một nguồn:
   - **Postman Collection** (`.json`)
   - **Swagger/OpenAPI** (`.json`, `.yaml`, `.yml`)
   - **Nhập request thủ công**
5. Bấm **Nhập & tạo test API** hoặc **Thêm request vào bộ API**.
6. Nhập biến môi trường nếu cần, ví dụ:

```json
{
  "baseUrl": "https://staging.example.com",
  "token": "test-token"
}
```

Các chuỗi `{{baseUrl}}` và `{{token}}` trong URL/header/body sẽ được thay thế trước khi chạy.

## Nguyên tắc chạy

- Backend gửi HTTP request thật bằng `urllib`; endpoint không có mock mode.
- GET/HEAD/OPTIONS có thể chạy ngay.
- POST/PUT/PATCH/DELETE bị `Blocked` nếu chưa bật **Cho phép request thay đổi dữ liệu**.
- Nên chạy bằng tài khoản test trên staging; không dùng token production.
- `verify_ssl` được bật mặc định. Chỉ tắt cho môi trường local có chứng chỉ tự ký.

## Các assertion hiện có

- HTTP status code.
- Body chứa chuỗi.
- JSON path bằng giá trị mong đợi.
- JSON path tồn tại (tự sinh từ `required` của OpenAPI).
- Header chứa giá trị.

## Sinh code CI/CD

Nút **Sinh pytest** tạo `test_api.py`. File này cũng gửi request thật; các case mutation được `skip` mặc định:

```powershell
cd backend
pip install -r requirements.txt
pytest test_api.py -v
```

Sau khi kiểm tra môi trường và dữ liệu, đổi `RUN_MUTATING = True` trong file sinh ra nếu muốn chạy POST/PUT/PATCH/DELETE.

## Định hướng mở rộng nên làm tiếp

1. Import Postman Environment riêng và profile `local/staging/production`.
2. Hỗ trợ OAuth2, API key và Basic Auth an toàn hơn.
3. Validate đầy đủ JSON Schema/OpenAPI response.
4. Thêm retry/backoff, kiểm tra SLA response time và chạy song song.
5. Lưu lịch sử API riêng trong báo cáo HTML/Excel.
6. Chỉ thêm browser network discovery sau khi có cơ chế lọc secret/token; OpenAPI/Postman vẫn là nguồn tin cậy và dễ dùng nhất.
