# 115上传模块故障排除

## 已解决的问题

### ❌ 问题1: 相对导入错误 (✅ 已修复)

**错误信息:**
```
❌ 导入上传模块失败: attempted relative import with no known parent package
```

**解决方案:** 添加try-except块支持相对和绝对导入  
**修复提交:** `f9092c5`

---

### ❌ 问题2: ECDH公钥验证失败 (⏸️ 临时禁用)

**错误信息:**
```
ValueError: Invalid EC key. Point is not on the curve specified.
```

**原因分析:**
- 115服务器的ECDH公钥点不在P-224曲线上
- 可能是公钥字节序或格式问题
- 需要从Go源码中确认正确的公钥处理方式

**临时方案:**
- 暂时禁用ECDH加密上传（第706行设置 `if False`）
- 保留传统上传方式
- 等待修复后重新启用

**后续计划:**
- [ ] 研究fake115uploader的Go源码中公钥处理方式
- [ ] 测试不同的公钥解析方法
- [ ] 或使用预计算的共享密钥

**修复提交:** `0850c91`

---

## 历史问题（已解决）

### ❌ 问题1: 相对导入错误 (✅ 完全修复)

**错误信息:**
```
❌ 导入上传模块失败: attempted relative import with no known parent package
```

**原因:**
- `upload115.py` 使用了相对导入 `from .ecdh_cipher import ...`
- 当通过 `sys.path` 动态导入时，Python无法识别包结构
- 相对导入只在作为包的一部分时有效

**解决方案:**
```python
# 添加了try-except块同时支持两种导入方式
try:
    from .ecdh_cipher import create_ecdh_cipher, EcdhCipher
    from .file_hash import calculate_sha1, calculate_range_sha1
    from .upload_signature import create_signature_calculator, UploadSignature
except ImportError:
    from ecdh_cipher import create_ecdh_cipher, EcdhCipher
    from file_hash import calculate_sha1, calculate_range_sha1
    from upload_signature import create_signature_calculator, UploadSignature
```

**适用场景:**
- ✅ 作为包导入: `from utils.upload115 import create_uploader`
- ✅ 动态导入: `sys.path.insert(0, 'utils'); import upload115`

**修复提交:** `f9092c5`

---

## 当前已知问题

### ⚠️ 问题2: 秒传失败

从日志看到：
```
📦 秒传响应: {'state': False, 'error': '', 'errno': ''}
```

**可能原因:**
1. 文件未在115服务器的秒传数据库中
2. Cookie认证信息不完整
3. 秒传请求格式问题

**下一步排查:**
- [ ] 检查Cookie是否有效
- [ ] 确认是否获取到userkey
- [ ] 验证ECDH加密是否正确
- [ ] 测试已知可秒传的文件（如常见电影）

### ⚠️ 问题3: STS上传bucket未知

日志显示：
```
⚠️ STS上传暂不支持（bucket未知），尝试回退到旧的上传方式
```

**原因:**
- 115的API响应中没有直接提供bucket名称
- 需要通过秒传失败后的响应获取bucket信息

**解决方案:**
使用我们的Python实现，它会：
1. 先尝试秒传获取fastToken（包含bucket信息）
2. 如果秒传失败，fastToken中会包含bucket和object信息
3. 使用这些信息进行OSS上传

### ⚠️ 问题4: 传统Web API上传失败

日志显示：
```
❌ 所有上传端点都失败
💡 建议：Web API真实上传较复杂，建议配置开放平台AppID
```

**原因:**
- 传统Web API上传需要复杂的签名和参数
- 直接表单上传通常会被拒绝
- 115的Web API主要用于网页端，不太适合程序调用

**解决方案:**
使用我们新实现的Python上传逻辑（基于fake115uploader）

---

## 完整的上传流程应该是

### ✅ 正确的流程（使用Python实现）

```
1. 调用 _upload_with_fake115_python()
   ↓
2. 获取用户信息（user_id, userkey）
   ↓
3. 创建Upload115实例
   ↓
4. 计算文件SHA1
   ↓
5. 尝试秒传（上传SHA1到115）
   ├─ 成功 → 完成 ✅
   ├─ 需要验证 → 计算范围SHA1 → 重新秒传
   └─ 失败 → 获取fastToken
       ↓
6. fastToken包含:
   - bucket: OSS bucket名称
   - object: OSS object key
   - callback: 115回调URL
   ↓
7. 获取OSS临时凭证
   ↓
8. 上传到OSS（普通上传或分片上传）
   ↓
9. OSS触发回调通知115
   ↓
10. 验证上传成功 ✅
```

### ❌ 当前错误的流程（回退到传统方式）

```
1. Python实现导入失败
   ↓
2. 回退到传统Web API
   ↓
3. 尝试秒传（格式可能不对）
   ↓
4. 秒传失败
   ↓
5. 尝试STS上传（bucket未知，失败）
   ↓
6. 尝试表单上传（被拒绝）
   ↓
7. 所有方式都失败 ❌
```

---

## 测试计划

### 1. 验证导入修复

```bash
cd app/backend
python3 << 'EOF'
import sys
from pathlib import Path

# 添加utils到路径
utils_path = Path(__file__).parent / 'utils'
sys.path.insert(0, str(utils_path))

# 测试导入
try:
    from upload115 import create_uploader
    print("✅ 导入成功")
except Exception as e:
    print(f"❌ 导入失败: {e}")
EOF
```

### 2. 测试ECDH加密

```bash
python -m utils.test_upload115
```

应该输出：
```
✅ 文件哈希测试通过
✅ ECDH加密测试通过
✅ 上传签名测试通过
```

### 3. 测试真实上传（需要配置）

```bash
# 设置环境变量
export TEST_115_USER_ID="your_user_id"
export TEST_115_USER_KEY="your_user_key"
export TEST_115_COOKIES="UID=...; CID=..."

# 运行测试
python -m utils.test_upload115
```

---

## 调试技巧

### 1. 启用详细日志

在 `pan115_client.py` 中：
```python
logger.setLevel(logging.DEBUG)
```

### 2. 测试单个模块

```python
# 测试ECDH
from utils.ecdh_cipher import create_ecdh_cipher
cipher = create_ecdh_cipher()
encrypted = cipher.encrypt(b"test")
print(f"加密成功: {len(encrypted)} bytes")

# 测试文件哈希
from utils.file_hash import calculate_sha1
block_hash, total_hash = calculate_sha1("test.txt")
print(f"SHA1: {total_hash}")

# 测试签名
from utils.upload_signature import create_signature_calculator
sig = create_signature_calculator("123", "key")
result = sig.calculate_sig("A"*40, "U_1_0")
print(f"签名: {result}")
```

### 3. 检查依赖

```bash
pip list | grep -E "lz4|oss2|cryptography"
```

应该显示：
```
cryptography    43.0.3
lz4             4.3.2
oss2            2.18.0
```

---

## 常见错误及解决

### 错误: ModuleNotFoundError: No module named 'lz4'

**解决:**
```bash
pip install lz4
```

### 错误: ModuleNotFoundError: No module named 'oss2'

**解决:**
```bash
pip install oss2
```

### 错误: ImportError: cannot import name 'create_ecdh_cipher'

**原因:** 文件未正确导入或语法错误

**解决:**
```bash
# 检查语法
python -m py_compile app/backend/utils/ecdh_cipher.py

# 测试导入
python -c "from utils.ecdh_cipher import create_ecdh_cipher"
```

### 错误: 秒传响应 state=False

**可能原因:**
1. 文件不在115的秒传库中（正常情况）
2. Cookie无效或过期
3. 签名计算错误

**排查:**
- 检查Cookie是否有效（访问115网页）
- 确认获取到了userkey
- 尝试上传常见文件（如Ubuntu ISO）

---

## 下一步优化

1. **改进错误处理**
   - 更详细的错误信息
   - 区分不同的失败原因

2. **添加重试机制**
   - 秒传失败自动重试
   - 网络错误自动重试

3. **优化日志输出**
   - 添加更多调试信息
   - 彩色日志输出

4. **性能优化**
   - 并发上传分片
   - 缓存OSS凭证

---

**更新时间:** 2025-10-18 23:30  
**状态:** 导入问题已修复 ✅  
**版本:** v1.0.1

