.PHONY: help test lint clean up down check-db

help:
	@echo "=========================================================="
	@echo "Comandos de desarrollo - BI Vinilos y Temperas"
	@echo "=========================================================="
	@echo "  make test      - Ejecuta la suite de pruebas unitarias (pytest)"
	@echo "  make lint      - Valida la sintaxis de los scripts Python"
	@echo "  make up        - Inicia los contenedores (PostgreSQL y Grafana)"
	@echo "  make down      - Detiene los contenedores Docker"
	@echo "  make check-db  - Verifica conectividad y latencia con PostgreSQL"
	@echo "  make clean     - Elimina archivos temporales y cache de Python"
	@echo "=========================================================="

test:
	python -m pytest

lint:
	python -m compileall etl simulacion sql docs/informe

up:
	docker compose up -d

down:
	docker compose down

check-db:
	python sql/verificar_conexion.py

clean:
	python -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]"
	python -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').glob('.pytest_cache')]"
