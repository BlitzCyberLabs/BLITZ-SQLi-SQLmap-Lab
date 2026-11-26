$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "[1/4] Checking Python..."
python --version
if ($LASTEXITCODE -ne 0) { throw "Install Python 3.11+ and enable 'Add Python to PATH'." }

Write-Host "[2/4] Checking for a MySQL or MariaDB Windows service..."
$svc = Get-Service | Where-Object { $_.Name -match 'MySQL|MariaDB' } | Select-Object -First 1
if (-not $svc) {
    Write-Host ""
    Write-Host "No MySQL/MariaDB Windows service was found."
    Write-Host "Install MariaDB Server for Windows, then rerun this script."
    Write-Host "Download: https://mariadb.org/download/"
    throw "MariaDB Server is required."
}
if ($svc.Status -ne "Running") { Start-Service $svc.Name }

Write-Host "[3/4] Creating database and restricted app account..."
$mariadb = Get-Command mariadb.exe -ErrorAction SilentlyContinue
$mysql = Get-Command mysql.exe -ErrorAction SilentlyContinue
$client = if ($mariadb) { $mariadb.Source } elseif ($mysql) { $mysql.Source } else { $null }
if (-not $client) {
    throw "Could not find mariadb.exe or mysql.exe in PATH. Add the MariaDB bin folder to PATH and rerun."
}
Write-Host "The setup SQL will be executed. Enter the database administrator password if prompted."
Get-Content setup.sql | & $client -u root -p
if ($LASTEXITCODE -ne 0) { throw "Database initialization failed." }

Write-Host "[4/4] Creating Python environment and installing dependencies..."
python -m venv venv
& .\venv\Scripts\python.exe -m pip install --upgrade pip
& .\venv\Scripts\pip.exe install -r requirements.txt
Write-Host "Setup complete. Run .\start-windows.ps1"
