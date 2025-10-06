# 批量更新项目链接脚本

Write-Host "🔧 开始更新项目链接..." -ForegroundColor Cyan

# 配置
$GITHUB_USERNAME = "Hav93"
$GITHUB_REPO = "TMC"
$TELEGRAM_GROUP = "tg_message93"

# 需要更新的文件列表
$files = @(
    "DEPLOYMENT.md",
    "GITHUB_SETUP.md",
    "RELEASE_NOTES.md",
    "PUBLISH_CHECKLIST.md"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "📝 更新 $file ..." -ForegroundColor Yellow
        
        # 读取文件内容
        $content = Get-Content $file -Raw
        
        # 替换 GitHub 用户名
        $content = $content -replace 'YOUR_USERNAME', $GITHUB_USERNAME
        
        # 替换 Telegram 群组
        $content = $content -replace 'YOUR_GROUP_LINK', $TELEGRAM_GROUP
        
        # 写回文件
        Set-Content -Path $file -Value $content -NoNewline
        
        Write-Host "  ✓ $file 已更新" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ $file 不存在，跳过" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "✅ 链接更新完成！" -ForegroundColor Green
Write-Host ""
Write-Host "已更新的配置:" -ForegroundColor Cyan
Write-Host "  GitHub: https://github.com/$GITHUB_USERNAME/$GITHUB_REPO"
Write-Host "  Telegram: https://t.me/$TELEGRAM_GROUP"
Write-Host "  Docker Hub: https://hub.docker.com/r/hav93/tmc"

