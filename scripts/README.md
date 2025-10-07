# TMC 项目脚本说明

本目录包含用于 TMC 项目管理的各种脚本。

---

## 📂 脚本分类

### 版本管理

#### `update-version.ps1`
**统一版本号更新脚本**

更新项目版本号到所有相关文件。

**使用方法：**
```powershell
.\scripts\update-version.ps1 1.2.0
```

**自动更新的文件：**
- `VERSION` - 主版本文件
- `app/frontend/package.json` - 前端包版本

**后端版本读取：**
- `app/backend/version.py` - 从 VERSION 文件动态读取
- `app/backend/config.py` - 使用 `version.py` 提供的版本号

**前端版本读取：**
- 构建时通过 `prebuild` 钩子自动同步 `package.json`

---

#### `sync-version.js`
**前端版本同步脚本**

从 `VERSION` 文件读取版本号并同步到 `app/frontend/package.json`。

**使用方法：**
```bash
node scripts/sync-version.js
```

**自动调用：**
- 前端构建时（`npm run build`）会自动执行

---

### Git 管理

#### `git-push.ps1`
**交互式 Git 推送脚本**

提供友好的交互式界面来提交和推送代码。

**使用方法：**
```powershell
.\scripts\git-push.ps1
```

**功能：**
- 查看当前状态
- 暂存所有更改
- 输入提交信息
- 推送到 GitHub

---

#### `push-to-github.ps1`
**快速推送脚本**

快速提交并推送代码到 GitHub。

**使用方法：**
```powershell
.\scripts\push-to-github.ps1 "your commit message"
```

---

## 🔄 版本更新工作流

### 标准流程

1. **更新版本号**
   ```powershell
   .\scripts\update-version.ps1 1.2.0
   ```

2. **更新文档**
   - 编辑 `CHANGELOG.md` 添加版本变更
   - 更新 `README.md` 的版本说明
   - 更新 `DEPLOYMENT.md` 的版本信息

3. **提交代码**
   ```powershell
   git add .
   git commit -m "chore: bump version to 1.2.0"
   ```

4. **打标签**
   ```powershell
   git tag v1.2.0
   ```

5. **推送**
   ```powershell
   git push && git push --tags
   ```

### 版本号规范

遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范：

- **主版本号(X)**: 不兼容的 API 修改
- **次版本号(Y)**: 向下兼容的功能性新增
- **修订号(Z)**: 向下兼容的问题修正

**示例：**
- `1.0.0` → `2.0.0` - 重大架构调整
- `1.0.0` → `1.1.0` - 新增功能特性
- `1.0.0` → `1.0.1` - Bug 修复

---

## 📝 版本文件说明

### `VERSION` 文件
项目的**唯一真实版本来源**，所有其他地方的版本号都从这里读取。

**格式：**
```
1.1.0
```

### 版本同步机制

```
VERSION 文件
    ↓
    ├─→ app/backend/version.py (运行时读取)
    │       ↓
    │   app/backend/config.py (使用)
    │
    └─→ scripts/sync-version.js (构建时)
            ↓
        app/frontend/package.json
```

---

## ⚙️ 自动化集成

### Docker 构建
`Dockerfile` 会将 `VERSION` 文件复制到容器中：
```dockerfile
COPY VERSION /app/VERSION
```

### 前端构建
`package.json` 的 `prebuild` 钩子会自动同步版本：
```json
"prebuild": "npm run sync-version"
```

### 后端运行时
`version.py` 会在运行时动态读取 `VERSION` 文件：
```python
from version import get_version
VERSION = get_version()  # 从 VERSION 文件读取
```

---

## 🧪 测试脚本

### 测试版本同步
```powershell
# 测试前端版本同步
node scripts/sync-version.js

# 测试后端版本读取
python -c "import sys; sys.path.insert(0, 'app/backend'); from version import get_version; print(get_version())"
```

---

## 📚 相关文档

- [VERSION](../VERSION) - 版本号文件
- [CHANGELOG.md](../CHANGELOG.md) - 更新日志
- [README.md](../README.md) - 项目说明
- [DEPLOYMENT.md](../DEPLOYMENT.md) - 部署指南

---

**最后更新**: 2025-10-07  
**维护者**: TMC Team
