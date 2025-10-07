# =====================================================
# Git UTF-8 提交辅助脚本
# =====================================================
# 解决 PowerShell 中文编码问题
# 使用方法: .\scripts\git-commit-utf8.ps1 "提交消息"

param(
    [Parameter(Mandatory=$true)]
    [string]$Message
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

# 创建临时提交消息文件
$msgFile = ".git/COMMIT_MSG_TEMP"
[System.IO.File]::WriteAllText("$PWD\$msgFile", $Message, (New-Object System.Text.UTF8Encoding $false))

# 提交
git commit -F $msgFile

# 清理临时文件
if (Test-Path $msgFile) {
    Remove-Item $msgFile -Force
}

Write-Host ""
Write-Host "Commit created with UTF-8 encoding" -ForegroundColor Green
Write-Host ""
Write-Host "Last commit:" -ForegroundColor Cyan
git log -1 --pretty=format:"%h - %s"
Write-Host ""
Write-Host ""

