# TMC 版本管理系统

## 📋 概述

TMC 采用**统一版本管理**机制，所有版本号都从单一的 `VERSION` 文件中读取，确保项目各部分版本号的一致性。

---

## 🏗️ 架构设计

### 版本号流转图

```
VERSION 文件 (唯一真实来源)
    ↓
    ├─→ 后端运行时读取
    │   └─→ app/backend/version.py
    │       └─→ app/backend/config.py (APP_VERSION, APP_DESCRIPTION)
    │
    └─→ 前端构建时同步
        └─→ scripts/sync-version.js
            └─→ app/frontend/package.json
```

### 核心文件

| 文件 | 作用 | 更新方式 |
|------|------|----------|
| `VERSION` | 版本号唯一来源 | 手动或脚本更新 |
| `app/backend/version.py` | 后端版本读取模块 | 运行时动态读取 |
| `app/backend/config.py` | 后端配置（使用版本） | 自动从 `version.py` 获取 |
| `app/frontend/package.json` | 前端包版本 | 构建时自动同步 |
| `scripts/sync-version.js` | 版本同步脚本 | 前端构建时自动调用 |
| `scripts/update-version.ps1` | 版本更新工具 | 手动调用 |

---

## 🚀 使用方法

### 方法一：使用自动化脚本（推荐）

```powershell
# 更新版本号到 1.2.0
.\scripts\update-version.ps1 1.2.0
```

**脚本会自动完成：**
1. ✅ 更新 `VERSION` 文件
2. ✅ 同步 `app/frontend/package.json`
3. ✅ 验证环境配置

**执行后需要手动：**
1. 更新 `CHANGELOG.md` 添加版本变更记录
2. 更新 `README.md` 的版本说明
3. 更新 `DEPLOYMENT.md` 的版本信息
4. 提交代码并打标签

### 方法二：手动更新

```powershell
# 1. 更新 VERSION 文件
echo "1.2.0" > VERSION

# 2. 同步到前端
node scripts/sync-version.js

# 3. 验证
python -c "import sys; sys.path.insert(0, 'app/backend'); from version import get_version; print(get_version())"
```

---

## 📝 版本号规范

遵循 **[语义化版本 2.0.0](https://semver.org/lang/zh-CN/)** 规范：

```
主版本号.次版本号.修订号
   X   .   Y   .  Z
```

### 版本号递增规则

| 类型 | 说明 | 示例 |
|------|------|------|
| **主版本号 (X)** | 不兼容的 API 修改 | `1.0.0` → `2.0.0` |
| **次版本号 (Y)** | 向下兼容的功能性新增 | `1.0.0` → `1.1.0` |
| **修订号 (Z)** | 向下兼容的问题修正 | `1.0.0` → `1.0.1` |

### 实际案例

```
1.0.0  初始版本发布
1.0.1  修复消息转发 Bug
1.1.0  新增消息日志功能
1.1.1  优化日志显示
2.0.0  重构客户端管理架构（不兼容旧版）
```

---

## 🔄 完整更新流程

### 1. 更新版本号

```powershell
.\scripts\update-version.ps1 1.2.0
```

### 2. 更新文档

#### CHANGELOG.md

```markdown
## [1.2.0] - 2025-10-08 ✨

### 新功能
- 添加 XXX 功能

### 修复
- 修复 YYY 问题

### 优化
- 优化 ZZZ 性能
```

#### README.md

```markdown
### v1.2.0 (2025-10-08)
- 新增 XXX 功能
- 修复 YYY 问题
```

#### DEPLOYMENT.md

```markdown
**当前版本**: v1.2.0
**镜像版本**: hav93/tmc:latest, hav93/tmc:1.2.0
```

### 3. 提交代码

```bash
git add .
git commit -m "chore: bump version to 1.2.0"
```

### 4. 打标签

```bash
git tag v1.2.0
git tag -a v1.2.0 -m "Release v1.2.0"  # 附注标签（推荐）
```

### 5. 推送

```bash
git push
git push --tags
```

---

## 🛠️ 技术实现

### 后端版本读取

**`app/backend/version.py`:**

```python
import os

def get_version():
    """从 VERSION 文件读取版本号"""
    version_file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
        'VERSION'
    )
    try:
        with open(version_file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "unknown"
    except Exception as e:
        print(f"Error reading VERSION file: {e}")
        return "unknown"
```

**`app/backend/config.py`:**

```python
from version import get_version

class Config:
    APP_VERSION = os.getenv('APP_VERSION', get_version())
    APP_DESCRIPTION = os.getenv('APP_DESCRIPTION', f'Telegram消息中心 - TMC v{get_version()}')
```

### 前端版本同步

**`app/frontend/package.json`:**

```json
{
  "scripts": {
    "sync-version": "node ../../scripts/sync-version.js",
    "prebuild": "npm run sync-version",
    "build": "vite build"
  }
}
```

**`scripts/sync-version.js`:**

```javascript
const fs = require('fs');
const path = require('path');

const versionFile = path.join(__dirname, '..', 'VERSION');
const packageFile = path.join(__dirname, '..', 'app', 'frontend', 'package.json');

const version = fs.readFileSync(versionFile, 'utf-8').trim();
const packageJson = JSON.parse(fs.readFileSync(packageFile, 'utf-8'));
packageJson.version = version;

fs.writeFileSync(packageFile, JSON.stringify(packageJson, null, 2) + '\n', 'utf-8');
console.log(`✅ 版本号已更新: ${version}`);
```

### Docker 构建支持

**`Dockerfile`:**

```dockerfile
# 复制版本文件到容器
COPY VERSION /app/VERSION

# 复制后端代码
COPY app/backend/ /app/
```

---

## ✅ 版本验证

### 检查版本一致性

```powershell
# PowerShell
$v1 = Get-Content VERSION
$v2 = (Get-Content app/frontend/package.json | ConvertFrom-Json).version
$v3 = python -c "import sys; sys.path.insert(0, 'app/backend'); from version import get_version; print(get_version(), end='')"

Write-Host "VERSION 文件:    $v1"
Write-Host "package.json:    $v2"
Write-Host "Backend 读取:    $v3"

if ($v1 -eq $v2 -and $v2 -eq $v3) {
    Write-Host "✅ 所有版本号一致！" -ForegroundColor Green
} else {
    Write-Host "❌ 版本号不一致！" -ForegroundColor Red
}
```

```bash
# Bash
v1=$(cat VERSION)
v2=$(node -p "require('./app/frontend/package.json').version")
v3=$(python -c "import sys; sys.path.insert(0, 'app/backend'); from version import get_version; print(get_version(), end='')")

echo "VERSION 文件:    $v1"
echo "package.json:    $v2"
echo "Backend 读取:    $v3"
```

---

## 🔧 故障排查

### 问题：后端读取版本失败

**症状：**
```
Error reading VERSION file: ...
```

**解决方案：**
1. 检查 `VERSION` 文件是否存在于项目根目录
2. 确认文件编码为 UTF-8（无 BOM）
3. 检查文件内容格式（仅包含版本号，如 `1.1.0`）

### 问题：前端版本不同步

**症状：**
`package.json` 版本号与 `VERSION` 文件不一致

**解决方案：**
```bash
# 手动同步
node scripts/sync-version.js

# 或使用更新脚本
.\scripts\update-version.ps1 <版本号>
```

### 问题：Docker 容器中版本错误

**症状：**
容器内 `get_version()` 返回 "unknown"

**解决方案：**
1. 确认 `Dockerfile` 中包含 `COPY VERSION /app/VERSION`
2. 重新构建镜像：`docker compose build --no-cache`

---

## 📚 相关文档

- [语义化版本规范](https://semver.org/lang/zh-CN/)
- [CHANGELOG.md](../CHANGELOG.md) - 版本更新日志
- [README.md](../README.md) - 项目说明
- [DEPLOYMENT.md](../DEPLOYMENT.md) - 部署指南
- [scripts/README.md](../scripts/README.md) - 脚本使用说明

---

**最后更新**: 2025-10-07  
**维护者**: TMC Team

