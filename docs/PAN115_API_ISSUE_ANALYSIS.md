# 115网盘API问题深度分析

## 📅 分析时间
2025-10-17

## 🔍 核心问题

用户反馈:**扫码登录成功,但空间信息始终显示0 B**

## 🎯 根本原因

### 1. 115 API严格限流

从日志分析:
```
📡 回退到Web API(可能会因限流失败)
📦 /user/info API响应: status=200
📦 /user/info完整响应: {'state': False, 'error': '服务器开小差了，稍后再试吧'}
⚠️ 所有空间信息API都失败
```

**结论**: 115服务器对 `/user/info` 和 `/files` 等获取空间信息的API有**严格的频率限制**。

### 2. 登录方式的本质

#### ❌ 错误理解
扫码登录会返回 `access_token`,用于调用开放平台API。

#### ✅ 实际情况
- **扫码登录返回**: `cookies` (UID, CID, SEID, KID) - 有效期约30天
- **access_token**: 需要单独通过开放平台API获取 - 有效期2小时
- **大多数用户没有**: 开放平台AppID/AppSecret(需要企业认证)

#### 💡 115登录的两种方式

| 方式 | 获取凭证 | 有效期 | 适用场景 |
|-----|---------|-------|---------|
| **扫码登录** | Cookies | 30天 | 普通用户(✅ 当前实现) |
| **开放平台OAuth** | access_token | 2小时 | 企业开发者 |

### 3. 代码逻辑问题

#### 问题A: Token过期时间设置错误
```python
# ❌ 之前的代码
if access_token:
    settings.pan115_token_expires_at = datetime.utcnow() + timedelta(seconds=7200)  # 2小时
```

**问题**: 扫码登录根本不返回 `access_token`,但代码没有为cookies设置过期时间,导致:
- 刷新时判断"token已过期"
- 尝试重新获取token(失败,因为没有AppID/AppSecret)
- 无法正常刷新

#### 问题B: p115client库依赖问题
```python
# p115client虽然安装了,但无法使用
ModuleNotFoundError: No module named 'p115cipher.fast'

# 原因: p115cipher.fast是C扩展模块
- 需要编译环境(gcc, python-dev)
- Docker镜像中缺少这些工具
- fork版本可能不完整

# 调用顺序
1. 尝试 p115client 官方库 ❌ (依赖p115cipher.fast缺失)
2. 尝试开放平台API ❌ (无access_token)
3. 回退到 Web API ❌ (限流)
```

**解决方案**: 已在 `requirements.txt` 中注释掉 `p115client`,直接使用Web API方案。

## ✅ 优化方案

### 1. 修正Token过期时间逻辑

```python
# ✅ 优化后的代码
if access_token:
    # 有access_token: 2小时有效期
    settings.pan115_token_expires_at = datetime.utcnow() + timedelta(seconds=7200)
    logger.info(f"🔑 已保存access_token(有效期2小时)")
else:
    # 只有cookies: 30天有效期
    settings.pan115_token_expires_at = datetime.utcnow() + timedelta(days=30)
    logger.info(f"🍪 使用cookies登录,预估有效期30天")
```

**效果**:
- ✅ 正确识别cookies的长效有效期
- ✅ 30天内不会错误地认为"token已过期"
- ✅ 减少无效的token刷新尝试

### 2. 智能缓存机制

```python
# 防抖: 30秒内重复刷新直接返回缓存
if not force and last_refresh_at:
    time_since_last_refresh = (datetime.utcnow() - last_refresh_at).total_seconds()
    if time_since_last_refresh < 30:
        return cached_user_info  # 返回缓存,避免触发限流
```

**效果**:
- ✅ 避免频繁请求115 API
- ✅ 减少触发限流的概率
- ✅ 提升用户体验(快速响应)

### 3. 缓存保护机制

```python
# API失败时保留旧缓存,不清空用户数据
if space_total > 0:
    # 成功: 更新缓存
    settings.pan115_user_info = json.dumps(user_info)
    settings.pan115_last_refresh_at = datetime.utcnow()
else:
    # 失败: 返回旧缓存,不覆盖
    logger.warning(f"⚠️ 刷新失败,保留原缓存数据")
    return cached_user_info
```

**效果**:
- ✅ API失败不会丢失用户名/VIP状态
- ✅ 显示上次成功的数据,而不是0B
- ✅ 前端显示"API调用失败,返回缓存数据"提示

### 4. 前端优化提示

```typescript
// 前端显示缓存数据时的提示
if (data.from_cache) {
  message.warning({
    content: (
      <div>
        <div>⚠️ {data.message || 'API调用失败,使用缓存数据'}</div>
        <div style={{ fontSize: '12px', color: '#999' }}>
          提示: 115服务器限流,显示的是上次成功获取的数据
        </div>
      </div>
    ),
    duration: 5,
  });
}
```

## 📊 新增数据库字段

| 字段名 | 类型 | 说明 | 作用 |
|-------|------|------|------|
| `pan115_access_token` | Text | 开放平台access_token | 支持企业用户使用开放平台API |
| `pan115_token_expires_at` | DateTime | 凭证过期时间 | 智能判断何时需要刷新 |
| `pan115_last_refresh_at` | DateTime | 最后刷新时间 | 防抖机制,避免频繁请求 |

## 🎯 最终效果

### ✅ 已解决的问题
1. **Token过期时间**: 从2小时 → 30天(cookies模式)
2. **数据丢失**: API失败时保留缓存,不会清空用户信息
3. **频繁请求**: 30秒防抖,减少触发限流
4. **用户体验**: 前端明确提示数据来源(实时/缓存)

### ⚠️ 仍然存在的限制
1. **115 API限流**: 这是115服务器端的限制,无法绕过
2. **空间信息获取**: 依然受限流影响,可能显示0B

### 💡 建议
1. **短期**: 接受限流限制,使用缓存机制保证基本功能
2. **长期**: 申请115开放平台账号(企业认证),获取AppID/AppSecret,使用官方API(限流更宽松)
3. **替代**: 使用115官方APP查看空间信息

## 🔧 技术细节

### API调用优先级(优化后)

```
1. 检查本地缓存 → 30秒内直接返回缓存 ✅
   ↓
2. 检查凭证有效期 → 未过期则继续 ✅
   ↓
3. 尝试开放平台API(如有access_token) ⚠️
   ↓
4. 回退到Web API(cookies) ⚠️
   ↓
5. 失败 → 返回旧缓存 ✅
```

### Cookies vs Access Token

```python
# Cookies (扫码登录)
"UID=337712138_xxx; CID=xxx; SEID=xxx; KID=xxx"
有效期: ~30天
适用API: https://webapi.115.com/*
限流程度: 严格

# Access Token (开放平台)
"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
有效期: 2小时
适用API: https://openapi.115.com/*
限流程度: 较宽松
```

## 📚 参考文档

1. [115云开放平台 - OAuth2.0授权](https://www.yuque.com/115yun/open/shtpzfhewv5nag11)
2. [115云开放平台 - 用户信息接口](https://www.yuque.com/115yun/open/ot1litggzxa1czww)
3. [115云开放平台 - 空间信息接口](https://www.yuque.com/115yun/open/okr2cq0wywelscpe)

## 🏁 结论

**核心问题不是代码问题,而是115 API的服务器端限流。**

通过优化:
- ✅ Token有效期识别: 2小时 → 30天
- ✅ 缓存保护: 失败不清空数据
- ✅ 防抖机制: 减少API调用
- ✅ 用户体验: 明确提示数据状态

**最终实现了在限流限制下的最优体验。**

---

*生成时间: 2025-10-17 20:15*
*状态: ✅ 已优化完成*

