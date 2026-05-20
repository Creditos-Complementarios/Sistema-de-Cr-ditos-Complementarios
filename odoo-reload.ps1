param(
    [string]$Module,
    [string]$Db = "odoo_dev",
    [switch]$HardReset
)

if (-not $Module) {
    Write-Host "Usage: .\odoo-reload.ps1 -Module your_module [-Db your_db] [-HardReset]"
    exit 1
}

$PgUser       = "odoo"
$PgPassword   = "odoo"
$AppContainer = "odoo19_app"
$DbContainer  = "odoo19_db"

function Invoke-PsqlOnPostgres {
    param([string]$Sql)
    docker exec -i $DbContainer `
        psql -U $PgUser -d postgres -c $Sql
}

function Invoke-Psql {
    param([string]$Sql)
    docker exec -i $DbContainer `
        psql -U $PgUser -d $Db -c $Sql
}

# ── HARD RESET ─────────────────────────────────────────────────────────────
if ($HardReset) {
    Write-Host "[!] Hard reset -- dropping '$Db'..."

    Write-Host "[>] Stopping Odoo container..."
    docker stop $AppContainer | Out-Null

    Write-Host "[>] Terminating active DB connections..."
    Invoke-PsqlOnPostgres "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$Db' AND pid <> pg_backend_pid();" | Out-Null

    Write-Host "[>] Dropping database..."
    Invoke-PsqlOnPostgres "DROP DATABASE IF EXISTS `"$Db`";"

    Write-Host "[>] Creating database..."
    Invoke-PsqlOnPostgres "CREATE DATABASE `"$Db`" OWNER $PgUser;"

    Write-Host "[>] Starting Odoo container..."
    docker start $AppContainer | Out-Null

    Write-Host "[>] Waiting for Odoo to initialize..."
    Start-Sleep -Seconds 10

    Write-Host "[>] Installing '$Module' with demo data..."
    docker exec $AppContainer odoo `
        --db_host=db --db_user=$PgUser --db_password=$PgPassword `
        -d $Db -i $Module `
        --stop-after-init --log-level=warn --without-demo=False

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[X] Installation failed (exit $LASTEXITCODE)."
        exit $LASTEXITCODE
    }

    Write-Host "[>] Restarting Odoo..."
    docker restart $AppContainer | Out-Null
    Write-Host "[OK] Hard reset complete."
    Write-Host "     Web login -> admin / admin"
    exit 0
}

# ── SOFT UPDATE ────────────────────────────────────────────────────────────
Write-Host "[>] Cleaning stale act_window.view records for '$Module'..."
Invoke-Psql "DELETE FROM ir_act_window_view iawv USING ir_act_window iaw, ir_model_data imd WHERE iawv.act_window_id = iaw.id AND imd.res_id = iaw.id AND imd.model = 'ir.actions.act_window' AND imd.module = '$Module';" | Out-Null

Write-Host "[>] Clearing view cache..."
Invoke-Psql "DELETE FROM ir_ui_view_custom WHERE user_id IS NOT NULL;" | Out-Null

Write-Host "[>] Updating '$Module' on '$Db'..."
docker exec $AppContainer odoo `
    --db_host=db --db_user=$PgUser --db_password=$PgPassword `
    -d $Db -u $Module `
    --stop-after-init --log-level=warn

if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] Update failed (exit $LASTEXITCODE). Try -HardReset."
    exit $LASTEXITCODE
}

Write-Host "[>] Restarting Odoo..."
docker restart $AppContainer | Out-Null
Write-Host "[OK] Done."