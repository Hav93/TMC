#!/bin/bash
# 检查 Docker 容器内的文件结构

echo "=== 检查 protos 目录 ==="
docker exec tmc ls -la /app/backend/protos/

echo ""
echo "=== 检查 proto Python 文件 ==="
docker exec tmc ls -la /app/backend/protos/*.py

echo ""
echo "=== 检查 Python 路径 ==="
docker exec tmc python -c "import sys; print('\n'.join(sys.path))"

echo ""
echo "=== 尝试导入 proto ==="
docker exec tmc python -c "
import sys
from pathlib import Path
sys.path.insert(0, '/app/backend')
print('Python path:', sys.path[:3])
try:
    from protos import clouddrive_pb2
    print('✅ 导入成功!')
except Exception as e:
    print(f'❌ 导入失败: {e}')
    import os
    print('protos 目录内容:', os.listdir('/app/backend/protos/'))
"

