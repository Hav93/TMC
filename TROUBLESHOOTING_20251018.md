# 问题排查与修复指南 (2025-10-18)

## 🔍 当前问题列表

### 1. ✅ 转发日志显示为空
**状态**: 已创建诊断工具

**问题**: 转发日志页面显示"暂无日志数据"

**可能原因**:
- 数据库表`message_logs`缺少必需字段
- 确实没有转发记录
- 字段名不匹配导致插入失败

**解决方案**:
```bash
# 运行诊断工具
docker exec -it <container> python /app/scripts/diagnose-logs.py

# 如果诊断显示缺少字段，运行修复
docker exec -it <container> python /app/scripts/fix-database-schema.py

# 重启容器
docker-compose restart backend
```

---

### 2. ❓ 媒体监控规则 - 115网盘远程路径保存后显示为空
**状态**: 需要进一步调查

**问题**: 在"编辑监控规则 → 归档配置"中填写115网盘远程路径并保存后，再次打开编辑界面，该字段显示为空

**前端代码位置**: 
- `app/frontend/src/pages/MediaMonitor/MonitorRuleForm.tsx` (第436行)
- 字段名: `pan115_remote_path`

**后端代码位置**:
- `app/backend/models.py` - `MediaMonitorRule.pan115_remote_path`
- `app/backend/api/routes/media_monitor.py` - 创建/更新规则API

**待检查**:
1. 前端是否正确将`pan115_remote_path`包含在提交的数据中
2. 后端API是否保存了该字段
3. 后端API返回规则时是否包含该字段
4. 前端初始化表单时是否正确设置该字段

---

### 3. ❌ 重新整理文件 - HTTP 404错误
**状态**: 需要诊断

**问题**: 点击"重新整理"按钮时，返回nginx的404错误页面

**错误信息**:
```html
<html>
<head><title>404 Not Found</title></head>
<body bgcolor="white">
<center><h1>404 Not Found</h1></center>
<hr><center>nginx/1.14.0</center>
</body>
</html>
```

**API端点**:
- 前端调用: `POST /api/media/files/{fileId}/reorganize`
- 后端定义: `@router.post("/files/{file_id}/reorganize")` in `media_files.py`
- 路由前缀: `/api/media`

**可能原因**:
1. nginx反向代理配置问题
2. 路由未正确注册
3. 前端使用的API URL不正确
4. Docker镜像中的代码未更新

**待检查**:
1. 确认后端容器日志中是否收到请求
2. 检查路由是否正确注册在`routes/__init__.py`
3. 验证前端构建是否使用最新代码
4. 检查Docker镜像缓存问题

---

## 🛠️ 通用排查步骤

### 步骤1: 确认代码已更新
```bash
# 在服务器上
cd /path/to/TMC
git pull origin test
git log -3  # 查看最近3次提交

# 查看当前镜像版本
docker images | grep tmc

# 拉取最新镜像
docker pull hav93/tmc:test
```

### 步骤2: 完全重启
```bash
# 停止并移除容器
docker-compose down

# 清除旧数据（谨慎！会删除数据库）
# rm -rf data/bot.db*

# 启动新容器
docker-compose up -d

# 查看启动日志
docker-compose logs -f backend | head -100
```

### 步骤3: 检查数据库
```bash
# 进入容器
docker exec -it tmc-backend-1 bash

# 运行诊断工具
python /app/scripts/diagnose-logs.py
python /app/scripts/fix-database-schema.py

# 检查特定表
sqlite3 /app/data/bot.db
> .schema media_monitor_rules
> SELECT id, name, pan115_remote_path FROM media_monitor_rules LIMIT 5;
> .quit
```

### 步骤4: 检查API路由
```bash
# 在容器中
cd /app
python -c "
from api.routes import ROUTES
for name, config in ROUTES.items():
    print(f'{name}: {config[\"prefix\"]}')
"
```

### 步骤5: 查看实时日志
```bash
# 后端日志
docker-compose logs -f backend

# API日志
docker exec -it tmc-backend-1 tail -f /app/logs/api.log

# 查找特定错误
docker-compose logs backend | grep -i "404\|error\|failed"
```

---

## 📋 需要收集的信息

如果问题持续，请提供：

1. **后端启动日志**（前100行）:
```bash
docker-compose logs backend | head -100 > startup.log
```

2. **数据库诊断结果**:
```bash
docker exec -it tmc-backend-1 python /app/scripts/diagnose-logs.py > diagnose.log
```

3. **API路由列表**:
```bash
docker exec -it tmc-backend-1 python -c "
from api.routes import ROUTES
import json
print(json.dumps({name: config['prefix'] for name, config in ROUTES.items()}, indent=2))
" > routes.log
```

4. **特定表结构**:
```bash
docker exec -it tmc-backend-1 sqlite3 /app/data/bot.db ".schema media_monitor_rules" > schema.log
docker exec -it tmc-backend-1 sqlite3 /app/data/bot.db ".schema message_logs" >> schema.log
```

5. **浏览器Network请求详情**:
- 打开浏览器开发者工具 → Network
- 执行操作（如点击"重新整理"）
- 复制失败请求的完整URL、Headers、Response

---

## ✅ 已完成的修复

1. ✅ 添加数据库自动修复脚本
2. ✅ 创建日志诊断工具
3. ✅ 修复115纯Cookie模式不需要app_id
4. ✅ 修复资源监控规则的target_path保存问题
5. ✅ 添加resource_monitor_rules表字段到修复脚本

---

## 🎯 下一步行动

1. **立即执行**: 运行诊断工具确认数据库状态
2. **验证**: 检查媒体监控规则的保存和读取逻辑
3. **修复**: 解决404错误的根本原因
4. **测试**: 完整的端到端测试流程

