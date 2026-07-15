# -*- coding: utf-8 -*-
"""
PASO 2 — Generar HTML interactivo
==================================
Lee el archivo resultado_secuencia.json generado por 1_algoritmo.py
y produce secuencia_pilotaje.html con la visualizacion interactiva.

Ejecutar este script cada vez que quieras ajustar la visualizacion
sin necesidad de volver a correr el algoritmo (que demora mucho).
"""

import json
import sys

RESULTADO   = "resultado_secuencia.json"
OUTPUT_HTML = "secuencia_pilotaje.html"


def export_html(rows, params, output_path):
    data_json   = json.dumps(rows)
    params_json = json.dumps(params)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Secuenciacion de Pilotaje</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', sans-serif; background: #F0F4F8; color: #1a1a2e; height: 100vh; display: flex; flex-direction: column; }}

  /* ---- HEADER ---- */
  #header {{ background: #1A5998; color: white; padding: 10px 18px; display: flex; align-items: center; justify-content: space-between; flex-shrink: 0; }}
  #header h1 {{ font-size: 15px; font-weight: 600; }}
  #params {{ font-size: 11px; opacity: .85; text-align: right; line-height: 1.6; }}

  /* ---- TABS ---- */
  #tabs {{ background: #163f70; display: flex; flex-shrink: 0; padding: 0 12px; gap: 2px; }}
  .tab-btn {{ padding: 8px 22px; font-size: 13px; font-weight: 600; color: rgba(255,255,255,0.65);
              border: none; background: transparent; cursor: pointer; border-bottom: 3px solid transparent;
              transition: color .15s, border-color .15s; }}
  .tab-btn:hover {{ color: white; }}
  .tab-btn.active {{ color: white; border-bottom-color: #FFD700; }}

  /* ---- VIEWS ---- */
  .view {{ display: none; flex: 1; overflow: hidden; }}
  .view.active {{ display: flex; }}

  /* ---- MAPA VIEW ---- */
  #view-mapa {{ gap: 6px; padding: 6px; }}

  /* ---- CANVAS PANEL ---- */
  #canvas-wrap {{ flex: 1 1 60%; background: white; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,.15); position: relative; overflow: hidden; }}
  #cvs {{ display: block; cursor: grab; }}
  #cvs.grabbing {{ cursor: grabbing; }}
  #zoom-btns {{ position: absolute; top: 8px; right: 8px; display: flex; flex-direction: column; gap: 4px; }}
  #zoom-btns button {{ width: 30px; height: 30px; border: none; border-radius: 6px; background: #1A5998; color: white; font-size: 18px; cursor: pointer; line-height: 1; }}
  #zoom-btns button:hover {{ background: #2a78c8; }}
  #btn-measure {{ font-size: 13px !important; }}
  #btn-measure.active {{ background: #e67e00 !important; }}
  #measure-result {{ position: absolute; top: 8px; left: 8px; font-size: 12px; font-weight: 600;
    background: rgba(255,255,255,.95); border: 1.5px solid #e67e00; color: #a04800;
    padding: 5px 12px; border-radius: 8px; display: none; }}
  #hint {{ position: absolute; bottom: 8px; left: 50%; transform: translateX(-50%); font-size: 11px; color: #777; background: rgba(255,255,255,.8); padding: 3px 10px; border-radius: 10px; pointer-events: none; }}

  /* ---- TABLE PANEL (secuencia) ---- */
  #table-wrap {{ flex: 0 0 420px; background: white; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,.15); display: flex; flex-direction: column; overflow: hidden; }}
  #table-header {{ padding: 8px 12px; border-bottom: 1px solid #e0e8f0; flex-shrink: 0; }}
  #table-header h2 {{ font-size: 13px; color: #1A5998; margin-bottom: 6px; }}
  #search {{ width: 100%; padding: 5px 9px; border: 1px solid #cdd8e8; border-radius: 6px; font-size: 12px; outline: none; }}
  #search:focus {{ border-color: #1A5998; }}
  #total-row {{ font-size: 12px; font-weight: 600; color: #1A5998; margin-top: 5px; }}
  #tbl-scroll {{ flex: 1; overflow-y: auto; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
  thead th {{ position: sticky; top: 0; background: #1A5998; color: white; padding: 7px 8px; text-align: center; font-weight: 600; font-size: 11px; cursor: pointer; user-select: none; white-space: nowrap; }}
  thead th:hover {{ background: #2a78c8; }}
  tbody tr {{ cursor: pointer; transition: background .12s; }}
  tbody tr:nth-child(even) {{ background: #f0f6ff; }}
  tbody tr:hover {{ background: #cfe2ff; }}
  tbody tr.active {{ background: #ffd966 !important; font-weight: 600; }}
  tbody tr.violation {{ background: #ffe0e0 !important; }}
  tbody tr.violation:hover {{ background: #ffb3b3 !important; }}
  tbody tr.violation.active {{ background: #ffd966 !important; }}
  td {{ padding: 5px 8px; text-align: center; border-bottom: 1px solid #e8eef8; white-space: nowrap; }}
  .badge-ok {{ color: #1a7a3a; font-weight: 600; }}
  .badge-warn {{ color: #cc0000; font-weight: 700; }}

  /* ---- CRONOGRAMA VIEW ---- */
  #view-crono {{ flex-direction: column; padding: 10px 14px; overflow-y: auto; gap: 10px; }}
  #crono-toolbar {{ display: flex; align-items: center; gap: 10px; flex-shrink: 0; }}
  #crono-search {{ padding: 6px 10px; border: 1px solid #cdd8e8; border-radius: 6px; font-size: 12px; outline: none; width: 240px; }}
  #crono-search:focus {{ border-color: #1A5998; }}
  #crono-summary {{ font-size: 12px; color: #555; }}
  #crono-container {{ display: flex; flex-direction: column; gap: 12px; }}

  .day-card {{ background: white; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,.12); overflow: hidden; }}
  .day-header {{ background: #1A5998; color: white; padding: 8px 14px; display: flex; align-items: center; justify-content: space-between; }}
  .day-header .day-title {{ font-size: 13px; font-weight: 700; }}
  .day-header .day-meta {{ font-size: 11px; opacity: .85; }}
  .day-table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
  .day-table thead th {{ background: #e8f0fb; color: #1A5998; padding: 6px 10px; text-align: center; font-weight: 600; font-size: 11px; border-bottom: 2px solid #c5d8f0; white-space: nowrap; }}
  .day-table tbody tr:nth-child(even) {{ background: #f5f9ff; }}
  .day-table tbody tr:hover {{ background: #ddeeff; cursor: pointer; }}
  .day-table tbody tr.crono-active {{ background: #ffd966 !important; font-weight: 600; }}
  .day-table tbody tr.crono-violation {{ background: #ffe0e0 !important; }}
  .day-table td {{ padding: 5px 10px; text-align: center; border-bottom: 1px solid #eef2fa; white-space: nowrap; }}
  .wait-badge {{ display: inline-block; background: #fff3cd; color: #856404; border-radius: 10px; padding: 1px 8px; font-size: 11px; font-weight: 600; }}
  .no-wait {{ color: #aaa; }}
  .day-card.has-violation .day-header {{ background: #b94040; }}
</style>
</head>
<body>

<div id="header">
  <h1>Secuenciacion Optima de Pilotaje</h1>
  <div id="params"></div>
</div>

<div id="tabs">
  <button class="tab-btn active" data-tab="mapa">Mapa y Secuencia</button>
  <button class="tab-btn" data-tab="crono">Cronograma</button>
</div>

<!-- ===== VISTA MAPA ===== -->
<div id="view-mapa" class="view active">
  <div id="canvas-wrap">
    <canvas id="cvs"></canvas>
    <div id="zoom-btns">
      <button id="btn-plus">+</button>
      <button id="btn-minus">&#8722;</button>
      <button id="btn-fit" title="Ajustar vista" style="font-size:12px;">&#8861;</button>
      <button id="btn-measure" title="Medir distancia entre dos puntos">&#128207;</button>
    </div>
    <div id="measure-result"></div>
    <div id="hint">Rueda: zoom &nbsp;&middot;&nbsp; Arrastrar: mover &nbsp;&middot;&nbsp; Clic en punto o fila: seleccionar</div>
  </div>

  <div id="table-wrap">
    <div id="table-header">
      <h2>Secuencia de ejecucion</h2>
      <input id="search" type="text" placeholder="Buscar por orden o ID de pilote...">
      <div id="total-row"></div>
    </div>
    <div id="tbl-scroll">
      <table id="tbl">
        <thead>
          <tr>
            <th data-col="rank">Orden &#8597;</th>
            <th data-col="id">ID Pilote &#8597;</th>
            <th data-col="x">X (m)</th>
            <th data-col="y">Y (m)</th>
            <th data-col="dist">Dist. anterior (m) &#8597;</th>
            <th data-col="wait">Espera (dias) &#8597;</th>
            <th data-col="open_day">Dia apertura &#8597;</th>
            <th data-col="release_day">Dia liberacion &#8597;</th>
            <th data-col="ok">Estado</th>
          </tr>
        </thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>
  </div>
</div>

<!-- ===== VISTA CRONOGRAMA ===== -->
<div id="view-crono" class="view">
  <div id="crono-toolbar">
    <input id="crono-search" type="text" placeholder="Buscar por dia, ID o coordenada...">
    <span id="crono-summary"></span>
  </div>
  <div id="crono-container"></div>
</div>

<script>
const DATA   = {data_json};
const PARAMS = {params_json};

// ---- Header ----
document.getElementById('params').innerHTML =
  `D critica: ${{PARAMS.D}} m &nbsp;|&nbsp; Espera: ${{PARAMS.T}} dia(s) &nbsp;|&nbsp; Ritmo: ${{PARAMS.R}} huecos/dia<br>` +
  `N pilotes: ${{PARAMS.n}} &nbsp;|&nbsp; Solver: ${{PARAMS.solver}}`;
document.getElementById('total-row').textContent =
  `Distancia total de recorrido: ${{PARAMS.total_dist.toFixed(2)}} m`;

// ---- Tabs ----
document.querySelectorAll('.tab-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('view-' + btn.dataset.tab).classList.add('active');
    if (btn.dataset.tab === 'mapa') {{ resize(); }}
    if (btn.dataset.tab === 'crono') {{ renderCrono(); }}
  }});
}});

// ============================================================
// VISTA MAPA
// ============================================================
const wrap = document.getElementById('canvas-wrap');
const cvs  = document.getElementById('cvs');
const ctx  = cvs.getContext('2d');
let scale = 1, offX = 0, offY = 0;
let dragging = false, lastMx = 0, lastMy = 0;
let selectedRank = null;
const PAD = 48;

let measureMode = false;
let measurePts  = [];

function resize() {{
  cvs.width  = wrap.clientWidth;
  cvs.height = wrap.clientHeight;
  fitView();
}}

function dataRange() {{
  const xs = DATA.map(d => d.x), ys = DATA.map(d => d.y);
  return {{ minX: Math.min(...xs), maxX: Math.max(...xs),
            minY: Math.min(...ys), maxY: Math.max(...ys) }};
}}

function fitView() {{
  const r = dataRange();
  const W = cvs.width - PAD*2, H = cvs.height - PAD*2;
  const dx = r.maxX - r.minX || 1, dy = r.maxY - r.minY || 1;
  scale = Math.min(W/dx, H/dy);
  offX  = PAD + (W - dx*scale)/2 - r.minX*scale;
  offY  = PAD + (H - dy*scale)/2 - r.minY*scale;
  draw();
}}

function toScreen(x, y) {{
  return [x*scale + offX, cvs.height - (y*scale + offY)];
}}

function niceStep(raw) {{
  const e = Math.pow(10, Math.floor(Math.log10(raw)));
  return [1,2,5,10].map(m => m*e).find(s => s >= raw) || e*10;
}}

function draw() {{
  ctx.clearRect(0, 0, cvs.width, cvs.height);

  const r = dataRange();
  const step = niceStep((r.maxX - r.minX) / 8);
  ctx.strokeStyle = '#e0e8f0'; ctx.lineWidth = 0.5;
  for (let gx = Math.floor(r.minX/step)*step; gx <= r.maxX+step; gx += step) {{
    const [sx] = toScreen(gx, 0);
    ctx.beginPath(); ctx.moveTo(sx, 0); ctx.lineTo(sx, cvs.height); ctx.stroke();
  }}
  for (let gy = Math.floor(r.minY/step)*step; gy <= r.maxY+step; gy += step) {{
    const [,sy] = toScreen(0, gy);
    ctx.beginPath(); ctx.moveTo(0, sy); ctx.lineTo(cvs.width, sy); ctx.stroke();
  }}

  for (let i = 1; i < DATA.length; i++) {{
    const [x0,y0] = toScreen(DATA[i-1].x, DATA[i-1].y);
    const [x1,y1] = toScreen(DATA[i].x,   DATA[i].y);
    drawArrow(x0, y0, x1, y1, selectedRank !== null && DATA[i].rank === selectedRank);
  }}

  if (selectedRank !== null) {{
    const sel = DATA.find(d => d.rank === selectedRank);
    if (sel) {{
      const [sx, sy] = toScreen(sel.x, sel.y);
      const rPx = PARAMS.D * scale;
      ctx.beginPath();
      ctx.arc(sx, sy, rPx, 0, Math.PI*2);
      ctx.fillStyle   = 'rgba(255, 107, 53, 0.10)';
      ctx.strokeStyle = 'rgba(255, 107, 53, 0.70)';
      ctx.lineWidth   = 1.5;
      ctx.setLineDash([5, 4]);
      ctx.fill(); ctx.stroke();
      ctx.setLineDash([]);
      ctx.font = '10px Segoe UI';
      ctx.fillStyle = '#FF6B35';
      ctx.textAlign = 'left';
      ctx.fillText(`D = ${{PARAMS.D}} m`, sx + rPx + 4, sy);
    }}
  }}

  drawMeasure();

  DATA.forEach(d => {{
    const [sx, sy] = toScreen(d.x, d.y);
    const sel = d.rank === selectedRank;
    ctx.beginPath();
    ctx.arc(sx, sy, sel ? 7 : 4, 0, Math.PI*2);
    ctx.fillStyle   = sel ? '#FF6B35' : '#1A5998';
    ctx.strokeStyle = 'white';
    ctx.lineWidth   = sel ? 2 : 1.2;
    ctx.fill(); ctx.stroke();

    if (scale > 6 || sel) {{
      ctx.font      = sel ? 'bold 11px Segoe UI' : '9px Segoe UI';
      ctx.fillStyle = '#1a1a2e';
      ctx.textAlign = 'center';
      ctx.lineWidth = 2.5;
      ctx.strokeStyle = 'white';
      ctx.strokeText(d.id, sx, sy - 9);
      ctx.fillText(d.id, sx, sy - 9);
    }}
  }});
}}

function drawMeasure() {{
  if (measurePts.length === 0) return;
  const [sx0, sy0] = toScreen(measurePts[0].x, measurePts[0].y);
  ctx.beginPath();
  ctx.arc(sx0, sy0, 7, 0, Math.PI*2);
  ctx.fillStyle = '#e67e00'; ctx.strokeStyle = 'white'; ctx.lineWidth = 2;
  ctx.fill(); ctx.stroke();

  if (measurePts.length === 2) {{
    const [sx1, sy1] = toScreen(measurePts[1].x, measurePts[1].y);
    const dx = measurePts[1].x - measurePts[0].x;
    const dy = measurePts[1].y - measurePts[0].y;
    const dist = Math.sqrt(dx*dx + dy*dy);
    ctx.beginPath();
    ctx.moveTo(sx0, sy0); ctx.lineTo(sx1, sy1);
    ctx.strokeStyle = '#e67e00'; ctx.lineWidth = 1.8;
    ctx.setLineDash([6, 4]); ctx.stroke(); ctx.setLineDash([]);
    ctx.beginPath();
    ctx.arc(sx1, sy1, 7, 0, Math.PI*2);
    ctx.fillStyle = '#e67e00'; ctx.strokeStyle = 'white'; ctx.lineWidth = 2;
    ctx.fill(); ctx.stroke();
    const mx = (sx0 + sx1) / 2, my = (sy0 + sy1) / 2;
    const label = dist.toFixed(2) + ' m';
    ctx.font = 'bold 12px Segoe UI';
    ctx.lineWidth = 3; ctx.strokeStyle = 'white';
    ctx.strokeText(label, mx + 6, my - 6);
    ctx.fillStyle = '#a04800';
    ctx.fillText(label, mx + 6, my - 6);
    const panel = document.getElementById('measure-result');
    panel.style.display = 'block';
    panel.innerHTML =
      `&#128207; ${{measurePts[0].id}} &rarr; ${{measurePts[1].id}}: <b>${{dist.toFixed(2)}} m</b>` +
      `&nbsp;&nbsp;<span style="font-weight:400;color:#888;">(clic en &#128207; para limpiar)</span>`;
  }}
}}

function drawArrow(x0, y0, x1, y1, highlight) {{
  const dx = x1-x0, dy = y1-y0, len = Math.sqrt(dx*dx+dy*dy);
  if (len < 1) return;
  const r = 5, ux = dx/len, uy = dy/len;
  ctx.beginPath();
  ctx.moveTo(x0, y0);
  ctx.lineTo(x1 - ux*5, y1 - uy*5);
  ctx.strokeStyle = highlight ? '#FF6B35' : '#3A7DC9';
  ctx.lineWidth   = highlight ? 2.2 : 1.1;
  ctx.globalAlpha = highlight ? 1 : 0.55;
  ctx.stroke();
  ctx.globalAlpha = 1;
  const angle = Math.atan2(uy, ux);
  ctx.beginPath();
  ctx.moveTo(x1 - ux*5, y1 - uy*5);
  ctx.lineTo(x1 - ux*5 - r*Math.cos(angle-0.4), y1 - uy*5 - r*Math.sin(angle-0.4));
  ctx.lineTo(x1 - ux*5 - r*Math.cos(angle+0.4), y1 - uy*5 - r*Math.sin(angle+0.4));
  ctx.closePath();
  ctx.fillStyle = highlight ? '#FF6B35' : '#3A7DC9';
  ctx.globalAlpha = highlight ? 1 : 0.65;
  ctx.fill();
  ctx.globalAlpha = 1;
}}

cvs.addEventListener('wheel', e => {{
  e.preventDefault();
  const rect = cvs.getBoundingClientRect();
  const mx = e.clientX - rect.left, my = e.clientY - rect.top;
  const factor = e.deltaY < 0 ? 1.15 : 1/1.15;
  offX = mx - (mx - offX)*factor;
  offY = (cvs.height - my) - ((cvs.height - my) - offY)*factor;
  scale *= factor;
  draw();
}}, {{passive: false}});

cvs.addEventListener('mousedown', e => {{
  const rect = cvs.getBoundingClientRect();
  const mx = e.clientX - rect.left, my = e.clientY - rect.top;
  let hit = null, minD = 12;
  DATA.forEach(d => {{
    const [sx,sy] = toScreen(d.x, d.y);
    const dist = Math.sqrt((sx-mx)**2 + (sy-my)**2);
    if (dist < minD) {{ minD = dist; hit = d; }}
  }});

  if (measureMode) {{
    if (hit) {{
      if (measurePts.length < 2) measurePts.push(hit);
      else measurePts = [hit];
      draw();
    }}
    return;
  }}

  if (hit) {{ selectRank(hit.rank); }}
  else {{ dragging = true; lastMx = e.clientX; lastMy = e.clientY; cvs.classList.add('grabbing'); }}
}});

window.addEventListener('mousemove', e => {{
  if (!dragging) return;
  offX += e.clientX - lastMx;
  offY -= e.clientY - lastMy;
  lastMx = e.clientX; lastMy = e.clientY;
  draw();
}});
window.addEventListener('mouseup', () => {{ dragging = false; cvs.classList.remove('grabbing'); }});

document.getElementById('btn-plus').onclick  = () => {{ scale *= 1.3; draw(); }};
document.getElementById('btn-minus').onclick = () => {{ scale /= 1.3; draw(); }};
document.getElementById('btn-fit').onclick   = fitView;

document.getElementById('btn-measure').onclick = () => {{
  measureMode = !measureMode;
  measurePts  = [];
  document.getElementById('measure-result').style.display = 'none';
  document.getElementById('btn-measure').classList.toggle('active', measureMode);
  document.getElementById('hint').textContent = measureMode
    ? 'Modo medicion: clic en el primer pilote, luego en el segundo'
    : 'Rueda: zoom · Arrastrar: mover · Clic en punto o fila: seleccionar';
  cvs.style.cursor = measureMode ? 'crosshair' : 'grab';
  draw();
}};

// ---- Tabla secuencia ----
let sortCol = 'rank', sortAsc = true, filterText = '';

function renderTable() {{
  let rows = DATA.filter(d =>
    String(d.rank).includes(filterText) ||
    d.id.toLowerCase().includes(filterText.toLowerCase())
  );
  rows.sort((a, b) => {{
    let va = a[sortCol] ?? -Infinity, vb = b[sortCol] ?? -Infinity;
    if (typeof va === 'string') va = va.toLowerCase();
    if (typeof vb === 'string') vb = vb.toLowerCase();
    return sortAsc ? (va > vb ? 1 : va < vb ? -1 : 0) : (va < vb ? 1 : va > vb ? -1 : 0);
  }});

  const tbody = document.getElementById('tbody');
  tbody.innerHTML = '';
  rows.forEach(d => {{
    const tr = document.createElement('tr');
    if (d.rank === selectedRank) tr.classList.add('active');
    if (!d.ok) tr.classList.add('violation');
    const estadoBadge = d.wait === null ? '&mdash;'
      : d.ok ? '<span class="badge-ok">OK</span>'
               : '<span class="badge-warn">VIOLACION</span>';
    tr.innerHTML =
      `<td>${{d.rank}}</td>` +
      `<td>${{d.id}}</td>` +
      `<td>${{d.x.toFixed(2)}}</td>` +
      `<td>${{d.y.toFixed(2)}}</td>` +
      `<td>${{d.dist !== null ? d.dist.toFixed(2) : '&mdash;'}}</td>` +
      `<td>${{d.wait !== null ? d.wait.toFixed(2) : '&mdash;'}}</td>` +
      `<td>${{d.open_day}}</td>` +
      `<td>${{d.release_day}}</td>` +
      `<td>${{estadoBadge}}</td>`;
    tr.addEventListener('click', () => selectRank(d.rank));
    tbody.appendChild(tr);
  }});
}}

function selectRank(rank) {{
  selectedRank = (selectedRank === rank) ? null : rank;
  draw();
  renderTable();
  if (selectedRank !== null) {{
    const active = document.querySelector('#tbody tr.active');
    if (active) active.scrollIntoView({{ block: 'nearest' }});
  }}
}}

document.getElementById('search').addEventListener('input', e => {{
  filterText = e.target.value;
  renderTable();
}});

document.querySelectorAll('thead th[data-col]').forEach(th => {{
  th.addEventListener('click', () => {{
    const col = th.dataset.col;
    if (sortCol === col) sortAsc = !sortAsc;
    else {{ sortCol = col; sortAsc = true; }}
    renderTable();
  }});
}});

// ============================================================
// VISTA CRONOGRAMA
// ============================================================
function buildDays() {{
  // Agrupar pilotes por dia calendario (ceil de open_day)
  const dayMap = new Map();
  DATA.forEach(d => {{
    const dayNum = Math.ceil(d.open_day);
    if (!dayMap.has(dayNum)) dayMap.set(dayNum, []);
    dayMap.get(dayNum).push(d);
  }});
  // Ordenar dias y dentro de cada dia por open_day
  const days = [];
  [...dayMap.keys()].sort((a,b) => a-b).forEach(dayNum => {{
    const piles = dayMap.get(dayNum).sort((a,b) => a.open_day - b.open_day);
    const hasViolation = piles.some(p => !p.ok);
    days.push({{ dayNum, piles, hasViolation }});
  }});
  return days;
}}

let cronoFilter = '';

function renderCrono() {{
  const days = buildDays();
  const container = document.getElementById('crono-container');
  container.innerHTML = '';

  const q = cronoFilter.toLowerCase();
  let totalDays = 0, totalPiles = 0;

  days.forEach(day => {{
    const pilesFiltered = q === '' ? day.piles : day.piles.filter(p =>
      String(day.dayNum).includes(q) ||
      p.id.toLowerCase().includes(q) ||
      String(p.x.toFixed(2)).includes(q) ||
      String(p.y.toFixed(2)).includes(q)
    );
    if (pilesFiltered.length === 0) return;
    totalDays++;
    totalPiles += pilesFiltered.length;

    const card = document.createElement('div');
    card.className = 'day-card' + (day.hasViolation ? ' has-violation' : '');

    const distTotal = pilesFiltered.reduce((s, p) => s + (p.dist || 0), 0);
    const waitTotal = pilesFiltered.reduce((s, p) => s + (p.wait || 0), 0);

    card.innerHTML = `
      <div class="day-header">
        <span class="day-title">Dia ${{day.dayNum}}</span>
        <span class="day-meta">
          ${{pilesFiltered.length}} hueco(s) &nbsp;|&nbsp;
          Dist. acum. del dia: ${{distTotal.toFixed(2)}} m
          ${{waitTotal > 0 ? ' &nbsp;|&nbsp; Espera acum.: ' + waitTotal.toFixed(2) + ' dia(s)' : ''}}
          ${{day.hasViolation ? ' &nbsp;|&nbsp; &#9888; VIOLACION' : ''}}
        </span>
      </div>
      <table class="day-table">
        <thead>
          <tr>
            <th>Orden</th>
            <th>ID Pilote</th>
            <th>X (m)</th>
            <th>Y (m)</th>
            <th>Dist. al anterior (m)</th>
            <th>Espera (dias)</th>
            <th>Hora apertura (dia)</th>
            <th>Liberacion (dia)</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          ${{pilesFiltered.map(p => {{
            const estadoBadge = p.wait === null ? '&mdash;'
              : p.ok ? '<span class="badge-ok">OK</span>'
                      : '<span class="badge-warn">VIOLACION</span>';
            const waitCell = p.wait !== null && p.wait > 0
              ? `<span class="wait-badge">+${{p.wait.toFixed(2)}} d</span>`
              : (p.wait === null ? '&mdash;' : '<span class="no-wait">0</span>');
            return `<tr class="${{!p.ok ? 'crono-violation' : ''}}" data-rank="${{p.rank}}">
              <td>${{p.rank}}</td>
              <td><b>${{p.id}}</b></td>
              <td>${{p.x.toFixed(2)}}</td>
              <td>${{p.y.toFixed(2)}}</td>
              <td>${{p.dist !== null ? p.dist.toFixed(2) : '&mdash;'}}</td>
              <td>${{waitCell}}</td>
              <td>${{p.open_day}}</td>
              <td>${{p.release_day}}</td>
              <td>${{estadoBadge}}</td>
            </tr>`;
          }}).join('')}}
        </tbody>
      </table>`;

    // Clic en fila del cronograma -> ir al mapa
    card.querySelectorAll('tr[data-rank]').forEach(tr => {{
      tr.addEventListener('click', () => {{
        const rank = parseInt(tr.dataset.rank);
        selectRank(rank);
        // Cambiar a vista mapa
        document.querySelector('.tab-btn[data-tab="mapa"]').click();
        setTimeout(() => {{
          const active = document.querySelector('#tbody tr.active');
          if (active) active.scrollIntoView({{ block: 'nearest' }});
        }}, 80);
      }});
    }});

    container.appendChild(card);
  }});

  const totalDias = buildDays().length;
  document.getElementById('crono-summary').textContent =
    `${{totalDias}} dias totales &nbsp;|&nbsp; ${{DATA.length}} pilotes &nbsp;|&nbsp; Ritmo: ${{PARAMS.R}} huecos/dia`;
}}

document.getElementById('crono-search').addEventListener('input', e => {{
  cronoFilter = e.target.value;
  renderCrono();
}});

// ---- Init ----
new ResizeObserver(resize).observe(wrap);
resize();
renderTable();
</script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML generado: {output_path}")


# ---------------------------------------------------------------------------
# EJECUCION PRINCIPAL
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 62)
    print("  PASO 2 — Generando HTML interactivo")
    print("=" * 62)

    try:
        with open(RESULTADO, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: No se encontro '{RESULTADO}'.")
        print("Primero ejecuta 1_algoritmo.py para generar el resultado.")
        sys.exit(1)

    rows   = data["rows"]
    params = data["params"]

    print(f"  Pilotes en resultado: {params['n']}")
    print(f"  Distancia total     : {params['total_dist']} m")
    print(f"  Solver              : {params['solver']}")
    print()

    export_html(rows, params, OUTPUT_HTML)
    print("Listo. Abre secuencia_pilotaje.html en el navegador.")
    input("\nPresiona Enter para cerrar...")
