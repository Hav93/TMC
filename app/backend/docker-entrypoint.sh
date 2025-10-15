#!/bin/bash
set -e

echo "🚀 TMC 启动中..."

# 创建必需的目录
mkdir -p /app/{data,logs,sessions,temp,config,media/{downloads,storage/{photos,videos,documents,audio}}}

# 设置数据库URL
export DATABASE_URL="${DATABASE_URL:-sqlite:///data/bot.db}"
DB_FILE="/app/data/bot.db"

cd /app

# ========== 数据库初始化 ==========
echo ""
echo "📦 数据库初始化"

if [ -f "$DB_FILE" ]; then
    echo "   ├─ 检测到已有数据库"
    
    # 检查 Alembic 版本表
    CURRENT_VERSION=$(python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('$DB_FILE')
    cursor = conn.cursor()
    cursor.execute('SELECT version_num FROM alembic_version LIMIT 1')
    print(cursor.fetchone()[0])
except:
    print('none')
" 2>/dev/null)
    
    if [ "$CURRENT_VERSION" = "none" ]; then
        echo "   ├─ ⚠️  数据库缺少版本信息"
        echo "   ├─ 尝试自动迁移..."
    else
        echo "   ├─ 当前版本: $CURRENT_VERSION"
    fi
    
    # 尝试迁移到最新版本
    echo "   ├─ 执行数据库迁移..."
    MIGRATION_OUTPUT=$(alembic upgrade head 2>&1)
    MIGRATION_EXIT=$?
    
    if [ $MIGRATION_EXIT -eq 0 ]; then
        echo "   └─ ✅ 数据库迁移成功"
    else
        # 显示完整错误信息
        echo ""
        echo "❌ 数据库迁移失败！完整错误信息："
        echo "============================================"
        echo "$MIGRATION_OUTPUT"
        echo "============================================"
        echo ""
        echo "💡 建议删除旧数据库后重新启动："
        echo "   docker-compose down"
        echo "   rm -rf data/bot.db*"
        echo "   docker-compose up -d"
        echo ""
        exit 1
    fi
else
    echo "   ├─ 未检测到数据库"
    echo "   ├─ 创建全新数据库..."
    
    # 使用 Alembic 创建数据库
    MIGRATION_OUTPUT=$(alembic upgrade head 2>&1)
    MIGRATION_EXIT=$?
    
    if [ $MIGRATION_EXIT -eq 0 ]; then
        echo "   └─ ✅ 数据库创建成功"
    else
        echo ""
        echo "❌ 数据库创建失败！完整错误信息："
        echo "============================================"
        echo "$MIGRATION_OUTPUT"
        echo "============================================"
        exit 1
    fi
fi

# 初始化管理员（静默失败）
python3 init_admin.py 2>/dev/null || true

# 启动应用
echo ""
echo "✅ 启动成功"
exec uvicorn main:app --host 0.0.0.0 --port 9393 --workers 1

