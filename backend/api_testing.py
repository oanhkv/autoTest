"""API testing core: import Postman/OpenAPI, generate real-request cases and run them.

The module intentionally does not mock responses.  Imported/manual cases are normalized
into one small contract so the UI, runner and code generator use the same data.
"""
from __future__ import annotations

import copy
import json
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # YAML is optional; JSON still works without PyYAML.
    yaml = None


MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
DEFAULT_TIMEOUT = 20.0


def _str(value: Any) -> str:
    return "" if value is None else str(value)


def _slug(value: str, fallback: str = "api_case") -> str:
    text = re.sub(r"[^A-Za-z0-9_]+", "_", _str(value)).strip("_").lower()
    return text[:70] or fallback


def _deep_get(obj: Any, path: str) -> Any:
    """Read a simple dotted JSON path, supporting array indexes and leading $."""
    path = _str(path).strip().lstrip("$").lstrip(".")
    if not path:
        return obj
    cur = obj
    for part in path.split("."):
        if isinstance(cur, list) and part.isdigit():
            idx = int(part)
            if idx >= len(cur):
                return None
            cur = cur[idx]
        elif isinstance(cur, dict):
            if part not in cur:
                return None
            cur = cur[part]
        else:
            return None
    return cur


def _resolve_vars(value: Any, variables: dict[str, Any]) -> Any:
    if isinstance(value, str):
        def repl(match: re.Match[str]) -> str:
            key = match.group(1).strip()
            return _str(variables.get(key, match.group(0)))
        return re.sub(r"\{\{\s*([^}]+?)\s*\}\}", repl, value)
    if isinstance(value, list):
        return [_resolve_vars(x, variables) for x in value]
    if isinstance(value, dict):
        return {k: _resolve_vars(v, variables) for k, v in value.items()}
    return value


def _json_or_text(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text:
        return ""
    try:
        return json.loads(text)
    except Exception:
        return value


def _sample_schema(schema: dict[str, Any] | None, root: dict[str, Any] | None = None) -> Any:
    """Create a conservative example from a JSON schema."""
    if not isinstance(schema, dict):
        return None
    root = root or schema
    if "$ref" in schema:
        ref = schema["$ref"]
        if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
            return _sample_schema(root.get("components", {}).get("schemas", {}).get(ref.rsplit("/", 1)[-1]), root)
        if isinstance(ref, str) and ref.startswith("#/definitions/"):
            return _sample_schema(root.get("definitions", {}).get(ref.rsplit("/", 1)[-1]), root)
        return None
    if "example" in schema:
        return copy.deepcopy(schema["example"])
    if "default" in schema:
        return copy.deepcopy(schema["default"])
    if "enum" in schema and schema["enum"]:
        return copy.deepcopy(schema["enum"][0])
    typ = schema.get("type")
    if not typ and "properties" in schema:
        typ = "object"
    if typ == "object":
        out = {}
        for name, prop in (schema.get("properties") or {}).items():
            if name in (schema.get("required") or []) or "example" in prop or "default" in prop:
                val = _sample_schema(prop, root)
                if val is not None:
                    out[name] = val
        return out
    if typ == "array":
        item = _sample_schema(schema.get("items") or {}, root)
        return [item] if item is not None else []
    if typ == "integer" or typ == "number":
        return schema.get("minimum", 1)
    if typ == "boolean":
        return True
    if typ == "string":
        fmt = schema.get("format")
        return {"email": "tester@example.com", "date": "2026-01-01", "date-time": "2026-01-01T00:00:00Z"}.get(fmt, "test-value")
    return None


def _status_assertion(status: Any) -> dict[str, Any]:
    if status is None:
        return {"type": "status", "expected": [200, 201, 202, 204]}
    try:
        return {"type": "status", "expected": [int(status)]}
    except (TypeError, ValueError):
        return {"type": "status", "expected": [200, 201, 202, 204]}


def _normalize_case(case: dict[str, Any], index: int = 1) -> dict[str, Any]:
    method = _str(case.get("method", "GET")).upper()
    url = _str(case.get("url") or "").strip()
    name = _str(case.get("name") or case.get("function") or f"API {method} {url}").strip()
    assertions = case.get("assertions") or [_status_assertion(case.get("expected_status"))]
    if not isinstance(assertions, list):
        assertions = [_status_assertion(case.get("expected_status"))]
    expected_status = case.get("expected_status")
    if expected_status is None:
        for a in assertions:
            if isinstance(a, dict) and a.get("type") == "status":
                vals = a.get("expected") or []
                if vals:
                    expected_status = vals[0]
                    break
    return {
        "id": _str(case.get("id") or f"API_{index:03d}"),
        "name": name,
        "method": method,
        "url": url,
        "headers": case.get("headers") if isinstance(case.get("headers"), dict) else {},
        "params": case.get("params") if isinstance(case.get("params"), dict) else {},
        "body": case.get("body", None),
        "body_type": _str(case.get("body_type") or ("json" if isinstance(case.get("body"), (dict, list)) else "")),
        "assertions": assertions,
        "expected_status": expected_status,
        "source": _str(case.get("source") or "manual"),
        "tags": case.get("tags") if isinstance(case.get("tags"), list) else [],
        "requires_confirmation": bool(case.get("requires_confirmation", method in MUTATING_METHODS)),
        "enabled": bool(case.get("enabled", True)),
        "notes": _str(case.get("notes")),
    }


def _postman_vars(data: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in data.get("variable") or []:
        if isinstance(item, dict) and item.get("key") is not None:
            out[_str(item["key"])] = _str(item.get("value", item.get("default", "")))
    return out


def _postman_url(url: Any) -> tuple[str, dict[str, str]]:
    if isinstance(url, str):
        return url, {}
    if not isinstance(url, dict):
        return "", {}
    raw = _str(url.get("raw"))
    if raw:
        return raw, {}
    protocol = _str(url.get("protocol"))
    host = url.get("host") or []
    path = url.get("path") or []
    host_s = ".".join(host) if isinstance(host, list) else _str(host)
    path_s = "/".join(_str(x) for x in path)
    base = f"{protocol}://{host_s}" if protocol and host_s else host_s
    query = []
    for q in url.get("query") or []:
        if isinstance(q, dict) and not q.get("disabled") and q.get("key"):
            query.append((_str(q["key"]), _str(q.get("value", ""))))
    return base.rstrip("/") + ("/" + path_s if path_s else "") + ("?" + urllib.parse.urlencode(query) if query else ""), {}


def _postman_headers(req: dict[str, Any], collection: dict[str, Any]) -> dict[str, str]:
    headers: dict[str, str] = {}
    for source in (collection.get("header") or [], req.get("header") or []):
        if isinstance(source, dict) and source.get("key") and not source.get("disabled"):
            headers[_str(source["key"])] = _str(source.get("value", ""))
    auth = req.get("auth") or collection.get("auth") or {}
    if isinstance(auth, dict):
        for a in auth.get("apikey") or []:
            if isinstance(a, dict) and a.get("key") and a.get("value") is not None:
                headers[_str(a["key"])] = _str(a["value"])
        bearer = auth.get("bearer") or []
        token = next((_str(x.get("value")) for x in bearer if isinstance(x, dict) and x.get("key") == "token"), "")
        if token:
            headers.setdefault("Authorization", f"Bearer {token}")
    return headers


def _postman_body(req: dict[str, Any]) -> tuple[Any, str]:
    body = req.get("body") or {}
    mode = body.get("mode") if isinstance(body, dict) else ""
    if mode == "raw":
        raw = _str(body.get("raw"))
        value = _json_or_text(raw)
        return value, "json" if isinstance(value, (dict, list)) else "text"
    if mode in ("urlencoded", "formdata"):
        out = {}
        for row in body.get(mode) or []:
            if isinstance(row, dict) and row.get("key") and not row.get("disabled"):
                out[_str(row["key"])] = _str(row.get("value", ""))
        return out, "form"
    return None, ""


def _postman_test_assertions(item: dict[str, Any]) -> list[dict[str, Any]]:
    scripts = []
    event = item.get("event") or []
    if isinstance(event, list):
        scripts.extend(_str(e.get("script", {}).get("exec", "")) for e in event if isinstance(e, dict) and e.get("listen") == "test")
    text = "\n".join(scripts)
    out = []
    for m in re.finditer(r"(?:response\.code|pm\.response\.code)\s*={1,3}\s*(\d{3})", text):
        out.append(_status_assertion(m.group(1)))
    for m in re.finditer(r"(?:response|pm\.response)\.to\.have\.status\s*\(\s*(\d{3})\s*\)", text):
        out.append(_status_assertion(m.group(1)))
    return out


def parse_postman(data: dict[str, Any]) -> dict[str, Any]:
    variables = _postman_vars(data)
    cases: list[dict[str, Any]] = []

    def walk(items: list[Any], folder: str = "") -> None:
        for item in items:
            if not isinstance(item, dict):
                continue
            if isinstance(item.get("item"), list):
                walk(item["item"], _str(item.get("name") or folder))
                continue
            req = item.get("request")
            if not isinstance(req, dict):
                continue
            url, _ = _postman_url(req.get("url"))
            body, body_type = _postman_body(req)
            assertions = _postman_test_assertions(item) or [_status_assertion(None)]
            case = _normalize_case({
                "id": f"API_{len(cases) + 1:03d}",
                "name": _str(item.get("name") or f"{req.get('method', 'GET')} {url}"),
                "method": req.get("method", "GET"), "url": url,
                "headers": _postman_headers(req, data), "body": body, "body_type": body_type,
                "assertions": assertions, "expected_status": (assertions[0].get("expected") or [None])[0],
                "source": "postman" + (f"/{folder}" if folder else ""),
            }, len(cases) + 1)
            cases.append(case)

    walk(data.get("item") or [])
    base_url = variables.get("baseUrl", variables.get("base_url", ""))
    return {"format": "postman", "base_url": base_url, "variables": variables, "cases": [_resolve_vars(c, variables) for c in cases], "warnings": []}


def _openapi_base(spec: dict[str, Any]) -> str:
    servers = spec.get("servers") or []
    if servers and isinstance(servers[0], dict):
        server = servers[0]
        url = _str(server.get("url"))
        for name, definition in (server.get("variables") or {}).items():
            if isinstance(definition, dict):
                url = url.replace("{" + _str(name) + "}", _str(definition.get("default", "")))
        return url
    host = _str(spec.get("host"))
    if host:
        scheme = (_str((spec.get("schemes") or ["https"])[0])).strip() or "https"
        return f"{scheme}://{host}{_str(spec.get('basePath'))}"
    return ""


def _openapi_schema(spec: dict[str, Any], schema: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(schema, dict):
        return None
    if "$ref" in schema:
        ref = _str(schema["$ref"])
        if ref.startswith("#/components/"):
            parts = ref.split("/")
            if len(parts) >= 4:
                return spec.get("components", {}).get(parts[2], {}).get(parts[3], {})
            return {}
        if ref.startswith("#/definitions/"):
            return spec.get("definitions", {}).get(ref.rsplit("/", 1)[-1], {})
    return schema


def _openapi_param_value(param: dict[str, Any], spec: dict[str, Any]) -> Any:
    param = _openapi_schema(spec, param) or param
    if "example" in param:
        return param["example"]
    if "examples" in param and isinstance(param["examples"], dict):
        first = next(iter(param["examples"].values()), {})
        return first.get("value") if isinstance(first, dict) else first
    return _sample_schema(param.get("schema") or param, spec) or ("1" if param.get("in") == "path" else "test-value")


def parse_openapi(spec: dict[str, Any]) -> dict[str, Any]:
    base_url = _openapi_base(spec).rstrip("/")
    cases: list[dict[str, Any]] = []
    paths = spec.get("paths") or {}
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        common_params = path_item.get("parameters") or []
        for method, operation in path_item.items():
            method_u = _str(method).upper()
            if method_u not in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"} or not isinstance(operation, dict):
                continue
            params = list(common_params) + list(operation.get("parameters") or [])
            url = base_url + "/" + _str(path).lstrip("/")
            query: dict[str, Any] = {}
            swagger_body_param = None
            swagger_form_params: list[dict[str, Any]] = []
            for raw_param in params:
                param = _openapi_schema(spec, raw_param) or raw_param
                if not isinstance(param, dict):
                    continue
                if param.get("in") == "body":
                    swagger_body_param = param
                    continue
                if param.get("in") == "formData":
                    swagger_form_params.append(param)
                    continue
                if param.get("in") not in ("path", "query", "header"):
                    continue
                value = _openapi_param_value(param, spec)
                if param.get("in") == "path":
                    url = url.replace("{" + _str(param.get("name")) + "}", urllib.parse.quote(_str(value), safe=""))
                elif param.get("in") == "query":
                    query[_str(param.get("name"))] = value
            headers: dict[str, str] = {}
            content = (operation.get("requestBody") or {}).get("content", {}) if isinstance(operation.get("requestBody"), dict) else {}
            body = None
            body_type = ""
            if content:
                preferred = content.get("application/json") or next(iter(content.values()), {})
                if isinstance(preferred, dict):
                    body = preferred.get("example")
                    if body is None and isinstance(preferred.get("examples"), dict):
                        ex = next(iter(preferred["examples"].values()), {})
                        body = ex.get("value") if isinstance(ex, dict) else ex
                    if body is None:
                        body = _sample_schema(preferred.get("schema"), spec)
                    body_type = "json" if "json" in next(iter(content.keys()), "") else "text"
                    if body_type == "json":
                        headers["Content-Type"] = "application/json"
            elif swagger_body_param:
                body = swagger_body_param.get("x-example") or swagger_body_param.get("example")
                if body is None:
                    body = _sample_schema(swagger_body_param.get("schema"), spec)
                body_type = "json"
                consumes = operation.get("consumes") or spec.get("consumes") or ["application/json"]
                headers["Content-Type"] = _str(consumes[0])
            elif swagger_form_params:
                body = {p.get("name"): _openapi_param_value(p, spec) for p in swagger_form_params if p.get("name")}
                body_type = "form"
                consumes = operation.get("consumes") or spec.get("consumes") or ["application/x-www-form-urlencoded"]
                headers["Content-Type"] = _str(consumes[0])
            responses = operation.get("responses") or {}
            expected = next((int(k) for k in responses if _str(k).isdigit() and 200 <= int(k) < 300), None)
            if expected is None:
                expected = 204 if method_u == "DELETE" else 200
            assertions = [_status_assertion(expected)]
            response_def = responses.get(str(expected)) or responses.get(expected) or responses.get("default") or {}
            response_content = response_def.get("content", {}) if isinstance(response_def, dict) else {}
            response_media = response_content.get("application/json") or (next(iter(response_content.values()), {}) if response_content else {})
            response_schema = _openapi_schema(spec, response_media.get("schema") if isinstance(response_media, dict) else None)
            if response_schema is None and isinstance(response_def, dict):
                response_schema = _openapi_schema(spec, response_def.get("schema"))
            if isinstance(response_schema, dict):
                for required_name in response_schema.get("required") or []:
                    assertions.append({
                        "type": "json_path_exists",
                        "path": str(required_name),
                    })
            case = _normalize_case({
                "id": f"API_{len(cases) + 1:03d}",
                "name": _str(operation.get("summary") or operation.get("operationId") or f"{method_u} {path}"),
                "method": method_u, "url": url, "params": query, "headers": headers,
                "body": body, "body_type": body_type, "expected_status": expected,
                "assertions": assertions, "source": "openapi",
                "requires_confirmation": method_u in MUTATING_METHODS,
                "notes": _str(operation.get("description")),
            }, len(cases) + 1)
            cases.append(case)
            # Safe negative case for missing required query/header/body fields.
            required = [p for p in params if isinstance(p, dict) and p.get("required") and p.get("in") in ("query", "header")]
            if required:
                neg = copy.deepcopy(case)
                neg["id"] = f"API_{len(cases) + 1:03d}"
                neg["name"] = f"{case['name']} — thiếu tham số bắt buộc"
                neg["tags"] = ["negative", "validation"]
                neg["requires_confirmation"] = method_u in MUTATING_METHODS
                missing = _str(required[0].get("name"))
                if required[0].get("in") == "query":
                    neg["params"].pop(missing, None)
                else:
                    neg["headers"].pop(missing, None)
                neg["assertions"] = [{"type": "status", "expected": [400, 401, 403, 404, 422]}]
                neg["expected_status"] = 400
                cases.append(neg)
    return {"format": "openapi", "base_url": base_url, "variables": {}, "cases": cases, "warnings": []}


def parse_definition(filename: str, raw: bytes, format_hint: str = "auto") -> dict[str, Any]:
    text = raw.decode("utf-8-sig", errors="replace")
    hint = _str(format_hint).lower().strip()
    if hint in ("yaml", "yml") or (hint == "auto" and filename.lower().endswith((".yaml", ".yml"))):
        if yaml is None:
            raise ValueError("Chưa cài PyYAML. Hãy chạy pip install -r requirements.txt hoặc dùng file JSON.")
        data = yaml.safe_load(text)
    else:
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            if yaml is None:
                raise ValueError("File không phải JSON hợp lệ; cần cài PyYAML để đọc Swagger/OpenAPI YAML.")
            data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("File API phải là một object JSON/YAML.")
    if hint == "postman" or (hint == "auto" and ("info" in data and "item" in data)):
        result = parse_postman(data)
    elif hint in ("openapi", "swagger") or "openapi" in data or "swagger" in data:
        result = parse_openapi(data)
    else:
        raise ValueError("Không nhận diện được file. Hãy chọn Postman Collection hoặc Swagger/OpenAPI.")
    if not result["cases"]:
        result["warnings"].append("Không tìm thấy request nào trong file.")
    result["count"] = len(result["cases"])
    return result


def _make_url(url: str, params: dict[str, Any]) -> str:
    if not params:
        return url
    parsed = urllib.parse.urlsplit(url)
    current = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    current.extend((str(k), _str(v)) for k, v in params.items() if v is not None and _str(v) != "")
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urllib.parse.urlencode(current), parsed.fragment))


def _assertions(response_status: int, response_headers: dict[str, str], body_text: str, body_json: Any, assertions: list[Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    for assertion in assertions or [_status_assertion(None)]:
        if not isinstance(assertion, dict):
            continue
        typ = _str(assertion.get("type", "status")).lower()
        if typ == "status":
            expected = assertion.get("expected", assertion.get("value", []))
            expected = expected if isinstance(expected, list) else [expected]
            values = []
            for x in expected:
                try: values.append(int(x))
                except (TypeError, ValueError): pass
            if values and response_status not in values:
                errors.append(f"HTTP {response_status}, mong đợi {values}")
        elif typ in ("contains", "body_contains"):
            needle = _str(assertion.get("value", assertion.get("expected")))
            if needle not in body_text:
                errors.append(f"Body không chứa: {needle}")
        elif typ in ("json_path", "jsonpath"):
            actual = _deep_get(body_json, _str(assertion.get("path"))) if body_json is not None else None
            expected = assertion.get("expected", assertion.get("value"))
            if actual != expected:
                errors.append(f"JSON {_str(assertion.get('path'))}: nhận {actual!r}, mong đợi {expected!r}")
        elif typ == "json_path_exists":
            actual = _deep_get(body_json, _str(assertion.get("path"))) if body_json is not None else None
            if actual is None:
                errors.append(f"JSON thiếu trường bắt buộc: {_str(assertion.get('path'))}")
        elif typ == "header":
            name = _str(assertion.get("name")).lower()
            actual = next((v for k, v in response_headers.items() if k.lower() == name), None)
            expected = _str(assertion.get("expected", assertion.get("value")))
            if actual is None or (expected and expected not in actual):
                errors.append(f"Header {name} không khớp: {actual!r}")
    return not errors, errors


def execute_case(case: dict[str, Any], variables: dict[str, Any] | None = None, timeout: float = DEFAULT_TIMEOUT, verify_ssl: bool = True) -> dict[str, Any]:
    variables = variables or {}
    case = _resolve_vars(copy.deepcopy(case), variables)
    method = _str(case.get("method", "GET")).upper()
    url = _make_url(_str(case.get("url")), case.get("params") or {})
    headers = {str(k): _str(v) for k, v in (case.get("headers") or {}).items()}
    body = case.get("body")
    data = None
    if body is not None and method not in ("GET", "HEAD"):
        body_type = _str(case.get("body_type")).lower()
        if isinstance(body, (dict, list)) and body_type != "form":
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            headers.setdefault("Content-Type", "application/json")
        elif body_type == "form" and isinstance(body, dict):
            data = urllib.parse.urlencode(body).encode("utf-8")
            headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
        else:
            data = _str(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    context = None if verify_ssl else ssl._create_unverified_context()
    started = time.perf_counter()
    status = 0
    response_headers: dict[str, str] = {}
    body_text = ""
    error = ""
    try:
        with urllib.request.urlopen(request, timeout=float(timeout), context=context) as response:
            status = int(response.status)
            response_headers = dict(response.headers.items())
            body_text = response.read(2_000_000).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        response_headers = dict(exc.headers.items()) if exc.headers else {}
        body_text = exc.read(2_000_000).decode("utf-8", errors="replace")
    except Exception as exc:
        error = str(exc)
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    try:
        body_json = json.loads(body_text) if body_text else None
    except Exception:
        body_json = None
    if error:
        ok, assertion_errors = False, [error]
    else:
        ok, assertion_errors = _assertions(status, response_headers, body_text, body_json, case.get("assertions") or [])
    return {
        "id": _str(case.get("id")), "name": _str(case.get("name")), "method": method, "url": url,
        "status": "Pass" if ok else "Fail", "http_status": status, "duration_ms": duration_ms,
        "actual": "; ".join(assertion_errors) if assertion_errors else f"HTTP {status} · {duration_ms} ms",
        "response_preview": body_text[:4000], "response_headers": response_headers,
        "error": error, "assertion_errors": assertion_errors,
    }


def run_cases(cases: list[dict[str, Any]], variables: dict[str, Any] | None = None, timeout: float = DEFAULT_TIMEOUT,
              verify_ssl: bool = True, allow_mutations: bool = False) -> list[dict[str, Any]]:
    results = []
    for raw in cases:
        case = _normalize_case(raw, len(results) + 1)
        if not case["enabled"]:
            results.append({"id": case["id"], "name": case["name"], "status": "Skipped", "actual": "Case đang tắt"})
        elif case["requires_confirmation"] and not allow_mutations:
            results.append({"id": case["id"], "name": case["name"], "method": case["method"], "url": case["url"], "status": "Blocked", "actual": "Request có thể thay đổi dữ liệu — hãy bật xác nhận chạy mutation."})
        else:
            results.append(execute_case(case, variables, timeout, verify_ssl))
    return results


def manual_case(payload: dict[str, Any]) -> dict[str, Any]:
    assertions = payload.get("assertions") or []
    if not assertions:
        assertions = [_status_assertion(payload.get("expected_status", 200))]
        contains = _str(payload.get("response_contains"))
        if contains:
            assertions.append({"type": "contains", "value": contains})
    return _normalize_case({**payload, "source": "manual", "assertions": assertions}, 1)


def generate_api_code(cases: list[dict[str, Any]], variables: dict[str, Any] | None = None, title: str = "AutoTest API") -> str:
    payload = json.dumps(variables or {}, ensure_ascii=False, indent=2)
    lines = [
        f'"""{title} — real API tests generated by AutoTest.',
        "",
        "Install: pip install pytest",
        "Run safe cases: pytest test_api.py -v",
        "To allow POST/PUT/PATCH/DELETE, set RUN_MUTATING = True after reviewing the environment.",
        '"""',
        "import json", "import ssl", "import urllib.error", "import urllib.parse", "import urllib.request",
        "import pytest", "",
        f"VARIABLES = {payload}", "RUN_MUTATING = False", "",
        "def _resolve(value):",
        "    if not isinstance(value, str): return value",
        "    for key, val in VARIABLES.items(): value = value.replace('{{' + key + '}}', str(val))",
        "    return value",
        "",
        "def _run(case):",
        "    url = _resolve(case['url'])",
        "    if case.get('params'):",
        "        q = urllib.parse.urlencode({k: _resolve(v) for k, v in case['params'].items()})",
        "        url += ('&' if '?' in url else '?') + q",
        "    headers = {k: _resolve(v) for k, v in case.get('headers', {}).items()}",
        "    body = case.get('body')",
        "    data = None",
        "    if body is not None:",
        "        data = json.dumps(body).encode() if isinstance(body, (dict, list)) else str(body).encode()",
        "        headers.setdefault('Content-Type', 'application/json')",
        "    req = urllib.request.Request(url, data=data, headers=headers, method=case['method'])",
        "    try:",
        "        with urllib.request.urlopen(req, timeout=20) as r: return r.status, r.read().decode(errors='replace')",
        "    except urllib.error.HTTPError as e: return e.code, e.read().decode(errors='replace')",
        "",
    ]
    for i, case in enumerate(cases, 1):
        name = _slug(case.get("name"), f"api_{i}")
        expected = []
        for a in case.get("assertions") or []:
            if isinstance(a, dict) and a.get("type") == "status":
                expected.extend(a.get("expected") or [])
        expected = [int(x) for x in expected if _str(x).isdigit()] or [200]
        serial = json.dumps({k: case.get(k) for k in ("method", "url", "params", "headers", "body")}, ensure_ascii=False)
        lines.append(f"def test_{name}():")
        if case.get("requires_confirmation"):
            lines.append("    if not RUN_MUTATING: pytest.skip('Mutation case: review and set RUN_MUTATING=True')")
        lines.extend([f"    status, body = _run({serial})", f"    assert status in {expected}, f'HTTP {{status}} != {expected}'"])
        has_json_assertion = any(
            isinstance(a, dict) and a.get("type") in ("json_path_exists", "json_path", "jsonpath")
            for a in (case.get("assertions") or [])
        )
        if has_json_assertion:
            lines.extend([
                "    data = json.loads(body)",
            ])
        for assertion in case.get("assertions") or []:
            if isinstance(assertion, dict) and assertion.get("type") == "contains":
                lines.append(f"    assert {json.dumps(_str(assertion.get('value')), ensure_ascii=False)} in body")
            elif isinstance(assertion, dict) and assertion.get("type") == "json_path_exists":
                path = _str(assertion.get("path"))
                lines.extend([
                    f"    value = data",
                    f"    for part in {json.dumps(path.split('.'), ensure_ascii=False)}: value = value[part]",
                    "    assert value is not None",
                ])
            elif isinstance(assertion, dict) and assertion.get("type") in ("json_path", "jsonpath"):
                path = _str(assertion.get("path"))
                lines.extend([
                    f"    value = data",
                    f"    for part in {json.dumps(path.split('.'), ensure_ascii=False)}: value = value[part]",
                    f"    assert value == {json.dumps(assertion.get('expected', assertion.get('value')), ensure_ascii=False)}",
                ])
        lines.append("")
    return "\n".join(lines)
