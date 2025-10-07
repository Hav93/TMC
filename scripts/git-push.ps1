# TMC 项目 Git 推送脚本
# 使用前请确保：
# 1. 已将微信收款码图片保存为 docs/images/wechat-donate.jpg
# 2. 已在 GitHub 创建仓库
# 3. 已配置好 GitHub SSH 或 HTTPS 访问

param(
    [string]$RepoUrl = "",
    [switch]$Help
)

if ($Help -or [string]::IsNullOrEmpty($RepoUrl)) {
    Write-Host @"
使用方法:
    .\git-push.ps1 -RepoUrl "https://github.com/YOUR_USERNAME/tmc.git"

或使用 SSH:
    .\git-push.ps1 -RepoUrl "git@github.com:YOUR_USERNAME/tmc.git"

参数:
    -RepoUrl    GitHub 仓库地址（必填）
    -Help       显示此帮助信息

示例:
    .\git-push.ps1 -RepoUrl "https://github.com/hav93/tmc.git"
"@
    exit 0
}

Write-Host "🚀 开始准备推送到 GitHub..." -ForegroundColor Cyan
Write-Host ""

# 检查微信收款码是否存在
$donateImage = "docs/images/wechat-donate.jpg"
if (-not (Test-Path $donateImage)) {
    Write-Host "⚠️  警告：未找到微信收款码图片！" -ForegroundColor Yellow
    Write-Host "   请将微信收款码保存为: $donateImage" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "是否继续推送？(y/N)"
    if ($continue -ne 'y' -and $continue -ne 'Y') {
        Write-Host "已取消推送" -ForegroundColor Red
        exit 1
    }
}

# 检查 Git 是否初始化
if (-not (Test-Path ".git")) {
    Write-Host "📦 初始化 Git 仓库..." -ForegroundColor Yellow
    git init
    git branch -M main
}

# 检查是否已添加远程仓库
$remotes = git remote
if ($remotes -notcontains "origin") {
    Write-Host "🔗 添加远程仓库..." -ForegroundColor Yellow
    git remote add origin $RepoUrl
} else {
    Write-Host "🔗 更新远程仓库地址..." -ForegroundColor Yellow
    git remote set-url origin $RepoUrl
}

Write-Host ""
Write-Host "📝 显示仓库信息:" -ForegroundColor Cyan
git remote -v

Write-Host ""
Write-Host "📋 准备提交的文件:" -ForegroundColor Cyan

# 添加所有文件
git add .

# 显示状态
git status --short

Write-Host ""
$commit = Read-Host "是否继续提交并推送？(y/N)"
if ($commit -ne 'y' -and $commit -ne 'Y') {
    Write-Host "已取消推送" -ForegroundColor Red
    exit 1
}

# 提交
Write-Host ""
Write-Host "💾 提交更改..." -ForegroundColor Yellow
git commit -m "🎉 Release v1.0.0 - First production-ready version

Features:
- Complete Telegram message forwarding system
- Multi-client management with enhanced bot support
- Flexible forwarding rules (keywords, replacements)
- Real-time logging and monitoring
- Modern responsive UI with smooth dark/light theme switching
- JWT authentication and user management
- Docker Hub auto-build with multi-arch support (amd64, arm64)

Improvements:
- Unified theme color system with View Transitions API
- Optimized project structure with archived dev files
- Complete deployment documentation
- GitHub Actions CI/CD pipeline

Security:
- Fixed authentication issues (container logs, system status)
- Secure JWT token management
- Database migration system

Documentation:
- Comprehensive README with donation support
- Deployment guide (DEPLOYMENT.md)
- GitHub setup guide (GITHUB_SETUP.md)
- Release notes and changelog
- Publish checklist

Infrastructure:
- Production-ready docker-compose.yml
- Multi-architecture Docker builds
- Automated Docker Hub publishing
- Health checks and restart policies
"

# 推送到 GitHub
Write-Host ""
Write-Host "🚀 推送到 GitHub..." -ForegroundColor Yellow
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ 代码推送成功！" -ForegroundColor Green
    
    # 创建并推送标签
    Write-Host ""
    Write-Host "🏷️  创建版本标签..." -ForegroundColor Yellow
    git tag -a v1.0.0 -m "Release v1.0.0

First production-ready version of TMC.

See RELEASE_NOTES.md for complete release notes.
"
    
    git push origin v1.0.0
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ 标签推送成功！" -ForegroundColor Green
        Write-Host ""
        Write-Host "🎉 发布完成！" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "下一步:" -ForegroundColor Yellow
        Write-Host "  1. 访问 GitHub Actions 查看构建状态"
        Write-Host "  2. 等待 Docker 镜像构建完成（约10-15分钟）"
        Write-Host "  3. 访问 Docker Hub 验证镜像: https://hub.docker.com/r/hav93/tmc"
        Write-Host "  4. 在 GitHub 创建 Release（可选）"
        Write-Host ""
    } else {
        Write-Host ""
        Write-Host "❌ 标签推送失败！" -ForegroundColor Red
        Write-Host "请检查错误信息并重试" -ForegroundColor Red
    }
} else {
    Write-Host ""
    Write-Host "❌ 推送失败！" -ForegroundColor Red
    Write-Host "请检查:" -ForegroundColor Yellow
    Write-Host "  1. GitHub 仓库地址是否正确"
    Write-Host "  2. 是否有推送权限"
    Write-Host "  3. 网络连接是否正常"
    Write-Host "  4. 是否已配置 Git 用户信息"
    Write-Host ""
    Write-Host "配置 Git 用户信息:" -ForegroundColor Cyan
    Write-Host '  git config --global user.name "Your Name"'
    Write-Host '  git config --global user.email "your.email@example.com"'
}

