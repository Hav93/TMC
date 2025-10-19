# 🔍 容器调试指南

## 问题现状
- ✅ 本地 proto 文件存在且可导入
- ✅ GitHub Actions 构建成功（5分钟前完成）
- ❌ 容器中无法导入 proto 文件

## 立即执行的调试命令

### 1. 强制更新镜像
```bash
# 停止并删除旧容器和镜像
docker-compose down
docker rmi hav93/tmc:test -f

# 拉取最新镜像
docker-compose pull

# 启动新容器
docker-compose up -d
```

### 2. 验证容器中的文件
```bash
# 检查 protos 目录
docker exec tmc ls -lh /app/protos/

# 应该看到：
# clouddrive_pb2.py (约 108K)
# clouddrive_pb2_grpc.py (约 330K)
# __init__.py

# 如果看不到这些文件，说明 Docker 构建有问题
```

### 3. 测试导入
```bash
docker exec tmc python -c "
import sys
sys.path.insert(0, '/app')
from protos import clouddrive_pb2
print('SUCCESS')
"
```

### 4. 查看镜像构建时间
```bash
# 检查镜像是否真的是最新的
docker inspect hav93/tmc:test --format='{{.Created}}'

# 应该显示最近的时间（5-10分钟前）
```

## 可能的问题

### 问题 A: Docker 缓存
即使 `docker-compose pull` 也可能使用缓存。解决方法：
```bash
docker rmi hav93/tmc:test -f
docker pull hav93/tmc:test --no-cache
```

### 问题 B: .dockerignore 还在生效
虽然我们修复了 `.dockerignore`，但 GitHub Actions 可能还在用缓存的构建环境。
解决方法：等待下一次构建，或在 GitHub Actions 中手动触发重新构建。

### 问题 C: 文件确实在镜像中，但 Python 路径不对
解决方法：检查 Python 路径
```bash
docker exec tmc python -c "import sys; print('\n'.join(sys.path))"
```

## 预期结果

成功的话应该看到：
```bash
$ docker exec tmc ls -lh /app/protos/
-rw-r--r-- 1 root root 108K Oct 19 12:45 clouddrive_pb2.py
-rw-r--r-- 1 root root 330K Oct 19 12:45 clouddrive_pb2_grpc.py
-rw-r--r-- 1 root root  289 Oct 19 12:46 __init__.py

$ docker exec tmc python -c "..."
SUCCESS
```

## 如果还是失败

请把以下信息发给我：

1. **镜像构建时间**
   ```bash
   docker inspect hav93/tmc:test --format='{{.Created}}'
   ```

2. **容器中的目录结构**
   ```bash
   docker exec tmc ls -la /app/protos/
   ```

3. **Python 导入错误**
   ```bash
   docker exec tmc python -c "import sys; sys.path.insert(0, '/app'); from protos import clouddrive_pb2" 2>&1
   ```

4. **镜像层信息**
   ```bash
   docker history hav93/tmc:test | head -20
   ```

