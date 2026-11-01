"""Punto de entrada del ETL.  Uso:  python etl/main.py

Extrae el Excel, lo limpia y transforma al modelo estrella, lo carga en PostgreSQL y valida
que los totales cuadren con la fuente. Requiere la base levantada (docker compose up -d).
"""
import sys
import time

import config
from cargar import cargar
from extraer import leer_base, leer_catalogo_codigos
from transformar import transformar
from validar import validar


def paso(texto: str) -> float:
    print(f"\n>> {texto}", flush=True)
    return time.time()


def main() -> int:
    t = paso(f"1/4 Extraer: {config.EXCEL.name}")
    base = leer_base(config.EXCEL)
    catalogo = leer_catalogo_codigos(config.EXCEL)
    print(f"   {len(base):,} filas leidas ({time.time() - t:.1f} s)")

    t = paso("2/4 Transformar: limpieza y modelo estrella")
    resultado = transformar(base, catalogo)
    for b in resultado.bitacora:
        print(f"   - {b['regla']}: {b['antes']:,} -> {b['despues']:,}")

    t = paso("3/4 Cargar en PostgreSQL")
    with config.conectar() as conn:
        cargadas = cargar(conn, resultado)
        for tabla, n in cargadas.items():
            print(f"   {tabla:28} {n:>7,} filas")

        paso("4/4 Validar contra la fuente")
        ok, informe = validar(conn, resultado)
    config.REPORTE_VALIDACION.write_text(informe, encoding="utf-8")
    print(f"\n   Informe: {config.REPORTE_VALIDACION}")
    print("   RESULTADO:", "TODO CUADRA" if ok else "HAY DIFERENCIAS SIN EXPLICAR")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
