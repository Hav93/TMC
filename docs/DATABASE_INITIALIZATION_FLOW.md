# 📚 数据库初始化流程说明

## 概述

本项目的数据库初始化采用 **Alembic 迁移 + SQLAlchemy 验证** 的双重机制，确保数据库结构正确且数据安全。

---

## 🔄 完整启动流程

### 容器启动时（docker-entrypoint.sh）

```
1. 创建目录结构
   ├── /app/data          # 数据库文件
   ├── /app/logs          # 日志文件
   ├── /app/sessions      # Telegram 会话
   ├── /app/media         # 媒体文件存储
   └── /app/config        # 配置文件

2. 检查并修复 Alembic 版本 (fix_alembic_version.py)
   ├── 检测数据库是否存在
   ├── 检测当前数据库版本
   ├── 修复版本记录（如果需要）
   └── ✅ 确保 alembic_version 表正确

3. 检查并修复数据库结构 (check_and_fix_schema.py)
   ├── 验证必要的表是否存在
   ├── 修复缺失的列
   ├── 修复列类型不匹配
   └── ✅ 确保基本结构完整

4. 运行 Alembic 迁移 (alembic upgrade head)
   ├── 检查当前数据库版本
   ├── 对比目标版本（head）
   ├── 应用增量迁移脚本
   └── ✅ 升级到最新结构

5. 创建默认管理员 (init_admin.py)
   ├── 检查 users 表是否为空
   ├── 如果为空，创建默认 admin 用户
   └── ✅ 确保至少有一个管理员

6. 启动 FastAPI 应用
   └── init_database()
       ├── 创建数据库连接池
       ├── 优化 SQLite 配置（WAL, 缓存等）
       ├── 验证表完整性
       └── ✅ 应用就绪
```

---

## 📊 三种启动场景

### 场景 1: 全新部署（无数据库文件）

```bash
启动前状态:
  ./data/ 目录为空

启动过程:
  1. fix_alembic_version.py  → 检测到空数据库，跳过
  2. check_and_fix_schema.py → 检测到空数据库，跳过
  3. alembic upgrade head    → 创建所有表（运行所有迁移）
  4. init_admin.py           → 创建默认管理员 (admin/admin123)
  5. init_database()         → 连接并验证

启动后状态:
  ✅ 数据库包含所有表
  ✅ alembic_version 记录最新版本
  ✅ 默认管理员已创建
  ✅ 可以正常使用所有功能

日志示例:
  🔧 Checking Alembic version...
  ⚠️  No database found, will create new one
  📦 Running database migrations...
  INFO  [alembic.runtime.migration] Running upgrade  -> initial_schema_001, Initial schema
  INFO  [alembic.runtime.migration] Running upgrade initial_schema_001 -> add_users_20251006, add users table
  ...
  ✅ Migration completed
  👤 Admin user created: admin
```

---

### 场景 2: 已有正确的数据库（test 分支最新版）

```bash
启动前状态:
  ./data/bot.db 存在且结构完整
  alembic_version = 'test_branch_features_20250111'

启动过程:
  1. fix_alembic_version.py  → 检测版本正确，无需修复
  2. check_and_fix_schema.py → 检测所有表结构正确，通过
  3. alembic upgrade head    → 检测已是最新版本，跳过迁移
  4. init_admin.py           → 检测管理员已存在，跳过
  5. init_database()         → 连接并验证

启动后状态:
  ✅ 数据库完全未改动
  ✅ 所有现有数据保留
  ✅ 直接使用现有配置
  ✅ 无需任何手动操作

日志示例:
  🔧 Checking Alembic version...
  ✅ Alembic version correct: test_branch_features_20250111
  🔍 Checking database schema...
  ✅ All tables verified
  📦 Running database migrations...
  INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
  INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
  ✅ Migration completed (already up to date)
  ⚠️  Admin user already exists
```

---

### 场景 3: 旧版数据库（需要升级）

```bash
启动前状态:
  ./data/bot.db 存在但是旧版本
  alembic_version = 'add_bot_settings_user_sessions_20251009'

启动过程:
  1. fix_alembic_version.py  → 检测版本较旧，标记为待升级
  2. check_and_fix_schema.py → 检测缺少新表，记录警告
  3. alembic upgrade head    → 应用增量迁移（创建新表/字段）
  4. init_admin.py           → 检测管理员已存在，跳过
  5. init_database()         → 连接并验证

启动后状态:
  ✅ 数据库已升级到最新版本
  ✅ 旧数据完整保留
  ✅ 新表和字段已添加
  ✅ 可以使用新功能

日志示例:
  🔧 Checking Alembic version...
  ⚠️  Old version detected: add_bot_settings_user_sessions_20251009
  📦 Running database migrations...
  INFO  [alembic.runtime.migration] Running upgrade add_bot_settings_user_sessions_20251009 -> test_branch_features_20250111
  INFO  Creating table media_settings
  INFO  Creating table media_monitor_rules
  INFO  Creating table media_files
  INFO  Creating table download_tasks
  ✅ Migration completed
```

---

## 🔍 代码层面的保护机制

### 1. init_database() - 只连接，不创建

```python
async def create_tables(self):
    """验证数据库表（不再自动创建，由 Alembic 管理）"""
    # 【重要】不再使用 create_all()，所有表结构由 Alembic 迁移管理
    # 这里只做验证，确保数据库已通过 Alembic 初始化
    
    logger.info("✅ 数据库表结构由 Alembic 管理")
    
    # 验证表是否正确创建
    await self.verify_tables()
```

**✅ 不会覆盖或修改现有表结构**

### 2. Alembic 幂等性

```python
# Alembic 迁移脚本都包含检查逻辑
def upgrade():
    if not table_exists('media_settings'):
        op.create_table('media_settings', ...)
    else:
        # 表已存在，只添加缺失的字段
        if not column_exists('media_settings', 'pan115_cookie'):
            batch_op.add_column(...)
```

**✅ 可以重复运行，不会报错或重复创建**

### 3. 自动版本检测

```python
# fix_alembic_version.py
def detect_database_version(cursor):
    """智能检测数据库版本"""
    # 1. 检查 alembic_version 表
    # 2. 通过表结构推断版本
    # 3. 自动修复错误的版本记录
```

**✅ 即使 alembic_version 丢失也能恢复**

---

## 🛡️ 数据安全保证

### 不会丢失数据的原因

1. **只添加不删除**
   - 迁移脚本只 `CREATE` 和 `ALTER ADD`
   - 不使用 `DROP` 或 `DELETE`

2. **原子性事务**
   - SQLite 使用 WAL 模式
   - 迁移失败会回滚

3. **验证机制**
   - 迁移前检查表结构
   - 迁移后验证完整性

4. **容错设计**
   - 迁移失败不中断启动
   - 允许部分功能降级运行

---

## 📝 常见问题

### Q: 如果数据库文件损坏了怎么办？

**A:** 启动脚本会尝试修复，如果无法修复会报错并拒绝启动，避免数据进一步损坏。

### Q: 手动删除了某个表，会自动重建吗？

**A:** 不会。`init_database()` 只验证不创建。需要手动运行 `alembic upgrade head` 或重建数据库。

### Q: 可以直接复制数据库文件到新容器吗？

**A:** 可以！只要数据库结构正确，容器启动时会自动检测并使用现有数据。

### Q: 如何确认数据库初始化成功？

**A:** 查看启动日志：
```bash
docker logs tmc-local | grep -E "(Migration|Database|Admin)"

# 应该看到：
# ✅ Alembic version correct
# ✅ All tables verified
# ✅ Migration completed
# ✅ 数据库初始化完成
```

### Q: 可以在运行中的容器手动运行迁移吗？

**A:** 可以：
```bash
docker exec tmc-local alembic upgrade head
```

---

## 🧪 测试数据库初始化

### 测试1: 全新部署

```bash
# 删除数据库
rm -f ./data/bot.db

# 启动容器
docker-compose up -d

# 查看日志
docker logs -f tmc-local

# 验证
docker exec tmc-local ls -lh /app/data/bot.db
docker exec tmc-local sqlite3 /app/data/bot.db "SELECT name FROM sqlite_master WHERE type='table'"
```

### 测试2: 使用现有数据库

```bash
# 确保 ./data/bot.db 存在

# 启动容器
docker-compose up -d

# 应该看到 "already up to date"
docker logs tmc-local | grep Migration
```

### 测试3: 强制重新迁移

```bash
# 重置 alembic 版本
docker exec tmc-local sqlite3 /app/data/bot.db "DELETE FROM alembic_version"

# 重启容器
docker restart tmc-local

# 会重新应用所有迁移
docker logs tmc-local
```

---

## 💡 最佳实践

### 生产环境

1. ✅ **定期备份数据库**
   ```bash
   docker exec tmc-local cp /app/data/bot.db /app/data/bot_backup_$(date +%Y%m%d).db
   ```

2. ✅ **监控迁移日志**
   ```bash
   docker logs tmc-local 2>&1 | grep -A 5 "Migration"
   ```

3. ✅ **升级前测试**
   - 先在测试环境验证
   - 确认数据库备份可用

### 开发环境

1. ✅ **快速重置**
   ```bash
   rm ./data/bot.db && docker-compose up -d
   ```

2. ✅ **查看表结构**
   ```bash
   docker exec tmc-local sqlite3 /app/data/bot.db .schema
   ```

3. ✅ **检查数据**
   ```bash
   docker exec tmc-local sqlite3 /app/data/bot.db "SELECT * FROM users"
   ```

---

## 总结

✅ **完全兼容已有数据库** - 无需担心数据丢失  
✅ **自动检测和升级** - 无需手动干预  
✅ **幂等性设计** - 可重复运行  
✅ **多重保护机制** - 数据安全有保障  

**结论：现有的 `init_database()` 设计非常合理，对已有正确数据库的处理是安全且高效的。**

