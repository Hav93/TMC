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
        # 显示错误信息
        echo "$MIGRATION_OUTPUT" | grep -v "^INFO" | grep -v "^$"
        echo ""
        echo "❌ 数据库迁移失败"
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
        echo "$MIGRATION_OUTPUT" | grep -v "^INFO" | grep -v "^$"
        echo ""
        echo "❌ 数据库创建失败"
        exit 1
    fi
fi

# ========== 初始化配置文件 ==========
echo ""
echo "📝 配置文件初始化"

CONFIG_FILE="/app/config/app.config"

# 如果配置文件不存在，从环境变量创建
if [ ! -f "$CONFIG_FILE" ]; then
    echo "   ├─ 配置文件不存在，从环境变量创建..."
    
    cat > "$CONFIG_FILE" << EOF
# TMC 配置文件（自动生成）
# 此文件由 docker-entrypoint.sh 从环境变量生成

# Telegram API配置
API_ID=${API_ID:-}
API_HASH=${API_HASH:-}
BOT_TOKEN=${BOT_TOKEN:-}
PHONE_NUMBER=${PHONE_NUMBER:-}

# 代理配置
ENABLE_PROXY=${ENABLE_PROXY:-false}
EOF

    # 如果设置了 HTTP_PROXY 或 HTTPS_PROXY，自动启用代理
    if [ -n "$HTTP_PROXY" ] || [ -n "$HTTPS_PROXY" ]; then
        echo "   ├─ 检测到代理环境变量，自动配置代理..."
        
        # 使用 HTTPS_PROXY，如果没有则使用 HTTP_PROXY
        PROXY_URL="${HTTPS_PROXY:-$HTTP_PROXY}"
        
        # 解析代理 URL
        PROXY_HOST=$(echo "$PROXY_URL" | sed -E 's#^https?://([^:]+):([0-9]+).*#\1#')
        PROXY_PORT=$(echo "$PROXY_URL" | sed -E 's#^https?://([^:]+):([0-9]+).*#\2#')
        PROXY_TYPE=$(echo "$PROXY_URL" | sed -E 's#^(https?)://.*#\1#')
        
        cat >> "$CONFIG_FILE" << EOF
ENABLE_PROXY=true
PROXY_TYPE=${PROXY_TYPE}
PROXY_HOST=${PROXY_HOST}
PROXY_PORT=${PROXY_PORT}
PROXY_USERNAME=${PROXY_USERNAME:-}
PROXY_PASSWORD=${PROXY_PASSWORD:-}
EOF
        echo "   ├─ ✅ 代理配置: ${PROXY_TYPE}://${PROXY_HOST}:${PROXY_PORT}"
    else
        # 使用传统的 PROXY_HOST/PROXY_PORT 配置
        if [ "${ENABLE_PROXY}" = "true" ]; then
            cat >> "$CONFIG_FILE" << EOF
PROXY_TYPE=${PROXY_TYPE:-http}
PROXY_HOST=${PROXY_HOST:-127.0.0.1}
PROXY_PORT=${PROXY_PORT:-7890}
PROXY_USERNAME=${PROXY_USERNAME:-}
PROXY_PASSWORD=${PROXY_PASSWORD:-}
EOF
            echo "   ├─ ✅ 代理配置: ${PROXY_TYPE:-http}://${PROXY_HOST:-127.0.0.1}:${PROXY_PORT:-7890}"
        else
            echo "   ├─ 代理未启用"
        fi
    fi
    
    echo "   └─ ✅ 配置文件已创建: $CONFIG_FILE"
else
    echo "   └─ ✅ 配置文件已存在，跳过初始化"
fi

# 初始化管理员（静默失败）
python3 init_admin.py 2>/dev/null || true

# 启动应用
echo ""
echo "✅ 启动成功"
exec uvicorn main:app --host 0.0.0.0 --port 9393 --workers 1

