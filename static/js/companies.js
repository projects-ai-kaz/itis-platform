/**
 * static/js/companies.js
 * Вкладка «Компании» — загрузка данных, управление профилями, сравнение ITIS.
 */

// ─── State ────────────────────────────────────────────────────────────────────
let allCompanies = [];
let selectedIds = new Set();
let editingId = null;

// ─── Bootstrap ───────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  loadCompanies();

  // Upload form
  const uploadForm = document.getElementById("co-upload-form");
  if (uploadForm) uploadForm.addEventListener("submit", handleFileUpload);

  // Manual add
  const addModuleBtn = document.getElementById("co-add-module-btn");
  if (addModuleBtn) addModuleBtn.addEventListener("click", addModuleRow);

  const saveBtn = document.getElementById("co-save-btn");
  if (saveBtn) saveBtn.addEventListener("click", saveCompany);

  const cancelBtn = document.getElementById("co-cancel-btn");
  if (cancelBtn) cancelBtn.addEventListener("click", cancelEdit);

  // Compare button
  const compareBtn = document.getElementById("co-compare-btn");
  if (compareBtn) compareBtn.addEventListener("click", runComparison);

  // Export button
  const exportBtn = document.getElementById("co-export-btn");
  if (exportBtn) exportBtn.addEventListener("click", exportToExcel);
});

// ─── Load & Render ────────────────────────────────────────────────────────────
async function loadCompanies() {
  try {
    const res = await fetch("/api/companies/");
    const data = await res.json();
    allCompanies = data.companies || [];
    renderCompaniesTable();
  } catch (e) {
    showError("co-error", "Ошибка загрузки данных: " + e.message);
  }
}

function renderCompaniesTable() {
  const tbody = document.getElementById("co-table-body");
  if (!tbody) return;

  if (!allCompanies.length) {
    tbody.innerHTML = `<tr><td colspan="7" class="co-empty">
      Компаний пока нет. Загрузите CSV/Excel или добавьте вручную.
    </td></tr>`;
    return;
  }

  tbody.innerHTML = allCompanies
    .sort((a, b) => b.itis_score - a.itis_score)
    .map((cp, i) => {
      const scoreClass = cp.itis_score >= 0.7 ? "score-high"
        : cp.itis_score >= 0.45 ? "score-mid" : "score-low";
      const checked = selectedIds.has(cp.id) ? "checked" : "";
      return `<tr data-id="${cp.id}">
        <td><input type="checkbox" class="co-select-cb" data-id="${cp.id}" ${checked}
          onchange="toggleSelect('${cp.id}', this.checked)"></td>
        <td>${i + 1}</td>
        <td class="co-name">${esc(cp.name)}</td>
        <td>${esc(cp.industry || "—")}</td>
        <td>${esc(cp.country || "—")}</td>
        <td>${cp.modules ? cp.modules.length : 0}</td>
        <td class="${scoreClass} co-score">${cp.itis_score.toFixed(3)}</td>
        <td class="co-class">${esc(cp.itis_class)}</td>
        <td class="co-actions">
          <button class="btn-icon" title="Редактировать" onclick="editCompany('${cp.id}')">✏️</button>
          <button class="btn-icon" title="Удалить" onclick="deleteCompany('${cp.id}')">🗑️</button>
        </td>
      </tr>`;
    }).join("");
}

// ─── Select / Compare ────────────────────────────────────────────────────────
function toggleSelect(id, checked) {
  if (checked) selectedIds.add(id);
  else selectedIds.delete(id);

  const count = selectedIds.size;
  const compareBtn = document.getElementById("co-compare-btn");
  if (compareBtn) compareBtn.textContent =
    count > 0 ? `Сравнить выбранные (${count})` : "Сравнить все";
}

async function runComparison() {
  const ids = selectedIds.size > 0 ? [...selectedIds] : [];
  clearError("co-error");
  try {
    const res = await fetch("/api/companies/compare", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ids })
    });
    const data = await res.json();
    renderComparison(data.comparison || []);
  } catch (e) {
    showError("co-error", "Ошибка сравнения: " + e.message);
  }
}

function renderComparison(items) {
  const container = document.getElementById("co-comparison-result");
  if (!container) return;
  container.style.display = "block";

  if (!items.length) {
    container.innerHTML = "<p>Нет данных для сравнения.</p>";
    return;
  }

  // Bar chart (plain CSS bars)
  const maxScore = Math.max(...items.map(c => c.itis_score), 1);
  const bars = items.map(c => {
    const pct = ((c.itis_score / maxScore) * 100).toFixed(1);
    const cls = c.itis_score >= 0.7 ? "bar-high" : c.itis_score >= 0.45 ? "bar-mid" : "bar-low";
    return `<div class="co-bar-row">
      <div class="co-bar-label" title="${esc(c.name)}">${c.rank}. ${esc(c.name)}</div>
      <div class="co-bar-track">
        <div class="co-bar ${cls}" style="width:${pct}%"></div>
      </div>
      <div class="co-bar-value">${c.itis_score.toFixed(3)}</div>
    </div>`;
  }).join("");

  container.innerHTML = `
    <h3 class="co-compare-title">Сравнение ITIS — ${items.length} компани${items.length === 1 ? 'я' : items.length < 5 ? 'и' : 'й'}</h3>
    <div class="co-bar-chart">${bars}</div>
    <table class="co-compare-table">
      <thead>
        <tr><th>#</th><th>Компания</th><th>Отрасль</th><th>Страна</th><th>Модулей</th><th>ITIS</th><th>Класс</th></tr>
      </thead>
      <tbody>
        ${items.map(c => `<tr>
          <td>${c.rank}</td>
          <td>${esc(c.name)}</td>
          <td>${esc(c.industry || "—")}</td>
          <td>${esc(c.country || "—")}</td>
          <td>${c.modules_count}</td>
          <td class="${c.itis_score >= 0.7 ? 'score-high' : c.itis_score >= 0.45 ? 'score-mid' : 'score-low'}">${c.itis_score.toFixed(3)}</td>
          <td>${esc(c.itis_class)}</td>
        </tr>`).join("")}
      </tbody>
    </table>`;
}

// ─── Upload ───────────────────────────────────────────────────────────────────
async function handleFileUpload(e) {
  e.preventDefault();
  clearError("co-error");
  clearError("co-upload-status");

  const fileInput = document.getElementById("co-file-input");
  if (!fileInput || !fileInput.files.length) {
    showError("co-error", "Выберите файл для загрузки.");
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  const btn = document.getElementById("co-upload-btn");
  btn.disabled = true;
  btn.textContent = "Загружаю...";

  try {
    const res = await fetch("/api/companies/upload", {
      method: "POST",
      body: formData
    });
    const data = await res.json();

    if (!res.ok) {
      showError("co-error", data.error + (data.hint ? "\n" + data.hint : ""));
      return;
    }

    showSuccess("co-upload-status",
      `✅ Загружено ${data.imported} компани${data.imported === 1 ? 'я' : data.imported < 5 ? 'и' : 'й'}`);
    fileInput.value = "";
    await loadCompanies();
  } catch (err) {
    showError("co-error", "Ошибка при загрузке: " + err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Загрузить";
  }
}

// ─── Manual CRUD ──────────────────────────────────────────────────────────────
function showForm(data = null) {
  const panel = document.getElementById("co-form-panel");
  if (panel) panel.style.display = "block";
  document.getElementById("co-form-title").textContent =
    data ? "Редактировать компанию" : "Добавить компанию";

  document.getElementById("co-field-name").value = data?.name || "";
  document.getElementById("co-field-industry").value = data?.industry || "";
  document.getElementById("co-field-country").value = data?.country || "";
  document.getElementById("co-field-description").value = data?.description || "";

  const modulesContainer = document.getElementById("co-modules-container");
  modulesContainer.innerHTML = "";
  const modules = data?.modules || [{ name: "", E: "", W: "", C: "", M: "" }];
  modules.forEach(m => addModuleRow(m));
}

function editCompany(id) {
  const cp = allCompanies.find(c => c.id === id);
  if (!cp) return;
  editingId = id;
  showForm(cp);
  document.getElementById("co-form-panel")?.scrollIntoView({ behavior: "smooth" });
}

function cancelEdit() {
  editingId = null;
  const panel = document.getElementById("co-form-panel");
  if (panel) panel.style.display = "none";
  clearError("co-form-error");
}

function addModuleRow(data = {}) {
  const container = document.getElementById("co-modules-container");
  const row = document.createElement("div");
  row.className = "co-module-row";
  row.innerHTML = `
    <input class="co-mod-name" placeholder="Название модуля" value="${esc(data.name || '')}">
    <input class="co-mod-E" type="number" step="0.01" min="0" max="1" placeholder="E" value="${data.E ?? ''}">
    <input class="co-mod-W" type="number" step="0.01" min="0" max="1" placeholder="W" value="${data.W ?? ''}">
    <input class="co-mod-C" type="number" step="0.01" min="0" max="1" placeholder="C" value="${data.C ?? ''}">
    <input class="co-mod-M" type="number" step="0.01" min="0" max="1" placeholder="M" value="${data.M ?? ''}">
    <button type="button" class="btn-icon" title="Удалить строку" onclick="this.parentElement.remove()">✕</button>`;
  container.appendChild(row);
}

async function saveCompany() {
  clearError("co-form-error");

  const name = document.getElementById("co-field-name").value.trim();
  if (!name) { showError("co-form-error", "Введите название компании."); return; }

  const moduleRows = document.querySelectorAll(".co-module-row");
  const modules = [];
  let hasError = false;

  moduleRows.forEach(row => {
    const mName = row.querySelector(".co-mod-name").value.trim() || "Модуль";
    const E = parseFloat(row.querySelector(".co-mod-E").value);
    const W = parseFloat(row.querySelector(".co-mod-W").value);
    const C = parseFloat(row.querySelector(".co-mod-C").value);
    const M = parseFloat(row.querySelector(".co-mod-M").value);
    if ([E, W, C, M].some(isNaN)) { hasError = true; return; }
    modules.push({ name: mName, E, W, C, M });
  });

  if (hasError) { showError("co-form-error", "Заполните все поля E, W, C, M (числа от 0 до 1)."); return; }
  if (!modules.length) { showError("co-form-error", "Добавьте хотя бы один модуль."); return; }

  const body = {
    name,
    industry: document.getElementById("co-field-industry").value.trim(),
    country: document.getElementById("co-field-country").value.trim(),
    description: document.getElementById("co-field-description").value.trim(),
    modules
  };

  const url = editingId ? `/api/companies/${editingId}` : "/api/companies/";
  const method = editingId ? "PUT" : "POST";

  try {
    const res = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    if (!res.ok) {
      const err = await res.json();
      showError("co-form-error", err.error || "Ошибка сохранения.");
      return;
    }
    cancelEdit();
    await loadCompanies();
  } catch (e) {
    showError("co-form-error", "Ошибка: " + e.message);
  }
}

async function deleteCompany(id) {
  if (!confirm("Удалить эту компанию?")) return;
  try {
    await fetch(`/api/companies/${id}`, { method: "DELETE" });
    selectedIds.delete(id);
    await loadCompanies();
    // Обновим сравнение если нужно
    const result = document.getElementById("co-comparison-result");
    if (result && result.style.display !== "none") runComparison();
  } catch (e) {
    showError("co-error", "Ошибка удаления: " + e.message);
  }
}

// ─── Export ───────────────────────────────────────────────────────────────────
async function exportToExcel() {
  const ids = selectedIds.size > 0 ? [...selectedIds] : [];
  const res = await fetch("/export/companies/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ids })
  });
  if (!res.ok) { showError("co-error", "Ошибка экспорта."); return; }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = "companies_itis_report.xlsx"; a.click();
  URL.revokeObjectURL(url);
}

// ─── Utils ────────────────────────────────────────────────────────────────────
function esc(str) {
  return String(str)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function showError(id, msg) {
  const el = document.getElementById(id);
  if (el) { el.textContent = msg; el.style.display = "block"; el.className = "co-alert co-alert-error"; }
}

function showSuccess(id, msg) {
  const el = document.getElementById(id);
  if (el) { el.textContent = msg; el.style.display = "block"; el.className = "co-alert co-alert-success"; }
}

function clearError(id) {
  const el = document.getElementById(id);
  if (el) { el.textContent = ""; el.style.display = "none"; }
}
