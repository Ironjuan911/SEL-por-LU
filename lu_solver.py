"""
lu_solver.py
Descomposición LU con pivoteo parcial (Doolittle).
Genera pasos intermedios con cadenas LaTeX para renderizado en la interfaz.
"""

import numpy as np
from fractions import Fraction


# ─────────────────────────── Formateo numérico ──────────────────────────────

def fmt(val, tol=1e-9):
    """Convierte un número a cadena LaTeX legible (fracción o decimal)."""
    if np.isnan(val):
        return r"\text{\_}"
    v = float(val)
    if abs(v) < tol:
        return "0"
    if abs(v - round(v)) < tol:
        return str(int(round(v)))
    try:
        f = Fraction(v).limit_denominator(1000)
        if abs(float(f) - v) < tol * 100:
            n, d = f.numerator, f.denominator
            if d == 1:
                return str(n)
            sign = "-" if n < 0 else ""
            return f"{sign}\\frac{{{abs(n)}}}{{{d}}}"
    except Exception:
        pass
    return f"{v:.5g}"


def mat_to_latex(M):
    """Convierte una matriz 2D (array o lista) a bmatrix LaTeX."""
    rows = []
    for row in M:
        rows.append(" & ".join(fmt(v) for v in row))
    body = r" \\ ".join(rows)
    return r"\begin{bmatrix}" + body + r"\end{bmatrix}"


def vec_to_latex(v):
    """Convierte un vector 1D a bmatrix columna LaTeX."""
    body = r" \\ ".join(fmt(x) for x in v)
    return r"\begin{bmatrix}" + body + r"\end{bmatrix}"


# ──────────────────────────── Algoritmo principal ───────────────────────────

def solve(A_input, b_input):
    """
    Resuelve Ax = b por descomposición LU con pivoteo parcial (PA = LU).
    Retorna un dict con:
      - 'steps': lista de pasos con título y LaTeX para la interfaz
      - 'x': solución como lista de floats
      - 'x_latex', 'L_latex', 'U_latex', 'P_latex': cadenas LaTeX finales
    """
    n = len(A_input)
    A = np.array(A_input, dtype=float)
    b = np.array(b_input, dtype=float)
    steps = []

    # ── Paso 0: Sistema original ─────────────────────────────────────────────
    steps.append({
        "type": "system",
        "phase": 0,
        "title": "Sistema original $Ax = b$",
        "latex": f"A = {mat_to_latex(A)}, \\qquad b = {vec_to_latex(b)}",
    })

    # ── Fase 1: Descomposición PA = LU ───────────────────────────────────────
    steps.append({
        "type": "phase_header",
        "phase": 1,
        "title": "Fase 1 — Descomposición $PA = LU$",
        "latex": (
            r"\text{Se buscan matrices } P, L, U \text{ tales que } PA = LU, "
            r"\text{ donde } L \text{ es triangular inferior con diagonal 1 y } "
            r"U \text{ es triangular superior.}"
        ),
    })

    L = np.eye(n)
    # Llenar la parte inferior de L (excluyendo diagonal) con NaN (faltantes)
    for r in range(1, n):
        for c in range(r):
            L[r, c] = np.nan
            
    U = np.full((n, n), np.nan)
    # Llenar la parte inferior de U con 0 (por definición)
    for r in range(1, n):
        for c in range(r):
            U[r, c] = 0.0
            
    P = np.eye(n)
    # Copia de A permutada (se actualizará durante el proceso si hay pivoteo)
    PA = A.copy()

    for i in range(n):
        # — Pivoteo parcial para la fila i —
        # Debemos encontrar el mejor pivote para U[i,i] considerando los elementos restantes de A
        # pero tomando en cuenta las eliminaciones ya hechas.
        # En el método directo con pivoteo, es más sencillo pivotar la matriz original A
        # o llevar un registro. Para mantener la claridad de "ecuaciones", simplemente
        # buscaremos el valor máximo en la columna i de la matriz PA (considerando lo ya calculado).
        
        max_idx = i + np.argmax(np.abs(PA[i:, i]))
        if max_idx != i:
            PA[[i, max_idx]] = PA[[max_idx, i]]
            P[[i, max_idx]] = P[[max_idx, i]]
            # Si ya calculamos parte de L, también debemos permutar sus filas (excepto la diagonal)
            if i > 0:
                L[[i, max_idx], :i] = L[[max_idx, i], :i]
            
            steps.append({
                "type": "pivot",
                "phase": 1,
                "title": f"Pivoteo — Intercambio de filas $R_{{{i+1}}} \\leftrightarrow R_{{{max_idx+1}}}$",
                "latex": f"\\text{{Se intercambian las filas }} {i+1} \\text{{ y }} {max_idx+1} \\text{{ para asegurar un pivote máximo.}}",
                "P_latex": mat_to_latex(P),
            })

        # Cálculo de la fila i de U
        for j in range(i, n):
            suma = sum(L[i, k] * U[k, j] for k in range(i))
            U[i, j] = PA[i, j] - suma
            
            term_suma = " - ".join(f"({fmt(L[i,k])} \\cdot {fmt(U[k,j])})" for k in range(i))
            lat_suma = f" - ({term_suma})" if i > 0 else ""
            steps.append({
                "type": "elimination",
                "phase": 1,
                "title": f"Cálculo de $u_{{{i+1},{j+1}}}$",
                "latex": f"u_{{{i+1},{j+1}}} = a_{{{i+1},{j+1}}}{lat_suma} = {fmt(PA[i,j])} - {fmt(suma)} = {fmt(U[i,j])}",
                "L_latex": mat_to_latex(L),
                "U_latex": mat_to_latex(U),
                "show_matrices": True,
            })

        # Verificar si la matriz es singular
        if abs(U[i, i]) < 1e-12:
            steps.append({
                "type": "error",
                "phase": 1,
                "title": "⚠ Matriz singular detectada",
                "latex": f"u_{{{i+1},{i+1}}} = {fmt(U[i,i])} \\approx 0. \\text{{ No se puede continuar.}}",
            })
            return {"n": n, "steps": steps, "L_latex": mat_to_latex(L), "U_latex": mat_to_latex(U), "P_latex": mat_to_latex(P)}

        # Cálculo de la columna i de L
        for j in range(i + 1, n):
            suma = sum(L[j, k] * U[k, i] for k in range(i))
            L[j, i] = (PA[j, i] - suma) / U[i, i]
            
            term_suma = " - ".join(f"({fmt(L[j,k])} \\cdot {fmt(U[k,i])})" for k in range(i))
            lat_suma = f" - ({term_suma})" if i > 0 else ""
            steps.append({
                "type": "elimination",
                "phase": 1,
                "title": f"Cálculo de $l_{{{j+1},{i+1}}}$",
                "latex": (
                    f"l_{{{j+1},{i+1}}} = \\frac{{a_{{{j+1},{i+1}}}{lat_suma}}}{{u_{{{i+1},{i+1}}}}} = "
                    f"\\frac{{{fmt(PA[j,i])} - {fmt(suma)}}}{{{fmt(U[i,i])}}} = {fmt(L[j,i])}"
                ),
                "L_latex": mat_to_latex(L),
                "U_latex": mat_to_latex(U),
                "show_matrices": True,
            })

    steps.append({
        "type": "lu_result",
        "phase": 1,
        "title": "Factorización $PA = LU$ completada",
        "latex": f"L = {mat_to_latex(L)}, \\quad U = {mat_to_latex(U)}, \\quad P = {mat_to_latex(P)}",
        "L_latex": mat_to_latex(L),
        "U_latex": mat_to_latex(U),
        "P_latex": mat_to_latex(P),
        "show_matrices": True,
    })

    # ── Fase 2: Sustitución hacia adelante Lz = Pb ───────────────────────────
    Pb = P @ b
    z = np.zeros(n)

    steps.append({
        "type": "phase_header",
        "phase": 2,
        "title": "Fase 2 — Sustitución hacia adelante $Lz = Pb$",
        "latex": f"Pb = {vec_to_latex(Pb)}, \\quad L = {mat_to_latex(L)}",
    })

    for i in range(n):
        dot = float(np.dot(L[i, :i], z[:i]))
        z[i] = Pb[i] - dot

        if i == 0:
            lat = f"z_{{{i+1}}} = (Pb)_{{{i+1}}} = {fmt(Pb[i])} = {fmt(z[i])}"
        else:
            terms = " - ".join(f"{fmt(L[i,j])} \\cdot z_{{{j+1}}}" for j in range(i))
            lat = f"z_{{{i+1}}} = B'_{{{i+1}}} - ({terms}) = {fmt(Pb[i])} - {fmt(dot)} = {fmt(z[i])}"

        steps.append({
            "type": "forward_step",
            "phase": 2,
            "title": f"Cálculo de $z_{{{i+1}}}$",
            "latex": lat,
        })

    steps.append({
        "type": "forward_result",
        "phase": 2,
        "title": "Vector $z$ obtenido",
        "latex": f"z = {vec_to_latex(z)}",
    })

    # ── Fase 3: Sustitución hacia atrás Ux = z ───────────────────────────────
    x = np.zeros(n)

    steps.append({
        "type": "phase_header",
        "phase": 3,
        "title": "Fase 3 — Sustitución hacia atrás $Ux = z$",
        "latex": f"z = {vec_to_latex(z)}, \\quad U = {mat_to_latex(U)}",
    })

    for i in range(n - 1, -1, -1):
        dot = float(np.dot(U[i, i + 1:], x[i + 1:]))
        rhs = z[i] - dot
        x[i] = rhs / U[i, i]

        if i == n - 1:
            lat = f"x_{{{i+1}}} = \\frac{{z_{{{i+1}}}}}{{u_{{{i+1},{i+1}}}}} = \\frac{{{fmt(z[i])}}}{{{fmt(U[i,i])}}} = {fmt(x[i])}"
        else:
            non_zero = [(j, U[i, j]) for j in range(i + 1, n) if abs(U[i, j]) > 1e-10]
            if non_zero:
                terms = " - ".join(f"{fmt(uij)} \\cdot x_{{{j+1}}}" for j, uij in non_zero)
                lat = f"x_{{{i+1}}} = \\frac{{z_{{{i+1}}} - ({terms})}}{{u_{{{i+1},{i+1}}}}} = \\frac{{{fmt(rhs)}}}{{{fmt(U[i,i])}}} = {fmt(x[i])}"
            else:
                lat = f"x_{{{i+1}}} = \\frac{{z_{{{i+1}}}}}{{u_{{{i+1},{i+1}}}}} = \\frac{{{fmt(z[i])}}}{{{fmt(U[i,i])}}} = {fmt(x[i])}"

        steps.append({
            "type": "backward_step",
            "phase": 3,
            "title": f"Cálculo de $x_{{{i+1}}}$",
            "latex": lat,
        })

    steps.append({
        "type": "solution",
        "phase": 3,
        "title": "Solución final $x$",
        "latex": f"x = {vec_to_latex(x)}",
        "x_values": x.tolist(),
    })

    return {
        "n": n,
        "steps": steps,
        "x": x.tolist(),
        "x_latex": vec_to_latex(x),
        "L_latex": mat_to_latex(L),
        "U_latex": mat_to_latex(U),
        "P_latex": mat_to_latex(P),
    }


# ──────────────────────────── Tests básicos ─────────────────────────────────

if __name__ == "__main__":
    import numpy.linalg as la

    print("=== TEST 3×3 (solución esperada: x = [2, 3, -1]) ===")
    A3 = [[2, 1, -1], [-3, -1, 2], [-2, 1, 2]]
    b3 = [8, -11, -3]
    r3 = solve(A3, b3)
    print("Obtenido: ", [round(v, 6) for v in r3["x"]])
    print("NumPy:    ", la.solve(np.array(A3, float), np.array(b3, float)).tolist())

    print("\n=== TEST 4×4 ===")
    A4 = [[2, -1, 0, 3], [4, 1, -1, 2], [-2, 3, 2, 0], [0, 2, -1, 1]]
    b4 = [7, 9, 3, 2]
    r4 = solve(A4, b4)
    ref4 = la.solve(np.array(A4, float), np.array(b4, float))
    print("Obtenido: ", [round(v, 6) for v in r4["x"]])
    print("NumPy:    ", ref4.tolist())
    print("Pasos 4x4:", len(r4["steps"]))

    print("\n=== TEST MATRIZ SINGULAR (Usuario) ===")
    A_sing = [[1, -1, 1, 1], [2, 1, -3, 1], [1, -2, 2, -1], [1, -3, 3, -3]]
    b_sing = [4, 4, 3, 2]
    r_sing = solve(A_sing, b_sing)
    if r_sing["steps"][-1]["type"] == "error":
        print("Detectado correctamente (paso de error encontrado)")
        print("Mensaje:", r_sing["steps"][-1]["title"])
        print("Pasos generados:", len(r_sing["steps"]))
    else:
        print("ERROR: No detectó la matriz singular")
