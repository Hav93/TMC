#!/bin/bash
# 快速检查容器中的 proto 文件

echo "🔍 检查容器中的 proto 文件..."
echo ""

# 方法1: 直接列出文件
echo "1️⃣ 列出 /app/protos/ 目录："
docker exec tmc ls -lh /app/protos/ 2>&1 || echo "❌ 命令失败"

echo ""
echo "2️⃣ 检查 clouddrive_pb2.py 文件："
docker exec tmc test -f /app/protos/clouddrive_pb2.py && echo "✅ 文件存在" || echo "❌ 文件不存在"

echo ""
echo "3️⃣ 尝试导入 proto："
docker exec tmc python -c "
import sys
sys.path.insert(0, '/app')
try:
    from protos import clouddrive_pb2
    print('✅ 导入成功！')
except Exception as e:
    print(f'❌ 导入失败: {e}')
    import os
    if os.path.exists('/app/protos'):
        print(f'protos 目录内容: {os.listdir(\"/app/protos/\")}')
" 2>&1

echo ""
echo "4️⃣ 检查镜像构建时间："
docker inspect tmc --format='{{.Created}}' 2>&1 || echo "❌ 命令失败"

