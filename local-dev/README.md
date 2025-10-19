# TMC 本地开发工具

> 本地开发所需的所有配置和脚本，简化开发流程

**版本：** v1.1.0  
**更新日期：** 2025-10-15

---

## ⚠️ 重要说明

### 前端文件挂载机制

本地开发环境使用**卷挂载**方式：
- 容器直接使用 `app/frontend/dist/` 目录（不构建在镜像内）
- **前端代码更新后，必须重新编译**：
  ```powershell
  .\local-dev\rebuild-frontend.ps1
  ```
- 编译后刷新浏览器即可看到新功能，无需重建镜像

### 代理配置

- 如需使用代理，通过**环境变量**设置：
  ```powershell
  $env:HTTP_PROXY = "http://192.168.31.6:7890"
  $env:HTTPS_PROXY = "http://192.168.31.6:7890"
  ```
- 不需要代理时保持环境变量为空

---

## 📁 文件说明

| 文件 | 用途 | 说明 |
|------|------|------|
| `build-test.ps1` | 交互式构建脚本 | ⭐ 主要开发工具 |
| `rebuild-frontend.ps1` | 前端编译脚本 | 🎨 前端更新时使用 |
| `quick-status.ps1` | 状态检查脚本 | 📊 快速诊断 |
| `docker-compose.local.yml` | Docker配置 | 🐳 容器配置 |
| `env.example` | 环境变量模板 | 📝 配置参考 |

---

## 🚀 快速开始

### 首次使用

1. **检查环境**：
   ```powershell
   .\local-dev\quick-status.ps1
   ```

2. **编译前端**：
   ```powershell
   .\local-dev\rebuild-frontend.ps1
   ```

3. **启动应用**：
   ```powershell
   .\local-dev\build-test.ps1
   # 选择：1 - 快速构建并启动
   ```

4. **访问应用**：
   - URL: http://localhost:9393
   - 用户名: `admin`
   - 密码: `admin123`

### 日常开发

**前端代码更新**：
```powershell
# 1. 重新编译
.\local-dev\rebuild-frontend.ps1

# 2. 刷新浏览器（Ctrl+F5 强制刷新）
```

**后端代码更新**：
```powershell
# 由于卷挂载，代码会自动重载
# 如需重启：
docker compose -f local-dev/docker-compose.local.yml restart
```

**查看日志**：
```powershell
docker compose -f local-dev/docker-compose.local.yml logs -f
```

---

## 📖 命令参考

### rebuild-frontend.ps1

**专门用于编译前端**：

```powershell
.\local-dev\rebuild-frontend.ps1
```

**功能**：
- ✅ 自动检测并安装依赖
- ✅ 编译前端生成 `dist/` 文件
- ✅ 显示构建输出文件信息
- ✅ 容器自动使用新文件

**使用场景**：
- 修改了前端代码（React/TypeScript）
- 拉取了包含前端更新的代码
- 前端页面显示不正常

---

### build-test.ps1

**交互式构建脚本**：

```powershell
.\local-dev\build-test.ps1
```

**菜单选项**：

| 选项 | 功能 | 说明 |
|------|------|------|
| 1 | 快速构建并启动 | ⭐ 自动编译前端 + 构建镜像 |
| 2 | 完全重建（无缓存） | 🔄 解决缓存问题 |
| 3 | 仅启动容器 | ▶️ 快速启动 |
| 4 | 停止容器 | ⏹️ 停止服务 |
| 5 | 重启容器 | 🔁 快速重启 |
| 6 | 查看日志 | 📋 实时日志 |
| 7 | 进入容器Shell | 🔧 调试用 |
| 8 | 查看状态 | 📊 容器/镜像信息 |
| 9 | 清理所有 | 🗑️ 完全重置 |
| 0 | 退出 | |

**选项1和2 新增功能**：
- 自动运行 `npm run build` 编译前端
- 编译失败会提前终止
- 确保容器使用最新前端文件

---

### quick-status.ps1

**快速状态检查**：

```powershell
.\local-dev\quick-status.ps1
```

**显示信息**：
- ✅ Docker 运行状态
- ✅ 容器状态（运行/停止）
- ✅ 镜像信息（大小/创建时间）
- ✅ 代理配置
- ✅ 访问URL

---

## 🔧 代理配置

### 方式一：环境变量（推荐）

```powershell
# 设置代理
$env:HTTP_PROXY = "http://192.168.31.6:7890"
$env:HTTPS_PROXY = "http://192.168.31.6:7890"

# 然后运行构建
.\local-dev\build-test.ps1
```

### 方式二：修改 .env 文件

```bash
# .env
HTTP_PROXY=http://192.168.31.6:7890
HTTPS_PROXY=http://192.168.31.6:7890
```

### 不使用代理

保持环境变量为空或不设置即可。

---

## 🐛 故障排查

### 问题：看不到新功能

**原因**：前端文件是旧的  
**解决**：
```powershell
.\local-dev\rebuild-frontend.ps1
# 然后刷新浏览器（Ctrl+F5）
```

### 问题：容器一直重启

**原因**：数据库迁移问题  
**解决**：
```powershell
# 1. 停止容器
docker compose -f local-dev/docker-compose.local.yml down

# 2. 重置数据库
.\scripts\reset-local-db.ps1

# 3. 重新启动
.\local-dev\build-test.ps1
```

### 问题：构建失败（网络问题）

**原因**：无法访问 Debian/PyPI/npm  
**解决**：
```powershell
# 设置代理
$env:HTTP_PROXY = "http://your-proxy:port"
$env:HTTPS_PROXY = "http://your-proxy:port"

# 重新构建
.\local-dev\build-test.ps1
# 选择：2 - 完全重建
```

### 问题：前端编译失败

**原因**：依赖未安装或版本不对  
**解决**：
```powershell
cd app/frontend
rm -r node_modules
npm install
npm run build
```

### 问题：端口被占用

**原因**：9393端口已被使用  
**解决**：
```powershell
# 查找占用进程
netstat -ano | findstr :9393

# 或修改端口（docker-compose.local.yml）
ports:
  - "9394:9393"  # 改为其他端口
```

---

## 💡 开发技巧

### 1. 热重载

后端代码修改后会自动重载（通过卷挂载）：
- `app/backend/api/`
- `app/backend/services/`
- `app/backend/models.py`
- `app/backend/main.py`

**无需重启容器！**

### 2. 前端开发

前端修改后：
```powershell
# 方式1：使用脚本
.\local-dev\rebuild-frontend.ps1

# 方式2：手动
cd app/frontend
npm run build
```

### 3. 查看实时日志

```powershell
# 所有日志
docker compose -f local-dev/docker-compose.local.yml logs -f

# 只看错误
docker compose -f local-dev/docker-compose.local.yml logs -f | Select-String "ERROR"

# 最后100行
docker compose -f local-dev/docker-compose.local.yml logs --tail=100
```

### 4. 进入容器调试

```powershell
# 使用脚本
.\local-dev\build-test.ps1
# 选择：7 - 进入容器Shell

# 或直接命令
docker exec -it tmc-local /bin/bash

# 在容器内
cd /app
python -c "from models import *; print('Models OK')"
alembic current
```

### 5. 清理磁盘空间

```powershell
# 清理所有未使用的资源
docker system prune -a

# 只清理本项目
.\local-dev\build-test.ps1
# 选择：9 - 清理所有
```

---

## 📚 相关文档

- `docs/DEVELOPMENT_SUMMARY_STAGE1_2_3_4_5.md` - 完整开发文档
- `docs/PROJECT_FILES_ANALYSIS.md` - 项目文件分析
- `docs/BUILD_ISSUES_AND_FIXES.md` - 构建问题记录
- `docs/FRONTEND_BUILD_ISSUE.md` - 前端构建问题分析

---

## 🔄 更新日志

### v1.1.0 (2025-10-15)
- ✨ 新增 `rebuild-frontend.ps1` 前端编译脚本
- 🔧 修复 `docker-compose.local.yml` 代理配置问题
- 📝 更新 `build-test.ps1`，自动编译前端
- 📖 重写 README，添加前端挂载机制说明
- 🐛 移除不兼容的 `network: host` 配置

### v1.0.0 (2025-01-14)
- 🎉 初始版本
- ✅ 交互式构建脚本
- ✅ 状态检查工具
- ✅ Docker Compose 配置

---

**问题反馈**：如遇到问题，请查看日志或提交 Issue
