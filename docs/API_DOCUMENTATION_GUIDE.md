# API文档使用指南

## 📚 访问API文档

本项目提供了两种交互式API文档界面：

### Swagger UI（推荐用于测试）
**URL**: http://localhost:9393/docs

**特点**:
- ✅ 交互式测试界面
- ✅ 直接在浏览器中测试API
- ✅ 自动填充示例数据
- ✅ 支持认证Token管理

### ReDoc（推荐用于阅读）
**URL**: http://localhost:9393/redoc

**特点**:
- ✅ 美观的阅读界面
- ✅ 响应式设计
- ✅ 更好的移动端体验
- ✅ 易于打印和分享

### OpenAPI规范
**URL**: http://localhost:9393/openapi.json

- 标准的OpenAPI 3.0规范
- 可导入Postman、Insomnia等工具

---

## 🔐 API认证

### 步骤1: 获取Token

**请求**:
```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 步骤2: 使用Token

在所有需要认证的请求中添加Header：

```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 在Swagger UI中使用认证

1. 点击页面右上角的 **🔓 Authorize** 按钮
2. 在弹出的对话框中输入：`Bearer <your-token>`
3. 点击 **Authorize** 确认
4. 现在你可以测试需要认证的API了

---

## 📖 API分类

### 1. 认证模块 (/api/auth)
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/register` - 用户注册
- `GET /api/auth/me` - 获取当前用户信息
- `PUT /api/auth/profile` - 更新用户资料
- `PUT /api/auth/password` - 修改密码
- `POST /api/auth/logout` - 退出登录

### 2. 转发规则 (/api/rules)
- `GET /api/rules` - 获取所有规则
- `POST /api/rules` - 创建规则
- `GET /api/rules/{id}` - 获取单个规则
- `PUT /api/rules/{id}` - 更新规则
- `DELETE /api/rules/{id}` - 删除规则
- `POST /api/rules/{id}/toggle` - 切换规则状态

### 3. 媒体监控 (/api/media/monitor)
- `GET /api/media/monitor/rules` - 获取监控规则列表
- `POST /api/media/monitor/rules` - 创建监控规则
- `GET /api/media/monitor/rules/{id}` - 获取规则详情
- `PUT /api/media/monitor/rules/{id}` - 更新规则
- `DELETE /api/media/monitor/rules/{id}` - 删除规则

### 4. 媒体文件 (/api/media)
- `GET /api/media/files` - 获取文件列表
- `GET /api/media/download-tasks` - 获取下载任务
- `POST /api/media/download-tasks/{id}/retry` - 重试下载
- `DELETE /api/media/files/{id}` - 删除文件

### 5. 115网盘 (/api/pan115)
- `POST /api/pan115/qrcode` - 获取登录二维码
- `GET /api/pan115/qrcode/status` - 查询扫码状态
- `GET /api/pan115/files` - 浏览文件列表
- `POST /api/pan115/upload` - 上传文件

### 6. 客户端管理 (/api/clients)
- `GET /api/clients` - 获取客户端列表
- `POST /api/clients` - 创建客户端
- `GET /api/clients/{id}` - 获取客户端详情
- `POST /api/clients/{id}/start` - 启动客户端
- `POST /api/clients/{id}/stop` - 停止客户端

### 7. 系统管理 (/api/system)
- `GET /api/system/info` - 系统信息
- `GET /api/system/stats` - 统计数据
- `POST /api/system/backup` - 数据备份
- `GET /api/system/logs` - 系统日志

---

## 💡 常见使用场景

### 场景1: 创建转发规则

```bash
# 1. 登录获取token
curl -X POST "http://localhost:9393/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 响应: {"access_token":"xxx","token_type":"bearer"}

# 2. 创建规则
curl -X POST "http://localhost:9393/api/rules" \
  -H "Authorization: Bearer xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "我的转发规则",
    "client_id": 1,
    "source_chats": "[\"123456789\"]",
    "target_chat_id": 987654321,
    "enabled": true
  }'
```

### 场景2: 监控频道媒体

```bash
# 创建媒体监控规则
curl -X POST "http://localhost:9393/api/media/monitor/rules" \
  -H "Authorization: Bearer xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "频道视频监控",
    "client_id": 1,
    "source_chats": "[\"123456789\"]",
    "media_types": "[\"video\",\"document\"]",
    "enabled": true
  }'

# 查看下载任务
curl -X GET "http://localhost:9393/api/media/download-tasks?status=completed" \
  -H "Authorization: Bearer xxx"
```

### 场景3: 115网盘登录

```bash
# 1. 获取二维码
curl -X POST "http://localhost:9393/api/pan115/qrcode" \
  -H "Authorization: Bearer xxx" \
  -H "Content-Type: application/json" \
  -d '{"app_id":"your_app_id"}'

# 响应: {"qrcode_url":"xxx","qrcode_token":"yyy"}

# 2. 轮询扫码状态
curl -X GET "http://localhost:9393/api/pan115/qrcode/status?token=yyy" \
  -H "Authorization: Bearer xxx"
```

---

## 🎯 响应格式

### 成功响应
```json
{
  "success": true,
  "message": "操作成功",
  "data": {
    "id": 1,
    "name": "示例"
  }
}
```

### 错误响应
```json
{
  "success": false,
  "message": "操作失败",
  "error": "详细错误信息",
  "code": "ERROR_CODE"
}
```

### 分页响应
```json
{
  "success": true,
  "message": "查询成功",
  "data": [...],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

---

## 📝 HTTP状态码

| 状态码 | 说明 | 常见场景 |
|--------|------|----------|
| 200 | 成功 | GET请求成功 |
| 201 | 已创建 | POST创建成功 |
| 204 | 无内容 | DELETE成功 |
| 400 | 请求错误 | 参数验证失败 |
| 401 | 未认证 | Token无效或过期 |
| 403 | 无权限 | 权限不足 |
| 404 | 未找到 | 资源不存在 |
| 422 | 参数错误 | 数据格式错误 |
| 500 | 服务器错误 | 内部错误 |

---

## 🔧 开发工具推荐

### 1. Postman
- 导入OpenAPI规范：http://localhost:9393/openapi.json
- 创建环境变量存储token
- 使用集合管理API请求

### 2. Insomnia
- 支持OpenAPI导入
- 优秀的GraphQL支持
- 插件生态丰富

### 3. HTTPie
```bash
# 命令行HTTP客户端
pip install httpie

# 使用示例
http POST localhost:9393/api/auth/login \
  username=admin password=admin123
```

### 4. curl
```bash
# 最通用的工具
curl -X POST "http://localhost:9393/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq '.'
```

---

## 📊 API测试建议

### 单元测试
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_login():
    async with AsyncClient(base_url="http://localhost:9393") as client:
        response = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "admin123"}
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
```

### 集成测试
- 使用Swagger UI的"Try it out"功能
- 验证所有API端点
- 测试边界条件和错误处理

---

## 🌐 CORS配置

默认允许的源:
- http://localhost:3000 (Vite开发服务器)
- http://localhost:9393 (生产环境)

如需添加其他源，修改 `app/backend/main.py` 中的 `allow_origins` 配置。

---

## 🔍 调试技巧

### 1. 查看详细错误
在开发环境中，错误响应会包含详细的堆栈追踪。

### 2. 使用日志
```bash
# 查看实时日志
docker logs -f tmc-local

# 查看最近100行
docker logs --tail 100 tmc-local
```

### 3. 数据库查询
```bash
# 进入容器
docker exec -it tmc-local bash

# 查看数据库
sqlite3 /app/data/bot.db
```

---

## 📞 技术支持

- **GitHub Issues**: https://github.com/yourusername/telegram-message-central/issues
- **文档**: https://github.com/yourusername/telegram-message-central/wiki
- **Email**: support@tmc.example.com

---

**最后更新**: 2025-01-11  
**API版本**: v1.3.0

