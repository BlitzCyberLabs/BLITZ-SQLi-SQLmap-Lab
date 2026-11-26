#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "[1/5] Installing local prerequisites..."
sudo apt update
sudo apt install -y mariadb-server python3-venv python3-pip sqlmap

echo "[2/5] Starting MariaDB..."
sudo systemctl enable --now mariadb

echo "[3/5] Creating BLITZ lab database and restricted application account..."
sudo mariadb < setup.sql

echo "[4/5] Creating Python virtual environment..."
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

echo "[5/5] Setup complete."
echo "Start the lab with: ./start-kali.sh"
