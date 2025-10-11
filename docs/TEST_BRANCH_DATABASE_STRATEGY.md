# Test 分支数据库管理策略

## 策略说明

test 分支采用基于 Alembic 的数据库版本管理策略，**支持未来的数据库迁移**。

### 核心原则

1. **保留 Alembic**：为未来的数据库结构变更提供迁移能力
2. **初始基线**：`test_branch_init` 作为 test 分支的第一个数据库版本
3. **自动迁移**：容器启动时自动执行数据库迁移
4. **降级友好**：如果迁移失败，提供清晰的降级指导

---

## 数据库版本管理

### 当前版本

- **版本号**: `test_branch_init`
- **创建时间**: 2025-10-11
- **包含表**:
  - `users` - 用户管理
  - `telegram_clients` - Telegram 客户端配置
  - `forward_rules` - 转发规则
  - `keywords` - 关键词规则
  - `replace_rules` - 替换规则
  - `message_logs` - 消息日志
  - `bot_settings` - 机器人设置
  - `user_sessions` - 用户会话
  - `media_monitor_rules` - 媒体监控规则
  - `download_tasks` - 下载任务
  - `media_files` - 媒体文件
  - `media_settings` - 媒体设置

### 未来迁移

当 test 分支需要添加新表或修改表结构时：

1. **创建迁移脚本**:
   ```bash
   cd app/backend
   alembic revision -m "描述变更内容"
   ```

2. **编辑迁移脚本**:
   ```python
   def upgrade() -> None:
       # 添加新表
       op.create_table('new_table', ...)
       
       # 或添加新列
       op.add_column('existing_table', 
                     sa.Column('new_column', sa.String(100)))
   
   def downgrade() -> None:
       # 回滚操作
       op.drop_table('new_table')
   ```

3. **测试迁移**:
   ```bash
   alembic upgrade head  # 升级到最新版本
   alembic downgrade -1  # 回滚一个版本（测试）
   alembic upgrade head  # 再次升级
   ```

4. **提交到 Git**:
   ```bash
   git add app/backend/alembic/versions/*.py
   git commit -m "feat: add database migration for xxx"
   ```

---

## 容器启动流程

### 1. 全新部署（无数据库）

```
📦 数据库初始化
   ├─ 未检测到数据库
   ├─ 创建全新数据库...
   └─ ✅ 数据库创建成功
```

**执行逻辑**:
- 运行 `alembic upgrade head`
- 创建所有表结构
- 初始化管理员账户（admin/admin123）

### 2. 已有数据库（版本正确）

```
📦 数据库初始化
   ├─ 检测到已有数据库
   ├─ 当前版本: test_branch_init
   ├─ 执行数据库迁移...
   └─ ✅ 数据库迁移成功
```

**执行逻辑**:
- 检测到已是最新版本
- 无需迁移，直接启动

### 3. 已有数据库（需要升级）

```
📦 数据库初始化
   ├─ 检测到已有数据库
   ├─ 当前版本: old_version
   ├─ 执行数据库迁移...
   └─ ✅ 数据库迁移成功 (old_version -> new_version)
```

**执行逻辑**:
- 自动执行 Alembic 迁移
- 升级到最新版本

### 4. 迁移失败

```
❌ 数据库迁移失败

💡 建议删除旧数据库后重新启动：
   docker-compose down
   rm -rf data/bot.db*
   docker-compose up -d
```

**常见原因**:
- 数据库文件损坏
- 迁移脚本错误
- 手动修改过数据库结构

---

## 用户升级指南

### 情况 A：从 main 分支迁移到 test 分支

**不支持直接迁移**。test 分支与 main 分支的数据库结构差异较大。

**推荐操作**:
1. 导出 main 分支的重要数据（如有需要）
2. 删除旧数据库
3. 部署 test 分支

```bash
# 备份 main 分支数据（可选）
docker cp your-container:/app/data/bot.db ./bot.db.main.backup

# 切换到 test 分支
git checkout test
docker-compose down
rm -rf data/bot.db*
docker-compose up -d
```

### 情况 B：test 分支内升级

**支持自动迁移**。只需更新代码并重启：

```bash
# 拉取最新代码
git pull origin test

# 重启容器（会自动执行数据库迁移）
docker-compose down
docker-compose up -d
```

### 情况 C：迁移失败处理

如果自动迁移失败，建议删除数据库：

```bash
# 备份当前数据库（可选）
cp data/bot.db data/bot.db.backup

# 删除数据库并重启
docker-compose down
rm -rf data/bot.db*
docker-compose up -d
```

---

## 开发者指南

### 创建新迁移

```bash
cd app/backend
alembic revision -m "add_new_feature"
```

### 迁移脚本示例

```python
"""add_new_feature

Revision ID: new_feature_20251012
Revises: test_branch_init
Create Date: 2025-10-12 10:00:00
"""
from alembic import op
import sqlalchemy as sa

revision = 'new_feature_20251012'
down_revision = 'test_branch_init'

def upgrade() -> None:
    # 添加新表
    op.create_table(
        'new_feature_table',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )
    
    # 添加索引
    op.create_index('idx_new_feature_name', 'new_feature_table', ['name'])

def downgrade() -> None:
    op.drop_index('idx_new_feature_name', 'new_feature_table')
    op.drop_table('new_feature_table')
```

### 测试迁移

```bash
# 升级
alembic upgrade head

# 检查当前版本
alembic current

# 查看历史
alembic history

# 回滚（仅测试，生产环境不推荐）
alembic downgrade -1
```

---

## 故障排查

### 问题 1: "Multiple head revisions"

**原因**: 有多个迁移脚本的 `down_revision` 指向同一个版本

**解决**:
```bash
# 查看所有 heads
alembic heads

# 合并 heads
alembic merge <head1> <head2> -m "merge heads"
```

### 问题 2: "Can't locate revision"

**原因**: 数据库中的版本号在代码中不存在

**解决**:
```bash
# 删除数据库，重新创建
rm -rf data/bot.db*
docker-compose restart
```

### 问题 3: 迁移执行但表未创建

**原因**: `test_branch_init` 迁移脚本依赖 `models.py`

**检查**:
```bash
# 进入容器
docker exec -it your-container bash

# 测试模型导入
python3 -c "from models import Base; print(Base.metadata.tables.keys())"

# 手动运行迁移
alembic upgrade head
```

---

## 优势与限制

### ✅ 优势

1. **支持未来升级**: 用户可以平滑升级，无需删库
2. **版本可追溯**: 清晰的迁移历史
3. **回滚能力**: 理论上支持降级（不推荐在生产环境使用）
4. **开发友好**: 使用标准的 Alembic 工作流

### ⚠️ 限制

1. **不支持从 main 分支迁移**: test 分支是全新起点
2. **复杂迁移可能失败**: 如大量数据迁移、表结构重大变更
3. **需要测试**: 每个迁移脚本都应在开发环境充分测试

---

## 总结

test 分支的数据库管理策略平衡了**灵活性**和**可维护性**：

- **初次部署**: 简单快速，自动创建完整数据库
- **后续升级**: 支持自动迁移，用户体验友好
- **降级方案**: 如果迁移失败，提供清晰的删库指导

这为 test 分支的持续开发和用户升级提供了坚实的基础。

