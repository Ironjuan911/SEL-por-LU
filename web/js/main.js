/**
 * main.js  –  Lógica del frontend para la app SEL por LU
 * Comunicación con Python via QWebChannel / Bridge.
 * Renderizado LaTeX con KaTeX.
 */

// ── Estado global ────────────────────────────────────────────────────────────
let currentN = 4;
let bridge = null;          // Objeto Bridge de QWebChannel
let solving = false;
const entryCells = {};      // { "i,j" | "i,b" : HTMLInputElement }

// ── Datos del ejemplo 4×4 ────────────────────────────────────────────────────
const EXAMPLE_A = [[2, -1, 0, 3], [4, 1, -1, 2], [-2, 3, 2, 0], [0, 2, -1, 1]];
const EXAMPLE_B = [7, 9, 3, 2];

// ── Inicialización ────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  buildSizeButtons();
  generateGrid(currentN);

  // Conectar con el backend Python via QWebChannel
  // qt.webChannelTransport es inyectado automáticamente por Qt
  if (typeof QWebChannel !== 'undefined' && typeof qt !== 'undefined') {
    new QWebChannel(qt.webChannelTransport, (channel) => {
      bridge = channel.objects.bridge;
      console.log('[Bridge] Conexión con Python establecida.');
    });
  } else {
    console.warn('[Bridge] QWebChannel no disponible. ¿Corriendo fuera de Qt?');
  }
});

// ── Botones de tamaño ─────────────────────────────────────────────────────────
function buildSizeButtons() {
  const container = document.getElementById('size-buttons');
  container.innerHTML = '';
  for (let n = 2; n <= 8; n++) {
    const btn = document.createElement('button');
    btn.className = 'size-btn' + (n === currentN ? ' active' : '');
    btn.textContent = `${n}×${n}`;
    btn.id = `size-btn-${n}`;
    btn.addEventListener('click', () => selectSize(n));
    container.appendChild(btn);
  }
}

function selectSize(n) {
  currentN = n;
  document.querySelectorAll('.size-btn').forEach(b => b.classList.remove('active'));
  const btn = document.getElementById(`size-btn-${n}`);
  if (btn) btn.classList.add('active');
  generateGrid(n);
  resetResults();
}

// ── Generador de grilla ───────────────────────────────────────────────────────
function generateGrid(n) {
  const container = document.getElementById('matrix-grid');
  container.innerHTML = '';
  Object.keys(entryCells).forEach(k => delete entryCells[k]);

  // n columnas A + 1 separador (9px) + 1 columna b
  container.style.gridTemplateColumns = `repeat(${n}, 56px) 9px 56px`;

  // ── Fila 0: etiquetas de columna ──
  for (let j = 0; j < n; j++) {
    const lbl = document.createElement('div');
    lbl.className = 'matrix-col-label';
    lbl.textContent = `x${j + 1}`;
    container.appendChild(lbl);
  }
  container.appendChild(document.createElement('div')); // hueco separador
  const bLbl = document.createElement('div');
  bLbl.className = 'matrix-col-label b-label';
  bLbl.textContent = 'b';
  container.appendChild(bLbl);

  // ── Filas de datos ──
  for (let i = 0; i < n; i++) {
    // Celdas de la matriz A
    for (let j = 0; j < n; j++) {
      const inp = document.createElement('input');
      inp.type = 'text';
      inp.className = 'matrix-input';
      inp.id = `cell-${i}-${j}`;
      inp.autocomplete = 'off';
      inp.inputMode = 'decimal';
      inp.addEventListener('keydown', (e) => handleKey(e, i, j, n));
      container.appendChild(inp);
      entryCells[`${i},${j}`] = inp;
    }

    // Separador visual
    const sep = document.createElement('div');
    sep.className = 'matrix-sep';
    container.appendChild(sep);

    // Celda del vector b
    const bInp = document.createElement('input');
    bInp.type = 'text';
    bInp.className = 'matrix-input b-input';
    bInp.id = `cell-${i}-b`;
    bInp.autocomplete = 'off';
    bInp.inputMode = 'decimal';
    bInp.addEventListener('keydown', (e) => handleKey(e, i, 'b', n));
    container.appendChild(bInp);
    entryCells[`${i},b`] = bInp;
  }
}

// ── Navegación por teclado ────────────────────────────────────────────────────
function handleKey(e, i, j, n) {
  if (e.key === 'ArrowRight') { e.preventDefault(); moveRight(i, j, n); }
  if (e.key === 'ArrowLeft')  { e.preventDefault(); moveLeft(i, j, n); }
  if (e.key === 'ArrowDown')  { e.preventDefault(); focusCell(i + 1, j, n); }
  if (e.key === 'ArrowUp')    { e.preventDefault(); focusCell(i - 1, j, n); }
  if (e.key === 'Enter')      { e.preventDefault(); moveRight(i, j, n, true); }
  if (e.key === 'Tab')        { e.preventDefault(); moveRight(i, j, n); }
}

function moveRight(i, j, n, fromEnter = false) {
  if (j === 'b') {
    if (i < n - 1) focusCell(i + 1, 0, n);
    else if (fromEnter) onSolve();
  } else if (j < n - 1) {
    focusCell(i, j + 1, n);
  } else {
    focusCell(i, 'b', n);
  }
}

function moveLeft(i, j, n) {
  if (j === 'b') focusCell(i, n - 1, n);
  else if (j > 0) focusCell(i, j - 1, n);
}

function focusCell(i, j, n) {
  if (i < 0 || i >= n) return;
  const key = (j === 'b') ? `${i},b` : `${i},${j}`;
  const inp = entryCells[key];
  if (inp) { inp.focus(); inp.select(); }
}

// ── Lectura de la matriz ──────────────────────────────────────────────────────
function readMatrix() {
  const A = [], b = [];
  for (let i = 0; i < currentN; i++) {
    const row = [];
    for (let j = 0; j < currentN; j++) {
      const v = parseFloat(entryCells[`${i},${j}`].value.trim());
      if (isNaN(v)) return null;
      row.push(v);
    }
    const bv = parseFloat(entryCells[`${i},b`].value.trim());
    if (isNaN(bv)) return null;
    A.push(row);
    b.push(bv);
  }
  return { A, b };
}

// ── Acciones de botones ───────────────────────────────────────────────────────
function onClear() {
  Object.values(entryCells).forEach(inp => (inp.value = ''));
  resetResults();
  document.getElementById('input-error').textContent = '';
}

function onExample() {
  if (currentN !== 4) selectSize(4);
  setTimeout(() => {
    for (let i = 0; i < 4; i++) {
      for (let j = 0; j < 4; j++) entryCells[`${i},${j}`].value = EXAMPLE_A[i][j];
      entryCells[`${i},b`].value = EXAMPLE_B[i];
    }
  }, 50);
}

function onSolve() {
  if (solving) return;
  document.getElementById('input-error').textContent = '';

  const data = readMatrix();
  if (!data) {
    document.getElementById('input-error').textContent =
      '⚠ Completa todas las celdas con valores numéricos.';
    return;
  }

  if (!bridge) {
    document.getElementById('input-error').textContent =
      '⚠ Conexión con el backend no establecida. Espera un momento.';
    return;
  }

  solving = true;
  const btn = document.getElementById('btn-solve');
  btn.disabled = true;
  btn.textContent = 'Calculando…';
  showLoader();

  // Llamada al Bridge de QWebChannel (Python)
  const payload = JSON.stringify({ A: data.A, b: data.b });
  bridge.solve(payload, (resultJson) => {
    solving = false;
    btn.disabled = false;
    btn.textContent = 'Resolver →';
    try {
      const result = JSON.parse(resultJson);
      renderResults(result);
    } catch (e) {
      renderResults({ error: 'Error al parsear la respuesta del backend.' });
    }
  });
}

// ── Resultados ────────────────────────────────────────────────────────────────
function showLoader() {
  document.getElementById('placeholder').style.display = 'none';
  const r = document.getElementById('results-content');
  r.style.display = 'block';
  r.innerHTML = `
    <div class="loader-wrap">
      <div class="spinner"></div>
      <span>Calculando…</span>
    </div>`;
}

function resetResults() {
  document.getElementById('placeholder').style.display = '';
  const r = document.getElementById('results-content');
  r.style.display = 'none';
  r.innerHTML = '';
}

function renderResults(result) {
  document.getElementById('placeholder').style.display = 'none';
  const r = document.getElementById('results-content');
  r.style.display = 'block';
  r.innerHTML = '';

  if (result.error) {
    r.innerHTML = `
      <div class="step-card type-error">
        <div class="step-card-title">Error</div>
        <div class="step-card-latex">${escapeHtml(result.error)}</div>
      </div>`;
    return;
  }

  // Banner de solución
  if (result.x_latex) {
    const banner = document.createElement('div');
    banner.className = 'solution-banner';
    const latexEl = document.createElement('div');
    latexEl.className = 'solution-banner-latex';
    banner.innerHTML = `<div class="solution-banner-title">✓ SOLUCIÓN ENCONTRADA</div>`;
    banner.appendChild(latexEl);
    r.appendChild(banner);
    renderKaTeX(latexEl, `x = ${result.x_latex}`);
  }

  // Tarjetas de pasos
  (result.steps || []).forEach((step, idx) => {
    const card = document.createElement('div');
    const type = step.type || 'system';
    card.className = `step-card type-${type}`;

    // Título limpio (sin LaTeX matemático)
    const rawTitle = (step.title || '').replace(/\$[^$]*\$/g, '');
    card.innerHTML = `
      <div class="step-card-title">${escapeHtml(rawTitle)}</div>
      <div class="step-card-latex" id="step-latex-${idx}"></div>`;
    r.appendChild(card);

    if (step.latex) {
      renderKaTeX(card.querySelector(`#step-latex-${idx}`), step.latex);
    }
  });
}

// ── KaTeX helper ──────────────────────────────────────────────────────────────
function renderKaTeX(el, latexStr) {
  if (!el || !latexStr) return;
  try {
    katex.render(latexStr, el, {
      displayMode: true,
      throwOnError: false,
      output: 'html',
    });
  } catch (e) {
    el.textContent = latexStr;
  }
}

// ── Modal ─────────────────────────────────────────────────────────────────────
function toggleManual() {
  document.getElementById('manual-overlay').classList.toggle('open');
}

// ── Util ──────────────────────────────────────────────────────────────────────
function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}
