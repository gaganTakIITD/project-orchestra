# Drive intent/chat → finalize → accept → submit → delivery (Track C / B6).
#
# Prerequisites:
#   docker compose up -d postgres
#   docker compose stop api   # if api shares the same DB (ASGI resets schema)
#   cd backend; pip install -e ".[dev]"
#
# Usage:
#   .\scripts\run-slice.ps1
#   .\scripts\run-slice.ps1 --http http://localhost:8000
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
python scripts/run-slice.py @args
exit $LASTEXITCODE
