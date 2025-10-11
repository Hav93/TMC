# 🚀 API快速开始指南

> 5分钟快速上手Telegram Message Central API

---

## 📍 第一步：访问API文档

### Swagger UI（推荐）
**🔗 http://localhost:9393/docs**

- 交互式测试界面
- 可以直接在浏览器中测试API
- 自动填充示例数据

### ReDoc
**🔗 http://localhost:9393/redoc**

- 美观的阅读界面
- 适合学习和理解API
- 更好的打印效果

---

## 🔐 第二步：获取访问令牌

### 方法1: 使用Swagger UI

1. 打开 http://localhost:9393/docs
2. 找到 **认证** 分组
3. 点击 `POST /api/auth/login`
4. 点击 **Try it out**
5. 输入：
   ```json
   {
     "username": "admin",
     "password": "admin123"
   }
   ```
6. 点击 **Execute**
7. 复制返回的 `access_token`

### 方法2: 使用curl

```bash
curl -X POST "http://localhost:9393/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**响应示例**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## 🎯 第三步：使用Token测试API

### 在Swagger UI中

1. 点击页面右上角的 **🔓 Authorize** 按钮
2. 输入：`Bearer <your-token>`
   ```
   Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
3. 点击 **Authorize**
4. 现在可以测试任何需要认证的API了！

### 使用curl

```bash
# 获取转发规则列表
curl -X GET "http://localhost:9393/api/rules" \
  -H "Authorization: Bearer <your-token>"

# 获取下载任务
curl -X GET "http://localhost:9393/api/media/download-tasks" \
  -H "Authorization: Bearer <your-token>"
```

---

## 💡 常用API示例

### 1️⃣ 创建转发规则

```bash
curl -X POST "http://localhost:9393/api/rules" \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "我的第一个规则",
    "client_id": 1,
    "source_chats": "[\"123456789\"]",
    "target_chat_id": 987654321,
    "enabled": true
  }'
```

### 2️⃣ 创建媒体监控规则

```bash
curl -X POST "http://localhost:9393/api/media/monitor/rules" \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "频道视频下载",
    "client_id": 1,
    "source_chats": "[\"123456789\"]",
    "media_types": "[\"video\",\"document\"]",
    "enabled": true
  }'
```

### 3️⃣ 查看下载任务

```bash
curl -X GET "http://localhost:9393/api/media/download-tasks?status=completed&page=1&page_size=20" \
  -H "Authorization: Bearer <your-token>"
```

### 4️⃣ 获取115网盘登录二维码

```bash
curl -X POST "http://localhost:9393/api/pan115/qrcode" \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"app_id":"your_app_id"}'
```

---

## 📚 API分类速查

| 分类 | 端点前缀 | 主要功能 |
|------|----------|----------|
| 认证 | `/api/auth` | 登录、注册、用户管理 |
| 转发规则 | `/api/rules` | 消息转发规则管理 |
| 媒体监控 | `/api/media/monitor` | 媒体监控规则 |
| 媒体文件 | `/api/media` | 文件和下载任务管理 |
| 115网盘 | `/api/pan115` | 115云盘集成 |
| 客户端 | `/api/clients` | Telegram客户端管理 |
| 系统 | `/api/system` | 系统信息和统计 |

---

## 🔍 状态码说明

| 状态码 | 含义 | 说明 |
|--------|------|------|
| 200 | ✅ 成功 | 请求成功 |
| 201 | ✅ 已创建 | 资源创建成功 |
| 400 | ❌ 请求错误 | 参数验证失败 |
| 401 | ❌ 未认证 | 需要登录或Token无效 |
| 403 | ❌ 无权限 | 权限不足 |
| 404 | ❌ 未找到 | 资源不存在 |
| 500 | ❌ 服务器错误 | 内部错误 |

---

## 🛠️ 推荐工具

### 浏览器
- ✅ **Swagger UI** - 最简单，推荐新手使用

### 命令行
```bash
# curl（最通用）
curl -X GET "http://localhost:9393/api/rules" \
  -H "Authorization: Bearer xxx"

# HTTPie（更友好）
pip install httpie
http GET localhost:9393/api/rules \
  Authorization:"Bearer xxx"
```

### GUI工具
- **Postman** - 功能最强大
- **Insomnia** - 界面最美观
- **Thunder Client** - VSCode插件

---

## ❓ 常见问题

### Q1: Token过期了怎么办？
**A**: 重新登录获取新Token，默认有效期24小时

### Q2: 如何查看详细错误信息？
**A**: 查看Docker日志
```bash
docker logs -f tmc-local
```

### Q3: 如何测试上传文件？
**A**: 在Swagger UI中使用"Try it out"功能，选择文件即可

### Q4: API返回401错误？
**A**: 检查：
1. Token是否正确
2. 是否添加了 `Bearer` 前缀
3. Token是否过期

---

## 📖 详细文档

- **完整指南**: [docs/API_DOCUMENTATION_GUIDE.md](docs/API_DOCUMENTATION_GUIDE.md)
- **总结报告**: [API_DOCUMENTATION_SUMMARY.md](API_DOCUMENTATION_SUMMARY.md)
- **项目文档**: [README.md](README.md)

---

## 🎉 恭喜！

你已经掌握了API的基本使用方法！

**下一步**:
1. 🔍 浏览所有API文档了解功能
2. 🧪 在Swagger UI中测试各种API
3. 💻 集成到你的应用中
4. 📚 阅读详细文档了解高级功能

**祝你使用愉快！** 🚀

---

**版本**: 1.3.0  
**最后更新**: 2025-01-11

