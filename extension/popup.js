// popup.js — quét trang (DOM + ảnh) → Gemini sinh test case → tích lũy nhiều màn → xuất Excel.
// Bộ test case được lưu trong chrome.storage.local nên không mất khi đóng/mở lại popup.

const API = "http://127.0.0.1:8000"; // dùng 127.0.0.1 (IPv4) để tránh lỗi IPv6 của localhost

const els = {
  screenName: document.getElementById("screenName"),
  spec: document.getElementById("spec"),
  specFile: document.getElementById("specFile"),
  fileName: document.getElementById("fileName"),
  thorough: document.getElementById("thorough"),
  runToggle: document.getElementById("runToggle"),
  scanBtn: document.getElementById("scanBtn"),
  genBtn: document.getElementById("genBtn"),
  genMdBtn: document.getElementById("genMdBtn"),
  exportBtn: document.getElementById("exportBtn"),
  reportBtn: document.getElementById("reportBtn"),
  codeBtn: document.getElementById("codeBtn"),
  codePlatform: document.getElementById("codePlatform"),
  runBtn: document.getElementById("runBtn"),
  importFile: document.getElementById("importFile"),
  clearBtn: document.getElementById("clearBtn"),
  status: document.getElementById("status"),
  setBar: document.getElementById("setBar"),
  setInfo: document.getElementById("setInfo"),
  result: document.getElementById("result"),
  count: document.getElementById("count"),
  list: document.getElementById("list"),
  // Dashboard
  dashBody: document.getElementById("dashBody"),
  dashToggle: document.getElementById("dashToggle"),
  kTotal: document.getElementById("kTotal"),
  kPass: document.getElementById("kPass"),
  kFail: document.getElementById("kFail"),
  kDone: document.getElementById("kDone"),
  donut: document.getElementById("donut"),
  donutPct: document.getElementById("donutPct"),
  screens: document.getElementById("screens"),
  history: document.getElementById("history"),
};

let runHistory = []; // [{t, url, pass, fail, manual, total}]

// Phân loại tình trạng để thống kê (khớp logic backend)
function classify(status) {
  const v = String(status || "").trim().toLowerCase();
  if (["pass", "passed", "đạt", "ok"].includes(v)) return "pass";
  if (["fail", "failed", "lỗi", "không đạt", "ng"].includes(v)) return "fail";
  if (["blocked", "block", "pending"].includes(v)) return "blocked";
  return "untested";
}

function statsOf(list) {
  const s = { total: list.length, pass: 0, fail: 0, blocked: 0, untested: 0 };
  for (const c of list) s[classify(c.status)]++;
  s.done = s.pass + s.fail + s.blocked;
  s.passPct = s.total ? Math.round((s.pass / s.total) * 100) : 0;
  s.donePct = s.total ? Math.round((s.done / s.total) * 100) : 0;
  return s;
}

// Vẽ bảng điều khiển từ bộ case hiện tại
function renderDashboard() {
  const s = statsOf(cases);
  els.kTotal.textContent = s.total;
  els.kPass.textContent = s.pass;
  els.kFail.textContent = s.fail;
  els.kDone.textContent = s.donePct + "%";

  // Donut bằng conic-gradient: pass(xanh) → fail(đỏ) → blocked(cam) → chưa test(xám)
  const total = s.total || 1;
  const seg = (n) => (n / total) * 360;
  let a = 0;
  const stops = [];
  const push = (color, n) => { if (n > 0) { stops.push(`${color} ${a}deg ${a + seg(n)}deg`); a += seg(n); } };
  push("#16a34a", s.pass);
  push("#dc2626", s.fail);
  push("#d97706", s.blocked);
  push("#cbd5e1", s.untested);
  els.donut.style.background = stops.length
    ? `conic-gradient(${stops.join(", ")})`
    : "#e2e8f0";
  els.donutPct.textContent = s.passPct + "%";

  // Tiến độ theo màn hình
  const byScreen = {};
  const order = [];
  for (const c of cases) {
    const scr = c.screen || "Chung";
    if (!byScreen[scr]) { byScreen[scr] = []; order.push(scr); }
    byScreen[scr].push(c);
  }
  els.screens.innerHTML = order.map((scr) => {
    const ss = statsOf(byScreen[scr]);
    const failPct = ss.total ? Math.round((ss.fail / ss.total) * 100) : 0;
    return `<div class="screen-row">
      <div class="sr-top"><span class="sr-name">${esc(scr)} (${ss.total})</span><span class="sr-pct">${ss.passPct}%</span></div>
      <div class="sr-bar"><span class="sr-pass" style="width:${ss.passPct}%"></span><span class="sr-fail" style="width:${failPct}%"></span></div>
    </div>`;
  }).join("") || '<div class="hist-empty">Chưa có dữ liệu màn hình.</div>';

  renderHistory();
}

function renderHistory() {
  if (!runHistory.length) {
    els.history.innerHTML = '<div class="history-title">🕘 Lịch sử chạy</div><div class="hist-empty">Chưa có lần chạy nào.</div>';
    return;
  }
  const rows = runHistory.slice(-5).reverse().map((h) => {
    const tot = h.total || 1;
    const passW = Math.round((h.pass / tot) * 100);
    const failW = Math.round((h.fail / tot) * 100);
    return `<div class="hist-row">
      <span class="hist-time">${esc(h.t)}</span>
      <span class="hist-bar"><span class="hb-pass" style="width:${passW}%"></span><span class="hb-fail" style="width:${failW}%"></span></span>
      <span class="hist-stat" style="color:#16a34a">${h.pass}✓</span>
      <span class="hist-stat" style="color:#dc2626">${h.fail}✗</span>
    </div>`;
  }).join("");
  els.history.innerHTML = '<div class="history-title">🕘 Lịch sử chạy (5 gần nhất)</div>' + rows;
}

// Lưu một mốc lịch sử sau khi chạy test
function pushHistory(stat, url) {
  const now = new Date();
  const t = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")} ${String(now.getDate()).padStart(2, "0")}/${String(now.getMonth() + 1).padStart(2, "0")}`;
  runHistory.push({ t, url: url || "", pass: stat.pass, fail: stat.fail, manual: stat.manual || 0, total: stat.total });
  runHistory = runHistory.slice(-20); // giữ tối đa 20 lần
  chrome.storage.local.set({ autotest_history: runHistory });
  renderHistory();
}

let domSummary = "";
let pageUrl = "";
let screenshot = "";
let cases = []; // bộ test case tích lũy (toàn bộ màn hình)

function setStatus(msg, type = "") {
  els.status.textContent = msg;
  els.status.className = "status " + type;
}

function sig(c) {
  const n = (s) => String(s || "").replace(/\s+/g, " ").trim().toLowerCase();
  return [n(c.screen), n(c.function), n(c.steps), n(c.expected)].join("|");
}

function mergeCases(existing, incoming) {
  const seen = new Set(existing.map(sig));
  const out = existing.slice();
  for (const c of incoming) {
    const s = sig(c);
    if (!seen.has(s)) {
      seen.add(s);
      out.push(c);
    }
  }
  return out;
}

// Gộp + CẬP NHẬT theo Mã TC: case cùng Mã TC -> thay thế (cập nhật); Mã TC mới -> thêm.
function updateMerge(existing, incoming) {
  const idx = {};
  existing.forEach((c, i) => { if (c.id) idx[c.id] = i; });
  const out = existing.slice();
  const seen = new Set(existing.map(sig));
  for (const c of incoming) {
    if (c.id && idx[c.id] !== undefined) {
      out[idx[c.id]] = c; // cập nhật case đã sửa
    } else if (!seen.has(sig(c))) {
      seen.add(sig(c));
      out.push(c); // case mới thêm vào
    }
  }
  return out;
}

function saveSet() {
  chrome.storage.local.set({ autotest_cases: cases });
}

function renderSet() {
  const screens = new Set(cases.map((c) => c.screen || "Chung"));
  els.setInfo.textContent = `Bộ hiện tại: ${cases.length} test case · ${screens.size} màn hình`;
  els.setBar.classList.toggle("hidden", cases.length === 0);

  els.count.textContent = `${cases.length} test case`;
  els.list.innerHTML = "";
  // Hiển thị tối đa 40 case gần nhất để nhẹ
  for (const tc of cases.slice(-40).reverse()) {
    const div = document.createElement("div");
    div.className = "tc";
    const subFn = tc.sub_function ? " › " + tc.sub_function : "";
    const st = tc.status ? ` · ${esc(tc.status)}` : "";
    div.innerHTML = `
      <button class="tc-del" data-id="${esc(tc.id)}" title="Xóa case này">×</button>
      <div class="tc-id">${esc(tc.id || "")} · ${esc(tc.screen || "")} · ${esc(tc.ui_function || "")}${st}</div>
      <div class="tc-title">${esc((tc.function || "") + subFn)}</div>
      <div class="tc-meta">${esc(tc.expected || "")}</div>`;
    els.list.appendChild(div);
  }
  els.result.classList.toggle("hidden", cases.length === 0);
  renderDashboard();
}

// Ẩn/hiện thân dashboard
els.dashToggle.addEventListener("click", () => {
  const hidden = els.dashBody.classList.toggle("hidden");
  els.dashToggle.textContent = hidden ? "Hiện" : "Ẩn";
});

// Xóa một case (bấm dấu ×)
els.list.addEventListener("click", (e) => {
  const btn = e.target.closest(".tc-del");
  if (!btn) return;
  const id = btn.getAttribute("data-id");
  cases = cases.filter((c) => c.id !== id);
  cases.forEach((c, i) => (c.id = `TC_${String(i + 1).padStart(3, "0")}`)); // đánh lại số
  saveSet();
  renderSet();
  setStatus(`Đã xóa 1 case. Còn ${cases.length} case.`, "ok");
});

function applyRunToggle() {
  els.runBtn.style.display = els.runToggle.checked ? "" : "none";
}

// Nạp bộ đã lưu + lịch sử + trạng thái công tắc khi mở popup
chrome.storage.local.get(["autotest_cases", "autotest_runEnabled", "autotest_history"], (data) => {
  cases = data.autotest_cases || [];
  runHistory = data.autotest_history || [];
  els.runToggle.checked = !!data.autotest_runEnabled; // mặc định TẮT
  applyRunToggle();
  renderSet();
  if (cases.length) setStatus(`Đã nạp bộ cũ: ${cases.length} test case.`, "ok");
});

els.runToggle.addEventListener("change", () => {
  chrome.storage.local.set({ autotest_runEnabled: els.runToggle.checked });
  applyRunToggle();
});

// --- Upload file đặc tả ---
els.specFile.addEventListener("change", async () => {
  const file = els.specFile.files[0];
  if (!file) return;
  els.fileName.textContent = "Đang đọc " + file.name + "...";
  const ext = file.name.toLowerCase().split(".").pop();
  try {
    if (["txt", "md", "csv", "log"].includes(ext)) {
      const text = await file.text();
      els.spec.value = text.trim();
      els.fileName.textContent = `✓ ${file.name} (${text.length} ký tự)`;
    } else {
      const form = new FormData();
      form.append("file", file);
      const resp = await fetch(`${API}/extract`, { method: "POST", body: form });
      if (!resp.ok) throw new Error((await resp.json().catch(() => ({}))).detail || resp.statusText);
      const data = await resp.json();
      els.spec.value = data.text || "";
      els.fileName.textContent = `✓ ${data.filename} (${data.chars} ký tự)`;
    }
  } catch (err) {
    els.fileName.textContent = "✗ Lỗi đọc file: " +
      (err.message.includes("Failed to fetch") ? "backend chưa chạy?" : err.message);
  }
});

// --- Bước 1: quét trang ---
els.scanBtn.addEventListener("click", async () => {
  setStatus("Đang quét trang...");
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    pageUrl = tab.url || "";
    const [res] = await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["content.js"] });
    domSummary = res.result || "";
    if (!domSummary) {
      setStatus("Không đọc được nội dung trang này.", "error");
      return;
    }
    try {
      const dataUrl = await chrome.tabs.captureVisibleTab(tab.windowId, { format: "jpeg", quality: 70 });
      screenshot = (dataUrl || "").split(",")[1] || "";
    } catch (e) {
      screenshot = "";
    }
    setStatus(`Đã quét xong (${domSummary.length} ký tự${screenshot ? " + ảnh màn hình" : ""}). Bấm "Sinh test case".`, "ok");
    els.genBtn.disabled = false;
    els.genMdBtn.disabled = false;
  } catch (err) {
    setStatus("Lỗi quét trang: " + err.message + " (trang chrome:// không quét được)", "error");
  }
});

// --- Bước 2: sinh test case (nối hoặc tạo mới) ---
els.genBtn.addEventListener("click", async () => {
  const thorough = els.thorough.checked;
  const mode = document.querySelector('input[name="mode"]:checked').value;
  const screen = els.screenName.value.trim();
  setStatus(thorough ? "AI đang vét cạn nhiều nhóm quan điểm, chờ ~40 giây..." : "AI đang sinh test case, chờ ~20 giây...");
  els.genBtn.disabled = true;
  els.scanBtn.disabled = true;
  try {
    const resp = await fetch(`${API}/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: pageUrl, dom_summary: domSummary, spec: els.spec.value, thorough, screenshot }),
    });
    if (!resp.ok) throw new Error((await resp.json().catch(() => ({}))).detail || resp.statusText);
    const data = await resp.json();
    let fresh = data.test_cases || [];
    if (fresh.length === 0) {
      setStatus("⚠️ Không sinh được test case. Thử lại hoặc thêm mô tả rõ hơn.", "error");
      return;
    }
    // Ép tên màn hình nếu người dùng nhập
    if (screen) fresh = fresh.map((c) => ({ ...c, screen }));

    const before = cases.length;
    if (mode === "new") {
      cases = fresh;
    } else {
      cases = mergeCases(cases, fresh);
    }
    saveSet();
    renderSet();
    const added = mode === "new" ? fresh.length : cases.length - before;
    setStatus(`✓ Sinh ${fresh.length} case (thêm ${added} mới). Bộ hiện có ${cases.length} case.`, "ok");
    // Công tắc BẬT -> tự động chạy test luôn
    if (els.runToggle.checked) {
      els.genBtn.disabled = false;
      els.scanBtn.disabled = false;
      await runAutoTests();
    }
  } catch (err) {
    const hint = err.message.includes("Failed to fetch")
      ? "Backend chưa chạy? Mở terminal chạy uvicorn."
      : err.message;
    setStatus("Lỗi: " + hint, "error");
  } finally {
    els.genBtn.disabled = false;
    els.scanBtn.disabled = false;
  }
});

// --- Nhập (gộp) file test case Excel cũ ---
els.importFile.addEventListener("change", async () => {
  const file = els.importFile.files[0];
  if (!file) return;
  setStatus("Đang đọc file test case cũ...");
  try {
    const form = new FormData();
    form.append("file", file);
    const resp = await fetch(`${API}/import_cases`, { method: "POST", body: form });
    if (!resp.ok) throw new Error((await resp.json().catch(() => ({}))).detail || resp.statusText);
    const data = await resp.json();
    const before = cases.length;
    cases = updateMerge(cases, data.test_cases || []); // cập nhật theo Mã TC + thêm case mới
    saveSet();
    renderSet();
    const added = cases.length - before;
    setStatus(`✓ Đã nhập ${data.count} case (cập nhật theo Mã TC, thêm mới ${added}). Bộ hiện có ${cases.length} case.`, "ok");
  } catch (err) {
    setStatus("Lỗi nhập file: " + err.message, "error");
  } finally {
    els.importFile.value = "";
  }
});

// --- Xóa bộ ---
els.clearBtn.addEventListener("click", () => {
  if (!cases.length) return;
  if (!confirm(`Xóa toàn bộ ${cases.length} test case trong bộ hiện tại?`)) return;
  cases = [];
  saveSet();
  renderSet();
  setStatus("Đã xóa bộ. Bắt đầu bộ mới.", "ok");
});

// --- Chạy test tự động (chế độ AN TOÀN) trên trang đang mở ---
els.runBtn.addEventListener("click", () => runAutoTests());

async function runAutoTests() {
  if (!cases.length) {
    setStatus("⚠️ Chưa có test case để chạy.", "error");
    return;
  }
  els.runBtn.disabled = true;
  setStatus("Đang chuẩn bị chạy test trên trang hiện tại...");
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    // Quét lại DOM hiện tại để lập kế hoạch sát trang
    const [scan] = await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["content.js"] });
    const dom = scan.result || "";

    // Chỉ chạy case của màn hình đang nhập (nếu có), nếu không thì chạy tất cả
    const scr = els.screenName.value.trim();
    const target = scr ? cases.filter((c) => (c.screen || "") === scr) : cases;
    if (!target.length) {
      setStatus("⚠️ Không có case của màn hình này. Bỏ trống 'Tên màn hình' để chạy tất cả.", "error");
      return;
    }

    setStatus(`AI đang lập kế hoạch chạy cho ${target.length} case...`);
    const resp = await fetch(`${API}/plan_auto`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dom_summary: dom, test_cases: target }),
    });
    if (!resp.ok) throw new Error((await resp.json().catch(() => ({}))).detail || resp.statusText);
    const plans = (await resp.json()).plans || [];

    const safe = plans.filter((p) => p.runnable && p.risk !== "confirm");
    const confirmPlans = plans.filter((p) => p.runnable && p.risk === "confirm");
    const manualPlans = plans.filter((p) => !p.runnable);
    let results = [];

    // 1) Case AN TOÀN: chạy luôn 1 lượt
    if (safe.length) {
      setStatus(`Đang chạy ${safe.length} case an toàn...`);
      const [ex] = await chrome.scripting.executeScript({ target: { tabId: tab.id }, func: runPlans, args: [safe] });
      results = results.concat(ex.result || []);
    }

    // 2) Case ẢNH HƯỞNG DỮ LIỆU: hỏi xác nhận TỪNG case trước khi chạy
    for (const p of confirmPlans) {
      const c = cases.find((x) => x.id === p.id) || {};
      const ok = confirm(
        `⚠️ XÁC NHẬN THỰC THI — ${p.id}\n\n` +
        `Chức năng: ${c.function || ""}\n` +
        `Mong đợi: ${(c.expected || "").slice(0, 100)}\n\n` +
        `Test này SẼ THAO TÁC ẢNH HƯỞNG DỮ LIỆU THẬT trên web (tạo / sửa / XÓA...).\n\n` +
        `Bấm OK = CHO PHÉP chạy.  Cancel = KHÔNG cho phép (bỏ qua).`
      );
      if (!ok) {
        results.push({ id: p.id, status: "Chưa test", actual: "⛔ Bạn KHÔNG cho phép thực thi (đã bỏ qua)" });
        continue;
      }
      const [ex] = await chrome.scripting.executeScript({ target: { tabId: tab.id }, func: runPlans, args: [[p]] });
      results = results.concat(ex.result || []);
    }

    // 3) Case không tự chạy được
    for (const p of manualPlans) {
      results.push({ id: p.id, status: "Manual", actual: p.reason || "Cần test thủ công" });
    }

    // Ghi kết quả vào bộ case theo id
    const byId = Object.fromEntries(results.map((r) => [r.id, r]));
    let pass = 0, fail = 0, manual = 0, skip = 0;
    for (const c of cases) {
      const r = byId[c.id];
      if (!r) continue;
      c.actual = r.actual || "";
      if (r.status === "Pass") { c.status = "Pass"; pass++; }
      else if (r.status === "Fail") { c.status = "Fail"; fail++; }
      else if (r.status === "Manual") { c.status = ""; manual++; }
      else { c.status = ""; skip++; }
    }
    saveSet();
    renderSet();
    // Ghi một mốc vào lịch sử chạy (xu hướng pass/fail theo thời gian)
    pushHistory({ pass, fail, manual, total: pass + fail + manual + skip }, tab.url);
    setStatus(`✓ Xong: ${pass} Pass · ${fail} Fail · ${manual} thủ công · ${skip} bỏ qua. Bấm Tải Excel/Báo cáo để lưu.`, "ok");
  } catch (err) {
    const hint = err.message.includes("Failed to fetch") ? "Backend chưa chạy?" : err.message;
    setStatus("Lỗi chạy test: " + hint, "error");
  } finally {
    els.runBtn.disabled = false;
  }
}

// Hàm chạy trong ngữ cảnh trang (phải tự chứa, không tham chiếu ngoài).
async function runPlans(plans) {
  const norm = (s) => (s || "").toString().trim().toLowerCase();
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  // Locator TỰ CHỮA (self-healing): thử nhiều chiến lược, CHẤM ĐIỂM, chọn ứng viên tốt nhất.
  // Khi locator trực tiếp (label/thuộc tính khớp nguyên văn) hỏng do UI đổi, vẫn dò lại được
  // bằng khớp một phần hoặc khớp theo từ khóa -> đánh dấu healed=true.
  function findEl(hint) {
    const h = norm(hint);
    if (!h) return null;
    const tokens = h.split(/\s+/).filter((t) => t.length > 1);
    const cands = [];
    const visible = (el) => { const r = el.getBoundingClientRect(); return r.width > 0 || r.height > 0; };
    const add = (el, score, strat) => { if (el && visible(el)) cands.push({ el, score, strat }); };
    const allTok = (text) => tokens.length > 0 && tokens.every((t) => text.includes(t));

    // 1) Nhãn <label> -> ô điều khiển (chính xác nhất)
    for (const l of document.querySelectorAll("label")) {
      const lt = norm(l.innerText);
      if (!lt) continue;
      let ctrl = null;
      const f = l.getAttribute("for");
      if (f) ctrl = document.getElementById(f);
      if (!ctrl) ctrl = l.querySelector("input,select,textarea");
      if (!ctrl) continue;
      if (lt === h) add(ctrl, 100, "nhãn khớp đúng");
      else if (lt.includes(h) || h.includes(lt)) add(ctrl, 82, "nhãn khớp một phần");
      else if (allTok(lt)) add(ctrl, 60, "nhãn khớp từ khóa (tự dò lại)");
    }
    // 2) Thuộc tính ô nhập: name / id / placeholder / aria-label
    for (const e of document.querySelectorAll("input,select,textarea")) {
      if (e.type === "hidden") continue;
      const attrs = norm([e.getAttribute("name"), e.id, e.getAttribute("placeholder"),
        e.getAttribute("aria-label")].filter(Boolean).join(" "));
      if (!attrs) continue;
      if (attrs === h) add(e, 95, "thuộc tính khớp đúng");
      else if (attrs.includes(h)) add(e, 72, "thuộc tính khớp một phần");
      else if (allTok(attrs)) add(e, 55, "thuộc tính khớp từ khóa (tự dò lại)");
    }
    // 3) Nút / liên kết theo chữ hiển thị
    for (const c of document.querySelectorAll("button,a,[role=button],input[type=submit],input[type=button]")) {
      const t = norm(c.innerText || c.value || c.getAttribute("aria-label"));
      if (!t) continue;
      if (t === h) add(c, 95, "chữ nút khớp đúng");
      else if (t.includes(h) || h.includes(t)) add(c, 76, "chữ nút khớp một phần");
      else if (allTok(t)) add(c, 50, "chữ nút khớp từ khóa (tự dò lại)");
    }
    if (!cands.length) return null;
    cands.sort((a, b) => b.score - a.score);
    const best = cands[0];
    return { el: best.el, strat: best.strat, healed: best.score < 80 };
  }
  // Lấy phần tử (tương thích code cũ) + ghi chú self-healing nếu phải dò lại
  const pick = (hint) => findEl(hint);
  const healNote = (m) => (m && m.healed ? ` ⚙️ tự dò lại (${m.strat})` : "");
  const bodyText = () => norm(document.body.innerText);
  const results = [];
  for (const p of plans) {
    try {
      if (!p.runnable) {
        results.push({ id: p.id, status: "Manual", actual: p.reason || "Cần test thủ công" });
        continue;
      }
      if (p.type === "ui") {
        const m = pick(p.find);
        const e = m && m.el;
        let ok = false, actual = "";
        if (p.assert === "is_password") {
          ok = e && e.tagName === "INPUT" && e.type === "password";
          actual = ok ? "Ô hiển thị dạng mật khẩu (●)" : "Không phải ô mật khẩu / không tìm thấy";
        } else if (p.assert === "absent") {
          ok = !e && !bodyText().includes(norm(p.find));
          actual = ok ? "Không hiển thị (đúng)" : "Vẫn hiển thị";
        } else {
          ok = !!e || bodyText().includes(norm(p.find));
          actual = ok ? "Hiển thị đúng" : "Không tìm thấy phần tử/đoạn chữ";
        }
        results.push({ id: p.id, status: ok ? "Pass" : "Fail", actual: actual + (e ? healNote(m) : "") });
      } else if (p.type === "validation") {
        let heal = "";
        for (const inp of p.inputs || []) {
          const m = pick(inp.find);
          const e = m && m.el;
          if (e && ["INPUT", "TEXTAREA", "SELECT"].includes(e.tagName)) {
            e.focus();
            e.value = inp.value || "";
            e.dispatchEvent(new Event("input", { bubbles: true }));
            e.dispatchEvent(new Event("change", { bubbles: true }));
            heal += healNote(m);
          }
        }
        const before = bodyText();
        const bm = pick(p.submit);
        const btn = bm && bm.el;
        if (btn) { btn.click(); heal += healNote(bm); }
        await sleep(900);
        const after = bodyText();
        const want = norm(p.assert_text);
        const ok = want ? after.includes(want) : after !== before;
        results.push({
          id: p.id,
          status: ok ? "Pass" : "Fail",
          actual: (ok ? "Có hiển thị thông báo lỗi mong đợi" : "Không thấy thông báo lỗi mong đợi") + heal,
        });
      } else if (p.type === "action") {
        // Case THAY ĐỔI DỮ LIỆU (đã được người dùng cho phép). Tự chấp nhận dialog xác nhận của web.
        try { window.confirm = () => true; window.alert = () => {}; } catch (e) {}
        let heal = "";
        for (const inp of p.inputs || []) {
          const m = pick(inp.find);
          const e = m && m.el;
          if (e && ["INPUT", "TEXTAREA", "SELECT"].includes(e.tagName)) {
            e.focus();
            e.value = inp.value || "";
            e.dispatchEvent(new Event("input", { bubbles: true }));
            e.dispatchEvent(new Event("change", { bubbles: true }));
            heal += healNote(m);
          }
        }
        const before = bodyText();
        const bm = pick(p.submit);
        const btn = bm && bm.el;
        if (btn) { btn.click(); heal += healNote(bm); }
        await sleep(1200);
        let after = "";
        try { after = bodyText(); } catch (e) { after = ""; }
        const want = norm(p.assert_text);
        const ok = want ? after.includes(want) : (after && after !== before);
        results.push({
          id: p.id,
          status: ok ? "Pass" : "Fail",
          actual: (ok ? "Đã thực hiện — có dấu hiệu thành công" : "Đã thực hiện — chưa thấy dấu hiệu thành công (kiểm tra lại)") + heal,
        });
      } else {
        results.push({ id: p.id, status: "Manual", actual: "Không xác định cách chạy" });
      }
    } catch (e) {
      results.push({ id: p.id, status: "Fail", actual: "Lỗi khi chạy: " + e.message });
    }
  }
  return results;
}

// --- Tải Excel (toàn bộ bộ) ---
els.exportBtn.addEventListener("click", async () => {
  if (!cases.length) {
    setStatus("⚠️ Chưa có test case để tải.", "error");
    return;
  }
  setStatus("Đang tạo file Excel...");
  els.exportBtn.disabled = true;
  try {
    const resp = await fetch(`${API}/export`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: pageUrl, test_cases: cases }),
    });
    if (!resp.ok) throw new Error("Export thất bại");
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "test_cases.xlsx";
    a.click();
    URL.revokeObjectURL(url);
    const screens = new Set(cases.map((c) => c.screen || "Chung")).size;
    setStatus(`✓ Đã tải Excel: ${cases.length} case · ${screens} sheet màn hình. Xem thư mục Tải xuống.`, "ok");
  } catch (err) {
    setStatus("Lỗi tải Excel: " + err.message, "error");
  } finally {
    els.exportBtn.disabled = false;
  }
});

// --- Tải BÁO CÁO HTML (chia sẻ/trình bày) ---
els.reportBtn.addEventListener("click", async () => {
  if (!cases.length) {
    setStatus("⚠️ Chưa có test case để xuất báo cáo.", "error");
    return;
  }
  setStatus("Đang tạo báo cáo HTML...");
  els.reportBtn.disabled = true;
  try {
    const title = els.screenName.value.trim()
      ? `Báo cáo kiểm thử — ${els.screenName.value.trim()}`
      : "Báo cáo kiểm thử";
    const resp = await fetch(`${API}/export_html`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: pageUrl, test_cases: cases, title }),
    });
    if (!resp.ok) throw new Error("Tạo báo cáo thất bại");
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "bao_cao_test.html";
    a.click();
    URL.revokeObjectURL(url);
    setStatus(`✓ Đã tải báo cáo HTML (${cases.length} case). Mở bằng trình duyệt để xem/chia sẻ.`, "ok");
  } catch (err) {
    const hint = err.message.includes("Failed to fetch") ? "Backend chưa chạy?" : err.message;
    setStatus("Lỗi tạo báo cáo: " + hint, "error");
  } finally {
    els.reportBtn.disabled = false;
  }
});

// Tải một chuỗi văn bản về máy thành file
function downloadText(text, filename, mime = "text/plain") {
  const blob = new Blob([text], { type: mime + ";charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// --- Tự sinh tài liệu .md từ trang (AI đọc DOM → đặc tả Markdown) ---
els.genMdBtn.addEventListener("click", async () => {
  if (!domSummary) {
    setStatus("⚠️ Hãy bấm '1 · Quét trang' trước.", "error");
    return;
  }
  setStatus("AI đang đọc trang và viết tài liệu .md...");
  els.genMdBtn.disabled = true;
  try {
    const resp = await fetch(`${API}/gen_spec_md`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: pageUrl, dom_summary: domSummary, spec: els.spec.value }),
    });
    if (!resp.ok) throw new Error((await resp.json().catch(() => ({}))).detail || resp.statusText);
    const data = await resp.json();
    els.spec.value = data.markdown || ""; // điền lại vào ô đặc tả để dùng sinh test/code
    const scr = els.screenName.value.trim().replace(/[^\p{L}\p{N}]+/gu, "_") || "trang";
    downloadText(data.markdown || "", `dactata_${scr}.md`, "text/markdown");
    setStatus(`✓ Đã sinh tài liệu .md (${data.chars} ký tự) — đã điền vào ô đặc tả & tải file.`, "ok");
  } catch (err) {
    const hint = err.message.includes("Failed to fetch") ? "Backend chưa chạy?" : err.message;
    setStatus("Lỗi sinh .md: " + hint, "error");
  } finally {
    els.genMdBtn.disabled = false;
  }
});

// --- Sinh CODE pytest + Playwright từ bộ test case (cắm được CI/CD) ---
els.codeBtn.addEventListener("click", async () => {
  if (!cases.length) {
    setStatus("⚠️ Chưa có test case để sinh code.", "error");
    return;
  }
  const platform = els.codePlatform.value; // "web" | "android"
  const target = platform === "android" ? "Appium (mobile)" : "Playwright (web)";
  setStatus(`AI đang sinh code ${target} (chờ ~30 giây)...`);
  els.codeBtn.disabled = true;
  try {
    const resp = await fetch(`${API}/gen_code`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: pageUrl, dom_summary: domSummary, spec: els.spec.value, test_cases: cases, platform }),
    });
    if (!resp.ok) throw new Error((await resp.json().catch(() => ({}))).detail || resp.statusText);
    const data = await resp.json();
    const fname = platform === "android" ? "test_appium.py" : "test_playwright.py";
    downloadText(data.code || "", fname, "text/x-python");
    setStatus(`✓ Đã sinh code ${data.target} (${data.lines} dòng) → ${fname}. Xem hướng dẫn chạy trong README.`, "ok");
  } catch (err) {
    const hint = err.message.includes("Failed to fetch") ? "Backend chưa chạy?" : err.message;
    setStatus("Lỗi sinh code: " + hint, "error");
  } finally {
    els.codeBtn.disabled = false;
  }
});

function esc(s) {
  return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}
