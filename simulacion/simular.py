"""Simulador de lecturas hora a hora para el monitoreo en Grafana.

Cada "tick" inserta una lectura por maquina en dw.fact_registro_horario (pacas de la hora y
minutos de paro). El ritmo y las causas salen de los datos historicos ya cargados por el ETL.

Uso (con la base levantada y el ETL corrido):
    python simulacion/simular.py                      # una lectura por maquina cada 10 s, sin parar
    python simulacion/simular.py --provocar Vinilos_2 # (en otra terminal) fuerza una falla larga
    python simulacion/simular.py --normalizar         # quita la falla provocada
    python simulacion/simular.py --reiniciar          # borra las lecturas simuladas y empieza de cero

Cada lectura representa UNA HORA de produccion. En la demo se emite una cada 10 s (--intervalo)
en lugar de una cada 3600 s, para que el tablero y la alerta reaccionen a la vista de todos.
"""
import argparse
import os
import random
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psycopg
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")
BANDERA = Path(__file__).resolve().parent / "falla.flag"   # contiene el nombre de la maquina con falla

COLOMBIA = timezone(timedelta(hours=-5))   # sin horario de verano
PROB_PARO = 0.20                           # probabilidad de paro en una lectura (el historico ronda 20-25 %)
MINUTOS_FALLA = (42, 58)                   # rango de minutos de paro de una falla provocada


def conectar() -> psycopg.Connection:
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"), port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.environ["POSTGRES_DB"], user=os.environ["POSTGRES_USER"], password=os.environ["POSTGRES_PASSWORD"])


def turno_de(hora: int) -> int:
    """Turno 1 de 6 a 14, turno 2 de 14 a 22, turno 3 de 22 a 6."""
    return 1 if 6 <= hora < 14 else 2 if 14 <= hora < 22 else 3


class Simulador:
    def __init__(self, conn: psycopg.Connection, semilla: int | None):
        self.conn, self.rng = conn, random.Random(semilla)
        with conn.cursor() as cur:
            cur.execute("SELECT nombre, maquina_key FROM dw.dim_maquina WHERE maquina_key > 0 ORDER BY 1")
            self.maquinas = dict(cur.fetchall())
            cur.execute("""SELECT DISTINCT maquina_key, referencia_key FROM dw.fact_produccion
                           WHERE referencia_key <> -1""")
            self.referencias: dict[int, list[int]] = {}
            for m, r in cur.fetchall():
                self.referencias.setdefault(m, []).append(r)
            cur.execute("SELECT maquina_key, referencia_key, meta_key, pacas_por_hora FROM dw.dim_meta_velocidad WHERE es_vigente AND meta_key > 0")
            self.metas = {(m, r): (k, float(p)) for m, r, k, p in cur.fetchall()}
            cur.execute("""SELECT f.paro_key, count(*) FROM dw.fact_paro f JOIN dw.dim_paro p USING (paro_key)
                           WHERE NOT p.es_programado GROUP BY 1""")
            causas = cur.fetchall()
            self.causas = [c for c, _ in causas]
            self.pesos = [n for _, n in causas]
            cur.execute("""SELECT paro_key FROM dw.dim_paro
                           WHERE codigo_paro = 1 AND subsistema_codigo = 'Sin subcodigo'""")
            self.causa_falla = cur.fetchone()[0]
        if not self.metas or not self.causas:
            sys.exit("Faltan datos: corre primero el ETL (python etl/main.py).")
        self.referencia_actual = {m: self.rng.choice(self.referencias.get(m, [-1])) for m in self.maquinas.values()}

    def meta(self, maquina_key: int, referencia_key: int) -> tuple[int, float]:
        return self.metas.get((maquina_key, referencia_key)) or self.metas.get((maquina_key, -1)) \
            or next(v for (m, _), v in self.metas.items() if m == maquina_key)

    def lectura(self, nombre: str, maquina_key: int, falla_en: str | None) -> dict:
        if self.rng.random() < 0.04 and len(self.referencias.get(maquina_key, [])) > 1:   # cambio de referencia
            self.referencia_actual[maquina_key] = self.rng.choice(self.referencias[maquina_key])
        referencia = self.referencia_actual[maquina_key]
        meta_key, pph = self.meta(maquina_key, referencia)
        if nombre == falla_en:
            minutos, paro = self.rng.uniform(*MINUTOS_FALLA), self.causa_falla
        elif self.rng.random() < PROB_PARO:
            minutos = min(max(self.rng.lognormvariate(2.5, 0.6), 3), 40)
            paro = self.rng.choices(self.causas, weights=self.pesos)[0]
        else:
            minutos, paro = 0.0, -1
        pacas = max(pph * (60 - minutos) / 60 * self.rng.gauss(0.90, 0.07), 0)
        return {"maquina_key": maquina_key, "referencia_key": referencia, "meta_key": meta_key, "paro_key": paro,
                "pacas": round(pacas, 2), "minutos": round(minutos, 2), "nombre": nombre}

    def tick(self, momento_utc: datetime, falla_en: str | None) -> list[dict]:
        local = momento_utc.replace(tzinfo=timezone.utc).astimezone(COLOMBIA)
        fecha_key, hora = int(local.strftime("%Y%m%d")), local.hour
        lecturas = [self.lectura(n, k, falla_en) for n, k in self.maquinas.items()]
        with self.conn.cursor() as cur:
            cur.executemany("""
                INSERT INTO dw.fact_registro_horario (fecha_hora, fecha_key, hora_key, maquina_key, turno_key,
                       referencia_key, paro_key, meta_key, pacas_hora, minutos_paro)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (maquina_key, fecha_hora) DO NOTHING""",
                [(momento_utc, fecha_key, hora, l["maquina_key"], turno_de(hora), l["referencia_key"], l["paro_key"],
                  l["meta_key"], l["pacas"], l["minutos"]) for l in lecturas])
        self.conn.commit()
        return lecturas


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--intervalo", type=float, default=10, help="segundos entre lecturas (por defecto 10)")
    ap.add_argument("--ciclos", type=int, default=0, help="detenerse tras N lecturas (0 = sin limite)")
    ap.add_argument("--historial", type=int, default=30, help="lecturas pasadas a generar al empezar (por defecto 30)")
    ap.add_argument("--reiniciar", action="store_true", help="borra las lecturas simuladas antes de empezar")
    ap.add_argument("--provocar", metavar="MAQUINA", help="fuerza una falla larga en esa maquina y sale")
    ap.add_argument("--normalizar", action="store_true", help="quita la falla provocada y sale")
    ap.add_argument("--semilla", type=int, help="semilla aleatoria, para resultados repetibles")
    a = ap.parse_args()

    if a.provocar:
        BANDERA.write_text(a.provocar.strip(), encoding="utf-8")
        print(f"Falla provocada en {a.provocar}. El simulador en marcha la aplica en su proxima lectura.")
        return 0
    if a.normalizar:
        BANDERA.unlink(missing_ok=True)
        print("Falla retirada. Las maquinas vuelven a su comportamiento normal.")
        return 0

    with conectar() as conn:
        sim = Simulador(conn, a.semilla)
        if a.reiniciar:
            with conn.cursor() as cur:
                cur.execute("TRUNCATE dw.fact_registro_horario RESTART IDENTITY")
            conn.commit()
            print("Lecturas anteriores borradas.")
        ahora = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)   # se guarda en UTC
        for i in range(a.historial, 0, -1):
            sim.tick(ahora - timedelta(seconds=i * a.intervalo), None)
        if a.historial:
            print(f"{a.historial} lecturas de historial creadas.")
        print(f"Simulando: una lectura por maquina cada {a.intervalo:g} s. Ctrl+C para detener.\n")
        n = 0
        try:
            while a.ciclos == 0 or n < a.ciclos:
                falla = BANDERA.read_text(encoding="utf-8").strip() if BANDERA.exists() else None
                momento = datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)
                lecturas = sim.tick(momento, falla)
                resumen = " | ".join(
                    f"{l['nombre']}: " + (f"PARO {l['minutos']:.0f} min" if l["minutos"] > 0 else "ok") + f" {l['pacas']:.0f} pacas"
                    for l in lecturas)
                print(f"{momento.replace(tzinfo=timezone.utc).astimezone(COLOMBIA):%H:%M:%S}  {resumen}", flush=True)
                n += 1
                if a.ciclos == 0 or n < a.ciclos:
                    time.sleep(a.intervalo)
        except KeyboardInterrupt:
            print("\nSimulacion detenida.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
