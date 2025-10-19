#!/bin/bash
# 等待 GitHub Actions 构建完成并更新

REPO="Hav93/TMC"
BRANCH="test"
IMAGE="hav93/tmc:test"

echo "=========================================="
echo "🔄 等待 GitHub Actions 构建完成"
echo "=========================================="
echo ""
echo "📦 仓库: $REPO"
echo "🌿 分支: $BRANCH"
echo "🐳 镜像: $IMAGE"
echo ""

# 提示用户手动检查
echo "请访问以下链接查看构建状态："
echo "https://github.com/$REPO/actions"
echo ""
echo "等待构建完成后（看到绿色的 ✓），按任意键继续..."
read -n 1 -s

echo ""
echo "=========================================="
echo "📥 拉取最新镜像"
echo "=========================================="

# 停止容器
echo "🛑 停止容器..."
docker-compose down

# 删除旧镜像（强制拉取新镜像）
echo "🗑️  删除旧镜像..."
docker rmi $IMAGE 2>/dev/null || echo "旧镜像不存在"

# 拉取新镜像
echo "📥 拉取新镜像..."
docker-compose pull

# 启动容器
echo "🚀 启动新容器..."
docker-compose up -d

# 等待容器启动
echo "⏳ 等待容器启动..."
sleep 5

echo ""
echo "=========================================="
echo "🔍 验证 proto 文件"
echo "=========================================="

# 检查文件
echo ""
echo "1️⃣ 检查 /app/protos/ 目录："
docker exec tmc ls -lh /app/protos/ 2>&1

echo ""
echo "2️⃣ 尝试导入 proto："
docker exec tmc python -c "
import sys
sys.path.insert(0, '/app')
try:
    from protos import clouddrive_pb2
    print('✅ proto 导入成功！')
except Exception as e:
    print(f'❌ proto 导入失败: {e}')
"

echo ""
echo "=========================================="
echo "📋 查看最新日志"
echo "=========================================="
docker-compose logs --tail=50

echo ""
echo "✅ 更新完成！"
echo "请在前端界面触发上传测试"

