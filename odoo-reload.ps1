param(
    [string]$Module,
    [string]$Db = "postgres"
)

if (-not $Module) {
    Write-Host "Usage: .\odoo-reload.ps1 -Module your_module [-Db your_db]"
    exit 1
}

Write-Host "→ Updating module: $Module"

docker exec odoo19_app odoo -u $Module -d $Db --stop-after-init

Write-Host "→ Restarting Odoo..."
docker restart odoo19_app

Write-Host "Done"