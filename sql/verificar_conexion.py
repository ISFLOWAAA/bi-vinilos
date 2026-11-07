"""Script de diagnostico para verificar la conexion y el estado de la base de datos PostgreSQL."""
import os
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "etl"))

try:
    from dotenv import load_dotenv
    load_dotenv(RAIZ / ".env")
except ImportError:
    pass

import config


def verificar_estado_bd() -> dict:
    """Intenta conectar a PostgreSQL y obtiene metricas de disponibilidad."""
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    dbname = os.getenv("POSTGRES_DB", "bi_vinilos")
    user = os.getenv("POSTGRES_USER", "postgres")

    info = {
        "host": host,
        "port": port,
        "dbname": dbname,
        "user": user,
        "conectado": False,
        "latencia_ms": None,
        "tablas_dw": 0,
        "mensaje": "",
    }

    inicio = time.perf_counter()
    try:
        with config.conectar() as conn:
            info["latencia_ms"] = round((time.perf_counter() - inicio) * 1000, 2)
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT count(*) FROM information_schema.tables 
                    WHERE table_schema = 'dw'
                """)
                info["tablas_dw"] = cur.fetchone()[0]
            info["conectado"] = True
            info["mensaje"] = "Conexion exitosa con PostgreSQL"
    except Exception as e:
        info["mensaje"] = f"No fue posible conectar: {e}"

    return info


def main():
    print("=" * 60)
    print("DIAGNOSTICO DE BASE DE DATOS - BI VINILOS")
    print("=" * 60)
    res = verificar_estado_bd()
    print(f"Host:           {res['host']}:{res['port']}")
    print(f"Base de datos:  {res['dbname']}")
    print(f"Usuario:        {res['user']}")
    print(f"Estado:         {'CONECTADO (OK)' if res['conectado'] else 'FALLO'}")
    if res['latencia_ms'] is not None:
        print(f"Latencia:       {res['latencia_ms']} ms")
        print(f"Tablas en 'dw': {res['tablas_dw']}")
    print(f"Detalle:        {res['mensaje']}")
    print("=" * 60)
    sys.exit(0 if res["conectado"] else 1)


if __name__ == "__main__":
    main()
