#!/bin/bash
set -e

echo "🚀 Starting Telegram Message Forwarder..."

# 等待数据库文件目录准备好
mkdir -p /app/data /app/logs /app/sessions /app/temp /app/config

# 创建媒体管理目录（v1.3.0 新增）
mkdir -p /app/media/downloads /app/media/storage
mkdir -p /app/media/storage/photos /app/media/storage/videos
mkdir -p /app/media/storage/documents /app/media/storage/audio

# 创建 CloudDrive 挂载目录
mkdir -p /mnt/clouddrive /mnt/data

# 设置数据库URL环境变量（如果未设置）
# 使用相对路径，基于工作目录 /app
export DATABASE_URL="${DATABASE_URL:-sqlite:///data/bot.db}"
echo "📊 Database URL: $DATABASE_URL"

# test 分支：推荐全新部署，不考虑迁移兼容性
echo "🔵 Test 分支模式：简化数据库初始化"

# 检查是否有旧数据库
if [ -f "/app/data/bot.db" ]; then
    echo "📊 检测到已有数据库文件"
    
    # 检查数据库是否包含核心表（简单验证）
    if sqlite3 /app/data/bot.db "SELECT name FROM sqlite_master WHERE type='table' AND name='users'" 2>/dev/null | grep -q users; then
        echo "✅ 数据库结构看起来正常，将直接使用"
    else
        echo "⚠️  数据库可能不完整或损坏"
        echo "💡 提示：如果遇到问题，请删除数据库文件重新启动"
    fi
else
    echo "📝 未检测到数据库，将创建全新数据库"
fi

# 运行数据库迁移（Alembic会自动处理新建或升级）
echo "📦 初始化数据库结构..."
cd /app
alembic upgrade head 2>&1 || {
    echo "❌ 数据库初始化失败"
    echo "💡 建议：删除 /app/data/bot.db 后重试"
    exit 1
}
echo "✅ 数据库就绪"

# 检查是否需要创建管理员用户
echo "👤 Checking for admin user..."
python3 init_admin.py || echo "⚠️  Admin user already exists or creation failed"

# 启动应用
echo "✅ Starting application..."
exec uvicorn main:app --host 0.0.0.0 --port 9393 --workers 1

