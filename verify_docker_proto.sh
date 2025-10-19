#!/bin/bash
# 验证 Docker 容器中的 proto 文件

echo "=========================================="
echo "🔍 验证 CloudDrive2 Proto 文件"
echo "=========================================="

CONTAINER_NAME="tmc"

echo ""
echo "1️⃣ 检查容器是否运行..."
if ! docker ps | grep -q $CONTAINER_NAME; then
    echo "❌ 容器未运行！"
    echo "请先运行: docker-compose up -d"
    exit 1
fi
echo "✅ 容器正在运行"

echo ""
echo "2️⃣ 检查 /app 目录结构..."
docker exec $CONTAINER_NAME ls -la /app/ | head -20

echo ""
echo "3️⃣ 检查 protos 目录..."
if docker exec $CONTAINER_NAME test -d /app/protos; then
    echo "✅ /app/protos 目录存在"
    docker exec $CONTAINER_NAME ls -la /app/protos/
else
    echo "❌ /app/protos 目录不存在！"
fi

echo ""
echo "4️⃣ 检查 backend 目录..."
if docker exec $CONTAINER_NAME test -d /app/backend; then
    echo "⚠️ /app/backend 目录存在（不应该存在！）"
    echo "这说明 Dockerfile COPY 有问题"
else
    echo "✅ /app/backend 目录不存在（正确）"
fi

echo ""
echo "5️⃣ 检查 proto Python 文件..."
for file in __init__.py clouddrive_pb2.py clouddrive_pb2_grpc.py clouddrive_pb2.pyi; do
    if docker exec $CONTAINER_NAME test -f /app/protos/$file; then
        size=$(docker exec $CONTAINER_NAME stat -f%z /app/protos/$file 2>/dev/null || docker exec $CONTAINER_NAME stat -c%s /app/protos/$file 2>/dev/null)
        echo "✅ $file ($size bytes)"
    else
        echo "❌ $file 不存在"
    fi
done

echo ""
echo "6️⃣ 测试 Python 导入..."
docker exec $CONTAINER_NAME python3 << 'EOF'
import sys
print(f"Python 版本: {sys.version}")
print(f"\nPython 路径 (前5个):")
for i, p in enumerate(sys.path[:5], 1):
    print(f"  {i}. {p}")

print("\n尝试导入 proto...")
try:
    # 添加 /app 到路径
    sys.path.insert(0, '/app')
    from protos import clouddrive_pb2
    print("✅ 成功: from protos import clouddrive_pb2")
except Exception as e:
    print(f"❌ 失败: {e}")
    
    # 检查目录
    import os
    if os.path.exists('/app/protos'):
        files = os.listdir('/app/protos')
        print(f"\n/app/protos 内容: {files}")
    else:
        print("\n/app/protos 不存在！")
EOF

echo ""
echo "=========================================="
echo "验证完成！"
echo "=========================================="

