# 115网盘功能清单与认证方式分析

## 📊 当前 `pan115_client.py` 功能全景

### ✅ **已实现的功能** (共25个方法)

---

## 🔐 **一、认证相关 (5个方法)**

### 1. Open API 认证流程
| 方法 | 功能 | API类型 | 是否需要AppID |
|------|------|---------|--------------|
| `get_device_code()` | 获取设备授权码 | Open API | ✅ 必需 |
| `poll_device_token()` | 轮询获取token | Open API | ✅ 必需 |
| `get_access_token()` | 获取访问令牌 | Open API | ✅ 必需 |

### 2. 常规扫码登录（纯Cookie方式）
| 方法 | 功能 | API类型 | 是否需要AppID |
|------|------|---------|--------------|
| `get_regular_qrcode()` | 获取常规登录二维码 | QR Code API | ❌ 不需要 |
| `check_regular_qrcode_status()` | 检查扫码状态 | QR Code API | ❌ 不需要 |

---

## 📁 **二、文件管理功能 (11个方法)**

| 方法 | 功能 | 使用的API | 认证方式 |
|------|------|-----------|----------|
| `create_directory()` | 创建单个目录 | `proapi.115.com/2.0/file/add` | Open API签名 |
| `create_directory_path()` | 创建多级目录 | Open API | Open API签名 |
| `list_files()` | 列出文件列表 | `proapi.115.com/2.0/file/list` | Open API签名 |
| `get_file_info()` | 获取文件详情 | `proapi.115.com/2.0/file/info` | Open API签名 |
| `search_files()` | 搜索文件 | `proapi.115.com/2.0/file/search` | Open API签名 |
| `move_files()` | 移动文件 | `proapi.115.com/2.0/file/move` | Open API签名 |
| `copy_files()` | 复制文件 | `proapi.115.com/2.0/file/copy` | Open API签名 |
| `rename_file()` | 重命名文件 | `proapi.115.com/2.0/file/edit` | Open API签名 |
| `delete_files()` | 删除文件 | `proapi.115.com/2.0/file/delete` | Open API签名 |
| `get_download_url()` | 获取下载链接 | `proapi.115.com/2.0/file/download_url` | Open API签名 |
| `save_share()` | 转存分享文件 | `proapi.115.com/2.0/share/save` | Open API签名 |
| `get_share_info()` | 获取分享信息 | `proapi.115.com/2.0/share/info` | Open API签名 |

---

## 📤 **三、上传功能 (3个方法)**

| 方法 | 功能 | 使用的API | 认证方式 |
|------|------|-----------|----------|
| `get_upload_info()` | 获取上传信息 | `proapi.115.com/2.0/upload/init` | Open API签名 |
| `upload_file()` | 上传文件（完整流程） | Open API | Open API签名 |
| `get_qrcode_token()` | 获取二维码token | Open API | Open API签名 |

---

## 👤 **四、用户信息 (4个方法)**

| 方法 | 功能 | 使用的API | 认证方式 |
|------|------|-----------|----------|
| `get_user_info()` | 获取用户信息（智能） | 混合 | **自动选择** |
| `_get_user_info_by_cookie()` | Cookie方式获取 | Web API | Cookie认证 |
| `_get_space_info_only()` | 获取空间信息 | 混合 | **自动选择** |
| `check_qrcode_status()` | 检查二维码状态 | Open API | Open API签名 |

---

## 🔍 **五、工具方法 (2个方法)**

| 方法 | 功能 |
|------|------|
| `test_connection()` | 测试连接 |
| `_generate_signature()` | 生成API签名 |

---

## ❌ **当前缺失的功能**

### 1. 离线下载功能（急需）
- ❌ `add_offline_task()` - 添加离线下载任务
- ❌ `get_offline_task_list()` - 获取离线任务列表
- ❌ `delete_offline_task()` - 删除离线任务
- ❌ `cancel_offline_task()` - 取消离线任务
- ❌ `clear_offline_completed()` - 清空已完成任务

### 2. 其他可选功能
- ❌ `get_file_history()` - 获取文件历史版本
- ❌ `set_file_label()` - 设置文件标签
- ❌ `get_recyclebin()` - 获取回收站文件
- ❌ `restore_from_recyclebin()` - 从回收站恢复

---

## 🎯 **关键问题：常规扫码登录能否使用所有功能？**

### 📋 **答案详解**

#### ✅ **可以使用的功能（Cookie认证）**

**1. 用户信息获取** ✅
```python
# 常规扫码登录后，user_key 存储的是 cookies
# 代码中已经实现了自动检测：
is_cookie_auth = self.user_key and ('UID=' in self.user_key or 'CID=' in self.user_key)

if is_cookie_auth:
    # 使用 Web API 获取用户信息
    return await self._get_user_info_by_cookie()
```

**使用的 API：**
- `webapi.115.com/user/info` - 获取用户信息
- `webapi.115.com/1.0/space/info` - 获取空间信息

**结论：** ✅ **常规扫码登录可以获取用户信息**

---

#### ❌ **不能使用的功能（需要 Open API）**

**2. 文件管理功能** ❌
```python
# 所有文件管理API都使用 Open API 签名
params = {
    'app_id': self.app_id,      # ❌ 需要AppID
    'user_id': self.user_id,    # ❌ 需要数字user_id
    'user_key': self.user_key,  # ❌ 需要user_key（不是cookies）
    'timestamp': str(int(time.time())),
    'cid': parent_id,
}
params['sign'] = self._generate_signature(params)  # ❌ 需要签名
```

**使用的 API 域名：**
- `proapi.115.com` - Open API专用域名

**问题根源：**
1. Open API 需要 `app_id`（AppID）
2. 需要数字格式的 `user_id`
3. 需要 `user_key`（不是 cookies）
4. 需要使用 `app_key` 生成签名

**结论：** ❌ **常规扫码登录无法使用文件管理功能**

---

**3. 文件上传功能** ❌
```python
async def upload_file(self, file_path: str, target_dir_id: str = "0"):
    # 代码中明确检查
    if not self.app_id:
        return {
            'success': False,
            'message': '115文件上传功能需要开放平台AppID。请在【系统设置 → 115网盘配置】中填写AppID并激活开放平台API。'
        }
```

**结论：** ❌ **常规扫码登录无法上传文件**

---

**4. 新建文件夹功能** ❌
```python
async def create_directory(self, dir_name: str, parent_id: str = "0"):
    params = {
        'app_id': self.app_id,  # ❌ 需要AppID
        # ... 其他参数
    }
    params['sign'] = self._generate_signature(params)  # ❌ 需要签名
    
    # 使用 Open API
    response = await client.post(
        f"{self.base_url}/2.0/file/add",  # proapi.115.com
        data=params
    )
```

**结论：** ❌ **常规扫码登录无法创建文件夹**

---

## 📊 **功能对比表**

| 功能分类 | 常规扫码登录<br>(纯Cookie) | 开放平台登录<br>(AppID + Access Token) |
|---------|--------------------------|-----------------------------------|
| **认证方式** | QR Code API | Open API Device Flow |
| **获取用户信息** | ✅ 可用 | ✅ 可用 |
| **获取空间信息** | ✅ 可用 | ✅ 可用 |
| **列出文件** | ❌ 不可用 | ✅ 可用 |
| **上传文件** | ❌ 不可用 | ✅ 可用 |
| **创建文件夹** | ❌ 不可用 | ✅ 可用 |
| **删除文件** | ❌ 不可用 | ✅ 可用 |
| **移动/复制文件** | ❌ 不可用 | ✅ 可用 |
| **重命名文件** | ❌ 不可用 | ✅ 可用 |
| **搜索文件** | ❌ 不可用 | ✅ 可用 |
| **获取下载链接** | ❌ 不可用 | ✅ 可用 |
| **转存分享** | ❌ 不可用 | ✅ 可用 |
| **离线下载** | ❌ 未实现 | ❌ 未实现 |

---

## 🔧 **解决方案**

### 方案一：激活开放平台API（推荐）✅

**步骤：**
1. 常规扫码登录获取 cookies
2. 调用 `get_access_token()` 使用 cookies + AppID 获取 access_token
3. 使用 access_token 调用 Open API

**代码示例：**
```python
# 1. 常规扫码登录
qr_result = await client.get_regular_qrcode(app="qandroid")
# 用户扫码...
status_result = await client.check_regular_qrcode_status(qrcode_token)

if status_result['status'] == 'confirmed':
    cookies = status_result['cookies']
    user_id = status_result['user_id']
    
    # 2. 使用 cookies + AppID 获取 access_token
    client = Pan115Client(
        app_id="your_app_id",
        app_key="your_app_key",
        user_id=user_id,
        user_key=cookies  # ⚠️ 此时 user_key 是 cookies
    )
    
    token_result = await client.get_access_token()
    
    if token_result['success']:
        # 3. 更新客户端，使用 access_token
        client.access_token = token_result['access_token']
        # ✅ 现在可以使用所有 Open API 功能了
        upload_result = await client.upload_file("test.txt", "0")
```

**优点：**
- ✅ 可以使用所有功能
- ✅ 符合官方推荐方式
- ✅ 代码已经支持

**缺点：**
- ⚠️ 需要用户申请 AppID（开放平台注册）
- ⚠️ access_token 有过期时间（2小时）

---

### 方案二：使用 Web API（需要补充实现）

**原理：**
使用 `webapi.115.com` 域名的常规 Web API，只需要 cookies 认证。

**需要补充的代码：**
```python
async def list_files_by_cookie(self, parent_id: str = "0") -> Dict[str, Any]:
    """
    使用 Cookie 方式列出文件（Web API）
    
    Args:
        parent_id: 目录ID
    """
    try:
        headers = {
            'Cookie': self.user_key,  # 直接使用 cookies
            'User-Agent': 'Mozilla/5.0 ...',
        }
        
        params = {
            'cid': parent_id,
            'limit': '1150',
            'offset': '0',
            'show_dir': '1',
        }
        
        async with httpx.AsyncClient(**self._get_client_kwargs()) as client:
            response = await client.get(
                f"{self.webapi_url}/files",  # Web API 端点
                params=params,
                headers=headers
            )
        
        # 处理响应...
```

**优点：**
- ✅ 不需要 AppID
- ✅ 只需要 cookies

**缺点：**
- ❌ 需要大量补充代码（每个功能都要实现）
- ❌ Web API 文档不完整
- ❌ 可能不稳定（非官方推荐方式）

---

## 🎯 **建议**

### 对于您的项目：

#### 1️⃣ **立即实施：激活开放平台API流程**

在 `pan115.py` 路由中，完善扫码登录后的 access_token 获取：

```python
@router.post("/regular-qrcode/status")
async def check_regular_qrcode_status(
    data: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """检查扫码状态并自动激活开放平台API"""
    # ... 现有的扫码状态检查代码 ...
    
    if status == 'confirmed':
        cookies = result['cookies']
        user_id = result['user_id']
        
        # 保存 cookies
        settings.pan115_user_id = user_id
        settings.pan115_user_key = cookies
        
        # ✅ 如果有 AppID，自动获取 access_token
        if settings.pan115_app_id:
            logger.info("🔑 检测到AppID，尝试激活开放平台API")
            
            temp_client = Pan115Client(
                app_id=settings.pan115_app_id,
                app_key="",  # 不需要 app_key
                user_id=user_id,
                user_key=cookies
            )
            
            token_result = await temp_client.get_access_token()
            
            if token_result.get('success'):
                # 保存 access_token
                settings.pan115_access_token = token_result['access_token']
                settings.pan115_token_expires_at = get_user_now() + timedelta(seconds=7200)
                
                logger.info("✅ 开放平台API已激活！")
                message = "登录成功，已自动激活开放平台API，可以使用上传、文件管理等功能"
            else:
                logger.warning(f"⚠️ 激活开放平台API失败: {token_result.get('message')}")
                message = "登录成功，但开放平台API激活失败，仅能查看用户信息"
        else:
            message = "登录成功，但未配置AppID，仅能查看用户信息。如需使用上传、文件管理功能，请先申请开放平台AppID"
        
        await db.commit()
        
        return {
            "success": True,
            "status": "confirmed",
            "message": message
        }
```

---

#### 2️⃣ **短期任务：补充离线下载功能**

在 `pan115_client.py` 中添加离线下载相关方法（使用 Open API）。

---

#### 3️⃣ **长期优化：考虑支持 Web API 作为备选方案**

如果用户不想申请 AppID，可以提供基于 Cookie 的 Web API 实现（功能有限）。

---

## ✅ **总结**

### 核心结论：

1. ✅ **您的代码已经实现了文件上传、创建文件夹等功能**
2. ❌ **但常规扫码登录（纯Cookie）无法使用这些功能**
3. ✅ **必须配合 AppID 激活开放平台API 才能使用**
4. ⚠️ **离线下载功能还未实现（需要补充）**

### 推荐流程：

```
用户扫码登录（获取 cookies）
    ↓
检测是否有 AppID
    ↓
如果有 AppID → 自动调用 get_access_token()
    ↓
获取 access_token（2小时有效）
    ↓
✅ 可以使用所有功能（上传、创建文件夹、移动文件等）
```

**没有 AppID 的情况：**
- ⚠️ 只能查看用户信息和空间信息
- ❌ 不能上传、创建文件夹、管理文件

---

## 📝 **下一步行动**

您希望我：

1. 🔧 **完善激活开放平台API的流程**（修改 `pan115.py` 路由）
2. ➕ **补充离线下载功能**（添加到 `pan115_client.py`）
3. 📚 **创建用户使用文档**（说明如何申请 AppID）
4. 🧪 **编写测试用例**（验证功能完整性）

请告诉我优先级！



