# 115网盘上传功能快速开始指南

## 🚀 快速安装

### 1. 安装依赖

```bash
cd app/backend
pip install lz4>=4.3.2
pip install oss2>=2.18.0
```

或者直接安装所有依赖：

```bash
pip install -r requirements.txt
```

### 2. 验证安装

```bash
python -c "import lz4; import oss2; import cryptography; print('✅ 所有依赖已安装')"
```

## 📝 获取115账号信息

### 方法1: 通过浏览器获取Cookie

1. 登录 [115.com](https://115.com)
2. 打开浏览器开发者工具（F12）
3. 转到"网络"(Network)标签
4. 刷新页面
5. 找到任意请求，查看请求头中的Cookie
6. 复制完整的Cookie字符串（应包含 `UID=...` 和 `CID=...`）

### 方法2: 通过API获取user_id和userkey

使用上面获取的Cookie，访问：

```bash
curl -H "Cookie: YOUR_COOKIE_HERE" https://proapi.115.com/app/uploadinfo
```

响应示例：
```json
{
  "user_id": 123456,
  "userkey": "your_user_key_here",
  ...
}
```

## 🧪 测试上传功能

### 基础功能测试（无需账号）

```bash
cd app/backend
python -m utils.test_upload115
```

这将测试：
- ✅ 文件哈希计算
- ✅ ECDH加密/解密
- ✅ 上传签名算法

### 真实上传测试（需要账号）

设置环境变量：

**Linux/Mac:**
```bash
export TEST_115_USER_ID="123456"
export TEST_115_USER_KEY="your_user_key"
export TEST_115_COOKIES="UID=...; CID=..."
```

**Windows PowerShell:**
```powershell
$env:TEST_115_USER_ID="123456"
$env:TEST_115_USER_KEY="your_user_key"
$env:TEST_115_COOKIES="UID=...; CID=..."
```

**Windows CMD:**
```cmd
set TEST_115_USER_ID=123456
set TEST_115_USER_KEY=your_user_key
set TEST_115_COOKIES=UID=...; CID=...
```

运行测试：

```bash
python -m utils.test_upload115
```

## 💻 代码示例

### 示例1: 直接使用上传器

```python
import asyncio
from utils.upload115 import create_uploader

async def upload_file():
    # 配置信息
    user_id = "123456"
    user_key = "your_user_key"
    cookies = "UID=...; CID=..."
    
    # 创建上传器
    uploader = create_uploader(
        user_id=user_id,
        user_key=user_key,
        cookies=cookies,
        use_proxy=False
    )
    
    # 上传文件
    result = await uploader.upload_file(
        file_path="/path/to/file.mp4",
        target_cid="0"  # 0表示根目录
    )
    
    print(f"上传结果: {result}")
    
    if result['success']:
        if result.get('quick_upload'):
            print("✅ 秒传成功！")
        else:
            print("✅ 上传成功！")
    else:
        print(f"❌ 上传失败: {result['message']}")

# 运行
asyncio.run(upload_file())
```

### 示例2: 通过Pan115Client使用

```python
import asyncio
from services.pan115_client import Pan115Client

async def upload_via_client():
    # 创建客户端（Cookie认证）
    client = Pan115Client(
        app_id="",      # 留空
        app_key="",     # 留空
        user_id="123456",
        user_key="UID=...; CID=...",  # Cookie字符串
        use_proxy=False
    )
    
    # 上传文件（自动使用新的上传逻辑）
    result = await client.upload_file(
        file_path="/path/to/file.mp4",
        target_dir_id="0"
    )
    
    print(f"上传结果: {result}")

# 运行
asyncio.run(upload_via_client())
```

### 示例3: 上传到指定目录

```python
import asyncio
from utils.upload115 import create_uploader

async def upload_to_directory():
    uploader = create_uploader(
        user_id="123456",
        user_key="your_user_key",
        cookies="UID=...; CID=...",
        use_proxy=False
    )
    
    # 上传到指定目录（需要知道目录ID）
    result = await uploader.upload_file(
        file_path="/path/to/video.mp4",
        target_cid="123456789"  # 目标目录的CID
    )
    
    print(f"上传结果: {result}")

# 运行
asyncio.run(upload_to_directory())
```

### 示例4: 带进度回调的上传

```python
import asyncio
from utils.upload115 import create_uploader

async def progress_callback(uploaded: int, total: int):
    """进度回调函数"""
    percent = (uploaded / total) * 100
    print(f"上传进度: {percent:.2f}% ({uploaded}/{total} bytes)")

async def upload_with_progress():
    uploader = create_uploader(
        user_id="123456",
        user_key="your_user_key",
        cookies="UID=...; CID=...",
        use_proxy=False
    )
    
    result = await uploader.upload_file(
        file_path="/path/to/large_file.mp4",
        target_cid="0",
        progress_callback=progress_callback  # 传入进度回调
    )
    
    print(f"上传结果: {result}")

# 运行
asyncio.run(upload_with_progress())
```

## 🔧 故障排除

### 问题1: ImportError: No module named 'lz4'

**解决方案:**

```bash
pip install lz4
```

如果在Windows上安装失败，尝试：

```bash
pip install lz4-wheels
```

### 问题2: ImportError: No module named 'oss2'

**解决方案:**

```bash
pip install oss2
```

### 问题3: 上传失败，提示"缺少userkey"

**原因:** Cookie中缺少必要的认证信息

**解决方案:**
1. 确保Cookie完整（包含UID和CID）
2. 尝试重新登录115获取新的Cookie
3. 使用 `/app/uploadinfo` 接口获取userkey

### 问题4: 秒传失败，开始实际上传但又失败

**可能原因:**
- OSS凭证问题
- 网络连接问题
- 文件权限问题

**解决方案:**
1. 检查网络连接
2. 确保文件可读
3. 查看详细日志输出
4. 尝试上传小文件测试

### 问题5: 上传成功但验证失败

**原因:** 文件列表未及时更新

**解决方案:**
- 等待几秒后再次查询
- 直接在115网盘中确认文件是否存在

## 📊 上传性能参考

| 文件大小 | 秒传 | 普通上传 | 分片上传 |
|---------|------|---------|---------|
| < 10MB | ~1s | ~5-10s | - |
| 10-100MB | ~1s | ~30s-2min | ~1-3min |
| 100MB-1GB | ~1s | 不适用 | ~5-15min |
| 1GB-10GB | ~1s | 不适用 | ~30min-2h |
| > 10GB | ~1s | 不适用 | 视网速而定 |

*注：秒传成功时无需实际上传，速度最快*

## 🎯 最佳实践

### 1. 优先使用秒传

大多数常见文件（电影、软件等）都能秒传成功：

```python
# 上传前无需任何准备，直接上传即可
# 系统会自动尝试秒传
result = await uploader.upload_file(file_path, target_cid)
if result.get('quick_upload'):
    print("✅ 秒传成功，节省时间和带宽！")
```

### 2. 大文件使用分片上传

100MB以上的文件自动使用分片上传：

```python
# 无需手动选择，系统会根据文件大小自动决定
result = await uploader.upload_file(large_file, target_cid)
```

### 3. 批量上传

```python
files = [
    "/path/to/video1.mp4",
    "/path/to/video2.mp4",
    "/path/to/video3.mp4",
]

for file_path in files:
    print(f"正在上传: {file_path}")
    result = await uploader.upload_file(file_path, target_cid="0")
    
    if result['success']:
        print(f"✅ {file_path} 上传成功")
    else:
        print(f"❌ {file_path} 上传失败: {result['message']}")
```

### 4. 错误处理

```python
try:
    result = await uploader.upload_file(file_path, target_cid)
    
    if result['success']:
        print("✅ 上传成功")
    else:
        # 处理上传失败
        print(f"❌ 上传失败: {result['message']}")
        
except Exception as e:
    # 处理异常
    print(f"❌ 上传异常: {e}")
```

## 📖 更多信息

- **详细文档:** `app/backend/utils/README_UPLOAD115.md`
- **实现报告:** `UPLOAD115_IMPLEMENTATION.md`
- **源码分析:** `c:\Users\16958\fake115uploader\分析报告.md`

## 🆘 获取帮助

如果遇到问题：

1. 查看日志输出（包含详细的调试信息）
2. 阅读完整文档
3. 检查网络连接
4. 确认115账号状态
5. 提交Issue（附上错误日志）

## ✅ 验证清单

在使用前，请确认：

- [ ] Python 3.7+ 已安装
- [ ] 所有依赖库已安装（lz4, oss2, cryptography, httpx）
- [ ] 已获取115账号的Cookie
- [ ] 已获取user_id和userkey
- [ ] 网络连接正常
- [ ] 基础功能测试通过

---

**祝使用愉快！** 🎉

