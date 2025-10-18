# 115 Web API 上传实现指南

基于 p115client 文档和逆向分析的完整上传实现

## 📚 参考资料

- [p115client 官方文档](https://p115client.readthedocs.io/en/latest/reference/module/client.html)
- 115 Web API 接口分析
- AList 115驱动实现

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
```env
PAN115_APP_ID=your_app_id
PAN115_APP_SECRET=your_app_secret
```

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

**最佳实践**：配置开放平台AppID

```bash
# 1. 访问 https://open.115.com/ 申请AppID
# 2. 配置环境变量
PAN115_APP_ID=your_app_id
PAN115_APP_SECRET=your_app_secret
# 3. 重启应用
docker-compose restart
```

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

## 🔄 未来改进

### 短期目标
- [ ] 继续尝试简化的上传接口
- [ ] 改善错误提示和用户引导
- [ ] 完善文档

### 长期目标  
- [ ] 研究上传签名算法（如果有时间和兴趣）
- [ ] 寻找社区中的其他实现方案
- [ ] 监控115 API的变化

---

## 📞 联系与支持

如果你：
- ✅ 成功破解了上传签名算法
- ✅ 发现了新的上传方式
- ✅ 有其他改进建议

欢迎：
- 提交 Pull Request
- 创建 Issue讨论
- 分享你的发现

---

**最后更新**：2025-01-18  
**维护者**：TMC 项目团队  
**参考**：[p115client文档](https://p115client.readthedocs.io/)

