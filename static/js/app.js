/* static/js/app.js — Shared utilities & page switching */
"use strict";

const COLS = ['#00e5b4','#3b82f6','#f59e0b','#d946ef','#22d3ee','#f97316','#a78bfa','#34d399'];

function switchPage(id, btn) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  btn.classList.add('active');
  if (id === 'p2') renderBak();
}

function toast(msg, col = '#00e5b4') {
  const t = document.getElementById('toast');
  t.textContent = msg; t.style.color = col; t.style.borderColor = col + '44';
  t.classList.add('show'); setTimeout(() => t.classList.remove('show'), 2500);
}

async function apiPost(url, body) {
  const r = await fetch(url, {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data.error || r.statusText);
  return data;
}

async function downloadFile(url, body, filename) {
  const r = await fetch(url, {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  });
  if (!r.ok) { const e = await r.json(); throw new Error(e.error); }
  const blob = await r.blob();
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = filename; a.click();
  URL.revokeObjectURL(a.href);
}

async function doExport() {
  const active = document.querySelector('.page.active').id;
  try {
    if (active === 'p1') await exportITIS();
    else if (active === 'p2') await exportBAK();
    else if (active === 'p3') await exportML();
    toast('✓ Excel сохранён');
  } catch(e) { toast(`Ошибка: ${e.message}`, '#ef4444'); }
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('p1-date').value = new Date().toISOString().split('T')[0];
  updateCalc();
  renderBak();
});
