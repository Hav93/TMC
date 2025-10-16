# Pan115Client API 文档

自定义的 115 网盘 Python 客户端，基于 115 Open API 开发。

## 📦 功能概览

`Pan115Client` 提供了完整的 115 网盘操作功能，不依赖第三方包，仅使用 `httpx` 进行 HTTP 请求。

## 🔧 初始化

```python
from services.pan115_client import Pan115Client

# Open API 方式初始化
client = Pan115Client(
    app_id="your_app_id",
    app_key="",  # Open API 通常不需要
    user_id="your_user_id",
    user_key="your_user_key"
)
```

## 📚 API 方法列表

### 1. 👤 用户管理

#### `get_user_info()`
获取用户信息和空间统计

**返回值：**
```python
{
    "success": bool,
    "user_info": {
        "user_id": str,
        "user_name": str,
        "email": str,
        "is_vip": bool,
        "vip_level": int,
        "space": {
            "total": int,  # 总空间（字节）
            "used": int,   # 已用空间（字节）
            "remain": int  # 剩余空间（字节）
        }
    },
    "message": str
}
```

**示例：**
```python
result = await client.get_user_info()
if result['success']:
    space = result['user_info']['space']
    print(f"总空间: {space['total'] / 1024**3:.2f} GB")
```

#### `test_connection()`
测试连接是否正常

---

### 2. 📁 目录管理

#### `create_directory(dir_name, parent_id="0")`
创建单个目录

**参数：**
- `dir_name`: 目录名称
- `parent_id`: 父目录 ID（默认为根目录）

**返回值：**
```python
{
    "success": bool,
    "dir_id": str,
    "message": str
}
```

#### `create_directory_path(path, parent_id="0")`
递归创建目录路径

**参数：**
- `path`: 目录路径，如 `/Media/Photos/2024`
- `parent_id`: 父目录 ID

**示例：**
```python
result = await client.create_directory_path("/Telegram媒体/photo/2025")
```

---

### 3. 📂 文件列表

#### `list_files(parent_id="0", limit=1150, offset=0, show_dir=1)`
列出目录下的文件和文件夹

**参数：**
- `parent_id`: 父目录 ID（"0" 表示根目录）
- `limit`: 返回数量限制
- `offset`: 偏移量
- `show_dir`: 是否显示文件夹（1=显示，0=不显示）

**返回值：**
```python
{
    "success": bool,
    "files": [
        {
            "id": str,
            "name": str,
            "size": int,
            "is_dir": bool,
            "ctime": int,  # 创建时间戳
            "utime": int,  # 修改时间戳
        }
    ],
    "count": int,
    "message": str
}
```

**示例：**
```python
result = await client.list_files(parent_id="0")
for file in result['files']:
    print(f"{'📁' if file['is_dir'] else '📄'} {file['name']}")
```

---

### 4. 📤 文件上传

#### `upload_file(file_path, target_dir_id="0", target_path=None)`
上传文件到 115 网盘

**参数：**
- `file_path`: 本地文件路径
- `target_dir_id`: 目标目录 ID
- `target_path`: 目标路径（如果提供，会先创建目录）

**返回值：**
```python
{
    "success": bool,
    "message": str,
    "file_id": str,
    "quick_upload": bool  # 是否秒传
}
```

**示例：**
```python
result = await client.upload_file(
    file_path="/path/to/file.mp4",
    target_path="/Telegram媒体/video"
)
```

---

### 5. 🗑️ 文件删除

#### `delete_files(file_ids)`
批量删除文件或文件夹

**参数：**
- `file_ids`: 文件 ID 列表

**示例：**
```python
result = await client.delete_files(["file_id_1", "file_id_2"])
```

---

### 6. 📦 文件移动/复制

#### `move_files(file_ids, target_dir_id)`
批量移动文件到目标目录

**参数：**
- `file_ids`: 要移动的文件 ID 列表
- `target_dir_id`: 目标目录 ID

#### `copy_files(file_ids, target_dir_id)`
批量复制文件到目标目录

**示例：**
```python
# 移动文件
result = await client.move_files(["file_id"], "target_dir_id")

# 复制文件
result = await client.copy_files(["file_id"], "target_dir_id")
```

---

### 7. ✏️ 文件重命名

#### `rename_file(file_id, new_name)`
重命名文件或文件夹

**参数：**
- `file_id`: 文件或文件夹 ID
- `new_name`: 新名称

**示例：**
```python
result = await client.rename_file("file_id", "新文件名.mp4")
```

---

### 8. 📋 文件信息

#### `get_file_info(file_id)`
获取文件或文件夹详细信息

**返回值：**
```python
{
    "success": bool,
    "file_info": {
        "id": str,
        "name": str,
        "size": int,
        "is_dir": bool,
        "ctime": int,
        "utime": int,
        "parent_id": str,
    },
    "message": str
}
```

---

### 9. 🔍 文件搜索

#### `search_files(keyword, parent_id="0", file_type=None, limit=100)`
搜索文件

**参数：**
- `keyword`: 搜索关键词
- `parent_id`: 搜索范围的父目录 ID（"0" 表示全盘搜索）
- `file_type`: 文件类型过滤
  - `None`: 所有类型
  - `"video"`: 视频
  - `"audio"`: 音频
  - `"image"`: 图片
  - `"document"`: 文档
- `limit`: 返回数量限制

**示例：**
```python
# 搜索所有视频文件
result = await client.search_files(
    keyword="电影",
    file_type="video",
    limit=50
)
```

---

### 10. 📥 下载链接

#### `get_download_url(file_id, user_agent=None)`
获取文件下载链接

**参数：**
- `file_id`: 文件 ID（pickcode）
- `user_agent`: 自定义 User-Agent

**返回值：**
```python
{
    "success": bool,
    "download_url": str,
    "file_name": str,
    "file_size": int,
    "message": str
}
```

---

### 11. 🔐 扫码登录

#### Open API 方式

##### `get_qrcode_token()`
获取 115 Open API 登录二维码

**返回值：**
```python
{
    "success": bool,
    "qrcode_token": str,
    "qrcode_url": str,
    "expires_in": int
}
```

##### `check_qrcode_status(qrcode_token)`
检查二维码扫码状态

**返回值：**
```python
{
    "success": bool,
    "status": str,  # "waiting" | "scanned" | "confirmed" | "expired"
    "user_id": str,  # 登录成功后返回
    "user_key": str  # 登录成功后返回
}
```

#### 常规登录方式（静态方法）

##### `@staticmethod get_regular_qrcode(app="web")`
获取常规 115 登录二维码

**参数：**
- `app`: 应用类型
  - `"web"`: 网页版（默认）
  - `"android"`: Android 客户端
  - `"ios"`: iOS 客户端
  - `"tv"`: TV 版
  - `"qandroid"`: 115 生活 Android 版
  - `"alipaymini"`: 支付宝小程序
  - `"wechatmini"`: 微信小程序

**返回值：**
```python
{
    "success": bool,
    "qrcode_url": str,  # 二维码图片 URL（base64）
    "qrcode_token": {
        "uid": str,
        "time": int,
        "sign": str
    },
    "expires_in": int,
    "app": str
}
```

**示例：**
```python
# 获取二维码
result = await Pan115Client.get_regular_qrcode(app="web")
qrcode_url = result['qrcode_url']
qrcode_token = result['qrcode_token']
```

##### `@staticmethod check_regular_qrcode_status(qrcode_token, app="web")`
检查常规登录二维码状态

**参数：**
- `qrcode_token`: 二维码 token 数据
- `app`: 应用类型（与获取二维码时保持一致）

**返回值：**
```python
{
    "success": bool,
    "status": str,  # "waiting" | "scanned" | "confirmed" | "expired"
    "cookies": str,  # 登录成功后的 cookies
    "user_id": str,
    "user_info": {...}
}
```

**示例：**
```python
# 轮询检查扫码状态
result = await Pan115Client.check_regular_qrcode_status(
    qrcode_token=qrcode_token,
    app="web"
)

if result['status'] == 'confirmed':
    cookies = result['cookies']
    # 保存 cookies 用于后续操作
```

---

## 🎯 使用场景示例

### 场景 1：上传 Telegram 下载的媒体文件

```python
client = Pan115Client(app_id, "", user_id, user_key)

# 1. 创建目标目录
await client.create_directory_path("/Telegram媒体/视频/2025/01")

# 2. 上传文件
result = await client.upload_file(
    file_path="/downloads/video.mp4",
    target_path="/Telegram媒体/视频/2025/01"
)

if result['success']:
    if result['quick_upload']:
        print("⚡ 秒传成功！")
    else:
        print("✅ 上传完成！")
```

### 场景 2：整理和重命名文件

```python
# 1. 列出目录文件
files_result = await client.list_files(parent_id="some_dir_id")

# 2. 批量重命名
for file in files_result['files']:
    if not file['is_dir'] and file['name'].endswith('.mp4'):
        new_name = f"renamed_{file['name']}"
        await client.rename_file(file['id'], new_name)
```

### 场景 3：搜索并下载文件

```python
# 1. 搜索视频文件
search_result = await client.search_files(
    keyword="教程",
    file_type="video"
)

# 2. 获取下载链接
for file in search_result['files']:
    url_result = await client.get_download_url(file['id'])
    if url_result['success']:
        download_url = url_result['download_url']
        # 使用 download_url 下载文件
```

### 场景 4：常规扫码登录

```python
# 1. 获取二维码
qr_result = await Pan115Client.get_regular_qrcode(app="web")
qrcode_url = qr_result['qrcode_url']
qrcode_token = qr_result['qrcode_token']

# 2. 显示二维码给用户扫描
# ... (前端显示二维码)

# 3. 轮询检查扫码状态
import asyncio

while True:
    status_result = await Pan115Client.check_regular_qrcode_status(
        qrcode_token=qrcode_token,
        app="web"
    )
    
    if status_result['status'] == 'confirmed':
        cookies = status_result['cookies']
        user_id = status_result['user_id']
        # 保存 cookies 和 user_id
        break
    elif status_result['status'] == 'expired':
        print("二维码已过期")
        break
    
    await asyncio.sleep(2)  # 每 2 秒检查一次
```

---

## 📝 注意事项

1. **签名机制**：所有 API 请求都需要签名，`_generate_signature()` 方法会自动处理
2. **时间戳**：每个请求都会自动添加当前时间戳
3. **错误处理**：所有方法都会返回包含 `success` 字段的字典，建议检查此字段
4. **异步操作**：所有方法都是异步的，需要使用 `await` 调用
5. **常规登录 vs Open API**：
   - 常规登录返回 **cookies**，适合个人使用
   - Open API 返回 **user_key**，适合应用开发

---

## 🔗 参考资料

- [115 Open API 文档](https://www.yuque.com/115yun/open/fd7fidbgsritauxm)
- [p115client 参考文档](https://p115client.readthedocs.io/)
- 代码位置：`app/backend/services/pan115_client.py`

---

## 📊 功能矩阵

| 功能分类 | 方法名 | Open API | 常规登录 |
|---------|--------|----------|---------|
| 用户信息 | `get_user_info()` | ✅ | ❌ |
| 文件列表 | `list_files()` | ✅ | ❌ |
| 文件上传 | `upload_file()` | ✅ | ❌ |
| 文件删除 | `delete_files()` | ✅ | ❌ |
| 文件移动 | `move_files()` | ✅ | ❌ |
| 文件复制 | `copy_files()` | ✅ | ❌ |
| 文件重命名 | `rename_file()` | ✅ | ❌ |
| 文件信息 | `get_file_info()` | ✅ | ❌ |
| 文件搜索 | `search_files()` | ✅ | ❌ |
| 下载链接 | `get_download_url()` | ✅ | ❌ |
| 创建目录 | `create_directory()` | ✅ | ❌ |
| Open 登录 | `get_qrcode_token()` | ✅ | N/A |
| 常规登录 | `get_regular_qrcode()` | N/A | ✅ |

*注：常规登录获取的 cookies 可以用于 p115client 包的其他功能*

