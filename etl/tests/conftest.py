"""Configuracion de fixtures y entorno de pruebas para etl/tests."""
import sys
from unittest.mock import MagicMock

# Si psycopg no esta instalado en el entorno de pruebas local, se registra un mock
# para permitir la ejecucion de pruebas unitarias puras sin depender del driver de PostgreSQL
try:
    import psycopg
except ImportError:
    mock_psycopg = MagicMock()
    mock_psycopg.Connection = object
    sys.modules["psycopg"] = mock_psycopg
