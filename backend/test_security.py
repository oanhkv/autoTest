from fastapi.testclient import TestClient

import main

EXT_ORIGIN = "chrome-extension://" + "a" * 32
RUN_BODY = {"cases": [{"method": "GET", "url": "http://127.0.0.1:1/x"}]}


def _client():
    return TestClient(main.app)


def test_foreign_website_is_blocked_from_running_requests():
    resp = _client().post("/api/run", json=RUN_BODY, headers={"Origin": "https://evil.example"})
    assert resp.status_code == 403


def test_foreign_website_simple_form_post_is_blocked():
    # Form POST "đơn giản" không qua preflight CORS -> phải bị chặn bởi kiểm tra Origin
    resp = _client().post("/extract", files={"file": ("a.txt", b"x")},
                          headers={"Origin": "https://evil.example"})
    assert resp.status_code == 403


def test_extension_localhost_and_scripts_are_allowed():
    c = _client()
    for headers in ({"Origin": EXT_ORIGIN}, {"Origin": "http://localhost:5173"}, {}):
        resp = c.post("/extract", files={"file": ("a.txt", "xin chào".encode())}, headers=headers)
        assert resp.status_code == 200, headers


def test_cors_preflight_only_echoes_allowed_origins():
    c = _client()
    pre = {"Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type"}
    ok = c.options("/api/run", headers={"Origin": EXT_ORIGIN, **pre})
    assert ok.headers.get("access-control-allow-origin") == EXT_ORIGIN
    bad = c.options("/api/run", headers={"Origin": "https://evil.example", **pre})
    assert bad.headers.get("access-control-allow-origin") is None


def test_token_required_when_configured(monkeypatch):
    monkeypatch.setenv("AUTOTEST_TOKEN", "bi-mat")
    c = _client()
    files = {"file": ("a.txt", b"x")}
    assert c.get("/health").status_code == 200  # /health luôn mở
    assert c.post("/extract", files=files).status_code == 401
    assert c.post("/extract", files=files, headers={"X-AutoTest-Token": "sai"}).status_code == 401
    assert c.post("/extract", files=files, headers={"X-AutoTest-Token": "bi-mat"}).status_code == 200
