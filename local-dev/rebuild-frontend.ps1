# =====================================================
# TMC Local Development - Rebuild Frontend
# =====================================================

Write-Host "TMC Frontend Rebuild Tool" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the correct directory
$RootPath = Split-Path -Parent $PSScriptRoot
Set-Location $RootPath

$frontendPath = ".\app\frontend"

if (-not (Test-Path $frontendPath)) {
    Write-Host "[ERROR] Frontend directory not found: $frontendPath" -ForegroundColor Red
    exit 1
}

Write-Host "[INFO] Frontend path: $frontendPath" -ForegroundColor Gray
Write-Host ""

# Check if node_modules exists
if (-not (Test-Path "$frontendPath\node_modules")) {
    Write-Host "[WARN] node_modules not found, running npm install first..." -ForegroundColor Yellow
    Push-Location $frontendPath
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] npm install failed!" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    Pop-Location
    Write-Host "[OK] Dependencies installed" -ForegroundColor Green
    Write-Host ""
}

# Build frontend
Write-Host "[BUILD] Building frontend..." -ForegroundColor Cyan
Write-Host "-----------------------------------" -ForegroundColor Gray
Push-Location $frontendPath

npm run build

if ($LASTEXITCODE -eq 0) {
    Pop-Location
    Write-Host ""
    Write-Host "[SUCCESS] Frontend built successfully!" -ForegroundColor Green
    Write-Host ""
    
    # Show build output
    Write-Host "[INFO] Build output:" -ForegroundColor Cyan
    $distPath = Join-Path $frontendPath "dist\assets"
    if (Test-Path $distPath) {
        $jsFiles = Get-ChildItem $distPath -Filter "index-*.js" | Select-Object Name, Length, LastWriteTime
        $jsFiles | Format-Table -AutoSize
        
        Write-Host ""
        Write-Host "[INFO] If container is running, it will use the new files automatically" -ForegroundColor Cyan
        Write-Host "[INFO] due to volume mounting in docker-compose.local.yml" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "[NEXT] To see changes:" -ForegroundColor Yellow
        Write-Host "  1. Refresh browser (Ctrl+F5 for hard refresh)" -ForegroundColor White
        Write-Host "  2. Or restart container: docker compose -f local-dev/docker-compose.local.yml restart" -ForegroundColor White
    }
} else {
    Pop-Location
    Write-Host ""
    Write-Host "[ERROR] Frontend build failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=========================" -ForegroundColor Cyan

