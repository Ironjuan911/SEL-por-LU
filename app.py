"""
app.py  –  Resolución de SEL por Descomposición LU
Interfaz de escritorio con CustomTkinter + matplotlib para LaTeX.
Ejecutar: python app.py
"""

import threading
import io
import re
import sys

import customtkinter as ctk
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.figure as mfig
from matplotlib.backends.backend_agg import FigureCanvasAgg

import lu_solver

# ─────────────────────────── Paleta de colores ────────────────────────────────

BG       = "#07091a"
SURFACE  = "#0f1127"
SURFACE2 = "#141730"
BORDER   = "#1e2245"
P1       = "#7c6bff"
P2       = "#00d4ff"
WARN     = "#f59e0b"
OK       = "#4ade80"
ERR      = "#f87171"
TXT      = "#e2e8f0"
MUTED    = "#64748b"

# Color de tarjeta por tipo de paso
STEP_COLORS = {
    "system":         (SURFACE2, P2),
    "phase_header":   (SURFACE,  P1),
    "pivot":          (SURFACE2, WARN),
    "elimination":    (SURFACE2, "#a78bfa"),
    "lu_result":      (SURFACE2, OK),
    "forward_step":   (SURFACE2, "#38bdf8"),
    "forward_result": (SURFACE2, "#14b8a6"),
    "backward_step":  (SURFACE2, "#fb7185"),
    "solution":       (SURFACE2, "#fbbf24"),
    "error":          (SURFACE2, ERR),
}


# ─────────────────────────── Helper: LaTeX → imagen ──────────────────────────

def _sanitize_latex(s: str) -> str:
    r"""
    Convierte LaTeX con \text{...} a formato compatible con matplotlib (inline math).
    Ejemplo: "\text{Hola } x=1" -> "Hola $x=1$"
    """
    # 1. Quitar símbolos de $ residuales (se envuelven más adelante de forma segura)
    s = s.replace("$", "")
    
    # 2. Reemplazos de conveniencia para saltos y reemplazo del "_" de NaN por punto central (\cdot)
    s = s.replace(r"\qquad", r" \quad ").replace(r"\quad", r" \; ")
    s = s.replace(r"\mathrm{\_}", r"\cdot").replace(r"\text{\_}", r"\cdot").replace(r"\_", r"\cdot")

    # 3. Procesar \text{...} separando en partes usando una regex iterativa
    parts = []
    last_pos = 0
    # Buscar \text{...} o \mathrm{...} (tratamos ambos como texto plano para mathtext si tienen espacios)
    for m in re.finditer(r"\\(?:text|mathrm)\{([^}]*)\}", s):
        # El bloque antes del comando es math
        math_part = s[last_pos:m.start()].strip()
        if math_part:
            # Eliminar comas residuales al inicio/fin del math part
            math_part = re.sub(r"^[,;\\;]+|[,;\\;]+$", "", math_part).strip()
            if math_part:
                parts.append(f"${math_part}$")
        
        # El contenido del comando es texto plano
        text_content = m.group(1)
        parts.append(text_content)
        
        last_pos = m.end()
    
    # El resto final es math
    remaining = s[last_pos:].strip()
    if remaining:
        remaining = re.sub(r"^[,;\\;]+|[,;\\;]+$", "", remaining).strip()
        if remaining:
            if not parts:
                return f"${remaining}$"
            parts.append(f"${remaining}$")
    
    if not parts:
        return ""
        
    return " ".join(parts)


# ── Segmentado: separa mathtext puro de entornos \begin{bmatrix} ─────────────

_BMATRIX_RE = re.compile(r"\\begin\{bmatrix\}(.*?)\\end\{bmatrix\}", re.DOTALL)


def _split_segments(latex: str) -> list:
    """
    Divide una cadena LaTeX en segmentos alternados:
      ('text',   str)        → fragmento de mathtext puro
      ('matrix', list[list]) → filas/columnas de una bmatrix
    """
    # Identifica matriz separándola de todo el texto que está antes y después.
    segs = []
    last = 0
    for m in _BMATRIX_RE.finditer(latex):
        if m.start() > last:
            segs.append(("text", latex[last:m.start()]))
        
        # Procesar contenido de la matriz
        rows = []
        # Dividir por \\ o \cr
        raw_rows = re.split(r"\\\\|\\cr", m.group(1))
        for row_s in raw_rows:
            row_s = row_s.strip()
            if row_s:
                # Dividir por &
                rows.append([c.strip() for c in row_s.split("&") if c.strip()])
        
        if rows:
            segs.append(("matrix", rows))
        last = m.end()
        
    if last < len(latex):
        segs.append(("text", latex[last:]))
    return segs


# ── Render: fragmento mathtext puro ──────────────────────────────────────────

def _render_mathtext(s: str, fg: str, fontsize: float, dpi: int) -> Image.Image | None:
    """Renderiza un fragmento (ya sea math puro, texto mixto o sanitizado) a PIL."""
    s = s.strip()
    if not s:
        return None
    
    # Si no tiene $, asumimos que es math puro y lo envolvemos
    if "$" not in s:
        s = f"${s}$"
    
    try:
        # Usamos una figura grande para la medición inicial
        fig = mfig.Figure(figsize=(15, 2), dpi=dpi)
        canvas = FigureCanvasAgg(fig)
        fig.patch.set_alpha(0)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_axis_off()
        ax.patch.set_alpha(0)
        
        txt = ax.text(0, 0.5, s, ha="left", va="center",
                      color=fg, fontsize=fontsize, usetex=False)
        
        canvas.draw()
        renderer = canvas.get_renderer()
        bbox = txt.get_window_extent(renderer=renderer)
        
        # Holgura para evitar cortes (escalada según DPI)
        scale = dpi / 150.0
        pad = int(12 * scale)
        w = int(bbox.width) + pad * 2
        h = int(bbox.height) + pad * 2
        w = max(w, 10)
        h = max(h, 10)

        # Re-renderizado con el tamaño ajustado
        fig2 = mfig.Figure(figsize=(w / dpi, h / dpi), dpi=dpi)
        FigureCanvasAgg(fig2)
        fig2.patch.set_alpha(0)
        ax2 = fig2.add_axes([0, 0, 1, 1])
        ax2.set_axis_off()
        ax2.patch.set_alpha(0)
        # Dibujamos centrado en la nueva figura
        ax2.text(0.5, 0.5, s, ha="center", va="center",
                 color=fg, fontsize=fontsize, usetex=False)
        
        buf = io.BytesIO()
        fig2.savefig(buf, format="png", dpi=dpi, transparent=True, pad_inches=0)
        buf.seek(0)
        return Image.open(buf).convert("RGBA")
    except Exception as exc:
        print(f"[mathtext] {exc}  src={s}")
        return None


# ── Render: matriz como imagen PIL ───────────────────────────────────────────

def _render_matrix(rows: list, fg: str, fontsize: float, dpi: int) -> Image.Image:
    """
    Renderiza una matriz como imagen PIL.
    """
    # Cada celda de la matriz es MATH puro; se generan imágenes individuales por celda.
    cell_imgs: list[list[Image.Image]] = []
    max_w = max_h = 0
    for row in rows:
        row_imgs = []
        for cell in row:
            # Asegurar modo math para la celda
            cell_math = cell.strip()
            if not cell_math.startswith("$"):
                cell_math = f"${cell_math}$"
            # Limpieza básica de NaN (\_) -> \cdot
            cell_math = cell_math.replace(r"\mathrm{\_}", r"\cdot").replace(r"\text{\_}", r"\cdot").replace(r"\_", r"\cdot")
            
            img = _render_mathtext(cell_math, fg, fontsize * 0.95, dpi)
            if img is None:
                img = Image.new("RGBA", (10, 10), (0, 0, 0, 0))
            row_imgs.append(img)
            max_w = max(max_w, img.width)
            max_h = max(max_h, img.height)
        cell_imgs.append(row_imgs)

    n_rows = len(rows)
    # Encontrar el número máximo de columnas
    n_cols = max(len(r) for r in cell_imgs) if cell_imgs else 0
    
    scale = dpi / 150.0
    pad_x, pad_y = int(10 * scale), int(8 * scale)
    cell_w = max_w + pad_x * 2
    cell_h = max_h + pad_y * 2
    grid_w = n_cols * cell_w
    grid_h = n_rows * cell_h

    # Dibujar corchetes - usando líneas simples de PIL
    bracket_w = int(14 * scale)
    total_w = grid_w + bracket_w * 2
    out = Image.new("RGBA", (total_w, grid_h), (0, 0, 0, 0))
    
    from PIL import ImageDraw
    draw = ImageDraw.Draw(out)
    
    line_w = max(1, int(2 * scale))
    # Corchete izquierdo [
    draw.line([(bracket_w - int(2*scale), int(2*scale)), (int(4*scale), int(2*scale)), (int(4*scale), grid_h - int(3*scale)), (bracket_w - int(2*scale), grid_h - int(3*scale))], fill=fg, width=line_w)
    # Corchete derecho ]
    draw.line([(total_w - bracket_w + int(2*scale), int(2*scale)), (total_w - int(4*scale), int(2*scale)), (total_w - int(4*scale), grid_h - int(3*scale)), (total_w - bracket_w + int(2*scale), grid_h - int(3*scale))], fill=fg, width=line_w)

    # Pegar celdas
    for i, row_imgs in enumerate(cell_imgs):
        for j, img in enumerate(row_imgs):
            x = bracket_w + j * cell_w + (cell_w - img.width) // 2
            y = i * cell_h + (cell_h - img.height) // 2
            out.paste(img, (x, y), img)

    return out


# ── Caché para no re-renderizar ──────────────────────────────────────────────
# Evitamos cálculos repetitivos (renderizar matplotlib a bytes a PIL y luego a CTkImage es costoso)
_IMAGE_CACHE: dict = {}

def latex_to_image(
    latex: str,
    fg: str = TXT,
    fontsize: float = 12,
    dpi: int = 300,
    max_width_px: int = 1720,
) -> ctk.CTkImage | None:
    """Renderiza LaTeX (incluyendo bmatrix) como CTkImage."""
    # NOTA: NO sanitizamos el string completo aquí para evitar que los 
    # $ residuales arruinen el spliteo de matrices.
    
    cache_key = (latex, fg, fontsize, dpi)
    if cache_key in _IMAGE_CACHE:
        return _IMAGE_CACHE[cache_key]

    try:
        segs = _split_segments(latex)
        
        part_imgs: list[Image.Image] = []
        for kind, data in segs:
            if kind == "text":
                # Sanitizamos el texto para convertir \text{} en $ math $
                sanitized_text = _sanitize_latex(data)
                img = _render_mathtext(sanitized_text, fg, fontsize, dpi)
            else:
                # Renderizado de matriz
                img = _render_matrix(data, fg, fontsize, dpi)
            if img:
                part_imgs.append(img)

        if not part_imgs:
            # Reintentar con el original sanitizado si todo falló
            img = _render_mathtext(_sanitize_latex(latex), fg, fontsize, dpi)
            if not img: return None
            part_imgs = [img]

        scale = dpi / 150.0
        gap = int(8 * scale)
        total_w = sum(i.width for i in part_imgs) + gap * (max(0, len(part_imgs) - 1))
        max_h = max(i.height for i in part_imgs)
        
        combined = Image.new("RGBA", (total_w, max_h), (0, 0, 0, 0))
        x_offset = 0
        for img in part_imgs:
            y_offset = (max_h - img.height) // 2
            combined.paste(img, (x_offset, y_offset), img)
            x_offset += img.width + gap

        # Escalar si es muy ancho
        final_img = combined
        if combined.width > max_width_px:
            ratio = max_width_px / combined.width
            final_img = combined.resize((max_width_px, int(combined.height * ratio)), Image.LANCZOS)

        ctk_img = ctk.CTkImage(
            light_image=final_img,
            dark_image=final_img,
            size=(final_img.width / scale, final_img.height / scale),
        )
        _IMAGE_CACHE[cache_key] = ctk_img
        return ctk_img

    except Exception as exc:
        print(f"[latex_to_image] Error: {exc}\n  LaTeX: {latex}")
        return None





# ─────────────────────────── Ventana principal ────────────────────────────────

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Resolución de SEL — Descomposición LU")
        self.geometry("1280x820")
        self.minsize(900, 600)
        self.configure(fg_color=BG)

        self.current_n = 4
        self._entry_cells: dict = {}   # (i, j) o (i, 'b') → CTkEntry
        self._solving = False

        self._build_ui()

    # ─────────────────────── Construcción de la UI ────────────────────────────

    def _build_ui(self):
        # ── Header ──────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="#0d0f2b", corner_radius=0)
        hdr.pack(fill="x", side="top")

        icon = ctk.CTkLabel(
            hdr, text="Σ", width=52, height=52,
            font=ctk.CTkFont(size=26, weight="bold"),
            fg_color=P1, corner_radius=14,
            text_color="white",
        )
        icon.pack(side="left", padx=(24, 14), pady=14)

        hdr_text = ctk.CTkFrame(hdr, fg_color="transparent")
        hdr_text.pack(side="left", pady=14)

        ctk.CTkLabel(
            hdr_text, text="Resolución de SEL — Descomposición LU",
            font=ctk.CTkFont(family="Arial", size=18, weight="bold"),
            text_color=P1,
        ).pack(anchor="w")
        ctk.CTkLabel(
            hdr_text,
            text="Método de Doolittle con pivoteo parcial · Paso a paso con LaTeX",
            font=ctk.CTkFont(size=11),
            text_color=MUTED,
        ).pack(anchor="w")

        # ── Cuerpo principal (izquierda + derecha) ───────────────────────────
        body = ctk.CTkFrame(self, fg_color=BG)
        body.pack(fill="both", expand=True, padx=0, pady=0)
        body.columnconfigure(0, weight=0, minsize=400)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # Panel izquierdo (entrada)
        left = ctk.CTkFrame(body, fg_color=SURFACE, corner_radius=0)
        left.grid(row=0, column=0, sticky="nsew")

        # Panel derecho (resultados)
        self.results_scroll = ctk.CTkScrollableFrame(
            body, fg_color=BG,
            scrollbar_button_color=BORDER,
            scrollbar_button_hover_color=P1,
        )
        self.results_scroll.grid(row=0, column=1, sticky="nsew")
        self.results_scroll.columnconfigure(0, weight=1)

        self._build_left(left)
        self._build_placeholder()

    def _build_left(self, parent):
        parent.columnconfigure(0, weight=1)

        # Título del panel
        ctk.CTkLabel(
            parent,
            text="Sistema de ecuaciones",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=P2,
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 6))

        # ── Selector de tamaño ───────────────────────────────────────────────
        size_row = ctk.CTkFrame(parent, fg_color="transparent")
        size_row.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 10))

        ctk.CTkLabel(
            size_row, text="Tamaño:", font=ctk.CTkFont(size=11),
            text_color=MUTED,
        ).pack(side="left", padx=(0, 8))

        self._size_buttons = {}
        for n in range(2, 9):
            btn = ctk.CTkButton(
                size_row,
                text=f"{n}×{n}",
                width=46, height=32,
                corner_radius=8,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=P1 if n == self.current_n else "transparent",
                border_color=BORDER,
                border_width=1,
                hover_color="#5a4ee0",
                text_color="white",
                command=lambda _n=n: self._select_size(_n),
            )
            btn.pack(side="left", padx=2)
            self._size_buttons[n] = btn

        # ── Área de la matriz ────────────────────────────────────────────────
        self.matrix_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.matrix_frame.grid(row=2, column=0, padx=20, pady=(0, 8), sticky="w")

        # Error de entrada
        self.input_error_var = ctk.StringVar(value="")
        self._err_label = ctk.CTkLabel(
            parent,
            textvariable=self.input_error_var,
            font=ctk.CTkFont(size=11),
            text_color=ERR,
            wraplength=340,
        )
        self._err_label.grid(row=3, column=0, sticky="w", padx=20, pady=(0, 4))

        # ── Botones ───────────────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.grid(row=4, column=0, sticky="w", padx=20, pady=(4, 20))

        self._solve_btn = ctk.CTkButton(
            btn_frame,
            text="Resolver  →",
            width=120, height=38,
            corner_radius=10,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=P1,
            hover_color="#5a4ee0",
            command=self._on_solve,
        )
        self._solve_btn.pack(side="left", padx=(0, 8))

        for label, cmd in [
            ("Copiar LaTeX", self._on_copy_latex),
            ("Limpiar",      self._on_clear),
            ("Ejemplo 4×4",  self._on_example),
        ]:
            ctk.CTkButton(
                btn_frame,
                text=label,
                width=110, height=38,
                corner_radius=10,
                font=ctk.CTkFont(size=11),
                fg_color="transparent",
                border_color=BORDER,
                border_width=1,
                hover_color=SURFACE2,
                text_color=TXT,
                command=cmd,
            ).pack(side="left", padx=(0, 6))

        # Generar grid inicial
        self._generate_grid(self.current_n)

    def _build_placeholder(self):
        """Mensaje inicial en el panel de resultados."""
        self._clear_results()
        ph = ctk.CTkLabel(
            self.results_scroll,
            text="Introduce el sistema y pulsa\n«Resolver →»",
            font=ctk.CTkFont(size=14),
            text_color=MUTED,
        )
        ph.grid(row=0, column=0, padx=40, pady=80)

    # ─────────────────────── Grid de entrada ─────────────────────────────────

    def _generate_grid(self, n: int):
        for w in self.matrix_frame.winfo_children():
            w.destroy()
        self._entry_cells.clear()

        # Etiquetas de columna
        for j in range(n):
            ctk.CTkLabel(
                self.matrix_frame,
                text=f"x{j+1}",
                font=ctk.CTkFont(size=9, weight="bold"),
                text_color=MUTED, width=58,
            ).grid(row=0, column=j * 2, padx=2)
        # Separador de etiqueta
        ctk.CTkLabel(self.matrix_frame, text="", width=8).grid(row=0, column=n * 2 - 1)
        ctk.CTkLabel(
            self.matrix_frame,
            text="b",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color=P2, width=58,
        ).grid(row=0, column=n * 2 + 1, padx=2)

        # Filas de entrada
        for i in range(n):
            for j in range(n):
                ent = ctk.CTkEntry(
                    self.matrix_frame,
                    width=58, height=40,
                    corner_radius=8,
                    border_color=BORDER,
                    fg_color="#0a0c20",
                    text_color=TXT,
                    font=ctk.CTkFont(size=12),
                    justify="center",
                )
                ent.grid(row=i + 1, column=j * 2, padx=2, pady=2)
                ent.bind("<Return>",
                         lambda e, _i=i, _j=j: self._next_focus(_i, _j))
                self._entry_cells[(i, j)] = ent

                # Línea separadora vertical (solo después de la última col A)
                if j == n - 1:
                    sep = ctk.CTkFrame(
                        self.matrix_frame,
                        width=2, height=40,
                        fg_color="#1e2245",
                    )
                    sep.grid(row=i + 1, column=n * 2 - 1, padx=4)

            # Entrada b
            b_ent = ctk.CTkEntry(
                self.matrix_frame,
                width=58, height=40,
                corner_radius=8,
                border_color="#003344",
                fg_color="#020e15",
                text_color=P2,
                font=ctk.CTkFont(size=12),
                justify="center",
            )
            b_ent.grid(row=i + 1, column=n * 2 + 1, padx=2, pady=2)
            b_ent.bind("<Return>",
                       lambda e, _i=i: self._next_focus(_i, "b"))
            self._entry_cells[(i, "b")] = b_ent

    def _next_focus(self, i: int, j):
        """Navega al siguiente campo con Enter."""
        n = self.current_n
        if j == "b":
            if i < n - 1:
                self._entry_cells.get((i + 1, 0), None)
            else:
                self._on_solve()
                return
            nxt = self._entry_cells.get((i + 1, 0))
        elif isinstance(j, int) and j < n - 1:
            nxt = self._entry_cells.get((i, j + 1))
        else:
            nxt = self._entry_cells.get((i, "b"))

        if nxt:
            nxt.focus_set()
            nxt.select_range(0, "end")

    # ─────────────────────── Acciones de botones ─────────────────────────────

    def _select_size(self, n: int):
        self.current_n = n
        for _n, btn in self._size_buttons.items():
            btn.configure(fg_color=P1 if _n == n else "transparent")
        self._generate_grid(n)
        self._reset_results()

    def _read_matrix(self):
        """Lee y valida el grid. Devuelve (A, b) o None si hay error."""
        n = self.current_n
        A, b = [], []
        for i in range(n):
            row = []
            for j in range(n):
                raw = self._entry_cells[(i, j)].get().strip()
                try:
                    row.append(float(raw))
                except ValueError:
                    return None
            A.append(row)
            try:
                b.append(float(self._entry_cells[(i, "b")].get().strip()))
            except ValueError:
                return None
        return A, b

    def _on_clear(self):
        for ent in self._entry_cells.values():
            ent.delete(0, "end")
        self._reset_results()

    def _on_example(self):
        n4A = [[2, -1, 0, 3], [4, 1, -1, 2], [-2, 3, 2, 0], [0, 2, -1, 1]]
        n4b = [7, 9, 3, 2]
        if self.current_n != 4:
            self._select_size(4)
        for i in range(4):
            for j in range(4):
                e = self._entry_cells[(i, j)]
                e.delete(0, "end")
                e.insert(0, str(n4A[i][j]))
            eb = self._entry_cells[(i, "b")]
            eb.delete(0, "end")
            eb.insert(0, str(n4b[i]))

    def _on_copy_latex(self):
        n = self.current_n
        A_rows, b_rows = [], []
        for i in range(n):
            row = [self._entry_cells[(i, j)].get() or "0" for j in range(n)]
            A_rows.append(" & ".join(row))
            b_rows.append(self._entry_cells[(i, "b")].get() or "0")

        A_lat = "\\begin{pmatrix}\n" + " \\\\\n".join(A_rows) + "\n\\end{pmatrix}"
        b_lat = "\\begin{pmatrix}\n" + " \\\\\n".join(b_rows) + "\n\\end{pmatrix}"
        latex = f"% Modo Matricial\nA = {A_lat}\n\nb = {b_lat}"

        self.clipboard_clear()
        self.clipboard_append(latex)
        self._show_toast("¡LaTeX copiado al portapapeles!")

    def _on_solve(self):
        if self._solving:
            return
        self.input_error_var.set("")
        data = self._read_matrix()
        if data is None:
            self.input_error_var.set("⚠ Completa todas las celdas con valores numéricos.")
            return

        A, b = data
        self._solving = True
        self._solve_btn.configure(state="disabled", text="Calculando…")
        self._show_loader()

        def run():
            try:
                result = lu_solver.solve(A, b)
            except Exception as exc:
                result = {"error": str(exc)}
            self.after(0, lambda: self._on_result(result))

        threading.Thread(target=run, daemon=True).start()

    # ─────────────────────── Renderizado de resultados ───────────────────────

    def _clear_results(self):
        for w in self.results_scroll.winfo_children():
            w.destroy()

    def _reset_results(self):
        self._clear_results()
        self._build_placeholder()

    def _show_loader(self):
        self._clear_results()
        ctk.CTkLabel(
            self.results_scroll,
            text="⏳  Calculando…",
            font=ctk.CTkFont(size=14),
            text_color=MUTED,
        ).grid(row=0, column=0, padx=40, pady=80)

    def _on_result(self, result: dict):
        self._solving = False
        self._solve_btn.configure(state="normal", text="Resolver  →")

        if "error" in result:
            self._clear_results()
            ctk.CTkLabel(
                self.results_scroll,
                text=f"Error: {result['error']}",
                font=ctk.CTkFont(size=12),
                text_color=ERR,
                wraplength=600,
            ).grid(row=0, column=0, padx=20, pady=20)
            return

        self._render_results(result)

    def _render_results(self, result: dict):
        self._clear_results()
        row_idx = 0

        # ── Banner de solución ────────────────────────────────────────────────
        if "x_latex" in result:
            banner = ctk.CTkFrame(
                self.results_scroll,
                fg_color="#0a1f12",
                corner_radius=12,
                border_color="#1a4a28",
                border_width=1,
            )
            banner.grid(row=row_idx, column=0, sticky="ew",
                        padx=16, pady=(16, 8))
            banner.columnconfigure(0, weight=1)
            row_idx += 1

            ctk.CTkLabel(
                banner,
                text="✓  SOLUCIÓN ENCONTRADA",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=OK,
            ).grid(row=0, column=0, pady=(14, 4))

            img = latex_to_image(
                f"x = {result['x_latex']}",
                fg=TXT, fontsize=13,
            )
            if img:
                ctk.CTkLabel(banner, image=img, text="").grid(
                    row=1, column=0, pady=(4, 14))

        # ── Tarjetas de pasos ─────────────────────────────────────────────────
        for step in result.get("steps", []):
            step_type = step.get("type", "system")
            bg_color, accent_color = STEP_COLORS.get(
                step_type, (SURFACE2, P2))

            card = ctk.CTkFrame(
                self.results_scroll,
                fg_color=bg_color,
                corner_radius=10,
                border_color=accent_color,
                border_width=1,
            )
            card.grid(row=row_idx, column=0, sticky="ew",
                      padx=16, pady=4)
            card.columnconfigure(0, weight=1)
            row_idx += 1

            # Título (texto plano con posible $ … $ inline)
            title_raw = re.sub(r"\$[^$]*\$", "", step.get("title", "")).strip()
            if not title_raw:
                title_raw = step.get("title", "")
            ctk.CTkLabel(
                card,
                text=title_raw,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=accent_color,
                anchor="w",
                wraplength=700,
            ).grid(row=0, column=0, sticky="w", padx=14, pady=(10, 4))

            # LaTeX principal
            if step.get("latex"):
                img = latex_to_image(step["latex"], fontsize=10)
                if img:
                    ctk.CTkLabel(card, image=img, text="").grid(
                        row=1, column=0, padx=14, pady=(0, 8))

            # Matrices L, U, P (cuando show_matrices)
            if step.get("show_matrices"):
                mat_row_frame = ctk.CTkFrame(card, fg_color="transparent")
                mat_row_frame.grid(row=2, column=0, pady=(0, 10))
                col = 0
                for key, label in [
                    ("L_latex", "L"), ("U_latex", "U"), ("P_latex", "P")
                ]:
                    if step.get(key):
                        blk = ctk.CTkFrame(
                            mat_row_frame, fg_color="transparent")
                        blk.grid(row=0, column=col, padx=12)
                        col += 1
                        ctk.CTkLabel(
                            blk,
                            text=label,
                            font=ctk.CTkFont(size=9, weight="bold"),
                            text_color=MUTED,
                        ).pack()
                        img = latex_to_image(
                            step[key], fontsize=9, max_width_px=520)
                        if img:
                            ctk.CTkLabel(blk, image=img, text="").pack()

        # Nota de fin
        ctk.CTkLabel(
            self.results_scroll,
            text="— Fin del proceso —",
            font=ctk.CTkFont(size=10),
            text_color=MUTED,
        ).grid(row=row_idx, column=0, pady=20)

    # ─────────────────────── Toast ────────────────────────────────────────────

    def _show_toast(self, msg: str):
        toast = ctk.CTkLabel(
            self,
            text=msg,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#1a1a3a",
            corner_radius=10,
            text_color=TXT,
            padx=20, pady=10,
        )
        toast.place(relx=0.5, rely=0.95, anchor="center")
        self.after(2000, toast.destroy)


# ─────────────────────────── Entry point ─────────────────────────────────────

if __name__ == "__main__":
    app = App()
    app.mainloop()
