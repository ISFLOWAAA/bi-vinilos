"""Arma el informe final en PDF a partir de los documentos del repositorio.

Uso (con la base levantada y el ETL corrido):
    python docs/informe/construir_pdf.py

Une los documentos .md en orden, agrega la portada, los resultados de las consultas (leidos de la
base) y las capturas de docs/capturas/, y genera con Chrome el PDF de entrega.
Si se cambia un documento o un tablero, basta volver a correrlo.
"""
import html
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import markdown
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(RAIZ / "etl"))
import config  # noqa: E402

CARPETA = Path(__file__).resolve().parent
SALIDA = CARPETA / "BI_ProyectoFinal_Asprilla_Grisales.pdf"
TEMPORAL = CARPETA / "_informe.html"
CAPTURAS = RAIZ / "docs" / "capturas"
REPO_URL = "https://github.com/ISFLOWAAA/bi-vinilos"
INTEGRANTES = ["Andrés Felipe Asprilla Pedroza", "Jorge Andrés Grisales"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

CSS = """
@page { size: A4; margin: 18mm 16mm 18mm 16mm; }
* { box-sizing: border-box; }
body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 10pt; line-height: 1.45; color: #0F172A; counter-reset: cap; }
h1 { font-size: 20pt; color: #0F766E; border-bottom: 2px solid #0F766E; padding-bottom: 6px; margin: 0 0 14px; break-before: page; }
h1.cap { counter-reset: sec; }
h1.cap::before { counter-increment: cap; content: counter(cap) ". "; }
h2.n::before { counter-increment: sec; content: counter(cap) "." counter(sec) "  "; color: #0F766E; }
h1.sin-salto { break-before: auto; }
h2 { font-size: 13.5pt; color: #0F172A; margin: 20px 0 6px; break-after: avoid; }
h3 { font-size: 11pt; color: #334155; margin: 14px 0 4px; break-after: avoid; }
p, li { orphans: 3; widows: 3; }
a, a:visited { color: #0F766E; text-decoration: none; }
table { border-collapse: collapse; width: 100%; margin: 8px 0 12px; font-size: 8.3pt; table-layout: auto; }
th { background: #F1F5F9; color: #334155; text-align: left; font-weight: 600; }
th, td { border: 1px solid #E2E8F0; padding: 3.5px 6px; vertical-align: top; overflow-wrap: break-word; }
tr { break-inside: avoid; }
code { font-family: Consolas, 'Courier New', monospace; font-size: 8.6pt; background: #F1F5F9; padding: 0 3px; border-radius: 3px; }
pre { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 8px 10px; overflow: hidden; break-inside: avoid; white-space: pre-wrap; }
pre code { background: none; padding: 0; font-size: 8pt; }
pre.mermaid { background: #FFFFFF; text-align: center; white-space: normal; }
img { max-width: 100%; }
figure { margin: 10px 0 14px; break-inside: avoid; text-align: center; }
figure img { border: 1px solid #E2E8F0; border-radius: 6px; }
figcaption { font-size: 8.5pt; color: #64748B; margin-top: 4px; }
.pendiente { border: 2px dashed #D97706; background: #FFFBEB; color: #92400E; padding: 14px; border-radius: 8px; text-align: center; margin: 10px 0; }
.portada { height: 255mm; display: flex; flex-direction: column; justify-content: center; page-break-after: always; }
.portada .etiqueta { color: #0F766E; font-weight: 600; letter-spacing: 2px; font-size: 11pt; }
.portada h1 { font-size: 30pt; border: none; line-height: 1.15; margin: 10px 0 8px; break-before: auto; color: #0F172A; }
.portada .sub { font-size: 14pt; color: #475569; margin-bottom: 40px; }
.portada .bloque { margin: 14px 0; }
.portada .bloque b { display: block; color: #64748B; font-weight: 600; font-size: 9pt; letter-spacing: 1px; text-transform: uppercase; }
.portada .bloque span { font-size: 13pt; }
.indice { page-break-after: always; }
.indice h1 { break-before: auto; }
.indice ol { line-height: 1.9; font-size: 11pt; }
"""

# (archivo, clase de encabezado) en el orden del informe
CAPITULOS = [
    "docs/resumen_ejecutivo.md",
    "docs/catalogo_indicadores.md",
    "docs/diagnostico/diagnostico_fuente.md",
    "docs/modelo_dimensional.md",
    "docs/diccionario_datos.md",
    "etl/README.md",
    "docs/validacion_etl.md",
    "docs/base_de_datos.md",
    "powerbi/README.md",
    "grafana/README.md",
    "simulacion/README.md",
    "docs/arquitectura.md",
    "docs/comparativo_power_bi_grafana.md",
    "docs/evolucion_plc_scada.md",
    "docs/seguridad_datos_personales.md",
]


def separar_listas(texto: str) -> str:
    """Inserta la linea en blanco que python-markdown exige antes de una lista (GitHub no la exige)."""
    salida, previa = [], ""
    es_item = re.compile(r"^\s*([-*+]|\d+\.)\s+")
    for linea in texto.splitlines():
        if es_item.match(linea) and previa.strip() and not es_item.match(previa) and not previa.lstrip().startswith(("|", ">", "```")):
            salida.append("")
        salida.append(linea)
        previa = linea
    return "\n".join(salida)


def md_a_html(ruta: Path) -> str:
    texto = separar_listas(ruta.read_text(encoding="utf-8"))
    cuerpo = markdown.markdown(texto, extensions=["tables", "fenced_code", "sane_lists"])
    # bloques mermaid -> el navegador los dibuja
    cuerpo = re.sub(r'<pre><code class="language-mermaid">(.*?)</code></pre>',
                    lambda m: f'<pre class="mermaid">{html.unescape(m.group(1))}</pre>', cuerpo, flags=re.S)

    def imagen(m):  # rutas relativas -> rutas absolutas para el PDF
        src = m.group(2)
        if not re.match(r"^(https?:|data:|file:)", src):
            src = (ruta.parent / src).resolve().as_uri()
        return f'{m.group(1)}{src}{m.group(3)}'
    cuerpo = re.sub(r'(<img[^>]*src=")([^"]+)(")', imagen, cuerpo)
    # enlaces a archivos del repositorio: se dejan como texto (en papel no se pueden abrir)
    cuerpo = re.sub(r'<a href="(?!https?:)[^"]*">(.*?)</a>', r"<span>\1</span>", cuerpo, flags=re.S)
    cuerpo = re.sub(r"<(h[23])>\s*\d+\.\s+", r"<\1>", cuerpo)         # la numeracion la pone el CSS
    cuerpo = cuerpo.replace("<h2>", '<h2 class="n">')
    cuerpo = re.sub(r"<code>(.*?)</code>", lambda m: "<code>" + m.group(1).replace("_", "_<wbr>") + "</code>", cuerpo, flags=re.S)
    cuerpo = cuerpo.replace("<h1>", '<h1 class="cap">', 1)
    return cuerpo


def tabla(columnas, filas, formatos=None):
    formatos = formatos or {}
    cab = "".join(f"<th>{html.escape(c)}</th>" for c in columnas)
    cuerpo = ""
    for f in filas:
        cuerpo += "<tr>" + "".join(
            f"<td>{html.escape(formatos.get(c, str)(v))}</td>" for c, v in zip(columnas, f)) + "</tr>"
    return f"<table><thead><tr>{cab}</tr></thead><tbody>{cuerpo}</tbody></table>"


def resultados_consultas() -> str:
    """Resultados reales de las consultas analiticas, leidos de la base."""
    consultas = {
        "Q1 · Pareto de causas de paro (10 primeras)": ("""
            SELECT p.codigo_paro, p.nombre_codigo, round(sum(f.horas_paro)::numeric, 0),
                   round(100 * sum(f.horas_paro) / sum(sum(f.horas_paro)) OVER (), 1),
                   round(100 * sum(sum(f.horas_paro)) OVER (ORDER BY sum(f.horas_paro) DESC) / sum(sum(f.horas_paro)) OVER (), 1)
            FROM dw.fact_paro f JOIN dw.dim_paro p USING (paro_key)
            GROUP BY p.codigo_paro, p.nombre_codigo ORDER BY 3 DESC LIMIT 10""",
            ["Código", "Causa", "Horas", "% del paro", "% acumulado"]),
        "Q2 · OEE y sus componentes por año (promedio de los meses de las 4 líneas)": ("""
            SELECT anio, round(100*avg(disponibilidad),1), round(100*avg(rendimiento),1), round(100*avg(calidad),1), round(100*avg(oee),1)
            FROM dw.v_oee_mensual GROUP BY 1 ORDER BY 1""",
            ["Año", "Disponibilidad %", "Rendimiento %", "Calidad (proxy) %", "OEE %"]),
        "Q4 · OEE promedio por máquina y año": ("""
            SELECT maquina, round(100*avg(oee) FILTER (WHERE anio=2022),1), round(100*avg(oee) FILTER (WHERE anio=2023),1),
                   round(100*avg(oee) FILTER (WHERE anio=2024),1), round(100*avg(oee) FILTER (WHERE anio=2025),1),
                   round(100*avg(oee),1)
            FROM dw.v_oee_mensual GROUP BY 1 ORDER BY 1""",
            ["Máquina", "2022", "2023", "2024", "2025 (hasta marzo)", "Todo el periodo"]),
        "Q6 · Fallas electromecánicas (código 01): MTTR y MTBF por máquina y año": ("""
            WITH f AS (SELECT fp.maquina_key, d.anio, sum(fp.horas_paro) h, count(*) n FROM dw.fact_paro fp
                       JOIN dw.dim_paro p USING (paro_key) JOIN dw.dim_fecha d USING (fecha_key) WHERE p.codigo_paro=1 GROUP BY 1,2),
                 hp AS (SELECT maquina_key, d.anio, sum(horas_programadas) hp FROM dw.fact_produccion fp JOIN dw.dim_fecha d USING (fecha_key) GROUP BY 1,2),
                 pa AS (SELECT maquina_key, d.anio, sum(horas_paro) pa FROM dw.fact_paro fp JOIN dw.dim_fecha d USING (fecha_key) GROUP BY 1,2)
            SELECT m.nombre, f.anio, f.n, round((f.h/f.n)::numeric,2), round(((hp.hp - coalesce(pa.pa,0))/f.n)::numeric,1)
            FROM f JOIN hp USING (maquina_key, anio) LEFT JOIN pa USING (maquina_key, anio) JOIN dw.dim_maquina m USING (maquina_key)
            ORDER BY 1,2""",
            ["Máquina", "Año", "Fallas", "MTTR (h)", "MTBF (h)"]),
    }
    salida = ["<h2>Resultados de las consultas (leídos de la base cargada)</h2>",
              "<p>Resultados reales de las consultas de <code>sql/consultas/consultas_analiticas.sql</code>, "
              "generados al construir este documento.</p>"]
    with config.conectar() as conn, conn.cursor() as cur:
        for titulo, (sql, cols) in consultas.items():
            cur.execute(sql)
            salida.append(f"<h3>{html.escape(titulo)}</h3>" + tabla(cols, cur.fetchall()))
    return "\n".join(salida)


def figura(archivo, pie, pendiente=None):
    ruta = CAPTURAS / archivo
    if ruta.exists():
        return f'<figure><img src="{ruta.as_uri()}"><figcaption>{html.escape(pie)}</figcaption></figure>'
    return f'<div class="pendiente"><b>Captura pendiente:</b> {html.escape(pendiente or pie)}<br>Guardar como <code>docs/capturas/{archivo}</code> y volver a construir el informe.</div>'


def capturas_powerbi() -> str:
    return ("<h2>Capturas del tablero</h2>"
            + figura("powerbi_1_resumen.png", "Página 1 · Resumen ejecutivo: OEE, disponibilidad, rendimiento y calidad por máquina.", "Power BI, página Resumen ejecutivo")
            + figura("powerbi_2_paros.png", "Página 2 · Paros y causas: Pareto y drill-down por la jerarquía de paros.", "Power BI, página Paros y causas")
            + figura("powerbi_3_comparativo.png", "Página 3 · Comparativo anual: OEE y pacas contra el mismo mes del año anterior.", "Power BI, página Comparativo anual"))


def capturas_grafana() -> str:
    return ("<h2>Capturas del tablero</h2>"
            + figura("grafana_normal.png", "Estado normal: las cuatro líneas produciendo, sin alertas.")
            + figura("grafana_alerta.png", "Falla provocada en Vinilos_2: la máquina pasa a PARADA y la alerta «Paro prolongado en máquina» está en Firing."))


def repositorio() -> str:
    readme = (RAIZ / "README.md").read_text(encoding="utf-8")
    m = re.search(r"## Estructura del repositorio.*?(?=## Tecnolog)", readme, flags=re.S)
    cuerpo = markdown.markdown(m.group(0) if m else "", extensions=["tables", "fenced_code", "sane_lists"])
    cuerpo = re.sub(r'<a href="(?!https?:)[^"]*">(.*?)</a>', r"<span>\1</span>", cuerpo, flags=re.S)
    log = subprocess.run(["git", "-C", str(RAIZ), "shortlog", "-sne", "HEAD"], capture_output=True, text=True).stdout.strip()
    filas = [re.match(r"\s*(\d+)\s+(.*?)\s+<", l) for l in log.splitlines()]
    autores = tabla(["Autor", "Commits"], [(f.group(2), f.group(1)) for f in filas if f])
    total = subprocess.run(["git", "-C", str(RAIZ), "rev-list", "--count", "HEAD"], capture_output=True, text=True).stdout.strip()
    return (f'<h1 class="cap">Repositorio y reproducción</h1>'
            f'<p>Código, scripts SQL, ETL, tablero de Grafana, proyecto de Power BI y documentación están versionados en GitHub: '
            f'<a href="{REPO_URL}">{REPO_URL}</a> (repositorio privado).</p>'
            f'<p><b>Formato de Power BI: PBIP</b> (proyecto en carpetas de texto) en lugar de <code>.pbix</code>, porque Git puede mostrar qué cambió '
            f'entre versiones y dos personas pueden trabajar sin pisarse; un <code>.pbix</code> es un binario que no se puede comparar ni fusionar.</p>'
            f'<p>No hay contraseñas ni cadenas de conexión con credenciales en el repositorio: el <code>.env</code> está excluido y se versiona '
            f'solo <code>.env.example</code>.</p>{cuerpo}'
            f'<h2>Historial de commits</h2><p>{total} commits en la rama <code>main</code>, por autor:</p>{autores}')


def portada() -> str:
    hoy = date.today()
    return (f'<div class="portada"><div class="etiqueta">INTELIGENCIA DE NEGOCIOS · PROYECTO FINAL</div>'
            f'<h1>BI Vinilos y Témperas</h1><div class="sub">Producción y paros de las líneas de envasado: de un Excel a un modelo dimensional, '
            f'un tablero analítico en Power BI y un tablero operativo con alertas en Grafana</div>'
            f'<div class="bloque"><b>Integrantes</b>' + "".join(f"<span>{n}</span><br>" for n in INTEGRANTES) + '</div>'
            f'<div class="bloque"><b>Repositorio</b><span>{REPO_URL}</span></div>'
            f'<div class="bloque"><b>Fecha</b><span>{hoy.day} de {MESES[hoy.month - 1]} de {hoy.year}</span></div></div>')


def indice(titulos) -> str:
    items = "".join(f"<li>{html.escape(t)}</li>" for t in titulos)
    return f'<div class="indice"><h1 class="sin-salto">Contenido</h1><ol>{items}</ol></div>'


def construir() -> None:
    secciones, titulos = [], []
    for rel in CAPITULOS:
        cuerpo = md_a_html(RAIZ / rel)
        titulos.append(re.search(r"<h1[^>]*>(.*?)</h1>", cuerpo, flags=re.S).group(1))
        if rel == "docs/base_de_datos.md":
            cuerpo += resultados_consultas()
        elif rel == "powerbi/README.md":
            cuerpo += capturas_powerbi()
        elif rel == "grafana/README.md":
            cuerpo += capturas_grafana()
        secciones.append(cuerpo)
    titulos.append("Repositorio y reproducción")
    pagina = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>BI Vinilos y Témperas</title>'
              f'<style>{CSS}</style></head><body>{portada()}{indice(titulos)}{"".join(secciones)}{repositorio()}'
              f'<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>'
              f'<script>mermaid.initialize({{startOnLoad: true, theme: "neutral", er: {{useMaxWidth: true}}}});</script></body></html>')
    TEMPORAL.write_text(pagina, encoding="utf-8")

    with sync_playwright() as p:
        navegador = p.chromium.launch(channel="chrome", headless=True)
        pag = navegador.new_page()
        pag.goto(TEMPORAL.as_uri())
        pag.wait_for_load_state("networkidle")
        pag.wait_for_function("document.querySelectorAll('pre.mermaid').length === document.querySelectorAll('pre.mermaid svg').length", timeout=60000)
        pag.pdf(path=str(SALIDA), format="A4", print_background=True, display_header_footer=True,
                margin={"top": "18mm", "bottom": "18mm", "left": "16mm", "right": "16mm"},
                header_template="<span></span>",
                footer_template='<div style="font-size:8px;color:#64748B;width:100%;text-align:center;font-family:Segoe UI,Arial">'
                                'BI Vinilos y Témperas · <span class="pageNumber"></span> / <span class="totalPages"></span></div>')
        navegador.close()
    TEMPORAL.unlink(missing_ok=True)
    print("PDF generado:", SALIDA, f"({SALIDA.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    construir()
