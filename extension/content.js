// content.js — chạy trong ngữ cảnh trang web, quét DOM và tóm tắt cấu trúc giao diện.
// Trả về một chuỗi văn bản súc tích để gửi cho AI (không gửi toàn bộ HTML cho nhẹ & rẻ).

function scanPage() {
  const lines = [];

  // Tiêu đề trang
  lines.push(`Tiêu đề trang: ${document.title}`);

  // Thứ tự thành phần theo VỊ TRÍ (trên→dưới, trái→phải) để AI sinh test đúng thứ tự
  lines.push("\n=== THỨ TỰ THÀNH PHẦN TRÊN MÀN HÌNH (trên→dưới, trái→phải) ===");
  lines.push(readingOrder());

  // Các heading h1-h3
  const headings = [...document.querySelectorAll("h1, h2, h3")]
    .map((h) => `  - ${h.tagName}: ${clean(h.innerText)}`)
    .filter((t) => t.length > 8)
    .slice(0, 20);
  if (headings.length) lines.push("Tiêu đề mục:\n" + headings.join("\n"));

  // Các form và input bên trong
  const forms = [...document.querySelectorAll("form")];
  if (forms.length) {
    lines.push(`\nSố form: ${forms.length}`);
    forms.forEach((form, i) => {
      lines.push(`Form #${i + 1}:`);
      const fields = [...form.querySelectorAll("input, select, textarea")]
        .map(describeField)
        .filter(Boolean)
        .slice(0, 30);
      lines.push(fields.map((f) => "  " + f).join("\n"));
    });
  }

  // Các input nằm ngoài form
  const looseInputs = [...document.querySelectorAll("input, select, textarea")]
    .filter((el) => !el.closest("form"))
    .map(describeField)
    .filter(Boolean)
    .slice(0, 30);
  if (looseInputs.length) {
    lines.push("\nÔ nhập liệu (ngoài form):");
    lines.push(looseInputs.map((f) => "  " + f).join("\n"));
  }

  // Các nút bấm
  const buttons = [...document.querySelectorAll('button, input[type="submit"], input[type="button"], [role="button"]')]
    .map((b) => clean(b.innerText || b.value || b.getAttribute("aria-label")))
    .filter((t) => t)
    .slice(0, 25);
  if (buttons.length) lines.push("\nNút bấm: " + [...new Set(buttons)].join(" | "));

  // Các liên kết chính
  const links = [...document.querySelectorAll("a[href]")]
    .map((a) => clean(a.innerText))
    .filter((t) => t && t.length > 1)
    .slice(0, 30);
  if (links.length) lines.push("\nLiên kết: " + [...new Set(links)].slice(0, 25).join(" | "));

  // Tín hiệu trực quan (màu, cỡ chữ, accessibility, responsive)
  lines.push("\n=== TÍN HIỆU TRỰC QUAN (UI/UX) ===");
  lines.push(collectVisualSignals());

  return lines.join("\n");
}

// Liệt kê thành phần tương tác theo thứ tự đọc: trên→dưới, trái→phải (theo vị trí thật).
function readingOrder() {
  const sel = "h1,h2,h3,input,select,textarea,button,a[href],[role=button]";
  const items = [...document.querySelectorAll(sel)]
    .map((el) => ({ el, r: el.getBoundingClientRect() }))
    .filter((o) => o.r.width > 0 && o.r.height > 0)
    .sort((a, b) => {
      const band = Math.round(a.r.top / 30) - Math.round(b.r.top / 30);
      return band !== 0 ? band : a.r.left - b.r.left;
    })
    .slice(0, 60);
  const out = [];
  let i = 1;
  for (const { el } of items) {
    const label = describeElement(el);
    if (label) out.push(`${i++}. ${label}`);
  }
  return out.join("\n") || "(không nhận diện được thành phần)";
}

function describeElement(el) {
  const tag = el.tagName.toLowerCase();
  const txt = clean(el.innerText || el.value || el.getAttribute("placeholder") || el.getAttribute("aria-label"));
  if (tag === "input" || tag === "select" || tag === "textarea") {
    const type = el.getAttribute("type") || tag;
    if (type === "hidden") return null;
    return `[ô nhập ${type}] ${findLabel(el) || txt || el.getAttribute("name") || ""}`.trim();
  }
  if (tag === "button" || el.getAttribute("role") === "button") return txt ? `[nút] ${txt}` : null;
  if (tag === "a") return txt ? `[liên kết] ${txt}` : null;
  if (/^h[1-3]$/.test(tag)) return txt ? `[tiêu đề] ${txt}` : null;
  return txt || null;
}

// Thu thập màu sắc, cỡ chữ, vấn đề khả dụng để AI sinh test UI/UX sát thực tế.
function collectVisualSignals() {
  const out = [];

  // Bảng màu chữ & nền của các phần tử chính
  const colorEls = [...document.querySelectorAll("body, h1, h2, button, a, p, label")].slice(0, 60);
  const textColors = new Set();
  const bgColors = new Set();
  const fontSizes = new Set();
  let tinyFontCount = 0;

  for (const el of colorEls) {
    const cs = getComputedStyle(el);
    if (cs.color) textColors.add(cs.color);
    const bg = cs.backgroundColor;
    if (bg && bg !== "rgba(0, 0, 0, 0)" && bg !== "transparent") bgColors.add(bg);
    const size = parseFloat(cs.fontSize);
    if (size) {
      fontSizes.add(Math.round(size) + "px");
      if (size < 12) tinyFontCount++;
    }
  }
  out.push("Màu chữ dùng: " + [...textColors].slice(0, 8).join(", "));
  out.push("Màu nền dùng: " + ([...bgColors].slice(0, 8).join(", ") || "(không rõ)"));
  out.push("Cỡ chữ xuất hiện: " + [...fontSizes].sort((a, b) => parseInt(a) - parseInt(b)).join(", "));
  if (tinyFontCount) out.push(`⚠ Có ${tinyFontCount} phần tử cỡ chữ < 12px (khó đọc).`);

  // Font chính
  const bodyFont = getComputedStyle(document.body).fontFamily;
  out.push("Font chính: " + (bodyFont || "(không rõ)"));

  // Accessibility: ảnh thiếu alt
  const imgs = [...document.querySelectorAll("img")];
  const noAlt = imgs.filter((i) => !i.getAttribute("alt")).length;
  if (imgs.length) out.push(`Ảnh: ${imgs.length} tấm, trong đó ${noAlt} tấm THIẾU alt.`);

  // Nút có vùng chạm quá nhỏ (< 32px) — khó bấm trên mobile
  const smallBtns = [...document.querySelectorAll("button, a, [role=button]")].filter((b) => {
    const r = b.getBoundingClientRect();
    return r.width > 0 && (r.height < 32 || r.width < 32);
  }).length;
  if (smallBtns) out.push(`⚠ Có ${smallBtns} nút/liên kết vùng chạm < 32px (khó bấm trên mobile).`);

  // Input thiếu label gắn kèm
  const inputs = [...document.querySelectorAll("input, select, textarea")];
  const noLabel = inputs.filter((el) => !findLabel(el)).length;
  if (inputs.length) out.push(`Ô nhập: ${inputs.length}, trong đó ${noLabel} ô THIẾU nhãn (label).`);

  // Responsive: có thẻ meta viewport không?
  const hasViewport = !!document.querySelector('meta[name="viewport"]');
  out.push("Responsive viewport: " + (hasViewport ? "có" : "KHÔNG có (có thể vỡ trên mobile)"));

  // Ngôn ngữ trang
  out.push("Thuộc tính lang: " + (document.documentElement.lang || "(trống)"));

  return out.join("\n");
}

function describeField(el) {
  const tag = el.tagName.toLowerCase();
  const type = el.getAttribute("type") || (tag === "select" ? "select" : "text");
  const name = el.getAttribute("name") || el.id || "";
  const placeholder = el.getAttribute("placeholder") || "";
  const required = el.required ? " (bắt buộc)" : "";
  const label = findLabel(el);
  const parts = [`[${type}]`];
  if (label) parts.push(`nhãn="${label}"`);
  if (name) parts.push(`name="${name}"`);
  if (placeholder) parts.push(`placeholder="${placeholder}"`);
  const desc = parts.join(" ") + required;
  return desc.length > 6 ? desc : null;
}

function findLabel(el) {
  if (el.id) {
    const lbl = document.querySelector(`label[for="${el.id}"]`);
    if (lbl) return clean(lbl.innerText);
  }
  const parentLabel = el.closest("label");
  if (parentLabel) return clean(parentLabel.innerText);
  return el.getAttribute("aria-label") || "";
}

function clean(text) {
  return (text || "").replace(/\s+/g, " ").trim().slice(0, 120);
}

// Trả kết quả về cho popup qua chrome.scripting (giá trị return cuối cùng)
scanPage();
