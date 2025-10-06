#!/bin/bash
set -e

echo "🚀 Starting Telegram Message Forwarder..."

# 等待数据库文件目录准备好
mkdir -p /app/data /app/logs /app/sessions /app/temp /app/config

# 运行数据库迁移
echo "📦 Running database migrations..."
cd /app
alembic upgrade head || echo "⚠️  Migration failed or already up to date"

# 检查是否需要创建管理员用户
echo "👤 Checking for admin user..."
python3 init_admin.py || echo "⚠️  Admin user already exists or creation failed"

# 启动应用
echo "✅ Starting application..."
exec uvicorn main:app --host 0.0.0.0 --port 9393 --workers 1

