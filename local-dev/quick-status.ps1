# Quick status check for TMC local development

Write-Host "TMC Local Development - Status Check" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check Docker
Write-Host "[1/4] Checking Docker..." -ForegroundColor Yellow
try {
    docker ps > $null 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  [OK] Docker is running" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] Docker is not running" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "  [ERROR] Docker not found" -ForegroundColor Red
    exit 1
}

# Check container
Write-Host "[2/4] Checking container..." -ForegroundColor Yellow
$container = docker ps -a --filter "name=tmc-local" --format "{{.Names}}" 2>$null
if ($container) {
    $status = docker ps --filter "name=tmc-local" --format "{{.Status}}" 2>$null
    if ($status) {
        Write-Host "  [OK] Container: $container (Running)" -ForegroundColor Green
        Write-Host "       Status: $status" -ForegroundColor Gray
    } else {
        Write-Host "  [WARN] Container: $container (Stopped)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  [INFO] Container not created yet" -ForegroundColor Gray
}

# Check image
Write-Host "[3/4] Checking image..." -ForegroundColor Yellow
$imageId = docker images "hav93/tmc:local" -q 2>$null
if ($imageId) {
    $imageSize = docker images "hav93/tmc:local" --format "{{.Size}}" 2>$null
    Write-Host "  [OK] Image: hav93/tmc:local" -ForegroundColor Green
    Write-Host "       Size: $imageSize" -ForegroundColor Gray
} else {
    Write-Host "  [INFO] Image not built yet" -ForegroundColor Gray
}

# Check proxy
Write-Host "[4/4] Checking proxy..." -ForegroundColor Yellow
$ProxyHost = if ($env:LOCAL_PROXY_HOST) { $env:LOCAL_PROXY_HOST } else { "192.168.31.6:7890" }
Write-Host "  [INFO] Proxy: http://$ProxyHost" -ForegroundColor Gray

# Summary
Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Summary:" -ForegroundColor Cyan
Write-Host "  - Docker: OK" -ForegroundColor Green

if ($container) {
    Write-Host "  - Container: Exists" -ForegroundColor Green
} else {
    Write-Host "  - Container: Not created" -ForegroundColor Gray
}

if ($imageId) {
    Write-Host "  - Image: Built" -ForegroundColor Green
} else {
    Write-Host "  - Image: Not built" -ForegroundColor Gray
}

Write-Host ""

if ($container -and $status) {
    Write-Host "App is accessible at: http://localhost:9393" -ForegroundColor Cyan
} else {
    Write-Host "To start the app, run:" -ForegroundColor Yellow
    Write-Host "  .\local-dev\build-test.ps1" -ForegroundColor White
}

Write-Host ""

