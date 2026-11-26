#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
sudo systemctl start mariadb
source venv/bin/activate
python app.py
