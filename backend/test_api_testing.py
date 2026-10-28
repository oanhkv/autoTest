import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import api_testing


def test_postman_collection_is_normalized():
    raw = json.dumps({
        "info": {"name": "Demo"},
        "variable": [{"key": "baseUrl", "value": "http://example.test"}],
        "item": [{
            "name": "List users",
            "request": {
                "method": "GET",
                "url": "{{baseUrl}}/users",
                "header": [{"key": "Accept", "value": "application/json"}],
            },
            "event": [{
                "listen": "test",
                "script": {"exec": ["pm.response.to.have.status(200);"]},
            }],
        }],
    }).encode()

    result = api_testing.parse_definition("demo.postman_collection.json", raw)

    assert result["format"] == "postman"
    assert len(result["cases"]) == 1
    assert result["cases"][0]["url"] == "http://example.test/users"
    assert result["cases"][0]["assertions"][0]["expected"] == [200]


def test_openapi_generates_happy_and_required_parameter_negative_case():
    spec = {
        "openapi": "3.0.3",
        "servers": [{"url": "https://api.example.test"}],
        "paths": {
            "/users": {
                "get": {
                    "summary": "List users",
                    "parameters": [{
                        "name": "page",
                        "in": "query",
                        "required": True,
                        "schema": {"type": "integer", "example": 1},
                    }],
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {"application/json": {
                                "schema": {"type": "object", "required": ["items"]}
                            }},
                        }
                    },
                }
            }
        },
    }

    result = api_testing.parse_definition("openapi.json", json.dumps(spec).encode())

    assert result["format"] == "openapi"
    assert len(result["cases"]) == 2
    assert result["cases"][0]["params"] == {"page": 1}
    assert result["cases"][0]["assertions"][1] == {
        "type": "json_path_exists", "path": "items"
    }
    assert result["cases"][1]["tags"] == ["negative", "validation"]
    assert result["cases"][1]["params"] == {}


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b'{"ok":true,"message":"hello"}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


def test_runner_sends_real_request_and_asserts_response():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        cases = [api_testing.manual_case({
            "method": "GET",
            "url": f"http://127.0.0.1:{port}/health",
            "expected_status": 200,
            "response_contains": '"ok":true',
        })]
        results = api_testing.run_cases(cases)
        assert results[0]["status"] == "Pass"
        assert results[0]["http_status"] == 200
    finally:
        server.shutdown()
        server.server_close()


def test_mutation_is_blocked_without_explicit_confirmation():
    case = api_testing.manual_case({
        "method": "POST",
        "url": "http://127.0.0.1:1/should-not-run",
        "expected_status": 201,
    })
    result = api_testing.run_cases([case])[0]
    assert result["status"] == "Blocked"
    assert "thay đổi dữ liệu" in result["actual"]


def test_generated_api_code_is_valid_python():
    case = api_testing.manual_case({
        "method": "GET",
        "url": "https://example.test/health",
        "expected_status": 200,
    })
    code = api_testing.generate_api_code([case])
    compile(code, "generated_api.py", "exec")
    assert "urllib.request.urlopen" in code
    assert "RUN_MUTATING = False" in code
