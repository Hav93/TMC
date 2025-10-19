# CloudDrive2 Python SDK 集成指南

## 📚 官方文档

CloudDrive2 官方 API 文档提供了完整的 Python 配置和代码实现：

- **官方文档**: https://www.clouddrive2.com/api/
- **Python 配置**: 查看官方文档中的 "Python 配置" 部分
- **API 参考**: 包含完整的 gRPC API 定义

## 🎯 当前实现状态

### ✅ 已实现

1. **HTTP REST API 客户端** (`clouddrive2_http_client.py`)
   - ✅ 挂载点列表
   - ✅ 文件列表
   - ✅ 创建目录
   - ✅ 认证支持

2. **gRPC 框架** (`clouddrive2_grpc_impl.py`)
   - ✅ 连接管理
   - ✅ 通道配置
   - ✅ 方法定义（待 proto 实现）

3. **统一客户端** (`clouddrive2_client.py`)
   - ✅ 智能上传策略
   - ✅ 本地挂载 + 远程 gRPC
   - ✅ 进度管理
   - ✅ 断点续传

### ⏳ 待完善

1. **Protobuf 定义**
   - 需要官方 `.proto` 文件
   - 或参考官方 Python SDK 的实现

2. **gRPC Stub 生成**
   ```bash
   # 需要运行
   python -m grpc_tools.protoc \
       -I. \
       --python_out=. \
       --grpc_python_out=. \
       protos/clouddrive2.proto
   ```

## 🔧 如何获取官方 Python SDK

### 方法 1: 查看官方文档

访问 https://www.clouddrive2.com/api/ 并查看 **Python 配置** 部分：

1. 点击侧边栏的 "Python 配置"
2. 查看示例代码
3. 下载官方提供的 Python SDK 包

### 方法 2: 从 CloudDrive2 安装包中提取

如果您已安装 CloudDrive2，可能包含 Python SDK：

```bash
# Windows
C:\Program Files\CloudDrive2\sdk\python\

# Linux/Docker
/opt/clouddrive2/sdk/python/
```

### 方法 3: 使用官方 GitHub（如果有）

```bash
git clone https://github.com/cloud-fs/clouddrive2-python-sdk.git
cd clouddrive2-python-sdk
pip install -e .
```

## 📦 集成官方 SDK

### 步骤 1: 安装依赖

```bash
pip install grpcio grpcio-tools protobuf
```

### 步骤 2: 复制官方 Proto 文件

将官方的 `.proto` 文件复制到项目中：

```bash
# 假设官方 SDK 在 /path/to/clouddrive2-sdk/
cp /path/to/clouddrive2-sdk/proto/*.proto app/backend/protos/
```

### 步骤 3: 生成 Python 代码

```bash
cd app/backend
python generate_grpc.py
```

### 步骤 4: 更新 Stub 实现

用生成的代码替换 `clouddrive2_stub.py` 中的占位符：

```python
# 导入生成的代码
from protos import clouddrive2_pb2
from protos import clouddrive2_pb2_grpc

class CloudDrive2Stub:
    def __init__(self, channel):
        self.channel = channel
        # 使用生成的 stub
        self.fs_stub = clouddrive2_pb2_grpc.FileSystemStub(channel)
        self.upload_stub = clouddrive2_pb2_grpc.UploadStub(channel)
        self.mount_stub = clouddrive2_pb2_grpc.MountStub(channel)
    
    async def ListMounts(self, request=None):
        # 使用真实的 gRPC 调用
        request = clouddrive2_pb2.Empty()
        response = await self.mount_stub.ListMounts(request)
        return [
            {
                'name': m.name,
                'path': m.path,
                'cloud_type': m.cloud_type,
                'mounted': m.mounted
            }
            for m in response.mounts
        ]
```

## 🚀 使用示例

### 基本使用

```python
from services.clouddrive2_client import create_clouddrive2_client

# 创建客户端
client = await create_clouddrive2_client()

# 连接
await client.connect()

# 获取挂载点
mounts = await client.get_mount_points()
print(f"找到 {len(mounts)} 个挂载点")

# 上传文件
result = await client.upload_file(
    local_path='/tmp/video.mp4',
    remote_path='/115/视频/test.mp4',
    mount_point='/115'
)

print(f"上传结果: {result}")
```

### 使用上下文管理器

```python
async with create_clouddrive2_client() as client:
    # 列出文件
    files = await client.list_files('/115/视频')
    
    # 创建目录
    await client.create_folder('/115/新目录')
    
    # 上传文件
    await client.upload_file(
        local_path='movie.mp4',
        remote_path='/115/新目录/movie.mp4'
    )
```

## 📝 API 对照表

| 功能 | HTTP API | gRPC API | TMC 实现 |
|------|----------|----------|----------|
| 列出挂载点 | GET /api/mounts | Mount.List | ✅ |
| 列出文件 | GET /api/fs/list | FileSystem.List | ✅ |
| 创建目录 | POST /api/fs/mkdir | FileSystem.Mkdir | ✅ |
| 创建上传会话 | POST /api/upload/create | Upload.CreateSession | ✅ 框架 |
| 上传数据块 | POST /api/upload/chunk | Upload.DataStream | ✅ 框架 |
| 完成上传 | POST /api/upload/complete | Upload.Complete | ✅ 框架 |

## 🔍 调试指南

### 查看 gRPC 日志

```python
import logging

# 启用 gRPC 日志
logging.basicConfig()
logging.getLogger('grpc').setLevel(logging.DEBUG)
```

### 测试连接

```python
from services.clouddrive2_grpc_impl import create_grpc_client

async def test_connection():
    client = await create_grpc_client(
        host='192.168.31.67',
        port=19798
    )
    
    if client.connected:
        print("✅ 连接成功")
        
        # 测试 API
        mounts = await client.mount_list()
        print(f"挂载点: {mounts}")
    else:
        print("❌ 连接失败")

import asyncio
asyncio.run(test_connection())
```

## 📖 参考资料

1. **CloudDrive2 官方文档**
   - API 参考: https://www.clouddrive2.com/api/
   - gRPC API 指南: https://www.clouddrive2.com/api/CloudDrive2_gRPC_API_Guide.html

2. **gRPC Python 文档**
   - 官方教程: https://grpc.io/docs/languages/python/
   - Async API: https://grpc.github.io/grpc/python/grpc_asyncio.html

3. **Protobuf 文档**
   - 语言指南: https://developers.google.com/protocol-buffers/docs/proto3
   - Python 生成: https://developers.google.com/protocol-buffers/docs/pythontutorial

## 💡 常见问题

### Q: 为什么 gRPC 调用返回空数据？

A: 当前使用的是占位符实现，需要：
1. 获取官方 `.proto` 文件
2. 生成 Python gRPC 代码
3. 更新 stub 实现

### Q: 可以只使用 HTTP API 吗？

A: 可以！当前已实现 HTTP API 作为备选：
- ✅ 挂载点列表
- ✅ 文件操作
- ⚠️ 上传功能建议使用 gRPC（更高效）

### Q: 如何切换 HTTP/gRPC？

A: 在 `clouddrive2_stub.py` 中设置：

```python
self._use_http_fallback = True   # 使用 HTTP
self._use_http_fallback = False  # 使用 gRPC
```

## 🎉 贡献

如果您获取到了官方的 Python SDK 或 `.proto` 文件，欢迎提交 PR！

1. Fork 项目
2. 添加官方文件到 `app/backend/protos/`
3. 更新实现
4. 提交 PR

---

**最后更新**: 2025-10-19  
**文档版本**: 1.0  
**作者**: TMC Team

