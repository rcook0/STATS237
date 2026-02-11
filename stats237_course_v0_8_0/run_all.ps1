$ErrorActionPreference = "Stop"

python scripts/build_all.py

Write-Host ""
Write-Host "Outputs:"
if (Test-Path "build/site/index.html") {
  Write-Host "- HTML site: build/site/index.html"
}
if (Test-Path "build/Stats237_Reader.pdf") {
  Write-Host "- PDF reader: build/Stats237_Reader.pdf"
}
