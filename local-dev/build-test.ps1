# TMC Local Development Build Script
# Simple version for testing

Write-Host "TMC Local Development Build" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check Docker
try {
    docker ps > $null 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Docker is not running" -ForegroundColor Red
        exit 1
    }
    Write-Host "[OK] Docker is running" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker not found" -ForegroundColor Red
    exit 1
}

# Set proxy
$ProxyHost = if ($env:LOCAL_PROXY_HOST) { $env:LOCAL_PROXY_HOST } else { "192.168.31.6:7890" }
Write-Host "[INFO] Proxy: http://$ProxyHost" -ForegroundColor Yellow
$env:HTTP_PROXY = "http://$ProxyHost"
$env:HTTPS_PROXY = "http://$ProxyHost"
$env:NO_PROXY = "localhost,127.0.0.1"

# Show current status
Write-Host ""
Write-Host "Current Status:" -ForegroundColor Cyan
Write-Host "---------------" -ForegroundColor Gray

$containers = docker ps -a --filter "name=tmc-local" --format "{{.Names}}" 2>$null
if ($containers) {
    $status = docker ps -a --filter "name=tmc-local" --format "{{.Status}}" 2>$null
    Write-Host "Container: $containers ($status)" -ForegroundColor White
} else {
    Write-Host "Container: Not created" -ForegroundColor Gray
}

$imageExists = docker images "hav93/tmc:local" -q 2>$null
if ($imageExists) {
    $imageSize = docker images "hav93/tmc:local" --format "{{.Size}}" 2>$null
    Write-Host "Image: hav93/tmc:local ($imageSize)" -ForegroundColor White
} else {
    Write-Host "Image: Not built" -ForegroundColor Gray
}

# Menu
Write-Host ""
Write-Host "Available Commands:" -ForegroundColor Green
Write-Host "  1. Quick build and start (with cache)" -ForegroundColor White
Write-Host "  2. Full rebuild (no cache)" -ForegroundColor White
Write-Host "  3. Start container only" -ForegroundColor White
Write-Host "  4. Stop container" -ForegroundColor White
Write-Host "  5. Restart container" -ForegroundColor White
Write-Host "  6. View logs" -ForegroundColor White
Write-Host "  7. Enter container shell" -ForegroundColor White
Write-Host "  8. Show container status" -ForegroundColor White
Write-Host "  9. Clean up all" -ForegroundColor White
Write-Host "  0. Exit" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Select operation (0-9)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "[BUILD] Quick build and start..." -ForegroundColor Cyan
        Write-Host "-----------------------------------" -ForegroundColor Gray
        
        # Build frontend first
        Write-Host "[FRONTEND] Building frontend..." -ForegroundColor Yellow
        Push-Location app/frontend
        npm run build
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] Frontend build failed!" -ForegroundColor Red
            Pop-Location
            break
        }
        Pop-Location
        Write-Host "[OK] Frontend built successfully" -ForegroundColor Green
        
        # Build and start container
        docker compose -f local-dev/docker-compose.local.yml up -d --build
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "[SUCCESS] Build and start completed!" -ForegroundColor Green
            Write-Host "[INFO] Access: http://localhost:9393" -ForegroundColor Cyan
        }
    }
    "2" {
        Write-Host ""
        Write-Host "[BUILD] Full rebuild (no cache)..." -ForegroundColor Cyan
        Write-Host "-----------------------------------" -ForegroundColor Gray
        Write-Host "[WARN] This will take longer..." -ForegroundColor Yellow
        
        # Build frontend first
        Write-Host "[FRONTEND] Building frontend..." -ForegroundColor Yellow
        Push-Location app/frontend
        npm run build
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] Frontend build failed!" -ForegroundColor Red
            Pop-Location
            break
        }
        Pop-Location
        Write-Host "[OK] Frontend built successfully" -ForegroundColor Green
        
        # Note: Proxy is configured via environment variables if needed
        Write-Host "[INFO] Building without cache (use HTTP_PROXY env var if needed)" -ForegroundColor Gray
        
        docker compose -f local-dev/docker-compose.local.yml build --no-cache
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "[SUCCESS] Build completed! Starting container..." -ForegroundColor Green
            docker compose -f local-dev/docker-compose.local.yml up -d
            if ($LASTEXITCODE -eq 0) {
                Write-Host ""
                Write-Host "[SUCCESS] Started!" -ForegroundColor Green
                Write-Host "[INFO] Access: http://localhost:9393" -ForegroundColor Cyan
            }
        }
    }
    "3" {
        Write-Host ""
        Write-Host "[START] Starting container..." -ForegroundColor Cyan
        Write-Host "-----------------------------------" -ForegroundColor Gray
        docker compose -f local-dev/docker-compose.local.yml up -d
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "[SUCCESS] Started!" -ForegroundColor Green
            Write-Host "[INFO] Access: http://localhost:9393" -ForegroundColor Cyan
        }
    }
    "4" {
        Write-Host ""
        Write-Host "[STOP] Stopping container..." -ForegroundColor Cyan
        Write-Host "-----------------------------------" -ForegroundColor Gray
        docker compose -f local-dev/docker-compose.local.yml down
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "[SUCCESS] Stopped!" -ForegroundColor Green
        }
    }
    "5" {
        Write-Host ""
        Write-Host "[RESTART] Restarting container..." -ForegroundColor Cyan
        Write-Host "-----------------------------------" -ForegroundColor Gray
        docker compose -f local-dev/docker-compose.local.yml restart
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "[SUCCESS] Restarted!" -ForegroundColor Green
            Write-Host "[INFO] Access: http://localhost:9393" -ForegroundColor Cyan
        }
    }
    "6" {
        Write-Host ""
        Write-Host "[LOGS] Viewing logs (Ctrl+C to exit)..." -ForegroundColor Cyan
        Write-Host "-----------------------------------" -ForegroundColor Gray
        docker compose -f local-dev/docker-compose.local.yml logs -f tmc
    }
    "7" {
        Write-Host ""
        Write-Host "[SHELL] Entering container shell..." -ForegroundColor Cyan
        Write-Host "-----------------------------------" -ForegroundColor Gray
        docker compose -f local-dev/docker-compose.local.yml exec tmc /bin/bash
    }
    "8" {
        Write-Host ""
        Write-Host "[STATUS] Container status..." -ForegroundColor Cyan
        Write-Host "-----------------------------------" -ForegroundColor Gray
        docker compose -f local-dev/docker-compose.local.yml ps
        Write-Host ""
        Write-Host "[DISK] Disk usage:" -ForegroundColor Cyan
        docker system df
    }
    "9" {
        Write-Host ""
        Write-Host "[WARN] This will clean all local containers and images!" -ForegroundColor Red
        Write-Host "-----------------------------------" -ForegroundColor Gray
        $confirm = Read-Host "Confirm cleanup? (yes/no)"
        if ($confirm -eq "yes") {
            Write-Host ""
            Write-Host "[CLEANUP] Cleaning up..." -ForegroundColor Yellow
            docker compose -f local-dev/docker-compose.local.yml down -v
            docker rmi hav93/tmc:local -f 2>$null
            Write-Host ""
            Write-Host "[SUCCESS] Cleanup completed!" -ForegroundColor Green
        } else {
            Write-Host ""
            Write-Host "[INFO] Cancelled" -ForegroundColor Yellow
        }
    }
    "0" {
        Write-Host ""
        Write-Host "Goodbye!" -ForegroundColor Cyan
        exit
    }
    default {
        Write-Host ""
        Write-Host "[ERROR] Invalid selection!" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "[DONE] Operation completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Tips:" -ForegroundColor Yellow
Write-Host "  - App URL: http://localhost:9393" -ForegroundColor White
Write-Host "  - View logs: docker compose -f local-dev/docker-compose.local.yml logs -f" -ForegroundColor White
Write-Host "  - Check status: docker compose -f local-dev/docker-compose.local.yml ps" -ForegroundColor White
Write-Host "  - Run again: .\local-dev\build-test.ps1" -ForegroundColor White
Write-Host ""

