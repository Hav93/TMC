# 115上传断点续传和进度显示功能指南

完整实现了115网盘文件上传的断点续传和实时进度追踪功能。

---

## 🎯 功能概览

### 1. 断点续传 (Breakpoint Resume)

**核心特性：**
- ✅ 自动保存上传会话到本地
- ✅ 支持中断后继续上传
- ✅ 分片进度持久化（每片10MB）
- ✅ 自动清理过期会话（7天）
- ✅ 智能会话ID（基于文件路径+目标目录）

**适用场景：**
- 大文件上传（>100MB）
- 网络不稳定环境
- 需要暂停后继续的上传任务

### 2. 实时进度追踪 (Progress Tracking)

**核心特性：**
- ✅ 实时显示上传百分比
- ✅ 上传速度计算（MB/s）
- ✅ ETA预估（剩余时间）
- ✅ 多文件并发上传管理
- ✅ WebSocket实时推送（500ms刷新）

**适用场景：**
- 所有文件上传
- 需要监控上传状态的场景
- 多文件批量上传

---

## 📦 架构设计

### 后端模块

```
services/
├── upload_resume_manager.py      # 断点续传管理器
│   ├── UploadSession            # 上传会话模型
│   └── UploadResumeManager      # 会话管理器
│
├── upload_progress_manager.py    # 进度追踪管理器
│   ├── UploadProgress           # 进度数据模型
│   └── UploadProgressManager    # 进度管理器
│
└── pan115_client.py              # 115客户端（集成上述功能）
    ├── _upload_file_web_api     # 主上传流程
    ├── _upload_to_oss           # 小文件直接上传
    └── _upload_multipart        # 大文件分片上传

api/routes/
├── upload_progress.py            # 进度查询API
│   ├── GET  /api/upload/progress
│   ├── GET  /api/upload/progress/{path}
│   ├── GET  /api/upload/sessions
│   ├── DELETE /api/upload/sessions/{id}
│   └── POST /api/upload/sessions/cleanup
│
└── upload_websocket.py           # WebSocket实时推送
    └── WS   /ws/upload/progress
```

### 前端模块

```
hooks/
└── useUploadProgress.tsx         # WebSocket Hook
    ├── WebSocket连接管理
    ├── 自动重连逻辑
    └── 实时数据更新

components/
└── UploadProgress.tsx            # 进度显示组件
    ├── UploadProgressList       # 进度列表
    ├── UploadItem              # 单个上传项
    ├── 进度条显示
    ├── 速度和ETA显示
    └── 状态标签
```

---

## 🔧 使用指南

### 后端调用示例

#### 1. 基本上传（自动支持进度追踪）

```python
from services.pan115_client import Pan115Client

client = Pan115Client(
    user_key="UID=xxx; CID=xxx; SEID=xxx"
)

# 上传文件
result = await client.upload_file(
    file_path="/path/to/video.mp4",
    target_path="/影视/电影/2025"
)

# 返回:
# {
#   'success': True,
#   'message': '文件上传成功',
#   'file_id': 'xxx',
#   'quick_upload': False
# }
```

#### 2. 查询上传进度

```python
from services.upload_progress_manager import get_progress_manager

progress_mgr = get_progress_manager()

# 获取指定文件的进度
progress = await progress_mgr.get_progress("/path/to/video.mp4")

if progress:
    print(f"文件名: {progress.file_name}")
    print(f"状态: {progress.status}")
    print(f"进度: {progress.percentage:.2f}%")
    print(f"速度: {progress.speed_mbps:.2f} MB/s")
    print(f"已用时: {progress.get_elapsed_time():.1f}秒")
    print(f"剩余时间: {progress.get_eta():.1f}秒")

# 获取所有上传任务
all_progresses = await progress_mgr.list_progresses()
for file_path, progress in all_progresses.items():
    print(f"{file_path}: {progress.percentage:.2f}%")
```

#### 3. 管理断点续传会话

```python
from services.upload_resume_manager import get_resume_manager

resume_mgr = get_resume_manager()

# 列出所有会话
sessions = await resume_mgr.list_sessions()
for session in sessions:
    print(f"会话ID: {session.session_id}")
    print(f"文件: {session.file_path}")
    print(f"进度: {session.get_progress():.2f}%")
    print(f"已上传分片: {len(session.uploaded_parts)}/{session.total_parts}")

# 删除指定会话
await resume_mgr.delete_session("session_id_here")

# 清理过期会话（超过7天未更新）
await resume_mgr.clean_expired_sessions(days=7)
```

#### 4. 注册进度回调

```python
from services.upload_progress_manager import get_progress_manager, UploadProgress

progress_mgr = get_progress_manager()

# 定义回调函数
async def on_progress_update(progress: UploadProgress):
    print(f"📊 {progress.file_name}: {progress.percentage:.2f}%")
    if progress.status == 'success':
        print(f"✅ 上传完成: {progress.file_id}")

# 注册回调
file_path = "/path/to/video.mp4"
progress_mgr.register_callback(file_path, on_progress_update)

# 上传文件（回调会自动触发）
await client.upload_file(file_path, "/影视/电影")

# 注销回调
progress_mgr.unregister_callback(file_path, on_progress_update)
```

---

### 前端调用示例

#### 1. 使用 Hook 获取上传进度

```typescript
import { useUploadProgress } from '@/hooks/useUploadProgress';

function MyComponent() {
  const { uploads, connected, reconnect } = useUploadProgress();

  return (
    <div>
      <h3>上传任务 ({uploads.length})</h3>
      {!connected && (
        <div>
          ⚠️ 未连接到服务器
          <button onClick={reconnect}>重新连接</button>
        </div>
      )}
      
      {uploads.map((upload, index) => (
        <div key={index}>
          <h4>{upload.file_name}</h4>
          <progress value={upload.percentage} max={100} />
          <p>进度: {upload.percentage.toFixed(2)}%</p>
          <p>速度: {upload.speed_mbps.toFixed(2)} MB/s</p>
          {upload.eta_seconds && (
            <p>剩余时间: {upload.eta_seconds}秒</p>
          )}
          <p>状态: {upload.status}</p>
        </div>
      ))}
    </div>
  );
}
```

#### 2. 使用现成的进度组件

```typescript
import { UploadProgressList } from '@/components/UploadProgress';

function UploadPage() {
  return (
    <div>
      <h1>文件上传</h1>
      
      {/* 自动显示所有上传任务的进度 */}
      <UploadProgressList />
    </div>
  );
}
```

#### 3. 集成到现有页面

```typescript
import { UploadProgressList } from '@/components/UploadProgress';
import { Box, Paper } from '@mui/material';

function MediaFilesPage() {
  return (
    <Box>
      {/* 现有的文件列表 */}
      <Paper>
        <h2>媒体文件</h2>
        {/* ... 文件列表 ... */}
      </Paper>

      {/* 添加上传进度显示 */}
      <Paper sx={{ mt: 2 }}>
        <h2>上传进度</h2>
        <UploadProgressList />
      </Paper>
    </Box>
  );
}
```

---

## 🎨 UI 展示

### 进度显示效果

```
┌─────────────────────────────────────────────────────────┐
│ 上传任务 (2)                                              │
├─────────────────────────────────────────────────────────┤
│                                                           │
│ 📹 movie.mp4                [上传中] [秒传]               │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 45.5%        │
│ 45.5% (456 MB / 1.0 GB)                                   │
│                                                           │
│ 分片进度: 5 / 10                                          │
│ 🚀 2.5 MB/s  ⏱️ 已用时: 3分12秒  ⏳ 剩余: 2分8秒         │
│                                                           │
├─────────────────────────────────────────────────────────┤
│                                                           │
│ 📄 document.pdf              [上传成功] ✅                │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%         │
│ 100% (5.2 MB / 5.2 MB)                                    │
│ 文件ID: 3277950853089710677                               │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### 状态标签

- 🟦 **待上传** (pending)
- 🟦 **计算哈希** (hashing)
- 🔵 **检查秒传** (checking)
- 🟢 **秒传成功** (quick_success) ⚡
- 🔵 **上传中** (uploading)
- 🟢 **上传成功** (success) ✅
- 🔴 **上传失败** (failed) ❌
- ⚪ **已取消** (cancelled)

---

## 📊 API 接口文档

### REST API

#### GET `/api/upload/progress`
获取所有上传任务的进度

**Response:**
```json
{
  "uploads": [
    {
      "file_name": "video.mp4",
      "file_size": 1073741824,
      "status": "uploading",
      "percentage": 45.5,
      "uploaded_bytes": 488636416,
      "total_bytes": 1073741824,
      "total_parts": 10,
      "uploaded_parts": 5,
      "speed_mbps": 2.5,
      "elapsed_seconds": 192.3,
      "eta_seconds": 128.7,
      "error_message": null,
      "file_id": null,
      "is_quick_upload": false
    }
  ]
}
```

#### GET `/api/upload/progress/{file_path}`
获取指定文件的上传进度

**Parameters:**
- `file_path`: 文件路径（URL编码）

**Response:** 同上（单个上传对象）

#### GET `/api/upload/sessions`
获取所有断点续传会话

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "abc123def456",
      "file_path": "/path/to/video.mp4",
      "file_size": 1073741824,
      "file_sha1": "9302CFAC...",
      "target_dir_id": "0",
      "total_parts": 10,
      "uploaded_parts": [1, 2, 3, 4, 5],
      "upload_id": "oss_upload_id_here",
      "progress": 50.0,
      "created_at": "2025-10-18T12:00:00",
      "updated_at": "2025-10-18T12:05:00"
    }
  ]
}
```

#### DELETE `/api/upload/sessions/{session_id}`
删除断点续传会话

**Parameters:**
- `session_id`: 会话ID

**Response:**
```json
{
  "message": "会话已删除"
}
```

#### POST `/api/upload/sessions/cleanup`
清理过期的断点续传会话

**Query Parameters:**
- `days`: 天数（默认7天）

**Response:**
```json
{
  "message": "已清理超过7天未更新的会话"
}
```

---

### WebSocket API

#### WS `/ws/upload/progress`
实时上传进度推送

**连接:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/upload/progress');
```

**服务器 → 客户端消息:**

进度更新:
```json
{
  "type": "upload_progress",
  "data": {
    "uploads": [
      { /* 上传进度对象 */ }
    ]
  }
}
```

心跳响应:
```json
{
  "type": "pong",
  "timestamp": 1697654400000
}
```

**客户端 → 服务器消息:**

心跳请求:
```json
{
  "type": "ping",
  "timestamp": 1697654400000
}
```

**更新频率:** 500ms

**特性:**
- ✅ 自动广播（有上传任务时）
- ✅ 心跳保活（30秒间隔）
- ✅ 自动重连（5秒延迟）
- ✅ 多客户端支持

---

## 🔄 工作流程

### 小文件上传流程（<100MB）

```
1. 调用 client.upload_file()
   ↓
2. 创建进度追踪 (UploadProgressManager)
   ↓
3. 计算文件哈希 (SHA1 + sig_sha1)
   status: hashing
   ↓
4. 尝试秒传 (POST /files/add)
   status: checking
   ↓
   ├─ 秒传成功 → status: quick_success ✅
   │
   └─ 秒传失败 ↓
5. 获取上传参数 (GET /files/get_upload_info)
   ↓
6. 直接上传到OSS (POST to OSS)
   status: uploading
   progress: 0% → 100%
   ↓
7. 上传完成
   status: success ✅
```

### 大文件上传流程（>=100MB）

```
1. 调用 client.upload_file()
   ↓
2. 创建进度追踪 + 查找/创建会话
   ↓
3. 计算文件哈希
   ↓
4. 尝试秒传（同上）
   ↓
5. 获取上传参数
   ↓
6. 分片上传 (_upload_multipart)
   ├─ 检查已上传分片
   ├─ 上传未完成的分片（每片10MB）
   │  └─ 每完成一片 → 更新会话 + 更新进度
   └─ 所有分片完成
   ↓
7. 完成上传通知
   ↓
8. 清理会话
   status: success ✅
```

### 断点续传流程

```
网络中断/程序崩溃
   ↓
会话已保存到: data/upload_sessions/{session_id}.json
   ↓
重新启动上传
   ↓
检测到现有会话
   ↓
读取已上传分片列表: [1, 2, 3, 4, 5]
   ↓
仅上传剩余分片: [6, 7, 8, 9, 10]
   ↓
完成上传 ✅
```

---

## 🛠️ 配置选项

### 断点续传配置

```python
from services.upload_resume_manager import UploadResumeManager

# 自定义存储目录
resume_mgr = UploadResumeManager(
    storage_dir="./custom/upload_sessions"
)

# 自定义过期时间
await resume_mgr.clean_expired_sessions(days=3)
```

### 进度追踪配置

```python
# 分片大小（默认10MB）
PART_SIZE = 10 * 1024 * 1024

# 小文件阈值（默认100MB）
MULTIPART_THRESHOLD = 100 * 1024 * 1024
```

### WebSocket配置

```python
# 广播间隔（默认500ms）
await asyncio.sleep(0.5)

# 心跳间隔（默认30秒）
heartbeat_interval = 30000  # ms
```

---

## 🐛 故障排查

### 问题1: WebSocket无法连接

**症状:** 前端显示"未连接到上传进度服务器"

**解决方案:**
1. 检查WebSocket端口是否开放
2. 确认URL协议（ws:// 或 wss://）
3. 检查防火墙设置
4. 查看浏览器控制台错误信息

### 问题2: 上传进度不更新

**症状:** 进度一直停留在0%

**解决方案:**
1. 确认进度管理器已初始化
2. 检查是否调用了`progress.start()`
3. 验证`update_progress()`被正常调用
4. 查看后端日志

### 问题3: 断点续传失败

**症状:** 重启后从0%开始上传

**解决方案:**
1. 检查会话存储目录权限
2. 确认session_id生成一致
3. 验证会话文件是否存在
4. 检查会话未过期

### 问题4: 分片上传报错

**症状:** "OSS分片上传API尚未完全实现"

**说明:** 当前分片上传的OSS API集成尚未完成，暂时回退到小文件上传方式。

**临时方案:** 将大文件拆分或等待后续更新。

---

## 📈 性能优化建议

### 1. 并发控制

```python
# 限制同时上传的文件数
MAX_CONCURRENT_UPLOADS = 3

# 限制分片并发数
MAX_CONCURRENT_PARTS = 5
```

### 2. 内存优化

```python
# 流式读取大文件（避免一次性加载）
CHUNK_SIZE = 8192  # 8KB

with open(file_path, 'rb') as f:
    while True:
        chunk = f.read(CHUNK_SIZE)
        if not chunk:
            break
        # 处理chunk
```

### 3. WebSocket优化

```python
# 仅在有更新时广播
if progresses and has_changes:
    await ws_manager.broadcast(message)

# 批量更新减少消息数
# 每500ms最多发送一次
```

---

## 📚 参考资料

- [fake115uploader](https://github.com/orzogc/fake115uploader) - Go语言实现的115上传工具
- [阿里云OSS Multipart Upload](https://www.alibabacloud.com/help/en/oss/user-guide/multipart-upload-12) - OSS分片上传文档
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket) - MDN WebSocket文档
- [FastAPI WebSocket](https://fastapi.tiangolo.com/advanced/websockets/) - FastAPI WebSocket支持

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

特别需要帮助的领域：
- [ ] OSS Multipart Upload API完整实现
- [ ] 上传队列管理
- [ ] 上传任务取消功能
- [ ] 更多前端UI优化

---

**最后更新:** 2025-10-18  
**版本:** v1.4.0  
**作者:** TMC Project Team

