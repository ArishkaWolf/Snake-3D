param([switch]$SkipTests)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$pythonExe = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    throw 'First create .venv and install requirements-dev.txt. See README.md.'
}
if (-not $SkipTests) {
    & $pythonExe -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
}
& $pythonExe -m PyInstaller --noconfirm Snake3D.spec
if ($LASTEXITCODE -ne 0) { throw 'Build failed.' }
Write-Output 'Ready: dist\Snake3D\Snake3D.exe. Distribute the entire Snake3D folder.'
