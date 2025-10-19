# Reset Local Development Database
# This script will backup and reset the local database for clean migration

Write-Host "TMC Local Database Reset Tool" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan
Write-Host ""

$DataPath = ".\data\bot.db"
$BackupPath = ".\data\bot.db.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"

# Check if database exists
if (Test-Path $DataPath) {
    Write-Host "[INFO] Current database found: $DataPath" -ForegroundColor Yellow
    
    # Show database info
    $dbSize = (Get-Item $DataPath).Length / 1MB
    Write-Host "       Size: $([math]::Round($dbSize, 2)) MB" -ForegroundColor Gray
    
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Green
    Write-Host "  1. Backup and reset (recommended)" -ForegroundColor White
    Write-Host "  2. Reset without backup (dangerous!)" -ForegroundColor Yellow
    Write-Host "  3. Just backup, no reset" -ForegroundColor White
    Write-Host "  0. Cancel" -ForegroundColor White
    Write-Host ""
    
    $choice = Read-Host "Select option (0-3)"
    
    switch ($choice) {
        "1" {
            Write-Host ""
            Write-Host "[BACKUP] Creating backup..." -ForegroundColor Cyan
            Copy-Item $DataPath $BackupPath
            Write-Host "[OK] Backup created: $BackupPath" -ForegroundColor Green
            
            Write-Host ""
            Write-Host "[RESET] Removing database..." -ForegroundColor Yellow
            Remove-Item $DataPath -Force
            
            # Remove WAL and SHM files
            Remove-Item "$DataPath-wal" -Force -ErrorAction SilentlyContinue
            Remove-Item "$DataPath-shm" -Force -ErrorAction SilentlyContinue
            
            Write-Host "[OK] Database reset complete!" -ForegroundColor Green
            Write-Host ""
            Write-Host "[INFO] On next start, the database will be recreated" -ForegroundColor Cyan
        }
        "2" {
            Write-Host ""
            Write-Host "[WARN] Resetting without backup..." -ForegroundColor Red
            $confirm = Read-Host "Are you sure? Type 'yes' to confirm"
            
            if ($confirm -eq "yes") {
                Remove-Item $DataPath -Force
                Remove-Item "$DataPath-wal" -Force -ErrorAction SilentlyContinue
                Remove-Item "$DataPath-shm" -Force -ErrorAction SilentlyContinue
                Write-Host "[OK] Database reset complete!" -ForegroundColor Green
            } else {
                Write-Host "[INFO] Cancelled" -ForegroundColor Yellow
            }
        }
        "3" {
            Write-Host ""
            Write-Host "[BACKUP] Creating backup..." -ForegroundColor Cyan
            Copy-Item $DataPath $BackupPath
            Write-Host "[OK] Backup created: $BackupPath" -ForegroundColor Green
        }
        "0" {
            Write-Host ""
            Write-Host "[INFO] Cancelled" -ForegroundColor Yellow
        }
        default {
            Write-Host ""
            Write-Host "[ERROR] Invalid option" -ForegroundColor Red
        }
    }
} else {
    Write-Host "[INFO] No database found at: $DataPath" -ForegroundColor Gray
    Write-Host "[INFO] Database will be created on first run" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "=============================" -ForegroundColor Cyan
Write-Host ""

