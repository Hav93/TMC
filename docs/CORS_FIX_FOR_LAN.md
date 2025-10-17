# CORS修复：局域网访问失败问题

## ❌ 问题症状

从局域网其他设备访问时出现：
- `Failed to fetch`
- 代理测试连接失败
- 前端API调用失败

**日志显示**：
```
INFO: 192.168.31.6:44266 - "GET /api/settings HTTP/1.1" 200 OK
但前端报错: Failed to fetch
```

## 🔍 根本原因

CORS配置只允许了localhost，没有允许局域网IP：

```python
# ❌ 旧配置（只允许localhost）
allow_origins=[
    "http://localhost:3000",
    "http://localhost:9393",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:9393",
],
```

当从`192.168.31.6:9393`访问时，浏览器会阻止跨域请求。

## ✅ 解决方案

已修改为允许所有来源：

```python
# ✅ 新配置（允许所有域名）
allow_origins=["*"],
```

## 🚀 部署修复

### 方法1：拉取最新代码

```bash
cd /path/to/TMC
git pull origin test
docker-compose build --no-cache
docker-compose up -d
```

### 方法2：手动修改

编辑 `app/backend/main.py`：

```python
# 找到第234行左右的CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 改为 ["*"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

然后重启容器：
```bash
docker-compose restart
```

## ⚠️ 安全建议

### 开发/内网环境
使用`["*"]`没问题，方便开发和内网访问。

### 生产环境（公网）
建议指定具体域名：

```python
allow_origins=[
    "https://your-domain.com",
    "https://www.your-domain.com",
],
```

或使用环境变量：

```python
# main.py
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    ...
)
```

```bash
# .env
ALLOWED_ORIGINS=https://domain1.com,https://domain2.com
```

## 🧪 验证修复

1. **检查容器日志**：
   ```bash
   docker logs tmc-local -f
   ```

2. **测试代理连接**：
   - 打开：`http://your-server-ip:9393/settings`
   - 点击"测试连接"
   - 应该能正常返回结果

3. **检查浏览器控制台**：
   - 按F12打开开发者工具
   - 查看Console标签
   - 不应该有CORS错误

## 📝 相关问题

### 问题：还是报Failed to fetch？

**检查清单**：
1. ✅ 容器已重启
2. ✅ 浏览器已清除缓存
3. ✅ JWT Token有效（重新登录）
4. ✅ 后端服务正常运行

### 问题：特定API还是失败？

可能是JWT Token过期，解决方案：
1. 设置固定的`JWT_SECRET_KEY`（见`docs/SERVER_DEPLOYMENT_GUIDE.md`）
2. 清除浏览器缓存
3. 重新登录

---

**修复版本**: Commit `9b87968`  
**更新日期**: 2025-10-18  
**状态**: ✅ 已修复

