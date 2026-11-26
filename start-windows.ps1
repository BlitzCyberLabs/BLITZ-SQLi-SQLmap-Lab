$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$svc = Get-Service | Where-Object { $_.Name -match 'MySQL|MariaDB' } | Select-Object -First 1
if (-not $svc) { throw "MySQL/MariaDB service not found. Run setup-windows.ps1 first." }
if ($svc.Status -ne "Running") { Start-Service $svc.Name }
& .\venv\Scripts\python.exe app.py
