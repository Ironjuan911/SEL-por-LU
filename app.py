"""
app.py  –  Resolución de SEL por Descomposición LU
Ventana nativa PyQt6 con Chromium embebido (QWebEngineView).
Ejecutar: python app.py
"""

import sys
import json
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineScript, QWebEngineSettings
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import QObject, pyqtSlot, QFile, QIODevice, QUrl

import lu_solver


# ──────────────────────── Bridge Python ↔ JS ────────────────────────────────

class Bridge(QObject):
    """Objeto expuesto al JS a través de QWebChannel."""

    @pyqtSlot(str, result=str)
    def solve(self, data_json: str) -> str:
        """
        Recibe un JSON con {"A": [...], "b": [...]} desde JS.
        Devuelve el resultado del solucionador LU como JSON string.
        """
        try:
            data = json.loads(data_json)
            result = lu_solver.solve(data["A"], data["b"])
            return json.dumps(result, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"error": str(exc)}, ensure_ascii=False)


# ──────────────────── Cargar qwebchannel.js desde Qt ────────────────────────

def _load_qwc_js() -> str:
    """Lee el archivo qwebchannel.js embebido en Qt (recursos de Qt)."""
    path = ":/qtwebchannel/qwebchannel.js"
    f = QFile(path)
    if f.open(QIODevice.OpenModeFlag.ReadOnly):
        content = bytes(f.readAll()).decode("utf-8")
        f.close()
        return content
    return "console.error('[Bridge] qwebchannel.js no encontrado en recursos Qt.');"


# ────────────────────────────── MainWindow ───────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Resolución de SEL — Descomposición LU")
        self.resize(1400, 860)

        self.view = QWebEngineView()

        # ── Permisos de la página ──
        settings = self.view.page().settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)

        # ── Inyectar qwebchannel.js ANTES de que cargue el documento ──
        qwc_script = QWebEngineScript()
        qwc_script.setName("qwebchannel_init")
        qwc_script.setSourceCode(_load_qwc_js())
        qwc_script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        qwc_script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        self.view.page().scripts().insert(qwc_script)

        # ── Configurar QWebChannel y registrar el Bridge ──
        self.channel = QWebChannel()
        self.bridge = Bridge()
        self.channel.registerObject("bridge", self.bridge)
        self.view.page().setWebChannel(self.channel)

        # ── Cargar index.html desde la carpeta web/ ──
        web_dir = Path(__file__).parent / "web"
        index_url = QUrl.fromLocalFile(str(web_dir / "index.html"))
        self.view.load(index_url)

        self.setCentralWidget(self.view)
        self.show()


# ─────────────────────────────── Entry point ─────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    sys.exit(app.exec())
