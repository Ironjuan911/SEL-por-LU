"""
app.py  –  Resolución de SEL por Descomposición LU
Aplicación de escritorio PyQt6 con interfaz HTML/CSS/JS embebida.
Ejecutar: python app.py
"""

import sys
import json

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import QObject, pyqtSlot, QFile, QIODevice, QUrl

import lu_solver


# ──────────────────────────── Bridge Python ↔ JS ────────────────────────────

class Bridge(QObject):
    """Objeto expuesto al JS a través de QWebChannel."""

    @pyqtSlot(str)
    def copyToClipboard(self, text):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

    @pyqtSlot(str, result=str)
    def solve(self, data_json: str) -> str:
        try:
            data = json.loads(data_json)
            result = lu_solver.solve(data["A"], data["b"])
            return json.dumps(result, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"error": str(exc)}, ensure_ascii=False)


# ──────────────────────── Cargar qwebchannel.js desde Qt ────────────────────

def _load_qwc_js() -> str:
    path = ":/qtwebchannel/qwebchannel.js"
    f = QFile(path)
    if f.open(QIODevice.OpenModeFlag.ReadOnly):
        content = bytes(f.readAll()).decode("utf-8")
        f.close()
        return content
    return "console.error('qwebchannel.js no encontrado');"


# ────────────────────────────── HTML de la app ──────────────────────────────

_HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>SEL — Descomposición LU</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<script>
MathJax = {
  tex: { inlineMath:[['$','$']], displayMath:[['\\[','\\]']], processEscapes:true },
  svg: { fontCache:'global' },
  startup: { typeset: false }
};
</script>
<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
<script>
%%QWEBCHANNEL%%
</script>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#07091a;--surface:rgba(255,255,255,.045);--border:rgba(255,255,255,.09);
  --p1:#7c6bff;--p2:#00d4ff;--warn:#f59e0b;--ok:#4ade80;--err:#f87171;
  --txt:#e2e8f0;--muted:#64748b;--radius:14px;
}
html{font-family:'Inter',sans-serif;font-size:15px;background:var(--bg);color:var(--txt);scroll-behavior:smooth}
body{min-height:100vh;padding-bottom:60px}

/* ── Header ── */
.app-header{
  background:linear-gradient(135deg,#0d0f2b 0%,#13183a 100%);
  border-bottom:1px solid var(--border);padding:22px 40px;
  display:flex;align-items:center;gap:18px;
}
.header-icon{
  width:52px;height:52px;border-radius:14px;font-size:26px;
  background:linear-gradient(135deg,var(--p1),var(--p2));
  display:grid;place-items:center;flex-shrink:0;
}
.app-header h1{font-size:1.45rem;font-weight:700;
  background:linear-gradient(90deg,var(--p1),var(--p2));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent}
.app-header p{font-size:.82rem;color:var(--muted);margin-top:2px}

/* ── Sections ── */
.container{max-width:1100px;margin:0 auto;padding:30px 24px}
.card{
  background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius);padding:28px;margin-bottom:22px;
  backdrop-filter:blur(12px);
}
.card h2{font-size:1rem;font-weight:600;color:var(--p2);margin-bottom:18px;
  display:flex;align-items:center;gap:8px}

/* ── Size selector ── */
.size-row{display:flex;align-items:center;gap:14px;margin-bottom:22px;flex-wrap:wrap}
.size-row label{font-size:.88rem;color:var(--muted);font-weight:500}
.size-btn{
  width:38px;height:38px;border-radius:8px;border:1px solid var(--border);
  background:transparent;color:var(--txt);font-size:.9rem;font-weight:600;
  cursor:pointer;transition:all .2s;
}
.size-btn:hover{border-color:var(--p1);color:var(--p1)}
.size-btn.active{background:var(--p1);border-color:var(--p1);color:#fff}

/* ── Matrix grid ── */
.matrix-area{display:flex;align-items:center;gap:4px;overflow-x:auto;padding:4px 0}
.bracket{font-size:3rem;color:var(--p2);font-weight:200;line-height:1;user-select:none;opacity:.7}
.sep-line{width:2px;background:var(--border);align-self:stretch;margin:0 6px}
.matrix-grid{display:grid;gap:7px}
.cell{
  width:62px;height:44px;background:rgba(255,255,255,.06);
  border:1px solid var(--border);border-radius:8px;
  color:var(--txt);font-size:.9rem;font-family:'Inter',sans-serif;
  text-align:center;outline:none;transition:border-color .2s;
}
.cell:focus{border-color:var(--p1);background:rgba(124,107,255,.12)}
.cell.b-cell{border-color:rgba(0,212,255,.25);background:rgba(0,212,255,.06)}
.cell.b-cell:focus{border-color:var(--p2)}
.col-label{
  font-size:.72rem;color:var(--muted);text-align:center;
  font-weight:600;letter-spacing:.04em;
}
.col-label.b-label{color:var(--p2)}

/* ── Buttons ── */
.btn-row{display:flex;gap:12px;margin-top:20px;flex-wrap:wrap}
.btn{
  padding:11px 28px;border-radius:10px;font-size:.9rem;font-weight:600;
  cursor:pointer;border:none;transition:all .2s;font-family:'Inter',sans-serif;
}
.btn-primary{
  background:linear-gradient(135deg,var(--p1),var(--p2));color:#fff;
}
.btn-primary:hover{opacity:.88;transform:translateY(-1px)}
.btn-secondary{
  background:transparent;border:1px solid var(--border);color:var(--txt);
}
.btn-secondary:hover{border-color:var(--p1);color:var(--p1)}

/* ── Solution banner ── */
#solution-banner{display:none}
.solution-banner{
  background:linear-gradient(135deg,rgba(74,222,128,.12),rgba(0,212,255,.08));
  border:1px solid rgba(74,222,128,.3);border-radius:var(--radius);
  padding:24px 28px;margin-bottom:22px;text-align:center;
}
.solution-banner h3{color:var(--ok);font-size:.88rem;font-weight:600;margin-bottom:10px}
.solution-math{font-size:1.05rem;min-height:40px}

/* ── Steps area ── */
.steps-toggle{
  background:transparent;border:1px solid var(--border);border-radius:10px;
  color:var(--muted);font-size:.85rem;padding:8px 16px;cursor:pointer;
  font-family:'Inter',sans-serif;transition:all .2s;margin-bottom:16px;
}
.steps-toggle:hover{border-color:var(--p1);color:var(--p1)}
.step-card{
  border-radius:12px;padding:20px 22px;margin-bottom:12px;
  border-left:4px solid var(--border);
  animation:fadeUp .4s ease both;
  transition:box-shadow .2s;
}
.step-card:hover{box-shadow:0 4px 20px rgba(0,0,0,.3)}
@keyframes fadeUp{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}

.step-title{font-size:.88rem;font-weight:600;margin-bottom:10px;color:var(--txt)}
.step-math{text-align:center;padding:10px 0;font-size:.95rem;overflow-x:auto}
.matrices-row{display:flex;flex-wrap:wrap;gap:18px;margin-top:14px;justify-content:center}
.mat-block{text-align:center}
.mat-label{font-size:.72rem;color:var(--muted);font-weight:600;letter-spacing:.08em;margin-bottom:6px}
.mat-math{font-size:.82rem;overflow-x:auto}

/* step type colors */
.type-system   {background:rgba(0,212,255,.07);  border-left-color:#00d4ff}
.type-phase    {background:rgba(124,107,255,.1);  border-left-color:var(--p1);padding:16px 22px}
.type-pivot    {background:rgba(245,158,11,.07); border-left-color:var(--warn)}
.type-elim     {background:rgba(167,139,250,.07);border-left-color:#a78bfa}
.type-lures    {background:rgba(74,222,128,.08); border-left-color:var(--ok)}
.type-fstep    {background:rgba(56,189,248,.07); border-left-color:#38bdf8}
.type-fres     {background:rgba(20,184,166,.07); border-left-color:#14b8a6}
.type-bstep    {background:rgba(251,113,133,.07);border-left-color:#fb7185}
.type-solution {background:rgba(251,191,36,.09); border-left-color:#fbbf24;padding:22px 26px}
.type-error    {background:rgba(248,113,113,.09);border-left-color:var(--err)}

.phase-title{font-size:1rem;font-weight:700;color:var(--p1)}
.sol-title{font-size:1.05rem;font-weight:700;color:#fbbf24}
.sol-math{font-size:1.15rem}

/* loader */
#loader{display:none;text-align:center;padding:30px;color:var(--muted)}
.spinner{width:34px;height:34px;border:3px solid var(--border);border-top-color:var(--p1);
  border-radius:50%;animation:spin .7s linear infinite;margin:0 auto 10px}
@keyframes spin{to{transform:rotate(360deg)}}

    /* toast */
    #toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:rgba(255,255,255,0.1);
      border:1px solid var(--p1);padding:12px 24px;border-radius:12px;backdrop-filter:blur(10px);
      z-index:2000;opacity:0;transition:opacity .3s;pointer-events:none;color:white;font-weight:500}
    #toast.show{opacity:1}
  </style>
</head>
<body>

<header class="app-header">
  <div class="header-icon">Σ</div>
  <div>
    <h1>Resolución de SEL — Descomposición LU</h1>
    <p>Método de Doolittle con pivoteo parcial &nbsp;·&nbsp; Paso a paso con LaTeX</p>
  </div>
</header>

<div class="container">

  <!-- Input card -->
  <div class="card">
    <h2>Sistema de ecuaciones</h2>
    <div class="size-row">
      <label>Tamaño del sistema:</label>
      <div id="size-buttons"></div>
    </div>
    <div class="matrix-area" id="matrix-area"></div>
    <div id="input-error"></div>
    <div class="btn-row">
      <button class="btn btn-primary" onclick="solveSystem()">Resolver →</button>
      <button class="btn btn-secondary" onclick="copyLatex()">Copiar LaTeX</button>
      <button class="btn btn-secondary" onclick="clearMatrix()">Limpiar</button>
      <button class="btn btn-secondary" onclick="loadExample()">Ejemplo 4×4</button>
    </div>
  </div>

  <!-- Solution banner -->
  <div id="solution-banner" class="solution-banner">
    <h3>✓ SOLUCIÓN ENCONTRADA</h3>
    <div class="solution-math" id="solution-math"></div>
  </div>

  <!-- Loader -->
  <div id="loader"><div class="spinner"></div><p>Calculando…</p></div>

  <!-- Steps -->
  <div id="steps-section" style="display:none">
    <button class="steps-toggle" onclick="toggleAllSteps()">▼ Colapsar todos los pasos</button>
    <div id="steps-container"></div>
  </div>

</div>
<div id="toast">¡Copiado!</div>

<script>
// ─── Estado ──────────────────────────────────────────────────────────────────
let currentN = 4;
let bridge = null;
let stepsCollapsed = false;

// ─── Inicializar QWebChannel ──────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  buildSizeButtons();
  generateGrid(currentN);
  new QWebChannel(qt.webChannelTransport, ch => {
    bridge = ch.objects.bridge;
  });
});

// ─── Botones de tamaño ────────────────────────────────────────────────────────
function buildSizeButtons() {
  const c = document.getElementById('size-buttons');
  c.innerHTML = '';
  for (let n = 2; n <= 8; n++) {
    const b = document.createElement('button');
    b.className = 'size-btn' + (n === currentN ? ' active' : '');
    b.textContent = n + '×' + n;
    b.onclick = () => { currentN = n; buildSizeButtons(); generateGrid(n); resetResults(); };
    c.appendChild(b);
  }
}

// ─── Generar grid de entrada ──────────────────────────────────────────────────
function generateGrid(n) {
  const area = document.getElementById('matrix-area');
  area.innerHTML = '';

  // bracket left
  const bl = document.createElement('span');
  bl.className = 'bracket'; bl.textContent = '[';
  area.appendChild(bl);

  const wrapper = document.createElement('div');
  const cols = n + 1; // n cols for A, 1 for b
  wrapper.style.display = 'grid';
  wrapper.style.gridTemplateColumns = `repeat(${n}, 1fr) 2px repeat(1, 1fr)`;
  wrapper.style.gap = '7px';
  wrapper.style.alignItems = 'center';

  // Column labels row
  for (let j = 0; j < n; j++) {
    const lbl = document.createElement('div');
    lbl.className = 'col-label';
    lbl.textContent = 'x' + (j + 1);
    wrapper.appendChild(lbl);
  }
  // separator label
  const sepLbl = document.createElement('div'); wrapper.appendChild(sepLbl);
  const bLbl = document.createElement('div');
  bLbl.className = 'col-label b-label'; bLbl.textContent = 'b';
  wrapper.appendChild(bLbl);

  // Data rows
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n; j++) {
      const inp = document.createElement('input');
      inp.type = 'number'; inp.step = 'any';
      inp.className = 'cell'; inp.id = `c${i}_${j}`;
      inp.onkeydown = (e) => handleMatrixKey(e, i, j);
      wrapper.appendChild(inp);
    }
    // separator
    const sep = document.createElement('div');
    sep.style.cssText = 'background:rgba(255,255,255,.12);width:2px;height:100%;border-radius:2px';
    wrapper.appendChild(sep);
    // b input
    const bInp = document.createElement('input');
    bInp.type = 'number'; bInp.step = 'any';
    bInp.className = 'cell b-cell'; bInp.id = `c${i}_b`;
    bInp.onkeydown = (e) => handleMatrixKey(e, i, 'b');
    wrapper.appendChild(bInp);
  }

  area.appendChild(wrapper);
  const br = document.createElement('span');
  br.className = 'bracket'; br.textContent = ']';
  area.appendChild(br);
}

// ─── Manejo de navegación con Enter ───────────────────────────────────────────
function handleMatrixKey(e, i, j) {
  if (e.key === 'Enter') {
    e.preventDefault();
    const n = currentN;
    let next = null;

    if (j === 'b') {
      if (i < n - 1) next = document.getElementById(`c${i+1}_0`);
      else solveSystem(); // Última celda -> Resolver
    } else {
      if (j < n - 1) next = document.getElementById(`c${i}_${j+1}`);
      else next = document.getElementById(`c${i}_b`);
    }

    if (next) {
      next.focus();
      next.select();
    }
  }
}

// ─── Leer datos del grid ─────────────────────────────────────────────────────
function readMatrix() {
  const n = currentN;
  const A = [], b = [];
  for (let i = 0; i < n; i++) {
    const row = [];
    for (let j = 0; j < n; j++) {
      const v = parseFloat(document.getElementById(`c${i}_${j}`).value);
      if (isNaN(v)) return null;
      row.push(v);
    }
    A.push(row);
    const bv = parseFloat(document.getElementById(`c${i}_b`).value);
    if (isNaN(bv)) return null;
    b.push(bv);
  }
  return { A, b };
}

// ─── Limpiar ─────────────────────────────────────────────────────────────────
function clearMatrix() {
  for (let i = 0; i < currentN; i++) {
    for (let j = 0; j < currentN; j++) document.getElementById(`c${i}_${j}`).value = '';
    document.getElementById(`c${i}_b`).value = '';
  }
  resetResults();
}

// ─── Ejemplo 4×4 ─────────────────────────────────────────────────────────────
function loadExample() {
  const n4 = [[2,-1,0,3],[4,1,-1,2],[-2,3,2,0],[0,2,-1,1]];
  const b4 = [7,9,3,2];

  // Switch to 4×4 if needed
  if (currentN !== 4) { currentN = 4; buildSizeButtons(); generateGrid(4); resetResults(); }

  setTimeout(() => {
    for (let i = 0; i < 4; i++) {
      for (let j = 0; j < 4; j++) document.getElementById(`c${i}_${j}`).value = n4[i][j];
      document.getElementById(`c${i}_b`).value = b4[i];
    }
  }, 50);
}

// ─── Resolver ─────────────────────────────────────────────────────────────────
function solveSystem() {
  document.getElementById('input-error').innerHTML = '';
  const data = readMatrix();
  if (!data) {
    document.getElementById('input-error').innerHTML =
      '<div class="msg-error">⚠ Completa todas las celdas con valores numéricos.</div>';
    return;
  }
  if (!bridge) {
    document.getElementById('input-error').innerHTML =
      '<div class="msg-error">⚠ Conexión con el backend no establecida. Espera un momento y vuelve a intentarlo.</div>';
    return;
  }
  showLoader(true);
  resetResults();
  bridge.solve(JSON.stringify(data), resultJson => {
    showLoader(false);
    const result = JSON.parse(resultJson);
    if (result.error) {
      document.getElementById('input-error').innerHTML =
        `<div class="msg-error">Error: ${result.error}</div>`;
      return;
    }
    renderResults(result);
  });
}

// ─── Copiar a LaTeX ──────────────────────────────────────────────────────────
function copyLatex() {
  const n = currentN;
  
  // — Formato Matricial —
  let Alatex = '\\begin{pmatrix}\n';
  for (let i = 0; i < n; i++) {
    let row = [];
    for (let j = 0; j < n; j++) {
      const val = document.getElementById(`c${i}_${j}`).value || '0';
      row.push(val);
    }
    Alatex += '  ' + row.join(' & ') + ' \\\\\n';
  }
  Alatex += '\\end{pmatrix}';
  
  let blatex = '\\begin{pmatrix}\n';
  for (let i = 0; i < n; i++) {
    const val = document.getElementById(`c${i}_b`).value || '0';
    blatex += `  ${val} \\\\\n`;
  }
  blatex += '\\end{pmatrix}';

  // — Formato de Sistema de Ecuaciones (SLE) —
  let sleLatex = '\\begin{cases}\n';
  const vars = n <= 4 ? ['x', 'y', 'z', 'w'] : Array.from({length:n}, (_,k) => `x_{${k+1}}`);
  
  for (let i = 0; i < n; i++) {
    let rowEq = [];
    let hasTerms = false;
    for (let j = 0; j < n; j++) {
      let raw = document.getElementById(`c${i}_${j}`).value || '0';
      let val = parseFloat(raw);
      if (val === 0) continue;
      
      let term = '';
      if (val === 1) term = vars[j];
      else if (val === -1) term = `-${vars[j]}`;
      else term = `${raw}${vars[j]}`;
      
      if (hasTerms && val > 0) term = `+ ${term}`;
      else if (hasTerms && val < 0) term = ` ${term}`; // El signo ya está en el término
      
      rowEq.push(term);
      hasTerms = true;
    }
    const bVal = document.getElementById(`c${i}_b`).value || '0';
    sleLatex += `  ${hasTerms ? rowEq.join(' ') : '0'} = ${bVal} \\\\\n`;
  }
  sleLatex += '\\end{cases}';

  const fullLatex = `% Modo Matricial\nA = ${Alatex}\n\nb = ${blatex}\n\n% Modo Sistema de Ecuaciones\n${sleLatex}`;
  
  if (bridge) {
    bridge.copyToClipboard(fullLatex);
    showToast('¡Matrices y SLE copiados!');
  } else {
    console.error('Bridge no disponible');
  }
}

function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2000);
}

// ─── Reset resultados ─────────────────────────────────────────────────────────
function resetResults() {
  document.getElementById('solution-banner').style.display = 'none';
  document.getElementById('steps-section').style.display = 'none';
  document.getElementById('steps-container').innerHTML = '';
}

// ─── Loader ───────────────────────────────────────────────────────────────────
function showLoader(on) {
  document.getElementById('loader').style.display = on ? 'block' : 'none';
}

// ─── Toggle colapsar pasos ────────────────────────────────────────────────────
function toggleAllSteps() {
  stepsCollapsed = !stepsCollapsed;
  document.querySelectorAll('.step-math, .matrices-row').forEach(el => {
    el.style.display = stepsCollapsed ? 'none' : '';
  });
  document.querySelector('.steps-toggle').textContent =
    stepsCollapsed ? '▶ Expandir todos los pasos' : '▼ Colapsar todos los pasos';
}

// ─── Renderizar resultados ────────────────────────────────────────────────────
async function renderResults(result) {
  // Solution banner
  const banner = document.getElementById('solution-banner');
  const mathDiv = document.getElementById('solution-math');
  mathDiv.innerHTML = `\\[x = ${result.x_latex}\\]`;
  banner.style.display = 'block';

  // Steps
  const stepsSection = document.getElementById('steps-section');
  const container = document.getElementById('steps-container');
  container.innerHTML = '';
  stepsSection.style.display = 'block';

  const typeClass = {
    system:'type-system', phase_header:'type-phase',
    pivot:'type-pivot', elimination:'type-elim', lu_result:'type-lures',
    forward_step:'type-fstep', forward_result:'type-fres',
    backward_step:'type-bstep', solution:'type-solution', error:'type-error'
  };

  for (let idx = 0; idx < result.steps.length; idx++) {
    const step = result.steps[idx];
    const card = document.createElement('div');
    const cls = typeClass[step.type] || 'type-system';
    card.className = `step-card ${cls}`;
    card.style.animationDelay = `${idx * 40}ms`;

    const isSolution = step.type === 'solution';
    const isPhase = step.type === 'phase_header';

    // Title
    const titleDiv = document.createElement('div');
    titleDiv.className = isSolution ? 'step-title sol-title' : (isPhase ? 'step-title phase-title' : 'step-title');
    titleDiv.innerHTML = step.title;
    card.appendChild(titleDiv);

    // Main latex
    if (step.latex) {
      const mathDiv2 = document.createElement('div');
      mathDiv2.className = 'step-math' + (isSolution ? ' sol-math' : '');
      mathDiv2.innerHTML = `\\[${step.latex}\\]`;
      card.appendChild(mathDiv2);
    }

    // Side-by-side matrices (L, U, P when show_matrices)
    if (step.show_matrices) {
      const row = document.createElement('div');
      row.className = 'matrices-row';
      const mats = [
        { key:'L_latex', label:'L' },
        { key:'U_latex', label:'U' },
        { key:'P_latex', label:'P' },
      ];
      for (const { key, label } of mats) {
        if (step[key]) {
          const blk = document.createElement('div');
          blk.className = 'mat-block';
          blk.innerHTML =
            `<div class="mat-label">${label}</div>`+
            `<div class="mat-math">\\[${step[key]}\\]</div>`;
          row.appendChild(blk);
        }
      }
      card.appendChild(row);
    }

    container.appendChild(card);
  }

  // Typeset all MathJax at once
  if (window.MathJax) {
    await MathJax.typesetPromise([
      document.getElementById('solution-math'),
      container
    ]);
  }
}
</script>
</body>
</html>
"""


# ─────────────────────────────── MainWindow ──────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Resolución de SEL — Descomposición LU")
        self.resize(1200, 820)

        self.view = QWebEngineView()

        # Configurar QWebChannel
        self.channel = QWebChannel()
        self.bridge = Bridge()
        self.channel.registerObject("bridge", self.bridge)
        self.view.page().setWebChannel(self.channel)

        # Inyectar qwebchannel.js en el HTML
        qwc_js = _load_qwc_js()
        html = _HTML.replace("%%QWEBCHANNEL%%", qwc_js)
        self.view.setHtml(html, QUrl("about:blank"))

        self.setCentralWidget(self.view)
        self.show()


# ─────────────────────────────── Entry point ─────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    sys.exit(app.exec())
