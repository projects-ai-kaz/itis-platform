/* static/js/itis.js — Вкладка 1: ITIS-калькулятор */
"use strict";

let mods = [
  {name: 'NLP-модуль ответа', E:.95, W:.30, C:.90, M:.85},
  {name: 'CRM-интеграция',     E:.88, W:.25, C:.85, M:.90},
  {name: 'Омниканал',          E:.90, W:.20, C:.80, M:.88},
  {name: 'Аналитика данных',   E:.78, W:.25, C:.75, M:.80},
];
let itisCharts = {bar: null, radar: null, dnt: null};

const itisi = m => Math.cbrt(m.E * m.C * m.M);
const totalITIS = () => {
  const ws = mods.reduce((s,m) => s + m.W, 0);
  return ws ? mods.reduce((s,m) => s + (m.W/ws)*itisi(m), 0) : 0;
};
const clsOf = v =>
  v < 0.45 ? {l:'Низкая эффективность', c:'#ef4444', b:'#ef444420',
               d:'Внедрение не достигает бизнес-целей. Пересмотрите стратегию.'}
: v < 0.70 ? {l:'Средняя эффективность', c:'#f59e0b', b:'#f59e0b20',
               d:'Частичное достижение целей. Необходима доработка слабых модулей.'}
             : {l:'Высокая эффективность', c:'#00e5b4', b:'#00e5b420',
               d:'Высокий бизнес-эффект. Рекомендуется масштабирование.'};

function renderMods() {
  const c = document.getElementById('mods-container'); c.innerHTML = '';
  const PC = {E:'#00e5b4', W:'#3b82f6', C:'#f59e0b', M:'#d946ef'};
  const RC = ['ca','cb','cc','cd'];
  mods.forEach((m, i) => {
    const col = COLS[i % COLS.length];
    const d = document.createElement('div'); d.className = 'mod-card';
    d.innerHTML = `
      <div class="mod-hdr">
        <span class="mod-dot" style="background:${col}"></span>
        <input class="mod-nm" value="${m.name}"
          oninput="mods[${i}].name=this.value;refreshCharts()"/>
        <button class="del-btn" onclick="delMod(${i})">×</button>
      </div>
      ${['E','C','M','W'].map((p,pi) => `
        <div class="prow">
          <span class="ptag" style="color:${PC[p]}">${p}</span>
          <input type="range" class="${RC[pi]}" min="0" max="1" step="0.01" value="${m[p].toFixed(2)}"
            oninput="mods[${i}]['${p}']=+this.value;
                     this.nextElementSibling.textContent=parseFloat(this.value).toFixed(2);
                     updateCalc()"/>
          <span class="pnum">${m[p].toFixed(2)}</span>
        </div>`).join('')}
      <div class="itis-row">
        <span class="itis-lbl">ITISᵢ</span>
        <span class="itis-val" style="color:${col}">${itisi(m).toFixed(3)}</span>
      </div>`;
    c.appendChild(d);
  });
}

function updateCalc() {
  const score = totalITIS(), cls = clsOf(score);
  const ws = mods.reduce((s,m) => s + m.W, 0);
  const ok = Math.abs(ws - 1) < 0.01;

  const arc = document.getElementById('g-arc');
  arc.style.strokeDasharray = `${Math.min(score,1)*226} 290`;
  arc.style.stroke = cls.c;
  const gn = document.getElementById('g-num');
  gn.textContent = score.toFixed(3); gn.style.color = cls.c;

  const b = document.getElementById('cls-badge');
  b.style.background = cls.b; b.style.color = cls.c;
  document.getElementById('cls-dot').style.background = cls.c;
  document.getElementById('cls-lbl').textContent = cls.l;
  document.getElementById('cls-desc').textContent = cls.d;

  document.getElementById('s-mods').textContent = mods.length;
  const vals = mods.map(itisi);
  const best = Math.max(...vals), worst = Math.min(...vals);
  const sb = document.getElementById('s-best'); sb.textContent = best.toFixed(3); sb.style.color = cls.c;
  const sw = document.getElementById('s-worst'); sw.textContent = worst.toFixed(3);
  sw.style.color = worst<.45?'#ef4444':worst<.70?'#f59e0b':'#00e5b4';

  const ws_el = document.getElementById('w-status');
  ws_el.className = ok ? 'wstat w-ok' : 'wstat w-warn';
  document.getElementById('w-txt').textContent = ok
    ? `✓ ΣW = ${ws.toFixed(2)} — корректно`
    : `⚠ ΣW = ${ws.toFixed(2)} ≠ 1.00 (нормализован)`;

  renderMods(); refreshCharts();
}

function refreshCharts() {
  const names = mods.map(m => m.name.length>15 ? m.name.slice(0,14)+'…' : m.name);
  const ivals = mods.map(m => +itisi(m).toFixed(3));
  const ws = mods.reduce((s,m) => s+m.W, 0) || 1;
  const ctr = mods.map(m => +((m.W/ws)*itisi(m)).toFixed(4));
  const score = totalITIS();

  const leg = id => {
    document.getElementById(id).innerHTML = mods.map((m,i) =>
      `<span class="lg"><span class="lg-d" style="background:${COLS[i%COLS.length]}"></span>${m.name.slice(0,16)}</span>`
    ).join('');
  };

  // BAR
  if (itisCharts.bar) { itisCharts.bar.destroy(); itisCharts.bar = null; }
  leg('bar-leg');
  document.getElementById('bar-wrap').style.height = Math.max(140, mods.length*50+40)+'px';
  itisCharts.bar = new Chart(document.getElementById('bar-c'), {
    type:'bar', data:{labels:names,datasets:[{
      data:ivals,backgroundColor:mods.map((_,i)=>COLS[i%COLS.length]+'bb'),
      borderColor:mods.map((_,i)=>COLS[i%COLS.length]),borderWidth:1.5,borderRadius:5,borderSkipped:false
    }]}, options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>`ITISᵢ: ${c.parsed.x.toFixed(3)}`}}},
      scales:{x:{min:0,max:1,grid:{color:'rgba(0,0,0,.05)'},ticks:{color:'#9ca3af',callback:v=>v.toFixed(1)}},
              y:{grid:{display:false},ticks:{color:'#6b7280',font:{size:11}}}}}
  });

  // RADAR
  if (itisCharts.radar) { itisCharts.radar.destroy(); itisCharts.radar = null; }
  itisCharts.radar = new Chart(document.getElementById('radar-c'), {
    type:'radar', data:{labels:names,datasets:[
      {label:'E',data:mods.map(m=>m.E),borderColor:'#00e5b4',backgroundColor:'#00e5b418',borderWidth:1.5,pointRadius:2,pointBackgroundColor:'#00e5b4'},
      {label:'C',data:mods.map(m=>m.C),borderColor:'#f59e0b',backgroundColor:'#f59e0b18',borderWidth:1.5,pointRadius:2,pointBackgroundColor:'#f59e0b'},
      {label:'M',data:mods.map(m=>m.M),borderColor:'#d946ef',backgroundColor:'#d946ef18',borderWidth:1.5,pointRadius:2,pointBackgroundColor:'#d946ef'},
      {label:'W',data:mods.map(m=>m.W),borderColor:'#3b82f6',backgroundColor:'#3b82f618',borderWidth:1.5,pointRadius:2,pointBackgroundColor:'#3b82f6'},
    ]}, options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},
      scales:{r:{min:0,max:1,backgroundColor:'transparent',grid:{color:'rgba(0,0,0,.06)'},
              angleLines:{color:'rgba(0,0,0,.06)'},pointLabels:{color:'#6b7280',font:{size:10}},ticks:{display:false}}}}
  });

  // DONUT
  if (itisCharts.dnt) { itisCharts.dnt.destroy(); itisCharts.dnt = null; }
  leg('dnt-leg');
  itisCharts.dnt = new Chart(document.getElementById('dnt-c'), {
    type:'doughnut', data:{labels:names,datasets:[{
      data:ctr,backgroundColor:mods.map((_,i)=>COLS[i%COLS.length]+'cc'),
      borderColor:mods.map((_,i)=>COLS[i%COLS.length]),borderWidth:1.5,hoverOffset:5
    }]}, options:{responsive:true,maintainAspectRatio:false,cutout:'66%',
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>`Вклад: ${score>0?(c.parsed/score*100).toFixed(1)+'%':'—'}`}}}}
  });

  document.getElementById('dnt-det').innerHTML = mods.map((m,i) => {
    const pct = score > 0 ? (ctr[i]/score*100).toFixed(1) : '0.0';
    return `<div style="display:flex;align-items:center;gap:8px">
      <div style="width:3px;height:26px;border-radius:3px;background:${COLS[i%COLS.length]};flex-shrink:0"></div>
      <div><div style="font-size:12px;font-weight:500">${m.name}</div>
      <div style="font-size:11px;color:var(--t3)">Вклад: <span style="color:${COLS[i%COLS.length]};font-weight:600">${pct}%</span> · W=${m.W.toFixed(2)} · ITISᵢ=${itisi(m).toFixed(3)}</div></div></div>`;
  }).join('');
}

function addMod() {
  mods.push({name:`Модуль ${mods.length+1}`, E:.80, W:+(1/(mods.length+1)).toFixed(2), C:.75, M:.75});
  updateCalc();
}
function delMod(i) {
  if (mods.length <= 1) { toast('Нужен хотя бы один модуль', '#ef4444'); return; }
  mods.splice(i, 1); updateCalc();
}

// Called from BAK tab to apply suggested weights
function applyBakWeights(weights) {
  weights.forEach((w, i) => { if (mods[i]) mods[i].W = +w.weight.toFixed(2); });
  updateCalc();
  toast('✓ Веса из БАК-матрицы применены');
}

async function exportITIS() {
  await downloadFile('/export/itis', {
    project: {
      company:   document.getElementById('p1-company').value,
      solution:  document.getElementById('p1-solution').value,
      analyst:   document.getElementById('p1-analyst').value,
      eval_date: document.getElementById('p1-date').value,
    },
    modules: mods
  }, `ITIS_${document.getElementById('p1-company').value.replace(/\s+/g,'_')}.xlsx`);
}
