# =====================================================
# TMC 本地开发构建脚本
# =====================================================

Write-Host "🚀 TMC 本地开发环境构建脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 设置代理（自动从环境变量读取或使用默认值）
$ProxyHost = if ($env:LOCAL_PROXY_HOST) { $env:LOCAL_PROXY_HOST } else { "192.168.31.6:7890" }

Write-Host "📡 配置代理: http://$ProxyHost" -ForegroundColor Yellow
$env:HTTP_PROXY = "http://$ProxyHost"
$env:HTTPS_PROXY = "http://$ProxyHost"
$env:NO_PROXY = "localhost,127.0.0.1"
$env:BUILD_HTTP_PROXY = "http://$ProxyHost"
$env:BUILD_HTTPS_PROXY = "http://$ProxyHost"

# 进入项目根目录
Set-Location "$PSScriptRoot\.."

# 显示可用命令
Write-Host ""
Write-Host "可用命令:" -ForegroundColor Green
Write-Host "  1. 快速构建并启动 (使用缓存)" -ForegroundColor White
Write-Host "  2. 完全重新构建 (不使用缓存)" -ForegroundColor White
Write-Host "  3. 仅启动容器" -ForegroundColor White
Write-Host "  4. 停止容器" -ForegroundColor White
Write-Host "  5. 查看日志" -ForegroundColor White
Write-Host "  6. 进入容器Shell" -ForegroundColor White
Write-Host "  7. 清理所有容器和镜像" -ForegroundColor White
Write-Host "  0. 退出" -ForegroundColor White
Write-Host ""

$choice = Read-Host "请选择操作 (0-7)"

switch ($choice) {
    "1" {
        Write-Host "🔨 快速构建并启动..." -ForegroundColor Cyan
        docker compose -f local-dev/docker-compose.local.yml up -d --build
    }
    "2" {
        Write-Host "🔨 完全重新构建（不使用缓存）..." -ForegroundColor Cyan
        docker compose -f local-dev/docker-compose.local.yml build --no-cache
        Write-Host "✅ 构建完成！现在启动容器..." -ForegroundColor Green
        docker compose -f local-dev/docker-compose.local.yml up -d
    }
    "3" {
        Write-Host "🚀 启动容器..." -ForegroundColor Cyan
        docker compose -f local-dev/docker-compose.local.yml up -d
    }
    "4" {
        Write-Host "🛑 停止容器..." -ForegroundColor Cyan
        docker compose -f local-dev/docker-compose.local.yml down
    }
    "5" {
        Write-Host "📋 查看日志（Ctrl+C 退出）..." -ForegroundColor Cyan
        docker compose -f local-dev/docker-compose.local.yml logs -f tmc
    }
    "6" {
        Write-Host "💻 进入容器Shell..." -ForegroundColor Cyan
        docker compose -f local-dev/docker-compose.local.yml exec tmc /bin/bash
    }
    "7" {
        Write-Host "⚠️  警告：将清理所有本地容器和镜像！" -ForegroundColor Red
        $confirm = Read-Host "确认清理? (yes/no)"
        if ($confirm -eq "yes") {
            docker compose -f local-dev/docker-compose.local.yml down -v
            docker rmi hav93/tmc:local -f
            Write-Host "✅ 清理完成！" -ForegroundColor Green
        } else {
            Write-Host "❌ 已取消" -ForegroundColor Yellow
        }
    }
    "0" {
        Write-Host "👋 再见！" -ForegroundColor Cyan
        exit
    }
    default {
        Write-Host "❌ 无效选择！" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "✅ 操作完成！" -ForegroundColor Green
Write-Host "📝 访问应用: http://localhost:9393" -ForegroundColor Cyan
Write-Host "📊 查看状态: docker compose -f local-dev/docker-compose.local.yml ps" -ForegroundColor Cyan

