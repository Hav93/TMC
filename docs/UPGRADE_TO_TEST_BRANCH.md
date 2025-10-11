# 🚀 升级到 test 分支指南

## 概述

test 分支引入了全新的**媒体监控和管理功能**，这是一个从 0 到 1 的重大更新。

**推荐方案：重新部署（最简单可靠）**

---

## ⚠️ 重要提醒

test 分支相比 main 分支的数据库结构有重大变化：
- ✅ **新增** 4 个媒体相关表（`media_settings`, `media_monitor_rules`, `media_files`, `download_tasks`）
- ✅ **增强** 文件元数据支持
- ✅ **集成** 115网盘功能
- ❌ **移除** CloudDrive 相关功能

由于变更较大，**建议直接重新部署**。

---

## 🎯 方案一：全新部署（推荐）⭐

### 适用场景
- ✅ 测试环境
- ✅ 数据可以重新配置
- ✅ 追求最简单的升级方式
- ✅ 想要最干净的数据库结构

### 步骤

#### 1. 备份重要配置（可选）

如果你想保留一些配置，可以先导出：

```bash
# 备份旧数据库
docker cp tmc-local:/app/data/bot.db ./backup_bot.db

# 备份环境变量
docker exec tmc-local env > backup_env.txt
```

#### 2. 停止并删除旧容器

```bash
docker-compose down
```

#### 3. 切换到 test 分支

```bash
git fetch origin
git checkout test
git pull origin test
```

#### 4. 删除旧数据库（重要）

```bash
# Windows PowerShell
Remove-Item .\data\bot.db -ErrorAction SilentlyContinue

# Linux/Mac
rm -f ./data/bot.db
```

#### 5. 重新构建和启动

```bash
# 无缓存重新构建
docker-compose build --no-cache

# 启动服务
docker-compose up -d
```

#### 6. 查看启动日志

```bash
docker logs -f tmc-local

# 成功的日志：
# 🚀 启动FastAPI应用...
# ✅ 数据库初始化完成
# ✅ 已创建数据库表
# ✅ EnhancedBot启动完成
```

#### 7. 重新配置

访问 `http://localhost:9393`，重新配置：
1. 创建管理员账号
2. 添加 Telegram 客户端
3. 配置媒体监控规则（新功能）
4. 配置 115 网盘（如需要）

---

## 🔧 方案二：保留部分数据

### 适用场景
- ✅ 需要保留用户账号
- ✅ 需要保留 Telegram 客户端配置
- ✅ 需要保留转发规则

### 步骤

#### 1. 导出需要保留的数据

创建导出脚本 `export_data.py`:

```python
#!/usr/bin/env python3
import sqlite3
import json

# 连接旧数据库
conn = sqlite3.connect('./data/bot.db')
conn.row_factory = sqlite3.Row

# 导出用户
cursor = conn.cursor()
cursor.execute("SELECT * FROM users")
users = [dict(row) for row in cursor.fetchall()]

# 导出 Telegram 客户端
cursor.execute("SELECT * FROM telegram_clients")
clients = [dict(row) for row in cursor.fetchall()]

# 导出转发规则
cursor.execute("SELECT * FROM forward_rules")
rules = [dict(row) for row in cursor.fetchall()]

# 保存到文件
with open('backup_data.json', 'w', encoding='utf-8') as f:
    json.dump({
        'users': users,
        'clients': clients,
        'rules': rules
    }, f, indent=2, ensure_ascii=False)

conn.close()
print("✅ 数据已导出到 backup_data.json")
```

运行：
```bash
docker cp export_data.py tmc-local:/tmp/export_data.py
docker exec tmc-local python /tmp/export_data.py
docker cp tmc-local:/tmp/backup_data.json ./backup_data.json
```

#### 2. 按照方案一重新部署

#### 3. 导入数据（创建导入脚本）

---

## 📋 方案三：保留所有数据（不推荐）

**⚠️ 警告：此方案复杂且容易出错，不推荐使用**

如果确实需要保留所有历史数据，可以：

1. 手动运行 SQL 创建新表
2. 使用数据库管理工具（如 DB Browser for SQLite）
3. 联系技术支持

---

## 🆚 方案对比

| 方案 | 难度 | 时间 | 数据保留 | 推荐度 |
|------|------|------|----------|--------|
| **全新部署** | ⭐ 简单 | 5分钟 | ❌ 不保留 | ⭐⭐⭐⭐⭐ |
| **部分保留** | ⭐⭐ 中等 | 15分钟 | ⚠️ 部分保留 | ⭐⭐⭐ |
| **完全迁移** | ⭐⭐⭐⭐⭐ 复杂 | 1小时+ | ✅ 全部保留 | ⭐ |

---

## 🎉 test 分支新功能预览

### 1. 媒体监控
- 监控 Telegram 频道的媒体文件
- 自动下载视频/图片/文档
- 智能文件过滤（大小、类型、关键词）
- 发送者黑白名单

### 2. 文件管理
- 自动整理和归档
- 元数据提取（分辨率、时长、编码等）
- 去重检测
- 收藏和标签

### 3. 115网盘集成
- 直接上传到115云盘
- 路径自定义
- 空间监控
- 上传进度跟踪

### 4. 下载任务管理
- 可视化任务队列
- 失败自动重试
- 断点续传
- 并发下载控制

---

## 🔍 故障排查

### 问题1: 数据库文件被锁定

```bash
# 确保容器已停止
docker-compose down

# 等待几秒
sleep 5

# 删除数据库
rm -f ./data/bot.db
```

### 问题2: 表已存在错误

```
sqlite3.OperationalError: table xxx already exists
```

**解决：** 说明数据库没有完全删除，手动删除 `./data/bot.db` 文件

### 问题3: 容器启动后立即退出

```bash
# 查看日志
docker logs tmc-local

# 常见原因：
# 1. 端口被占用 -> 修改 docker-compose.yml 中的端口
# 2. 环境变量错误 -> 检查 .env 文件
# 3. 数据目录权限 -> chmod 777 ./data
```

---

## 📝 升级检查清单

- [ ] 已备份旧数据库（如需要）
- [ ] 已停止旧容器
- [ ] 已切换到 test 分支
- [ ] 已删除旧数据库文件
- [ ] 已重新构建镜像
- [ ] 容器成功启动
- [ ] 可以访问 Web 界面
- [ ] 已重新配置必要设置
- [ ] 已测试基本功能

---

## 💡 最佳实践建议

### 生产环境

1. **先在测试环境验证** test 分支的稳定性
2. **选择维护窗口** 在业务低峰期升级
3. **完整备份** 所有数据和配置
4. **准备回滚方案** 保留 main 分支的镜像

### 开发环境

1. **直接重新部署** 最快最简单
2. **定期清理** 测试数据
3. **使用 docker-compose** 快速重建

---

## 🆘 需要帮助？

如果遇到问题：

1. 查看日志：`docker logs tmc-local`
2. 检查数据库：`ls -lh ./data/bot.db`
3. 验证分支：`git branch`
4. 提交 Issue 并附上错误信息

---

## 📚 相关文档

- [数据库重置工具](../scripts/maintenance/reset_database.py)
- [Docker 部署指南](./DOCKER_GUIDE.md)
- [API 文档](./API_DOCUMENTATION_GUIDE.md)
- [功能说明](../README.md)

