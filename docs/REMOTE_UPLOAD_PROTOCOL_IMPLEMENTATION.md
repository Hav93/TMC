# CloudDrive2 远程上传协议实现指南

## 📋 当前状态

**实现进度**: 70% 完成

- ✅ 官方 proto 集成
- ✅ `StartRemoteUpload` RPC 调用
- ✅ 路径处理修复
- ⏳ `RemoteUploadChannel` 双向流式通信
- ⏳ `RemoteReadData` / `RemoteHashProgress` 响应

---

## 🔄 远程上传协议流程

### 官方协议设计

CloudDrive2 的远程上传协议是**基于服务器驱动的双向流式通信**：

```
客户端                                     服务器
   |                                          |
   |------ StartRemoteUpload ---------------->|
   |<------ upload_id ------------------------|
   |                                          |
   |------ RemoteUploadChannel (stream) ----->|
   |                                          |
   |<------ read_data(offset, length) --------|  服务器请求数据
   |------ RemoteReadData(data) ------------->|  客户端发送数据
   |                                          |
   |<------ hash_data ----------------------->|  服务器请求哈希
   |------ RemoteHashProgress -------------->|  客户端发送哈希进度
   |                                          |
   |<------ status_changed(Uploading) --------|
   |<------ status_changed(Success) ----------|  上传完成！
   |                                          |
```

### 关键特点

1. **服务器驱动**: 服务器主动请求需要的数据
2. **按需传输**: 只传输服务器请求的部分
3. **实时状态**: 通过 channel 推送状态变化
4. **无需 Complete**: 服务器决定何时完成

---

## 💻 实现细节

### 步骤 1: 启动上传会话 ✅

```python
# 已实现
request = clouddrive_pb2.StartRemoteUploadRequest(
    file_path='/115/视频/test.mp4',  # 远程路径
    file_size=1024000,
    device_id='TMC'
)

response = await stub.StartRemoteUpload(request)
upload_id = response.upload_id
```

**状态**: ✅ 完成

---

### 步骤 2: 监听上传通道 ⏳

```python
# 需要实现
async def handle_upload_channel(upload_id, local_file_path):
    """处理远程上传通道"""
    
    # 创建通道请求
    request = clouddrive_pb2.RemoteUploadChannelRequest(
        device_id='TMC'
    )
    
    # 监听服务器流式推送
    async for reply in stub.RemoteUploadChannel(request):
        if reply.upload_id != upload_id:
            continue  # 跳过其他上传任务
        
        # 处理不同类型的服务器请求
        if reply.HasField('read_data'):
            # 服务器请求读取文件数据
            await handle_read_data(reply.read_data, local_file_path)
        
        elif reply.HasField('hash_data'):
            # 服务器请求计算哈希
            await handle_hash_data(reply.hash_data, local_file_path)
        
        elif reply.HasField('status_changed'):
            # 上传状态变化
            status = reply.status_changed.status
            if status == UploadFileInfo.Success:
                logger.info("✅ 上传成功！")
                break
            elif status == UploadFileInfo.Error:
                error = reply.status_changed.error_message
                logger.error(f"❌ 上传失败: {error}")
                break
```

**状态**: ⏳ 待实现

---

### 步骤 3: 响应读取数据请求 ⏳

```python
# 需要实现
async def handle_read_data(read_data_request, local_file_path):
    """响应服务器的数据读取请求"""
    
    offset = read_data_request.offset
    length = read_data_request.length
    lazy_read = read_data_request.lazy_read
    
    # 从本地文件读取数据
    with open(local_file_path, 'rb') as f:
        f.seek(offset)
        data = f.read(length)
    
    # 发送数据给服务器
    request = clouddrive_pb2.RemoteReadDataUpload(
        upload_id=upload_id,
        offset=offset,
        length=len(data),
        data=data
    )
    
    response = await stub.RemoteReadData(request)
    
    if response.received:
        logger.info(f"✅ 数据块已发送: offset={offset}, length={len(data)}")
    else:
        logger.error(f"❌ 数据块发送失败")
```

**状态**: ⏳ 待实现

---

### 步骤 4: 响应哈希计算请求 ⏳

```python
# 需要实现
async def handle_hash_data(hash_data_request, local_file_path):
    """响应服务器的哈希计算请求"""
    
    file_size = os.path.getsize(local_file_path)
    
    # 计算哈希并报告进度
    with open(local_file_path, 'rb') as f:
        bytes_hashed = 0
        chunk_size = 1024 * 1024  # 1MB
        
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            
            bytes_hashed += len(chunk)
            
            # 报告进度
            request = clouddrive_pb2.RemoteHashProgressUpload(
                upload_id=upload_id,
                bytes_hashed=bytes_hashed,
                total_bytes=file_size
            )
            
            await stub.RemoteHashProgress(request)
            
            # 每 10MB 报告一次
            if bytes_hashed % (10 * 1024 * 1024) == 0:
                logger.info(f"📊 哈希进度: {bytes_hashed}/{file_size} ({bytes_hashed/file_size*100:.1f}%)")
```

**状态**: ⏳ 待实现

---

## 🎯 实现计划

### 阶段 1: 重构上传流程 (当前)

需要修改 `_upload_via_remote_protocol`:

```python
# 当前实现（错误）
async def _upload_via_remote_protocol(self, local_path, remote_path, ...):
    # ❌ 主动分块上传
    for chunk in read_file_chunks(local_path):
        await self._upload_chunk(session_id, chunk)
    
    # ❌ 主动调用 Complete
    await self._complete_upload_session(session_id)
```

```python
# 正确实现（服务器驱动）
async def _upload_via_remote_protocol(self, local_path, remote_path, ...):
    # 1. 启动会话
    session_id = await self._create_upload_session(...)
    
    # 2. 处理上传通道（服务器驱动）
    result = await self._handle_remote_upload_channel(
        session_id=session_id,
        local_path=local_path
    )
    
    return result
```

### 阶段 2: 实现通道处理

创建新方法 `_handle_remote_upload_channel`:

```python
async def _handle_remote_upload_channel(
    self,
    session_id: str,
    local_path: str
) -> Dict[str, Any]:
    """
    处理远程上传通道
    
    监听服务器请求并响应
    """
    try:
        # 创建通道
        request = clouddrive_pb2.RemoteUploadChannelRequest(
            device_id='TMC'
        )
        
        # 监听服务器流式推送
        async for reply in self.stub.RemoteUploadChannel(request):
            if reply.upload_id != session_id:
                continue
            
            # 处理服务器请求
            if reply.HasField('read_data'):
                await self._handle_read_request(
                    session_id, 
                    reply.read_data, 
                    local_path
                )
            elif reply.HasField('hash_data'):
                await self._handle_hash_request(
                    session_id,
                    reply.hash_data,
                    local_path
                )
            elif reply.HasField('status_changed'):
                status = reply.status_changed.status
                if status == UploadFileInfo.Success:
                    return {'success': True, 'message': '上传成功'}
                elif status == UploadFileInfo.Error:
                    return {
                        'success': False, 
                        'message': reply.status_changed.error_message
                    }
        
        return {'success': False, 'message': '上传通道关闭'}
    
    except Exception as e:
        logger.error(f"❌ 上传通道处理失败: {e}")
        return {'success': False, 'message': str(e)}
```

### 阶段 3: 实现请求处理器

```python
async def _handle_read_request(
    self,
    session_id: str,
    read_request: clouddrive_pb2.RemoteReadDataRequest,
    local_path: str
):
    """处理读取数据请求"""
    # 实现细节见上文

async def _handle_hash_request(
    self,
    session_id: str,
    hash_request: clouddrive_pb2.RemoteHashDataRequest,
    local_path: str
):
    """处理哈希计算请求"""
    # 实现细节见上文
```

---

## 📊 Proto 消息定义

### StartRemoteUploadRequest

```protobuf
message StartRemoteUploadRequest {
  string file_path = 1;      // 远程路径
  uint64 file_size = 2;      // 文件大小
  string device_id = 3;      // 设备ID
}
```

### RemoteUploadChannelRequest

```protobuf
message RemoteUploadChannelRequest {
  string device_id = 1;      // 设备ID
}
```

### RemoteUploadChannelReply

```protobuf
message RemoteUploadChannelReply {
  string upload_id = 1;
  oneof request {
    RemoteReadDataRequest read_data = 2;
    RemoteHashDataRequest hash_data = 3;
    RemoteUploadStatusChanged status_changed = 4;
  }
}
```

### RemoteReadDataRequest

```protobuf
message RemoteReadDataRequest {
  uint64 offset = 1;         // 读取偏移量
  uint64 length = 2;         // 读取长度
  bool lazy_read = 3;        // 延迟读取
}
```

### RemoteReadDataUpload

```protobuf
message RemoteReadDataUpload {
  string upload_id = 1;
  uint64 offset = 3;
  uint64 length = 4;
  bytes data = 5;            // 文件数据
}
```

---

## 🐛 已知问题

### 问题 1: CompleteUpload 未实现

**状态**: 不需要实现  
**原因**: 远程上传协议由服务器控制完成，通过 `status_changed` 通知

### 问题 2: 当前使用同步分块上传

**状态**: 需要重构  
**原因**: 应该使用服务器驱动的按需传输

### 问题 3: 没有监听 RemoteUploadChannel

**状态**: 需要实现  
**原因**: 这是协议的核心，必须监听服务器请求

---

## ✅ 下一步行动

1. **立即**: 实现 `_handle_remote_upload_channel` 方法
2. **然后**: 实现 `_handle_read_request` 和 `_handle_hash_request`
3. **测试**: 完整的上传流程
4. **优化**: 进度报告、错误处理、重试机制

---

## 📖 参考资料

1. **官方 Proto**: `app/backend/protos/clouddrive.proto` (行 451-1807)
2. **远程上传协议**: 搜索 "Remote Upload Protocol"
3. **示例代码**: `app/backend/services/clouddrive_official_client.py`

---

**文档版本**: 1.0  
**更新日期**: 2025-10-19  
**状态**: 🟡 实施中

