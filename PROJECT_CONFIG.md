# 项目配置信息

在发布到 GitHub 之前，请修改以下配置：

---

## 📝 需要修改的地方

### 1. GitHub 仓库地址
在以下文件中，将 `YOUR_USERNAME` 替换为你的 GitHub 用户名：

- `README.md`
  - Line 279: `https://t.me/YOUR_GROUP_LINK`
  - Line 283: `https://github.com/YOUR_USERNAME/tmc/issues`
  - Line 284: `https://github.com/YOUR_USERNAME/tmc/issues/new`

- `DEPLOYMENT.md`
  - 搜索并替换所有 `YOUR_USERNAME`

- `GITHUB_SETUP.md`
  - 搜索并替换所有 `YOUR_USERNAME`

- `RELEASE_NOTES.md`
  - 搜索并替换所有 `YOUR_USERNAME`

### 2. Telegram 交流群链接
在 `README.md` 中修改：
```markdown
https://t.me/YOUR_GROUP_LINK
```
替换为你的实际 Telegram 群组链接，例如：
```markdown
https://t.me/tmc_community
```

### 3. Docker Hub 镜像名
确认 Docker Hub 用户名为 `hav93`，如需修改：

在以下文件中搜索并替换 `hav93/tmc`:
- `docker-compose.yml`
- `.github/workflows/docker-build.yml`
- `README.md`
- `DEPLOYMENT.md`

---

## 🔧 快速替换脚本

### PowerShell 批量替换

```powershell
# 设置你的配置
$GITHUB_USERNAME = "your_github_username"
$TELEGRAM_GROUP = "your_telegram_group"
$DOCKER_USERNAME = "hav93"

# 替换 GitHub 用户名
Get-ChildItem -Path . -Include *.md -Recurse | ForEach-Object {
    (Get-Content $_.FullName) -replace 'YOUR_USERNAME', $GITHUB_USERNAME | Set-Content $_.FullName
}

# 替换 Telegram 群组链接
Get-ChildItem -Path . -Include *.md -Recurse | ForEach-Object {
    (Get-Content $_.FullName) -replace 'YOUR_GROUP_LINK', $TELEGRAM_GROUP | Set-Content $_.FullName
}

Write-Host "✅ 配置替换完成！"
```

### 手动替换清单

- [ ] GitHub 仓库地址
- [ ] Telegram 交流群链接
- [ ] Docker Hub 用户名（如需修改）
- [ ] 项目描述和介绍（可选）

---

## 📋 当前配置

```yaml
github:
  username: YOUR_USERNAME  # 待修改
  repo: tmc
  
telegram:
  group: YOUR_GROUP_LINK   # 待修改
  
docker:
  username: hav93
  image: hav93/tmc
  
version: 1.0.0
```

---

## ✅ 验证清单

发布前确认：
- [ ] 收款码图片已复制 (`docs/images/wechat-donate.jpg`)
- [ ] GitHub 用户名已替换
- [ ] Telegram 群链接已更新
- [ ] Docker Hub 配置正确
- [ ] 所有文档链接可访问
- [ ] 版本号一致 (v1.0.0)

---

**修改完成后，删除此文件或移动到 `_archived` 目录**

