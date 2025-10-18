# 115网盘上传模块说明

## 概述

这是一个完全基于 Python 实现的 115 网盘上传模块，移植自 Go 语言项目 [fake115uploader](https://github.com/fakename/fake115uploader)。

## 核心文件

### 1. ecdh_cipher.py
实现了 115 网盘的 ECDH 加密机制：
- P-224 椭圆曲线密钥协商
- AES 加密/解密
- LZ4 压缩/解压
- k_ec 参数生成（Token 编码）

**关键类：**
- `EcdhCipher`: ECDH 加密器
  - `encrypt(plaintext)`: 加密明文
  - `decrypt(ciphertext)`: 解密密文
  - `encode_token(timestamp)`: 生成 k_ec 参数

### 2. file_hash.py
文件哈希计算工具：
- SHA1 哈希计算（完整文件和前 128KB）
- 范围 SHA1 计算（用于二次验证）
- MD5 计算（用于 OSS 上传）

**主要函数：**
- `calculate_sha1(file_path)`: 返回 (block_hash, total_hash)
- `calculate_range_sha1(file_path, start, end)`: 计算指定范围的 SHA1
- `calculate_file_md5(file_path)`: 计算文件 MD5
- `calculate_content_md5(data)`: 计算内容 MD5（Base64）

### 3. upload_signature.py
115 上传签名算法：
- sig 签名计算
- token 签名计算
- 表单数据构建

**关键类：**
- `UploadSignature`: 签名计算器
  - `calculate_sig(file_id, target)`: 计算 sig 签名
  - `calculate_token(...)`: 计算 token 签名
  - `build_upload_form(...)`: 构建上传表单

**签名算法：**
```
sig = SHA1(userKey + SHA1(userID + fileID + target + "0") + "000000")

token = MD5(
    salt + fileID + fileSize + signKey + signVal + 
    userID + timestamp + MD5(userID) + appVersion
)
```

### 4. upload115.py
完整的上传逻辑实现：
- 秒传（SHA1 快速上传）
- 二次验证处理
- 普通 OSS 上传（小文件）
- 分片 OSS 上传（大文件）
- 上传验证

**关键类：**
- `Upload115`: 115 上传器
  - `upload_file(file_path, target_cid)`: 主上传方法
  - `_fast_upload(...)`: 尝试秒传
  - `_normal_upload(...)`: 普通上传
  - `_multipart_upload(...)`: 分片上传
  - `_verify_upload(...)`: 验证上传

## 上传流程

```
1. 计算文件 SHA1
   ↓
2. 尝试秒传（上传 SHA1 到 115 服务器）
   ↓
   ├─ 秒传成功 → 完成
   ├─ 需要二次验证 → 计算指定范围 SHA1 → 重新秒传
   └─ 秒传失败 → 获取 fastToken
       ↓
3. 获取 OSS 临时凭证
   ↓
4. 选择上传方式
   ├─ 文件 ≤ 100MB → 普通上传
   └─ 文件 > 100MB → 分片上传
       ↓
5. 上传到阿里云 OSS
   ↓
6. OSS 触发回调通知 115
   ↓
7. 验证上传成功
```

## 依赖库

```bash
pip install cryptography>=43.0.0  # ECDH 加密
pip install lz4>=4.3.2            # LZ4 压缩/解压
pip install oss2>=2.18.0          # 阿里云 OSS SDK
pip install httpx>=0.27.0         # HTTP 客户端
```

## 使用示例

### 基本使用

```python
from upload115 import create_uploader

# 创建上传器
uploader = create_uploader(
    user_id="123456",           # 用户ID
    user_key="your_user_key",   # 用户密钥（从 /app/uploadinfo 获取）
    cookies="UID=...; CID=...",  # Cookie 字符串
    use_proxy=False
)

# 上传文件
result = await uploader.upload_file(
    file_path="/path/to/file.mp4",
    target_cid="0"  # 目标目录ID，0 表示根目录
)

print(result)
# {'success': True, 'message': '秒传成功', 'quick_upload': True, 'file_id': '...'}
```

### 在 Pan115Client 中集成

```python
from services.pan115_client import Pan115Client

client = Pan115Client(
    app_id="",  # 留空
    app_key="", # 留空
    user_id="123456",
    user_key="UID=...; CID=...",  # Cookie
    use_proxy=False
)

# 上传文件（自动使用新的上传逻辑）
result = await client.upload_file(
    file_path="/path/to/file.mp4",
    target_dir_id="0"
)
```

## 技术细节

### ECDH 加密

115 使用 P-224 椭圆曲线进行密钥协商：

1. **密钥生成：**
   - 客户端生成本地 P-224 密钥对
   - 使用硬编码的 115 服务器公钥
   - 计算 ECDH 共享密钥

2. **密钥派生：**
   ```
   共享密钥 = ECDH(本地私钥, 服务器公钥)
   AES密钥 = 共享密钥[:16]   # 前16字节
   AES_IV = 共享密钥[-16:]    # 后16字节
   ```

3. **加密流程：**
   ```
   明文 → PKCS7填充 → XOR IV → AES-ECB加密 → 密文
   ```

4. **解密流程：**
   ```
   密文 → AES-CBC解密 → LZ4解压 → 明文
   ```

### k_ec 参数结构

k_ec 是一个 48 字节的特殊编码，包含：

```
字节 0-14:   本地公钥前15字节 XOR r1
字节 15:     r1（随机数）
字节 16:     0x73 XOR r1
字节 17-19:  r1（重复3次）
字节 20-23:  时间戳（大端序）XOR r1
字节 24-38:  本地公钥后15字节 XOR r2
字节 39:     r2（随机数）
字节 40:     0x01 XOR r2
字节 41-43:  r2（重复3次）
字节 44-47:  CRC32校验和（包含盐值）
```

最后进行 Base64 编码作为 URL 参数。

### 分片上传策略

根据文件大小自动确定分片数量：

| 文件大小 | 分片数 | 每片大小（约） |
|---------|--------|---------------|
| < 1GB   | 1000   | ~1MB          |
| 1-2GB   | 2000   | ~1MB          |
| 2-3GB   | 3000   | ~1MB          |
| ...     | ...    | ...           |
| > 9GB   | 10000  | ~1MB+         |

每片最小 100KB，最大 10000 片（约 115GB）。

### OSS 回调机制

115 使用阿里云 OSS 的回调功能通知上传完成：

1. 上传文件到 OSS 时设置回调参数
2. OSS 上传成功后自动调用 115 的回调 URL
3. 115 服务器验证回调并创建文件记录
4. 客户端通过查询文件列表验证上传成功

**重要 Header：**
- `x-oss-security-token`: STS 临时令牌
- `x-oss-hash-sha1`: 文件 SHA1（仅分片上传）
- `x-oss-callback`: Base64 编码的回调 URL
- `x-oss-callback-var`: Base64 编码的回调变量

## 常见问题

### 1. 秒传失败，需要二次验证

**问题：** 服务器返回 status=7, statuscode=701

**解决：**
- 服务器要求验证文件的指定范围（sign_check: "0-131071"）
- 计算该范围的 SHA1 作为 sign_val
- 使用 sign_key 和 sign_val 重新上传

**代码已自动处理这种情况。**

### 2. OSS 上传失败

**可能原因：**
- STS 凭证过期（每小时过期）
- 网络问题
- Bucket 或 Object 配置错误

**解决：**
- 自动重试机制（分片失败重试 3 次）
- Token 自动刷新（提前 10 分钟）

### 3. 缺少 lz4 库

**问题：** ImportError: No module named 'lz4'

**解决：**
```bash
pip install lz4
```

如果安装失败（Windows），可以尝试：
```bash
pip install lz4-wheels
```

### 4. 缺少 oss2 库

**问题：** ImportError: No module named 'oss2'

**解决：**
```bash
pip install oss2
```

## 性能优化

1. **并发上传：** 分片上传时可并发上传多个分片
2. **断点续传：** 保存上传进度，支持中断恢复
3. **秒传优化：** 优先尝试秒传，节省带宽
4. **智能分片：** 根据文件大小自动调整分片策略

## 安全性

1. **端到端加密：** 请求/响应使用 ECDH+AES 加密
2. **多重签名：** sig、token、k_ec 三重签名验证
3. **防重放：** 时间戳机制防止重放攻击
4. **二次验证：** 对可疑文件进行范围哈希验证

## 参考资料

- [fake115uploader 源码](https://github.com/fakename/fake115uploader)
- [阿里云 OSS API](https://help.aliyun.com/document_detail/31948.html)
- [115 网盘开放平台](https://www.yuque.com/115yun/open)

## 许可证

基于原项目 fake115uploader 的许可证。

## 维护

- 作者：TMC Team
- 版本：1.0.0
- 日期：2025-10-18

