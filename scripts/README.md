# TMC 脚本说明

## 📁 脚本列表

### 版本管理
- **`update-version.ps1`** - 更新项目版本号
  ```powershell
  # 更新版本号为 1.2.0
  .\scripts\update-version.ps1 1.2.0
  ```

- **`sync-version.js`** - 同步 VERSION 文件到 package.json
  ```bash
  # 通常由 update-version.ps1 或 npm prebuild 自动调用
  node scripts/sync-version.js
  ```

### Docker 操作
- **`docker-build-push.ps1`** - 构建并推送 Docker 镜像到 Docker Hub
  ```powershell
  # 构建并推送（自动读取 VERSION 文件）
  .\scripts\docker-build-push.ps1
  ```

## 💡 常用工作流

### 1️⃣ 开发完成后发布新版本

```powershell
# Step 1: 更新版本号
.\scripts\update-version.ps1 1.2.0

# Step 2: 提交并推送到 GitHub
git add .
git commit -m "release: v1.2.0 正式发布"
git push origin main

# Step 3: 创建版本标签
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin v1.2.0

# Step 4: 构建并推送 Docker 镜像
.\scripts\docker-build-push.ps1
```

### 2️⃣ 日常代码提交

```bash
# 添加所有更改
git add .

# 提交（支持中文，GitHub 显示正常）
git commit -m "feat: 添加新功能"

# 推送到 GitHub
git push origin main
```

### 3️⃣ 仅构建 Docker 镜像

```powershell
# 构建并推送到 Docker Hub
.\scripts\docker-build-push.ps1
```

## ⚙️ 提交消息规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>: <subject>

[optional body]
```

### 常用类型
- `feat`: 新功能
- `fix`: 修复问题
- `perf`: 性能优化
- `refactor`: 代码重构
- `style`: 样式调整
- `docs`: 文档更新
- `test`: 测试相关
- `chore`: 构建/工具相关
- `release`: 版本发布

### 示例
```
feat: 添加消息过滤功能
fix: 修复主题切换卡顿问题
perf: 优化日志查询性能
docs: 更新部署文档
release: v1.1.0 正式发布
```

## 🔧 环境要求

- **PowerShell 5.1+** (Windows)
- **Node.js 18+** (用于 sync-version.js)
- **Git** (配置好 user.name 和 user.email)
- **Docker** (用于构建镜像)

## 📝 Git 操作说明

### Git 配置（已自动配置）
项目已配置 UTF-8 编码支持：
```bash
git config i18n.commitencoding utf-8
git config i18n.logoutputencoding utf-8
```

### 提交消息规范
✅ **推荐：直接使用 Git 命令**
- 支持中文提交消息
- GitHub 网页端显示完全正常
- 本地终端可能显示乱码（不影响使用）

```bash
# 中文提交（GitHub 显示正常）
git commit -m "feat: 添加新功能"

# 英文提交（最稳定，参考 Telegram Message v3.2 项目）
git commit -m "feat: add new feature"
```

## 📝 注意事项

1. **版本管理**: VERSION 文件是唯一的版本源，其他地方自动同步
2. **GitHub Actions**: 推送代码后会自动触发 Docker 构建
3. **标签规范**: 版本标签格式为 `v1.2.3`
4. **提交消息**: 直接使用 `git commit -m`，不需要额外脚本

## 🆘 常见问题

### Q: 本地终端提交消息显示乱码？
A: 这是 Windows PowerShell 的显示问题，不影响实际使用。GitHub 网页端显示完全正常。

### Q: Docker 构建失败？
A: 确保 VERSION 文件存在且格式正确（纯数字版本号，如 `1.1.0`）

### Q: 如何回滚版本？
```bash
# 修改 VERSION 文件，然后重新推送
.\scripts\update-version.ps1 1.0.0
git add .
git commit -m "chore: rollback to v1.0.0"
git push origin main
```
