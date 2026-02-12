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
if (Test-Path "build/reading_edition") {
  $pdfs = Get-ChildItem "build/reading_edition" -Filter "*.pdf" -ErrorAction SilentlyContinue
  if ($pdfs.Count -gt 0) {
    Write-Host "- Reading Edition PDFs: build/reading_edition/*.pdf"
  }
}
