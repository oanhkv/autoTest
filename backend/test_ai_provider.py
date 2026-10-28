import io
import json

import ai_generator


def test_gemini_api_key_sent_in_header_not_url(monkeypatch):
    monkeypatch.setenv("PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "KEY-123")
    seen = {}

    def fake_urlopen(req, timeout=None):
        seen["url"] = req.full_url
        seen["key"] = req.get_header("X-goog-api-key")
        body = {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}
        return io.BytesIO(json.dumps(body).encode())

    monkeypatch.setattr(ai_generator.urllib.request, "urlopen", fake_urlopen)
    assert ai_generator.Provider().complete("sys", "user") == "ok"
    assert "KEY-123" not in seen["url"]
    assert seen["key"] == "KEY-123"
