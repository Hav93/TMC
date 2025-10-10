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

# 修复 Alembic 版本记录（如果需要）
echo "🔧 Checking Alembic version..."
cd /app
python3 fix_alembic_version.py || echo "⚠️  Version check skipped"

# 检查数据库状态
echo "🔍 Checking database schema..."
python3 check_and_fix_schema.py || echo "⚠️  Schema check completed with warnings"

# 运行数据库迁移
echo "📦 Running database migrations..."
alembic upgrade head 2>&1 || echo "⚠️  Migration failed or already up to date"
echo "✅ Migration completed"

# 检查是否需要创建管理员用户
echo "👤 Checking for admin user..."
python3 init_admin.py || echo "⚠️  Admin user already exists or creation failed"

# 启动应用
echo "✅ Starting application..."
exec uvicorn main:app --host 0.0.0.0 --port 9393 --workers 1

