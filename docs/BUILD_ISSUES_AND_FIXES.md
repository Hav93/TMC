# 本地构建问题与解决方案

> 记录本地开发环境构建过程中遇到的问题和解决方法

**日期：** 2025-01-14  
**版本：** v1.0.0

---

## 问题列表

### 1. 容器反复重启 - 数据库迁移问题

**现象：**
```
容器一直处于 Restarting 状态
日志显示：
🚀 TMC 启动中...
📦 数据库初始化
   ├─ 检测到已有数据库
   ├─ 当前版本: test_branch_init
   ├─ 执行数据库迁移...
（然后容器重启，循环往复）
```

**原因分析：**
1. 数据库版本停留在 `test_branch_init`
2. 这个版本是测试分支的初始化迁移
3. 迁移脚本可能存在问题导致无法继续执行

**解决方案：**
```powershell
# 1. 停止容器
docker compose -f local-dev/docker-compose.local.yml down

# 2. 备份并重置数据库
.\scripts\reset-local-db.ps1
# 选择选项 1（备份并重置）

# 3. 重新启动
docker compose -f local-dev/docker-compose.local.yml up -d
```

**预防措施：**
- 定期备份数据库
- 测试新的迁移脚本后再合并
- 保留迁移文件的向前兼容性

---

### 2. Docker构建失败 - p115client包缺失

**现象：**
```
ERROR: Could not find a version that satisfies the requirement p115client>=0.0.6.11.8
ERROR: No matching distribution found for p115client>=0.0.6.11.8
```

**原因分析：**
1. `p115client` 不在PyPI官方仓库
2. 需要从GitHub安装
3. Docker构建时无法通过pip直接安装

**解决方案：**

**临时方案（已应用）：**
```python
# 修改 requirements.txt
# 注释掉 p115client
# p115client>=0.0.6.11.8
```

**完整方案（推荐）：**
```dockerfile
# 在 Dockerfile 中添加
RUN pip install git+https://github.com/ChenyangGao/p115client.git
```

或者修改 `requirements.txt`：
```
# 使用git+https协议安装
git+https://github.com/ChenyangGao/p115client.git@v0.0.6.11.8
```

**已修改文件：**
- ✅ `app/backend/requirements.txt` - 临时注释掉p115client

**影响范围：**
- ⚠️ 115网盘相关功能暂时不可用
- ✅ 其他功能正常
- ✅ 可以成功构建Docker镜像

---

### 3. PowerShell脚本编码问题

**现象：**
```
����ʽ������а�������ı�ǡ�}����
```

**原因分析：**
1. PowerShell脚本包含中文字符
2. 终端编码设置不匹配
3. 导致语法解析错误

**解决方案：**

**方案1：使用纯ASCII版本**
```powershell
# 使用英文版本的脚本
.\local-dev\build-test.ps1
```

**方案2：设置PowerShell编码**
```powershell
# 设置控制台编码为UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
```

**方案3：使用BOM的UTF-8**
- 在编辑器中保存文件时选择 "UTF-8 with BOM"

**已创建的解决方案：**
- ✅ `build-test.ps1` - 纯英文版本
- ✅ `quick-status.ps1` - 纯英文状态检查

---

## 工具脚本

### 数据库重置工具

**文件：** `scripts/reset-local-db.ps1`

**功能：**
- 备份现有数据库
- 重置数据库
- 删除WAL和SHM文件

**使用方法：**
```powershell
.\scripts\reset-local-db.ps1

# 选项:
# 1. 备份并重置 (推荐)
# 2. 直接重置 (危险)
# 3. 仅备份
# 0. 取消
```

### 构建测试工具

**文件：** `local-dev/build-test.ps1`

**功能：**
- Docker状态检查
- 9个构建和管理选项
- 纯英文界面，无编码问题

**使用方法：**
```powershell
.\local-dev\build-test.ps1

# 选择对应的数字选项
```

### 快速状态检查

**文件：** `local-dev/quick-status.ps1`

**功能：**
- 检查Docker状态
- 检查容器状态  
- 检查镜像状态
- 显示代理配置

**使用方法：**
```powershell
.\local-dev\quick-status.ps1
```

---

## 常见问题排查流程

### 容器无法启动

```powershell
# 1. 查看状态
.\local-dev\quick-status.ps1

# 2. 查看日志
docker compose -f local-dev/docker-compose.local.yml logs --tail=100

# 3. 如果是数据库问题
.\scripts\reset-local-db.ps1  # 选择 1

# 4. 重新构建
.\local-dev\build-test.ps1   # 选择 2
```

### 构建失败

```powershell
# 1. 停止并清理
docker compose -f local-dev/docker-compose.local.yml down -v

# 2. 删除旧镜像
docker rmi hav93/tmc:local -f

# 3. 完全重新构建
docker compose -f local-dev/docker-compose.local.yml build --no-cache

# 4. 启动
docker compose -f local-dev/docker-compose.local.yml up -d
```

### 依赖包安装失败

```powershell
# 1. 检查代理设置
$env:HTTP_PROXY
$env:HTTPS_PROXY

# 2. 测试网络连接
curl -x http://192.168.31.6:7890 https://pypi.org

# 3. 检查requirements.txt
cat app/backend/requirements.txt

# 4. 手动测试pip安装
docker run -it --rm python:3.12-slim pip install <package_name>
```

---

## 已知限制

### 当前限制

1. **115网盘功能暂时不可用**
   - 原因：p115client未安装
   - 影响：无法使用115云盘自动保存
   - 解决：等待Dockerfile更新

2. **中文PowerShell脚本编码问题**
   - 原因：终端编码不匹配
   - 影响：部分中文提示显示乱码
   - 解决：使用英文版脚本

### 计划改进

1. **优化Docker构建**
   - [ ] 添加p115client安装
   - [ ] 使用多阶段构建优化镜像大小
   - [ ] 添加健康检查改进

2. **改进迁移系统**
   - [ ] 添加迁移验证
   - [ ] 自动备份机制
   - [ ] 回滚支持

3. **增强脚本工具**
   - [x] 数据库重置工具
   - [x] 状态检查工具
   - [ ] 日志分析工具
   - [ ] 性能监控工具

---

## 版本历史

### v1.0.0 (2025-01-14)

**新增：**
- ✅ 数据库重置工具
- ✅ 英文版构建脚本
- ✅ 快速状态检查工具

**修复：**
- ✅ 容器反复重启问题
- ✅ p115client构建失败
- ✅ PowerShell编码问题

**文档：**
- ✅ 问题排查指南
- ✅ 工具使用说明
- ✅ 已知限制说明

---

## 参考资料

### 相关文档
- [本地开发README](../local-dev/README.md)
- [本地开发改进报告](./LOCAL_DEV_IMPROVEMENTS.md)
- [项目文件分析](./PROJECT_FILES_ANALYSIS.md)

### 外部资源
- [p115client GitHub](https://github.com/ChenyangGao/p115client)
- [Docker文档](https://docs.docker.com/)
- [PowerShell编码指南](https://docs.microsoft.com/en-us/powershell/)

---

**维护者：** TMC开发团队  
**最后更新：** 2025-01-14

