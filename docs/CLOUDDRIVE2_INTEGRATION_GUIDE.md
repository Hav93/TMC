# CloudDrive2 集成使用手册

本文档提供了在任何Python项目中集成CloudDrive2 gRPC-Web客户端的完整指南。

## 目录

1. [概述](#概述)
2. [核心文件](#核心文件)
3. [依赖项](#依赖项)
4. [快速开始](#快速开始)
5. [核心实现](#核心实现)
6. [API使用示例](#api使用示例)
7. [常见问题](#常见问题)
8. [性能优化](#性能优化)

---

## 概述

CloudDrive2 是一个云盘挂载工具，使用 gRPC-Web 协议进行通信。本指南提供了完整的客户端实现，支持：

- ✅ 文件/目录浏览
- ✅ 磁力链接推送
- ✅ 文件上传/下载
- ✅ 目录管理（创建、删除、移动、复制）
- ✅ Token自动缓存
- ✅ 正确的Protobuf解析

---

## 核心文件

从本项目复制以下文件到您的项目：

```
your_project/
├── services/
│   ├── clouddrive2_client.py    # CloudDrive2客户端（核心）
│   └── clouddrive_pb2.py         # Protobuf定义和解析
└── requirements.txt              # 添加依赖
```

**文件说明**：

1. **`clouddrive2_client.py`** - CloudDrive2客户端实现
   - 提供完整的gRPC-Web通信
   - 支持所有CloudDrive2操作
   
2. **`clouddrive_pb2.py`** - Protobuf消息定义
   - 手工实现的Protobuf解析（无需.proto文件）
   - 包含varint解码和消息解析

---

## 依赖项

在 `requirements.txt` 中添加：

```txt
httpx>=0.24.0         # 异步HTTP客户端
protobuf>=4.21.0      # Protobuf支持
```

安装依赖：

```bash
pip install httpx protobuf
```

---

## 快速开始

### 1. 基本使用

```python
from services.clouddrive2_client import CloudDrive2Client

# 创建客户端
client = CloudDrive2Client(
    url="http://192.168.1.100:19798",  # CloudDrive2服务地址
    username="your_email@example.com",  # CloudDrive2账号
    password="your_password"            # CloudDrive2密码
)

# 浏览目录
async def browse_directory():
    result = await client.list_files("/")
    
    if result["success"]:
        for directory in result["directories"]:
            print(f"📁 {directory['name']} -> {directory['path']}")
        
        for file in result["files"]:
            print(f"📄 {file['name']} ({file['size']} bytes)")
    else:
        print(f"错误: {result['message']}")

# 运行
import asyncio
asyncio.run(browse_directory())
```

### 2. 客户端缓存（推荐）

为了避免重复获取token，建议使用客户端缓存：

```python
# 全局客户端缓存
_clouddrive_clients = {}

def get_cached_clouddrive_client(url: str, username: str, password: str):
    """获取缓存的CloudDrive客户端"""
    cache_key = f"{url}::{username}"
    
    if cache_key not in _clouddrive_clients:
        _clouddrive_clients[cache_key] = CloudDrive2Client(
            url=url,
            username=username,
            password=password
        )
    else:
        # 检查密码是否变化
        existing_client = _clouddrive_clients[cache_key]
        if existing_client.password != password:
            _clouddrive_clients[cache_key] = CloudDrive2Client(
                url=url,
                username=username,
                password=password
            )
    
    return _clouddrive_clients[cache_key]

# 使用缓存客户端
client = get_cached_clouddrive_client(
    url="http://192.168.1.100:19798",
    username="user@example.com",
    password="password"
)
```

---

## 核心实现

### Protobuf解析关键点

CloudDrive2的Protobuf结构有以下特点：

#### 1. FileItem结构

```python
# CloudDriveFile消息结构
{
    field 1: id (string)          # 文件/目录ID
    field 2: name (string)        # 名称
    field 3: path (string)        # 完整路径
    field 5: size (varint)        # 大小（字节）
    field 6: createTime (message) # 创建时间
    field 7: writeTime (message)  # 修改时间
    field 9: metadata (message)   # 元数据（包含isFolder标记）
}
```

#### 2. isFolder标记的位置

**关键发现**：`isFolder` 不是直接字段，而是在 **field 9（元数据）** 的嵌套消息中：

```python
# field 9 内部结构
if b'\x40\x01' in field_9_bytes:  # 0x40 = field 8, 0x01 = true
    is_folder = True
```

#### 3. 根目录挂载点的特殊处理

CloudDrive2的根目录挂载点（如`115open`、`阿里云盘Open`）可能不包含isFolder标记，需要智能推断：

```python
# 智能判断逻辑
if not is_folder and size == 0:
    if path == '/' and name in item_path:
        is_folder = True  # 推断为挂载点
```

### Varint解码

Protobuf使用varint编码整数，需要正确解码：

```python
def _decode_varint(data, pos):
    """解码protobuf varint"""
    result = 0
    shift = 0
    while pos < len(data):
        byte = data[pos]
        pos += 1
        result |= (byte & 0x7f) << shift
        if not (byte & 0x80):
            return result, pos
        shift += 7
    return result, pos
```

### gRPC-Web Payload格式

```python
# gRPC-Web请求格式
payload = b'\x00' + struct.pack('>I', len(protobuf_bytes)) + protobuf_bytes

# gRPC-Web响应格式
message_bytes = response_content[5:5+length]  # 跳过前5字节
```

---

## API使用示例

### 1. 浏览目录

```python
async def list_directory(path="/"):
    result = await client.list_files(path)
    return result
    # 返回: {
    #   "success": True,
    #   "directories": [{"name": "...", "path": "...", "isDirectory": True}],
    #   "files": [{"name": "...", "path": "...", "size": 123, "isDirectory": False}],
    #   "current_path": "/",
    #   "message": "成功解析 X 个目录, Y 个文件"
    # }
```

### 2. 推送磁力链接

```python
async def add_magnet(magnet_url: str, target_path: str = "/"):
    result = await client.push_magnet_with_folder(
        magnet_urls=[magnet_url],
        target_path=target_path
    )
    return result
    # 返回: {"success": True/False, "message": "..."}
```

### 3. 创建目录

```python
async def create_directory(path: str):
    result = await client.create_folder(path)
    return result
```

### 4. 删除文件/目录

```python
async def delete_item(path: str):
    result = await client.delete_file(path)
    return result
```

### 5. 移动/复制文件

```python
# 移动
result = await client.move_file(
    source_path="/source/file.txt",
    target_path="/dest/file.txt"
)

# 复制
result = await client.copy_file(
    source_path="/source/file.txt",
    target_path="/dest/file.txt"
)
```

### 6. 上传文件

```python
async def upload_file(local_path: str, remote_path: str):
    result = await client.upload_file(
        local_file_path=local_path,
        remote_path=remote_path,
        file_name="custom_name.txt"  # 可选
    )
    return result
```

---

## 常见问题

### Q1: 为什么目录显示为文件？

**A**: CloudDrive2的protobuf响应中，`isFolder`标记位于field 9的嵌套消息中。确保正确解析：

```python
# 在clouddrive_pb2.py的CloudDriveFile.ParseFromString()中
elif field_number == 9:  # field 9 - 元数据
    if b'\x40\x01' in value_bytes:
        self.isFolder = True
```

### Q2: 根目录的挂载点（如115open）显示不正确？

**A**: 挂载点可能没有isFolder标记，使用智能推断：

```python
if not is_directory and item.size == 0:
    if path in ['/', ''] and item.name in item.path:
        is_directory = True
```

### Q3: 加载速度慢？

**A**: 实现token缓存和客户端缓存（见上文"客户端缓存"部分）。

### Q4: 连接失败或404错误？

**A**: 
- 确认CloudDrive2服务地址正确（通常是 `http://IP:19798`）
- 确认使用gRPC-Web端点（不是REST API）
- 检查用户名密码是否正确

### Q5: 中文目录名乱码？

**A**: 确保使用UTF-8解码：

```python
name = value_bytes.decode('utf-8', errors='ignore')
```

---

## 性能优化

### 1. Token缓存

CloudDrive2的token有效期较长，缓存token避免重复获取：

```python
class CloudDrive2Client:
    def __init__(self, url, username, password):
        self._token_cache = None  # Token缓存
    
    async def get_token(self):
        if self._token_cache:
            return self._token_cache  # 复用缓存
        # ... 获取新token
```

### 2. 客户端实例复用

避免每次请求都创建新的客户端实例：

```python
# 全局缓存
_clients = {}

def get_client(url, username, password):
    key = f"{url}::{username}"
    if key not in _clients:
        _clients[key] = CloudDrive2Client(url, username, password)
    return _clients[key]
```

### 3. 减少日志输出

生产环境移除详细日志：

```python
# 移除或注释掉debug日志
# logger.debug(f"解析item: {data.hex()}")
```

### 4. 异步批量操作

对于批量操作，使用异步并发：

```python
import asyncio

async def batch_list_directories(paths):
    tasks = [client.list_files(path) for path in paths]
    results = await asyncio.gather(*tasks)
    return results
```

---

## 集成到FastAPI示例

```python
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter()

# 客户端缓存
_clients = {}

def get_cached_client(url: str, username: str, password: str):
    key = f"{url}::{username}"
    if key not in _clients:
        _clients[key] = CloudDrive2Client(url, username, password)
    return _clients[key]

@router.post("/browse")
async def browse_directory(data: Dict[str, Any]):
    """浏览CloudDrive目录"""
    url = data.get("url")
    username = data.get("username", "")
    password = data.get("password", "")
    path = data.get("path", "/")
    
    if not url:
        raise HTTPException(status_code=400, detail="URL不能为空")
    
    client = get_cached_client(url, username, password)
    result = await client.list_files(path)
    
    return result

@router.post("/push-magnet")
async def push_magnet(data: Dict[str, Any]):
    """推送磁力链接"""
    url = data.get("url")
    username = data.get("username", "")
    password = data.get("password", "")
    magnet_url = data.get("magnet_url")
    target_path = data.get("target_path", "/")
    
    if not url or not magnet_url:
        raise HTTPException(status_code=400, detail="缺少必要参数")
    
    client = get_cached_client(url, username, password)
    result = await client.push_magnet_with_folder(
        magnet_urls=[magnet_url],
        target_path=target_path
    )
    
    return result
```

---

## 完整代码结构

```python
your_project/
├── services/
│   ├── __init__.py
│   ├── clouddrive2_client.py      # CloudDrive2客户端
│   └── clouddrive_pb2.py           # Protobuf定义
├── api/
│   └── clouddrive.py               # API路由（可选）
├── requirements.txt
└── main.py
```

---

## 测试示例

```python
import asyncio
from services.clouddrive2_client import CloudDrive2Client

async def test_clouddrive():
    # 创建客户端
    client = CloudDrive2Client(
        url="http://192.168.1.100:19798",
        username="test@example.com",
        password="password123"
    )
    
    # 1. 测试连接
    token = await client.get_token()
    print(f"✅ Token获取成功: {token[:20]}...")
    
    # 2. 浏览根目录
    result = await client.list_files("/")
    print(f"✅ 根目录: {len(result['directories'])} 个目录")
    
    # 3. 创建目录
    result = await client.create_folder("/test_folder")
    print(f"✅ 创建目录: {result['message']}")
    
    # 4. 推送磁力链接
    result = await client.push_magnet(
        ["magnet:?xt=urn:btih:..."],
        "/test_folder"
    )
    print(f"✅ 推送磁力: {result['message']}")
    
    print("\n所有测试通过！")

if __name__ == "__main__":
    asyncio.run(test_clouddrive())
```

---

## 注意事项

1. **协议版本**：本实现基于CloudDrive2的gRPC-Web协议，与REST API不兼容
2. **网络环境**：确保能访问CloudDrive2服务（无代理干扰）
3. **并发限制**：CloudDrive2可能有并发请求限制，建议使用客户端缓存
4. **错误处理**：所有方法都返回`{"success": bool, "message": str}`格式
5. **路径格式**：路径必须以`/`开头，如`/115open/folder`

---

## 许可证

本集成代码基于实际CloudDrive2协议逆向工程，仅供学习和个人使用。

---

## 更新日志

- **v1.0** (2025-01-09)
  - 初始版本
  - 完整的gRPC-Web实现
  - 正确的Protobuf解析（包括isFolder标记）
  - Token缓存机制
  - 支持所有主要操作

---

**祝使用愉快！如有问题，请查看源码或提交Issue。**

