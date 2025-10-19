#!/bin/bash
# 运行 proto 诊断脚本

echo "🔍 运行 CloudDrive2 Proto 诊断..."
echo ""

# 尝试不同的方式
if command -v docker-compose &> /dev/null; then
    echo "使用 docker-compose exec..."
    docker-compose exec backend python /app/backend/diagnose_proto.py
elif command -v docker &> /dev/null; then
    echo "使用 docker exec..."
    sudo docker exec tmc python /app/backend/diagnose_proto.py
else
    echo "❌ 找不到 docker 或 docker-compose 命令"
    exit 1
fi

