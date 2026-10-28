"""Xuất bộ test case ra BÁO CÁO HTML tự chứa (single-file).

Khác với Excel (để tester điền tay), báo cáo HTML dùng để CHIA SẺ / TRÌNH BÀY:
- Mở bằng mọi trình duyệt, không cần cài gì.
- Có KPI, biểu đồ donut (SVG), thanh tiến độ theo màn hình, bảng case lọc/tìm được.
- Toàn bộ CSS/JS nhúng sẵn trong 1 file .html — gửi qua mail/Zalo là xem được ngay.
"""
import html
import io
import json
from datetime import datetime


def _classify(value: str) -> str:
    v = str(value or "").strip().lower()
    if v in ("pass", "passed", "đạt", "ok"):
        return "pass"
    if v in ("fail", "failed", "lỗi", "không đạt", "ng"):
        return "fail"
    if v in ("blocked", "block", "pending"):
        return "blocked"
    if v in ("stopped", "stop", "đã dừng", "dừng"):
        return "stopped"
    return "untested"


def _stats(cases: list[dict]) -> dict:
    cnt = {"pass": 0, "fail": 0, "blocked": 0, "stopped": 0, "untested": 0}
    for c in cases:
        cnt[_classify(c.get("status", ""))] += 1
    total = len(cases)
    done = cnt["pass"] + cnt["fail"] + cnt["blocked"]
    cnt["total"] = total
    cnt["done"] = done
    cnt["pass_pct"] = round(cnt["pass"] / total * 100) if total else 0
    cnt["done_pct"] = round(done / total * 100) if total else 0
    return cnt


def _donut_svg(s: dict) -> str:
    """Vẽ donut tỷ lệ kết quả bằng SVG thuần (không cần thư viện)."""
    total = s["total"] or 1
    segs = [("#16a34a", s["pass"]), ("#dc2626", s["fail"]),
            ("#d97706", s["blocked"]), ("#64748b", s["stopped"]),
            ("#cbd5e1", s["untested"])]
    r, cx, cy, w = 70, 90, 90, 26
    circ = 2 * 3.141592653589793 * r
    parts, offset = [], 0.0
    for color, val in segs:
        if val <= 0:
            continue
        frac = val / total
        dash = frac * circ
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" '
            f'stroke-width="{w}" stroke-dasharray="{dash:.2f} {circ - dash:.2f}" '
            f'stroke-dashoffset="{-offset:.2f}" transform="rotate(-90 {cx} {cy})"/>'
        )
        offset += dash
    ring = "".join(parts) or (
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#e2e8f0" stroke-width="{w}"/>'
    )
    return (
        f'<svg viewBox="0 0 180 180" width="180" height="180">{ring}'
        f'<text x="{cx}" y="{cy - 4}" text-anchor="middle" font-size="34" font-weight="800" '
        f'fill="#1f3864">{s["pass_pct"]}%</text>'
        f'<text x="{cx}" y="{cy + 20}" text-anchor="middle" font-size="13" fill="#64748b">Pass</text></svg>'
    )


def _esc(v) -> str:
    return html.escape(str(v or ""))


def _status_badge(status: str) -> str:
    k = _classify(status)
    label = {
        "pass": "Pass", "fail": "Fail", "blocked": "Blocked",
        "stopped": "Đã dừng", "untested": "Chưa test",
    }[k]
    return f'<span class="badge {k}">{label}</span>'


def build_html(test_cases: list[dict], url: str = "", title: str = "Báo cáo kiểm thử") -> str:
    s = _stats(test_cases)

    # Gom theo màn hình (giữ thứ tự xuất hiện)
    by_screen, order = {}, []
    for c in test_cases:
        scr = c.get("screen") or "Chung"
        if scr not in by_screen:
            by_screen[scr] = []
            order.append(scr)
        by_screen[scr].append(c)

    # Thanh tiến độ theo màn hình
    screen_rows = []
    for scr in order:
        ss = _stats(by_screen[scr])
        screen_rows.append(
            f'<div class="screen-row"><div class="screen-name">{_esc(scr)} '
            f'<span class="screen-count">{ss["total"]} case</span></div>'
            f'<div class="bar"><span class="bar-pass" style="width:{ss["pass_pct"]}%"></span>'
            f'<span class="bar-fail" style="width:{round(ss["fail"]/ (ss["total"] or 1)*100)}%"></span></div>'
            f'<div class="screen-pct">{ss["pass_pct"]}%</div></div>'
        )

    # Bảng case (đẩy data qua JSON để JS lọc/tìm phía client)
    rows = []
    for i, c in enumerate(test_cases, start=1):
        rows.append({
            "stt": i,
            "id": c.get("id", ""),
            "screen": c.get("screen", ""),
            "function": c.get("function", ""),
            "ui_function": c.get("ui_function", ""),
            "steps": c.get("steps", ""),
            "expected": c.get("expected", ""),
            "actual": c.get("actual", ""),
            "status": _classify(c.get("status", "")),
        })
    # Nhúng JSON vào <script> nhưng không để dữ liệu người dùng có thể đóng
    # thẻ script sớm (ví dụ payload XSS: </script><script>...).
    #
    # Không được tách chuỗi bằng cách nối "<" + "/" ở đây: cách đó làm JSON
    # trở thành JavaScript không hợp lệ và khiến toàn bộ phần bảng không render.
    # Các escape Unicode vẫn được trình duyệt giải mã lại đúng khi gán vào DATA.
    data_json = json.dumps(rows, ensure_ascii=False)
    data_json = (
        data_json
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )
    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    kpis = [
        ("Tổng test case", s["total"], "#2f5597"),
        ("Pass", s["pass"], "#16a34a"),
        ("Fail", s["fail"], "#dc2626"),
        ("Đã test", f'{s["done_pct"]}%', "#7c3aed"),
        ("Số màn hình", len(order), "#0891b2"),
    ]
    kpi_html = "".join(
        f'<div class="kpi" style="--c:{color}"><div class="kpi-val">{_esc(val)}</div>'
        f'<div class="kpi-label">{_esc(label)}</div></div>'
        for label, val, color in kpis
    )

    return _TEMPLATE.format(
        title=_esc(title), url=_esc(url), now=now,
        kpi_html=kpi_html, donut=_donut_svg(s),
        legend_pass=s["pass"], legend_fail=s["fail"],
        legend_blocked=s["blocked"], legend_stopped=s["stopped"],
        legend_untested=s["untested"],
        screen_rows="".join(screen_rows) or '<div class="muted">Chưa có dữ liệu màn hình.</div>',
        data_json=data_json,
    )


def to_bytes(test_cases: list[dict], url: str = "", title: str = "Báo cáo kiểm thử") -> bytes:
    return build_html(test_cases, url, title).encode("utf-8")


_TEMPLATE = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: "Segoe UI", Roboto, Arial, sans-serif; color: #1f2937; background: #f1f5f9; }}
  .wrap {{ max-width: 1100px; margin: 0 auto; padding: 24px 18px 60px; }}
  header.rep {{ background: linear-gradient(135deg, #2f5597, #1f3864); color: #fff;
    border-radius: 14px; padding: 22px 26px; box-shadow: 0 6px 20px rgba(31,56,100,.25); }}
  header.rep h1 {{ font-size: 24px; }}
  header.rep .meta {{ font-size: 13px; opacity: .9; margin-top: 6px; }}
  .kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 14px; margin: 20px 0; }}
  .kpi {{ background: #fff; border-radius: 12px; padding: 16px; border-top: 4px solid var(--c);
    box-shadow: 0 2px 8px rgba(0,0,0,.05); }}
  .kpi-val {{ font-size: 30px; font-weight: 800; color: var(--c); }}
  .kpi-label {{ font-size: 12px; color: #64748b; margin-top: 4px; }}
  .grid2 {{ display: grid; grid-template-columns: 240px 1fr; gap: 18px; }}
  @media (max-width: 720px) {{ .grid2 {{ grid-template-columns: 1fr; }} }}
  .card {{ background: #fff; border-radius: 12px; padding: 18px; box-shadow: 0 2px 8px rgba(0,0,0,.05); }}
  .card h2 {{ font-size: 15px; color: #1f3864; margin-bottom: 12px; }}
  .donut-card {{ display: flex; flex-direction: column; align-items: center; }}
  .legend {{ margin-top: 10px; width: 100%; font-size: 13px; }}
  .legend div {{ display: flex; justify-content: space-between; padding: 3px 0; }}
  .dot {{ display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 6px; }}
  .screen-row {{ display: grid; grid-template-columns: 1fr 200px 46px; align-items: center;
    gap: 10px; padding: 7px 0; border-bottom: 1px solid #f1f5f9; }}
  .screen-name {{ font-size: 13px; font-weight: 600; }}
  .screen-count {{ font-weight: 400; color: #94a3b8; font-size: 11px; }}
  .bar {{ height: 12px; background: #e2e8f0; border-radius: 6px; overflow: hidden; display: flex; }}
  .bar-pass {{ background: #16a34a; }} .bar-fail {{ background: #dc2626; }}
  .screen-pct {{ text-align: right; font-weight: 700; font-size: 13px; color: #1f3864; }}
  .toolbar {{ display: flex; gap: 10px; margin: 22px 0 10px; flex-wrap: wrap; align-items: center; }}
  .toolbar input, .toolbar select {{ padding: 8px 10px; border: 1px solid #cbd5e1; border-radius: 8px;
    font-size: 13px; }}
  .toolbar input {{ flex: 1; min-width: 180px; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff; border-radius: 12px;
    overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,.05); }}
  th, td {{ padding: 9px 11px; text-align: left; font-size: 12.5px; border-bottom: 1px solid #eef2f7;
    vertical-align: top; }}
  th {{ background: #2f5597; color: #fff; position: sticky; top: 0; font-size: 12px; }}
  tr:hover td {{ background: #f8fafc; }}
  td.pre {{ white-space: pre-wrap; max-width: 320px; }}
  .badge {{ font-size: 11px; font-weight: 700; padding: 2px 9px; border-radius: 20px; white-space: nowrap; }}
  .badge.pass {{ background: #dcfce7; color: #15803d; }}
  .badge.fail {{ background: #fee2e2; color: #b91c1c; }}
  .badge.blocked {{ background: #fef3c7; color: #b45309; }}
  .badge.untested {{ background: #e2e8f0; color: #475569; }}
  .muted {{ color: #94a3b8; font-size: 13px; }}
  footer.rep {{ text-align: center; color: #94a3b8; font-size: 12px; margin-top: 30px; }}
</style>
</head>
<body>
<div class="wrap">
  <header class="rep">
    <h1>🧪 {title}</h1>
    <div class="meta">URL: {url} · Xuất lúc: {now} · AutoTest</div>
  </header>

  <div class="kpis">{kpi_html}</div>

  <div class="grid2">
    <div class="card donut-card">
      <h2>Phân bố kết quả</h2>
      {donut}
      <div class="legend">
        <div><span><span class="dot" style="background:#16a34a"></span>Pass</span><b>{legend_pass}</b></div>
        <div><span><span class="dot" style="background:#dc2626"></span>Fail</span><b>{legend_fail}</b></div>
        <div><span><span class="dot" style="background:#d97706"></span>Blocked</span><b>{legend_blocked}</b></div>
        <div><span><span class="dot" style="background:#64748b"></span>Đã dừng</span><b>{legend_stopped}</b></div>
        <div><span><span class="dot" style="background:#cbd5e1"></span>Chưa test</span><b>{legend_untested}</b></div>
      </div>
    </div>
    <div class="card">
      <h2>Tiến độ pass theo màn hình</h2>
      {screen_rows}
    </div>
  </div>

  <div class="toolbar">
    <input id="q" placeholder="🔎 Tìm theo mã, chức năng, bước, kết quả...">
    <select id="filterStatus">
      <option value="">Tất cả tình trạng</option>
      <option value="pass">Chỉ Pass</option>
      <option value="fail">Chỉ Fail</option>
      <option value="blocked">Chỉ Blocked</option>
      <option value="untested">Chỉ Chưa test</option>
    </select>
    <span class="muted" id="shown"></span>
  </div>

  <table>
    <thead><tr>
      <th>STT</th><th>Mã TC</th><th>Màn hình</th><th>Chức năng</th><th>Loại</th>
      <th>Bước tái hiện</th><th>Kết quả mong muốn</th><th>Kết quả thực tế</th><th>Tình trạng</th>
    </tr></thead>
    <tbody id="tbody"></tbody>
  </table>

  <footer class="rep">Tạo bởi AutoTest — công cụ sinh &amp; chạy test case tự động bằng AI.</footer>
</div>

<script>
  const DATA = {data_json};
  const tbody = document.getElementById("tbody");
  const q = document.getElementById("q");
  const fs = document.getElementById("filterStatus");
  const shown = document.getElementById("shown");
  const LABEL = {{ pass: "Pass", fail: "Fail", blocked: "Blocked", untested: "Chưa test" }};
  function esc(s) {{
    if (s == null) return "";
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }}
  function render() {{
    const term = q.value.trim().toLowerCase();
    const st = fs.value;
    const rows = DATA.filter(r => {{
      if (st && r.status !== st) return false;
      if (!term) return true;
      return [r.id, r.screen, r.function, r.steps, r.expected, r.actual]
        .join(" ").toLowerCase().includes(term);
    }});
    tbody.innerHTML = "";
    for (const r of rows) {{
      const tr = document.createElement('tr');
      const cols = [r.stt, r.id, r.screen, r.function, r.ui_function, r.steps, r.expected, r.actual];
      for (let i = 0; i < cols.length; i++) {{
        const td = document.createElement('td');
        if (i >= 5) td.classList.add('pre');
        td.textContent = String(cols[i] || '');
        tr.appendChild(td);
      }}
      const tdStatus = document.createElement('td');
      const badge = document.createElement('span');
      badge.className = 'badge ' + r.status;
      badge.textContent = LABEL[r.status];
      tdStatus.appendChild(badge);
      tr.appendChild(tdStatus);
      tbody.appendChild(tr);
    }}
    shown.textContent = `Hiện ${{rows.length}}/${{DATA.length}} case`;
  }}
  q.addEventListener("input", render);
  fs.addEventListener("change", render);
  render();
</script>
</body>
</html>"""
