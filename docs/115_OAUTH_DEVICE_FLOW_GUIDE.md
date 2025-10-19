# 115开放平台 OAuth 2.0 Device Code Flow 实现指南

## 📋 概述

本项目已成功实现115开放平台的完整OAuth 2.0设备授权码流程(Device Authorization Grant Flow with PKCE)。这是一个标准的OAuth 2.0流程,适用于无浏览器或输入受限的设备。

---

## 🎯 实现的功能

### 后端实现

#### 1. **Pan115Client** (`app/backend/services/pan115_client.py`)

新增/修改的核心方法:

- **`_generate_pkce_pair()`** 
  - 生成PKCE (Proof Key for Code Exchange) 参数
  - `code_verifier`: 43-128字符的随机字符串
  - `code_challenge`: code_verifier的SHA256哈希值(Base64 URL编码)
  - 增强安全性,防止授权码被拦截攻击

- **`get_device_code()`**
  - OAuth 2.0 Device Code Flow 第一步
  - 向`https://passportapi.115.com/open/authDeviceCode`请求设备授权码
  - 返回: `device_code`, `user_code`, `verification_uri`, `expires_in`, `interval`, `code_verifier`

- **`poll_device_token(device_code, code_verifier, max_attempts, interval)`**
  - OAuth 2.0 Device Code Flow 第二步
  - 轮询`https://passportapi.115.com/open/token`获取访问令牌
  - 支持多种状态处理:
    - `authorization_pending`: 用户尚未授权,继续等待
    - `slow_down`: 轮询过于频繁,增加等待时间
    - `expired_token`: 设备码已过期
    - `access_denied`: 用户拒绝授权
  - 成功后返回: `access_token`, `refresh_token`, `expires_in`

- **`get_access_token()`**
  - 简化调用入口,直接调用`get_device_code()`
  - 返回设备授权信息供前端使用

#### 2. **API路由** (`app/backend/api/routes/pan115.py`)

新增/修改的端点:

- **`POST /api/pan115/activate-open-api`**
  - 修改为返回设备授权码信息(而非直接获取token)
  - 响应格式:
    ```json
    {
      "success": true,
      "step": "device_authorization",
      "device_code": "xxx",
      "user_code": "ABC-DEF",
      "verification_uri": "https://115.com/authorize",
      "expires_in": 600,
      "interval": 5,
      "code_verifier": "xxx",
      "message": "请在浏览器中访问授权页面..."
    }
    ```

- **`POST /api/pan115/poll-device-token`** (新增)
  - 轮询获取访问令牌
  - 请求参数: `device_code`, `code_verifier`
  - 响应格式:
    ```json
    {
      "success": true/false,
      "status": "pending|authorized|error|expired",
      "message": "..."
    }
    ```
  - 成功时自动保存`access_token`和`refresh_token`到数据库
  - 自动刷新用户信息和空间数据

### 前端实现

#### 1. **服务层** (`app/frontend/src/services/pan115.ts`)

新增API方法:

- **`activateOpenApi()`**
  - 调用后端获取设备授权码
  - 返回类型包含: `device_code`, `user_code`, `verification_uri`等

- **`pollDeviceToken(deviceCode, codeVerifier)`**
  - 轮询获取访问令牌
  - 前端定时调用,直到授权完成

#### 2. **UI组件** (`app/frontend/src/pages/Settings/Pan115Settings.tsx`)

新增状态管理:

```typescript
// OAuth 2.0 Device Code Flow状态
const [authModalVisible, setAuthModalVisible] = useState(false);
const [authUserCode, setAuthUserCode] = useState('');
const [authVerificationUri, setAuthVerificationUri] = useState('');
const [authDeviceCode, setAuthDeviceCode] = useState('');
const [authCodeVerifier, setAuthCodeVerifier] = useState('');
const [authPolling, setAuthPolling] = useState(false);
const [authStatus, setAuthStatus] = useState<'pending' | 'authorized' | 'error' | 'expired'>('pending');
```

新增核心功能:

- **OAuth授权弹窗**
  - 显示大字体授权码(user_code)
  - 提供"打开授权页面"按钮
  - 实时显示授权状态
  - 轮询进度显示

- **轮询机制**
  - `startAuthPolling()`: 开始定时轮询
  - `stopAuthPolling()`: 停止轮询
  - 最大轮询次数: 120次 (5秒间隔 × 120 = 10分钟)
  - 自动处理授权成功/失败/超时

---

## 🔄 完整的授权流程

### 用户操作流程

1. **扫码登录115账号** (步骤1)
   - 选择设备类型(qandroid/web/ios等)
   - 扫码获取cookies
   - 系统保存cookies到`/config/115-cookies.txt`

2. **填写AppID** (步骤2)
   - 在115设置页面输入AppID
   - 在[115开放平台](https://www.yuque.com/115yun/open)申请

3. **启用开放平台API** (步骤2)
   - 点击"启用OPENAPI"开关
   - 系统自动获取设备授权码

4. **完成OAuth授权** (弹窗引导)
   - 点击"打开授权页面"按钮
   - 在新打开的页面中输入显示的授权码
   - 完成授权
   - 系统自动获取`access_token`
   - 自动刷新用户信息和空间数据

### 技术流程

```
┌─────────────┐
│ 用户点击启用 │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────┐
│ 前端: 调用 activateOpenApi()      │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ 后端: 生成 PKCE 参数              │
│  - code_verifier (随机字符串)     │
│  - code_challenge (SHA256哈希)    │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ 请求设备授权码                     │
│ POST /open/authDeviceCode         │
│ 参数: client_id, code_challenge   │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ 115服务器返回:                     │
│  - device_code (设备码)           │
│  - user_code (用户授权码)         │
│  - verification_uri (授权URL)    │
│  - expires_in (有效期)            │
│  - interval (轮询间隔)            │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ 前端: 显示授权弹窗                 │
│  - 展示 user_code                 │
│  - 提供授权URL链接                │
│  - 开始定时轮询                   │
└──────┬───────────────────────────┘
       │
       ├─────────────────────────────┐
       │                             │
       ▼                             ▼
┌─────────────────┐         ┌────────────────┐
│ 用户在浏览器中:  │         │ 前端定时轮询:   │
│ 1. 打开授权页面 │         │ pollDeviceToken │
│ 2. 输入授权码   │         │ 每5秒调用一次   │
│ 3. 确认授权     │         └────────┬───────┘
└─────────────────┘                  │
                                     ▼
                            ┌────────────────┐
                            │ 后端检查状态:   │
                            │ POST /open/token│
                            │ 参数: device_code,│
                            │ code_verifier   │
                            └────────┬───────┘
                                     │
       ┌─────────────────────────────┼─────────────────────┐
       │                             │                     │
       ▼                             ▼                     ▼
┌─────────────┐          ┌──────────────────┐   ┌────────────────┐
│ pending     │          │ authorized       │   │ error/expired  │
│ 继续等待... │          │ 获取到token!     │   │ 授权失败       │
└─────────────┘          └──────┬───────────┘   └────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ 保存到数据库:     │
                       │  - access_token  │
                       │  - refresh_token │
                       │  - expires_at    │
                       └──────┬───────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │ 刷新用户信息:     │
                       │  - 用户名        │
                       │  - VIP等级       │
                       │  - 空间信息      │
                       └──────────────────┘
```

---

## 🔒 安全特性

### PKCE (Proof Key for Code Exchange)

- **目的**: 防止授权码拦截攻击
- **工作原理**:
  1. 客户端生成随机`code_verifier`
  2. 使用SHA256计算`code_challenge = BASE64URL(SHA256(code_verifier))`
  3. 请求设备码时发送`code_challenge`
  4. 请求token时发送`code_verifier`
  5. 服务器验证`SHA256(code_verifier) == code_challenge`

### 其他安全措施

- ✅ 使用HTTPS (passportapi.115.com)
- ✅ Token存储在后端数据库,前端不暴露
- ✅ 支持代理配置(可选)
- ✅ 轮询超时保护(最多10分钟)
- ✅ 授权码有效期限制

---

## 📊 状态码说明

| 状态 | 描述 | 处理方式 |
|------|------|----------|
| `authorization_pending` | 用户尚未授权 | 继续轮询,等待用户操作 |
| `slow_down` | 轮询过于频繁 | 增加等待时间(interval × 2) |
| `expired_token` | 设备码已过期 | 停止轮询,提示用户重新激活 |
| `access_denied` | 用户拒绝授权 | 停止轮询,提示授权被拒绝 |
| `authorized` | 授权成功 | 停止轮询,保存token,刷新用户信息 |

---

## 🎨 UI/UX特性

### 授权弹窗设计

1. **清晰的步骤说明**
   - 三步操作指引
   - 图文并茂的说明

2. **突出显示授权码**
   - 大字体(32px)
   - 蓝色高亮
   - 等宽字体,增加字间距
   - 灰色背景卡片

3. **实时状态反馈**
   - 轮询进度显示(当前次数/总次数)
   - Spin加载动画
   - 状态文本提示

4. **多状态展示**
   - pending: 等待授权(Spin + 进度)
   - authorized: 授权成功(绿色对勾 + 成功提示)
   - error: 授权失败(红色警告)
   - expired: 超时(黄色警告 + 重新激活按钮)

---

## 🛠️ 配置说明

### 后端配置

无需额外配置,只需确保以下字段存在于数据库:

```python
# models.py - MediaSettings
pan115_app_id = Column(String, comment='115开放平台AppID')
pan115_user_id = Column(String, comment='115用户ID')
pan115_user_key = Column(String, comment='115用户凭证(cookies)')
pan115_access_token = Column(String, comment='115开放平台访问令牌')
pan115_refresh_token = Column(String, comment='115开放平台刷新令牌')
pan115_token_expires_at = Column(DateTime, comment='令牌过期时间')
pan115_use_proxy = Column(Boolean, default=False, comment='是否使用代理')
```

### 前端配置

无需配置,前端会自动适配后端API。

---

## 📝 API文档

### 1. 获取设备授权码

**端点**: `POST /api/pan115/activate-open-api`

**请求**: 无需body参数,从数据库读取AppID和cookies

**响应**:
```json
{
  "success": true,
  "step": "device_authorization",
  "device_code": "d1e2f3g4h5i6j7k8",
  "user_code": "ABCD-EFGH",
  "verification_uri": "https://115.com/authorize",
  "expires_in": 600,
  "interval": 5,
  "code_verifier": "random_generated_string",
  "message": "请在浏览器中访问授权页面..."
}
```

### 2. 轮询获取访问令牌

**端点**: `POST /api/pan115/poll-device-token`

**请求**:
```json
{
  "device_code": "d1e2f3g4h5i6j7k8",
  "code_verifier": "random_generated_string"
}
```

**响应 - 等待中**:
```json
{
  "success": false,
  "status": "pending",
  "message": "等待用户授权..."
}
```

**响应 - 授权成功**:
```json
{
  "success": true,
  "status": "authorized",
  "message": "授权成功,访问令牌已获取"
}
```

**响应 - 授权失败**:
```json
{
  "success": false,
  "status": "error",
  "message": "具体错误信息"
}
```

---

## 🐛 故障排查

### 问题1: 获取设备授权码失败

**可能原因**:
- AppID未配置
- Cookies未配置或已过期
- 网络问题
- 代理配置错误

**解决方案**:
1. 检查AppID是否正确
2. 重新扫码登录获取cookies
3. 测试网络连接
4. 检查代理设置(是否需要代理)

### 问题2: 轮询超时

**可能原因**:
- 用户未在规定时间内完成授权
- 授权页面访问失败

**解决方案**:
1. 确认用户已打开授权页面
2. 确认授权码输入正确
3. 检查115服务器状态
4. 重新激活获取新的授权码

### 问题3: 授权成功但未获取空间信息

**可能原因**:
- 115 API限流
- access_token有效但权限不足

**解决方案**:
1. 等待几分钟后点击"刷新用户信息"
2. 检查后端日志查看详细错误
3. 确认AppID拥有正确的权限范围

---

## 📚 参考资料

- [115开放平台文档](https://www.yuque.com/115yun/open)
- [OAuth 2.0 Device Authorization Grant](https://datatracker.ietf.org/doc/html/rfc8628)
- [PKCE (RFC 7636)](https://datatracker.ietf.org/doc/html/rfc7636)

---

## 🎉 总结

通过实现完整的OAuth 2.0 Device Code Flow with PKCE,我们:

✅ 提升了安全性(PKCE防止授权码拦截)
✅ 改善了用户体验(清晰的授权流程引导)
✅ 提高了可靠性(标准OAuth流程,更稳定)
✅ 支持了灵活配置(代理可选,自动保存token)

**不再需要AppSecret,只需要AppID + Cookies即可完成整个授权流程!** 🚀

