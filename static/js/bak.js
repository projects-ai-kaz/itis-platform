/* static/js/bak.js — Вкладка 2: БАК-матрица */
"use strict";

let bakState = {
  goals: [
    {id:1, name:'Рост конверсии продаж',       kpi:'Conversion Rate, AOV'},
    {id:2, name:'Снижение оттока клиентов',     kpi:'Churn Rate, NPS'},
    {id:3, name:'Автоматизация поддержки',      kpi:'Ticket Resolution, CSAT'},
    {id:4, name:'Улучшение персонализации',     kpi:'CTR, Engagement Rate'},
  ],
  modules: [
    {id:1, name:'NLP-чат-бот'},
    {id:2, name:'CRM-интеграция'},
    {id:3, name:'Рекомендательная система'},
    {id:4, name:'Предикт оттока'},
  ],
  covered: [],   // [[goal_id, module_id], ...]
  nextGid: 5,
  nextMid: 5,
};

const isCovered = (gid, mid) =>
  bakState.covered.some(([g,m]) => g===gid && m===mid);

function toggleCell(gid, mid) {
  const idx = bakState.covered.findIndex(([g,m]) => g===gid && m===mid);
  if (idx >= 0) bakState.covered.splice(idx, 1);
  else          bakState.covered.push([gid, mid]);
  renderBak();
}

function addGoal() {
  const inp = document.getElementById('goal-inp');
  const v = inp.value.trim(); if (!v) return;
  bakState.goals.push({id: bakState.nextGid++, name: v, kpi: '—'});
  inp.value = ''; renderBak();
}
function addBakMod() {
  const inp = document.getElementById('bmod-inp');
  const v = inp.value.trim(); if (!v) return;
  bakState.modules.push({id: bakState.nextMid++, name: v});
  inp.value = ''; renderBak();
}
function delGoal(id)  { bakState.goals   = bakState.goals.filter(g => g.id!==id); renderBak(); }
function delBakMod(id){ bakState.modules = bakState.modules.filter(m => m.id!==id); renderBak(); }

function calcWeights() {
  const n = bakState.goals.length || 1;
  const scores = bakState.modules.map(m => ({
    ...m,
    score: bakState.goals.filter(g => isCovered(g.id, m.id)).length / n
  }));
  const total = scores.reduce((s,x) => s+x.score, 0) || 1;
  return scores.map(x => ({...x, weight: +(x.score/total).toFixed(4)}));
}

function goalCovPct(gid) {
  const n = bakState.modules.length || 1;
  return bakState.modules.filter(m => isCovered(gid, m.id)).length / n;
}

function renderBak() {
  // Goals list
  document.getElementById('goals-list').innerHTML = bakState.goals.map(g =>
    `<div class="li"><span>${g.name}</span><button class="x" onclick="delGoal(${g.id})">×</button></div>`
  ).join('');

  // Modules list
  document.getElementById('bmod-list').innerHTML = bakState.modules.map(m =>
    `<div class="li"><span>${m.name}</span><button class="x" onclick="delBakMod(${m.id})">×</button></div>`
  ).join('');

  // Matrix
  const tbl = document.getElementById('mx-tbl');
  let html = `<tr><th class="rh"></th>${bakState.modules.map(m=>`<th>${m.name.slice(0,13)}</th>`).join('')}</tr>`;
  bakState.goals.forEach(g => {
    html += `<tr><th class="rh">${g.name.slice(0,18)}</th>`;
    bakState.modules.forEach(m => {
      const on = isCovered(g.id, m.id);
      html += `<td><div class="mx-cell ${on?'on':'off'}" onclick="toggleCell(${g.id},${m.id})">${on?'✓':''}</div></td>`;
    });
    html += '</tr>';
  });
  tbl.innerHTML = html;

  // Weights
  const weights = calcWeights();
  document.getElementById('ws-list').innerHTML = weights.map(w => `
    <div class="ws-row">
      <span class="ws-name">${w.name}</span>
      <div class="ws-bar-w"><div class="ws-bar" style="width:${w.weight*100}%"></div></div>
      <span class="ws-val">${w.weight.toFixed(2)}</span>
      <span style="font-size:11px;color:var(--t3);min-width:46px">${(w.score*100).toFixed(0)}% покр.</span>
    </div>`).join('');

  // KPI table
  document.getElementById('kpi-tbody').innerHTML = bakState.goals.map(g => {
    const pct = (goalCovPct(g.id)*100).toFixed(0);
    const col = pct>=70?'#00e5b4':pct>=40?'#f59e0b':'#ef4444';
    return `<tr>
      <td style="font-weight:500">${g.name}</td>
      <td style="color:var(--t2)">${g.kpi}</td>
      <td><div style="display:flex;align-items:center;gap:7px">
        <div style="flex:1;height:5px;border-radius:3px;background:var(--bg5)">
          <div style="width:${pct}%;height:100%;border-radius:3px;background:${col}"></div></div>
        <span style="font-size:11px;color:${col};font-weight:600;min-width:28px">${pct}%</span></div></td>
      <td style="font-family:var(--f);font-size:12px;font-weight:600;color:var(--a)">${(weights.find(w=>w.id===g.id)||{weight:0}).weight?.toFixed(2)||'—'}</td>
    </tr>`;
  }).join('');
}

function applyWeightsToCalc() {
  applyBakWeights(calcWeights());
  switchPage('p1', document.querySelector('[data-page="p1"]'));
}

async function exportBAK() {
  await downloadFile('/export/bak', {
    goals:   bakState.goals,
    modules: bakState.modules,
    covered: bakState.covered,
  }, 'BAK_Matrix.xlsx');
}
