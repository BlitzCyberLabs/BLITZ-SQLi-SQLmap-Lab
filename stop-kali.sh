#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
echo "Stop the Flask lab in its running terminal with Ctrl+C."
echo "The next start (./start-kali.sh) automatically resets the database to the original static training dataset."
echo "To stop MariaDB as well: sudo systemctl stop mariadb"
