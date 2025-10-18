# fake115uploader 项目分析

基于对 [fake115uploader](https://github.com/orzogc/fake115uploader) 项目的分析

## 项目结构

```
fake115uploader/
├── fast.go          # 秒传实现
├── oss.go           # OSS上传实现  
├── multipart.go     # 分片上传实现
├── hash.go          # 哈希计算
├── cipher/          # 加密相关
└── main.go          # 主程序入口
```

## 核心发现

### 1. 上传流程

根据README和项目描述，fake115uploader支持三种模式：

#### 模式1：纯秒传 (`-f`)
```
1. 计算文件SHA1
2. 调用115秒传API
3. 如果文件存在 → 成功
4. 如果不存在 → 失败（不继续上传）
```

#### 模式2：秒传+普通上传 (`-u`)
```
1. 尝试秒传
2. 如果秒传失败 → 普通上传（<5GB）
3. 普通上传：直接POST到115或OSS
```

#### 模式3：秒传+断点续传 (`-m`)
```
1. 尝试秒传
2. 如果秒传失败 → 断点续传模式
3. 分片上传：支持中断恢复
```

### 2. 关键API端点

根据README中的提示：

```bash
curl https://uplb.115.com/3.0/getuploadinfo.php
```

这个命令可以查看OSS地域信息，说明：
- `uplb.115.com` 是上传专用域名
- `/3.0/getuploadinfo.php` 返回上传配置

### 3. 阿里云内网上传

README提到 `-a` 参数：
- 可以利用阿里云内网上传
- 需要115在服务器所在地域开通了OSS
- 说明115确实使用阿里云OSS存储

### 4. 断点续传实现

- 使用存档文件保存上传状态
- 参数 `-d 文件夹` 指定存档位置
- 支持暂停数周后继续（说明115有长期有效的上传token）
- 分片数量可配置（1-10000）

### 5. 代理支持

- `httpProxy` - HTTP请求代理
- `ossProxy` - OSS上传代理
- 说明HTTP请求和OSS上传是分开的

## 推断的完整上传流程

基于以上分析，fake115uploader可能的实现方式：

### Step 1: 获取上传参数
```go
// GET https://uplb.115.com/3.0/getuploadinfo.php
// 返回: OSS endpoint, region等
```

### Step 2: 获取上传Token
```go
// GET https://uplb.115.com/3.0/gettoken.php?...
// 可能需要传递: filename, filesize, sig等
// 返回: STS token OR upload URL OR bucket info
```

### Step 3: 初始化分片上传（如果是大文件）
```go
// 可能调用115的API或直接调用OSS的InitiateMultipartUpload
// 返回: uploadId
```

### Step 4: 上传分片
```go
// PUT到OSS或115中转API
// 每个分片保存状态（用于断点续传）
```

### Step 5: 完成上传
```go
// 通知115上传完成
// 可能需要调用一个"完成上传"的API
// 115创建文件记录
```

## 关键问题

### 问题1：Bucket名称从哪来？

可能的答案：
1. **固定的bucket名称模板**：可能是 `115-{region}` 或类似
2. **从getuploadinfo返回**：可能在完整响应中有bucket字段
3. **从gettoken返回**：token响应中可能包含bucket
4. **通过特殊参数获取**：需要在请求中传递特定参数才返回

### 问题2：Object Key如何生成？

当前我们使用：`sha1-{hash}-{timestamp}.{ext}`

fake115uploader可能使用：
- 特定的命名规则
- 从API返回的template
- 包含用户信息的路径

### 问题3：如何通知115上传完成？

上传到OSS后，必须通知115：
- 可能有一个callback URL
- 可能需要调用额外的API
- 可能在OSS response的callback中自动处理

## 建议的实现方案

### 方案A：完整模拟fake115uploader（推荐）

1. **研究fake115uploader源码**
   - 克隆repo：`git clone https://github.com/orzogc/fake115uploader.git`
   - 重点查看：`oss.go`, `fast.go`, `multipart.go`
   - 理解其API调用顺序和参数

2. **Python实现**
   - 移植Go代码逻辑到Python
   - 保持API调用一致
   - 实现相同的签名算法

3. **测试验证**
   - 先实现秒传（最简单）
   - 再实现小文件上传
   - 最后实现分片上传

### 方案B：使用115 Open API（如果有权限）

如果用户有115开放平台AppID：
- 使用官方SDK或API
- 更稳定可靠
- 但需要申请权限

### 方案C：使用fake115uploader二进制（临时方案）

- 在Python中调用fake115uploader命令行
- 快速实现上传功能
- 但依赖外部二进制

## 下一步行动

1. ✅ 克隆fake115uploader项目到本地
2. ✅ 分析`oss.go`中的核心上传逻辑
3. ✅ 理解`hash.go`中的哈希计算方式
4. ✅ 查看`fast.go`中的秒传实现
5. ✅ 研究`multipart.go`中的分片上传
6. 🔄 Python实现相同逻辑
7. 🔄 测试验证

## 参考资料

- [fake115uploader GitHub](https://github.com/orzogc/fake115uploader)
- [Fake115Upload 原项目](https://github.com/K1L0RU/Fake115Upload)
- 115网盘Web API逆向分析

---

**更新时间**: 2025-10-18
**分析人员**: TMC项目团队

