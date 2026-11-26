# BLITZ SQLi & SQLMap Lab

A deliberately vulnerable e-commerce training application for controlled SQL injection and SQLMap practice. Run it only on an isolated lab network. Do not expose it to the public internet.

## Kali Linux setup

Requirements: Kali Linux, internet access, Git, and sudo access.

1. Clone the repository:
   ```bash
   git clone https://github.com/BlitzCyberLabs/BLITZ-SQLi-SQLmap-Lab.git
   ```
2. Enter the project directory:
   ```bash
   cd BLITZ-SQLi-SQLmap-Lab
   ```
3. Make scripts executable:
   ```bash
   chmod +x setup-kali.sh start-kali.sh stop-kali.sh
   ```
4. Run one-time setup:
   ```bash
   sudo ./setup-kali.sh
   ```
5. Start the lab:
   ```bash
   ./start-kali.sh
   ```

The startup script prints the local and LAN URLs. Open the local URL in Kali or use the LAN URL from another device on the same trusted network.

If you are upgrading an earlier installation, rerun the database permission setup once after replacing the project files:

```bash
sudo mariadb < setup.sql
```

## Reset behavior

**The database is reset automatically every time `app.py` starts.** Stop the Flask server with `Ctrl+C`; when you run `./start-kali.sh` again, all tables are cleared and repopulated with the same deterministic training dataset. Changes made during the previous run are discarded. No manual database cleanup is required.

The final training flag is fixed for every student and every installation:

```text
BLITZ{a67b1c38938e29bc7bae1dce}
```

The flag is not randomly generated. The local admin username and password are created once in `lab_config.json` and remain stable across restarts. Keep that file if you want to retain the same local admin credentials.

## Windows

Install MariaDB Server and ensure its client is available in PATH. Run PowerShell as Administrator:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup-windows.ps1
.\start-windows.ps1
```

Stop with `Ctrl+C`. Starting again performs the same automatic database reset.

## SQL injection practice endpoint

The intentionally vulnerable product endpoint is `/product?id=1`. It is deliberately unsafe for this isolated training exercise.

## Safety

Use only in an isolated classroom/lab environment or trusted private network. Never port-forward it or expose it directly to the internet.
