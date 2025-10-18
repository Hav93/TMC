# 115 Web API 上传实现指南

基于 fake115uploader 项目的纯Python上传实现

## 📚 参考资料

- [fake115uploader GitHub](https://github.com/orzogc/fake115uploader)
- 115 Web API 接口分析
- 阿里云OSS Multipart Upload API

## 🔍 上传流程分析

### 方案1：秒传（Quick Upload）

**条件**：文件已存在于115服务器

**流程**：
```
1. 计算文件SHA1
2. POST /files/add
   - filename: 文件名
   - filesize: 文件大小
   - file_id: 目标目录ID
   - target: U_1_{目录ID}
3. 如果 state=true → 秒传成功
```

**状态**：✅ 已实现

---

### 方案2：真实上传（Real Upload）

**问题**：115的上传接口需要复杂的签名和加密

**关键接口**（从p115client文档）：

#### 1. `upload_init()` - 初始化上传

```python
POST https://uplb.115.com/4.0/initupload.php

Payload:
- filename: str  # 文件名
- filesize: int  # 文件大小  
- target: str    # 格式: U_1_{目录ID}
- sign_key: str  # 签名密钥（需要计算）
- sign_val: str  # 签名值（需要计算）
```

**签名算法**（这是关键）：
```python
# 需要的组件：
1. sign_key: 基于时间戳和特定算法生成
2. sign_val: 基于文件信息的签名
3. 可能需要 RSA 加密
```

#### 2. `upload_gettoken()` - 获取上传token

```python
GET https://uplb.115.com/4.0/gettoken.php

Response:
{
    "token": "...",      # 上传token
    "endpoint": "...",   # 上传服务器
    ...
}
```

#### 3. 真实上传

```python
POST {endpoint}/upload

multipart/form-data:
- file: 文件内容
- token: 从gettoken获取
- sign: 签名
- ...其他参数
```

---

## 🚧 当前实现状态

### ✅ 已实现功能

| 功能 | 状态 | 实现文件 |
|------|------|---------|
| 秒传检测 | ✅ | `_try_quick_upload()` |
| 文件SHA1计算 | ✅ | `_upload_file_web_api()` |
| 列出文件 | ✅ | `_list_files_web_api()` |
| 删除文件 | ✅ | `_delete_files_web_api()` |
| 移动/复制 | ✅ | `_move_files_web_api()` / `_copy_files_web_api()` |
| 创建目录 | ✅ | `_create_directory_web_api()` |
| 离线下载 | ✅ | 全套离线下载API |

### ⚠️ 部分实现

| 功能 | 状态 | 问题 |
|------|------|------|
| 真实上传 | ⚠️ | 缺少签名算法 |

---

## 💡 解决方案

### 方案A：开放平台API（推荐）✅

**优势**：
- ✅ 官方支持
- ✅ 稳定可靠
- ✅ 有完整文档
- ✅ 已在项目中实现

**使用方法**：
```bash
# 方式1：在Web界面配置（推荐）
1. 访问 TMC Web 界面
2. 进入"设置" -> "115云盘配置"
3. 填写：
   - AppID: 你的开放平台AppID
   - AppSecret: 你的开放平台AppSecret
   - 用户Cookie: 你的115 Cookie
4. 保存配置

# 方式2：环境变量配置
PAN115_APP_ID=your_app_id
PAN115_APP_SECRET=your_app_secret
```

**⚠️ 重要：必须同时配置 AppID 和 AppSecret！**

### 方案B：研究签名算法 🔬

**需要逆向分析的内容**：

1. **签名密钥生成**
   ```python
   # 可能的实现
   def generate_sign_key():
       timestamp = int(time.time())
       # 需要特定的加密算法
       # 可能涉及 RSA、AES 等
       return sign_key
   ```

2. **签名值计算**
   ```python
   def calculate_sign_val(filename, filesize, ...):
       # 基于文件信息计算签名
       # 可能需要特定的哈希或加密
       return sign_val
   ```

3. **Token获取和使用**
   ```python
   # 需要理解token的生成和验证机制
   token = get_upload_token(...)
   ```

**难点**：
- ❌ 签名算法未公开
- ❌ 可能有反爬虫机制
- ❌ 需要持续维护（115可能随时更改）

### 方案C：使用第三方库 📦

**可选库**：
1. ~~`p115client`~~ - 已删库
2. 其他社区实现 - 需要调研

**状态**：不推荐，依赖外部维护

---

## 🎯 实施建议

### 对于普通用户

**最佳实践**：配置开放平台AppID和AppSecret

```bash
# 步骤1：访问开放平台
打开 https://open.115.com/
注册/登录账号
创建应用
获取 AppID 和 AppSecret（⚠️ 两者都必需！）

# 步骤2：在TMC中配置（推荐Web界面）
1. 访问 TMC Web 界面
2. 进入"设置" -> "115云盘配置"
3. 填写：
   - AppID: 你的应用ID
   - AppSecret: 你的应用密钥（用于签名）
   - 用户Cookie: 你的115账号Cookie
4. 保存并测试连接

# 或者：通过环境变量配置
PAN115_APP_ID=your_app_id
PAN115_APP_SECRET=your_app_secret
# 然后重启应用
docker-compose restart
```

**⚠️ 重要说明**：
- **AppID 和 AppSecret 必须同时配置**
- AppSecret 用于生成访问令牌的签名
- 缺少任何一个都无法使用开放平台API

### 对于开发者

如果你有兴趣研究上传签名算法：

**步骤1：抓包分析**
```bash
# 使用 Wireshark/Charles/Fiddler
# 观察 115 客户端的上传请求
```

**步骤2：代码分析**
```bash
# 可以尝试分析：
# - 115 Windows客户端
# - 115 Android APK
# - 115 网页版 JavaScript
```

**步骤3：实现并测试**
```python
# 在 pan115_client.py 中实现
async def _upload_with_signature(self, ...):
    sign_key = self._generate_sign_key()
    sign_val = self._calculate_sign_val(...)
    # ... 完整实现
```

---

## 📊 当前项目状态

### 功能完整度

```
文件管理: ████████████████████ 100%
  ✅ 列表/删除/移动/复制/重命名/创建目录

下载管理: ████████████████████ 100%
  ✅ 获取下载链接
  ✅ 离线下载管理

上传管理: ████████░░░░░░░░░░░░  40%
  ✅ 秒传（已存在文件）
  ⚠️ 真实上传（新文件，需要AppID）
```

### 用户体验

| 场景 | 体验 | 说明 |
|------|------|------|
| 下载文件 | ⭐⭐⭐⭐⭐ | 完美支持 |
| 管理文件 | ⭐⭐⭐⭐⭐ | 完美支持 |
| 离线下载 | ⭐⭐⭐⭐⭐ | 完美支持 |
| 上传热门文件 | ⭐⭐⭐⭐⭐ | 秒传成功 |
| 上传新文件（无AppID） | ⭐⭐ | 需要配置 |
| 上传新文件（有AppID） | ⭐⭐⭐⭐⭐ | 完美支持 |

---

## 📋 实现总结 (v1.4.0 - 2025-10-18)

### ✅ 已完成功能

#### 1. 基础上传功能
- ✅ 秒传检测（Quick Upload）
- ✅ 小文件直接上传（<100MB）
- ✅ 文件哈希计算（SHA1 + sig_sha1）
- ✅ 阿里云OSS上传

#### 2. 断点续传功能 🆕
- ✅ 上传会话管理（UploadResumeManager）
- ✅ 分片进度持久化（JSON存储）
- ✅ 自动恢复未完成的上传
- ✅ 会话ID生成（文件+目标目录）
- ✅ 过期会话清理（7天）

#### 3. 进度追踪功能 🆕
- ✅ 实时进度跟踪（UploadProgressManager）
- ✅ 多文件并发上传管理
- ✅ 上传速度计算（MB/s）
- ✅ ETA预估（剩余时间）
- ✅ 进度回调机制

#### 4. WebSocket实时推送 🆕
- ✅ WebSocket连接管理
- ✅ 自动广播上传进度（500ms间隔）
- ✅ 心跳保活机制
- ✅ 自动重连

#### 5. 前端进度显示 🆕
- ✅ `useUploadProgress` Hook
- ✅ `UploadProgressList` 组件
- ✅ 进度条显示
- ✅ 速度和ETA显示
- ✅ 分片进度显示
- ✅ 状态标签（上传中/成功/失败/秒传）

#### 6. API接口 🆕
- ✅ GET `/api/upload/progress` - 获取所有上传进度
- ✅ GET `/api/upload/progress/{file_path}` - 获取指定文件进度
- ✅ GET `/api/upload/sessions` - 获取断点续传会话
- ✅ DELETE `/api/upload/sessions/{session_id}` - 删除会话
- ✅ POST `/api/upload/sessions/cleanup` - 清理过期会话
- ✅ WS `/ws/upload/progress` - WebSocket实时进度推送

### ⚠️ 待实现

#### 1. 大文件分片上传
- ⚠️ OSS Multipart Upload API集成
- ⚠️ 分片并发上传
- ⚠️ 分片上传完成通知

#### 2. 高级功能
- 📝 并发上传限制
- 📝 上传队列管理
- 📝 上传任务取消
- 📝 上传失败自动重试

### 💡 使用示例

#### 后端调用
```python
from services.pan115_client import Pan115Client

client = Pan115Client(user_key="UID=xxx; CID=xxx; SEID=xxx")

# 上传文件（自动秒传检测，支持进度追踪）
result = await client.upload_file(
    file_path="/path/to/video.mp4",
    target_path="/影视/电影/2025"
)

# 查询上传进度
from services.upload_progress_manager import get_progress_manager
progress_mgr = get_progress_manager()
progress = await progress_mgr.get_progress("/path/to/video.mp4")
print(f"进度: {progress.percentage}%, 速度: {progress.speed_mbps}MB/s")

# 管理断点续传会话
from services.upload_resume_manager import get_resume_manager
resume_mgr = get_resume_manager()
sessions = await resume_mgr.list_sessions()
```

#### 前端调用
```typescript
import { UploadProgressList } from '@/components/UploadProgress';

function MyPage() {
  return (
    <div>
      <h1>文件上传</h1>
      <UploadProgressList />
    </div>
  );
}
```

---

## 🔄 未来改进

### 短期目标
- [ ] 完成OSS分片上传API集成
- [ ] 实现上传任务取消功能
- [ ] 添加上传队列管理

### 长期目标  
- [ ] 支持更多云存储服务
- [ ] 优化大文件上传性能
- [ ] 增加上传统计和分析

---

**最后更新**：2025-10-18  
**维护者**：TMC 项目团队  
**参考**：[fake115uploader](https://github.com/orzogc/fake115uploader)

