# 📚 数据库迁移指南

## 概述

本项目使用 Alembic 管理数据库迁移。从 `main` 分支升级到 `test` 分支时，需要应用新的数据库迁移。

## 🎯 推荐方案：自动迁移（保留数据）

### 优点
- ✅ **保留所有用户数据**
- ✅ **无缝升级体验**
- ✅ **自动备份数据库**
- ✅ **符合生产环境最佳实践**

### 使用方法

#### 1. 启用自动迁移

在 `docker-compose.yml` 或 `.env` 中添加环境变量：

```yaml
environment:
  - AUTO_MIGRATE=true              # 启用自动迁移
  - BACKUP_BEFORE_MIGRATE=true     # 迁移前自动备份（推荐）
```

或者在启动容器时指定：

```bash
docker run -e AUTO_MIGRATE=true your-image
```

#### 2. 重启容器

```bash
docker-compose down
docker-compose up -d
```

应用会在启动时自动：
1. 🔍 检查是否有待应用的迁移
2. 📦 备份当前数据库（如果启用）
3. 🚀 应用所有待处理的迁移
4. ✅ 启动应用

#### 3. 查看日志

```bash
docker logs -f tmc-local

# 成功的日志输出：
# 🔍 检查数据库迁移...
# 📋 检测到待应用的数据库迁移
#    当前版本: add_bot_settings_user_sessions_20251009 (main分支)
#    目标版本: test_branch_features_20250111 (test分支)
# 📦 正在备份数据库...
# ✅ 数据库已备份到: /app/data/bot_backup_20250111_140000.db
# 🚀 开始应用数据库迁移...
# ✅ 数据库迁移应用成功
# ✅ 数据库初始化完成
```

---

## 🔧 方案二：手动迁移（高级用户）

如果不想启用自动迁移，可以手动执行：

### 1. 备份数据库

```bash
docker exec tmc-local cp /app/data/bot.db /app/data/bot_backup.db
```

### 2. 检查待迁移版本

```bash
docker exec tmc-local alembic current
docker exec tmc-local alembic heads
```

### 3. 应用迁移

```bash
docker exec tmc-local alembic upgrade head
```

### 4. 验证

```bash
docker exec tmc-local alembic current
# 应显示: test_branch_features_20250111 (head)
```

---

## 🗑️ 方案三：重置数据库（⚠️ 丢失数据）

**仅适用于以下情况：**
- 开发/测试环境
- 数据库损坏无法修复
- 不需要保留历史数据

### 使用重置工具

```bash
# 完全重置（删除所有数据）
docker exec tmc-local python scripts/maintenance/reset_database.py --confirm --backup

# 重置但保留配置
docker exec tmc-local python scripts/maintenance/reset_database.py --confirm --keep-config

# 然后重启容器
docker restart tmc-local
```

### 手动删除数据库

```bash
# 停止容器
docker-compose down

# 删除数据库文件
rm ./data/bot.db

# 重新启动
docker-compose up -d
```

---

## 📋 迁移内容说明

### test 分支新增功能

`test_branch_features_20250111` 迁移包含以下更改：

#### 1. 115网盘集成
- `media_settings.pan115_cookie`: 115网盘Cookie
- `media_settings.pan115_enabled`: 是否启用115网盘
- `media_settings.pan115_upload_path`: 上传路径
- `media_monitor_rules.pan115_*`: 规则级别的115网盘配置

#### 2. 文件元数据增强
- `media_files.file_metadata`: 完整元数据（JSON）
- `media_files.width/height`: 视频/图片尺寸
- `media_files.duration_seconds`: 时长
- `media_files.resolution`: 分辨率（如 1920x1080）
- `media_files.codec`: 编码格式
- `media_files.bitrate_kbps`: 码率

#### 3. 来源信息跟踪
- `media_files.source_chat`: 来源频道/群组
- `media_files.sender_id`: 发送者ID
- `media_files.sender_username`: 发送者用户名

#### 4. CloudDrive 移除
- 移除所有 `clouddrive_*` 字段
- `clouddrive_path` 重命名为 `pan115_path`

---

## 🔍 故障排查

### 问题1: 迁移超时

```
❌ 迁移超时（>60秒）
```

**解决方案：**
- 数据库文件过大，手动迁移：`docker exec tmc-local alembic upgrade head`

### 问题2: 列已存在

```
sqlite3.OperationalError: duplicate column name: pan115_cookie
```

**原因：** 迁移已部分应用

**解决方案：**
```bash
# 检查当前版本
docker exec tmc-local alembic current

# 强制标记为最新（如果数据已正确）
docker exec tmc-local alembic stamp head
```

### 问题3: 多个迁移头

```
FAILED: Multiple head revisions are present
```

**解决方案：**
```bash
# 升级到合并迁移
docker exec tmc-local alembic upgrade test_branch_features_20250111
```

### 问题4: 数据库锁定

```
sqlite3.OperationalError: database is locked
```

**解决方案：**
```bash
# 停止所有服务
docker-compose down

# 重新启动
docker-compose up -d
```

---

## ⚙️ 配置参考

### docker-compose.yml 完整配置示例

```yaml
version: '3.8'

services:
  app:
    image: your-image:test
    environment:
      # 自动迁移配置
      - AUTO_MIGRATE=true              # 启用自动迁移
      - BACKUP_BEFORE_MIGRATE=true     # 迁移前备份
      
      # 其他配置...
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

### .env 文件示例

```bash
# 数据库迁移
AUTO_MIGRATE=true
BACKUP_BEFORE_MIGRATE=true

# 其他环境变量...
```

---

## 📝 最佳实践

### 生产环境

1. ✅ **始终备份**: 升级前手动备份数据库
2. ✅ **测试环境**: 先在测试环境验证迁移
3. ✅ **监控日志**: 观察迁移过程是否正常
4. ✅ **回滚计划**: 准备数据库备份用于回滚

### 开发环境

1. ✅ **启用自动迁移**: `AUTO_MIGRATE=true`
2. ✅ **定期重置**: 使用重置工具清理测试数据
3. ✅ **版本控制**: 提交迁移脚本到Git

---

## 🆘 需要帮助？

如果遇到问题：

1. 查看日志：`docker logs tmc-local`
2. 检查数据库：`docker exec tmc-local alembic current`
3. 提交Issue并附上完整错误信息

---

## 📚 相关文档

- [Alembic 官方文档](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 文档](https://www.sqlalchemy.org/)
- [项目 CHANGELOG](../CHANGELOG.md)

