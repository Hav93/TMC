# 115网盘集成快速参考

## 🚀 快速开始（5分钟完成基础集成）

### 方式一：Cookie登录（推荐新手）

**不需要申请任何账号，立即可用！**

#### 后端：
```python
# 1. 获取二维码
client = Pan115Client(app_id="", app_key="", user_id="", user_key="")
qr_result = await client.get_regular_qrcode(app="qandroid")
# 返回: qrcode_url（二维码图片）, qrcode_token（用于轮询）

# 2. 检查扫码状态（前端每2秒调用一次）
status_result = await client.check_regular_qrcode_status(qrcode_token, "qandroid")
# status: waiting → scanned → confirmed

# 3. 扫码成功后获得：
# - cookies (UID=xxx; CID=xxx; SEID=xxx)
# - user_id
# - user_info (用户名、VIP等级、空间信息)
```

#### 前端：
```typescript
// 1. 点击"扫码登录"
await pan115Api.getRegularQRCode("qandroid");

// 2. 显示二维码Modal，启动轮询
const poll = setInterval(async () => {
  const result = await pan115Api.checkRegularQRCodeStatus(token, "qandroid");
  if (result.status === 'confirmed') {
    message.success('登录成功！');
    clearInterval(poll);
  }
}, 2000);

// 3. 后端自动保存Cookie到：
// - 数据库：media_settings.pan115_user_key
// - 文件：/app/config/115-cookies.txt
```

**完成！现在可以使用基础文件操作功能。**

---

### 方式二：开放平台OAuth（生产环境推荐）

**需要：115账号 + 开放平台AppID**

#### 前置条件：
1. 先完成方式一（扫码登录）
2. 申请115开放平台AppID（联系115官方）
3. 在设置页面填写AppID

#### 激活流程：
```python
# 后端：使用已有Cookie + AppID获取Access Token
client = Pan115Client(
    app_id="your_app_id",
    app_key="",
    user_id="your_user_id",
    user_key="your_cookies"
)

# 方法1：直接激活（最简单）
token_result = await client.get_access_token()
# 返回: access_token, refresh_token, expires_in (7200秒=2小时)

# 方法2：OAuth Device Flow（更标准）
device_result = await client.get_device_code()
# 返回二维码，用户扫码后：
token_result = await client.poll_device_token(device_code, code_verifier)
```

#### 前端：
```typescript
// 填写AppID后，点击"启用OPENAPI"开关
await pan115Api.activateOpenApi();
// 系统自动：
// 1. 读取Cookie
// 2. 调用 /app/1.0/token 获取 access_token
// 3. 保存到数据库
// 4. 刷新用户信息（获取更准确的空间数据）
```

---

## 📝 核心代码示例

### 1. 文件上传

```python
client = Pan115Client(
    app_id=app_id,
    app_key="",
    user_id=user_id,
    user_key=cookies  # 或 access_token
)

# 上传到根目录
result = await client.upload_file(
    file_path="/path/to/file.mp4",
    target_dir_id="0"
)

# 上传到指定路径（自动创建目录）
result = await client.upload_file(
    file_path="/path/to/file.mp4",
    target_path="/telegram_downloads/videos"
)

# 返回:
# {
#   "success": True,
#   "file_id": "file123",
#   "quick_upload": False,  # True表示秒传
#   "message": "上传成功"
# }
```

### 2. 列出文件

```python
result = await client.list_files(
    parent_id="0",      # 0=根目录
    limit=100,
    show_dir=1          # 1=显示文件夹
)

# 返回:
# {
#   "success": True,
#   "files": [
#     {
#       "id": "file123",
#       "name": "video.mp4",
#       "size": 104857600,
#       "is_dir": False,
#       "ctime": 1698765432,
#       "utime": 1698765432
#     }
#   ],
#   "count": 10
# }
```

### 3. 获取用户信息

```python
result = await client.get_user_info()

# 返回:
# {
#   "success": True,
#   "user_info": {
#     "user_id": "987654321",
#     "user_name": "用户名",
#     "is_vip": True,
#     "vip_level": 5,
#     "vip_name": "年费VIP",
#     "space": {
#       "total": 107374182400,  # 100GB
#       "used": 53687091200,    # 50GB
#       "remain": 53687091200   # 50GB
#     }
#   }
# }
```

---

## 🔐 认证方式对比

| 特性 | Cookie登录 | 开放平台OAuth |
|------|-----------|--------------|
| **申请难度** | ⭐ 无需申请 | ⭐⭐⭐ 需要申请AppID |
| **集成速度** | ⚡ 5分钟 | ⚡⚡ 10分钟（需先Cookie登录） |
| **稳定性** | ⭐⭐⭐ Cookie有效期~30天 | ⭐⭐⭐⭐⭐ Token可刷新 |
| **功能完整性** | ⭐⭐⭐⭐ 基础功能完整 | ⭐⭐⭐⭐⭐ 支持高级API |
| **API限流** | ⚠️ 较严格 | ✅ 较宽松 |
| **空间信息准确性** | ⚠️ 可能被限流返回0 | ✅ 稳定准确 |
| **推荐场景** | 个人使用、测试开发 | 生产环境、企业应用 |

---

## 🛠️ 关键配置

### 数据库字段（MediaSettings表）

```python
pan115_app_id              # 开放平台AppID（可选）
pan115_user_id             # 用户ID
pan115_user_key            # Cookie或Token
pan115_device_type         # 登录设备类型（qandroid/web等）
pan115_request_interval    # API请求间隔（默认1.0秒）
pan115_use_proxy           # 是否使用代理（默认False）
pan115_access_token        # 开放平台访问令牌
pan115_refresh_token       # 刷新令牌
pan115_token_expires_at    # Token过期时间
pan115_user_info           # 用户信息缓存（JSON）
pan115_last_refresh_at     # 上次刷新时间
```

### 文件存储

```bash
/app/config/115-cookies.txt  # Cookie持久化文件
/app/backend/logs/pan115.log # 115客户端日志
```

---

## 🔄 工作流程

### Cookie登录流程
```
用户点击"扫码登录"
  ↓
获取二维码 (qrcodeapi.115.com)
  ↓
显示二维码，启动轮询
  ↓
用户用115 APP扫码
  ↓
检查状态：waiting → scanned → confirmed
  ↓
调用登录API获取Cookie (passportapi.115.com)
  ↓
保存到数据库 + 文件系统
  ↓
提取用户信息（VIP等级、空间等）
  ↓
✅ 登录成功
```

### OAuth激活流程
```
用户填写AppID并点击"启用"
  ↓
读取已保存的Cookie
  ↓
调用 /app/1.0/token (Cookie + AppID)
  ↓
获取 access_token (有效期2小时)
  ↓
保存到数据库
  ↓
使用access_token刷新用户信息
  ↓
✅ 开放平台API已激活
```

---

## 📡 API端点速查

### 115官方API

```bash
# 二维码API
GET https://qrcodeapi.115.com/api/1.0/{app}/1.0/token
GET https://qrcodeapi.115.com/get/status/?uid={uid}&time={time}&sign={sign}

# 登录API
POST https://passportapi.115.com/app/1.0/{app}/1.0/login/qrcode

# OAuth API（需要AppID）
POST https://passportapi.115.com/open/authDeviceCode
POST https://passportapi.115.com/app/1.0/token

# 用户信息API
GET https://webapi.115.com/user/info
POST https://passportapi.115.com/open/user/info

# 文件操作API
POST https://proapi.115.com/2.0/upload/init
POST https://proapi.115.com/2.0/file/list
POST https://proapi.115.com/2.0/file/delete
```

### 本项目后端API

```bash
# 配置管理
GET  /api/pan115/config
POST /api/pan115/config

# Cookie登录
POST /api/pan115/regular-qrcode
POST /api/pan115/regular-qrcode/status

# OAuth激活
POST /api/pan115/activate-open-api
POST /api/pan115/poll-device-token

# 用户信息
POST /api/pan115/refresh-user-info
POST /api/pan115/test-cookies

# 文件操作
POST /api/pan115/upload
```

---

## ⚠️ 常见问题快速解决

### 1. 二维码过期
```bash
# 症状：轮询超时（5分钟）
# 解决：前端自动刷新二维码
if (pollingCount > 150) {
  await getRegularQRCode();  // 重新获取
}
```

### 2. Cookie失效
```bash
# 症状：API返回401/403
# 解决：重新扫码登录
# Cookie通常有效期30天，到期需重新登录
```

### 3. 空间信息为0
```bash
# 症状：user_info.space.total = 0
# 原因：115 API限流（最常见）
# 解决：
# 1. 等待1-2分钟后点击"刷新信息"
# 2. 激活开放平台API（更稳定）
# 3. 前端会使用缓存数据，不影响正常使用
```

### 4. 上传失败
```bash
# 检查清单：
# - 文件是否存在
# - 文件大小是否超限（VIP限制）
# - 网络是否稳定
# - 目标目录是否存在
# - 签名是否正确（检查app_id/user_id/user_key）
```

### 5. 激活开放平台失败
```bash
# 确认：
# 1. AppID是否正确（纯数字）
# 2. 是否已扫码登录（需要先有Cookie）
# 3. Cookie是否有效（点击"检测可用性"）
# 4. 查看后端日志：tail -f app/backend/logs/pan115.log
```

---

## 📊 监控与调试

### 日志级别

```python
logger.info("✅ 正常操作")
logger.warning("⚠️ 警告（如API限流）")
logger.error("❌ 错误（如网络失败）")
```

### 关键日志搜索

```bash
# 登录相关
grep "登录成功" app/backend/logs/pan115.log
grep "扫码" app/backend/logs/pan115.log

# Token相关
grep "access_token" app/backend/logs/pan115.log
grep "激活" app/backend/logs/pan115.log

# 上传相关
grep "上传" app/backend/logs/pan115.log
grep "秒传" app/backend/logs/pan115.log

# 错误排查
grep "ERROR" app/backend/logs/pan115.log
grep "异常" app/backend/logs/pan115.log
```

### 数据库检查

```sql
-- 查看配置
SELECT pan115_user_id, pan115_app_id, 
       pan115_token_expires_at, pan115_last_refresh_at 
FROM media_settings;

-- 查看用户信息（JSON）
SELECT pan115_user_info FROM media_settings;
```

---

## 🎯 最佳实践

### 1. 使用建议

✅ **推荐做法**：
- 优先使用`qandroid`设备类型（最稳定）
- Cookie保存到文件系统（防止数据库问题）
- 用户信息使用缓存+定期刷新（避免频繁API调用）
- API调用间隔≥1秒（防止限流）
- 开放平台API适用于生产环境

❌ **避免做法**：
- 频繁调用空间信息API（会被限流）
- 同时发起多个上传请求（需要排队）
- 在国内服务器使用代理（115是国内服务）
- Cookie泄露（敏感信息，需加密存储）

### 2. 性能优化

```python
# 1. API限流控制
request_interval = 1.0  # 秒

# 2. 用户信息防抖
if time_since_last_refresh < 30:
    return cached_user_info  # 30秒内返回缓存

# 3. 空间信息优先使用开放平台API
if access_token:
    use_open_api()  # 更稳定
else:
    use_web_api()   # 可能被限流

# 4. 上传大文件使用分片上传（待实现）
if file_size > 100MB:
    use_chunked_upload()
```

### 3. 安全建议

```python
# 1. Cookie加密存储（可选）
from cryptography.fernet import Fernet
encrypted_cookie = cipher.encrypt(cookie.encode())

# 2. 定期检查Token有效性
if datetime.utcnow() >= token_expires_at:
    await refresh_access_token()

# 3. 日志脱敏
logger.info(f"User: {user_id}, Cookie: {cookie[:10]}****")

# 4. HTTPS传输
# 115 API全部使用HTTPS，无需额外配置
```

---

## 📚 扩展阅读

- 📖 [完整集成指南](./115_INTEGRATION_GUIDE.md) - 详细实现步骤
- 🔐 [OAuth Device Flow指南](./115_OAUTH_DEVICE_FLOW_GUIDE.md) - OAuth流程详解
- 🌐 [115开放平台官方文档](https://www.yuque.com/115yun/open)

---

**快速参考版本**：v1.0  
**最后更新**：2025-01-17


