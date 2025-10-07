# =====================================================
# TMC Docker 构建和推送脚本
# =====================================================
# 自动从 VERSION 文件读取版本号并推送到 Docker Hub

param(
    [switch]$NoPush,
    [switch]$NoCache,
    [string]$Registry = "hav93/tmc"
)

$ErrorActionPreference = "Stop"

# 进入项目根目录
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " TMC Docker Build & Push Tool" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 读取版本号
if (-not (Test-Path "VERSION")) {
    Write-Host "[ERROR] VERSION file not found" -ForegroundColor Red
    exit 1
}

$version = (Get-Content VERSION).Trim()
Write-Host "Version: $version" -ForegroundColor Yellow
Write-Host "Registry: $Registry" -ForegroundColor Yellow
Write-Host ""

# 构建参数
$buildArgs = @("build")
if ($NoCache) {
    $buildArgs += "--no-cache"
}
$buildArgs += @(
    "-t", "$Registry:latest",
    "-t", "$Registry:$version",
    "."
)

# 构建镜像
Write-Host "[1/3] Building Docker image..." -ForegroundColor Green
Write-Host "Tags: $Registry:latest, $Registry:$version" -ForegroundColor Gray
Write-Host ""

docker @buildArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] Docker build failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[2/3] Build completed successfully" -ForegroundColor Green
Write-Host ""

# 显示镜像信息
docker images $Registry --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

Write-Host ""

# 推送镜像
if (-not $NoPush) {
    Write-Host "[3/3] Pushing to Docker Hub..." -ForegroundColor Green
    Write-Host ""
    
    # 推送 latest 标签
    Write-Host "Pushing $Registry:latest..." -ForegroundColor Cyan
    docker push "$Registry:latest"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "[ERROR] Failed to push latest tag" -ForegroundColor Red
        exit 1
    }
    
    # 推送版本标签
    Write-Host ""
    Write-Host "Pushing $Registry:$version..." -ForegroundColor Cyan
    docker push "$Registry:$version"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "[ERROR] Failed to push version tag" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host " Push Completed Successfully" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Available tags:" -ForegroundColor Cyan
    Write-Host "  - $Registry:latest" -ForegroundColor White
    Write-Host "  - $Registry:$version" -ForegroundColor White
    Write-Host ""
    Write-Host "Pull command:" -ForegroundColor Cyan
    Write-Host "  docker pull $Registry:$version" -ForegroundColor Gray
    Write-Host "  docker pull $Registry:latest" -ForegroundColor Gray
    Write-Host ""
} else {
    Write-Host "[3/3] Skipping push (--NoPush flag set)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To push manually:" -ForegroundColor Cyan
    Write-Host "  docker push $Registry:latest" -ForegroundColor Gray
    Write-Host "  docker push $Registry:$version" -ForegroundColor Gray
    Write-Host ""
}

