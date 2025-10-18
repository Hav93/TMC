# 115 Web API 文件操作指南

## 概述

本文档详细说明了 `Pan115Client` 中实现的 115 Web API 文件操作功能。这些功能允许在**没有配置开放平台 AppID** 的情况下，通过 Cookie 认证进行文件管理操作。

## 功能特性

### 自动API选择

`Pan115Client` 实现了智能 API 选择机制：

- **开放平台 API**：当配置了 `app_id` 时使用
- **Web API**：当只有 Cookie（`user_key`）但没有 `app_id` 时使用

### 支持的操作

以下操作均支持自动选择使用开放平台 API 或 Web API：

| 操作 | 方法名 | Web API 实现 | 说明 |
|------|--------|--------------|------|
| 列出文件 | `list_files()` | ✅ 完整实现 | 获取指定目录下的文件列表 |
| 删除文件 | `delete_files()` | ✅ 完整实现 | 删除指定的文件或文件夹 |
| 移动文件 | `move_files()` | ✅ 完整实现 | 移动文件到目标目录 |
| 复制文件 | `copy_files()` | ✅ 完整实现 | 复制文件到目标目录 |
| 重命名 | `rename_file()` | ✅ 完整实现 | 重命名文件或文件夹 |
| 创建目录 | `create_directory()` | ✅ 完整实现 | 创建新目录，支持已存在检测 |
| 上传文件 | `upload_file()` | ⚠️ 秒传支持 | 支持秒传检测，真实上传待完善 |
| 下载链接 | `get_download_url()` | ✅ 完整实现 | 获取文件下载链接 |
| 添加离线任务 | `add_offline_task()` | ✅ 完整实现 | 添加HTTP/磁力/BT离线下载 |
| 离线任务列表 | `get_offline_tasks()` | ✅ 完整实现 | 获取离线任务列表 |
| 删除离线任务 | `delete_offline_task()` | ✅ 完整实现 | 删除指定离线任务 |
| 清空离线任务 | `clear_offline_tasks()` | ✅ 完整实现 | 清空已完成/失败任务 |

## 技术实现

### 1. Cookie 认证检测

```python
is_cookie_auth = self.user_key and ('UID=' in self.user_key or 'CID=' in self.user_key)

if is_cookie_auth and not self.app_id:
    # 使用 Web API
    return await self._list_files_web_api(...)
else:
    # 使用开放平台 API
    ...
```

### 2. Web API 端点

所有 Web API 请求使用基础 URL：`https://webapi.115.com`

| 功能 | 端点 | 方法 |
|------|------|------|
| 列出文件 | `/files` | GET |
| 删除文件 | `/rb/delete` | POST |
| 移动文件 | `/files/move` | POST |
| 复制文件 | `/files/copy` | POST |
| 重命名 | `/files/edit` | POST |
| 创建目录 | `/files/add` | POST |
| 下载链接 | `/files/download` | POST |
| 添加离线任务 | `/lixian/add` | POST |
| 离线任务列表 | `/lixian/task` | GET |
| 删除离线任务 | `/lixian/task_del` | POST |
| 清空离线任务 | `/lixian/task_clear` | POST |

### 3. 请求格式

#### 通用请求头

```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Cookie': self.user_key,
    'Accept': 'application/json',
}
```

#### 文件ID参数格式

对于批量操作（删除、移动、复制），Web API 使用特殊的数组格式：

```python
# 错误 ❌
data = {'fid': '123,456,789'}

# 正确 ✅
data = {
    'fid[0]': '123',
    'fid[1]': '456',
    'fid[2]': '789',
    'pid': 'target_directory_id'  # 对于移动/复制操作
}
```

### 4. 响应处理

#### 成功响应

```json
{
    "state": true,
    "data": {...},
    "count": 10
}
```

#### 错误响应

```json
{
    "state": false,
    "error": "错误信息",
    "errno": 错误码
}
```

## 实现的 Web API 方法

### 1. _list_files_web_api()

**功能**：使用 Cookie 认证列出文件

**请求示例**：
```python
params = {
    'cid': parent_id,        # 目录ID，0表示根目录
    'limit': 1150,           # 每页数量
    'offset': 0,             # 偏移量
    'show_dir': 1,           # 是否显示目录
    'o': 'user_ptime',       # 排序方式
    'asc': 0,                # 0=降序，1=升序
}
```

**返回数据映射**：
```python
{
    'id': item.get('fid') or item.get('cid', ''),  # 文件ID或目录ID
    'name': item.get('n', ''),                      # 名称
    'size': int(item.get('s', 0)),                  # 大小（字节）
    'is_dir': bool(item.get('cid') and not item.get('fid')),  # 是否是目录
    'ctime': int(item.get('te', 0)),                # 创建时间
    'utime': int(item.get('tu', 0)),                # 修改时间
    'pick_code': item.get('pc', ''),                # 提取码
    'sha1': item.get('sha', ''),                    # SHA1哈希
}
```

### 2. _delete_files_web_api()

**功能**：删除文件或文件夹

**请求示例**：
```python
data = {
    'fid[0]': 'file_id_1',
    'fid[1]': 'file_id_2',
    ...
}
```

### 3. _move_files_web_api()

**功能**：移动文件到目标目录

**请求示例**：
```python
data = {
    'pid': 'target_directory_id',  # 目标目录
    'fid[0]': 'file_id_1',
    'fid[1]': 'file_id_2',
    ...
}
```

### 4. _copy_files_web_api()

**功能**：复制文件到目标目录

**请求示例**：
```python
data = {
    'pid': 'target_directory_id',  # 目标目录
    'fid[0]': 'file_id_1',
    'fid[1]': 'file_id_2',
    ...
}
```

### 5. _rename_file_web_api()

**功能**：重命名文件或文件夹

**请求示例**：
```python
data = {
    'fid': 'file_id',
    'file_name': 'new_name.txt',
}
```

### 6. _create_directory_web_api()

**功能**：创建新目录

**请求示例**：
```python
data = {
    'pid': 'parent_directory_id',  # 父目录，0表示根目录
    'cname': 'new_directory_name',
}
```

**特殊处理**：
- 如果目录已存在，会查询现有目录ID并返回
- 支持递归查找已存在的目录

### 7. _upload_file_web_api()

**功能**：上传文件（当前仅支持秒传检测）

**实现说明**：
- ✅ 支持文件 SHA1 计算
- ✅ 支持秒传检测
- ⚠️ 真实上传流程较复杂，建议使用开放平台 API

**秒传检测**：
```python
check_data = {
    'file_id': target_dir_id,
    'file_name': file_name,
    'file_size': file_size,
    'file_sha1': file_sha1,
}
```

### 8. _get_download_url_web_api()

**功能**：获取文件下载链接

**请求示例**：
```python
data = {
    'pickcode': pick_code,  # 文件的提取码
}
```

**返回处理**：
```python
# URL 可能是字典或字符串
if isinstance(file_url, dict):
    download_url = file_url.get('url', '')
else:
    download_url = file_url
```

### 9. _add_offline_task_web_api()

**功能**：添加离线下载任务

**支持的链接类型**：
- HTTP/HTTPS 直链
- 磁力链接 (magnet:)
- BT种子 URL

**请求示例**：
```python
data = {
    'url': 'magnet:?xt=urn:btih:...',  # 下载链接
    'wp_path_id': '0',  # 目标目录ID
}
```

**返回数据**：
```python
{
    'success': True,
    'task_id': 'abc123...',  # 任务ID (info_hash)
    'message': '离线任务添加成功'
}
```

### 10. _get_offline_tasks_web_api()

**功能**：获取离线任务列表

**请求示例**：
```python
params = {
    'page': 1,  # 页码
}
```

**任务状态**：
- `-1`: 等待中
- `0`: 下载中
- `1`: 已完成
- `2`: 失败
- `4`: 已删除

**返回数据映射**：
```python
{
    'task_id': task.get('info_hash', ''),  # 任务ID
    'name': task.get('name', ''),          # 任务名称
    'status': int,                         # 状态码
    'status_text': str,                    # 状态文本
    'size': int,                           # 文件大小
    'percentDone': float,                  # 完成百分比 (0-100)
    'add_time': int,                       # 添加时间戳
    'file_id': str,                        # 完成后的文件ID
}
```

### 11. _delete_offline_task_web_api()

**功能**：删除离线任务

**请求示例**：
```python
data = {
    'hash[0]': 'task_id_1',
    'hash[1]': 'task_id_2',
    ...
}
```

### 12. _clear_offline_tasks_web_api()

**功能**：清空离线任务

**清空类型**：
- `flag=0`: 清空所有任务
- `flag=1`: 清空已完成任务（推荐）
- `flag=2`: 清空失败任务

**请求示例**：
```python
data = {
    'flag': 1,  # 清空已完成任务
}
```

## 使用示例

### 基础配置（仅 Cookie）

```python
from app.backend.services.pan115_client import Pan115Client

# 仅使用 Cookie，不需要 AppID
client = Pan115Client(
    app_id=None,
    app_secret=None,
    user_id=None,
    user_key="UID=xxx; CID=xxx; SEID=xxx",  # 从浏览器复制的 Cookie
    use_proxy=False
)
```

### 列出文件

```python
result = await client.list_files(parent_id="0", limit=100)

if result['success']:
    for file in result['files']:
        print(f"📄 {file['name']} - {file['size']} bytes")
```

### 删除文件

```python
file_ids = ['file_id_1', 'file_id_2']
result = await client.delete_files(file_ids)

if result['success']:
    print(f"✅ {result['message']}")
```

### 移动文件

```python
file_ids = ['file_id_1', 'file_id_2']
target_dir = 'target_directory_id'

result = await client.move_files(file_ids, target_dir)

if result['success']:
    print(f"✅ 文件已移动")
```

### 复制文件

```python
file_ids = ['file_id_1']
target_dir = 'target_directory_id'

result = await client.copy_files(file_ids, target_dir)

if result['success']:
    print(f"✅ 文件已复制")
```

### 重命名文件

```python
result = await client.rename_file(
    file_id='file_id',
    new_name='新文件名.txt'
)

if result['success']:
    print(f"✅ 重命名成功")
```

### 创建目录

```python
result = await client.create_directory(
    dir_name='新目录',
    parent_id='0'  # 根目录
)

if result['success']:
    print(f"✅ 目录创建成功，ID: {result['dir_id']}")
```

### 获取下载链接

```python
result = await client.get_download_url(
    file_id='pick_code',
    user_agent='CustomUserAgent/1.0'
)

if result['success']:
    print(f"📥 下载链接: {result['download_url']}")
    print(f"📝 文件名: {result['file_name']}")
    print(f"📊 大小: {result['file_size']} bytes")
```

### 添加离线任务

```python
# 添加磁力链接
result = await client.add_offline_task(
    url='magnet:?xt=urn:btih:abc123...',
    target_dir_id='0'
)

if result['success']:
    print(f"✅ 任务添加成功，ID: {result['task_id']}")

# 添加HTTP下载
result = await client.add_offline_task(
    url='https://example.com/file.zip',
    target_dir_id='target_dir_id'
)
```

### 获取离线任务列表

```python
result = await client.get_offline_tasks(page=1)

if result['success']:
    print(f"📋 共有 {result['count']} 个离线任务")
    for task in result['tasks']:
        print(f"  📦 {task['name']}")
        print(f"     状态: {task['status_text']}")
        print(f"     进度: {task['percentDone']:.1f}%")
        print(f"     大小: {task['size'] / 1024 / 1024:.2f} MB")
```

### 删除离线任务

```python
task_ids = ['task_id_1', 'task_id_2']
result = await client.delete_offline_task(task_ids)

if result['success']:
    print(f"✅ {result['message']}")
```

### 清空已完成任务

```python
# 清空已完成任务
result = await client.clear_offline_tasks(flag=1)

if result['success']:
    print(f"✅ 已清空已完成的离线任务")

# 清空失败任务
result = await client.clear_offline_tasks(flag=2)

# 清空所有任务（慎用）
result = await client.clear_offline_tasks(flag=0)
```

## Cookie 获取方法

### 方法 1：浏览器开发者工具

1. 打开 115 网站并登录：https://115.com
2. 按 `F12` 打开开发者工具
3. 切换到 `Network` 标签
4. 刷新页面
5. 点击任意请求，查看 `Request Headers`
6. 复制 `Cookie` 值

### 方法 2：扫码登录（推荐）

使用项目提供的二维码登录功能：

```python
# 1. 获取二维码
result = await client.get_qrcode_token()
qrcode_url = result['qrcode_url']

# 2. 扫码后获取 Cookie
result = await client.poll_qrcode_status(qrcode_token)
if result['success']:
    user_key = result['cookie']  # 这就是需要的 Cookie
```

### Cookie 格式示例

```
UID=123456_A1_1234567890; CID=abcdef1234567890; SEID=xyz789; ...
```

**重要字段**：
- `UID`: 用户ID
- `CID`: 客户端ID
- `SEID`: 会话ID

## 错误处理

### 常见错误

| 错误 | 原因 | 解决方法 |
|------|------|----------|
| `state: false` | API 请求失败 | 检查参数是否正确 |
| HTTP 401/403 | Cookie 无效或过期 | 重新获取 Cookie |
| HTTP 405 | 请求方法错误 | 检查是否使用了正确的 HTTP 方法 |
| `目录已存在` | 创建重复目录 | 自动处理，会返回现有目录ID |
| `下载链接无效` | 离线任务URL不支持 | 检查链接格式是否正确 |
| `任务数量已达上限` | 离线任务配额已满 | 清理已完成的任务 |
| `任务已存在` | 重复添加离线任务 | 任务已在列表中 |

### 错误日志

所有 Web API 操作都会记录详细日志：

```python
logger.info(f"📦 Web API响应: {result}")
logger.error(f"❌ Web API操作异常: {e}")
```

使用 `import traceback; traceback.print_exc()` 输出完整错误堆栈。

## 性能建议

### 1. 批量操作

优先使用批量操作接口：

```python
# 好 ✅
await client.delete_files(['id1', 'id2', 'id3'])

# 差 ❌
for file_id in ['id1', 'id2', 'id3']:
    await client.delete_files([file_id])
```

### 2. 超时设置

不同操作建议不同的超时时间：

- 文件列表：10-30秒
- 删除/移动/复制：30秒
- 下载链接：10秒
- 上传：600秒（10分钟）

### 3. 并发控制

避免同时发起大量请求：

```python
import asyncio

# 使用信号量控制并发
semaphore = asyncio.Semaphore(5)  # 最多5个并发

async def limited_operation(file_id):
    async with semaphore:
        return await client.delete_files([file_id])
```

## 与开放平台 API 对比

| 特性 | Web API | 开放平台 API |
|------|---------|--------------|
| **认证方式** | Cookie | OAuth 2.0 + 签名 |
| **配置复杂度** | 低（仅需 Cookie） | 中（需要 AppID、Secret） |
| **稳定性** | 中（依赖浏览器行为） | 高（官方支持） |
| **功能完整性** | 较完整 | 完整 |
| **上传支持** | 秒传支持，真实上传待完善 | 完整支持 |
| **API文档** | 非官方 | 官方文档 |
| **推荐场景** | 快速集成、个人使用 | 生产环境、企业应用 |

## 最佳实践

### 1. 优先使用开放平台 API

如果可能，建议配置开放平台 AppID：

- ✅ 更稳定
- ✅ 功能更完整
- ✅ 有官方支持

### 2. Web API 作为备选

Web API 适用于以下场景：

- 🎯 快速原型开发
- 🎯 个人工具
- 🎯 临时需求
- 🎯 无法获取开放平台权限

### 3. Cookie 安全

- 🔒 不要在代码中硬编码 Cookie
- 🔒 使用环境变量或配置文件
- 🔒 定期更新 Cookie
- 🔒 不要在公开仓库中提交 Cookie

### 4. 错误重试

实现合理的重试机制：

```python
async def retry_operation(operation, max_retries=3):
    for i in range(max_retries):
        try:
            result = await operation()
            if result['success']:
                return result
        except Exception as e:
            if i == max_retries - 1:
                raise
            await asyncio.sleep(2 ** i)  # 指数退避
```

## 未来改进

### 1. Web API 真实上传

当前 Web API 上传仅支持秒传检测，完整的上传流程包括：

1. ✅ 文件 SHA1 计算
2. ✅ 秒传检测
3. ⚠️ 获取上传地址
4. ⚠️ 分片上传
5. ⚠️ 上传确认

### 2. 搜索功能

计划添加 Web API 搜索支持：

```python
async def _search_files_web_api(self, keyword: str) -> Dict[str, Any]:
    # 待实现
    pass
```

### 3. 文件分享

计划添加 Web API 分享功能：

```python
async def _create_share_web_api(self, file_ids: List[str]) -> Dict[str, Any]:
    # 待实现
    pass
```

### 4. 离线任务进度监控

计划添加实时进度监控：

```python
async def get_offline_task_status(self, task_id: str) -> Dict[str, Any]:
    # 待实现：实时获取单个任务的详细状态
    pass
```

## 故障排查

### 问题：Cookie 认证失败

**症状**：
```
❌ Web API操作异常: HTTP 401
```

**解决**：
1. 检查 Cookie 是否包含 `UID` 和 `CID`
2. 检查 Cookie 是否过期（重新登录）
3. 检查网络连接

### 问题：文件ID格式错误

**症状**：
```
❌ Web API操作异常: 参数错误
```

**解决**：
1. 确认使用正确的 ID 类型（fid vs cid）
2. 检查是否使用了数组格式 `fid[0]`, `fid[1]`

### 问题：操作无响应

**症状**：请求长时间没有返回

**解决**：
1. 检查代理设置（`use_proxy` 参数）
2. 增加超时时间
3. 检查网络连接

## 技术支持

- 📖 查看开放平台文档：[115 云盘开放平台](https://www.yuque.com/115yun/open)
- 🐛 报告问题：项目 Issues
- 💬 技术讨论：项目 Discussions

## 更新日志

### v1.1.0 (2025-01-18)

- ✅ 新增离线下载功能
- ✅ 添加离线任务（HTTP/磁力/BT）
- ✅ 获取离线任务列表
- ✅ 删除离线任务
- ✅ 清空已完成/失败任务
- ✅ 支持开放平台 API 和 Web API 双模式

### v1.0.0 (2025-01-17)

- ✅ 实现基础文件操作 Web API 支持
- ✅ 列出文件
- ✅ 删除文件
- ✅ 移动文件
- ✅ 复制文件
- ✅ 重命名文件
- ✅ 创建目录
- ✅ 获取下载链接
- ⚠️ 上传文件（秒传支持）

---

**最后更新**：2025-01-18  
**维护者**：TMC 项目团队

