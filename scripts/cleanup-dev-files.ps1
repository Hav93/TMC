#!/usr/bin/env pwsh
# TMC项目开发文件清理脚本
# 用途：清理开发过程中产生的临时文件、缓存和测试文件

Write-Host "🧹 TMC项目文件清理脚本" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

$rootPath = Split-Path -Parent $PSScriptRoot

# 统计信息
$deletedFiles = 0
$deletedDirs = 0
$freedSpace = 0

function Remove-ItemSafely {
    param(
        [string]$Path,
        [string]$Description
    )
    
    if (Test-Path $Path) {
        try {
            $size = (Get-ChildItem $Path -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
            Remove-Item -Path $Path -Recurse -Force -ErrorAction Stop
            $script:deletedDirs++
            $script:freedSpace += $size
            Write-Host "✅ 已删除: $Description" -ForegroundColor Green
            return $true
        } catch {
            Write-Host "❌ 删除失败: $Description - $($_.Exception.Message)" -ForegroundColor Red
            return $false
        }
    } else {
        Write-Host "⏭️  跳过: $Description (不存在)" -ForegroundColor Yellow
        return $false
    }
}

Write-Host "1️⃣  清理Python缓存..." -ForegroundColor Cyan
Write-Host "-----------------------------------"

# 查找并删除所有__pycache__目录
$pycacheDirs = Get-ChildItem -Path $rootPath -Include __pycache__ -Recurse -Directory -Force -ErrorAction SilentlyContinue
foreach ($dir in $pycacheDirs) {
    if (Remove-ItemSafely -Path $dir.FullName -Description "Python缓存: $($dir.FullName.Replace($rootPath, ''))") {
        # 已在函数中统计
    }
}

# 删除.pyc文件
$pycFiles = Get-ChildItem -Path $rootPath -Filter "*.pyc" -Recurse -File -Force -ErrorAction SilentlyContinue
foreach ($file in $pycFiles) {
    try {
        $size = $file.Length
        Remove-Item -Path $file.FullName -Force
        $deletedFiles++
        $freedSpace += $size
    } catch {
        Write-Host "❌ 删除失败: $($file.FullName)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "2️⃣  清理前端测试文件..." -ForegroundColor Cyan
Write-Host "-----------------------------------"

# 删除测试文件
$testFiles = @(
    "app/frontend/src/pages/MediaMonitor/MonitorRuleFormTest.tsx",
    "app/frontend/src/pages/Settings/Pan115Settings.test.tsx"
)

foreach ($file in $testFiles) {
    $fullPath = Join-Path $rootPath $file
    if (Test-Path $fullPath) {
        try {
            $size = (Get-Item $fullPath).Length
            Remove-Item -Path $fullPath -Force
            $deletedFiles++
            $freedSpace += $size
            Write-Host "✅ 已删除: $file" -ForegroundColor Green
        } catch {
            Write-Host "❌ 删除失败: $file" -ForegroundColor Red
        }
    }
}

# 删除__tests__目录
$testDirs = @(
    "app/frontend/src/services/__tests__",
    "app/frontend/src/stores/__tests__",
    "app/frontend/src/pages/Dashboard/components/__tests__"
)

foreach ($dir in $testDirs) {
    $fullPath = Join-Path $rootPath $dir
    Remove-ItemSafely -Path $fullPath -Description "测试目录: $dir" | Out-Null
}

Write-Host ""
Write-Host "3️⃣  清理后端开发工具..." -ForegroundColor Cyan
Write-Host "-----------------------------------"

$devFiles = @(
    "app/backend/check_migrations.py"
)

foreach ($file in $devFiles) {
    $fullPath = Join-Path $rootPath $file
    if (Test-Path $fullPath) {
        try {
            $size = (Get-Item $fullPath).Length
            Remove-Item -Path $fullPath -Force
            $deletedFiles++
            $freedSpace += $size
            Write-Host "✅ 已删除: $file" -ForegroundColor Green
        } catch {
            Write-Host "❌ 删除失败: $file" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "4️⃣  清理日志文件..." -ForegroundColor Cyan
Write-Host "-----------------------------------"

# 清理日志（保留最近的）
$logDirs = @(
    "logs",
    "app/backend/logs"
)

foreach ($dir in $logDirs) {
    $fullPath = Join-Path $rootPath $dir
    if (Test-Path $fullPath) {
        $logFiles = Get-ChildItem -Path $fullPath -Filter "*.log" -File -ErrorAction SilentlyContinue
        foreach ($logFile in $logFiles) {
            # 只删除7天前的日志
            if ($logFile.LastWriteTime -lt (Get-Date).AddDays(-7)) {
                try {
                    $size = $logFile.Length
                    Remove-Item -Path $logFile.FullName -Force
                    $deletedFiles++
                    $freedSpace += $size
                    Write-Host "✅ 已删除旧日志: $($logFile.Name)" -ForegroundColor Green
                } catch {
                    Write-Host "❌ 删除失败: $($logFile.Name)" -ForegroundColor Red
                }
            }
        }
    }
}

Write-Host ""
Write-Host "5️⃣  清理临时文件..." -ForegroundColor Cyan
Write-Host "-----------------------------------"

$tempDirs = @(
    "temp"
)

foreach ($dir in $tempDirs) {
    $fullPath = Join-Path $rootPath $dir
    if (Test-Path $fullPath) {
        $tempFiles = Get-ChildItem -Path $fullPath -Recurse -File -ErrorAction SilentlyContinue
        foreach ($file in $tempFiles) {
            try {
                $size = $file.Length
                Remove-Item -Path $file.FullName -Force
                $deletedFiles++
                $freedSpace += $size
            } catch {
                # 忽略错误
            }
        }
        if ($tempFiles.Count -gt 0) {
            Write-Host "✅ 已清理临时文件: $($tempFiles.Count) 个" -ForegroundColor Green
        }
    }
}

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "🎉 清理完成！" -ForegroundColor Green
Write-Host ""
Write-Host "📊 清理统计：" -ForegroundColor Cyan
Write-Host "  - 删除文件数: $deletedFiles" -ForegroundColor White
Write-Host "  - 删除目录数: $deletedDirs" -ForegroundColor White
Write-Host "  - 释放空间: $([math]::Round($freedSpace / 1MB, 2)) MB" -ForegroundColor White
Write-Host ""
Write-Host "💡 提示：" -ForegroundColor Yellow
Write-Host "  - Python缓存会在运行时自动重新生成" -ForegroundColor Gray
Write-Host "  - 测试文件已删除，不影响生产环境" -ForegroundColor Gray
Write-Host "  - 7天前的日志已清理" -ForegroundColor Gray
Write-Host ""

