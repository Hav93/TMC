# =====================================================
# TMC GitHub 推送脚本
# =====================================================
# 功能：添加、提交并推送代码到 GitHub
# 使用方法: .\scripts\push-github.ps1 "提交消息" [-Tag "v1.1.0"]

param(
    [Parameter(Mandatory=$true)]
    [string]$Message,
    
    [Parameter(Mandatory=$false)]
    [string]$Tag = ""
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  TMC GitHub 推送" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Git 状态
Write-Host "[1/5] 检查 Git 状态..." -ForegroundColor Yellow
$status = git status --short
if ([string]::IsNullOrEmpty($status)) {
    Write-Host "  ℹ 没有需要提交的更改" -ForegroundColor Yellow
    exit 0
}

Write-Host $status
Write-Host ""

# 添加文件
Write-Host "[2/5] 添加文件到 Git..." -ForegroundColor Yellow
git add .
Write-Host "  ✓ 文件已添加" -ForegroundColor Green
Write-Host ""

# 提交（使用 UTF-8 编码）
Write-Host "[3/5] 提交更改..." -ForegroundColor Yellow
$msgFile = ".git\COMMIT_MSG_TEMP"
[System.IO.File]::WriteAllText("$PWD\$msgFile", $Message, (New-Object System.Text.UTF8Encoding $false))
git commit -F $msgFile

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ 提交成功" -ForegroundColor Green
    
    # 清理临时文件
    if (Test-Path $msgFile) {
        Remove-Item $msgFile -Force
    }
} else {
    Write-Host "  ❌ 提交失败" -ForegroundColor Red
    if (Test-Path $msgFile) {
        Remove-Item $msgFile -Force
    }
    exit 1
}
Write-Host ""

# 推送到 GitHub
Write-Host "[4/5] 推送到 GitHub..." -ForegroundColor Yellow
git push origin main

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ❌ 推送失败" -ForegroundColor Red
    exit 1
}
Write-Host "  ✓ 代码推送成功" -ForegroundColor Green
Write-Host ""

# 创建并推送标签（可选）
if (-not [string]::IsNullOrEmpty($Tag)) {
    Write-Host "[5/5] 创建并推送标签 $Tag..." -ForegroundColor Yellow
    git tag -a $Tag -m "Release $Tag"
    git push origin $Tag
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ 标签推送成功" -ForegroundColor Green
    } else {
        Write-Host "  ❌ 标签推送失败" -ForegroundColor Red
    }
} else {
    Write-Host "[5/5] 跳过标签创建" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✅ 推送完成" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "最近提交:" -ForegroundColor Cyan
git log -1 --pretty=format:"%h - %s" --encoding=utf-8
Write-Host ""
Write-Host ""
Write-Host "📊 项目信息:" -ForegroundColor Cyan
Write-Host "  GitHub:     https://github.com/Hav93/TMC" -ForegroundColor White
Write-Host "  Docker Hub: https://hub.docker.com/r/hav93/tmc" -ForegroundColor White
Write-Host "  Telegram:   https://t.me/tg_message93" -ForegroundColor White
Write-Host ""

