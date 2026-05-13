param(
    [string]$Module,
    [string]$Db = "postgres",
    [switch]$HardReset
)

if (-not $Module) {
    Write-Host "Usage: .\odoo-reload.ps1 -Module your_module [-Db your_db] [-HardReset]"
    Write-Host "  -HardReset  Drops and recreates the DB. Use when views/actions are stale."
    exit 1
}

$PgUser       = "odoo"
$PgPassword   = "odoo"
$AppContainer = "odoo19_app"
$DbContainer  = "odoo19_db"

function Invoke-Psql {
    param([string]$Sql)
    docker exec -e PGPASSWORD=$PgPassword $DbContainer `
        psql -U $PgUser -d $Db -c $Sql
}

function Invoke-PsqlOnPostgres {
    param([string]$Sql)
    docker exec -e PGPASSWORD=$PgPassword $DbContainer `
        psql -U $PgUser -d postgres -c $Sql
}

# ── HARD RESET ─────────────────────────────────────────────────────────────
if ($HardReset) {
    Write-Host "[!] Hard reset requested -- dropping database '$Db'..."

    Write-Host "[>] Stopping Odoo container..."
    docker stop $AppContainer | Out-Null

    Write-Host "[>] Terminating active connections..."
    Invoke-PsqlOnPostgres "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$Db' AND pid <> pg_backend_pid();" | Out-Null

    Write-Host "[>] Dropping database..."
    Invoke-PsqlOnPostgres "DROP DATABASE IF EXISTS ""$Db"";"

    Write-Host "[>] Creating database..."
    Invoke-PsqlOnPostgres "CREATE DATABASE ""$Db"" OWNER $PgUser;"

    Write-Host "[>] Starting Odoo container..."
    docker start $AppContainer | Out-Null
    Start-Sleep -Seconds 5

    Write-Host "[>] Installing module from scratch (with demo)..."
    docker exec $AppContainer odoo -i $Module -d $Db --stop-after-init

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[X] Installation failed (exit code $LASTEXITCODE)."
        exit $LASTEXITCODE
    }

    Write-Host "[>] Restarting Odoo..."
    docker restart $AppContainer
    Write-Host "[OK] Hard reset complete."
    exit 0
}

# ── SOFT UPDATE ────────────────────────────────────────────────────────────
Write-Host "[>] Cleaning stale act_window.view records for module '$Module'..."

$cleanSql = "DELETE FROM ir_act_window_view iawv USING ir_act_window iaw, ir_model_data imd WHERE iawv.act_window_id = iaw.id AND imd.res_id = iaw.id AND imd.model = 'ir.actions.act_window' AND imd.module = '$Module';"
Invoke-Psql $cleanSql | Out-Null

Write-Host "[>] Clearing view cache..."
Invoke-Psql "DELETE FROM ir_ui_view_custom WHERE user_id IS NOT NULL;" | Out-Null

Write-Host "[>] Updating module '$Module' on database '$Db'..."
docker exec $AppContainer odoo -u $Module -d $Db --stop-after-init

if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] Module update failed (exit code $LASTEXITCODE). Try -HardReset."
    exit $LASTEXITCODE
}

Write-Host "[>] Restarting Odoo..."
docker restart $AppContainer
Write-Host "[OK] Done. Use -HardReset if views still look stale."