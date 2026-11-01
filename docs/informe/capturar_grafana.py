"""Toma las capturas del tablero de Grafana para el informe.

Uso (con Docker arriba y la simulacion corriendo):
    python docs/informe/capturar_grafana.py

Genera en docs/capturas/:
    grafana_normal.png   todas las maquinas produciendo
    grafana_alerta.png   Vinilos_2 con falla provocada y la alerta disparada
Usa el Chrome instalado en el equipo (no descarga ningun navegador).
"""
import subprocess
import sys
import time
from pathlib import Path

from dotenv import dotenv_values
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parent.parent.parent
CAPTURAS = RAIZ / "docs" / "capturas"
ENV = dotenv_values(RAIZ / ".env")
BASE = f"http://localhost:{ENV['GRAFANA_PORT']}"
TABLERO = f"{BASE}/d/monitoreo-lineas/monitoreo?orgId=1&kiosk&theme=light&from=now-15m&to=now&refresh=5s"
PYTHON = RAIZ / ".venv" / "Scripts" / "python.exe"


def simulador(*args):
    subprocess.run([str(PYTHON), str(RAIZ / "simulacion" / "simular.py"), *args], check=True, capture_output=True)


def capturar(pagina, archivo, espera=8):
    pagina.goto(TABLERO)
    pagina.wait_for_load_state("networkidle")
    time.sleep(espera)   # deja que se pinten los paneles
    pagina.screenshot(path=str(CAPTURAS / archivo))
    print("capturado", archivo)


def main() -> int:
    CAPTURAS.mkdir(exist_ok=True)
    simulador("--normalizar")
    with sync_playwright() as p:
        navegador = p.chromium.launch(channel="chrome", headless=True)
        pagina = navegador.new_context(viewport={"width": 1600, "height": 1000}, device_scale_factor=1.5).new_page()
        pagina.goto(f"{BASE}/login")
        pagina.fill("input[name='user']", ENV["GF_SECURITY_ADMIN_USER"])
        pagina.fill("input[name='password']", ENV["GF_SECURITY_ADMIN_PASSWORD"])
        pagina.click("button[type='submit']")
        pagina.wait_for_load_state("networkidle")

        capturar(pagina, "grafana_normal.png")

        simulador("--provocar", "Vinilos_2")
        print("falla provocada en Vinilos_2; esperando a que la alerta se dispare...")
        time.sleep(55)
        capturar(pagina, "grafana_alerta.png")
        simulador("--normalizar")
        navegador.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
