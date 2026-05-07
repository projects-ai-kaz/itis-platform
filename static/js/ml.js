/* static/js/ml.js — Вкладка 3: ML-предсказатель */
"use strict";

async function runPredict() {
  const get = id => parseFloat(document.getElementById(id).value);
  const payload = {
    digitalization:  get('ml-digit'),
    data_readiness:  get('ml-data'),
    mgmt_support:    get('ml-mgmt'),
    goal_clarity:    get('ml-clarity'),
    budget:          get('ml-budget'),
    company_size:    get('ml-size'),
    industry_coeff:  get('ml-industry'),
  };
  try {
    const res = await apiPost('/api/ml/predict', payload);
    renderMLResult(res);
  } catch(e) {
    toast(`Ошибка: ${e.message}`, '#ef4444');
  }
}

function renderMLResult(res) {
  const classMap = {
    'Высокий эффект': {emoji:'🚀', color:'#00e5b4', bg:'#00e5b415',
      recs:['Масштабируйте решение на новые бизнес-направления.',
            'Зафиксируйте метрики успеха для кейса внедрения.',
            'Рассмотрите интеграцию дополнительных AI-модулей.',
            'Инвестируйте в обучение команды для ROI.']},
    'Средний эффект': {emoji:'📈', color:'#f59e0b', bg:'#f59e0b15',
      recs:['Усильте подготовку и качество данных.',
            'Повысьте вовлечённость руководства.',
            'Уточните бизнес-цели и KPI.',
            'Проведите пилот на одном процессе.']},
    'Низкий эффект':  {emoji:'⚠️', color:'#ef4444', bg:'#ef444415',
      recs:['Пересмотрите готовность данных.',
            'Проведите аудит бизнес-процессов.',
            'Обеспечьте поддержку C-suite.',
            'Начните с простого Quick Win.']},
  };
  const cls = classMap[res.predicted_class] || classMap['Средний эффект'];
  const probs = Object.entries(res.probabilities)
    .sort((a,b) => b[1]-a[1])
    .map(([label,p]) => ({label, p, color: (classMap[label]||{}).color||'#fff'}));

  const icons = ['💡','🎯','⚡','📊'];

  document.getElementById('ml-res').innerHTML = `
    <div class="res-hero">
      <div class="res-cls-box" style="background:${cls.bg};border:1px solid ${cls.color}33">
        <div class="res-emoji">${cls.emoji}</div>
        <div class="res-cls-name" style="color:${cls.color}">${res.predicted_class}</div>
      </div>
      <div class="res-details">
        <div style="font-family:var(--f);font-size:14px;font-weight:700">Прогноз Random Forest</div>
        <div style="font-size:11px;color:var(--t2);margin-bottom:3px">Вероятности классов:</div>
        ${probs.map(({label,p,color}) => `
        <div class="prob-row">
          <span class="prob-lbl">${label}</span>
          <div class="prob-bw"><div class="prob-b" style="width:${p*100}%;background:${color}"></div></div>
          <span class="prob-pct" style="color:${color}">${(p*100).toFixed(1)}%</span>
        </div>`).join('')}
        <div style="font-size:11px;color:var(--t3);margin-top:4px">Score: <span style="color:${cls.color};font-weight:600">${res.raw_score.toFixed(3)}</span></div>
      </div>
    </div>

    <div class="feat-grid">
      <div class="feat-card">
        <div class="feat-ttl">Важность признаков (Feature Importance)</div>
        ${res.feature_importance.map((f,i) => `
        <div class="feat-row">
          <span class="feat-name">${f.feature}</span>
          <div style="display:flex;align-items:center;gap:7px">
            <div style="width:60px;height:4px;border-radius:2px;background:var(--bg5)">
              <div style="width:${f.importance*500}%;max-width:100%;height:100%;border-radius:2px;background:${COLS[i%COLS.length]}"></div></div>
            <span class="feat-val" style="color:${COLS[i%COLS.length]}">${(f.importance*100).toFixed(0)}%</span>
          </div>
        </div>`).join('')}
      </div>
      <div class="feat-card">
        <div class="feat-ttl">Вклад признаков в прогноз</div>
        ${res.feature_contributions.slice(0,7).map((f,i) => `
        <div class="feat-row">
          <span class="feat-name">${f.feature}</span>
          <div style="display:flex;align-items:center;gap:7px">
            <div style="width:60px;height:4px;border-radius:2px;background:var(--bg5)">
              <div style="width:${f.contribution*200}%;max-width:100%;height:100%;border-radius:2px;background:${COLS[i%COLS.length]}"></div></div>
            <span class="feat-val" style="color:${COLS[i%COLS.length]}">${f.contribution.toFixed(3)}</span>
          </div>
        </div>`).join('')}
      </div>
      <div class="reco-card">
        <div class="feat-ttl" style="margin-bottom:.5rem">Рекомендации</div>
        <div class="reco-list">
          ${res.recommendations.map((r,i) =>
            `<div class="reco-item"><span class="reco-icon">${icons[i]||'•'}</span>${r}</div>`
          ).join('')}
        </div>
      </div>
    </div>`;
}

async function exportML() {
  const get = id => parseFloat(document.getElementById(id).value);
  await downloadFile('/export/ml', {
    digitalization: get('ml-digit'),
    data_readiness: get('ml-data'),
    mgmt_support:   get('ml-mgmt'),
    goal_clarity:   get('ml-clarity'),
    budget:         get('ml-budget'),
    company_size:   get('ml-size'),
    industry_coeff: get('ml-industry'),
  }, 'ML_Predict.xlsx');
}
