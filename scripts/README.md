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

### Git 操作
- **`push-github.ps1`** - 添加、提交并推送代码到 GitHub
  ```powershell
  # 基本提交
  .\scripts\push-github.ps1 "feat: 添加新功能"
  
  # 带版本标签的提交
  .\scripts\push-github.ps1 "release: v1.1.0 正式发布" -Tag "v1.1.0"
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

# Step 2: 推送到 GitHub（带标签）
.\scripts\push-github.ps1 "release: v1.2.0 正式发布" -Tag "v1.2.0"

# Step 3: 构建并推送 Docker 镜像
.\scripts\docker-build-push.ps1
```

### 2️⃣ 日常代码提交

```powershell
# 直接提交推送
.\scripts\push-github.ps1 "fix: 修复登录问题"
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

## 📝 注意事项

1. **UTF-8 编码**: 所有脚本已配置 UTF-8 编码，支持中文提交消息
2. **版本管理**: VERSION 文件是唯一的版本源，其他地方自动同步
3. **GitHub Actions**: 推送代码后会自动触发 Docker 构建
4. **标签规范**: 版本标签格式为 `v1.2.3`

## 🆘 常见问题

### Q: 提交消息出现乱码？
A: 使用 `push-github.ps1` 脚本，它已配置 UTF-8 编码

### Q: Docker 构建失败？
A: 确保 VERSION 文件存在且格式正确（纯数字版本号，如 `1.1.0`）

### Q: 如何回滚版本？
```powershell
# 修改 VERSION 文件，然后重新推送
.\scripts\update-version.ps1 1.0.0
.\scripts\push-github.ps1 "chore: 回滚到 v1.0.0"
```
