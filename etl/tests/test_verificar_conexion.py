"""Pruebas unitarias para el script utilitario de diagnostico de base de datos."""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

RAIZ = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(RAIZ / "sql"))

from verificar_conexion import verificar_estado_bd


def test_verificar_estado_bd_captura_excepcion():
    """Valida que si no hay conexion, devuelva un diccionario estructurado sin lanzar excepcion."""
    with patch("config.conectar", side_effect=ConnectionRefusedError("Conexion rechazada")):
        res = verificar_estado_bd()
        assert isinstance(res, dict)
        assert res["conectado"] is False
        assert "Conexion rechazada" in res["mensaje"]
        assert res["latencia_ms"] is None


def test_verificar_estado_bd_conexion_exitosa():
    """Valida que con una conexion exitosa devuelva latencia y conteo de tablas dw."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = [12]
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    with patch("config.conectar", return_value=mock_conn):
        res = verificar_estado_bd()
        assert res["conectado"] is True
        assert res["tablas_dw"] == 12
        assert res["latencia_ms"] is not None
