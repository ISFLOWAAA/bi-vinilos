<#
.SYNOPSIS
  Levanta todo el proyecto con un comando (Windows PowerShell):   .\iniciar.ps1

.DESCRIPTION
  1. Verifica Docker y Python.
  2. Crea el archivo .env si no existe, con contrasenas aleatorias (nunca se sube a Git).
  3. Levanta PostgreSQL y Grafana con Docker Compose.
  4. Prepara el entorno de Python.
  5. Ejecuta el ETL (carga el Excel al modelo estrella y valida los totales).

  Se puede ejecutar varias veces: no duplica datos.
  Si Windows bloquea el script:  powershell -ExecutionPolicy Bypass -File .\iniciar.ps1
#>
$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot

function Paso($texto) { Write-Host "`n>> $texto" -ForegroundColor Cyan }
function Fallar($texto) { Write-Host "`nERROR: $texto" -ForegroundColor Red; exit 1 }
function ClaveAleatoria { -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 20 | ForEach-Object { [char]$_ }) }
function PuertoLibre($preferido, $alterno) {
    if (Get-NetTCPConnection -LocalPort $preferido -State Listen -ErrorAction SilentlyContinue) { $alterno } else { $preferido }
}

# ---------------------------------------------------------------- 1. herramientas
Paso "1/5 Verificando herramientas"
foreach ($c in "git", "docker", "python") {
    if (-not (Get-Command $c -ErrorAction SilentlyContinue)) { Fallar "Falta '$c'. Ver la seccion Requisitos del README." }
}
& python -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)"
if ($LASTEXITCODE -ne 0) { Fallar "Se necesita Python 3.11 o superior." }
cmd /c "docker info >nul 2>nul"
if ($LASTEXITCODE -ne 0) { Fallar "Docker Desktop no esta en marcha. Abrelo y espera a que diga 'Engine running'." }
Write-Host "   Git, Docker y Python disponibles."

# ---------------------------------------------------------------- 2. .env
Paso "2/5 Archivo .env"
if (Test-Path ".env") {
    Write-Host "   Ya existe .env: se conserva tal cual."
}
else {
    $texto = Get-Content ".env.example" -Raw
    $texto = $texto -replace "(?m)^POSTGRES_PASSWORD=.*$", "POSTGRES_PASSWORD=$(ClaveAleatoria)"
    $texto = $texto -replace "(?m)^GF_SECURITY_ADMIN_PASSWORD=.*$", "GF_SECURITY_ADMIN_PASSWORD=$(ClaveAleatoria)"
    $texto = $texto -replace "(?m)^BI_LECTOR_PASSWORD=.*$", "BI_LECTOR_PASSWORD=$(ClaveAleatoria)"
    $texto = $texto -replace "(?m)^POSTGRES_PORT=.*$", "POSTGRES_PORT=$(PuertoLibre 5432 5433)"
    $texto = $texto -replace "(?m)^GRAFANA_PORT=.*$", "GRAFANA_PORT=$(PuertoLibre 3000 3001)"
    [System.IO.File]::WriteAllText((Join-Path $PSScriptRoot ".env"), $texto, (New-Object System.Text.UTF8Encoding $false))
    Write-Host "   .env creado con contrasenas aleatorias (no se sube a Git). Reviselo para conocer usuarios, contrasenas y puertos."
}

# ---------------------------------------------------------------- 3. Docker
Paso "3/5 Levantando PostgreSQL y Grafana (la primera vez descarga las imagenes)"
docker compose up -d --wait
if ($LASTEXITCODE -ne 0) { Fallar "Docker Compose no pudo levantar los servicios. Ver 'docker compose logs'." }

# ---------------------------------------------------------------- 4. Python
Paso "4/5 Entorno de Python"
if (-not (Test-Path ".venv")) { python -m venv .venv }
$py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
& $py -m pip install -q -r etl\requirements.txt
if ($LASTEXITCODE -ne 0) { Fallar "No se pudieron instalar las librerias de Python." }
Write-Host "   Librerias instaladas."

# ---------------------------------------------------------------- 5. ETL
Paso "5/5 Ejecutando el ETL"
$env:PYTHONIOENCODING = "utf-8"
& $py etl\main.py
if ($LASTEXITCODE -ne 0) { Fallar "El ETL termino con diferencias. Ver docs\validacion_etl.md." }

# ---------------------------------------------------------------- resumen
$cfg = @{}
foreach ($linea in Get-Content ".env") { if ($linea -match '^\s*([A-Z_]+)=(.*)$') { $cfg[$Matches[1]] = $Matches[2] } }
Write-Host "`n=== LISTO ===" -ForegroundColor Green
Write-Host "Grafana    : http://localhost:$($cfg.GRAFANA_PORT)   (usuario $($cfg.GF_SECURITY_ADMIN_USER); la contrasena esta en .env)"
Write-Host "PostgreSQL : localhost:$($cfg.POSTGRES_PORT), base $($cfg.POSTGRES_DB), usuario de solo lectura $($cfg.BI_LECTOR_USER)"
Write-Host "Datos en movimiento : .venv\Scripts\python simulacion\simular.py"
Write-Host "Power BI            : abrir powerbi\BI_Vinilos.pbip (ver powerbi\README.md)"
