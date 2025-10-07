# =====================================================
# TMC 快速构建脚本（使用代理）
# =====================================================

Write-Host "🚀 快速构建 TMC（使用代理）..." -ForegroundColor Cyan

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

# 构建并启动
docker compose -f local-dev/docker-compose.local.yml up -d --build

Write-Host "✅ 完成！访问: http://localhost:9393" -ForegroundColor Green

