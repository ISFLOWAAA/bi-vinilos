"""Arma el informe RESUMIDO en Word (.docx) y lo exporta a PDF con Microsoft Word.

Uso (con la base levantada, para los resultados de las consultas):
    python docs/informe/construir_docx.py

Solo incluye lo que pide la rubrica del proyecto. El contenido sale de los documentos del repositorio
(docs/, etl/, powerbi/, grafana/, simulacion/); las capturas de docs/capturas/ y las figuras de
docs/informe/figuras/. Genera el .docx y, si hay Word instalado, actualiza el contenido y exporta el PDF.
"""
import re
import subprocess
import sys
import unicodedata
from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

RAIZ = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(RAIZ / "etl"))
CARPETA = Path(__file__).resolve().parent
FIGURAS = CARPETA / "figuras"
CAPTURAS = RAIZ / "docs" / "capturas"
SALIDA_DOCX = CARPETA / "BI_ProyectoFinal_Asprilla_Grisales.docx"   # informe OFICIAL (su PDF sale con el mismo nombre)
REPO_URL = "https://github.com/ISFLOWAAA/bi-vinilos"
INTEGRANTES = ["Andrés Felipe Asprilla Pedroza", "Jorge Andrés Grisales"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

TEAL, OSCURO, GRIS, CLARO = RGBColor(0x0F, 0x76, 0x6E), RGBColor(0x0F, 0x17, 0x2A), RGBColor(0x64, 0x74, 0x8B), "E6F4F1"
FUENTE = "Calibri"

# =========================================================================== lectura de markdown
INLINE = re.compile(r"(\*\*.+?\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\)|(?<!\*)\*[^*\s][^*]*?\*(?!\*))")


def sin_tildes(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c)).lower()


def limpiar_titulo(t: str) -> str:
    t = re.sub(r"`", "", t).strip()
    return re.sub(r"^\d+(\.\d+)*\.?\s+", "", t)


def parsear(texto: str) -> list[dict]:
    """Convierte markdown en bloques: heading, para, bullet, num, table, code, img."""
    bloques, lineas, i = [], texto.splitlines(), 0
    while i < len(lineas):
        l = lineas[i]
        if l.strip().startswith("```"):
            i += 1
            cod = []
            while i < len(lineas) and not lineas[i].strip().startswith("```"):
                cod.append(lineas[i]); i += 1
            bloques.append({"t": "code", "x": "\n".join(cod)}); i += 1; continue
        if l.strip().startswith("|"):
            filas = []
            while i < len(lineas) and lineas[i].strip().startswith("|"):
                celdas = [c.strip() for c in lineas[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-+:?", c) for c in celdas):
                    filas.append(celdas)
                i += 1
            bloques.append({"t": "table", "rows": filas}); continue
        m = re.match(r"^(#{1,6})\s+(.*)", l)
        if m:
            bloques.append({"t": "heading", "n": len(m.group(1)), "x": limpiar_titulo(m.group(2))}); i += 1; continue
        m = re.match(r"^!\[(.*?)\]\((.*?)\)\s*$", l)
        if m:
            bloques.append({"t": "img", "alt": m.group(1), "src": m.group(2)}); i += 1; continue
        m = re.match(r"^(\s*)([-*+])\s+(.*)", l)
        if m:
            bloques.append({"t": "bullet", "x": m.group(3), "nivel": len(m.group(1)) // 2}); i += 1; continue
        m = re.match(r"^\s*\d+\.\s+(.*)", l)
        if m:
            bloques.append({"t": "num", "x": m.group(1)}); i += 1; continue
        if not l.strip():
            i += 1; continue
        par = [l.strip()]
        i += 1
        while i < len(lineas) and lineas[i].strip() and not re.match(r"^(#{1,6}\s|\||\s*[-*+]\s|\s*\d+\.\s|```|!\[)", lineas[i]):
            par.append(lineas[i].strip()); i += 1
        bloques.append({"t": "para", "x": " ".join(par)})
    return bloques


def secciones(ruta: Path, titulos: list[str], intro: bool = False) -> list[dict]:
    """Devuelve los bloques de las secciones H2 con esos titulos (en ese orden); intro = texto antes del primer H2."""
    bl = parsear(ruta.read_text(encoding="utf-8"))
    partes, actual = {}, None
    previo = []
    for b in bl:
        if b["t"] == "heading" and b["n"] == 1:
            continue
        if b["t"] == "heading" and b["n"] == 2:
            actual = b["x"]; partes[actual] = []; continue
        (partes[actual] if actual else previo).append(b)
    salida = list(previo) if intro else []
    for t in titulos:
        clave = next((k for k in partes if sin_tildes(k).startswith(sin_tildes(t))), None)
        if clave is None:
            raise SystemExit(f"No encontre la seccion '{t}' en {ruta.name}. Hay: {list(partes)}")
        salida.append({"t": "heading", "n": 2, "x": clave})
        salida += partes[clave]
    return salida


# ============================================================================== escritura de Word
def fuente(run, size=None, bold=None, italic=None, color=None, mono=False):
    run.font.name = "Consolas" if mono else FUENTE
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas" if mono else FUENTE)
    if size: run.font.size = Pt(size)
    if bold is not None: run.font.bold = bold
    if italic is not None: run.font.italic = italic
    if color is not None: run.font.color.rgb = color


def inline(par, texto, size=10, negrita=False, color=None):
    for parte in INLINE.split(texto):
        if not parte:
            continue
        if parte.startswith("**") and parte.endswith("**") and len(parte) > 4:
            inline(par, parte[2:-2], size, True, color)
        elif parte.startswith("`") and parte.endswith("`"):
            fuente(par.add_run(parte[1:-1]), max(size - 1, 7), negrita, color=color or TEAL, mono=True)
        elif parte.startswith("["):
            m = re.match(r"\[([^\]]+)\]\(([^)]+)\)", parte)
            if m: inline(par, m.group(1), size, negrita, color)
            else: fuente(par.add_run(parte), size, negrita, color=color)
        elif parte.startswith("*") and parte.endswith("*") and len(parte) > 2:
            fuente(par.add_run(parte[1:-1]), size, negrita, True, color=color)
        else:
            fuente(par.add_run(parte), size, negrita, color=color)


def sombrear(celda, hex_color):
    pr = celda._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), hex_color)
    pr.append(sh)


def margenes_celda(celda, v=35, h=70):
    pr = celda._tc.get_or_add_tcPr()
    m = OxmlElement("w:tcMar")
    for lado, val in (("top", v), ("left", h), ("bottom", v), ("right", h)):
        e = OxmlElement(f"w:{lado}"); e.set(qn("w:w"), str(val)); e.set(qn("w:type"), "dxa"); m.append(e)
    pr.append(m)


class Informe:
    def __init__(self):
        self.doc = Document()
        self.cap = 0
        self.sec = 0
        self.ancho_cm = 17.0
        self.tam_tabla = None
        self._estilos()
        s = self.doc.sections[0]
        s.page_width, s.page_height = Cm(21), Cm(29.7)
        for lado in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
            setattr(s, lado, Cm(2))
        self._pie(s)

    def _estilos(self):
        st = self.doc.styles
        n = st["Normal"]; n.font.name = FUENTE; n.font.size = Pt(10)
        n.element.rPr.rFonts.set(qn("w:eastAsia"), FUENTE)
        n.paragraph_format.space_after = Pt(4); n.paragraph_format.line_spacing = 1.08
        for nombre, tam, color, antes, desp in (("Heading 1", 17, TEAL, 16, 6), ("Heading 2", 12.5, OSCURO, 10, 3), ("Heading 3", 10.5, GRIS, 8, 2)):
            h = st[nombre]; h.font.name = FUENTE; h.font.size = Pt(tam); h.font.bold = True; h.font.color.rgb = color
            h.element.rPr.rFonts.set(qn("w:eastAsia"), FUENTE); h.element.rPr.rFonts.set(qn("w:ascii"), FUENTE); h.element.rPr.rFonts.set(qn("w:hAnsi"), FUENTE)
            h.paragraph_format.space_before = Pt(antes); h.paragraph_format.space_after = Pt(desp); h.paragraph_format.keep_with_next = True

    def _campo(self, par, instr, texto=""):
        for tipo in ("begin", None, "separate", "texto", "end"):
            r = par.add_run()
            if tipo == "texto":
                r.text = texto; fuente(r, 8, color=GRIS); continue
            if tipo is None:
                e = OxmlElement("w:instrText"); e.set(qn("xml:space"), "preserve"); e.text = instr; r._r.append(e); continue
            f = OxmlElement("w:fldChar"); f.set(qn("w:fldCharType"), tipo); r._r.append(f)

    def _pie(self, seccion):
        p = seccion.footer.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        fuente(p.add_run("BI Vinilos y Témperas  ·  "), 8, color=GRIS)
        self._campo(p, "PAGE", "1")

    def nueva_seccion(self, horizontal: bool):
        s = self.doc.add_section(WD_SECTION.NEW_PAGE)
        if horizontal:
            s.orientation = WD_ORIENT.LANDSCAPE; s.page_width, s.page_height = Cm(29.7), Cm(21); self.ancho_cm = 25.7
        else:
            s.orientation = WD_ORIENT.PORTRAIT; s.page_width, s.page_height = Cm(21), Cm(29.7); self.ancho_cm = 17.0
        return s

    # ---- bloques
    def h1(self, texto, numerar=True):
        if numerar:
            self.cap += 1; self.sec = 0; texto = f"{self.cap}. {texto}"
        self.doc.add_paragraph(texto, style="Heading 1")

    def h2(self, texto, numerar=True):
        if numerar:
            self.sec += 1; texto = f"{self.cap}.{self.sec} {texto}"
        self.doc.add_paragraph(texto, style="Heading 2")

    def h3(self, texto):
        self.doc.add_paragraph(texto, style="Heading 3")

    def parrafo(self, texto, size=10, italica=False, centrado=False, color=None):
        p = self.doc.add_paragraph()
        if centrado: p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if italica:
            fuente(p.add_run(texto), size, False, True, color=color or GRIS)
        else:
            inline(p, texto, size, color=color)
        return p

    def viñeta(self, texto, nivel=0, num=False):
        p = self.doc.add_paragraph(style="List Number" if num else "List Bullet")
        p.paragraph_format.left_indent = Cm(0.63 + 0.6 * nivel); p.paragraph_format.space_after = Pt(2)
        inline(p, texto, 10)

    def codigo(self, texto):
        p = self.doc.add_paragraph(); p.paragraph_format.left_indent = Cm(0.3)
        for k, l in enumerate(texto.splitlines()):
            if k: p.add_run().add_break()
            fuente(p.add_run(l), 7.5, mono=True, color=OSCURO)

    def imagen(self, ruta: Path, pie: str, ancho_cm=None):
        p = self.doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.keep_with_next = True
        p.add_run().add_picture(str(ruta), width=Cm(min(ancho_cm or self.ancho_cm, self.ancho_cm)))
        c = self.parrafo(pie, 8.5, italica=True, centrado=True); c.paragraph_format.space_after = Pt(8)

    def tabla(self, filas, tam=None):
        if not filas: return
        ncol = len(filas[0]); filas = [(f + [""] * ncol)[:ncol] for f in filas]
        tam = tam or self.tam_tabla or (9 if ncol <= 3 else 8.5 if ncol <= 5 else 8 if ncol <= 7 else 7.5)
        pesos = []
        for j in range(ncol):
            largos = [len(re.sub(r"[*`]", "", f[j])) for f in filas]
            pesos.append(max(3.0, min(48.0, 0.55 * max(largos[0], 4) + 0.45 * (sum(largos[1:]) / max(len(largos) - 1, 1)))))
        total = sum(pesos); minimo = 1.3 if ncol > 6 else 1.6
        anchos = [max(minimo, self.ancho_cm * p / total) for p in pesos]
        if ncol <= 4: anchos[0] = max(anchos[0], 2.9)   # la primera columna suele ser una etiqueta: que no parta palabras
        esc = self.ancho_cm / sum(anchos); anchos = [a * esc for a in anchos]
        t = self.doc.add_table(rows=0, cols=ncol); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.autofit = False
        for i, f in enumerate(filas):
            fila = t.add_row()
            trPr = fila._tr.get_or_add_trPr()
            cs = OxmlElement("w:cantSplit"); trPr.append(cs)
            if i == 0:
                th = OxmlElement("w:tblHeader"); trPr.append(th)
            for j, txt in enumerate(f):
                c = fila.cells[j]; c.width = Cm(anchos[j]); margenes_celda(c)
                p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(0); p.paragraph_format.space_before = Pt(0)
                inline(p, txt, tam, negrita=(i == 0))
                if i == 0: sombrear(c, CLARO)
        sp = self.doc.add_paragraph(); sp.paragraph_format.space_after = Pt(0); sp.paragraph_format.line_spacing = 0.5
        fuente(sp.add_run(' '), 3)

    def bloques(self, bl, numerar=True, saltar_img=False):
        for b in bl:
            t = b["t"]
            if t == "heading":
                (self.h2 if b["n"] == 2 else self.h3)(b["x"]) if b["n"] != 2 else self.h2(b["x"], numerar)
            elif t == "para": self.parrafo(b["x"])
            elif t == "bullet": self.viñeta(b["x"], b.get("nivel", 0))
            elif t == "num": self.viñeta(b["x"], num=True)
            elif t == "table": self.tabla(b["rows"])
            elif t == "code": self.codigo(b["x"])
            elif t == "img" and not saltar_img:
                nombre = Path(b["src"]).name.replace(".svg", ".png")
                ruta = FIGURAS / nombre
                if ruta.exists(): self.imagen(ruta, b["alt"])

    def salto(self):
        self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    def guardar(self, ruta):
        self.doc.save(str(ruta))


# ================================================================================ contenido
def md(ruta, *titulos, intro=False, resumir=False):
    bl = secciones(RAIZ / ruta, list(titulos), intro)
    if resumir:   # cuadre de totales: 3 medidas principales + 3 causas mas grandes; las 18 estan en docs/validacion_etl.md
        for b in bl:
            if b["t"] == "table" and b["rows"][0][0] == "Medida":
                claves = ("Pacas", "Horas trabajadas", "Tiempo de paro", "Horas del codigo 05", "Horas del codigo 06", "Horas del codigo 16")
                b["rows"] = [b["rows"][0]] + [f for f in b["rows"][1:] if f[0].startswith(claves)]
                bl.insert(bl.index(b) + 1, {"t": "para", "x": "*Se muestran las medidas principales y las 3 causas de paro más grandes; **las 18 causas cuadran** (detalle completo en `docs/validacion_etl.md`).*"})
                break
    return bl


def resultados_bd():
    import config
    out = {}
    with config.conectar() as conn, conn.cursor() as cur:
        cur.execute("""SELECT p.codigo_paro::text, p.nombre_codigo, round(sum(f.horas_paro)::numeric, 0)::text,
                              round(100*sum(f.horas_paro)/sum(sum(f.horas_paro)) OVER (), 1)::text||' %',
                              round(100*sum(sum(f.horas_paro)) OVER (ORDER BY sum(f.horas_paro) DESC)/sum(sum(f.horas_paro)) OVER (), 1)::text||' %'
                       FROM dw.fact_paro f JOIN dw.dim_paro p USING (paro_key)
                       GROUP BY 1,2 ORDER BY sum(f.horas_paro) DESC LIMIT 8""")
        out["pareto"] = [["Código", "Causa", "Horas", "% del paro", "% acumulado"]] + [list(r) for r in cur.fetchall()]
        cur.execute("""SELECT anio::text, round(100*avg(disponibilidad),1)::text, round(100*avg(rendimiento),1)::text,
                              round(100*avg(calidad),1)::text, round(100*avg(oee),1)::text
                       FROM dw.v_oee_mensual GROUP BY 1 ORDER BY 1""")
        out["oee"] = [["Año", "Disponibilidad %", "Rendimiento %", "Calidad (proxy) %", "OEE %"]] + [list(r) for r in cur.fetchall()]
    return out


def commits():
    log = subprocess.run(["git", "-C", str(RAIZ), "shortlog", "-sn", "HEAD"], capture_output=True, text=True).stdout.strip()
    filas = [["Autor", "Commits"]]
    for l in log.splitlines():
        m = re.match(r"\s*(\d+)\s+(.*)", l)
        if m: filas.append([m.group(2), m.group(1)])
    total = subprocess.run(["git", "-C", str(RAIZ), "rev-list", "--count", "HEAD"], capture_output=True, text=True).stdout.strip()
    return filas, total


def construir() -> Path:
    r = Informe()
    d = r.doc
    hoy = date.today()
    bd = resultados_bd()
    filas_commits, total_commits = commits()

    # ---- portada
    for _ in range(5): d.add_paragraph()
    fuente(d.add_paragraph().add_run("INTELIGENCIA DE NEGOCIOS  ·  PROYECTO FINAL"), 11, True, color=TEAL)
    p = d.add_paragraph(); fuente(p.add_run("BI Vinilos y Témperas"), 32, True, color=OSCURO)
    p = d.add_paragraph(); p.paragraph_format.space_after = Pt(30)
    fuente(p.add_run("Producción y paros de las líneas de envasado: del Excel a un modelo dimensional, un tablero analítico en Power BI y un tablero operativo con alertas en Grafana"), 14, color=GRIS)
    for etiqueta, valores in (("INTEGRANTES", INTEGRANTES), ("REPOSITORIO", [REPO_URL]), ("FECHA", [f"{hoy.day} de {MESES[hoy.month - 1]} de {hoy.year}"])):
        fuente(d.add_paragraph().add_run(etiqueta), 9, True, color=GRIS)
        for v in valores:
            q = d.add_paragraph(); q.paragraph_format.space_after = Pt(0); fuente(q.add_run(v), 13)
        d.add_paragraph()
    r.salto()

    # ---- contenido (campo TOC que Word actualiza)
    t_cont = d.add_paragraph(); t_cont.paragraph_format.space_after = Pt(10)
    fuente(t_cont.add_run("Contenido"), 17, True, color=TEAL)
    p = d.add_paragraph()
    r._campo(p, 'TOC \\o "1-1" \\h \\z \\u', "Haga clic derecho y elija «Actualizar campo» para ver el contenido.")
    r.salto()

    # 1
    r.h1("Resumen y hallazgos")
    r.bloques(md("docs/resumen_ejecutivo.md", "El problema", "Hallazgos", "Recomendaciones", intro=True))
    # 2
    r.h1("Usuarios y preguntas de negocio")
    r.bloques(md("docs/catalogo_indicadores.md", "Usuarios y preguntas de negocio"))
    # 3
    r.h1("Diagnóstico de la fuente")
    r.bloques(md("docs/diagnostico/diagnostico_fuente.md", "Estructura del libro", "Qué está bien", "Problemas de calidad de datos", "Limitaciones del esquema actual de reporte"))
    # 4 catalogo (horizontal)
    r.nueva_seccion(True)
    r.h1("Catálogo de indicadores")
    r.parrafo("Incluye los indicadores que reporta hoy el procedimiento P-MTO-22 (por máquina, mes y año, % por código de paro y detalle de los códigos 01, 03 y 05) y los indicadores nuevos que el Excel no calcula, con su justificación.")
    r.bloques(md("docs/catalogo_indicadores.md", "Supuestos de cálculo", "Catálogo de indicadores", "Por qué estos indicadores nuevos"))
    # 5 modelo
    r.nueva_seccion(False)
    r.h1("Modelo dimensional")
    nota_dic = {"t": "para", "x": "El diccionario de datos completo (columnas, tipos, llaves, reglas de transformación y origen de cada campo) está en el **Anexo A**. Además de estas tablas existen `seguridad.operario_pii` (nombres reales, acceso restringido) y `calidad.incidencias` (bitácora de correcciones del ETL)."}
    modelo = md("docs/modelo_dimensional.md", "Decisión: esquema en estrella", "Tablas de hechos", "Dimensiones", "Matriz de bus", "Dimensión de cambio lento", "Diagrama")
    r.bloques([nota_dic if (b["t"] == "para" and b["x"].startswith("El diccionario de datos completo")) else b for b in modelo])
    # 6 ETL
    r.h1("ETL y validación de los datos")
    r.parrafo("El proceso (carpeta `etl/`) se ejecuta con un solo comando, **desde cero**: lee el Excel, limpia y transforma, carga el modelo en PostgreSQL y valida que los totales cuadren con la fuente. Cada corrida reemplaza lo cargado antes, dentro de una transacción, y no duplica datos. Tiene 10 pruebas automáticas de las reglas de limpieza.")
    r.bloques(md("etl/README.md", "Por qué Python"))
    r.bloques(md("docs/validacion_etl.md", "Reglas de limpieza aplicadas", "Cuadre de totales contra la fuente", "Cuadre por maquina y anio", "Conclusion", resumir=True))
    # 7 BD
    r.h1("Base de datos")
    r.parrafo("PostgreSQL 16 administrado desde DBeaver. El DDL completo está en `sql/init/01_ddl.sql` y se ejecuta solo al crear el contenedor (9 dimensiones, 3 tablas de hechos y los esquemas `seguridad` y `calidad`).")
    r.bloques(md("docs/base_de_datos.md", "Restricciones y por qué", "Índices y por qué", "Consultas analíticas"))
    r.h3("Resultados de dos consultas, leídos de la base cargada")
    r.parrafo("**Q1 · Pareto de causas de paro** (8 primeras)", 9.5); r.tabla(bd["pareto"])
    r.parrafo("**Q2 · OEE y sus componentes por año** (promedio de los meses de las 4 líneas)", 9.5); r.tabla(bd["oee"])
    # 8 Power BI
    r.h1("Power BI: tablero analítico")
    r.bloques(md("powerbi/README.md", "Que contiene"))
    r.imagen(CAPTURAS / "powerbi_1_resumen.png", "Página 1 · Resumen ejecutivo: OEE, disponibilidad, rendimiento y calidad por máquina.", 13.5)
    r.imagen(CAPTURAS / "powerbi_2_paros.png", "Página 2 · Paros y causas: Pareto y drill-down por la jerarquía de paros (área › código › subsistema › detalle).", 13.5)
    r.imagen(CAPTURAS / "powerbi_3_comparativo.png", "Página 3 · Comparativo anual: OEE contra el mismo mes del año anterior, por máquina y por turno.", 13.5)
    # 9 Grafana
    r.h1("Grafana: monitoreo casi en tiempo real")
    r.bloques(md("grafana/README.md", "El tablero", "La alerta"))
    r.bloques(md("simulacion/README.md", "Que simula"))
    r.parrafo("Para la demostración se ejecuta `simular.py`, que emite una lectura por máquina cada 10 segundos (cada lectura equivale a una hora de producción). Con `--provocar Vinilos_2` se fuerza una falla: la máquina pasa a **PARADA** y, tras 2 lecturas seguidas con más de 30 minutos de paro, la alerta se dispara en menos de un minuto; con `--normalizar` se apaga.")
    r.imagen(CAPTURAS / "grafana_normal.png", "Estado normal: las cuatro líneas produciendo y sin alertas.", 14.5)
    r.imagen(CAPTURAS / "grafana_alerta.png", "Falla provocada en Vinilos_2: estado PARADA y alerta «Paro prolongado en maquina» en Firing.", 14.5)
    # 10 Arquitectura
    r.h1("Arquitectura de la solución")
    r.imagen(FIGURAS / "arquitectura.png", "Arquitectura completa: de la fuente al consumo.", 17)
    r.bloques(md("docs/arquitectura.md", "Flujo de datos"))
    # 11 comparativo
    r.h1("Power BI y Grafana: análisis comparativo")
    r.bloques(md("docs/comparativo_power_bi_grafana.md", "Comparativo", "Por qué no se intercambian"))
    # 12 PLC
    r.h1("Evolución con datos de PLC o SCADA")
    flujo = {"t": "para", "x": "**Flujo propuesto:** PLC de cada línea → gateway OPC UA / Modbus → broker MQTT → procesador de flujo → PostgreSQL / TimescaleDB (mismo modelo estrella) → Power BI y Grafana, sin cambiar las definiciones de los indicadores."}
    r.bloques([flujo if b["t"] == "code" else b for b in md("docs/evolucion_plc_scada.md", "Arquitectura propuesta", "Qué cambia y qué no")])
    # 13 seguridad
    r.h1("Datos personales y seguridad de acceso")
    r.bloques(md("docs/seguridad_datos_personales.md", "Qué datos personales hay", "Cómo se trató", "Seguridad de acceso"))
    # 14 docker
    r.h1("Despliegue con Docker (bonificación)")
    for t in ("**Un solo comando:** `docker compose up -d --wait` levanta PostgreSQL y Grafana (o `iniciar.ps1`, que además crea el `.env`, prepara Python y corre el ETL).",
              "**Persistencia con volúmenes:** `pgdata` guarda la base y `grafana-data` el estado de Grafana; `docker compose down` los conserva.",
              "**Credenciales por variables de entorno:** las contraseñas viven en el `.env`, que no se versiona; se versiona `.env.example`.",
              "**Grafana sin configuración manual (*provisioning*):** la fuente de datos, el tablero y la alerta se cargan desde archivos al iniciar el contenedor.",
              "**Power BI y DBeaver** corren en el equipo anfitrión y se conectan a los puertos publicados. En la sustentación todo se levanta en frío, de cero.",
              "**Probado desde un clon limpio** del repositorio en GitHub: crea el `.env`, carga los datos, el ETL cuadra y Grafana aparece configurado."):
        r.viñeta(t)
    # 15 repositorio
    r.h1("Repositorio y reproducción")
    r.parrafo(f"Todo está versionado en GitHub: {REPO_URL} (repositorio privado). Incluye los scripts SQL, el código del ETL, el tablero de Grafana exportado, el proyecto de Power BI y la documentación, con un `README.md` que explica el proyecto, su arquitectura y cómo reproducirlo desde cero.")
    for t in ("**Formato de Power BI: PBIP** (carpetas de texto) en lugar de `.pbix`: Git puede mostrar qué cambió entre versiones y dos personas pueden trabajar sin pisarse; un `.pbix` es un binario que no se puede comparar ni fusionar.",
              "**Sin credenciales en el repositorio:** el `.env` está excluido por el `.gitignore` y no hay cadenas de conexión con contraseñas.",
              "**Reproducir:** clonar el repositorio y ejecutar `iniciar.ps1` (Windows) o `iniciar.sh` (Linux/macOS); después, `simulacion/simular.py` para ver datos en movimiento."):
        r.viñeta(t)
    r.parrafo(f"**Historial de commits:** {total_commits} commits en la rama `main`, por autor.", 10)
    r.tabla(filas_commits)

    # Anexo: diccionario (horizontal)
    r.nueva_seccion(True)
    r.h1("Anexo A. Diccionario de datos", numerar=False)
    r.parrafo("Para cada tabla: descripción, columnas, tipos, llaves (PK / FK), reglas de transformación y origen de cada campo. Generado desde la propia base para que no se desfase del DDL.")
    bl = parsear((RAIZ / "docs" / "diccionario_datos.md").read_text(encoding="utf-8"))
    empezar = next(i for i, b in enumerate(bl) if b["t"] == "heading" and b["n"] == 2)
    r.tam_tabla = 7
    r.bloques(bl[empezar:], numerar=False)

    r.guardar(SALIDA_DOCX)
    print("Word generado:", SALIDA_DOCX)
    return SALIDA_DOCX


POWERSHELL = r"""
$ErrorActionPreference = 'Stop'
$word = New-Object -ComObject Word.Application
$word.Visible = $false; $word.DisplayAlerts = 0
try {
  $doc = $word.Documents.Open('%s')
  $doc.Fields.Update() | Out-Null
  foreach ($t in $doc.TablesOfContents) { $t.Update() }
  $doc.Repaginate()
  foreach ($t in $doc.TablesOfContents) { $t.Update() }
  $doc.Save()
  $doc.ExportAsFixedFormat('%s', 17)
  Write-Output ("Paginas: " + $doc.ComputeStatistics(2))
  $doc.Close($false)
} finally { $word.Quit() }
"""


def exportar_pdf(docx: Path) -> Path:
    pdf = docx.with_suffix(".pdf")
    script = POWERSHELL % (str(docx), str(pdf))
    res = subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True)
    print(res.stdout.strip() or res.stderr.strip())
    return pdf


if __name__ == "__main__":
    ruta = construir()
    if "--sin-pdf" not in sys.argv:
        print("PDF:", exportar_pdf(ruta))
