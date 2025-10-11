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

# 获取最新的 Alembic 版本号
LATEST_VERSION=$(alembic heads | grep -o '[a-z0-9_]*' | head -1)
echo "   ├─ 最新版本: $LATEST_VERSION"

if [ -f "$DB_FILE" ]; then
    echo "   ├─ 检测到已有数据库"
    
    # 检查 alembic_version 表是否存在
    if sqlite3 "$DB_FILE" "SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version';" 2>/dev/null | grep -q alembic_version; then
        # 获取当前数据库版本
        CURRENT_VERSION=$(sqlite3 "$DB_FILE" "SELECT version_num FROM alembic_version LIMIT 1;" 2>/dev/null || echo "")
        
        if [ "$CURRENT_VERSION" = "$LATEST_VERSION" ]; then
            echo "   ├─ ✅ 数据库版本匹配: $CURRENT_VERSION"
            echo "   └─ 直接使用现有数据库"
        else
            echo ""
            echo "❌ 数据库版本不匹配"
            echo "   当前版本: ${CURRENT_VERSION:-未知}"
            echo "   需要版本: $LATEST_VERSION"
            echo ""
            echo "💡 test 分支不支持数据迁移，请删除数据库："
            echo "   docker-compose down -v"
            echo "   docker-compose up -d"
            echo ""
            exit 1
        fi
    else
        echo ""
        echo "❌ 数据库结构不完整（缺少版本表）"
        echo ""
        echo "💡 请删除数据库后重新启动："
        echo "   docker-compose down -v"
        echo "   docker-compose up -d"
        echo ""
        exit 1
    fi
else
    echo "   ├─ 未检测到数据库"
    echo "   ├─ 创建全新数据库..."
    
    # 创建全新数据库
    if alembic upgrade head 2>&1 | grep -v "^INFO"; then
        echo "   └─ ✅ 数据库创建成功"
    else
        echo ""
        echo "❌ 数据库创建失败"
        exit 1
    fi
fi

# 初始化管理员（静默失败）
python3 init_admin.py 2>/dev/null || true

# 启动应用
echo ""
echo "✅ 启动成功"
exec uvicorn main:app --host 0.0.0.0 --port 9393 --workers 1

