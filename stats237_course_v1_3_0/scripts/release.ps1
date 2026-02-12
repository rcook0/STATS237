$ErrorActionPreference = "Stop"

$VERSION = "1.0.0"
$ROOT = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ROOT

python scripts/build_all.py
python scripts/release_gate.py --strict

$DIST = Join-Path $ROOT ("dist/stats237_course_v" + $VERSION)
if (Test-Path $DIST) { Remove-Item -Recurse -Force $DIST }
New-Item -ItemType Directory -Force -Path $DIST | Out-Null

# Core artifacts
if (Test-Path "build") { Copy-Item -Recurse -Force "build" (Join-Path $DIST "build") }
if (Test-Path "docs") { Copy-Item -Recurse -Force "docs" (Join-Path $DIST "docs") }
if (Test-Path "golden") { Copy-Item -Recurse -Force "golden" (Join-Path $DIST "golden") }

foreach ($d in @("registry","problem_bank","coverage","reports")) {
  if (Test-Path $d) { Copy-Item -Recurse -Force $d (Join-Path $DIST $d) }
}

New-Item -ItemType Directory -Force -Path (Join-Path $DIST "api") | Out-Null
Copy-Item -Force "api/openapi_snapshot.json" (Join-Path $DIST "api/openapi_snapshot.json")

New-Item -ItemType Directory -Force -Path (Join-Path $DIST "wheels") | Out-Null
python -m pip wheel .\stats237_quantlib --no-deps -w (Join-Path $DIST "wheels") | Out-Null

Write-Host ("Release dist written to: " + $DIST)
