param([switch]$SkipTests)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
& (Join-Path $PSScriptRoot 'build_windows.ps1') -SkipTests:$SkipTests
if ($LASTEXITCODE -ne 0) { throw 'Windows build failed.' }
$pythonExe = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
& $pythonExe tools/create_press_kit.py
if ($LASTEXITCODE -ne 0) { throw 'Press kit generation failed.' }
& $pythonExe tools/package_release.py
if ($LASTEXITCODE -ne 0) { throw 'Release packaging failed.' }
& $pythonExe tools/verify_release.py dist/Snake-3D-v1.0-Windows.zip
if ($LASTEXITCODE -ne 0) { throw 'Archive verification failed.' }
Write-Output 'Ready: dist\Snake-3D-v1.0-Windows.zip and dist\Snake-3D-v1.0-itchio-kit.zip'
