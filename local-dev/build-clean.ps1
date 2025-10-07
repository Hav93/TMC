# =====================================================
# TMC 完全重新构建脚本（不使用缓存）
# =====================================================

Write-Host "🔨 完全重新构建 TMC（不使用缓存）..." -ForegroundColor Cyan

# 设置代理
$ProxyHost = if ($env:LOCAL_PROXY_HOST) { $env:LOCAL_PROXY_HOST } else { "192.168.31.6:7890" }
Write-Host "📡 代理: http://$ProxyHost" -ForegroundColor Yellow

$env:HTTP_PROXY = "http://$ProxyHost"
$env:HTTPS_PROXY = "http://$ProxyHost"
$env:NO_PROXY = "localhost,127.0.0.1"
$env:BUILD_HTTP_PROXY = "http://$ProxyHost"
$env:BUILD_HTTPS_PROXY = "http://$ProxyHost"

# 进入项目根目录
Set-Location "$PSScriptRoot\.."

# 停止现有容器
Write-Host "🛑 停止现有容器..." -ForegroundColor Yellow
docker compose -f local-dev/docker-compose.local.yml down

# 完全重新构建
Write-Host "🔨 开始构建..." -ForegroundColor Cyan
docker compose -f local-dev/docker-compose.local.yml build --no-cache

# 启动容器
Write-Host "🚀 启动容器..." -ForegroundColor Cyan
docker compose -f local-dev/docker-compose.local.yml up -d

Write-Host "✅ 完成！访问: http://localhost:9393" -ForegroundColor Green

