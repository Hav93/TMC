# TMC v1.0.0 推送到 GitHub
# 仓库: https://github.com/Hav93/TMC

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  TMC v1.0.0 - 推送到 GitHub" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 配置
$REPO_URL = "https://github.com/Hav93/TMC.git"
$REPO_NAME = "TMC"

# 检查收款码图片
Write-Host "[1/6] 检查必要文件..." -ForegroundColor Yellow
if (-not (Test-Path "docs\images\wechat-donate.jpg")) {
    Write-Host "  ❌ 错误：未找到收款码图片！" -ForegroundColor Red
    exit 1
}
Write-Host "  ✓ 收款码图片已准备" -ForegroundColor Green

# 初始化 Git
Write-Host ""
Write-Host "[2/6] 初始化 Git 仓库..." -ForegroundColor Yellow
if (-not (Test-Path ".git")) {
    git init
    git branch -M main
    Write-Host "  ✓ Git 仓库已初始化" -ForegroundColor Green
} else {
    Write-Host "  ✓ Git 仓库已存在" -ForegroundColor Green
}

# 配置远程仓库
Write-Host ""
Write-Host "[3/6] 配置远程仓库..." -ForegroundColor Yellow
$remotes = git remote
if ($remotes -contains "origin") {
    git remote set-url origin $REPO_URL
    Write-Host "  ✓ 远程仓库已更新" -ForegroundColor Green
} else {
    git remote add origin $REPO_URL
    Write-Host "  ✓ 远程仓库已添加" -ForegroundColor Green
}

Write-Host "  仓库地址: $REPO_URL" -ForegroundColor Cyan

# 添加文件
Write-Host ""
Write-Host "[4/6] 添加文件到 Git..." -ForegroundColor Yellow
git add .
Write-Host "  ✓ 文件已添加" -ForegroundColor Green

# 提交
Write-Host ""
Write-Host "[5/6] 提交更改..." -ForegroundColor Yellow
git commit -m "🎉 Release v1.0.0 - First production-ready version

Features:
✨ Complete Telegram message forwarding system
✨ Multi-client management with enhanced bot
✨ Flexible forwarding rules (keywords, replacements)
✨ Real-time logging and monitoring
✨ Modern responsive UI with dark/light theme
✨ JWT authentication system
✨ Docker Hub auto-build (multi-arch)

Improvements:
🎨 Unified theme color system
🎨 View Transitions API animations
📁 Optimized project structure
📝 Complete documentation
🔧 GitHub Actions CI/CD

Security:
🔐 Fixed authentication issues
🔐 Secure JWT token management
🔐 Database migration system

Community:
💬 Telegram Group: https://t.me/tg_message93
🐛 GitHub Issues: https://github.com/Hav93/TMC/issues
💖 WeChat Donate Support

Docker:
🐳 Docker Hub: hav93/tmc
🏗️ Multi-arch support (amd64, arm64)
"

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ 提交成功" -ForegroundColor Green
} else {
    Write-Host "  ℹ 没有新的更改需要提交" -ForegroundColor Yellow
}

# 推送
Write-Host ""
Write-Host "[6/6] 推送到 GitHub..." -ForegroundColor Yellow
Write-Host "  正在推送主分支..." -ForegroundColor Cyan
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ 主分支推送成功！" -ForegroundColor Green
    
    # 创建并推送标签
    Write-Host ""
    Write-Host "  创建版本标签 v1.0.0..." -ForegroundColor Cyan
    git tag -a v1.0.0 -m "Release v1.0.0

First production-ready version of TMC.

🎉 Major Features:
- Complete Telegram message forwarding
- Multi-client management
- Modern responsive UI
- Docker Hub integration

📖 Documentation:
- See RELEASE_NOTES.md for details
- Visit https://github.com/Hav93/TMC

💬 Community:
- Telegram: https://t.me/tg_message93
- Docker Hub: https://hub.docker.com/r/hav93/tmc
"
    
    git push origin v1.0.0
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ 标签推送成功！" -ForegroundColor Green
        
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  🎉 发布成功！" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "📊 项目信息:" -ForegroundColor Cyan
        Write-Host "  GitHub:     https://github.com/Hav93/TMC" -ForegroundColor White
        Write-Host "  Telegram:   https://t.me/tg_message93" -ForegroundColor White
        Write-Host "  Docker Hub: https://hub.docker.com/r/hav93/tmc" -ForegroundColor White
        Write-Host ""
        Write-Host "🚀 下一步:" -ForegroundColor Yellow
        Write-Host "  1. 访问 GitHub Actions 查看构建状态"
        Write-Host "  2. 等待 Docker 镜像构建完成 (约10-15分钟)"
        Write-Host "  3. 在 GitHub 创建 Release (可选)"
        Write-Host "  4. 在 Telegram 群组发布更新通知"
        Write-Host ""
    } else {
        Write-Host "  ❌ 标签推送失败！" -ForegroundColor Red
    }
} else {
    Write-Host "  ❌ 推送失败！" -ForegroundColor Red
    Write-Host ""
    Write-Host "请检查:" -ForegroundColor Yellow
    Write-Host "  1. 网络连接是否正常"
    Write-Host "  2. GitHub 仓库是否已创建"
    Write-Host "  3. 是否有推送权限"
    Write-Host ""
}

